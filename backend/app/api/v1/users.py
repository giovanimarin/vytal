import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["users"])
_user_repo = UserRepository()


def _deserialize_user(user: dict) -> dict:
    raw = user.get("preferred_modalities")
    if raw and isinstance(raw, str):
        try:
            user["preferred_modalities"] = json.loads(raw)
        except Exception:
            user["preferred_modalities"] = []
    elif not raw:
        user["preferred_modalities"] = []
    return user


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    goal: Optional[str] = None
    gender: Optional[str] = None
    preferred_modalities: Optional[List[str]] = None


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await _user_repo.get_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    user.pop("password_hash", None)
    return _deserialize_user(user)


@router.patch("/me")
async def update_me(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "preferred_modalities" in data:
        data["preferred_modalities"] = json.dumps(data["preferred_modalities"])
    user = await _user_repo.update_profile(current_user["user_id"], data)
    if user:
        user.pop("password_hash", None)
    return _deserialize_user(user)
