from datetime import UTC, date, datetime, time
from decimal import Decimal
from unittest.mock import Mock

import pytest
from app.adapters.cloud.gcp import BigQueryWarehouseProvider
from app.repositories.refresh_token_repo import RefreshTokenRepository
from google.cloud import bigquery


@pytest.fixture
def provider():
    provider = BigQueryWarehouseProvider.__new__(BigQueryWarehouseProvider)
    provider.project, provider.dataset = "synthetic-project", "vytal"
    provider.client = Mock()
    provider.client.query.return_value.result.return_value = [{"user_id": "A"}]
    provider.client.query.return_value.num_dml_affected_rows = 1
    return provider


async def test_read_binds_named_values_and_default_dataset(provider):
    result = await provider.query("SELECT * FROM refresh_tokens WHERE token_hash = :hash", {"hash": "synthetic"})
    assert result == [{"user_id": "A"}]
    call = provider.client.query.call_args
    assert call.args[0] == "SELECT * FROM refresh_tokens WHERE token_hash = @hash"
    config = call.kwargs["job_config"]
    assert config.use_legacy_sql is False
    assert config.default_dataset.project == "synthetic-project"
    assert config.default_dataset.dataset_id == "vytal"
    assert config.query_parameters[0].to_api_repr() == bigquery.ScalarQueryParameter("hash", "STRING", "synthetic").to_api_repr()


async def test_positional_binding_supports_logout_without_interpolation(provider):
    await provider.query("UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?", ["not-sql' OR 1=1"])
    call = provider.client.query.call_args
    assert call.args[0].endswith("token_hash = ?")
    params = call.kwargs["job_config"].query_parameters
    assert params[0].name is None
    assert params[0].value == "not-sql' OR 1=1"
    assert call.kwargs["job_config"].to_api_repr()["query"]["parameterMode"] == "POSITIONAL"


async def test_dml_preserves_datetime_types_and_repeated_parameters(provider):
    now = datetime(2026, 11, 5, 12, tzinfo=UTC)
    await provider.execute_affected("UPDATE refresh_tokens SET created_at=:now WHERE expires_at>:now", {"now": now})
    call = provider.client.query.call_args
    assert call.args[0] == "UPDATE refresh_tokens SET created_at=@now WHERE expires_at>@now"
    params = call.kwargs["job_config"].query_parameters
    assert len(params) == 1
    assert params[0].type_ == "TIMESTAMP"
    assert params[0].value == now
    assert params[0].to_api_repr()["parameterValue"]["value"] == "2026-11-05 12:00:00+00:00"


@pytest.mark.parametrize(("value", "kind"), [(True, "BOOL"), (3, "INT64"), (2.5, "FLOAT64"),
    ("2026-11-05", "STRING"), (date(2026, 11, 5), "DATE"),
    (datetime(2026, 11, 5, 12), "DATETIME"),
    (b"synthetic", "BYTES"), (Decimal("1.25"), "NUMERIC"), (time(12, 30), "TIME")])
async def test_scalar_types_are_not_all_strings(provider, value, kind):
    await provider.query("SELECT :value", {"value": value})
    param = provider.client.query.call_args.kwargs["job_config"].query_parameters[0]
    assert param.type_ == kind
    assert param.to_api_repr()["parameterType"]["type"] == kind


async def test_refresh_rotation_passes_timestamp_parameters_not_iso_strings(provider):
    repo = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repo.wh = provider
    assert await repo.rotate("synthetic-old", "A")
    params = {p.name: p for p in provider.client.query.call_args.kwargs["job_config"].query_parameters}
    assert params["now"].type_ == params["expires"].type_ == "TIMESTAMP"
    assert isinstance(params["now"].value, datetime)
    assert params["now"].value.tzinfo is not None
    assert params["previous"].type_ == params["replacement"].type_ == params["user_id"].type_ == "STRING"


@pytest.mark.parametrize(("year", "valid"), [(2099, True), (2000, False)])
async def test_native_timestamp_result_is_accepted_by_refresh_repository(provider, year, valid):
    provider.client.query.return_value.result.return_value = [{"expires_at": datetime(year, 1, 1, tzinfo=UTC), "user_id": "A"}]
    repo = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repo.wh = provider
    result = await repo.get_by_token("synthetic")
    assert (result is not None) is valid
    if valid:
        assert result["user_id"] == "A"


async def test_literals_comments_and_system_variables_are_not_parameters(provider):
    sql = '''SELECT ':text ?', "@quoted", `:identifier`, @@project_id,
        \"\"\"triple :unchanged ?\"\"\", :actual
        -- :comment ?
        /* @another ? */ # :last
    '''
    await provider.query(sql, {"actual": "bound"})
    call = provider.client.query.call_args
    assert call.args[0] == sql.replace(":actual", "@actual")
    assert [p.name for p in call.kwargs["job_config"].query_parameters] == ["actual"]


async def test_native_named_bigquery_parameters_are_supported(provider):
    await provider.query("SELECT @name, @name", {"name": "bound"})
    assert provider.client.query.call_args.args[0] == "SELECT @name, @name"
    assert len(provider.client.query.call_args.kwargs["job_config"].query_parameters) == 1


