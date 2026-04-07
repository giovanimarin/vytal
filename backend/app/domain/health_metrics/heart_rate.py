from dataclasses import dataclass
from datetime import date
from typing import Any
import uuid

from app.domain.health_metrics.base import HealthMetric, RawEvent


@dataclass
class HeartRateMetric(HealthMetric):
    _user_id: str
    _date: date
    resting_bpm: float
    average_bpm: float
    max_bpm: float
    min_bpm: float
    source_event_id: str
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())

    @property
    def metric_type(self) -> str:
        return "heart_rate"

    @property
    def date(self) -> date:
        return self._date

    @property
    def user_id(self) -> str:
        return self._user_id

    @classmethod
    def from_raw(cls, event: RawEvent) -> "HeartRateMetric":
        p = event.raw_payload
        samples = p.get("samples", [])
        values = [s.get("bpm", 0) for s in samples if s.get("bpm", 0) > 0]

        avg = sum(values) / len(values) if values else 0
        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            resting_bpm=float(p.get("restingHeartRate", avg)),
            average_bpm=float(p.get("averageBpm", avg)),
            max_bpm=float(max(values, default=0)),
            min_bpm=float(min(values, default=0)),
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        # Ranges fisiológicos humanos
        return (
            20 <= self.resting_bpm <= 220
            and 20 <= self.average_bpm <= 220
            and self.max_bpm >= self.min_bpm
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "user_id": self._user_id,
            "date": self._date.isoformat(),
            "resting_bpm": self.resting_bpm,
            "average_bpm": self.average_bpm,
            "max_bpm": self.max_bpm,
            "min_bpm": self.min_bpm,
            "source_event_id": self.source_event_id,
        }
