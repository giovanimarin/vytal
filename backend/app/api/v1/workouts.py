from datetime import date as _date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.authorization import authorized_account_id
from app.auth.dependencies import AuthenticatedUser, AuthorizedAccountId
from app.services.muscle_recovery_service import MuscleRecoveryService
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/workouts", tags=["workouts"])
_workout_service = WorkoutService()
_recovery_service = MuscleRecoveryService()


class ExerciseIn(BaseModel):
    name: str
    sets: int | None = None
    reps: int | None = None


class WorkoutIn(BaseModel):
    user_id: str
    modality: str = Field(..., description="crossfit|corrida|academia|tenis|pilates|surfe|yoga|ciclismo")
    intensity: str = Field(..., description="leve|moderado|intenso")
    duration_min: int = Field(..., gt=0)
    date: str | None = None
    notes: str | None = None
    exercises: list[ExerciseIn] = []
    free_text: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_workout(body: WorkoutIn, current_user: AuthenticatedUser):
    """Registra um treino e atualiza o estado de recuperação muscular."""
    account_id = authorized_account_id(current_user["user_id"], body.user_id)
    valid_modalities = {"crossfit", "corrida", "academia", "tenis", "pilates", "surfe", "yoga", "ciclismo"}
    valid_intensities = {"leve", "moderado", "intenso"}

    if body.modality not in valid_modalities:
        raise HTTPException(status_code=400, detail=f"Modalidade inválida: {body.modality}")
    if body.intensity not in valid_intensities:
        raise HTTPException(status_code=400, detail=f"Intensidade inválida: {body.intensity}")

    workout_date = body.date if body.date is not None else str(_date.today())
    try:
        _date.fromisoformat(workout_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workout date. Use YYYY-MM-DD.") from None

    payload = body.model_dump()
    payload["date"] = workout_date
    payload["user_id"] = account_id
    exercises_raw = [e.model_dump() for e in body.exercises]
    payload["exercises"] = exercises_raw

    workout = await _workout_service.register(account_id, payload)

    # Recalcula recuperação muscular após novo treino
    await _recovery_service.calculate(account_id, workout_date)

    return workout


@router.get("/{user_id}")
async def get_workout_history(user_id: AuthorizedAccountId, start_date: str, end_date: str):
    """Histórico de treinos no período."""
    return await _workout_service.get_history(user_id, start_date, end_date)


@router.get("/exercises/catalog")
async def list_exercises():
    """Catálogo de exercícios com mapeamento de grupos musculares."""
    return _workout_service.list_exercises()
