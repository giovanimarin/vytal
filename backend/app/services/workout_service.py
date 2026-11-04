import json
import uuid
from datetime import datetime, timezone

from app.repositories.workout_repo import WorkoutRepository
from app.domain.sports.exercise_bank import EXERCISE_BY_NAME, parse_free_text_muscles, EXERCISE_BANK


class WorkoutService:
    def __init__(self):
        self.repo = WorkoutRepository()

    async def register(self, user_id: str, payload: dict) -> dict:
        """
        Registra um treino e persiste os exercícios com seus grupos musculares.
        payload esperado:
          modality, intensity, duration_min, date, notes (opt)
          exercises: list of {name, sets?, reps?}  OR  free_text
        """
        workout_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        workout_date = payload.get("date", datetime.now(timezone.utc).date().isoformat())

        workout = {
            "workout_id":   workout_id,
            "user_id":      user_id,
            "date":         workout_date,
            "modality":     payload["modality"],
            "intensity":    payload["intensity"],
            "duration_min": int(payload["duration_min"]),
            "notes":        payload.get("notes"),
            "created_at":   now,
        }
        await self.repo.save_workout(workout)

        exercises = self._parse_exercises(workout_id, payload)
        if exercises:
            await self.repo.save_exercises(exercises)

        workout["exercises"] = exercises
        return workout

    async def get_history(self, user_id: str, start_date: str, end_date: str) -> list[dict]:
        workouts = await self.repo.get_workouts(user_id, start_date, end_date)
        for w in workouts:
            w["exercises"] = await self.repo.get_exercises(w["workout_id"])
        return workouts

    def list_exercises(self) -> list[dict]:
        return [
            {"name": e.name, "primary": e.primary, "secondary": e.secondary}
            for e in EXERCISE_BANK
        ]

    # -------------------------------------------------------------------------

    def _parse_exercises(self, workout_id: str, payload: dict) -> list[dict]:
        exercises_payload = payload.get("exercises", [])
        free_text = payload.get("free_text", "")
        result: list[dict] = []

        # Exercícios explícitos da lista
        for ex in exercises_payload:
            name = ex.get("name", "")
            known = EXERCISE_BY_NAME.get(name.lower())
            muscles = (known.primary + known.secondary) if known else parse_free_text_muscles(name)
            result.append({
                "exercise_id":   str(uuid.uuid4()),
                "workout_id":    workout_id,
                "name":          name,
                "muscle_groups": muscles,
                "sets":          ex.get("sets"),
                "reps":          ex.get("reps"),
            })

        # Texto livre → mapeia músculos
        if free_text and not exercises_payload:
            muscles = parse_free_text_muscles(free_text)
            if muscles:
                result.append({
                    "exercise_id":   str(uuid.uuid4()),
                    "workout_id":    workout_id,
                    "name":          free_text[:100],
                    "muscle_groups": muscles,
                    "sets":          None,
                    "reps":          None,
                })

        return result
