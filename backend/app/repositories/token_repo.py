from datetime import datetime, timezone

from app.adapters.cloud.factory import get_warehouse
from app.adapters.connectors.base import OAuthToken


class TokenRepository:
    async def save(self, token: OAuthToken) -> None:
        warehouse = get_warehouse()
        await warehouse.insert("oauth_tokens", [{
            "user_id": token.user_id,
            "provider": token.provider,
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at.isoformat(),
        }])

    async def get(self, user_id: str, provider: str) -> OAuthToken | None:
        warehouse = get_warehouse()
        rows = await warehouse.query(
            "SELECT * FROM oauth_tokens WHERE user_id = :user_id AND provider = :provider",
            {"user_id": user_id, "provider": provider},
        )
        if not rows:
            return None
        r = rows[0]
        return OAuthToken(
            access_token=r["access_token"],
            refresh_token=r["refresh_token"],
            expires_at=datetime.fromisoformat(r["expires_at"]),
            provider=r["provider"],
            user_id=r["user_id"],
        )
