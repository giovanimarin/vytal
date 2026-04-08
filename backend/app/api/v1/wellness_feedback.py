import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.repositories.wellness_repo import WellnessRepository

router = APIRouter(prefix="/wellness-feedback", tags=["wellness-feedback"])
_repo = WellnessRepository()


class WellnessFeedbackRequest(BaseModel):
    user_id: str
    date: str
    feeling_score: Optional[int] = None
    workout_worthwhile: Optional[bool] = None
    workout_readiness: Optional[str] = None
    energy_level: Optional[int] = None
    notes: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_feedback(body: WellnessFeedbackRequest):
    """Salva o feedback subjetivo de bem-estar do usuário para o dia."""
    feedback_id = str(uuid.uuid4())
    record = {
        "feedback_id": feedback_id,
        "user_id": body.user_id,
        "date": body.date,
        "feeling_score": body.feeling_score,
        "workout_worthwhile": int(body.workout_worthwhile) if body.workout_worthwhile is not None else None,
        "workout_readiness": body.workout_readiness,
        "energy_level": body.energy_level,
        "notes": body.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _repo.save(record)
    return {"status": "saved", "feedback_id": feedback_id}


@router.get("/{user_id}")
async def get_feedback(user_id: str, date: str = None):
    """Recupera o feedback de bem-estar do usuário para a data informada."""
    from datetime import date as _date
    target_date = date if date is not None else str(_date.today())

    record = await _repo.get(user_id, target_date)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No wellness feedback found for user '{user_id}' on {target_date}.",
        )
    return record
