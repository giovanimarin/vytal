from datetime import datetime, timezone
import pytest

from app.domain.health_metrics.sleep import SleepMetric
from app.domain.health_metrics.base import RawEvent


def _make_event(payload: dict) -> RawEvent:
    return RawEvent(
        event_id="evt-1",
        user_id="user-123",
        provider="google_fit",
        metric_type="sleep",
        raw_payload=payload,
        collected_at=datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        pipeline_run="run-1",
    )


def test_from_raw_converts_millis_to_minutes():
    event = _make_event({
        "durationMillis": 27000000,      # 450 min = 7.5h
        "deepSleepMillis": 5400000,      # 90 min
        "lightSleepMillis": 12600000,    # 210 min
        "remSleepMillis": 7200000,       # 120 min
        "awakeDuringRestMillis": 1800000, # 30 min
        "sleepScore": 82.0,
    })
    metric = SleepMetric.from_raw(event)

    assert metric.duration_minutes == 450
    assert metric.deep_sleep_minutes == 90
    assert metric.light_sleep_minutes == 210
    assert metric.rem_sleep_minutes == 120
    assert metric.awake_minutes == 30
    assert metric.sleep_score == 82.0
    assert metric.user_id == "user-123"
    assert metric.date.isoformat() == "2024-01-15"


def test_is_valid_with_good_data():
    event = _make_event({"durationMillis": 27000000})
    assert SleepMetric.from_raw(event).is_valid() is True


def test_is_valid_rejects_zero_duration():
    event = _make_event({"durationMillis": 0})
    assert SleepMetric.from_raw(event).is_valid() is False


def test_is_valid_rejects_over_24h():
    event = _make_event({"durationMillis": 90000000})  # 1500 min > 1440
    assert SleepMetric.from_raw(event).is_valid() is False


def test_from_raw_handles_missing_fields():
    event = _make_event({})
    metric = SleepMetric.from_raw(event)
    assert metric.duration_minutes == 0
    assert metric.sleep_score is None


def test_to_dict_contains_required_fields():
    event = _make_event({"durationMillis": 27000000, "sleepScore": 75.0})
    d = SleepMetric.from_raw(event).to_dict()

    assert "record_id" in d
    assert d["user_id"] == "user-123"
    assert d["date"] == "2024-01-15"
    assert d["duration_minutes"] == 450
    assert d["sleep_score"] == 75.0
