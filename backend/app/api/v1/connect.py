from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config.settings import settings
from app.services.oauth_service import OAuthService

router = APIRouter(prefix="/connect", tags=["connect"])
_service = OAuthService()


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


@router.get("/{provider}/auth-url")
async def get_auth_url(provider: str, user_id: str, redirect_uri: str = None):
    """Retorna a URL de autorização OAuth do provider."""
    redirect_uri = redirect_uri or settings.google_redirect_uri
    try:
        url, state = _service.get_auth_url(provider, user_id, redirect_uri)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"auth_url": url, "state": state}


@router.get("/{provider}/callback")
async def oauth_callback_get(provider: str, code: str, state: str):
    """Callback GET — recebido diretamente do browser após autorização OAuth."""
    try:
        token = await _service.handle_callback(
            provider=provider,
            code=code,
            state=state,
            redirect_uri=settings.google_redirect_uri,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "user_id": token.user_id,
        "provider": token.provider,
        "connected": True,
        "connected_at": token.expires_at.isoformat(),
        "message": "Conta conectada com sucesso! Pode fechar esta aba.",
    }


@router.post("/{provider}/callback")
async def oauth_callback(provider: str, body: OAuthCallbackRequest):
    """Troca o authorization code pelo token e persiste."""
    try:
        token = await _service.handle_callback(
            provider=provider,
            code=body.code,
            state=body.state,
            redirect_uri=body.redirect_uri,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "user_id": token.user_id,
        "provider": token.provider,
        "connected": True,
        "connected_at": token.expires_at.isoformat(),
    }
