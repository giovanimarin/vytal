import json
import sqlite3
from pathlib import Path

import pytest
from scripts.check_v1_contract import assert_compatible, contract
from scripts.sqlite_contract import sqlite_contract

FIXTURES = Path(__file__).parent / "fixtures"


def test_live_openapi_matches_committed_baseline(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(f"cloud:\n  provider: local\nlocal:\n  data_dir: {tmp_path}\n  db_path: {tmp_path}/openapi.db\n")
    backend = Path(__file__).resolve().parents[2]
    assert_compatible(json.loads((FIXTURES / "openapi-v1.json").read_text()), contract(backend, config))


def test_all_16_sqlite_tables_columns_keys_defaults_indexes_and_fk_match_baseline():
    expected = json.loads((FIXTURES / "sqlite-schema.json").read_text())
    actual = sqlite_contract()
    assert len(actual["tables"]) == 16
    assert actual == expected


@pytest.fixture
def warehouse(tmp_path):
    from app.adapters.cloud.local import LocalWarehouseProvider
    from app.config.cloud_config import LocalConfig
    return LocalWarehouseProvider(LocalConfig(db_path=str(tmp_path / "isolated.db")))


@pytest.mark.parametrize("table,first,second,where", [
    ("users", {"user_id": "A", "email": "A@example.invalid", "name": "A", "password_hash": "synthetic", "created_at": "2026-01-15", "updated_at": "2026-01-15"},
     {"user_id": "B", "email": "A@example.invalid", "name": "B", "password_hash": "synthetic", "created_at": "2026-01-15", "updated_at": "2026-01-15"}, "email"),
    ("wellness_feedback", {"feedback_id": "f1", "user_id": "A", "date": "2026-01-15", "created_at": "2026-01-15", "notes": "first"},
     {"feedback_id": "f2", "user_id": "A", "date": "2026-01-15", "created_at": "2026-01-15", "notes": "second"}, "user_id"),
    ("oauth_tokens", {"user_id": "A", "provider": "google_fit", "access_token": "synthetic-first", "expires_at": "2099-01-01T00:00:00+00:00"},
     {"user_id": "A", "provider": "google_fit", "access_token": "synthetic-second", "expires_at": "2099-01-01T00:00:00+00:00"}, "user_id"),
])
async def test_current_insert_or_replace_semantics_are_characterized(warehouse, table, first, second, where):
    await warehouse.init_schema()
    await warehouse.insert(table, [first])
    await warehouse.insert(table, [second])
    rows = await warehouse.query(f"SELECT * FROM {table} WHERE {where} = ?", [second[where]])
    assert len(rows) == 1
    for key, value in second.items():
        assert rows[0][key] == value


async def test_workout_foreign_key_is_declared_but_not_enabled_currently(warehouse):
    await warehouse.init_schema()
    await warehouse.insert("workout_exercises", [{"exercise_id": "orphan", "workout_id": "missing", "name": "synthetic", "muscle_groups": "[]"}])
    with sqlite3.connect(warehouse.db_path) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 0
        assert len(db.execute("PRAGMA foreign_key_check").fetchall()) == 1


async def test_failed_batch_rolls_back_earlier_rows_of_same_insert_call(warehouse):
    await warehouse.init_schema()
    rows = [{"workout_id": "w1", "user_id": "A", "date": "2026-01-15", "modality": "corrida", "intensity": "leve", "duration_min": 20, "created_at": "2026-01-15"},
            {"workout_id": "w2", "user_id": None, "date": "2026-01-15", "modality": "corrida", "intensity": "leve", "duration_min": 20, "created_at": "2026-01-15"}]
    with pytest.raises(sqlite3.IntegrityError):
        await warehouse.insert("workout_history", rows)
    assert await warehouse.query("SELECT * FROM workout_history") == []


async def test_failure_in_second_repository_call_does_not_undo_first_commit(warehouse):
    await warehouse.init_schema()
    await warehouse.insert("workout_history", [{"workout_id": "w1", "user_id": "A", "date": "2026-01-15", "modality": "corrida", "intensity": "leve", "duration_min": 20, "created_at": "2026-01-15"}])
    with pytest.raises(sqlite3.IntegrityError):
        await warehouse.insert("workout_exercises", [{"exercise_id": "e1", "workout_id": "w1", "name": None, "muscle_groups": "[]"}])
    assert len(await warehouse.query("SELECT * FROM workout_history")) == 1
    assert await warehouse.query("SELECT * FROM workout_exercises") == []
