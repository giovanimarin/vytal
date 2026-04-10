from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["users"])
_user_repo = UserRepository()


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    goal: Optional[str] = None


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await _user_repo.get_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    user.pop("password_hash", None)
    return user


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    user = await _user_repo.update_profile(current_user["user_id"], fields)
    if user:
        user.pop("password_hash", None)
    return user
