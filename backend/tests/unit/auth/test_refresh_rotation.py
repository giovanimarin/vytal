import asyncio
import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.adapters.cloud.local import LocalWarehouseProvider
from app.auth.jwt_handler import decode_access_token
from app.config.cloud_config import LocalConfig
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.services.auth_service import AuthService
from fastapi import HTTPException


@pytest.fixture
async def service(tmp_path):
    warehouse = LocalWarehouseProvider(LocalConfig(db_path=str(tmp_path / "auth.db")))
    await warehouse.init_schema()
    repository = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repository.wh = warehouse
    service = AuthService.__new__(AuthService)
    service.token_repo = repository
    service.user_repo = AsyncMock()
    service.user_repo.get_by_id.return_value = {"user_id": "A", "email": "A@example.invalid"}
    return service


async def test_concurrent_refresh_has_exactly_one_winner_across_repository_instances(service):
    raw = await service.token_repo.create("A")
    second = AuthService.__new__(AuthService)
    second.token_repo = RefreshTokenRepository.__new__(RefreshTokenRepository)
    second.token_repo.wh = service.token_repo.wh
    second.user_repo = service.user_repo
    # Force both contenders past the old read-before-revoke boundary.
    ready = asyncio.Event()
    count = 0
    for repo in (service.token_repo, second.token_repo):
        original = repo.get_by_token
        async def read(token, original=original):
            nonlocal count
            result = await original(token)
            count += 1
            if count == 2:
                ready.set()
            await ready.wait()
            return result
        repo.get_by_token = read
    results = await asyncio.gather(service.refresh(raw), second.refresh(raw), return_exceptions=True)
    winners = [r for r in results if isinstance(r, dict)]
    denied = [r for r in results if isinstance(r, HTTPException)]
    assert len(winners) == len(denied) == 1
    assert denied[0].status_code == 401
    assert decode_access_token(winners[0]["access_token"])["sub"] == "A"
    assert await service.token_repo.get_by_token(raw) is None
    assert await service.token_repo.get_by_token(winners[0]["refresh_token"])


async def test_rotation_replay_and_logout(service):
    raw = await service.token_repo.create("A")
    new = await service.refresh(raw)
    with pytest.raises(HTTPException) as error:
        await service.refresh(raw)
    assert error.value.status_code == 401
    assert await service.token_repo.get_by_token(new["refresh_token"])
    await service.logout(new["refresh_token"])
    with pytest.raises(HTTPException) as error:
        await service.refresh(new["refresh_token"])
    assert error.value.status_code == 401


@pytest.mark.parametrize("state", ["expired", "revoked", "wrong-owner", "unknown"])
async def test_unusable_refresh_cannot_rotate(service, state):
    raw = await service.token_repo.create("A")
    if state == "expired":
        await service.token_repo.wh.query("UPDATE refresh_tokens SET expires_at = :end",
                                         {"end": (datetime.now(UTC) - timedelta(days=1)).isoformat()})
    elif state == "revoked":
        await service.logout(raw)
    elif state == "unknown":
        raw = "not-issued"
    owner = "B" if state == "wrong-owner" else "A"
    before = await service.token_repo.wh.query("SELECT * FROM refresh_tokens")
    assert await service.token_repo.rotate(raw, owner) is None
    assert await service.token_repo.wh.query("SELECT * FROM refresh_tokens") == before


async def test_failed_atomic_update_preserves_original_credential(service):
    raw = await service.token_repo.create("A")
    service.token_repo.wh.execute_affected = AsyncMock(side_effect=RuntimeError("synthetic storage failure"))
    with pytest.raises(RuntimeError):
        await service.refresh(raw)
    assert await service.token_repo.get_by_token(raw)


async def test_missing_user_cannot_receive_replacement(service):
    raw = await service.token_repo.create("A")
    service.user_repo.get_by_id.return_value = None
    with pytest.raises(HTTPException) as error:
        await service.refresh(raw)
    assert error.value.status_code == 401


async def test_bigquery_conditional_update_binds_parameters_without_network(monkeypatch):
    sdk = ModuleType("google.cloud.bigquery")
    sdk.QueryJobConfig = lambda **kwargs: SimpleNamespace(**kwargs)
    sdk.ScalarQueryParameter = lambda name, kind, value: SimpleNamespace(name=name, value=value, kind=kind)
    cloud = ModuleType("google.cloud")
    cloud.bigquery = sdk
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", sdk)
    from app.adapters.cloud.gcp import BigQueryWarehouseProvider
    provider = BigQueryWarehouseProvider.__new__(BigQueryWarehouseProvider)
    provider.project, provider.dataset = "synthetic", "vytal"
    provider.client = Mock()
    provider.client.query.return_value.num_dml_affected_rows = 1
    assert await provider.execute_affected("UPDATE refresh_tokens SET token_hash=:new WHERE token_hash=:old",
                                           {"new": "synthetic-new", "old": "synthetic-old"}) == 1
    sql = provider.client.query.call_args.args[0]
    assert "@new" in sql and "@old" in sql and "synthetic-old" not in sql
    config = provider.client.query.call_args.kwargs["job_config"]
    assert [p.value for p in config.query_parameters] == ["synthetic-new", "synthetic-old"]
