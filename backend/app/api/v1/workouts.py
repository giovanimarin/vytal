from datetime import date as _date
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.workout_service import WorkoutService
from app.services.muscle_recovery_service import MuscleRecoveryService

router = APIRouter(prefix="/workouts", tags=["workouts"])
_workout_service = WorkoutService()
_recovery_service = MuscleRecoveryService()


class ExerciseIn(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None


class WorkoutIn(BaseModel):
    user_id: str
    modality: str = Field(..., description="crossfit|corrida|academia|tenis|pilates|surfe|yoga|ciclismo")
    intensity: str = Field(..., description="leve|moderado|intenso")
    duration_min: int = Field(..., gt=0)
    date: Optional[str] = None
    notes: Optional[str] = None
    exercises: list[ExerciseIn] = []
    free_text: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_workout(body: WorkoutIn):
    """Registra um treino e atualiza o estado de recuperação muscular."""
    valid_modalities = {"crossfit", "corrida", "academia", "tenis", "pilates", "surfe", "yoga", "ciclismo"}
    valid_intensities = {"leve", "moderado", "intenso"}

    if body.modality not in valid_modalities:
        raise HTTPException(status_code=400, detail=f"Modalidade inválida: {body.modality}")
    if body.intensity not in valid_intensities:
        raise HTTPException(status_code=400, detail=f"Intensidade inválida: {body.intensity}")

    payload = body.model_dump()
    exercises_raw = [e.model_dump() for e in body.exercises]
    payload["exercises"] = exercises_raw

    workout = await _workout_service.register(body.user_id, payload)

    # Recalcula recuperação muscular após novo treino
    workout_date = body.date or str(_date.today())
    await _recovery_service.calculate(body.user_id, workout_date)

    return workout


@router.get("/{user_id}")
async def get_workout_history(user_id: str, start_date: str, end_date: str):
    """Histórico de treinos no período."""
    return await _workout_service.get_history(user_id, start_date, end_date)


@router.get("/exercises/catalog")
async def list_exercises():
    """Catálogo de exercícios com mapeamento de grupos musculares."""
    return _workout_service.list_exercises()
