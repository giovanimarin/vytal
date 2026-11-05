import importlib.util
from datetime import date
from pathlib import Path

import pytest
from app.adapters.cloud.local import LocalWarehouseProvider
from app.config.cloud_config import CloudConfig, LocalConfig
from scripts.seed_local_account import seed_account

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("mvp_launcher", ROOT / "scripts/local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


@pytest.mark.parametrize("environment", ["production", "staging", "unknown", "test"])
def test_launcher_refuses_non_local_runtime(monkeypatch, tmp_path, environment):
    monkeypatch.setenv("ENVIRONMENT", environment)
    with pytest.raises(ValueError):
        launcher.local_environment(tmp_path)
    assert not (tmp_path / ".local-vytal").exists()


def test_launcher_reuses_private_keys_sqlite_and_consistent_local_config(monkeypatch, tmp_path):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    first = launcher.local_environment(tmp_path)
    second = launcher.local_environment(tmp_path)
    assert first["SECRET_KEY"] == second["SECRET_KEY"]
    assert first["JWT_SECRET_KEY"] == second["JWT_SECRET_KEY"]
    assert first["JWT_SECRET_KEY"] != first["SECRET_KEY"]
    assert first["ENVIRONMENT"] == "local" and first["ALLOW_DEV_SEED"] == "false"
    assert Path(first["CONFIG_PATH"]).is_file()
    assert launcher.python_path(tmp_path).parent.parent == tmp_path / ".venv"


def test_launcher_refuses_managed_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("K_SERVICE", "synthetic-service")
    with pytest.raises(ValueError):
        launcher.local_environment(tmp_path)


@pytest.fixture
async def warehouse(monkeypatch, tmp_path):
    from app.adapters.cloud import factory
    from app.config import cloud_config

    config = LocalConfig(db_path=str(tmp_path / "demo.db"))
    wh = LocalWarehouseProvider(config)
    await wh.init_schema()
    monkeypatch.setattr(factory, "_warehouse", wh)
    monkeypatch.setattr(cloud_config, "_cloud_config", CloudConfig(local=config))
    for account in ("A", "B"):
        await wh.insert("users", [{"user_id": account, "email": account + "@example.invalid", "name": account,
                                  "password_hash": "synthetic-unused", "created_at": "2026-01-15", "updated_at": "2026-01-15"}])
    return wh


async def test_demo_generation_is_idempotent_account_scoped_and_uses_existing_formulas(warehouse):
    for _ in range(2):
        assert await seed_account("A@example.invalid", date(2026, 1, 15), 3) == 3
    assert len(await warehouse.query("SELECT * FROM raw_health_events")) == 15
    assert len(await warehouse.query("SELECT * FROM normalized_sleep")) == 3
    assert len(await warehouse.query("SELECT * FROM fact_daily_readiness WHERE user_id='A'")) == 3
    assert await warehouse.query("SELECT * FROM fact_daily_readiness WHERE user_id='B'") == []
    assert all(r["provider"] == "local_demo" for r in await warehouse.query("SELECT * FROM raw_health_events"))


async def test_demo_refuses_missing_account_or_existing_non_demo_records(warehouse):
    with pytest.raises(ValueError, match="Create a local account"):
        await seed_account("missing@example.invalid", date(2026, 1, 15), 1)
    await warehouse.insert("normalized_sleep", [{"record_id": "real-placeholder", "user_id": "A", "date": "2026-01-15"}])
    with pytest.raises(ValueError, match="refuses to mix"):
        await seed_account("A@example.invalid", date(2026, 1, 15), 1)
    assert await warehouse.query("SELECT * FROM raw_health_events") == []


async def test_demo_rejects_production_before_writes(monkeypatch, warehouse):
    from app.config.settings import settings
    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(ValueError, match="local environment"):
        await seed_account("A@example.invalid", date(2026, 1, 15), 1)
    assert await warehouse.query("SELECT * FROM raw_health_events") == []


async def test_demo_refuses_unprocessed_non_demo_raw_events(warehouse):
    await warehouse.insert("raw_health_events", [{"event_id": "non-demo", "user_id": "A", "provider": "google_fit",
        "metric_type": "sleep", "raw_payload": "{}", "collected_at": "2026-01-15T00:00:00+00:00",
        "ingested_at": "2026-01-15T00:00:00+00:00", "pipeline_run": "synthetic"}])
    with pytest.raises(ValueError, match="refuses to mix"):
        await seed_account("A@example.invalid", date(2026, 1, 15), 1)
    assert await warehouse.query("SELECT * FROM normalized_sleep") == []


@pytest.mark.parametrize("component", ["backend", "web", "android"])
def test_launcher_command_ports_and_offline_android_are_reproducible(monkeypatch, tmp_path, component):
    from unittest.mock import Mock

    executable = tmp_path / "python"
    executable.touch()
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "python_path", lambda: executable)
    monkeypatch.setattr(launcher, "local_environment", lambda: {"ENVIRONMENT": "local"})
    monkeypatch.setattr(launcher.shutil, "which", lambda _: "npm")
    monkeypatch.setattr(launcher.sys, "argv", ["local.py", component])
    run = Mock()
    monkeypatch.setattr(launcher.subprocess, "run", run)
    launcher.main()
    command = run.call_args.args[0]
    env = run.call_args.kwargs["env"]
    if component == "backend":
        assert command[-4:] == ["--host", "127.0.0.1", "--port", "8000"]
    elif component == "web":
        assert command == ["npm", "run", "dev"]
        assert env["VYTAL_BACKEND_URL"] == "http://127.0.0.1:8000"
        assert env["NEXT_TELEMETRY_DISABLED"] == "1"
    else:
        assert command == ["npm", "start", "--", "--go", "--localhost"]
        assert env["EXPO_OFFLINE"] == "1"
        assert env["EXPO_PUBLIC_API_URL"] == "http://10.0.2.2:8000/api/v1"
