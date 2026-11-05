"""Pure Health Connect normalization and conservative source reconciliation.

Keep all raw provenance. Exact mirrored observations share a canonical display
record. Never add totals from different origins or mix HC totals with Fit totals.
"""
import hashlib
import json
import math
from datetime import UTC, datetime
from itertools import pairwise


def fingerprint(record: dict) -> str:
    observed = {k: record[k] for k in ('category', 'start', 'end', 'values')}
    # Presentation titles do not identify an exercise observation.
    if observed['category'] == 'ExerciseSession':
        observed['values'] = {k: v for k, v in record['values'].items() if k != 'title'}
    observed['start'] = datetime.fromisoformat(record['start'].replace('Z', '+00:00')).astimezone(UTC).isoformat()
    observed['end'] = datetime.fromisoformat(record['end'].replace('Z', '+00:00')).astimezone(UTC).isoformat()
    return hashlib.sha256(json.dumps(observed, sort_keys=True, allow_nan=False).encode()).hexdigest()


def priority(record):
    return (0 if record['origin'] == 'com.garmin.android.apps.connectmobile' else
            2 if record['origin'] == 'com.google.android.apps.fitness' else 1, record['origin'], record['id'])


def canonical(records: list[dict]) -> list[dict]:
    selected = {}
    for record in sorted(records, key=priority):
        key = fingerprint(record)
        if key not in selected:
            selected[key] = dict(record, aliases=[])
        selected[key]['aliases'].append({'origin': record['origin'], 'id': record['id'], 'metadata': record['metadata']})
    return list(selected.values())


def day(record):
    # Existing v1 day buckets use UTC. Exact native timestamps/offsets remain raw.
    value = record['end'] if record['category'] == 'SleepSession' else record['start']
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(UTC).date().isoformat()


def validate_values(record):
    category, values = record['category'], record['values']
    units = {'Steps': 'steps', 'Distance': 'm', 'ElevationGained': 'm', 'Weight': 'kg',
             'ActiveCaloriesBurned': 'kcal', 'TotalCaloriesBurned': 'kcal', 'RestingHeartRate': 'bpm',
             'HeartRate': 'bpm', 'Speed': 'm/s', 'SleepSession': 'interval', 'ExerciseSession': 'interval'}
    if values.get('unit') != units[category]:
        raise ValueError('Unexpected canonical unit')
    def number(value):
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError('Invalid observed number')
    if category == 'Steps':
        number(values.get('count'))
        if int(values['count']) != values['count']:
            raise ValueError('Steps must be integral')
    elif category in {'HeartRate', 'Speed'}:
        if not isinstance(values.get('samples'), list):
            raise ValueError('Samples required')
        for sample in values['samples']:
            number(sample.get('value'))
            stamp = datetime.fromisoformat(sample['time'].replace('Z', '+00:00'))
            if stamp.utcoffset() is None or stamp < datetime.fromisoformat(record['start']) or stamp > datetime.fromisoformat(record['end']):
                raise ValueError('Sample timezone required')
    elif category == 'ExerciseSession':
        number(values.get('exerciseType'))
    elif category == 'SleepSession':
        if not isinstance(values.get('stages'), list):
            raise ValueError('Sleep stages must be a list')
        for stage in values['stages']:
            start = datetime.fromisoformat(stage['startTime'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(stage['endTime'].replace('Z', '+00:00'))
            if start.utcoffset() is None or end.utcoffset() is None or end <= start or start < datetime.fromisoformat(record['start']) or end > datetime.fromisoformat(record['end']):
                raise ValueError('Invalid sleep stage interval')
    else:
        number(values.get('value'))
    modified = record.get('metadata', {}).get('lastModifiedTime')
    if modified and datetime.fromisoformat(modified.replace('Z', '+00:00')).utcoffset() is None:
        raise ValueError('Modification timezone required')
    json.dumps(record, allow_nan=False)


def preferred(records, category):
    rows = sorted((r for r in canonical(records) if r['category'] == category), key=priority)
    return [r for r in rows if r['origin'] == rows[0]['origin']] if rows else []


def projections(records: list[dict]) -> dict[str, dict]:
    result = {}
    steps = preferred(records, 'Steps')
    if steps:
        ordered = sorted(steps, key=lambda r: r['start'])
        # Overlapping totals of one origin cannot safely be prorated as measurements.
        if all(datetime.fromisoformat(a['end']) <= datetime.fromisoformat(b['start']) for a, b in pairwise(ordered)):
            result['steps'] = {'total_steps': sum(r['values']['count'] for r in steps), 'hourly_steps': '[]'}
    resting = preferred(records, 'RestingHeartRate')
    if resting:
        latest = max(resting, key=lambda r: r['start'])
        samples = [s for r in preferred(records, 'HeartRate') for s in r['values']['samples']]
        sample_values = list({(s['time'], s['value']): s['value'] for s in samples}.values())
        result['heart_rate'] = {'resting_bpm': latest['values']['value'],
            'average_bpm': sum(sample_values) / len(sample_values) if sample_values else None,
            'max_bpm': max(sample_values) if sample_values else None, 'min_bpm': min(sample_values) if sample_values else None}
    # Sleep duration only from observed asleep stages; no invented sleep score or
    # inference that a whole session without stages was spent sleeping.
    stages = []
    for record in preferred(records, 'SleepSession'):
        stages.extend(record['values']['stages'])
    intervals = sorted((datetime.fromisoformat(s['startTime']), datetime.fromisoformat(s['endTime']))
                       for s in stages if s.get('stage') in {2, 4, 5, 6})
    merged = []
    for start, end in intervals:
        if start.utcoffset() is None or end.utcoffset() is None or end <= start:
            raise ValueError('Invalid sleep stage times')
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    if merged:
        result['sleep'] = {'duration_minutes': int(sum((end - start).total_seconds() for start, end in merged) / 60),
                           'deep_sleep_minutes': None, 'light_sleep_minutes': None, 'rem_sleep_minutes': None,
                           'awake_minutes': None, 'sleep_score': None}
    return result
