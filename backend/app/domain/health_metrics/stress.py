from dataclasses import dataclass
from datetime import date
from typing import Any
import uuid

from app.domain.health_metrics.base import HealthMetric, RawEvent


@dataclass
class StressMetric(HealthMetric):
    _user_id: str
    _date: date
    stress_score: float | None  # 0-100, 0 = sem estresse
    available: bool
    source_event_id: str
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())

    @property
    def metric_type(self) -> str:
        return "stress"

    @property
    def date(self) -> date:
        return self._date

    @property
    def user_id(self) -> str:
        return self._user_id

    @classmethod
    def from_raw(cls, event: RawEvent) -> "StressMetric":
        p = event.raw_payload
        score = p.get("stressScore")
        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            stress_score=float(score) if score is not None else None,
            available=score is not None,
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        if not self.available:
            return True  # ausência de dado é válida — nem todo relógio mede estresse
        return self.stress_score is not None and 0 <= self.stress_score <= 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "user_id": self._user_id,
            "date": self._date.isoformat(),
            "stress_score": self.stress_score,
            "available": int(self.available),
            "source_event_id": self.source_event_id,
        }
