"""Launcher state regression: preserve the original SQLite and auth keys."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('vytal_android_local', Path(__file__).parents[1] / 'scripts/android/local.py')
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)


@pytest.fixture
def root(tmp_path, monkeypatch):
    for name in ('ENVIRONMENT', 'K_SERVICE', 'CONFIG_PATH', 'SECRET_KEY', 'JWT_SECRET_KEY'):
        monkeypatch.delenv(name, raising=False)
    backend = tmp_path / 'backend'
    backend.mkdir()
    (backend / 'config.yaml').write_text('cloud:\n  provider: local\nlocal:\n  db_path: data/vytal.db\n')
    (backend / 'data').mkdir()
    (backend / 'data/vytal.db').write_bytes(b'EXISTING_USER_DATABASE')
    return tmp_path


def test_restart_reuses_database_and_secrets(root):
    env, db = local.prepare(root)
    again, same_db = local.prepare(root)
    assert db == same_db == root / 'backend/data/vytal.db'
    assert db.read_bytes() == b'EXISTING_USER_DATABASE'
    assert all(env[key] == again[key] for key in ('SECRET_KEY', 'JWT_SECRET_KEY'))


def test_env_keys_and_windows_launcher_database_are_preserved(root):
    (root / 'backend/.env').write_text('SECRET_KEY=existing-one\nJWT_SECRET_KEY=existing-two\n')
    env, _ = local.prepare(root)
    assert env['SECRET_KEY'] == 'existing-one'
    assert env['JWT_SECRET_KEY'] == 'existing-two'
    before = (root / '.local-vytal/keys.json').read_bytes()
    local.prepare(root)
    assert (root / '.local-vytal/keys.json').read_bytes() == before


def test_ambiguous_databases_fail_without_modifying_either(root):
    state = root / '.local-vytal'
    state.mkdir()
    other = root / 'other.db'
    other.write_bytes(b'OTHER_DATABASE')
    (state / 'windows-config.json').write_text(json.dumps({'cloud': {'provider': 'local'}, 'local': {'db_path': str(other)}}))
    with pytest.raises(ValueError, match='ambíguo'):
        local.prepare(root)
    assert other.read_bytes() == b'OTHER_DATABASE'
    assert not (state / 'keys.json').exists()


def test_invalid_existing_keys_fail_closed(root):
    state = root / '.local-vytal'
    state.mkdir()
    (state / 'keys.json').write_text('{}')
    with pytest.raises(ValueError, match='Chaves locais inválidas'):
        local.prepare(root)
    assert (state / 'keys.json').read_text() == '{}'
