import json
from datetime import date as _date

from fastapi import APIRouter, HTTPException, status

from app.repositories.user_repo import UserRepository
from app.services.readiness_modality_service import ReadinessModalityService

router = APIRouter(prefix="/readiness/modalities", tags=["readiness-modalities"])
_service = ReadinessModalityService()
_user_repo = UserRepository()


@router.get("/{user_id}")
async def get_modality_readiness(user_id: str, date: str = None):
    """Score de readiness 0–100 pelas modalidades preferidas do usuário."""
    target_date = date if date is not None else str(_date.today())

    user = await _user_repo.get_by_id(user_id)
    preferred: list[str] = []
    if user:
        raw = user.get("preferred_modalities")
        if raw and isinstance(raw, str):
            try:
                preferred = json.loads(raw)
            except Exception:
                preferred = []
        elif isinstance(raw, list):
            preferred = raw

    records = await _service.get(user_id, target_date, filter_modalities=preferred or None)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient health data. Sync before requesting modality readiness.",
        )
    return {"user_id": user_id, "date": target_date, "modalities": records}
