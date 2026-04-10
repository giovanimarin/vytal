import uuid
import hashlib
from datetime import datetime, timezone, timedelta

from app.adapters.cloud.factory import get_warehouse
from app.config.settings import get_settings


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RefreshTokenRepository:
    def __init__(self):
        self.wh = get_warehouse()

    async def create(self, user_id: str) -> str:
        settings = get_settings()
        raw_token = str(uuid.uuid4())
        token_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)
        await self.wh.insert("refresh_tokens", [{
            "token_id": token_id,
            "user_id": user_id,
            "token_hash": _hash_token(raw_token),
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "revoked": 0,
        }])
        return raw_token

    async def get_by_token(self, raw_token: str) -> dict | None:
        token_hash = _hash_token(raw_token)
        rows = await self.wh.query(
            "SELECT * FROM refresh_tokens WHERE token_hash = :token_hash AND revoked = 0",
            {"token_hash": token_hash},
        )
        if not rows:
            return None
        row = rows[0]
        if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            return None
        return row

    async def revoke(self, raw_token: str) -> None:
        token_hash = _hash_token(raw_token)
        await self.wh.query(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
            [token_hash],
        )

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self.wh.query(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
            [user_id],
        )
