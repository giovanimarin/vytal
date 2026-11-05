"""Offline schema/SDK checks. These deliberately do NOT emulate BigQuery isolation."""
import copy
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from app.adapters.cloud.gcp import BigQueryWarehouseProvider
from app.repositories.refresh_token_repo import RefreshTokenRepository
from google.cloud import bigquery
from scripts.readiness_audit import (
    audit,
    compare_tables,
    declared_schemas,
    local_columns,
    validate_refresh_schema,
)

ROOT = Path(__file__).resolve().parents[4]
MODULE = ROOT / "infrastructure/terraform/modules/gcp/bigquery"


@pytest.fixture
def candidate():
    return json.loads((MODULE / "schemas/proposed/refresh_tokens.json").read_text())


def test_proposed_schema_matches_local_and_actual_refresh_creation(candidate):
    local = local_columns((ROOT / "backend/app/adapters/cloud/local.py").read_text())
    assert set(local["refresh_tokens"]) == {c["name"] for c in candidate}
    assert validate_refresh_schema(candidate) == []
    assert [f.name for f in bigquery.SchemaField.from_api_repr({"name": "record", "type": "RECORD", "fields": candidate}).fields] == [c["name"] for c in candidate]
    # Candidate is intentionally not wired to Terraform until architecture is approved.
    assert "refresh_tokens" not in declared_schemas(MODULE)


async def test_real_refresh_create_row_matches_candidate_and_contains_only_hashed_credential(candidate):
    repository = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repository.wh = Mock(insert=AsyncMock())
    credential = await repository.create("synthetic-account")
    table, rows = repository.wh.insert.call_args.args
    assert table == "refresh_tokens"
    assert set(rows[0]) == {c["name"] for c in candidate}
    assert credential not in json.dumps(rows)
    assert len(rows[0]["token_hash"]) == 64
    assert isinstance(rows[0]["revoked"], int)
    from datetime import datetime
    assert datetime.fromisoformat(rows[0]["expires_at"]).utcoffset() is not None
    assert datetime.fromisoformat(rows[0]["created_at"]).utcoffset() is not None


@pytest.mark.parametrize("mutation", ["timestamp-as-string", "bool-revoked", "nullable", "missing", "duplicate", "date-partition"])
def test_candidate_rejects_schema_changes_that_break_repository_contract(candidate, mutation):
    bad = copy.deepcopy(candidate)
    if mutation == "timestamp-as-string":
        next(c for c in bad if c["name"] == "expires_at")["type"] = "STRING"
    elif mutation == "bool-revoked":
        next(c for c in bad if c["name"] == "revoked")["type"] = "BOOL"
    elif mutation == "nullable":
        bad[0]["mode"] = "NULLABLE"
    elif mutation == "missing":
        bad.pop()
    elif mutation == "duplicate":
        bad.append(copy.deepcopy(bad[0]))
    else:
        bad.append({"name": "date", "type": "DATE", "mode": "REQUIRED"})
    assert validate_refresh_schema(bad)


def test_table_comparison_detects_missing_writes_and_required_columns():
    local = {"refresh_tokens": {"token_hash"}, "dim_user": {"user_id", "created_at"}}
    declared = {"dim_user": [{"name": "user_id", "mode": "REQUIRED"}, {"name": "date", "mode": "REQUIRED"}]}
    findings = compare_tables(local, declared)
    mismatch = next(f for f in findings if f["id"] == "column-mismatch")
    assert mismatch["missing_columns"] == ["created_at"]
    assert mismatch["extra_required_columns"] == ["date"]
    assert any(f["id"] == "missing-table" and f["table"] == "refresh_tokens" for f in findings)
    assert compare_tables({"t": {"id"}}, {"t": [{"name": "id", "mode": "REQUIRED"}]}) == []


def test_repository_audit_never_claims_cloud_or_concurrency_validation():
    result = audit(ROOT)
    assert result["scope"] == "offline-static-only"
    assert not result["gcp_validated"] and not result["ready_for_deploy"]
    assert any(f["id"] == "refresh-concurrency-unverified" for f in result["findings"])


@pytest.fixture
def provider():
    result = BigQueryWarehouseProvider.__new__(BigQueryWarehouseProvider)
    result.project, result.dataset = "synthetic-project", "synthetic_dataset"
    result.client = Mock()
    return result


async def test_streaming_api_is_exposed_as_readiness_risk_not_mocked_as_dml_safe(provider):
    provider.client.insert_rows_json.return_value = []
    assert await provider.insert("refresh_tokens", [{"revoked": 0}]) == 1
    provider.client.insert_rows_json.assert_called_once_with(
        "synthetic-project.synthetic_dataset.refresh_tokens", [{"revoked": 0}])
    provider.client.query.assert_not_called()


async def test_dml_conflict_propagates_without_issuing_replacement_credential(provider):
    from google.api_core.exceptions import Conflict

    provider.client.query.return_value.result.side_effect = Conflict("synthetic conflict")
    repository = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repository.wh = provider
    with pytest.raises(Conflict):
        await repository.rotate("synthetic-old", "synthetic-account")
    assert provider.client.query.call_count == 1
    provider.client.insert_rows_json.assert_not_called()


@pytest.mark.parametrize("rows", [0, None, 2])
async def test_unknown_or_duplicate_dml_count_never_returns_a_rotated_credential(provider, rows):
    provider.client.query.return_value.num_dml_affected_rows = rows
    repository = RefreshTokenRepository.__new__(RefreshTokenRepository)
    repository.wh = provider
    assert await repository.rotate("synthetic-old", "synthetic-account") is None


async def test_provider_insert_errors_cannot_expose_sensitive_response_details(provider):
    marker = "SYNTHETIC_PRIVATE_RESPONSE_MARKER"
    provider.client.insert_rows_json.return_value = [{"errors": [{"message": marker}], "row": {"token": marker}}]
    with pytest.raises(RuntimeError) as error:
        await provider.insert("refresh_tokens", [{"revoked": 0}])
    assert marker not in str(error.value)


@pytest.mark.parametrize("native", [True, False])
async def test_oauth_repository_accepts_native_gcp_timestamp_and_existing_iso_format(native, monkeypatch):
    from datetime import UTC, datetime

    from app.repositories import token_repo

    expires = datetime(2099, 1, 1, tzinfo=UTC)
    warehouse = Mock(query=AsyncMock(return_value=[{
        "access_token": "synthetic", "refresh_token": "synthetic", "provider": "google_fit",
        "user_id": "synthetic-account", "expires_at": expires if native else expires.isoformat(),
    }]))
    monkeypatch.setattr(token_repo, "get_warehouse", lambda: warehouse)
    token = await token_repo.TokenRepository().get("synthetic-account", "google_fit")
    assert token.expires_at == expires
    assert token.user_id == "synthetic-account"


def test_readiness_cli_without_any_runtime_credentials_reports_blocked():
    import os
    import subprocess
    import sys

    result = subprocess.run([sys.executable, str(ROOT / "backend/scripts/readiness_audit.py"), "--check"],
                            env={"PATH": os.defpath}, capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["findings"] and not report["ready_for_deploy"]
    assert not report["gcp_validated"]


def test_all_committed_terraform_source_parses_without_provider_access():
    import hcl2

    for path in (ROOT / "infrastructure/terraform").rglob("*.tf"):
        with path.open() as source:
            assert hcl2.load(source)
