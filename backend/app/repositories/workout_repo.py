import json

from app.adapters.cloud.factory import get_warehouse


class WorkoutRepository:

    async def save_workout(self, workout: dict) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("workout_history", [workout])

    async def save_exercises(self, exercises: list[dict]) -> None:
        if not exercises:
            return
        # Serializa muscle_groups como JSON string para SQLite
        rows = [
            {**ex, "muscle_groups": json.dumps(ex["muscle_groups"])}
            for ex in exercises
        ]
        warehouse = get_warehouse()
        await warehouse.insert("workout_exercises", rows)

    async def get_workouts(self, user_id: str, start_date: str, end_date: str) -> list[dict]:
        warehouse = get_warehouse()
        return await warehouse.query(
            """SELECT * FROM workout_history
               WHERE user_id = :user_id
                 AND date BETWEEN :start AND :end
               ORDER BY date DESC""",
            {"user_id": user_id, "start": start_date, "end": end_date},
        )

    async def get_exercises(self, workout_id: str) -> list[dict]:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            "SELECT * FROM workout_exercises WHERE workout_id = :workout_id",
            {"workout_id": workout_id},
        )
        for row in rows:
            if isinstance(row.get("muscle_groups"), str):
                row["muscle_groups"] = json.loads(row["muscle_groups"])
        return rows

    async def get_recent_workouts(self, user_id: str, days: int = 7) -> list[dict]:
        warehouse = get_warehouse()
        return await warehouse.query(
            """SELECT * FROM workout_history
               WHERE user_id = :user_id
                 AND date >= date('now', :offset)
               ORDER BY date DESC""",
            {"user_id": user_id, "offset": f"-{days} days"},
        )
