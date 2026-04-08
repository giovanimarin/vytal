
from app.adapters.cloud.factory import get_warehouse


class ReadinessRepository:

    async def save(self, record: dict) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("fact_daily_readiness", [record])

    async def get(self, user_id: str, date: str) -> dict | None:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            "SELECT * FROM fact_daily_readiness WHERE user_id = :user_id AND date = :date",
            {"user_id": user_id, "date": date},
        )
        return rows[0] if rows else None

    async def get_history(self, user_id: str, start_date: str, end_date: str) -> list[dict]:
        warehouse = get_warehouse()
        return await warehouse.query(
            """SELECT date, readiness_score, readiness_category
               FROM fact_daily_readiness
               WHERE user_id = :user_id
                 AND date BETWEEN :start AND :end
               ORDER BY date DESC""",
            {"user_id": user_id, "start": start_date, "end": end_date},
        )
