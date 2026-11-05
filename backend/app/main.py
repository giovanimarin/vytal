from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.cloud.factory import init_warehouse
from app.api.v1.router import router as v1_router
from app.auth.authorization import AccountAccessDenied


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o warehouse (cria tabelas SQLite em modo local)
    await init_warehouse()
    yield


app = FastAPI(
    title="Vytal API",
    version="0.1.0",
    description="Health analytics for everyday smartwatch users.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(AccountAccessDenied)
async def account_access_denied_handler(request: Request, exc: AccountAccessDenied):
    return JSONResponse(status_code=404, content={"detail": "Not found"})
