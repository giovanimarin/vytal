import { Category, ImportedRecord, RECORD_TYPES } from './types'

const finite = (value: unknown): number => {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid native value')
  return value
}
const unit = (value: unknown, name: string) => finite((value as Record<string, unknown>)?.[name])
export function normalize(category: Category, record: Record<string, unknown>): ImportedRecord {
  if (!RECORD_TYPES.includes(category)) throw new Error('Unsupported category')
  const metadata = record.metadata as Record<string, unknown> | undefined
  if (!metadata || typeof metadata.id !== 'string' || !metadata.id || typeof metadata.dataOrigin !== 'string' || !metadata.dataOrigin) throw new Error('Missing native identity/origin')
  const start = (record.startTime || record.time) as string
  const end = (record.endTime || record.time) as string
  const aware = (time: string) => /(?:Z|[+-]\d{2}:\d{2})$/i.test(time)
  if (!aware(start) || !aware(end) || !Number.isFinite(Date.parse(start)) || !Number.isFinite(Date.parse(end)) || Date.parse(end) < Date.parse(start)) throw new Error('Invalid native time')
  let values: Record<string, unknown>
  switch (category) {
    case 'Steps': values = { count: finite(record.count), unit: 'steps' }; break
    case 'Distance': values = { value: unit(record.distance, 'inMeters'), unit: 'm' }; break
    case 'ElevationGained': values = { value: unit(record.elevation, 'inMeters'), unit: 'm' }; break
    case 'Weight': values = { value: unit(record.weight, 'inKilograms'), unit: 'kg' }; break
    case 'ActiveCaloriesBurned':
    case 'TotalCaloriesBurned': values = { value: unit(record.energy, 'inKilocalories'), unit: 'kcal' }; break
    case 'RestingHeartRate': values = { value: finite(record.beatsPerMinute), unit: 'bpm' }; break
    case 'HeartRate': values = { samples: (record.samples as Record<string, unknown>[]).map(s => ({ time: s.time, value: finite(s.beatsPerMinute) })), unit: 'bpm' }; break
    case 'Speed': values = { samples: (record.samples as Record<string, unknown>[]).map(s => ({ time: s.time, value: unit(s.speed, 'inMetersPerSecond') })), unit: 'm/s' }; break
    case 'SleepSession': values = { stages: record.stages || [], unit: 'interval' }; break
    case 'ExerciseSession': values = { exerciseType: finite(record.exerciseType), title: record.title || null, unit: 'interval' }; break
  }
  // Keep exact source identifiers, offsets, units, device and modification metadata.
  return { category, id: metadata.id, origin: metadata.dataOrigin, start, end, values, metadata, native: record }
}
