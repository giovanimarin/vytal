from fastapi import APIRouter
from pydantic import BaseModel

from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
_service = AuthService()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    return await _service.register(body.email, body.password, body.name)


@router.post("/login")
async def login(body: LoginRequest):
    return await _service.login(body.email, body.password)


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    return await _service.refresh(body.refresh_token)


@router.post("/logout")
async def logout(body: LogoutRequest):
    await _service.logout(body.refresh_token)
    return {"ok": True}
