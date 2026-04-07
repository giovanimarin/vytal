"""
Google Fit Adapter.
Docs: https://developers.google.com/fit/rest/v1/reference
Uses the dataset:aggregate endpoint for reliable daily summaries.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from google_auth_oauthlib.flow import Flow

from app.adapters.connectors.base import HealthDataProvider, OAuthToken
from app.config.settings import settings
from app.domain.health_metrics.base import RawEvent

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.body.read",
]

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FIT_BASE_URL = "https://www.googleapis.com/fitness/v1/users/me"
_AGGREGATE_URL = f"{_FIT_BASE_URL}/dataset:aggregate"
_SESSIONS_URL = f"{_FIT_BASE_URL}/sessions"


class GoogleFitAdapter(HealthDataProvider):

    @property
    def provider_name(self) -> str:
        return "google_fit"

    def _build_flow(self, redirect_uri: str) -> Flow:
        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": _GOOGLE_TOKEN_URL,
                "redirect_uris": [redirect_uri],
            }
        }
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri
        return flow

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        flow = self._build_flow(redirect_uri)
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )
        return auth_url

    async def exchange_token(self, code: str, redirect_uri: str) -> OAuthToken:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            provider=self.provider_name,
            user_id="",
        )

    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _GOOGLE_TOKEN_URL,
                data={
                    "refresh_token": token.refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=token.refresh_token,
            expires_at=expires_at,
            provider=self.provider_name,
            user_id=token.user_id,
        )

    async def fetch_raw_events(
        self,
        user_id: str,
        token: OAuthToken,
        start: datetime,
        end: datetime,
        metric_types: list[str],
    ) -> list[RawEvent]:
        if datetime.now(timezone.utc) >= token.expires_at and token.refresh_token:
            token = await self.refresh_token(token)

        pipeline_run = str(uuid.uuid4())
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        events: list[RawEvent] = []

        # steps e heart_rate via aggregate (mais confiável)
        aggregate_types = {
            "steps":      "com.google.step_count.delta",
            "heart_rate": "com.google.heart_rate.bpm",
            "activity":   "com.google.activity.segment",
        }
        aggregate_metrics = [m for m in metric_types if m in aggregate_types and m != "stress"]

        if aggregate_metrics:
            payloads = await self._fetch_aggregate(
                token=token,
                data_types=[aggregate_types[m] for m in aggregate_metrics],
                start_ms=start_ms,
                end_ms=end_ms,
            )
            # payloads: dict metric_type → list[dict por dia]
            for metric_type, daily_list in payloads.items():
                for day_payload in daily_list:
                    events.append(RawEvent(
                        event_id=str(uuid.uuid4()),
                        user_id=user_id,
                        provider=self.provider_name,
                        metric_type=metric_type,
                        raw_payload=day_payload,
                        collected_at=datetime.fromtimestamp(
                            day_payload["startTimeMillis"] / 1000, tz=timezone.utc
                        ),
                        ingested_at=datetime.now(timezone.utc),
                        pipeline_run=pipeline_run,
                    ))

        # sleep via sessions API
        if "sleep" in metric_types:
            sleep_payloads = await self._fetch_sleep_sessions(token, start_ms, end_ms)
            for payload in sleep_payloads:
                events.append(RawEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user_id,
                    provider=self.provider_name,
                    metric_type="sleep",
                    raw_payload=payload,
                    collected_at=datetime.fromtimestamp(
                        int(payload["startTimeMillis"]) / 1000, tz=timezone.utc
                    ),
                    ingested_at=datetime.now(timezone.utc),
                    pipeline_run=pipeline_run,
                ))

        logger.info("Fetched %d raw events for user %s", len(events), user_id)
        return events

    async def _fetch_aggregate(
        self,
        token: OAuthToken,
        data_types: list[str],
        start_ms: int,
        end_ms: int,
    ) -> dict[str, list[dict]]:
        """
        Usa dataset:aggregate para buscar resumos diários.
        Retorna dict: metric_type → lista de payloads por dia.
        """
        body = {
            "aggregateBy": [{"dataTypeName": dt} for dt in data_types],
            "bucketByTime": {"durationMillis": 86400000},  # 1 dia
            "startTimeMillis": start_ms,
            "endTimeMillis": end_ms,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _AGGREGATE_URL,
                json=body,
                headers={"Authorization": f"Bearer {token.access_token}"},
            )
            if resp.status_code != 200:
                logger.warning("Aggregate API error %s: %s", resp.status_code, resp.text)
                return {}
            data = resp.json()

        # Mapeia data_type → metric_type
        type_to_metric = {
            "com.google.step_count.delta": "steps",
            "com.google.heart_rate.bpm":   "heart_rate",
            "com.google.activity.segment": "activity",
        }

        result: dict[str, list[dict]] = {}

        for bucket in data.get("bucket", []):
            bucket_start = int(bucket.get("startTimeMillis", 0))
            bucket_end   = int(bucket.get("endTimeMillis", 0))

            for dataset in bucket.get("dataset", []):
                data_type = dataset.get("dataSourceId", "")
                # extrai o tipo canônico do dataSourceId
                metric_type = None
                for dt, mt in type_to_metric.items():
                    if dt in data_type:
                        metric_type = mt
                        break
                if not metric_type:
                    continue

                points = dataset.get("point", [])
                if not points:
                    continue

                payload = self._parse_aggregate_points(metric_type, points, bucket_start, bucket_end)
                if payload:
                    result.setdefault(metric_type, []).append(payload)

        return result

    def _parse_aggregate_points(
        self, metric_type: str, points: list[dict], start_ms: int, end_ms: int
    ) -> dict | None:
        """Converte pontos do aggregate para o payload interno por métrica."""

        if metric_type == "steps":
            total = sum(
                v.get("intVal", 0)
                for p in points
                for v in p.get("value", [])
            )
            if total == 0:
                return None
            return {
                "startTimeMillis": start_ms,
                "endTimeMillis":   end_ms,
                "totalSteps":      total,
            }

        elif metric_type == "heart_rate":
            fp_values = [
                v.get("fpVal", 0)
                for p in points
                for v in p.get("value", [])
                if v.get("fpVal", 0) > 0
            ]
            if not fp_values:
                return None
            return {
                "startTimeMillis":  start_ms,
                "endTimeMillis":    end_ms,
                "restingHeartRate": min(fp_values),   # mínimo do dia ≈ repouso
                "averageBpm":       sum(fp_values) / len(fp_values),
                "samples":          [{"bpm": v} for v in fp_values],
            }

        elif metric_type == "activity":
            activities = []
            for p in points:
                values = p.get("value", [])
                activity_type = values[0].get("intVal", 3) if values else 3
                duration_ms = int(p.get("endTimeNanos", 0)) // 1_000_000 - int(p.get("startTimeNanos", 0)) // 1_000_000
                activities.append({
                    "startTimeMillis": start_ms,
                    "endTimeMillis":   end_ms,
                    "activityType":    activity_type,
                    "durationMillis":  duration_ms,
                    "calories":        0,
                })
            return activities[0] if len(activities) == 1 else (activities[0] if activities else None)

        return None

    async def _fetch_sleep_sessions(
        self, token: OAuthToken, start_ms: int, end_ms: int
    ) -> list[dict]:
        """Busca sessões de sono via sessions API."""
        params = {
            "startTime": datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat(),
            "endTime":   datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).isoformat(),
            "activityType": 72,  # 72 = sleep no Google Fit
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _SESSIONS_URL,
                params=params,
                headers={"Authorization": f"Bearer {token.access_token}"},
            )
            if resp.status_code != 200:
                logger.warning("Sessions API error %s: %s", resp.status_code, resp.text)
                return []
            data = resp.json()

        payloads = []
        for session in data.get("session", []):
            start_ms_s = int(session.get("startTimeMillis", 0))
            end_ms_s   = int(session.get("endTimeMillis", 0))
            duration   = end_ms_s - start_ms_s

            if duration <= 0:
                continue

            payloads.append({
                "startTimeMillis":        start_ms_s,
                "endTimeMillis":          end_ms_s,
                "durationMillis":         duration,
                "deepSleepMillis":        int(duration * 0.20),  # estimativa sem dado granular
                "lightSleepMillis":       int(duration * 0.55),
                "remSleepMillis":         int(duration * 0.20),
                "awakeDuringRestMillis":  int(duration * 0.05),
                "sleepScore":             None,
            })

        logger.info("Found %d sleep sessions", len(payloads))
        return payloads
