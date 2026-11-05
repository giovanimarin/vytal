"""Direct business tests: no handlers, database factory or external providers."""
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from app.services.readiness_service import ReadinessService


@pytest.fixture
def service(monkeypatch):
    from app.adapters.cloud import factory

    monkeypatch.setattr(factory, "get_warehouse", Mock(side_effect=AssertionError("No persistence allowed")))
    result = ReadinessService.__new__(ReadinessService)
    result.health_repo = Mock(get_normalized=AsyncMock())
    result.readiness_repo = Mock(save=AsyncMock())
    return result


@pytest.mark.parametrize("minutes,device,bpm,activity,stress,score,category", [
    (480, 85, 60, [], None, 86.7, "intense"),
    (360, None, 78, [{"intensity": "high"}], {"available": 1, "stress_score": 80}, 56.5, "light"),
    (240, None, 100, [{"intensity": "high"}], {"available": 1, "stress_score": 100}, 22.5, "rest"),
    (360, None, 60, [], None, 78.9, "moderate"),
])
async def test_existing_readiness_results_without_http_or_database(service, minutes, device, bpm, activity, stress, score, category):
    rows = {"sleep": [{"duration_minutes": minutes, "sleep_score": device}],
            "heart_rate": [{"resting_bpm": bpm}], "activity": activity, "stress": [stress] if stress else []}
    service.health_repo.get_normalized.side_effect = lambda user, day, metric: rows[metric]
    record = await service.calculate("synthetic-A", "2026-01-15")
    assert record["readiness_score"] == score and record["readiness_category"] == category
    assert record["user_id"] == "synthetic-A" and record["date"] == "2026-01-15"
    assert isinstance(record["readiness_score"], float) and isinstance(record["insight_text"], str)
    assert datetime.fromisoformat(record["calculated_at"]).utcoffset() is not None
    service.readiness_repo.save.assert_awaited_once_with(record)


@pytest.mark.parametrize("missing", ["sleep", "heart_rate"])
async def test_missing_core_data_does_not_publish_readiness(service, missing):
    rows = {"sleep": [{"duration_minutes": 480}], "heart_rate": [{"resting_bpm": 60}]}
    rows[missing] = []
    service.health_repo.get_normalized.side_effect = lambda user, day, metric: rows.get(metric, [])
    assert await service.calculate("synthetic-A", "2026-01-15") is None
    service.readiness_repo.save.assert_not_called()


async def test_workout_rules_can_run_without_http_or_database():
    from app.services.workout_service import WorkoutService

    service = WorkoutService.__new__(WorkoutService)
    service.repo = Mock(save_workout=AsyncMock(), save_exercises=AsyncMock())
    record = await service.register("synthetic-A", {"modality": "academia", "intensity": "moderado",
        "duration_min": 30, "date": "2026-01-15", "notes": None,
        "exercises": [{"name": "Supino reto", "sets": 3, "reps": None}]})
    assert record["user_id"] == "synthetic-A" and record["duration_min"] == 30
    assert len(record["exercises"]) == 1 and record["exercises"][0]["reps"] is None
    assert record["exercises"][0]["workout_id"] == record["workout_id"]
    service.repo.save_workout.assert_awaited_once()
    service.repo.save_exercises.assert_awaited_once_with(record["exercises"])


async def test_workout_second_step_failure_is_not_hidden_by_business_layer():
    from app.services.workout_service import WorkoutService

    service = WorkoutService.__new__(WorkoutService)
    service.repo = Mock(save_workout=AsyncMock(), save_exercises=AsyncMock(side_effect=RuntimeError("synthetic failure")))
    with pytest.raises(RuntimeError, match="synthetic failure"):
        await service.register("synthetic-A", {"modality": "academia", "intensity": "moderado",
            "duration_min": 30, "date": "2026-01-15", "exercises": [{"name": "Supino reto"}]})
    service.repo.save_workout.assert_awaited_once()
