"""Hermetic v1 smoke: real auth/services/SQLite; only OAuth/Fit boundary is synthetic.

Writes a safe summary only. No tokens, credentials, user data or bodies on stdout.
"""
import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from app.adapters.connectors.base import OAuthToken
from app.config.cloud_config import get_cloud_config
from app.domain.health_metrics.base import RawEvent
from fastapi.testclient import TestClient

DAY = "2026-01-15"
checks = []


def require(condition, name):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def events(user_id, **_kwargs):
    now = datetime(2026, 1, 15, tzinfo=UTC)
    payloads = {
        "sleep": {"durationMillis": 480 * 60000, "sleepScore": 85},
        "heart_rate": {"restingHeartRate": 60, "averageBpm": 75, "samples": [{"bpm": 60}, {"bpm": 90}]},
    }
    return [RawEvent(str(uuid.uuid4()), user_id, "google_fit", metric, payload, now, now, "synthetic-run")
            for metric, payload in payloads.items()]


def main():
    from app.config.settings import settings

    if settings.environment != "test" or get_cloud_config().provider != "local":
        raise RuntimeError("Offline smoke requires explicit test environment and local provider")
    from app.main import app

    connector = Mock()
    connector.get_auth_url.return_value = "https://provider.invalid/authorize"
    connector.exchange_token = AsyncMock(side_effect=lambda *_args, **_kwargs: OAuthToken(
        "synthetic-provider-access", "synthetic-provider-refresh", datetime.now(UTC) + timedelta(days=1), "google_fit", ""))
    connector.fetch_raw_events = AsyncMock(side_effect=events)
    with patch("app.services.oauth_service.get_connector", return_value=connector), \
         patch("app.services.health_data_service.get_connector", return_value=connector), \
         patch("httpx.HTTPTransport.handle_request", side_effect=AssertionError("External network forbidden")), \
         patch("httpx.AsyncHTTPTransport.handle_async_request", side_effect=AssertionError("External network forbidden")), \
         TestClient(app) as client:
        require(client.get("/health").status_code == 200, "startup-local")
        actors = []
        for name in ("A", "B"):
            account = {"email": f"{name}@example.invalid", "password": "synthetic-password-123", "name": name}
            registered = client.post("/api/v1/auth/register", json=account)
            require(registered.status_code == 201, "register-" + name)
            login = client.post("/api/v1/auth/login", json=account)
            require(login.status_code == 200, "login-" + name)
            actor = login.json()
            actors.append(actor)
            headers = {"Authorization": "Bearer " + actor["access_token"]}
            missing = client.get(f'/api/v1/readiness/{actor["user_id"]}', params={"date": DAY}, headers=headers)
            require(missing.status_code == 422, "insufficient-data-" + name)
            authorization = client.get("/api/v1/connect/google_fit/auth-url", params={"user_id": actor["user_id"]}, headers=headers)
            require(authorization.status_code == 200, "provider-authorization-" + name)
            connected = client.post("/api/v1/connect/google_fit/callback", headers=headers, json={
                "code": "synthetic-code", "state": authorization.json()["state"], "redirect_uri": "http://localhost/callback"})
            require(connected.status_code == 200, "provider-callback-" + name)
            result = client.post("/api/v1/health-data/sync", headers=headers, json={
                "user_id": actor["user_id"], "start_date": DAY, "end_date": DAY})
            require(result.status_code == 202, "sync-status-" + name)
            require(result.json()["raw_events_ingested"] == 2 and result.json()["normalized_records"] == 2
                    and result.json()["readiness_calculated_for"] == [DAY], "sync-persistence-" + name)
            summary = client.get(f'/api/v1/health-data/{actor["user_id"]}/summary', params={"date": DAY}, headers=headers)
            require(summary.status_code == 200 and summary.json()["sleep"]["duration_minutes"] == 480
                    and summary.json()["heart_rate"]["resting_bpm"] == 60, "metrics-" + name)
            readiness = client.get(f'/api/v1/readiness/{actor["user_id"]}', params={"date": DAY}, headers=headers)
            require(readiness.status_code == 200 and readiness.json()["readiness_score"] == 86.7
                    and bool(readiness.json()["insight_text"]), "readiness-insight-" + name)
            history = client.get(f'/api/v1/readiness/{actor["user_id"]}/history',
                                 params={"start_date": DAY, "end_date": DAY}, headers=headers)
            require(history.status_code == 200 and len(history.json()) == 1, "history-" + name)
            advanced = client.get(f'/api/v1/readiness/{actor["user_id"]}/advanced', params={"date": DAY}, headers=headers)
            require(advanced.status_code == 200 and "signal_quality" in advanced.json(), "advanced-" + name)
            refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": actor["refresh_token"]})
            require(refreshed.status_code == 200, "refresh-" + name)
            require(client.post("/api/v1/auth/refresh", json={"refresh_token": actor["refresh_token"]}).status_code == 401,
                    "refresh-replay-rejected-" + name)
            replacement = refreshed.json()
            renewed = client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + replacement["access_token"]})
            require(renewed.status_code == 200 and renewed.json()["user_id"] == actor["user_id"], "renewed-identity-" + name)
            require(client.post("/api/v1/auth/logout", json={"refresh_token": replacement["refresh_token"]}).status_code == 200,
                    "logout-" + name)
            require(client.post("/api/v1/auth/refresh", json={"refresh_token": replacement["refresh_token"]}).status_code == 401,
                    "logout-revocation-" + name)
        require(client.post("/api/v1/auth/login", json={"email": "A@example.invalid", "password": "wrong"}).status_code == 401,
                "invalid-login")
        for actor, target in (actors, reversed(actors)):
            headers = {"Authorization": "Bearer " + actor["access_token"]}
            for path in (f'/health-data/{target["user_id"]}/summary', f'/readiness/{target["user_id"]}',
                         f'/readiness/{target["user_id"]}/advanced'):
                require(client.get("/api/v1" + path, params={"date": DAY}, headers=headers).status_code == 404, "cross-account-read")
            before = connector.fetch_raw_events.call_count
            denied = client.post("/api/v1/health-data/sync", headers=headers, json={
                "user_id": target["user_id"], "start_date": DAY, "end_date": DAY})
            require(denied.status_code == 404 and connector.fetch_raw_events.call_count == before, "cross-account-sync-no-effect")
        require(client.get(f'/api/v1/readiness/{actors[0]["user_id"]}', params={"date": DAY}).status_code == 403, "unauthenticated")
        with sqlite3.connect(get_cloud_config().local.db_path) as db:
            require(db.execute("SELECT COUNT(*) FROM raw_health_events").fetchone()[0] == 4, "raw-rows-persisted")
            require(db.execute("SELECT COUNT(*) FROM fact_daily_readiness").fetchone()[0] == 2, "readiness-rows-persisted")
    print(json.dumps({"status": "passed", "checks": len(checks), "cloud_validated": False}))


if __name__ == "__main__":
    main()
