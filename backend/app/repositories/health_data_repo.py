import json
from datetime import datetime, timezone

from app.adapters.cloud.factory import get_warehouse
from app.domain.health_metrics.base import RawEvent, HealthMetric


class HealthDataRepository:

    async def save_raw_event(self, event: RawEvent) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("raw_health_events", [{
            "event_id": event.event_id,
            "user_id": event.user_id,
            "provider": event.provider,
            "metric_type": event.metric_type,
            "raw_payload": json.dumps(event.raw_payload),
            "collected_at": event.collected_at.isoformat(),
            "ingested_at": event.ingested_at.isoformat(),
            "pipeline_run": event.pipeline_run,
        }])

    async def save_raw_events(self, events: list[RawEvent]) -> int:
        if not events:
            return 0
        warehouse = get_warehouse()
        rows = [{
            "event_id": e.event_id,
            "user_id": e.user_id,
            "provider": e.provider,
            "metric_type": e.metric_type,
            "raw_payload": json.dumps(e.raw_payload),
            "collected_at": e.collected_at.isoformat(),
            "ingested_at": e.ingested_at.isoformat(),
            "pipeline_run": e.pipeline_run,
        } for e in events]
        return await warehouse.insert("raw_health_events", rows)

    async def save_normalized(self, metric: HealthMetric) -> None:
        warehouse = get_warehouse()
        table = f"normalized_{metric.metric_type}"
        row = metric.to_dict()
        row["normalized_at"] = datetime.now(timezone.utc).isoformat()
        await warehouse.insert(table, [row])

    async def get_normalized(
        self,
        user_id: str,
        date: str,
        metric_type: str,
    ) -> list[dict]:
        warehouse = get_warehouse()
        table = f"normalized_{metric_type}"
        rows = await warehouse.query(
            f"SELECT * FROM {table} WHERE user_id = :user_id AND date = :date",
            {"user_id": user_id, "date": date},
        )
        # One authoritative per-day source; never sum Health Connect and Fit mirrors.
        imported = [row for row in rows if str(row.get("source_event_id", "")).startswith("hc-day:")]
        return imported or rows


    async def get_raw_events(
        self,
        user_id: str,
        metric_type: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            """SELECT * FROM raw_health_events
               WHERE user_id = :user_id
                 AND metric_type = :metric_type
                 AND date(collected_at) BETWEEN :start AND :end""",
            {"user_id": user_id, "metric_type": metric_type, "start": start_date, "end": end_date},
        )
        for row in rows:
            row["raw_payload"] = json.loads(row["raw_payload"])
        return rows

    async def ensure_user(self, user_id: str, provider: str) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("dim_user", [{
            "user_id": user_id,
            "provider": provider,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }])
