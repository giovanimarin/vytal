from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.authorization import authorized_account_id
from app.auth.dependencies import AuthenticatedUser, AuthorizedAccountId
from app.services.health_data_service import HealthDataService

router = APIRouter(prefix="/health-data", tags=["health-data"])
_service = HealthDataService()


class SyncRequest(BaseModel):
    user_id: str
    provider: str = "google_fit"
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    metric_types: Optional[list[str]] = None


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_health_data(body: SyncRequest, current_user: AuthenticatedUser):
    """Inicia sincronização de dados do provider para o usuário."""
    account_id = authorized_account_id(current_user["user_id"], body.user_id)
    try:
        start = datetime.fromisoformat(body.start_date).replace(tzinfo=timezone.utc)
        end   = datetime.fromisoformat(body.end_date).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    try:
        result = await _service.sync(
            user_id=account_id,
            provider=body.provider,
            start_date=start,
            end_date=end,
            metric_types=body.metric_types,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return result


@router.get("/{user_id}/summary")
async def get_health_summary(user_id: AuthorizedAccountId, date: str):
    """Retorna dados de saúde normalizados do dia para o mobile."""
    try:
        datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    summary = await _service.get_summary(user_id, date)
    return summary
