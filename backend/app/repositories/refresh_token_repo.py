import hashlib
import uuid
from datetime import UTC, datetime, timedelta

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
        now = datetime.now(UTC)
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
        expires_at = row["expires_at"]
        if not isinstance(expires_at, datetime):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.utcoffset() is None:
            raise ValueError("Refresh expiry must be timezone-aware")
        if expires_at <= datetime.now(UTC):
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

    async def rotate(self, raw_token: str, user_id: str) -> str | None:
        """Replace the credential atomically; exactly one concurrent consumer wins.

        Reuse the existing row/schema. Failure to commit cannot consume the old
        credential without installing its replacement in the same statement.
        """
        now = datetime.now(UTC)
        replacement = str(uuid.uuid4())
        affected = await self.wh.execute_affected(
            """UPDATE refresh_tokens
               SET token_hash = :replacement, created_at = :now, expires_at = :expires
               WHERE token_hash = :previous AND user_id = :user_id
                 AND revoked = 0 AND expires_at > :now""",
            {"replacement": _hash_token(replacement), "previous": _hash_token(raw_token),
             "user_id": user_id, "now": now,
             "expires": now + timedelta(days=get_settings().refresh_token_expire_days)},
        )
        return replacement if affected == 1 else None
