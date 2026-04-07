from fastapi import APIRouter

from app.api.v1.connect import router as connect_router
from app.api.v1.health_data import router as health_data_router
from app.api.v1.readiness import router as readiness_router

router = APIRouter()
router.include_router(connect_router)
router.include_router(health_data_router)
router.include_router(readiness_router)
