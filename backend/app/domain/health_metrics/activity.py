from dataclasses import dataclass
from datetime import date
from typing import Any
import uuid

from app.domain.health_metrics.base import HealthMetric, RawEvent

# Mapeamento de tipos de atividade do Google Fit para nomes legíveis
ACTIVITY_TYPE_MAP = {
    7: "walking",
    8: "running",
    1: "biking",
    10: "hiking",
    17: "strength_training",
    21: "yoga",
    108: "swimming",
    3: "still",
}

INTENSITY_MAP = {
    "walking": "low",
    "hiking": "low",
    "yoga": "low",
    "biking": "moderate",
    "swimming": "moderate",
    "strength_training": "moderate",
    "running": "high",
}


@dataclass
class ActivityMetric(HealthMetric):
    _user_id: str
    _date: date
    activity_type: str
    duration_minutes: int
    intensity: str  # low | moderate | high
    calories_burned: float
    source_event_id: str
    record_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())

    @property
    def metric_type(self) -> str:
        return "activity"

    @property
    def date(self) -> date:
        return self._date

    @property
    def user_id(self) -> str:
        return self._user_id

    @classmethod
    def from_raw(cls, event: RawEvent) -> "ActivityMetric":
        p = event.raw_payload
        activity_type_id = p.get("activityType", 3)
        activity_type = ACTIVITY_TYPE_MAP.get(activity_type_id, "other")
        intensity = INTENSITY_MAP.get(activity_type, "low")

        return cls(
            _user_id=event.user_id,
            _date=event.collected_at.date(),
            activity_type=activity_type,
            duration_minutes=int(p.get("durationMillis", 0)) // 60000,
            intensity=intensity,
            calories_burned=float(p.get("calories", 0)),
            source_event_id=event.event_id,
        )

    def is_valid(self) -> bool:
        return (
            0 < self.duration_minutes <= 1440
            and self.calories_burned >= 0
            and self.intensity in ("low", "moderate", "high")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "user_id": self._user_id,
            "date": self._date.isoformat(),
            "activity_type": self.activity_type,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "calories_burned": self.calories_burned,
            "source_event_id": self.source_event_id,
        }
