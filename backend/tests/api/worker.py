"""Isolated ASGI worker: real JWT/auth/persistence, synthetic external provider only."""
import asyncio
import hashlib
import json
import sqlite3
import sys
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from app.adapters.cloud.factory import get_warehouse
from app.adapters.connectors.base import OAuthToken
from app.config.settings import settings
from app.main import app
from app.repositories.token_repo import TokenRepository
from app.services.oauth_service import OAuthService
from fastapi.testclient import TestClient
from jose import jwt


def digest():
    from app.config.cloud_config import get_cloud_config
    with sqlite3.connect(get_cloud_config().local.db_path) as db:
        return hashlib.sha256('\n'.join(db.iterdump()).encode()).hexdigest()


def token():
    return OAuthToken('synthetic', 'synthetic', datetime.now(UTC) + timedelta(days=1),
                      'google_fit', '')


connector = Mock()
connector.get_auth_url.return_value = 'https://provider.invalid/authorize'
connector.exchange_token = AsyncMock(side_effect=lambda *a, **k: token())
connector.fetch_raw_events = AsyncMock(return_value=[])
with patch('app.services.oauth_service.get_connector', return_value=connector), \
     patch('app.services.health_data_service.get_connector', return_value=connector), \
     patch('httpx.HTTPTransport.handle_request', side_effect=AssertionError('External network forbidden')), \
     patch('httpx.AsyncHTTPTransport.handle_async_request', side_effect=AssertionError('External network forbidden')), \
     TestClient(app) as client:
    actors = {}
    for name in ('A', 'B'):
        response = client.post('/api/v1/auth/register', json={
            'email': f'{name}@example.invalid', 'name': name, 'password': 'synthetic-password-123'})
        assert response.status_code == 201
        actor = response.json()
        actor['state'] = OAuthService()._generate_state(actor['user_id'])
        actors[name] = actor
        seed_token = token()
        seed_token.user_id = actor['user_id']
        asyncio.run(TokenRepository().save(seed_token))
        for table, values in (
            ('normalized_sleep', {'duration_minutes': 480, 'sleep_score': 85}),
            ('normalized_heart_rate', {'resting_bpm': 60, 'average_bpm': 75}),
        ):
            asyncio.run(get_warehouse().insert(table, [{
                'record_id': str(uuid.uuid4()), 'user_id': actor['user_id'],
                'date': '2026-01-15', **values}]))
        headers = {'Authorization': 'Bearer ' + actor['access_token']}
        seeded = client.post('/api/v1/workouts', headers=headers, json={
            'user_id': actor['user_id'], 'modality': 'corrida', 'intensity': 'leve',
            'duration_min': 20, 'date': '2026-01-15', 'notes': name})
        assert seeded.status_code == 201
        client.post('/api/v1/wellness-feedback', headers={'Authorization': 'Bearer ' + actor['access_token']},
                    json={'user_id': actor['user_id'], 'date': '2026-01-15', 'notes': name})
    for label, changes in {
        'missing-email': {'email': None}, 'empty-sub': {'sub': ''},
        'empty-email': {'email': ' '}, 'wrong-type': {'type': 'refresh'},
        'expired': {'exp': 1}, 'forged': {},
    }.items():
        claims = {'sub': actors['B']['user_id'], 'email': 'B@example.invalid',
                  'type': 'access', 'exp': datetime.now(UTC) + timedelta(minutes=5)}
        claims.update(changes)
        if label == 'missing-email':
            del claims['email']
        actors[label] = {'access_token': jwt.encode(
            claims, 'incorrect-signing-key' if label == 'forged' else settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm)}
    actors['unknown'] = {'user_id': 'nonexistent-account',
                         'state': OAuthService()._generate_state('nonexistent-account')}
    wh = get_warehouse()
    wh.query = AsyncMock(wraps=wh.query)
    wh.insert = AsyncMock(wraps=wh.insert)
    print(json.dumps(actors), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        for mock in (wh.query, wh.insert, connector.get_auth_url,
                     connector.exchange_token, connector.fetch_raw_events):
            mock.reset_mock()
        before = digest()
        response = client.request(**request)
        effects = sum(mock.call_count for mock in (
            wh.query, wh.insert, connector.get_auth_url,
            connector.exchange_token, connector.fetch_raw_events))
        print(json.dumps({'status': response.status_code, 'body': response.json(),
                          'effects': effects, 'unchanged': before == digest()}), flush=True)
