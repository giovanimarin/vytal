"""
Transforms de sanitização — validam e filtram RawEvents antes da normalização.
"""
import json
import logging

import apache_beam as beam

from app.domain.health_metrics import METRIC_REGISTRY
from app.domain.health_metrics.base import RawEvent

logger = logging.getLogger(__name__)


class ParseRawEvent(beam.DoFn):
    """Deserializa um dict (do warehouse) em RawEvent."""
    def process(self, element: dict):
        try:
            from datetime import datetime
            yield RawEvent(
                event_id=element["event_id"],
                user_id=element["user_id"],
                provider=element["provider"],
                metric_type=element["metric_type"],
                raw_payload=json.loads(element["raw_payload"]) if isinstance(element["raw_payload"], str) else element["raw_payload"],
                collected_at=datetime.fromisoformat(element["collected_at"]),
                ingested_at=datetime.fromisoformat(element["ingested_at"]),
                pipeline_run=element["pipeline_run"],
            )
        except Exception as e:
            logger.warning("Failed to parse raw event %s: %s", element.get("event_id"), e)
            yield beam.pvalue.TaggedOutput("dead_letter", {**element, "error": str(e)})


class NormalizeMetric(beam.DoFn):
    """
    Converte RawEvent em HealthMetric normalizada usando o METRIC_REGISTRY.
    Eventos inválidos vão para dead_letter.
    """
    def process(self, event: RawEvent):
        metric_cls = METRIC_REGISTRY.get(event.metric_type)
        if not metric_cls:
            yield beam.pvalue.TaggedOutput(
                "dead_letter",
                {"event_id": event.event_id, "error": f"Unknown metric_type: {event.metric_type}"},
            )
            return

        try:
            metric = metric_cls.from_raw(event)
            if metric.is_valid():
                yield metric
            else:
                yield beam.pvalue.TaggedOutput(
                    "dead_letter",
                    {"event_id": event.event_id, "error": "Metric failed validation", "data": metric.to_dict()},
                )
        except Exception as e:
            yield beam.pvalue.TaggedOutput(
                "dead_letter",
                {"event_id": event.event_id, "error": str(e)},
            )
