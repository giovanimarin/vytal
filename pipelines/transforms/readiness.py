"""
Transform para cálculo do Daily Readiness Score no pipeline Beam.
Reutiliza a lógica do ReadinessService de forma síncrona (para o DirectRunner).
"""
import asyncio
import logging

import apache_beam as beam

logger = logging.getLogger(__name__)


class CalculateReadiness(beam.DoFn):
    """
    Recebe (user_id, date) e calcula o Daily Readiness Score.
    Persiste no warehouse via ReadinessService.
    """

    def process(self, element: tuple[str, str]):
        user_id, date = element
        try:
            result = asyncio.get_event_loop().run_until_complete(
                self._calculate(user_id, date)
            )
            if result:
                yield result
            else:
                logger.info("Insufficient data for readiness: user=%s date=%s", user_id, date)
        except Exception as e:
            logger.error("Failed to calculate readiness (%s)", type(e).__name__)
            yield beam.pvalue.TaggedOutput("dead_letter", {"user_id": user_id, "date": date, "error": str(e)})

    async def _calculate(self, user_id: str, date: str):
        from app.services.readiness_service import ReadinessService
        service = ReadinessService()
        return await service.calculate(user_id, date)
