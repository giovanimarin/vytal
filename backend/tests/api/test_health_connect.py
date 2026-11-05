import pytest
from test_account_isolation import api as api


def record(identifier):
    return {'category': 'Steps', 'id': identifier, 'origin': 'com.garmin.android.apps.connectmobile',
            'start': '2026-01-15T12:00:00Z', 'end': '2026-01-15T13:00:00Z',
            'values': {'count': 123, 'unit': 'steps'}, 'metadata': {'id': identifier}, 'native': {'synthetic': True}}


@pytest.mark.parametrize('actor', ['A', 'B'])
def test_real_jwt_api_import_reads_only_authenticated_account(api, actor):
    actors, request = api
    body = {'installation_id': 'synthetic-phone', 'records': [record('native-' + actor)]}
    for _ in range(2):
        assert request('POST', '/health-connect/records', actor, body)['status'] == 200
    records = request('GET', '/health-connect/records', actor)['body']['records']
    assert [r['id'] for r in records] == ['native-' + actor]
    summary = request('GET', '/health-data/' + actors[actor]['user_id'] + '/summary?date=2026-01-15', actor)
    assert summary['body']['steps']['total_steps'] == 123


@pytest.mark.parametrize('actor,status', [(None, 403), ('forged', 401)])
def test_import_without_valid_auth_cannot_write(api, actor, status):
    result = api[1]('POST', '/health-connect/records', actor, {'installation_id': 'synthetic-phone', 'records': []})
    assert result['status'] == status and result['unchanged']


def test_manipulated_user_identity_and_bad_units_are_rejected_without_writes(api):
    body = {'installation_id': 'synthetic-phone', 'records': [record('bad')], 'user_id': api[0]['B']['user_id']}
    assert api[1]('POST', '/health-connect/records', 'A', body)['status'] == 422
    del body['user_id']
    body['records'][0]['values']['unit'] = 'wrong'
    result = api[1]('POST', '/health-connect/records', 'A', body)
    assert result['status'] == 422 and result['unchanged']
