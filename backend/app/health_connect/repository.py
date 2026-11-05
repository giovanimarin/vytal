"""Local SQLite transaction boundary; no table/schema or cloud migration."""
import hashlib
import json
from datetime import UTC, datetime

import aiosqlite
from app.health_connect.normalize import canonical, day, projections, validate_values


class HealthConnectRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    async def import_batch(self, account: str, installation: str, records: list[dict], deleted: list[str]):
        for record in records:
            validate_values(record)
        now = datetime.now(UTC).isoformat()
        affected = set()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute('BEGIN IMMEDIATE')
            for identifier in deleted:
                cursor = await db.execute("SELECT event_id,raw_payload FROM raw_health_events WHERE user_id=? AND provider='health_connect' AND json_extract(raw_payload,'$.installation_id')=? AND json_extract(raw_payload,'$.id')=?",
                                          [account, installation, identifier])
                for row in await cursor.fetchall():
                    affected.add(day(json.loads(row['raw_payload'])))
                    await db.execute('DELETE FROM raw_health_events WHERE event_id=? AND user_id=?', [row['event_id'], account])
            for record in records:
                key = hashlib.sha256(json.dumps([account, installation, record['category'], record['origin'], record['id']]).encode()).hexdigest()
                event_id = 'hc:' + key
                cursor = await db.execute('SELECT raw_payload FROM raw_health_events WHERE event_id=? AND user_id=?', [event_id, account])
                old = await cursor.fetchone()
                if old:
                    previous = json.loads(old['raw_payload'])
                    # Native changes may be replayed out of order after transport failure.
                    old_time = previous.get('metadata', {}).get('lastModifiedTime')
                    new_time = record.get('metadata', {}).get('lastModifiedTime')
                    if old_time and new_time and datetime.fromisoformat(old_time.replace('Z', '+00:00')) > datetime.fromisoformat(new_time.replace('Z', '+00:00')):
                        continue
                    affected.add(day(previous))
                affected.add(day(record))
                payload = dict(record, installation_id=installation)
                await db.execute('INSERT OR REPLACE INTO raw_health_events (event_id,user_id,provider,metric_type,raw_payload,collected_at,ingested_at,pipeline_run) VALUES (?,?,?,?,?,?,?,?)',
                    [event_id, account, 'health_connect', record['category'], json.dumps(payload, allow_nan=False), record['start'], now, 'health-connect'])
            all_records = []
            if affected:
                cursor = await db.execute(
                    "SELECT raw_payload FROM raw_health_events WHERE user_id=? AND provider='health_connect' "
                    "AND event_id LIKE 'hc:%' AND metric_type IN ('Steps','SleepSession','HeartRate','RestingHeartRate') "
                    "AND date(CASE WHEN metric_type='SleepSession' THEN json_extract(raw_payload,'$.end') ELSE collected_at END) IN ("
                    + ','.join('?' for _ in affected) + ')', [account, *sorted(affected)])
                all_records = [json.loads(row['raw_payload']) for row in await cursor.fetchall()]
            warnings = []
            for date in affected:
                current = [r for r in all_records if day(r) == date]
                derived = projections(current)
                if any(r['category'] == 'Steps' for r in current) and 'steps' not in derived:
                    warnings.append('steps-overlap:' + date)
                changed_inputs = False
                for metric in ('steps', 'sleep', 'heart_rate'):
                    cursor = await db.execute(f"SELECT * FROM normalized_{metric} WHERE user_id=? AND date=? AND source_event_id LIKE 'hc-day:%'", [account, date])
                    previous = [dict(r) for r in await cursor.fetchall()]
                    values = derived.get(metric)
                    if values and len(previous) == 1 and all(previous[0].get(key) == value for key, value in values.items()):
                        continue
                    if not values and not previous:
                        continue
                    await db.execute(f"DELETE FROM normalized_{metric} WHERE user_id=? AND date=? AND source_event_id LIKE 'hc-day:%'", [account, date])
                    if values:
                        identifier = 'hc-day:' + hashlib.sha256(f'{account}/{date}/{metric}'.encode()).hexdigest()
                        row = dict(values, user_id=account, date=date, record_id=identifier, source_event_id=identifier, normalized_at=now)
                        columns = ','.join(row)
                        await db.execute(f"INSERT INTO normalized_{metric} ({columns}) VALUES ({','.join('?' for _ in row)})", list(row.values()))
                    changed_inputs = changed_inputs or metric in {'sleep', 'heart_rate'}
                if changed_inputs:
                    for table in ('fact_daily_readiness', 'fact_readiness_by_modality'):
                        await db.execute(f'DELETE FROM {table} WHERE user_id=? AND date=?', [account, date])
            await db.commit()
        return {'accepted': len(records), 'deleted_requested': len(deleted), 'affected_days': sorted(affected), 'source': 'health_connect', 'projection_warnings': warnings}

    async def recent(self, account: str, category: str | None = None, origin: str | None = None):
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT raw_payload FROM raw_health_events WHERE user_id=? AND provider='health_connect' AND event_id LIKE 'hc:%'"
            params = [account]
            if category:
                sql += " AND metric_type=?"
                params.append(category)
            if origin:
                sql += " AND json_extract(raw_payload,'$.origin')=?"
                params.append(origin)
            cursor = await db.execute(sql + " ORDER BY collected_at DESC LIMIT 200", params)
            records = [json.loads(row[0]) for row in await cursor.fetchall()]
        selected = canonical(records)
        return {'records': selected, 'retained_raw': len(records), 'displayed': len(selected), 'source': 'health_connect', 'simulated': False}
