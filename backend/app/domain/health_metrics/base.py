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
    Cada implementação sabe como se construir a partir de um RawEvent
    e como se validar.
    """

    @property
    @abstractmethod
    def metric_type(self) -> str:
        """Identificador único. Ex: 'sleep', 'steps', 'heart_rate'."""

    @classmethod
    @abstractmethod
    def from_raw(cls, event: RawEvent) -> "HealthMetric":
        """Constrói a métrica normalizada a partir de um evento bruto."""

    @abstractmethod
    def is_valid(self) -> bool:
        """Valida se os valores estão dentro de ranges fisiológicos esperados."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serializa para persistência."""

    @property
    @abstractmethod
    def date(self) -> date:
        """Data de referência da métrica."""

    @property
    @abstractmethod
    def user_id(self) -> str:
        pass
