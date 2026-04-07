# Interfaces Abstratas — Vytal

**Status**: Aguardando aprovação do Tech Lead  
**Agente**: Architect  
**Versão**: 0.1

---

## HealthMetric — Interface base para métricas de saúde

Toda métrica de saúde coletada implementa esta interface. Garante que novos tipos de dados (HRV, SpO2, etc.) possam ser adicionados sem alterar o pipeline existente.

```python
# backend/app/domain/health_metrics/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

@dataclass
class RawEvent:
    event_id: str
    user_id: str
    provider: str
    metric_type: str
    raw_payload: dict[str, Any]
    collected_at: datetime
    ingested_at: datetime
    pipeline_run: str

class HealthMetric(ABC):
    """
    Interface base para todas as métricas de saúde.
    Cada métrica sabe como se validar e se normalizar a partir de um RawEvent.
    """

    @property
    @abstractmethod
    def metric_type(self) -> str:
        """Identificador único da métrica. Ex: 'sleep', 'steps', 'heart_rate'."""
        pass

    @abstractmethod
    def from_raw(self, event: RawEvent) -> "HealthMetric":
        """Constrói a métrica normalizada a partir de um evento bruto."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Valida se os dados da métrica estão dentro dos ranges esperados."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serializa para persistência no warehouse."""
        pass

    @property
    @abstractmethod
    def date(self) -> date:
        """Data de referência da métrica."""
        pass

    @property
    @abstractmethod
    def user_id(self) -> str:
        pass
```

### Implementações no MVP

```python
# backend/app/domain/health_metrics/sleep.py
@dataclass
class SleepMetric(HealthMetric):
    _user_id: str
    _date: date
    duration_minutes: int
    deep_sleep_minutes: int
    light_sleep_minutes: int
    rem_sleep_minutes: int
    awake_minutes: int
    sleep_score: float | None
    source_event_id: str

    @property
    def metric_type(self) -> str:
        return "sleep"

    @classmethod
    def from_raw(cls, event: RawEvent) -> "SleepMetric":
        p = event.raw_payload  # payload específico do Google Fit
        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            duration_minutes=p.get("durationMillis", 0) // 60000,
            deep_sleep_minutes=p.get("deepSleepMillis", 0) // 60000,
            light_sleep_minutes=p.get("lightSleepMillis", 0) // 60000,
            rem_sleep_minutes=p.get("remSleepMillis", 0) // 60000,
            awake_minutes=p.get("awakeDuringRestMillis", 0) // 60000,
            sleep_score=p.get("sleepScore"),
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        return (
            0 < self.duration_minutes <= 1440  # máx 24h
            and self.deep_sleep_minutes >= 0
            and self.light_sleep_minutes >= 0
        )

    # StepsMetric, ActivityMetric, HeartRateMetric, StressMetric → mesmo padrão
```

---

## HealthDataProvider — Interface para conectores de saúde

Todo conector de plataforma de saúde (Google Fit, Apple Health, etc.) implementa esta interface.

```python
# backend/app/adapters/connectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str
    expires_at: datetime
    provider: str
    user_id: str

class HealthDataProvider(ABC):
    """
    Interface para conectores de plataformas de saúde.
    Garante que trocar de Google Fit para Apple Health não afete nada além do adapter.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identificador do provider. Ex: 'google_fit', 'apple_health'."""
        pass

    @abstractmethod
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Retorna a URL de autorização OAuth do provider."""
        pass

    @abstractmethod
    async def exchange_token(self, code: str, redirect_uri: str) -> OAuthToken:
        """Troca o authorization code pelo access token."""
        pass

    @abstractmethod
    async def refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Renova um token expirado."""
        pass

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
        Busca dados brutos do provider para o período e métricas especificados.
        Retorna RawEvents prontos para ingestão na camada raw/.
        """
        pass
```

---

## CloudProvider — Interfaces de abstração cloud

```python
# backend/app/adapters/cloud/base.py
from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, path: str, data: bytes, content_type: str = None) -> str:
        pass

    @abstractmethod
    async def download(self, path: str) -> bytes:
        pass

    @abstractmethod
    async def list(self, prefix: str) -> list[str]:
        pass

class WarehouseProvider(ABC):
    @abstractmethod
    async def insert(self, table: str, rows: list[dict]) -> int:
        pass

    @abstractmethod
    async def query(self, sql: str, params: dict = None) -> list[dict]:
        pass

class StreamProvider(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: dict) -> str:
        pass

class PipelineProvider(ABC):
    @abstractmethod
    def get_runner_name(self) -> str:
        """Ex: 'DirectRunner', 'DataflowRunner'."""
        pass

    @abstractmethod
    def get_runner_options(self) -> dict:
        """Opções específicas do runner para o Beam pipeline."""
        pass
```

---

## Registro de Métricas e Providers

Ambos usam o padrão Registry para permitir extensão sem modificar código existente:

```python
# Registro de métricas — adicionar nova métrica = registrar aqui
METRIC_REGISTRY: dict[str, type[HealthMetric]] = {
    "sleep":       SleepMetric,
    "steps":       StepsMetric,
    "activity":    ActivityMetric,
    "heart_rate":  HeartRateMetric,
    "stress":      StressMetric,
}

# Registro de providers — adicionar novo conector = registrar aqui
PROVIDER_REGISTRY: dict[str, type[HealthDataProvider]] = {
    "google_fit":     GoogleFitAdapter,
    # "apple_health": AppleHealthAdapter,   ← MVP v2
    # "samsung":      SamsungAdapter,       ← MVP v2
}
```
