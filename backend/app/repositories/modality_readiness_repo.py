from app.adapters.cloud.factory import get_warehouse


class ModalityReadinessRepository:

    async def save_batch(self, records: list[dict]) -> None:
        if not records:
            return
        warehouse = get_warehouse()
        await warehouse.insert("fact_readiness_by_modality", records)

    async def get_by_date(self, user_id: str, date: str) -> list[dict]:
        warehouse = get_warehouse()
        return await warehouse.query(
            """SELECT * FROM fact_readiness_by_modality
               WHERE user_id = :user_id AND date = :date
               ORDER BY score DESC""",
            {"user_id": user_id, "date": date},
        )

    async def get_single(self, user_id: str, date: str, modality: str) -> dict | None:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            """SELECT * FROM fact_readiness_by_modality
               WHERE user_id = :user_id AND date = :date AND modality = :modality""",
            {"user_id": user_id, "date": date, "modality": modality},
        )
        return rows[0] if rows else None
