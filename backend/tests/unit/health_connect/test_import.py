import copy

import pytest
from app.adapters.cloud.local import LocalWarehouseProvider
from app.config.cloud_config import LocalConfig
from app.health_connect.normalize import canonical, projections
from app.health_connect.repository import HealthConnectRepository
from app.repositories.health_data_repo import HealthDataRepository

GARMIN = 'com.garmin.android.apps.connectmobile'
FIT = 'com.google.android.apps.fitness'


def record(category='Steps', identifier='synthetic-1', origin=GARMIN, values=None):
    values = values or {'count': 120, 'unit': 'steps'}
    return {'category': category, 'id': identifier, 'origin': origin, 'start': '2026-01-15T12:00:00+00:00',
            'end': '2026-01-15T13:00:00+00:00', 'values': values,
            'metadata': {'id': identifier, 'dataOrigin': origin, 'lastModifiedTime': '2026-01-15T14:00:00Z'},
            'native': {'synthetic': True, 'offset': '+00:00'}}


@pytest.fixture
async def local(tmp_path, monkeypatch):
    from app.adapters.cloud import factory
    warehouse = LocalWarehouseProvider(LocalConfig(db_path=str(tmp_path / 'hc.db')))
    await warehouse.init_schema()
    monkeypatch.setattr(factory, '_warehouse', warehouse)
    return warehouse, HealthConnectRepository(warehouse.db_path)


async def test_repeat_update_and_deletion_are_idempotent_and_account_scoped(local):
    warehouse, repository = local
    original = record()
    for _ in range(2):
        await repository.import_batch('A', 'phone', [original], [])
    assert len(await warehouse.query("SELECT * FROM raw_health_events WHERE user_id='A'")) == 1
    assert (await HealthDataRepository().get_normalized('A', '2026-01-15', 'steps'))[0]['total_steps'] == 120
    assert (await repository.recent('B'))['records'] == []
    changed = record(values={'count': 130, 'unit': 'steps'})
    await repository.import_batch('A', 'phone', [changed], [])
    assert (await repository.recent('A'))['records'][0]['values']['count'] == 130
    await repository.import_batch('B', 'phone', [], [original['id']])
    assert len((await repository.recent('A'))['records']) == 1
    await repository.import_batch('A', 'different-phone', [], [original['id']])
    assert len((await repository.recent('A'))['records']) == 1
    await repository.import_batch('A', 'phone', [], [original['id']])
    assert (await repository.recent('A'))['records'] == []
    assert await HealthDataRepository().get_normalized('A', '2026-01-15', 'steps') == []


async def test_mirrored_fit_and_garmin_preserve_raw_aliases_but_count_once(local):
    warehouse, repository = local
    await repository.import_batch('A', 'phone', [record(), record(identifier='mirror', origin=FIT)], [])
    recent = await repository.recent('A')
    assert recent['retained_raw'] == 2 and recent['displayed'] == 1
    assert recent['records'][0]['origin'] == GARMIN
    assert len(recent['records'][0]['aliases']) == 2
    assert (await HealthDataRepository().get_normalized('A', '2026-01-15', 'steps'))[0]['total_steps'] == 120
    await warehouse.insert('normalized_steps', [{'record_id': 'legacy-fit', 'user_id': 'A', 'date': '2026-01-15', 'total_steps': 120, 'source_event_id': 'fit-raw'}])
    assert len(await HealthDataRepository().get_normalized('A', '2026-01-15', 'steps')) == 1
    assert len(await warehouse.query('SELECT * FROM normalized_steps')) == 2


@pytest.mark.parametrize('category,values', [
    ('Distance', {'value': 1500.5, 'unit': 'm'}), ('ElevationGained', {'value': 125, 'unit': 'm'}),
    ('Weight', {'value': 72.5, 'unit': 'kg'}), ('ActiveCaloriesBurned', {'value': 350, 'unit': 'kcal'}),
    ('TotalCaloriesBurned', {'value': 2000, 'unit': 'kcal'}),
    ('HeartRate', {'samples': [{'time': '2026-01-15T12:00:00Z', 'value': 75}], 'unit': 'bpm'}),
    ('RestingHeartRate', {'value': 60, 'unit': 'bpm'}),
    ('Speed', {'samples': [{'time': '2026-01-15T12:00:00Z', 'value': 2.5}], 'unit': 'm/s'}),
    ('ExerciseSession', {'exerciseType': 56, 'title': 'Synthetic run', 'unit': 'interval'}),
    ('SleepSession', {'stages': [{'startTime': '2026-01-15T12:00:00Z', 'endTime': '2026-01-15T13:00:00Z', 'stage': 4}], 'unit': 'interval'}),
])
async def test_supported_categories_preserve_units_times_identity_and_metadata(local, category, values):
    _, repository = local
    original = record(category, values=values)
    await repository.import_batch('A', 'phone', [original], [])
    imported = (await repository.recent('A'))['records'][0]
    for key in ('id', 'origin', 'start', 'end', 'values', 'metadata', 'native'):
        assert imported[key] == original[key]