@pytest.mark.parametrize(("sql", "params"), [
    ("SELECT :missing", {}), ("SELECT 1", {"extra": "not-used"}),
    ("SELECT ?", []), ("SELECT :named", ["value"]),
    ("SELECT :named, ?", {"named": "value"}), ("SELECT ?", {"name": "value"}),
])
async def test_parameter_mismatch_fails_before_sending_sql(provider, sql, params):
    with pytest.raises(ValueError):
        await provider.query(sql, params)
    provider.client.query.assert_not_called()


async def test_no_parameters_still_sets_the_default_dataset(provider):
    await provider.query("SELECT 1")
    config = provider.client.query.call_args.kwargs["job_config"]
    assert config.query_parameters == []
    assert config.default_dataset.dataset_id == "vytal"


@pytest.mark.parametrize("count", [0, 1, 2, None])
async def test_affected_count_comes_from_the_completed_dml_job(provider, count):
    job = provider.client.query.return_value
    job.num_dml_affected_rows = count
    assert await provider.execute_affected("UPDATE t SET flag=:value", {"value": 1}) == (count or 0)
    job.result.assert_called_once()
    provider.client.query.assert_called_once()


@pytest.mark.parametrize("count", [0, 2, None])
async def test_rotation_only_accepts_exactly_one_affected_row(provider, count):
    provider.client.query.return_value.num_dml_affected_rows = count
    repo = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repo.wh = provider
    assert await repo.rotate("synthetic-old", "A") is None
    provider.client.query.assert_called_once()


@pytest.mark.parametrize("method", ["query", "execute_affected"])
async def test_job_failure_is_not_reported_as_a_successful_rotation(provider, method):
    provider.client.query.return_value.result.side_effect = RuntimeError("synthetic job failure")
    with pytest.raises(RuntimeError, match="synthetic job failure"):
        await getattr(provider, method)("UPDATE t SET flag=:value", {"value": 1})
    provider.client.query.assert_called_once()


async def test_timestamp_offset_is_normalized_and_null_is_explicit(provider):
    from datetime import timedelta, timezone

    from app.adapters.cloud.base import QueryParameter
    instant = datetime(2026, 11, 5, 9, tzinfo=timezone(timedelta(hours=-3)))
    await provider.query("SELECT :instant, :empty", {"instant": instant, "empty": QueryParameter("TIMESTAMP", None)})
    params = {p.name: p for p in provider.client.query.call_args.kwargs["job_config"].query_parameters}
    assert params["instant"].type_ == "TIMESTAMP"
    assert params["instant"].value == datetime(2026, 11, 5, 12, tzinfo=UTC)
    assert params["instant"].value.tzinfo is UTC
    assert params["empty"].to_api_repr()["parameterType"]["type"] == "TIMESTAMP"
    assert params["empty"].to_api_repr()["parameterValue"]["value"] is None


@pytest.mark.parametrize("kind", ["TIMESTAMP", "DATETIME"])
async def test_temporal_timezone_mismatch_is_rejected(provider, kind):
    from app.adapters.cloud.base import QueryParameter
    value = datetime(2026, 11, 5) if kind == "TIMESTAMP" else datetime(2026, 11, 5, tzinfo=UTC)
    with pytest.raises(ValueError):
        await provider.query("SELECT :instant", {"instant": QueryParameter(kind, value)})
    provider.client.query.assert_not_called()


@pytest.mark.parametrize("value", [None, [], object()])
async def test_ambiguous_values_are_not_silently_stringified(provider, value):
    with pytest.raises(TypeError):
        await provider.query("SELECT :value", {"value": value})
    provider.client.query.assert_not_called()


async def test_bound_temporal_values_match_checked_in_gcp_schema(provider):
    import json
    from pathlib import Path

    schemas = Path(__file__).resolve().parents[4] / "infrastructure/terraform/modules/gcp/bigquery/schemas"
    schema = {field["name"]: field["type"] for field in json.loads((schemas / "dim_user.json").read_text())}
    await provider.query("SELECT :user_id, :date, :created_at", {
        "user_id": "A", "date": date(2026, 11, 5), "created_at": datetime(2026, 11, 5, tzinfo=UTC),
    })
    types = {p.name: p.type_ for p in provider.client.query.call_args.kwargs["job_config"].query_parameters}
    assert types == {name: schema[name] for name in types}


async def test_expired_same_day_sqlite_rotation_stays_denied_with_native_timestamps(tmp_path):
    from datetime import timedelta

    from app.adapters.cloud.local import LocalWarehouseProvider
    from app.config.cloud_config import LocalConfig

    warehouse = LocalWarehouseProvider(LocalConfig(db_path=str(tmp_path / "auth.db")))
    await warehouse.init_schema()
    repo = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repo.wh = warehouse
    raw = await repo.create("A")
    expired = datetime.now(UTC) - timedelta(minutes=1)
    await warehouse.query("UPDATE refresh_tokens SET expires_at=:end", {"end": expired})
    before = await warehouse.query("SELECT * FROM refresh_tokens")
    assert "T" in before[0]["expires_at"]
    assert await repo.rotate(raw, "A") is None
    assert await warehouse.query("SELECT * FROM refresh_tokens") == before


async def test_aware_time_requires_explicit_timezone_removal(provider):
    with pytest.raises(ValueError, match="TIME"):
        await provider.query("SELECT :value", {"value": time(12, tzinfo=UTC)})
    provider.client.query.assert_not_called()
