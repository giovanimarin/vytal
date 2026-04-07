from datetime import datetime, timezone
import pytest

from app.domain.health_metrics.heart_rate import HeartRateMetric
from app.domain.health_metrics.base import RawEvent


def _make_event(payload: dict) -> RawEvent:
    return RawEvent(
        event_id="evt-hr-1",
        user_id="user-123",
        provider="google_fit",
        metric_type="heart_rate",
        raw_payload=payload,
        collected_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        pipeline_run="run-1",
    )


def test_from_raw_with_explicit_values():
    event = _make_event({
        "restingHeartRate": 58.0,
        "averageBpm": 72.0,
        "samples": [{"bpm": 55}, {"bpm": 60}, {"bpm": 90}],
    })
    metric = HeartRateMetric.from_raw(event)

    assert metric.resting_bpm == 58.0
    assert metric.average_bpm == 72.0
    assert metric.max_bpm == 90.0
    assert metric.min_bpm == 55.0


def test_from_raw_computes_average_from_samples():
    event = _make_event({
        "samples": [{"bpm": 60}, {"bpm": 80}],
    })
    metric = HeartRateMetric.from_raw(event)
    assert metric.average_bpm == 70.0


def test_is_valid_accepts_normal_range():
    event = _make_event({"restingHeartRate": 65.0, "averageBpm": 75.0, "samples": []})
    assert HeartRateMetric.from_raw(event).is_valid() is True


def test_is_valid_rejects_impossible_values():
    event = _make_event({"restingHeartRate": 10.0, "averageBpm": 10.0, "samples": []})
    assert HeartRateMetric.from_raw(event).is_valid() is False


def test_is_valid_rejects_over_220():
    event = _make_event({"restingHeartRate": 250.0, "averageBpm": 250.0, "samples": []})
    assert HeartRateMetric.from_raw(event).is_valid() is False
