from unittest.mock import AsyncMock, patch
import pytest

from app.services.readiness_service import ReadinessService


def _sleep(duration_minutes=450, sleep_score=None):
    return {"duration_minutes": duration_minutes, "sleep_score": sleep_score}


def _hr(resting_bpm=62.0):
    return {"resting_bpm": resting_bpm, "average_bpm": 70.0, "max_bpm": 120.0, "min_bpm": 55.0}


def _activity(intensity="moderate"):
    return [{"activity_type": "running", "duration_minutes": 45, "intensity": intensity, "calories_burned": 400}]


def _stress(score=30.0):
    return {"stress_score": score, "available": 1}


@pytest.fixture
def service():
    return ReadinessService()


# --- Testes de contribuição ---

def test_sleep_contribution_ideal(service):
    assert service._sleep_contribution(_sleep(duration_minutes=480)) == 100.0


def test_sleep_contribution_poor(service):
    assert service._sleep_contribution(_sleep(duration_minutes=200)) == 25.0


def test_sleep_contribution_zero_duration(service):
    assert service._sleep_contribution(_sleep(duration_minutes=0)) == 0.0


def test_sleep_contribution_uses_device_score(service):
    result = service._sleep_contribution(_sleep(duration_minutes=480, sleep_score=60.0))
    assert result == 80.0  # 100 * 0.5 + 60 * 0.5


def test_hr_contribution_athletic(service):
    assert service._hr_contribution(_hr(resting_bpm=52)) == 100.0


def test_hr_contribution_elevated(service):
    assert service._hr_contribution(_hr(resting_bpm=95)) == 15.0


def test_hr_contribution_neutral_when_no_data(service):
    assert service._hr_contribution({"resting_bpm": 0}) == 50.0


def test_activity_contribution_no_activity(service):
    assert service._activity_contribution([]) == 70.0


def test_activity_contribution_high_intensity(service):
    assert service._activity_contribution(_activity("high")) == 40.0


def test_stress_contribution_low_stress(service):
    assert service._stress_contribution(_stress(0)) == 100.0


def test_stress_contribution_high_stress(service):
    assert service._stress_contribution(_stress(80)) == 20.0


def test_stress_contribution_unavailable(service):
    assert service._stress_contribution(None) is None
    assert service._stress_contribution({"available": 0, "stress_score": None}) is None


# --- Teste do cálculo completo ---

@pytest.mark.asyncio
async def test_calculate_returns_none_without_sleep(service):
    with patch.object(service.health_repo, "get_normalized", new_callable=AsyncMock) as mock:
        mock.return_value = []
        result = await service.calculate("user-123", "2024-01-15")
        assert result is None


@pytest.mark.asyncio
async def test_calculate_score_in_range(service):
    async def mock_get_normalized(user_id, date, metric_type):
        if metric_type == "sleep":     return [_sleep(420)]
        if metric_type == "heart_rate": return [_hr(68)]
        if metric_type == "activity":  return _activity("moderate")
        if metric_type == "stress":    return [_stress(25)]
        return []

    with patch.object(service.health_repo, "get_normalized", side_effect=mock_get_normalized):
        with patch.object(service.readiness_repo, "save", new_callable=AsyncMock):
            result = await service.calculate("user-123", "2024-01-15")

    assert result is not None
    assert 0 <= result["readiness_score"] <= 100
    assert result["readiness_category"] in ("rest", "light", "moderate", "intense")
    assert result["insight_text"]


@pytest.mark.asyncio
async def test_calculate_redistributes_stress_weight(service):
    """Quando stress não está disponível, o score ainda deve ser calculado."""
    async def mock_get_normalized(user_id, date, metric_type):
        if metric_type == "sleep":     return [_sleep(480)]
        if metric_type == "heart_rate": return [_hr(58)]
        if metric_type == "activity":  return []
        if metric_type == "stress":    return []  # indisponível
        return []

    with patch.object(service.health_repo, "get_normalized", side_effect=mock_get_normalized):
        with patch.object(service.readiness_repo, "save", new_callable=AsyncMock):
            result = await service.calculate("user-123", "2024-01-15")

    assert result is not None
    assert result["stress_score_contribution"] is None
    assert result["readiness_score"] > 0


@pytest.mark.asyncio
async def test_calculate_intense_category_for_excellent_data(service):
    async def mock_get_normalized(user_id, date, metric_type):
        if metric_type == "sleep":     return [_sleep(480, sleep_score=95)]
        if metric_type == "heart_rate": return [_hr(52)]
        if metric_type == "activity":  return _activity("low")
        if metric_type == "stress":    return [_stress(10)]
        return []

    with patch.object(service.health_repo, "get_normalized", side_effect=mock_get_normalized):
        with patch.object(service.readiness_repo, "save", new_callable=AsyncMock):
            result = await service.calculate("user-123", "2024-01-15")

    assert result["readiness_category"] == "intense"
    assert result["readiness_score"] >= 80


@pytest.mark.asyncio
async def test_calculate_rest_category_for_poor_data(service):
    async def mock_get_normalized(user_id, date, metric_type):
        if metric_type == "sleep":     return [_sleep(180)]  # 3h
        if metric_type == "heart_rate": return [_hr(95)]     # muito elevado
        if metric_type == "activity":  return _activity("high")
        if metric_type == "stress":    return [_stress(90)]  # alto estresse
        return []

    with patch.object(service.health_repo, "get_normalized", side_effect=mock_get_normalized):
        with patch.object(service.readiness_repo, "save", new_callable=AsyncMock):
            result = await service.calculate("user-123", "2024-01-15")

    assert result["readiness_category"] in ("rest", "light")
    assert result["readiness_score"] < 50
