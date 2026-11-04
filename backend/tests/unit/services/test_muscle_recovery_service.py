"""
Testes unitários — MuscleRecoveryService.
Cenários: músculo sem treino, recuperação parcial, sono ruim, sugestão do dia.
"""
from unittest.mock import AsyncMock, patch
import pytest

from app.services.muscle_recovery_service import MuscleRecoveryService
from app.domain.sports.exercise_bank import MUSCLE_GROUPS


@pytest.fixture
def service():
    return MuscleRecoveryService()


def _workout(date="2026-04-17", modality="corrida", intensity="intenso", workout_id="w-1"):
    return {
        "workout_id": workout_id,
        "user_id":    "u-1",
        "date":       date,
        "modality":   modality,
        "intensity":  intensity,
        "duration_min": 60,
    }


def _sleep(duration_minutes=450):
    return {"duration_minutes": duration_minutes}


# ─── _sleep_modifier ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sleep_modifier_good_sleep(service):
    with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                      return_value=[_sleep(480)]):  # 8h
        mod = await service._sleep_modifier("u-1", "2026-04-19")
    assert mod == 1.0


@pytest.mark.asyncio
async def test_sleep_modifier_poor_sleep(service):
    with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                      return_value=[_sleep(240)]):  # 4h
        mod = await service._sleep_modifier("u-1", "2026-04-19")
    assert mod == 1.50


@pytest.mark.asyncio
async def test_sleep_modifier_no_data(service):
    with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                      return_value=[]):
        mod = await service._sleep_modifier("u-1", "2026-04-19")
    assert mod == 1.0


@pytest.mark.asyncio
async def test_sleep_modifier_six_hours(service):
    with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                      return_value=[_sleep(370)]):  # ~6.2h
        mod = await service._sleep_modifier("u-1", "2026-04-19")
    assert mod == 1.15


# ─── calculate ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_muscles_100_without_workouts(service):
    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock, return_value=[]):
        with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                          return_value=[_sleep(480)]):
            with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                result = await service.calculate("u-1", "2026-04-19")

    assert len(result) == len(MUSCLE_GROUPS)
    for r in result:
        assert r["recovery_score"] == 100.0
        assert r["last_workout_id"] is None


@pytest.mark.asyncio
async def test_recent_intense_workout_lowers_score(service):
    w = _workout(date="2026-04-18", modality="corrida", intensity="intenso")

    async def mock_exercises(workout_id):
        return []

    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock,
                      return_value=[w]):
        with patch.object(service.workout_repo, "get_exercises",
                          side_effect=mock_exercises):
            with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                              return_value=[_sleep(480)]):
                with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                    result = await service.calculate("u-1", "2026-04-19")

    quads = next((r for r in result if r["muscle_group"] == "quads"), None)
    assert quads is not None
    # 24h elapsed de 72h required = ~33%
    assert quads["recovery_score"] < 50.0
    assert quads["last_workout_id"] == "w-1"


@pytest.mark.asyncio
async def test_old_workout_fully_recovered(service):
    w = _workout(date="2026-04-11", modality="corrida", intensity="intenso")  # 8 days ago

    async def mock_exercises(workout_id):
        return []

    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock,
                      return_value=[w]):
        with patch.object(service.workout_repo, "get_exercises",
                          side_effect=mock_exercises):
            with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                              return_value=[_sleep(480)]):
                with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                    result = await service.calculate("u-1", "2026-04-19")

    quads = next((r for r in result if r["muscle_group"] == "quads"), None)
    assert quads["recovery_score"] == 100.0


@pytest.mark.asyncio
async def test_poor_sleep_slows_recovery(service):
    w = _workout(date="2026-04-18", modality="corrida", intensity="intenso")

    async def mock_exercises(workout_id):
        return []

    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock,
                      return_value=[w]):
        with patch.object(service.workout_repo, "get_exercises",
                          side_effect=mock_exercises):
            with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                              return_value=[_sleep(240)]):  # 4h, modifier=1.5
                with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                    result_poor = await service.calculate("u-1", "2026-04-19")

    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock,
                      return_value=[w]):
        with patch.object(service.workout_repo, "get_exercises",
                          side_effect=mock_exercises):
            with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                              return_value=[_sleep(480)]):  # 8h, modifier=1.0
                with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                    result_good = await service.calculate("u-1", "2026-04-19")

    quads_poor = next(r for r in result_poor if r["muscle_group"] == "quads")
    quads_good = next(r for r in result_good if r["muscle_group"] == "quads")
    assert quads_good["recovery_score"] > quads_poor["recovery_score"]


@pytest.mark.asyncio
async def test_scores_in_valid_range(service):
    w = _workout(date="2026-04-18", modality="academia", intensity="moderado")

    async def mock_exercises(workout_id):
        return []

    with patch.object(service.workout_repo, "get_workouts", new_callable=AsyncMock,
                      return_value=[w]):
        with patch.object(service.workout_repo, "get_exercises",
                          side_effect=mock_exercises):
            with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                              return_value=[_sleep(420)]):
                with patch.object(service.recovery_repo, "save_batch", new_callable=AsyncMock):
                    result = await service.calculate("u-1", "2026-04-19")

    for r in result:
        assert 0 <= r["recovery_score"] <= 100


# ─── get_suggestion ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_suggestion_returns_best_muscle(service):
    fake_records = [
        {"muscle_group": "quads",  "recovery_score": 45.0, "last_workout_id": "w-1", "estimated_full_recovery_at": None},
        {"muscle_group": "chest",  "recovery_score": 90.0, "last_workout_id": None,  "estimated_full_recovery_at": None},
        {"muscle_group": "biceps", "recovery_score": 60.0, "last_workout_id": "w-1", "estimated_full_recovery_at": None},
    ]
    with patch.object(service, "get", new_callable=AsyncMock, return_value=fake_records):
        result = await service.get_suggestion("u-1", "2026-04-19")

    assert result["suggestion"] == "chest"
    assert result["score"] == 90.0


@pytest.mark.asyncio
async def test_suggestion_no_data(service):
    with patch.object(service, "get", new_callable=AsyncMock, return_value=[]):
        result = await service.get_suggestion("u-1", "2026-04-19")

    assert result["suggestion"] is None
