from datetime import date as _date

from fastapi import APIRouter, HTTPException, status

from app.services.advanced_metrics_service import AdvancedMetricsService

router = APIRouter(prefix="/readiness", tags=["advanced-metrics"])
_service = AdvancedMetricsService()


@router.get("/{user_id}/advanced")
async def get_advanced_metrics(user_id: str, date: str = None):
    """Retorna métricas avançadas: Social Jetlag, Recovery Curve e Signal Quality."""
    target_date = date if date is not None else str(_date.today())

    result = await _service.calculate(user_id, target_date)
    return result
