import uuid
from datetime import datetime, timezone

from app.adapters.connectors.factory import get_connector
from app.domain.health_metrics import METRIC_REGISTRY
from app.repositories.health_data_repo import HealthDataRepository
from app.repositories.token_repo import TokenRepository
from app.services.readiness_service import ReadinessService

DEFAULT_METRIC_TYPES = ["sleep", "steps", "activity", "heart_rate", "stress"]


class HealthDataService:
    def __init__(self):
        self.health_repo = HealthDataRepository()
        self.token_repo = TokenRepository()
        self.readiness_service = ReadinessService()

    async def sync(
        self,
        user_id: str,
        provider: str,
        start_date: datetime,
        end_date: datetime,
        metric_types: list[str] = None,
    ) -> dict:
        """
        Fluxo completo: busca dados do provider → persiste raw →
        normaliza → calcula Daily Readiness.
        """
        sync_id = str(uuid.uuid4())
        metric_types = metric_types or DEFAULT_METRIC_TYPES

        token = await self.token_repo.get(user_id, provider)
        if not token:
            raise ValueError(f"No token found for user '{user_id}' and provider '{provider}'")

        # 1. Busca dados brutos do provider
        connector = get_connector(provider)
        raw_events = await connector.fetch_raw_events(
            user_id=user_id,
            token=token,
            start=start_date,
            end=end_date,
            metric_types=metric_types,
        )

        # 2. Persiste raw events
        await self.health_repo.save_raw_events(raw_events)

        # 3. Normaliza cada evento usando a métrica correspondente
        normalized_count = 0
        for event in raw_events:
            metric_cls = METRIC_REGISTRY.get(event.metric_type)
            if not metric_cls:
                continue
            metric = metric_cls.from_raw(event)
            if metric.is_valid():
                await self.health_repo.save_normalized(metric)
                normalized_count += 1

        # 4. Calcula Daily Readiness para cada dia no período
        current = start_date.date()
        end = end_date.date()
        readiness_dates = []
        while current <= end:
            date_str = current.isoformat()
            readiness = await self.readiness_service.calculate(user_id, date_str)
            if readiness:
                readiness_dates.append(date_str)
            from datetime import timedelta
            current += timedelta(days=1)

        return {
            "sync_id": sync_id,
            "status": "completed",
            "user_id": user_id,
            "raw_events_ingested": len(raw_events),
            "normalized_records": normalized_count,
            "readiness_calculated_for": readiness_dates,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_summary(self, user_id: str, date: str) -> dict:
        """Retorna dados normalizados do dia para o mobile."""
        summary = {"user_id": user_id, "date": date}

        for metric_type in DEFAULT_METRIC_TYPES:
            rows = await self.health_repo.get_normalized(user_id, date, metric_type)
            if metric_type == "activity":
                summary[metric_type] = rows  # pode ter múltiplos por dia
            else:
                summary[metric_type] = rows[0] if rows else None

        return summary
