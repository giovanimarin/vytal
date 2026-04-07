from datetime import date as _date

from fastapi import APIRouter, HTTPException, status

from app.services.readiness_service import ReadinessService

router = APIRouter(prefix="/readiness", tags=["readiness"])
_service = ReadinessService()


@router.get("/{user_id}")
async def get_readiness(user_id: str, date: str = None):
    """Retorna o Daily Readiness Score do dia (padrão: hoje)."""
    target_date = date if date is not None else str(_date.today())

    record = await _service.get(user_id, target_date)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient data to calculate readiness. Sync health data first.",
        )
    return record


@router.get("/{user_id}/history")
async def get_readiness_history(user_id: str, start_date: str, end_date: str):
    """Histórico de Daily Readiness Score no período."""
    history = await _service.get_history(user_id, start_date, end_date)
    return history
