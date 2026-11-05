"""
Pipeline: raw_health_events → normalized_*

Lê eventos brutos do warehouse, normaliza e persiste nas tabelas normalized_*.
Roda com DirectRunner (local) ou DataflowRunner (GCP).

Uso:
    python pipeline_raw_normalized_health.py \
        --user_id=user-123 \
        --start_date=2024-01-01 \
        --end_date=2024-01-07
"""
import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from app.adapters.cloud.factory import get_pipeline, get_warehouse, init_warehouse
from app.config.safe_logging import log_discarded_event
from app.domain.health_metrics.base import HealthMetric

from pipelines.transforms.sanitize import NormalizeMetric, ParseRawEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersistNormalized(beam.DoFn):
    """Persiste a métrica normalizada no warehouse."""

    def process(self, metric: HealthMetric):
        asyncio.get_event_loop().run_until_complete(self._persist(metric))
        yield metric.to_dict()

    async def _persist(self, metric: HealthMetric):
        from app.repositories.health_data_repo import HealthDataRepository
        repo = HealthDataRepository()
        await repo.save_normalized(metric)


def run(user_id: str, start_date: str, end_date: str):
    asyncio.get_event_loop().run_until_complete(init_warehouse())

    pipeline_provider = get_pipeline()
    options = PipelineOptions(
        runner=pipeline_provider.get_runner_name(),
        **pipeline_provider.get_runner_options(),
    )

    # Carrega eventos brutos do warehouse
    warehouse = get_warehouse()
    raw_rows = asyncio.get_event_loop().run_until_complete(
        warehouse.query(
            """SELECT * FROM raw_health_events
               WHERE user_id = :user_id
                 AND date(collected_at) BETWEEN :start AND :end""",
            {"user_id": user_id, "start": start_date, "end": end_date},
        )
    )

    logger.info("Processing %d raw events for user %s", len(raw_rows), user_id)

    with beam.Pipeline(options=options) as p:
        raw_events, dead_parse = (
            p
            | "CreateRaw" >> beam.Create(raw_rows)
            | "ParseRawEvent" >> beam.ParDo(ParseRawEvent()).with_outputs("dead_letter", main="valid")
        )

        normalized, dead_normalize = (
            raw_events
            | "NormalizeMetric" >> beam.ParDo(NormalizeMetric()).with_outputs("dead_letter", main="valid")
        )

        normalized | "PersistNormalized" >> beam.ParDo(PersistNormalized())

        # Dead letters — log para investigação
        dead_parse    | "LogDeadParse"    >> beam.Map(lambda x: log_discarded_event(x, "parse"))
        dead_normalize | "LogDeadNorm"    >> beam.Map(lambda x: log_discarded_event(x, "normalize"))

    logger.info("Pipeline completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id",    required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date",   required=True)
    args = parser.parse_args()
    run(args.user_id, args.start_date, args.end_date)
