const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const ts = require('typescript')
require.extensions['.ts'] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename)
const { normalize } = require('../src/healthConnect/normalize.ts')
const { synchronize } = require('../src/healthConnect/sync.ts')
const { RECORD_TYPES } = require('../src/healthConnect/types.ts')
const stamp = '2026-01-15T12:00:00Z'
function native(type = 'Steps', id = 'synthetic-1') {
  const values = {
    Steps: { count: 120 }, Distance: { distance: { inMeters: 1500 } },
    ElevationGained: { elevation: { inMeters: 75 } }, Weight: { weight: { inKilograms: 72.5 } },
    ActiveCaloriesBurned: { energy: { inKilocalories: 300 } }, TotalCaloriesBurned: { energy: { inKilocalories: 2200 } },
    RestingHeartRate: { beatsPerMinute: 60 }, HeartRate: { samples: [{ time: stamp, beatsPerMinute: 75 }] },
    Speed: { samples: [{ time: stamp, speed: { inMetersPerSecond: 2.5 } }] },
    SleepSession: { stages: [{ startTime: stamp, endTime: '2026-01-15T13:00:00Z', stage: 4 }] },
    ExerciseSession: { exerciseType: 56, title: 'Synthetic exercise' },
  }
  return { recordType: type, metadata: { id, dataOrigin: 'com.garmin.android.apps.connectmobile', clientRecordId: id,
    lastModifiedTime: stamp, device: { model: 'synthetic' }, recordingMethod: 2 },
    startTime: stamp, endTime: '2026-01-15T13:00:00Z', time: stamp, ...values[type] }
}
for (const type of RECORD_TYPES) {
  test(`normalizes ${type} preserving exact native origin/identity/times/units`, () => {
    const record = native(type)
    const result = normalize(type, record)
    assert.equal(result.id, record.metadata.id)
    assert.equal(result.origin, record.metadata.dataOrigin)
    assert.deepEqual(result.native, record)
    assert.deepEqual(result.metadata, record.metadata)
    assert.equal(result.start, stamp)
    assert.ok(result.values.unit)
  })
}
test('normalization rejects missing identities, units, invalid values and times', () => {
  const missing = native(); delete missing.metadata.id
  assert.throws(() => normalize('Steps', missing))
  assert.throws(() => normalize('Weight', { ...native('Weight'), weight: { value: 150, unit: 'pounds' } }))
  assert.throws(() => normalize('Steps', { ...native(), count: NaN }))
  assert.throws(() => normalize('Steps', { ...native(), startTime: 'invalid' }))
})
function deps(overrides = {}) {
  let calls = 0
  return {
    reader: { permissions: async () => [...RECORD_TYPES],
      page: async type => ({ records: type === 'Steps' ? [native()] : [] }),
      changes: async () => ({ upsertionChanges: [], deletionChanges: [], nextChangesToken: 't' + calls++, hasMore: false, changesTokenExpired: false }) },
    load: async () => null, save: async () => {}, upload: async () => {}, stillOwner: () => true, ...overrides,
  }
}
test('initial snapshot pages all records and commits cursor only after acknowledgement', async () => {
  const events = []
  const input = deps({ upload: async rows => events.push('upload:' + rows.length), save: async () => events.push('save') })
  input.reader.page = async (type, start, end, token) => ({ records: type === 'Steps' ? [native('Steps', token || 'first')] : [], pageToken: type === 'Steps' && !token ? 'next-page' : undefined })
  const result = await synchronize(input, new Date(stamp))
  assert.equal(result.records, 2)
  assert.deepEqual(events, ['upload:1', 'upload:1', 'save'])
})
test('incremental changes include updates and deletions without rereading history', async () => {
  const input = deps({ load: async () => ({ token: 'old', permissions: [...RECORD_TYPES] }) })
  input.reader.page = async () => { throw new Error('No snapshot expected') }
  input.reader.changes = async token => {
    assert.equal(token, 'old')
    return { upsertionChanges: [{ record: native() }], deletionChanges: [{ recordId: 'deleted' }], nextChangesToken: 'new', hasMore: false, changesTokenExpired: false }
  }
  input.upload = async (rows, deleted) => { assert.equal(rows.length, 1); assert.deepEqual(deleted, ['deleted']) }
  input.save = async value => assert.equal(value.token, 'new')
  assert.equal((await synchronize(input)).records, 1)
})
test('transport failure cannot advance an incremental cursor', async () => {
  let saved = false
  const input = deps({ load: async () => ({ token: 'old', permissions: [...RECORD_TYPES] }),
    upload: async () => { throw new Error('offline') }, save: async () => { saved = true } })
  input.reader.changes = async () => ({ upsertionChanges: [{ record: native() }], deletionChanges: [], nextChangesToken: 'new', hasMore: false })
  await assert.rejects(synchronize(input), /offline/)
  assert.equal(saved, false)
})
test('denied permissions do not read or upload', async () => {
  const input = deps()
  input.reader.permissions = async () => []
  input.reader.changes = async () => { throw new Error('No native read allowed') }
  assert.equal((await synchronize(input)).state, 'denied')
})
test('partial initial read retains previous checkpoint and reports category', async () => {
  let saved = false
  const input = deps({ save: async () => { saved = true } })
  input.reader.page = async type => { if (type === 'Weight') throw new Error('permission revoked'); return { records: [] } }
  const result = await synchronize(input, new Date(stamp))
  assert.equal(result.state, 'partial'); assert.deepEqual(result.failed, ['Weight']); assert.equal(saved, false)
})
test('expired token is cleared and asks for bounded history rescan', async () => {
  const input = deps({ load: async () => ({ token: 'old', permissions: [...RECORD_TYPES] }), save: async v => assert.equal(v, null) })
  input.reader.changes = async () => ({ changesTokenExpired: true })
  assert.equal((await synchronize(input)).state, 'expired')
})
test('account switch during native read stops upload and checkpoint commit', async () => {
  let owned = true, uploaded = false
  const input = deps({ stillOwner: () => owned, upload: async () => { uploaded = true } })
  input.reader.page = async () => { owned = false; return { records: [native()] } }
  await assert.rejects(synchronize(input), /Session changed/)
  assert.equal(uploaded, false)
})
test('large changes pages split bounded HTTP batches before checkpoint', async () => {
  const lengths = []
  const input = deps({ load: async () => ({ token: 'old', permissions: [...RECORD_TYPES] }),
    upload: async rows => lengths.push(rows.length) })
  input.reader.changes = async () => ({ upsertionChanges: Array.from({ length: 401 }, (_, i) => ({ record: native('Steps', 'id-' + i) })), deletionChanges: [], nextChangesToken: 'new', hasMore: false })
  await synchronize(input)
  assert.deepEqual(lengths, [200, 200, 1])
})
test('changes captured at token creation are not lost between token and snapshot', async () => {
  const ids = []
  const input = deps({ upload: async rows => ids.push(...rows.map(r => r.id)) })
  let first = true
  input.reader.changes = async () => { const upsertionChanges = first ? [{ record: native('Steps', 'during-snapshot') }] : []; first = false; return { upsertionChanges, deletionChanges: [], nextChangesToken: 'new', hasMore: false } }
  await synchronize(input)
  assert.ok(ids.includes('during-snapshot'))
})
