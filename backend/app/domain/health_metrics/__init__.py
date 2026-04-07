from app.domain.health_metrics.base import HealthMetric, RawEvent
from app.domain.health_metrics.sleep import SleepMetric
from app.domain.health_metrics.steps import StepsMetric
from app.domain.health_metrics.activity import ActivityMetric
from app.domain.health_metrics.heart_rate import HeartRateMetric
from app.domain.health_metrics.stress import StressMetric

# Registry — adicionar nova métrica = registrar aqui
METRIC_REGISTRY: dict[str, type[HealthMetric]] = {
    "sleep": SleepMetric,
    "steps": StepsMetric,
    "activity": ActivityMetric,
    "heart_rate": HeartRateMetric,
    "stress": StressMetric,
}

__all__ = [
    "HealthMetric",
    "RawEvent",
    "SleepMetric",
    "StepsMetric",
    "ActivityMetric",
    "HeartRateMetric",
    "StressMetric",
    "METRIC_REGISTRY",
]
