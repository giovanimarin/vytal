import hashlib
import hmac
import secrets

from app.adapters.connectors.base import OAuthToken
from app.adapters.connectors.factory import get_connector
from app.auth.authorization import authorized_account_id
from app.config.settings import settings
from app.repositories.health_data_repo import HealthDataRepository
from app.repositories.token_repo import TokenRepository


class OAuthService:
    def __init__(self):
        self.token_repo = TokenRepository()
        self.health_repo = HealthDataRepository()

    def get_auth_url(self, provider: str, user_id: str, redirect_uri: str) -> tuple[str, str]:
        """Retorna (auth_url, state)."""
        state = self._generate_state(user_id)
        connector = get_connector(provider)
        url = connector.get_auth_url(redirect_uri=redirect_uri, state=state)
        return url, state

    async def handle_callback(
        self,
        provider: str,
        code: str,
        state: str,
        redirect_uri: str,
        *,
        expected_user_id: str,
    ) -> OAuthToken:
        state_user_id = self._validate_state(state)
        user_id = authorized_account_id(expected_user_id, state_user_id)
        connector = get_connector(provider)

        token = await connector.exchange_token(code, redirect_uri)
        token.user_id = user_id

        await self.token_repo.save(token)
        await self.health_repo.ensure_user(user_id, provider)

        return token

    def _generate_state(self, user_id: str) -> str:
        nonce = secrets.token_hex(16)
        signature = hmac.new(
            settings.secret_key.get_secret_value().encode(),
            f"{user_id}:{nonce}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{user_id}:{nonce}:{signature}"

    def _validate_state(self, state: str) -> str:
        """Valida o state anti-CSRF e retorna o user_id."""
        try:
            user_id, nonce, signature = state.split(":")
        except ValueError:
            raise ValueError("Invalid state format") from None

        expected = hmac.new(
            settings.secret_key.get_secret_value().encode(),
            f"{user_id}:{nonce}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid state signature")

        return user_id
