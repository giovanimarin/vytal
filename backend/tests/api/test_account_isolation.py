"""Real HTTP/auth/SQLite regressions without changing application dependency wiring."""
import json
import os
import secrets
import select
import subprocess
import sys
from pathlib import Path

import pytest


class Actors(dict):
    def __repr__(self):
        return '<synthetic identities; credentials redacted>'


@pytest.fixture(scope='module')
def api(tmp_path_factory):
    root = tmp_path_factory.mktemp('account-isolation')
    config = root / 'config.yaml'
    config.write_text(f'cloud:\n  provider: local\nlocal:\n  data_dir: {root}\n  db_path: {root}/test.db\n')
    env = dict(os.environ, CONFIG_PATH=str(config), ENVIRONMENT='local',
               GOOGLE_CLIENT_ID='synthetic', GOOGLE_CLIENT_SECRET='synthetic',
               SECRET_KEY=secrets.token_hex(32), JWT_SECRET_KEY=secrets.token_hex(32),
               PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name('worker.py'))],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)

    def receive():
        assert select.select([process.stdout], [], [], 30)[0], 'ASGI worker timed out'
        line = process.stdout.readline()
        assert line, f'ASGI worker exited: {process.poll()}'
        return json.loads(line)

    try:
        actors = Actors(receive())

        def request(method, url, actor=None, body=None, invalid=False):
            headers = {}
            if actor:
                headers['Authorization'] = 'Bearer ' + ('invalid' if invalid else actors[actor]['access_token'])
            process.stdin.write(json.dumps({'method': method, 'url': '/api/v1' + url,
                                               'headers': headers, 'json': body}) + '\n')
            process.stdin.flush()
            return receive()
        yield actors, request
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdout.close()


CASES = [
    ('GET', '/connect/google_fit/auth-url?user_id={id}', None, 200),
    ('GET', '/connect/google_fit/callback?code=synthetic&state={state}', None, 200),
    ('POST', '/connect/google_fit/callback', {'code': 'synthetic', 'state': '{state}', 'redirect_uri': 'http://localhost/callback'}, 200),
    ('POST', '/health-data/sync', {'user_id': '{id}', 'start_date': '2026-01-15', 'end_date': '2026-01-15'}, 202),
    ('GET', '/health-data/{id}/summary?date=2026-01-15', None, 200),
    ('GET', '/readiness/{id}?date=2026-01-15', None, 200),
    ('GET', '/readiness/{id}/history?start_date=2026-01-15&end_date=2026-01-15', None, 200),
    ('GET', '/readiness/{id}/advanced?date=2026-01-15', None, 200),
    ('GET', '/readiness/modalities/{id}?date=2026-01-15', None, 200),
    ('POST', '/workouts', {'user_id': '{id}', 'modality': 'corrida', 'intensity': 'leve', 'duration_min': 20, 'date': '2026-01-15'}, 201),
    ('GET', '/workouts/{id}?start_date=2026-01-15&end_date=2026-01-15', None, 200),
    ('GET', '/muscles/{id}/recovery?date=2026-01-15', None, 200),
    ('GET', '/muscles/{id}/suggestion?date=2026-01-15', None, 200),
    ('POST', '/wellness-feedback', {'user_id': '{id}', 'date': '2026-01-15', 'notes': 'regression'}, 201),
    ('GET', '/wellness-feedback/{id}?date=2026-01-15', None, 200),
]


def call(api, case, actor, target, invalid=False):
    actors, request = api
    method, path, body, _ = case
    values = {'id': actors[target]['user_id'], 'state': actors[target]['state']}
    body = {k: v.format(**values) if isinstance(v, str) else v for k, v in body.items()} if body else None
    return request(method, path.format(**values), actor, body, invalid)


@pytest.mark.parametrize('case', CASES, ids=[f'{c[0]} {c[1].split("?")[0]}' for c in CASES])
@pytest.mark.parametrize(('actor', 'target'), [('A', 'B'), ('B', 'A'), ('A', 'unknown')])
def test_cross_account_denied_before_effects(api, case, actor, target):
    result = call(api, case, actor, target)
    assert result['status'] == 404
    assert result['body'] == {'detail': 'Not found'}
    assert result['effects'] == 0
    assert result['unchanged']


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('actor', ['A', 'B'])
def test_own_account_contract(api, case, actor):
    result = call(api, case, actor, actor)
    assert result['status'] == case[3]
    def check_owners(value):
        if isinstance(value, dict):
            if 'user_id' in value:
                assert value['user_id'] == api[0][actor]['user_id']
            for child in value.values():
                check_owners(child)
        elif isinstance(value, list):
            for child in value:
                check_owners(child)
    check_owners(result['body'])


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize(('actor', 'invalid', 'expected'), [(None, False, 403), ('A', True, 401)])
def test_authentication_required(api, case, actor, invalid, expected):
    result = call(api, case, actor, 'B', invalid)
    assert result['status'] == expected
    assert result['effects'] == 0
    assert result['unchanged']


@pytest.mark.parametrize('method', ['GET', 'POST'])
def test_invalid_oauth_state_stays_bad_request(api, method):
    _, request = api
    path = '/connect/google_fit/callback'
    body = {'code': 'synthetic', 'state': 'invalid', 'redirect_uri': 'http://localhost/callback'}
    result = request(method, path + ('?code=synthetic&state=invalid' if method == 'GET' else ''),
                     'A', body if method == 'POST' else None)
    assert result['status'] == 400
    assert result['effects'] == 0
    assert result['unchanged']


@pytest.mark.parametrize(('actor', 'other'), [('A', 'B'), ('B', 'A')])
def test_profile_update_uses_token_not_extra_client_identity(api, actor, other):
    actors, request = api
    before = request('GET', '/users/me', other)['body']
    result = request('PATCH', '/users/me?user_id=' + actors[other]['user_id'], actor,
                     {'user_id': actors[other]['user_id'], 'name': 'Own updated profile'})
    assert result['status'] == 200
    assert result['body']['user_id'] == actors[actor]['user_id']
    assert result['body']['name'] == 'Own updated profile'
    assert 'password_hash' not in result['body']
    assert request('GET', '/users/me', other)['body'] == before


@pytest.mark.parametrize('actor', ['A', 'B'])
def test_authenticated_catalog_is_preserved(api, actor):
    assert api[1]('GET', '/workouts/exercises/catalog', actor)['status'] == 200


@pytest.mark.parametrize('actor', ['missing-email', 'empty-sub', 'empty-email', 'wrong-type', 'expired', 'forged'])
def test_invalid_identity_tokens_rejected(api, actor):
    result = api[1]('GET', '/wellness-feedback/' + api[0]['B']['user_id'], actor)
    assert result['status'] == 401
    assert result['effects'] == 0
    assert result['unchanged']


@pytest.mark.parametrize(('method', 'path', 'body'), [
    ('GET', '/users/me', None), ('PATCH', '/users/me', {'name': 'Unauthorized'}),
    ('GET', '/workouts/exercises/catalog', None),
])
@pytest.mark.parametrize(('actor', 'invalid', 'expected'), [(None, False, 403), ('A', True, 401)])
def test_existing_profile_and_catalog_require_auth(api, method, path, body, actor, invalid, expected):
    result = api[1](method, path, actor, body, invalid)
    assert result['status'] == expected
    assert result['effects'] == 0
    assert result['unchanged']
