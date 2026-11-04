from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.adapters.cloud.factory import get_warehouse
from app.auth.jwt_handler import create_access_token
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.token_repo = RefreshTokenRepository()

    async def register(self, email: str, password: str, name: str) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email já cadastrado",
            )
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Senha deve ter ao menos 8 caracteres",
            )
        user = await self.user_repo.create(email, password, name)
        # Also insert into dim_user for analytics
        wh = get_warehouse()
        await wh.insert("dim_user", [{
            "user_id": user["user_id"],
            "provider": "email",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }])
        access_token = create_access_token(user["user_id"], user["email"])
        refresh_token = await self.token_repo.create(user["user_id"])
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.verify_credentials(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
            )
        access_token = create_access_token(user["user_id"], user["email"])
        refresh_token = await self.token_repo.create(user["user_id"])
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh(self, raw_refresh_token: str) -> dict:
        token_row = await self.token_repo.get_by_token(raw_refresh_token)
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado",
            )
        user = await self.user_repo.get_by_id(token_row["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
            )
        await self.token_repo.revoke(raw_refresh_token)
        access_token = create_access_token(user["user_id"], user["email"])
        new_refresh_token = await self.token_repo.create(user["user_id"])
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, raw_refresh_token: str) -> None:
        await self.token_repo.revoke(raw_refresh_token)
