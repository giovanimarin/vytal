"""Test-only ASGI process: fixed clock/IDs, synthetic Fit, real rules/JWT/SQLite.

Restore a private in-memory SQLite snapshot between tests. Never emit tokens.
"""
import importlib
import itertools
import json
import socket
import sqlite3
import sys
import uuid
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        instant = cls(2026, 1, 15, 12, tzinfo=UTC)
        return instant.astimezone(tz) if tz is not None else instant.replace(tzinfo=None)

    @classmethod
    def utcnow(cls):
        return cls.now(UTC).replace(tzinfo=None)


def main():
    from app.config.cloud_config import get_cloud_config
    from app.config.settings import settings

    if settings.environment != "test" or get_cloud_config().provider != "local":
        raise RuntimeError("Baseline requires test environment and local provider")
    from app.adapters.connectors.base import OAuthToken
    from app.domain.health_metrics.base import RawEvent
    from app.main import app
    from fastapi.testclient import TestClient

    ids = itertools.count(1)
    connector = Mock()
    connector.get_auth_url.return_value = "https://provider.invalid/authorize"
    connector.exchange_token = AsyncMock(side_effect=lambda *a, **k: OAuthToken(
        "synthetic-provider", "synthetic-provider", Clock.now(UTC) + timedelta(days=1), "google_fit", ""))

    def events(user_id, **kwargs):
        stamp = Clock(2026, 1, 15, tzinfo=UTC)
        payloads = {"sleep": {"durationMillis": 480 * 60000, "sleepScore": 85},
                    "heart_rate": {"restingHeartRate": 60, "averageBpm": 75, "samples": [{"bpm": 60}, {"bpm": 90}]}}
        return [RawEvent(str(uuid.uuid4()), user_id, "google_fit", name, payload,
                         stamp, stamp, "synthetic-run") for name, payload in payloads.items()]
    connector.fetch_raw_events = AsyncMock(side_effect=events)
    with ExitStack() as stack:
        stack.enter_context(patch("uuid.uuid4", side_effect=lambda: uuid.UUID(int=next(ids))))
        for module in ("app.auth.jwt_handler", "app.repositories.user_repo", "app.repositories.refresh_token_repo",
                       "app.repositories.token_repo", "app.repositories.health_data_repo", "app.services.auth_service",
                       "app.services.health_data_service", "app.services.readiness_service",
                       "app.services.readiness_modality_service", "app.services.workout_service",
                       "app.services.muscle_recovery_service", "app.api.v1.wellness_feedback", "jose.jwt"):
            stack.enter_context(patch.object(importlib.import_module(module), "datetime", Clock))
        stack.enter_context(patch("app.services.oauth_service.get_connector", return_value=connector))
        stack.enter_context(patch("app.services.health_data_service.get_connector", return_value=connector))
        stack.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")))
        client = stack.enter_context(TestClient(app, raise_server_exceptions=False))
        actors = {}
        for name in ("A", "B"):
            response = client.post("/api/v1/auth/register", json={
                "email": f"{name}@example.invalid", "password": "synthetic-password-123", "name": name})
            if response.status_code != 201:
                raise RuntimeError("Synthetic baseline registration failed")
            actors[name] = response.json()
        db_path = get_cloud_config().local.db_path
        snapshot = stack.enter_context(sqlite3.connect(":memory:"))
        with sqlite3.connect(db_path) as db:
            db.backup(snapshot)
        initial_id = next(ids)

        last_tokens = {}

        def substitute(value):
            if isinstance(value, str):
                value = value.replace("{last.refresh}", last_tokens.get("refresh_token", "not-issued"))
                for name, actor in actors.items():
                    value = value.replace("{" + name + "}", actor["user_id"])
                    value = value.replace("{" + name + ".refresh}", actor["refresh_token"])
                return value
            if isinstance(value, dict):
                return {k: substitute(v) for k, v in value.items()}
            if isinstance(value, list):
                return [substitute(v) for v in value]
            return value

        def redact(value):
            if isinstance(value, dict):
                return {k: ("<redacted>" if k in {"access_token", "refresh_token", "state"}
                            and isinstance(v, str) else redact(v)) for k, v in value.items()}
            if isinstance(value, list):
                return [redact(v) for v in value]
            return value

        print(json.dumps({"ready": True}), flush=True)
        for line in sys.stdin:
            command = json.loads(line)
            if command.get("reset"):
                with sqlite3.connect(db_path) as db:
                    snapshot.backup(db)
                ids = itertools.count(initial_id)
                connector.reset_mock()
                last_tokens.clear()
                print(json.dumps({"reset": True}), flush=True)
                continue
            actor = command.get("actor")
            headers = {"Authorization": "Bearer " + actors[actor]["access_token"]} if actor in actors else {}
            if actor == "invalid":
                headers = {"Authorization": "Bearer invalid"}
            if command["method"] == "CONNECT":
                state = client.get("/api/v1/connect/google_fit/auth-url",
                                   params={"user_id": actors[actor]["user_id"]}, headers=headers).json()["state"]
                response = client.post("/api/v1/connect/google_fit/callback", headers=headers, json={
                    "code": "synthetic", "state": state, "redirect_uri": "http://localhost/callback"})
                print(json.dumps({"status": response.status_code, "body": redact(response.json()), "provider_calls": 0}), flush=True)
                continue
            before = connector.fetch_raw_events.call_count
            response = client.request(command["method"], "/api/v1" + substitute(command["path"]),
                                      headers=headers, json=substitute(command.get("body")))
            try:
                body = response.json()
            except ValueError:
                body = response.text
            if isinstance(body, dict) and response.status_code < 300 and "refresh_token" in body:
                last_tokens.update({k: body[k] for k in ("access_token", "refresh_token")})
            print(json.dumps({"status": response.status_code, "body": redact(body),
                              "provider_calls": connector.fetch_raw_events.call_count - before}), flush=True)


if __name__ == "__main__":
    main()
