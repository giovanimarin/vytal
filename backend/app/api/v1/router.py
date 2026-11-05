from fastapi import APIRouter, Depends

from app.api.v1.auth import router as auth_router
from app.api.v1.connect import router as connect_router
from app.api.v1.dev_seed import router as dev_seed_router
from app.api.v1.health_connect import router as health_connect_router
from app.api.v1.health_data import router as health_data_router
from app.api.v1.modality_readiness import router as modality_readiness_router
from app.api.v1.muscles import router as muscles_router
from app.api.v1.readiness import router as readiness_router
from app.api.v1.users import router as users_router
from app.api.v1.wellness_feedback import router as wellness_feedback_router
from app.api.v1.workouts import router as workouts_router
from app.auth.dependencies import get_current_user

router = APIRouter()
router.include_router(health_connect_router)
router.include_router(dev_seed_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(connect_router, dependencies=[Depends(get_current_user)])
router.include_router(health_data_router, dependencies=[Depends(get_current_user)])
router.include_router(readiness_router, dependencies=[Depends(get_current_user)])
router.include_router(modality_readiness_router, dependencies=[Depends(get_current_user)])
router.include_router(workouts_router, dependencies=[Depends(get_current_user)])
router.include_router(muscles_router, dependencies=[Depends(get_current_user)])
router.include_router(wellness_feedback_router, dependencies=[Depends(get_current_user)])
