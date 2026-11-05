from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.authorization import authorized_account_id
from app.auth.jwt_handler import decode_access_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id, email = payload.get("sub"), payload.get("email")
        if not all(isinstance(value, str) and value.strip() for value in (user_id, email)):
            raise ValueError("Missing identity claims")
        return {"user_id": user_id, "email": email}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None


AuthenticatedUser = Annotated[dict, Depends(get_current_user)]


def get_authorized_account(user_id: str, current_user: AuthenticatedUser) -> str:
    return authorized_account_id(current_user["user_id"], user_id)


AuthorizedAccountId = Annotated[str, Depends(get_authorized_account)]
