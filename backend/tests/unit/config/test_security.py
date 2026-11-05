import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from app.config.cloud_config import load_cloud_config
from app.config.safe_logging import log_discarded_event
from app.config.security import ConfigurationError, environment_name
from app.config.settings import Settings
from pydantic import ValidationError


def config(**changes):
    values = {"environment": "production", "google_client_id": "synthetic-client",
              "google_client_secret": secrets.token_urlsafe(32), "secret_key": secrets.token_urlsafe(48),
              "jwt_secret_key": secrets.token_urlsafe(48), "google_redirect_uri": "https://app.example.invalid/oauth",
              "config_path": "/not-read-by-pure-settings-test.yaml"}
    values.update(changes)
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize("environment", ["production", "staging", "prod", "PRODUCTION"])
def test_valid_secure_environment(environment):
    settings = config(environment=environment)
    assert settings.environment == environment.lower()
    assert not settings.allow_dev_seed
    assert settings.cors_origins == []


@pytest.mark.parametrize("environment", [None, "", "prodution", "preview", "unknown"])
def test_environment_has_no_silent_development_fallback(environment):
    with pytest.raises(ConfigurationError):
        environment_name(environment)


@pytest.mark.parametrize("field", ["secret_key", "jwt_secret_key"])
@pytest.mark.parametrize("value", [None, "", " ", "dev-secret-change-in-prod", "dev-secret-change-in-production",
                                  "change-me", "test-secret-key", "your-secret"])
def test_production_rejects_missing_or_known_unsafe_signing_keys(field, value):
    with pytest.raises(ValidationError):
        config(**{field: value})


@pytest.mark.parametrize("changes", [
    {"google_client_secret": "your-client-secret"}, {"google_client_id": ""},
    {"google_redirect_uri": None}, {"google_redirect_uri": "http://localhost:8000/callback"},
    {"google_redirect_uri": "https://127.0.0.1/callback"},
    {"google_redirect_uri": "https://[::ffff:127.0.0.1]/callback"},
    {"google_redirect_uri": "https://user:synthetic-marker@app.example.invalid/callback"},
    {"cors_origins": ["*"]}, {"cors_origins": ["https://*"]},
    {"cors_origins": ["http://localhost:3000"]}, {"allow_dev_seed": True},
    {"demo_password": "synthetic-password"}, {"jwt_algorithm": "none"},
    {"access_token_expire_minutes": 0}, {"refresh_token_expire_days": -1}, {"config_path": None},
])
def test_production_rejects_unsafe_configuration(changes):
    with pytest.raises(ValidationError):
        config(**changes)


def test_explicit_https_cors_allowed():
    assert config(cors_origins=["https://app.example.invalid"]).cors_origins == ["https://app.example.invalid"]


def test_local_and_test_generate_distinct_ephemeral_keys_when_omitted():
    first = config(environment="test", secret_key=None, jwt_secret_key=None)
    second = config(environment="local", secret_key=None, jwt_secret_key=None)
    assert first.secret_key != second.secret_key
    assert first.jwt_secret_key != second.jwt_secret_key
    assert first.secret_key != first.jwt_secret_key


def test_local_seed_requires_opt_in_and_explicit_password():
    assert not config(environment="test").allow_dev_seed
    with pytest.raises(ValidationError):
        config(environment="test", allow_dev_seed=True, demo_password=None)
    assert config(environment="test", allow_dev_seed=True, demo_password="synthetic-local-password").allow_dev_seed


def test_secrets_are_masked_in_repr_json_logs_and_errors(caplog):
    marker = "SYNTHETIC_PRIVATE_CONFIG_MARKER"
    settings = config(secret_key=marker, jwt_secret_key=marker, google_client_secret=marker)
    with caplog.at_level(logging.INFO):
        logging.getLogger(__name__).info("settings=%r", settings)
    assert marker not in repr(settings)
    assert marker not in settings.model_dump_json()
    assert marker not in caplog.text
    with pytest.raises(ValidationError) as error:
        config(google_redirect_uri=f"https://user:{marker}@example.invalid")
    assert marker not in str(error.value)


def test_discard_logging_does_not_include_payload_or_untrusted_stage(caplog):
    marker = "SYNTHETIC_CREDENTIAL_LOG_MARKER"
    with caplog.at_level(logging.WARNING):
        log_discarded_event({"access_token": marker, "nested": {"client_secret": marker}}, marker)
    assert marker not in caplog.text
    assert "unknown" in caplog.text


def test_strict_config_does_not_fall_back_to_local_storage(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ConfigurationError):
        load_cloud_config(str(missing), strict=True)
    assert load_cloud_config(str(missing)).provider == "local"
    path = tmp_path / "provider.yaml"
    path.write_text("local:\n  db_path: ignored.db\n")
    with pytest.raises(ConfigurationError):
        load_cloud_config(str(path), strict=True)
    path.write_text("cloud:\n  provider: local\n")
    assert load_cloud_config(str(path), strict=True).provider == "local"


