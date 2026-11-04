from dataclasses import dataclass
from datetime import date
from typing import Any
import uuid

from app.domain.health_metrics.base import HealthMetric, RawEvent


@dataclass
class StepsMetric(HealthMetric):
    _user_id: str
    _date: date
    total_steps: int
    hourly_steps: list[dict]  # [{"hour": 8, "steps": 342}, ...]
    source_event_id: str
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())

    @property
    def metric_type(self) -> str:
        return "steps"

    @property
    def date(self) -> date:
        return self._date

    @property
    def user_id(self) -> str:
        return self._user_id

    @classmethod
    def from_raw(cls, event: RawEvent) -> "StepsMetric":
        p = event.raw_payload
        hourly = p.get("hourlySteps", [])
        total = p.get("totalSteps") or sum(h.get("steps", 0) for h in hourly)
        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            total_steps=int(total),
            hourly_steps=hourly,
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        return 0 <= self.total_steps <= 100_000  # 100k passos/dia = limite razoável

    def to_dict(self) -> dict[str, Any]:
        import json
        return {
            "record_id": self.record_id,
            "user_id": self._user_id,
            "date": self._date.isoformat(),
            "total_steps": self.total_steps,
            "hourly_steps": json.dumps(self.hourly_steps),
            "source_event_id": self.source_event_id,
        }
