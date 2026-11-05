from datetime import date as _date

from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import AuthorizedAccountId
from app.services.muscle_recovery_service import MuscleRecoveryService

router = APIRouter(prefix="/muscles", tags=["muscles"])
_service = MuscleRecoveryService()


@router.get("/{user_id}/recovery")
async def get_muscle_recovery(user_id: AuthorizedAccountId, date: str = None):
    """Score de recuperação 0–100 por grupo muscular."""
    target_date = date if date is not None else str(_date.today())
    records = await _service.get(user_id, target_date)
    return {"user_id": user_id, "date": target_date, "muscles": records}


@router.get("/{user_id}/suggestion")
async def get_muscle_suggestion(user_id: AuthorizedAccountId, date: str = None):
    """Grupo muscular mais recuperado e pronto para treinar hoje."""
    target_date = date if date is not None else str(_date.today())
    return await _service.get_suggestion(user_id, target_date)
