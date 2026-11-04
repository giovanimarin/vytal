from app.adapters.cloud.factory import get_warehouse


class MuscleRecoveryRepository:

    async def save_batch(self, records: list[dict]) -> None:
        if not records:
            return
        warehouse = get_warehouse()
        await warehouse.insert("muscle_recovery", records)

    async def get_by_date(self, user_id: str, date: str) -> list[dict]:
        warehouse = get_warehouse()
        return await warehouse.query(
            """SELECT * FROM muscle_recovery
               WHERE user_id = :user_id AND date = :date
               ORDER BY recovery_score DESC""",
            {"user_id": user_id, "date": date},
        )

    async def get_single(self, user_id: str, date: str, muscle_group: str) -> dict | None:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            """SELECT * FROM muscle_recovery
               WHERE user_id = :user_id AND date = :date AND muscle_group = :muscle_group""",
            {"user_id": user_id, "date": date, "muscle_group": muscle_group},
        )
        return rows[0] if rows else None
