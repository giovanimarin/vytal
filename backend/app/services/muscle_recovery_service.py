"""
MuscleRecoveryService — score de recuperação 0–100 por grupo muscular.

Modelo de recuperação:
  recovery_hours_total = base_hours(intensity) / sleep_modifier
  elapsed_hours        = horas desde o treino até target_date
  raw_score            = min(100, elapsed_hours / recovery_hours_total * 100)

Base de recuperação por intensidade:
  leve    → 24h
  moderado → 48h
  intenso  → 72h

Sleep modifier: sono ruim (<6h) aumenta o tempo de recuperação em até 50%.
"""
import json
import uuid
from datetime import date, datetime, timedelta, timezone

from app.repositories.workout_repo import WorkoutRepository
from app.repositories.muscle_recovery_repo import MuscleRecoveryRepository
from app.repositories.health_data_repo import HealthDataRepository
from app.domain.sports.exercise_bank import MUSCLE_GROUPS
from app.services.readiness_modality_service import _MODALITY_MUSCLE_WEIGHTS

_RECOVERY_HOURS = {"leve": 24, "moderado": 48, "intenso": 72}


class MuscleRecoveryService:
    def __init__(self):
        self.workout_repo = WorkoutRepository()
        self.recovery_repo = MuscleRecoveryRepository()
        self.health_repo = HealthDataRepository()

    async def calculate(self, user_id: str, date_str: str) -> list[dict]:
        """Calcula e persiste recovery score para todos os grupos musculares."""
        target = date.fromisoformat(date_str)
        lookback_start = (target - timedelta(days=7)).isoformat()
        workouts = await self.workout_repo.get_workouts(user_id, lookback_start, date_str)

        # Média do sono dos últimos 3 dias para o modificador de recuperação
        sleep_modifier = await self._sleep_modifier(user_id, date_str)

        # Para cada músculo, encontra o treino mais recente que o trabalhou
        last_workout_per_muscle: dict[str, dict] = {}
        for workout in sorted(workouts, key=lambda w: w["date"], reverse=True):
            muscles_hit = await self._muscles_in_workout(workout)
            for muscle in muscles_hit:
                if muscle not in last_workout_per_muscle:
                    last_workout_per_muscle[muscle] = workout

        records: list[dict] = []
        now = datetime.now(timezone.utc)

        for muscle in MUSCLE_GROUPS:
            workout = last_workout_per_muscle.get(muscle)
            if workout is None:
                # Músculo não trabalhado recentemente → totalmente recuperado
                score = 100.0
                last_workout_id = None
                full_recovery_at = None
            else:
                workout_date = date.fromisoformat(workout["date"])
                elapsed_hours = (target - workout_date).days * 24
                base_hours = _RECOVERY_HOURS.get(workout.get("intensity", "moderado"), 48)
                total_hours = base_hours * sleep_modifier
                score = round(min(100.0, (elapsed_hours / total_hours) * 100), 1)
                last_workout_id = workout["workout_id"]

                remaining_hours = max(0, total_hours - elapsed_hours)
                full_recovery_dt = now + timedelta(hours=remaining_hours)
                full_recovery_at = full_recovery_dt.isoformat() if score < 100 else None

            records.append({
                "record_id":                str(uuid.uuid4()),
                "user_id":                  user_id,
                "date":                     date_str,
                "muscle_group":             muscle,
                "recovery_score":           score,
                "last_workout_id":          last_workout_id,
                "estimated_full_recovery_at": full_recovery_at,
                "updated_at":               now.isoformat(),
            })

        await self.recovery_repo.save_batch(records)
        return records

    async def get(self, user_id: str, date_str: str) -> list[dict]:
        existing = await self.recovery_repo.get_by_date(user_id, date_str)
        if existing:
            return existing
        return await self.calculate(user_id, date_str)

    async def get_suggestion(self, user_id: str, date_str: str) -> dict:
        """Retorna o grupo muscular mais pronto para treinar hoje."""
        records = await self.get(user_id, date_str)
        if not records:
            return {"suggestion": None, "message": "Sem dados de treino para gerar sugestão."}

        best = max(records, key=lambda r: r["recovery_score"])
        score = best["recovery_score"]

        if score >= 90:
            msg = f"Seus {_muscle_pt(best['muscle_group'])} estão 100% recuperados. Ótimo dia para trabalha-los!"
        elif score >= 70:
            msg = f"Seus {_muscle_pt(best['muscle_group'])} estão bem recuperados ({score:.0f}%). Uma boa opção para hoje."
        else:
            msg = f"Todos os músculos ainda estão em recuperação. O grupo mais descansado são {_muscle_pt(best['muscle_group'])} ({score:.0f}%)."

        return {"suggestion": best["muscle_group"], "score": score, "message": msg}

    # -------------------------------------------------------------------------

    async def _sleep_modifier(self, user_id: str, date_str: str) -> float:
        """Modificador 1.0–1.5: sono ruim aumenta tempo de recuperação."""
        target = date.fromisoformat(date_str)
        total_duration = 0
        days_with_data = 0

        for offset in range(1, 4):
            d = (target - timedelta(days=offset)).isoformat()
            rows = await self.health_repo.get_normalized(user_id, d, "sleep")
            if rows:
                duration = rows[0].get("duration_minutes") or 0
                if duration > 0:
                    total_duration += duration
                    days_with_data += 1

        if days_with_data == 0:
            return 1.0

        avg_hours = (total_duration / days_with_data) / 60.0
        if avg_hours >= 7:
            return 1.0
        elif avg_hours >= 6:
            return 1.15
        elif avg_hours >= 5:
            return 1.30
        else:
            return 1.50

    async def _muscles_in_workout(self, workout: dict) -> list[str]:
        """Retorna todos os músculos trabalhados em um treino."""
        modality = workout.get("modality", "academia")
        muscles: set[str] = set()

        # Músculos da modalidade
        weights = _MODALITY_MUSCLE_WEIGHTS.get(modality, {})
        muscles.update(weights.keys())

        # Músculos dos exercícios registrados
        exercises = await self.workout_repo.get_exercises(workout["workout_id"])
        for ex in exercises:
            mg = ex.get("muscle_groups", [])
            if isinstance(mg, str):
                mg = json.loads(mg)
            muscles.update(mg)

        return list(muscles)


def _muscle_pt(muscle: str) -> str:
    _pt = {
        "chest": "peitoral",
        "front_shoulders": "ombros anteriores",
        "rear_shoulders": "ombros posteriores",
        "biceps": "bíceps",
        "triceps": "tríceps",
        "upper_back": "costas superiores",
        "lower_back": "lombar",
        "core": "core/abdômen",
        "glutes": "glúteos",
        "quads": "quadríceps",
        "hamstrings": "posterior de coxa",
        "calves": "panturrilhas",
        "hip_flexors": "flexores do quadril",
    }
    return _pt.get(muscle, muscle)
