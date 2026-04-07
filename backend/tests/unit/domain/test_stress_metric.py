from datetime import datetime, timezone
import pytest

from app.domain.health_metrics.stress import StressMetric
from app.domain.health_metrics.base import RawEvent


def _make_event(payload: dict) -> RawEvent:
    return RawEvent(
        event_id="evt-stress-1",
        user_id="user-123",
        provider="google_fit",
        metric_type="stress",
        raw_payload=payload,
        collected_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        pipeline_run="run-1",
    )


def test_from_raw_with_stress_score():
    metric = StressMetric.from_raw(_make_event({"stressScore": 40.0}))
    assert metric.stress_score == 40.0
    assert metric.available is True


def test_from_raw_without_stress_score():
    metric = StressMetric.from_raw(_make_event({}))
    assert metric.stress_score is None
    assert metric.available is False


def test_is_valid_when_unavailable():
    metric = StressMetric.from_raw(_make_event({}))
    assert metric.is_valid() is True  # ausência é válida


def test_is_valid_accepts_valid_range():
    metric = StressMetric.from_raw(_make_event({"stressScore": 0}))
    assert metric.is_valid() is True
    metric2 = StressMetric.from_raw(_make_event({"stressScore": 100}))
    assert metric2.is_valid() is True


def test_is_valid_rejects_out_of_range():
    from app.domain.health_metrics.stress import StressMetric as SM
    from datetime import date
    m = SM(
        _user_id="u",
        _date=date.today(),
        stress_score=150.0,
        available=True,
        source_event_id="x",
    )
    assert m.is_valid() is False