def test_copied_dotenv_cannot_select_development_environment(tmp_path):
    (tmp_path / ".env").write_text("ENVIRONMENT=local\nSECRET_KEY=SYNTHETIC_PRIVATE_CONFIG_MARKER\n")
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[3]))
    env.pop("ENVIRONMENT", None)
    result = subprocess.run([sys.executable, "-c", "import app.config.settings"], cwd=tmp_path,
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "ENVIRONMENT" in result.stderr
    assert "SYNTHETIC_PRIVATE_CONFIG_MARKER" not in result.stderr


async def test_production_seed_is_rejected_before_database_access(monkeypatch):
    from app.api.v1 import dev_seed
    from fastapi import HTTPException

    monkeypatch.setattr(dev_seed, "settings", config())
    service = Mock(side_effect=AssertionError("Seed must not access accounts"))
    monkeypatch.setattr(dev_seed, "AuthService", service)
    with pytest.raises(HTTPException) as error:
        await dev_seed.seed_demo_data()
    assert error.value.status_code == 403
    service.assert_not_called()


async def test_provider_error_body_cannot_reach_logs(monkeypatch, caplog):
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock

    import httpx
    from app.adapters.connectors.base import OAuthToken
    from app.adapters.connectors.google_fit import GoogleFitAdapter

    marker = "SYNTHETIC_PROVIDER_SECRET_MARKER"
    response = httpx.Response(400, text=marker)
    client = AsyncMock()
    client.post.return_value = response
    context = Mock()
    context.__aenter__ = AsyncMock(return_value=client)
    context.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(httpx, "AsyncClient", Mock(return_value=context))
    token = OAuthToken(marker, None, datetime(2099, 1, 1, tzinfo=UTC), "google_fit", "A")
    with caplog.at_level(logging.WARNING):
        assert await GoogleFitAdapter()._fetch_aggregate(token, [], 0, 1) == {}
    assert "status=400" in caplog.text
    assert marker not in caplog.text


def test_managed_runtime_cannot_select_local_mode(monkeypatch):
    from app.config.settings import load_settings
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("K_SERVICE", "synthetic-managed-service")
    with pytest.raises(ConfigurationError, match="production/staging"):
        load_settings()


def test_production_ignores_development_dotenv_and_does_not_log_invalid_env_values(monkeypatch, tmp_path):
    from app.config.settings import load_settings
    marker = "SYNTHETIC_PRIVATE_CONFIG_MARKER"
    values = config()
    for name in ("environment", "google_client_id", "google_redirect_uri", "config_path"):
        monkeypatch.setenv(name.upper(), getattr(values, name))
    for name in ("google_client_secret", "secret_key", "jwt_secret_key"):
        monkeypatch.setenv(name.upper(), getattr(values, name).get_secret_value())
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ALLOW_DEV_SEED=true\nJWT_SECRET_KEY=change-me\n")
    assert not load_settings().allow_dev_seed
    monkeypatch.setenv("CORS_ORIGINS", marker)
    with pytest.raises(ConfigurationError) as error:
        load_settings()
    assert marker not in str(error.value)


def test_startup_validation_reports_only_field_names(monkeypatch):
    from app.config.settings import load_settings
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ConfigurationError) as error:
        load_settings()
    assert "SECRET_KEY" in str(error.value)


@pytest.mark.parametrize("yaml_text", ["local: []", "gcp: []", "local:\n  unexpected: private-marker"])
def test_cloud_configuration_shape_errors_do_not_echo_values(tmp_path, yaml_text):
    path = tmp_path / "config.yaml"
    path.write_text("cloud:\n  provider: local\n" + yaml_text)
    with pytest.raises(ConfigurationError) as error:
        load_cloud_config(str(path), strict=True)
    assert "private-marker" not in str(error.value)


def test_parse_pipeline_does_not_log_rejected_event_or_exception_values(monkeypatch, caplog):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[4]))
    from pipelines.transforms.sanitize import ParseRawEvent

    marker = "SYNTHETIC_PIPELINE_SECRET_MARKER"
    with caplog.at_level(logging.WARNING):
        rejected = list(ParseRawEvent().process({"event_id": marker, "access_token": marker}))
        for event in rejected:
            log_discarded_event(event.value, "parse")
    assert len(rejected) == 1
    assert marker not in caplog.text
    assert "Failed to parse" in caplog.text


def test_readiness_pipeline_does_not_log_exception_values(monkeypatch, caplog):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[4]))
    from pipelines.transforms import readiness

    marker = "SYNTHETIC_PIPELINE_SECRET_MARKER"
    transform = readiness.CalculateReadiness()
    monkeypatch.setattr(transform, "_calculate", Mock(return_value=None))
    loop = Mock()
    loop.run_until_complete.side_effect = ValueError(marker)
    monkeypatch.setattr(readiness.asyncio, "get_event_loop", Mock(return_value=loop))
    with caplog.at_level(logging.ERROR):
        rejected = list(transform.process(("A", "2026-01-15")))
    assert len(rejected) == 1
    assert marker not in caplog.text
    assert "ValueError" in caplog.text
