import uuid
from datetime import datetime, timezone

from app.adapters.cloud.factory import get_warehouse
from app.auth.password import hash_password, verify_password


class UserRepository:
    def __init__(self):
        self.wh = get_warehouse()

    async def create(self, email: str, password: str, name: str) -> dict:
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "password_hash": hash_password(password),
            "birth_date": None,
            "weight_kg": None,
            "height_cm": None,
            "goal": "general_wellness",
            "created_at": now,
            "updated_at": now,
        }
        await self.wh.insert("users", [row])
        return row

    async def get_by_email(self, email: str) -> dict | None:
        rows = await self.wh.query(
            "SELECT * FROM users WHERE email = :email",
            {"email": email},
        )
        return rows[0] if rows else None

    async def get_by_id(self, user_id: str) -> dict | None:
        rows = await self.wh.query(
            "SELECT * FROM users WHERE user_id = :user_id",
            {"user_id": user_id},
        )
        return rows[0] if rows else None

    async def update_profile(self, user_id: str, fields: dict) -> dict | None:
        if not fields:
            return await self.get_by_id(user_id)
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        await self.wh.query(
            f"UPDATE users SET {set_clause} WHERE user_id = ?",
            values,
        )
        return await self.get_by_id(user_id)

    async def verify_credentials(self, email: str, password: str) -> dict | None:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return user
