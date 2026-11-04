from app.adapters.cloud.factory import get_warehouse


class WellnessRepository:

    async def save(self, record: dict) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("wellness_feedback", [record])

    async def get(self, user_id: str, date: str) -> dict | None:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            "SELECT * FROM wellness_feedback WHERE user_id = :user_id AND date = :date",
            {"user_id": user_id, "date": date},
        )
        return rows[0] if rows else None
