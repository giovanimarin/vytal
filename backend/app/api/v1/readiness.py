from datetime import date as _date

from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import AuthorizedAccountId
from app.services.advanced_metrics_service import AdvancedMetricsService
from app.services.readiness_service import ReadinessService

router = APIRouter(prefix="/readiness", tags=["readiness"])
_service = ReadinessService()
_advanced_service = AdvancedMetricsService()


@router.get("/{user_id}/history")
async def get_readiness_history(user_id: AuthorizedAccountId, start_date: str, end_date: str):
    """Histórico de Daily Readiness Score no período."""
    history = await _service.get_history(user_id, start_date, end_date)
    return history


@router.get("/{user_id}/advanced")
async def get_advanced_metrics(user_id: AuthorizedAccountId, date: str | None = None):
    """Retorna métricas avançadas: Social Jetlag, Recovery Curve e Signal Quality."""
    target_date = date if date is not None else str(_date.today())
    return await _advanced_service.calculate(user_id, target_date)


@router.get("/{user_id}")
async def get_readiness(user_id: AuthorizedAccountId, date: str | None = None):
    """Retorna o Daily Readiness Score do dia (padrão: hoje)."""
    target_date = date if date is not None else str(_date.today())

    record = await _service.get(user_id, target_date)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient data to calculate readiness. Sync health data first.",
        )
    return record
