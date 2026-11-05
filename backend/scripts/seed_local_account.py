"""Synthetic health data for an EXISTING local SQLite account; no cloud or tokens."""
import argparse
import asyncio
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def seed_account(email: str, end: date, days: int = 14) -> int:
    from app.adapters.cloud.factory import get_warehouse
    from app.config.cloud_config import get_cloud_config
    from app.config.settings import settings

    if settings.environment not in {"local", "dev", "development", "test"} or get_cloud_config().provider != "local":
        raise ValueError("Demo generation requires a local environment and SQLite")
    if not 1 <= days <= 90:
        raise ValueError("Demo period must be between 1 and 90 days")
    from app.domain.health_metrics import METRIC_REGISTRY
    from app.domain.health_metrics.base import RawEvent
    from app.repositories.health_data_repo import HealthDataRepository
    from app.services.readiness_service import ReadinessService

    warehouse = get_warehouse()
    await warehouse.init_schema()
    rows = await warehouse.query("SELECT user_id FROM users WHERE email = ?", [email])
    if not rows:
        raise ValueError("Create a local account before generating demo data")
    user_id = rows[0]["user_id"]
    start = (end - timedelta(days=days - 1)).isoformat()
    raw_existing = await warehouse.query(
        "SELECT event_id FROM raw_health_events WHERE user_id = ? AND date(collected_at) BETWEEN ? AND ? "
        "AND provider != 'local_demo'", [user_id, start, end.isoformat()])
    if raw_existing:
        raise ValueError("Demo generation refuses to mix with existing non-demo health data")
    for metric in METRIC_REGISTRY:
        existing = await warehouse.query(
            f"SELECT record_id FROM normalized_{metric} WHERE user_id = ? AND date BETWEEN ? AND ? "
            "AND (source_event_id IS NULL OR source_event_id NOT LIKE 'local-demo:%')", [user_id, start, end.isoformat()])
        if existing:
            raise ValueError("Demo generation refuses to mix with existing non-demo health data")
    repo = HealthDataRepository()
    for offset in range(days):
        day = end - timedelta(days=offset)
        stamp = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        payloads = {"sleep": {"durationMillis": (450 + offset % 3 * 15) * 60000, "sleepScore": 85},
                    "heart_rate": {"restingHeartRate": 60, "averageBpm": 75, "samples": [{"bpm": 60}, {"bpm": 90}]},
                    "steps": {"totalSteps": 7600 + offset * 100},
                    "activity": {"activityType": 7, "durationMillis": 30 * 60000, "calories": 120},
                    "stress": {"stressScore": 25}}
        for name, payload in payloads.items():
            identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, f"local-demo/{user_id}/{day}/{name}"))
            event = RawEvent("local-demo:" + identifier, user_id, "local_demo", name, payload, stamp, stamp, "local-demo")
            await repo.save_raw_event(event)
            normalized = METRIC_REGISTRY[name].from_raw(event)
            normalized.record_id = identifier
            await repo.save_normalized(normalized)
        await ReadinessService().calculate(user_id, day.isoformat())
    return days


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    try:
        days = asyncio.run(seed_account(args.email, datetime.now(UTC).date()))
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(f"Generated {days} days of clearly synthetic local_demo health data. No cloud calls.")


if __name__ == "__main__":
    main()
