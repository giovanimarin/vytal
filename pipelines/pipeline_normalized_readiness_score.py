"""
Pipeline: normalized_* → fact_daily_readiness

Lê dados normalizados e calcula o Daily Readiness Score por usuário/data.

Uso:
    python pipeline_normalized_readiness_score.py \
        --user_id=user-123 \
        --start_date=2024-01-01 \
        --end_date=2024-01-07
"""
import argparse
import asyncio
import logging
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from app.adapters.cloud.factory import get_pipeline, init_warehouse
from pipelines.transforms.readiness import CalculateReadiness

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _date_range(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    end_d   = date.fromisoformat(end)
    dates = []
    while current <= end_d:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def run(user_id: str, start_date: str, end_date: str):
    asyncio.get_event_loop().run_until_complete(init_warehouse())

    pipeline_provider = get_pipeline()
    options = PipelineOptions(
        runner=pipeline_provider.get_runner_name(),
        **pipeline_provider.get_runner_options(),
    )

    date_pairs = [(user_id, d) for d in _date_range(start_date, end_date)]
    logger.info("Calculating readiness for %d days", len(date_pairs))

    with beam.Pipeline(options=options) as p:
        results, dead = (
            p
            | "CreateDates"         >> beam.Create(date_pairs)
            | "CalculateReadiness"  >> beam.ParDo(CalculateReadiness()).with_outputs("dead_letter", main="valid")
        )

        results | "LogResults" >> beam.Map(
            lambda r: logger.info("Readiness calculated: user=%s date=%s score=%s", r["user_id"], r["date"], r["readiness_score"])
        )
        dead    | "LogDead"    >> beam.Map(lambda x: logger.warning("Dead letter (readiness): %s", x))

    logger.info("Readiness pipeline completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id",    required=True)
    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date",   required=True)
    args = parser.parse_args()
    run(args.user_id, args.start_date, args.end_date)
