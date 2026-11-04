"""
Testes unitários — ReadinessModalityService.
Cenários: com HRV, sem HRV, overtraining detectado, score zerado por fadiga extrema.
"""
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from app.services.readiness_modality_service import ReadinessModalityService, MODALITIES


@pytest.fixture
def service():
    return ReadinessModalityService()


def _workout(date="2026-04-18", modality="crossfit", intensity="intenso"):
    return {
        "workout_id": "w-1",
        "user_id": "u-1",
        "date": date,
        "modality": modality,
        "intensity": intensity,
        "duration_min": 60,
    }


def _readiness_record(score=75.0):
    return {
        "readiness_score": score,
        "readiness_category": "moderate",
    }


# ─── _to_status ──────────────────────────────────────────────────────────────

def test_status_green(service):
    assert service._to_status(75.0) == "green"


def test_status_yellow(service):
    assert service._to_status(55.0) == "yellow"


def test_status_red(service):
    assert service._to_status(30.0) == "red"


def test_status_boundary_green(service):
    assert service._to_status(70.0) == "green"


def test_status_boundary_yellow(service):
    assert service._to_status(40.0) == "yellow"


# ─── _training_load_penalty ──────────────────────────────────────────────────

def test_no_penalty_for_few_workouts(service):
    workouts = [_workout(intensity="leve") for _ in range(3)]
    assert service._training_load_penalty(workouts) == 0.0


def test_penalty_for_too_many_workouts(service):
    workouts = [_workout() for _ in range(6)]
    assert service._training_load_penalty(workouts) == 10.0


def test_penalty_for_many_intense(service):
    workouts = [_workout(intensity="intenso") for _ in range(4)]
    assert service._training_load_penalty(workouts) == 15.0


def test_penalty_three_intense(service):
    workouts = [_workout(intensity="intenso") for _ in range(3)]
    assert service._training_load_penalty(workouts) == 5.0


# ─── _compute_muscle_fatigue ─────────────────────────────────────────────────

def test_no_fatigue_without_workouts(service):
    fatigue = service._compute_muscle_fatigue([], "2026-04-19")
    assert all(v == 0.0 for v in fatigue.values())


def test_fatigue_decays_over_time(service):
    w_recent = _workout(date="2026-04-18", modality="corrida", intensity="intenso")
    w_old    = _workout(date="2026-04-12", modality="corrida", intensity="intenso")

    fatigue_recent = service._compute_muscle_fatigue([w_recent], "2026-04-19")
    fatigue_old    = service._compute_muscle_fatigue([w_old],    "2026-04-19")

    assert fatigue_recent["quads"] > fatigue_old["quads"]


def test_fatigue_zero_for_same_day_workout(service):
    w = _workout(date="2026-04-19", modality="corrida", intensity="intenso")
    fatigue = service._compute_muscle_fatigue([w], "2026-04-19")
    assert fatigue["quads"] == 0.0  # mesmo dia não conta


# ─── _modality_score ─────────────────────────────────────────────────────────

def test_score_decreases_with_fatigue(service):
    zero_fatigue = {m: 0.0 for m in ["quads", "hamstrings", "calves", "hip_flexors",
                                      "chest", "upper_back", "core", "glutes",
                                      "front_shoulders", "lower_back", "biceps",
                                      "triceps", "rear_shoulders"]}
    high_fatigue = {**zero_fatigue, "quads": 1.0, "hamstrings": 1.0, "calves": 1.0}

    score_fresh, _ = service._modality_score("corrida", 70.0, zero_fatigue, 0.0, False)
    score_tired, _ = service._modality_score("corrida", 70.0, high_fatigue, 0.0, False)

    assert score_fresh > score_tired


def test_score_clamped_to_zero(service):
    extreme_fatigue = {m: 1.0 for m in ["quads", "hamstrings", "calves", "hip_flexors",
                                          "chest", "upper_back", "core", "glutes",
                                          "front_shoulders", "lower_back", "biceps",
                                          "triceps", "rear_shoulders"]}
    score, _ = service._modality_score("crossfit", 20.0, extreme_fatigue, 15.0, False)
    assert score >= 0.0


def test_low_confidence_flag_when_no_hrv(service):
    fatigue = {m: 0.0 for m in ["quads", "hamstrings", "calves", "hip_flexors",
                                  "chest", "upper_back", "core", "glutes",
                                  "front_shoulders", "lower_back", "biceps",
                                  "triceps", "rear_shoulders"]}
    _, low_conf = service._modality_score("corrida", 75.0, fatigue, 0.0, hrv_available=False)
    assert low_conf is True


def test_no_low_confidence_with_hrv(service):
    fatigue = {m: 0.0 for m in ["quads", "hamstrings", "calves", "hip_flexors",
                                  "chest", "upper_back", "core", "glutes",
                                  "front_shoulders", "lower_back", "biceps",
                                  "triceps", "rear_shoulders"]}
    _, low_conf = service._modality_score("corrida", 75.0, fatigue, 0.0, hrv_available=True)
    assert low_conf is False


# ─── calculate_all (integração leve) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_calculate_all_returns_all_modalities(service):
    with patch.object(service.readiness_repo, "get", new_callable=AsyncMock,
                      return_value=_readiness_record(75.0)):
        with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                          return_value=[]):
            with patch.object(service.workout_repo, "get_recent_workouts", new_callable=AsyncMock,
                              return_value=[]):
                with patch.object(service.modality_repo, "save_batch", new_callable=AsyncMock):
                    result = await service.calculate_all("u-1", "2026-04-19")

    assert len(result) == len(MODALITIES)
    modalities_returned = {r["modality"] for r in result}
    assert modalities_returned == set(MODALITIES)


@pytest.mark.asyncio
async def test_calculate_all_scores_in_range(service):
    with patch.object(service.readiness_repo, "get", new_callable=AsyncMock,
                      return_value=_readiness_record(80.0)):
        with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                          return_value=[]):
            with patch.object(service.workout_repo, "get_recent_workouts", new_callable=AsyncMock,
                              return_value=[]):
                with patch.object(service.modality_repo, "save_batch", new_callable=AsyncMock):
                    result = await service.calculate_all("u-1", "2026-04-19")

    for r in result:
        assert 0 <= r["score"] <= 100
        assert r["status"] in ("green", "yellow", "red")
        assert r["recommendation"]


@pytest.mark.asyncio
async def test_overtraining_lowers_all_scores(service):
    heavy_week = [_workout(date="2026-04-18", intensity="intenso") for _ in range(4)]

    with patch.object(service.readiness_repo, "get", new_callable=AsyncMock,
                      return_value=_readiness_record(70.0)):
        with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                          return_value=[]):
            with patch.object(service.workout_repo, "get_recent_workouts", new_callable=AsyncMock,
                              return_value=heavy_week):
                with patch.object(service.modality_repo, "save_batch", new_callable=AsyncMock):
                    result_heavy = await service.calculate_all("u-1", "2026-04-19")

    with patch.object(service.readiness_repo, "get", new_callable=AsyncMock,
                      return_value=_readiness_record(70.0)):
        with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock,
                          return_value=[]):
            with patch.object(service.workout_repo, "get_recent_workouts", new_callable=AsyncMock,
                              return_value=[]):
                with patch.object(service.modality_repo, "save_batch", new_callable=AsyncMock):
                    result_fresh = await service.calculate_all("u-1", "2026-04-19")

    avg_heavy = sum(r["score"] for r in result_heavy) / len(result_heavy)
    avg_fresh = sum(r["score"] for r in result_fresh) / len(result_fresh)
    assert avg_fresh > avg_heavy
