from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.health_data_service import HealthDataService
from app.adapters.connectors.base import OAuthToken
from app.domain.health_metrics.base import RawEvent
from app.domain.health_metrics.sleep import SleepMetric


def _make_token(user_id="user-123") -> OAuthToken:
    return OAuthToken(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        provider="google_fit",
        user_id=user_id,
    )


def _make_raw_event(metric_type="sleep") -> RawEvent:
    return RawEvent(
        event_id="evt-1",
        user_id="user-123",
        provider="google_fit",
        metric_type=metric_type,
        raw_payload={"durationMillis": 27000000},
        collected_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        pipeline_run="run-1",
    )


@pytest.fixture
def service():
    return HealthDataService()


@pytest.mark.asyncio
async def test_sync_raises_when_no_token(service):
    with patch.object(service.token_repo, "get", new_callable=AsyncMock, return_value=None):
        with pytest.raises(ValueError, match="No token found"):
            await service.sync(
                user_id="user-123",
                provider="google_fit",
                start_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
                end_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            )


@pytest.mark.asyncio
async def test_sync_saves_raw_and_normalized(service):
    token = _make_token()
    raw_events = [_make_raw_event("sleep")]

    with patch.object(service.token_repo, "get", new_callable=AsyncMock, return_value=token), \
         patch("app.services.health_data_service.get_connector") as mock_connector_factory, \
         patch.object(service.health_repo, "save_raw_events", new_callable=AsyncMock, return_value=1) as mock_raw, \
         patch.object(service.health_repo, "save_normalized", new_callable=AsyncMock) as mock_norm, \
         patch.object(service.readiness_service, "calculate", new_callable=AsyncMock, return_value={"score": 75}):

        mock_connector = AsyncMock()
        mock_connector.fetch_raw_events = AsyncMock(return_value=raw_events)
        mock_connector_factory.return_value = mock_connector

        result = await service.sync(
            user_id="user-123",
            provider="google_fit",
            start_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

    mock_raw.assert_called_once_with(raw_events)
    mock_norm.assert_called_once()
    assert result["raw_events_ingested"] == 1
    assert result["normalized_records"] == 1


@pytest.mark.asyncio
async def test_sync_skips_invalid_metrics(service):
    token = _make_token()
    # evento com duração zero → is_valid() retorna False
    bad_event = RawEvent(
        event_id="evt-bad",
        user_id="user-123",
        provider="google_fit",
        metric_type="sleep",
        raw_payload={"durationMillis": 0},
        collected_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        pipeline_run="run-1",
    )

    with patch.object(service.token_repo, "get", new_callable=AsyncMock, return_value=token), \
         patch("app.services.health_data_service.get_connector") as mock_factory, \
         patch.object(service.health_repo, "save_raw_events", new_callable=AsyncMock), \
         patch.object(service.health_repo, "save_normalized", new_callable=AsyncMock) as mock_norm, \
         patch.object(service.readiness_service, "calculate", new_callable=AsyncMock, return_value=None):

        mock_connector = AsyncMock()
        mock_connector.fetch_raw_events = AsyncMock(return_value=[bad_event])
        mock_factory.return_value = mock_connector

        result = await service.sync(
            user_id="user-123",
            provider="google_fit",
            start_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )

    mock_norm.assert_not_called()
    assert result["normalized_records"] == 0
