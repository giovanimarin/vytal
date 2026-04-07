from dataclasses import dataclass
from datetime import date
from typing import Any
import uuid

from app.domain.health_metrics.base import HealthMetric, RawEvent


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
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())

    @property
    def metric_type(self) -> str:
        return "sleep"

    @property
    def date(self) -> date:
        return self._date

    @property
    def user_id(self) -> str:
        return self._user_id

    @classmethod
    def from_raw(cls, event: RawEvent) -> "SleepMetric":
        p = event.raw_payload
        # Google Fit retorna durações em milissegundos
        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            duration_minutes=int(p.get("durationMillis", 0)) // 60000,
            deep_sleep_minutes=int(p.get("deepSleepMillis", 0)) // 60000,
            light_sleep_minutes=int(p.get("lightSleepMillis", 0)) // 60000,
            rem_sleep_minutes=int(p.get("remSleepMillis", 0)) // 60000,
            awake_minutes=int(p.get("awakeDuringRestMillis", 0)) // 60000,
            sleep_score=p.get("sleepScore"),
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        return (
            0 < self.duration_minutes <= 1440  # máx 24h
            and self.deep_sleep_minutes >= 0
            and self.light_sleep_minutes >= 0
            and self.rem_sleep_minutes >= 0
            and self.awake_minutes >= 0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "user_id": self._user_id,
            "date": self._date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "deep_sleep_minutes": self.deep_sleep_minutes,
            "light_sleep_minutes": self.light_sleep_minutes,
            "rem_sleep_minutes": self.rem_sleep_minutes,
            "awake_minutes": self.awake_minutes,
            "sleep_score": self.sleep_score,
            "source_event_id": self.source_event_id,
        }
