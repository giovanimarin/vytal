from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.domain.health_metrics.base import RawEvent


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str | None
    expires_at: datetime
    provider: str
    user_id: str


class HealthDataProvider(ABC):
    """
    Interface para conectores de plataformas de saúde.
    Trocar de Google Fit para Apple Health = criar novo Adapter, zero impacto no restante.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Ex: 'google_fit', 'apple_health'."""

    @abstractmethod
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """URL de autorização OAuth do provider."""

    @abstractmethod
    async def exchange_token(self, code: str, redirect_uri: str) -> OAuthToken:
        """Troca o authorization code pelo access token."""

    @abstractmethod
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Renova token expirado."""

    @abstractmethod
    async def fetch_raw_events(
        self,
        user_id: str,
        token: OAuthToken,
        start: datetime,
        end: datetime,
        metric_types: list[str],
    ) -> list[RawEvent]:
        """
        Busca dados do provider e retorna como RawEvents prontos para ingestão.
        Toda conversão de formato externo → interno acontece aqui.
        """