def test_no_inferred_resting_hr_sleep_or_overlapping_step_totals():
    hr = record('HeartRate', values={'samples': [{'time': '2026-01-15T12:00:00Z', 'value': 80}], 'unit': 'bpm'})
    sleep = record('SleepSession', values={'stages': [], 'unit': 'interval'})
    overlap = record(identifier='overlap', values={'count': 200, 'unit': 'steps'})
    overlap['start'] = '2026-01-15T12:30:00+00:00'
    assert projections([hr, sleep, record(), overlap]) == {}


async def test_bad_batch_or_projection_failure_rolls_back_all_writes(local):
    warehouse, repository = local
    bad = record('SleepSession', identifier='bad', values={'stages': [{'startTime': 'invalid', 'endTime': 'invalid', 'stage': 4}], 'unit': 'interval'})
    with pytest.raises(ValueError):
        await repository.import_batch('A', 'phone', [record(), bad], [])
    assert await warehouse.query('SELECT * FROM raw_health_events') == []
    assert await warehouse.query('SELECT * FROM normalized_steps') == []


async def test_change_of_native_day_reprojects_previous_and_new_day(local):
    warehouse, repository = local
    await repository.import_batch('A', 'phone', [record()], [])
    changed = record()
    changed['start'] = '2026-01-16T12:00:00+00:00'
    changed['end'] = '2026-01-16T13:00:00+00:00'
    await repository.import_batch('A', 'phone', [changed], [])
    rows = await warehouse.query('SELECT date FROM normalized_steps')
    assert [r['date'] for r in rows] == ['2026-01-16']


def test_equal_instants_with_different_offsets_reconcile_without_losing_origins():
    first, second = record(), record(identifier='mirror', origin=FIT)
    second['start'], second['end'] = '2026-01-15T09:00:00-03:00', '2026-01-15T10:00:00-03:00'
    assert len(canonical([first, second])) == 1


async def test_native_modification_replay_cannot_overwrite_newer_values(local):
    _, repository = local
    fresh = record(values={'count': 200, 'unit': 'steps'})
    fresh['metadata']['lastModifiedTime'] = '2026-01-15T16:00:00Z'
    await repository.import_batch('A', 'phone', [fresh], [])
    await repository.import_batch('A', 'phone', [record()], [])
    assert (await repository.recent('A'))['records'][0]['values']['count'] == 200


async def test_canonical_records_are_copies_and_raw_observations_remain_intact(local):
    _, repository = local
    original = record()
    before = copy.deepcopy(original)
    await repository.import_batch('A', 'phone', [original], [])
    assert original == before


async def test_concurrent_retries_from_distinct_repository_instances_do_not_duplicate(local):
    import asyncio

    warehouse, repository = local
    second = HealthConnectRepository(warehouse.db_path)
    await asyncio.gather(repository.import_batch('A', 'phone', [record()], []),
                         second.import_batch('A', 'phone', [record()], []))
    assert len(await warehouse.query('SELECT * FROM raw_health_events')) == 1
    assert len(await warehouse.query('SELECT * FROM normalized_steps')) == 1


async def test_repeat_does_not_invalidate_unchanged_readiness_or_normalization(local):
    warehouse, repository = local
    native = record('RestingHeartRate', values={'value': 60, 'unit': 'bpm'})
    await repository.import_batch('A', 'phone', [native], [])
    before = await warehouse.query('SELECT * FROM normalized_heart_rate')
    await warehouse.insert('fact_daily_readiness', [{'readiness_id': 'known', 'user_id': 'A', 'date': '2026-01-15',
        'readiness_score': 80, 'readiness_category': 'intense', 'calculated_at': '2026-01-15T14:00:00Z'}])
    await repository.import_batch('A', 'phone', [native], [])
    assert await warehouse.query('SELECT * FROM normalized_heart_rate') == before
    assert len(await warehouse.query('SELECT * FROM fact_daily_readiness')) == 1


async def test_recent_filter_can_find_garmin_without_other_origins_hiding_it(local):
    _, repository = local
    await repository.import_batch('A', 'phone', [record(), record('Weight', 'weight-other', FIT, {'value': 70, 'unit': 'kg'})], [])
    assert len((await repository.recent('A', origin=GARMIN))['records']) == 1
    assert (await repository.recent('A', category='Weight', origin=GARMIN))['records'] == []
    assert (await repository.recent('B', origin=GARMIN))['records'] == []
