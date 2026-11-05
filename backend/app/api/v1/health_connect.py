from fastapi import APIRouter, HTTPException

from app.auth.dependencies import AuthenticatedUser
from app.config.cloud_config import get_cloud_config
from app.config.security import is_local
from app.config.settings import settings
from app.health_connect.models import Category, ImportBatch
from app.health_connect.repository import HealthConnectRepository

router = APIRouter(prefix='/health-connect', tags=['health-connect'])


def repository():
    config = get_cloud_config()
    if not is_local(settings.environment) or config.provider != 'local':
        raise HTTPException(503, 'Health Connect import is enabled only on the local SQLite backend')
    return HealthConnectRepository(config.local.db_path)


@router.post('/records')
async def import_records(body: ImportBatch, current_user: AuthenticatedUser):
    try:
        return await repository().import_batch(current_user['user_id'], body.installation_id,
            [r.model_dump(mode='json') for r in body.records], body.deleted)
    except (ValueError, KeyError, TypeError):
        raise HTTPException(422, 'Invalid Health Connect record; batch was not committed') from None


@router.get('/records')
async def imported_records(current_user: AuthenticatedUser, category: Category | None = None):
    return await repository().recent(current_user['user_id'], category)
