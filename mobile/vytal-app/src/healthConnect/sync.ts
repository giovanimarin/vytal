import { normalize } from './normalize'
import { Category, ImportedRecord, Reader, RECORD_TYPES } from './types'

export interface Checkpoint { token: string; permissions: string[] }
export interface SyncDependencies {
  reader: Reader
  load(): Promise<Checkpoint | null>
  save(value: Checkpoint | null): Promise<void>
  upload(records: ImportedRecord[], deleted: string[]): Promise<void>
  stillOwner(): boolean
}
export async function synchronize(deps: SyncDependencies, now = new Date()): Promise<{ state: string; records: number; failed: string[] }> {
  const granted = await deps.reader.permissions()
  const types = RECORD_TYPES.filter(t => granted.includes(t))
  if (!types.length) return { state: 'denied', records: 0, failed: [] }
  const owner = () => { if (!deps.stillOwner()) throw new Error('Session changed during import') }
  owner()
  const stored = await deps.load()
  let token = stored && JSON.stringify([...stored.permissions].sort()) === JSON.stringify([...types].sort()) ? stored.token : undefined
  let records = 0
  const failed: string[] = []
  const upload = async (raw: Record<string, unknown>[], deleted: string[], category?: Category) => {
    owner()
    const normalized: ImportedRecord[] = []
    for (const record of raw) {
      try { normalized.push(normalize(category || record.recordType as Category, record)) }
      catch { throw new Error('Native record could not be normalized; checkpoint retained') }
    }
    for (let offset = 0; offset < Math.max(normalized.length, deleted.length); offset += 200) {
      owner()
      await deps.upload(normalized.slice(offset, offset + 200), deleted.slice(offset, offset + 200))
    }
    owner()
    records += normalized.length
  }
  if (!token) {
    // Capture token BEFORE full snapshot; replay changes catches modifications during paging.
    const first = await deps.reader.changes(undefined, [...types])
    token = first.nextChangesToken
    const start = new Date(now.getTime() - 30 * 86400000).toISOString()
    for (const type of types) {
      try {
        let pageToken: string | undefined
        do {
          owner()
          const page = await deps.reader.page(type, start, now.toISOString(), pageToken)
          await upload(page.records, [], type)
          pageToken = page.pageToken
        } while (pageToken)
      } catch { owner(); failed.push(type) }
    }
    // No checkpoint on partial snapshot: next attempt replays idempotently.
    if (failed.length) return { state: 'partial', records, failed }
    await upload(first.upsertionChanges.map(c => c.record), first.deletionChanges.map(c => c.recordId))
  }
  for (;;) {
    owner()
    const changes = await deps.reader.changes(token, [...types])
    if (changes.changesTokenExpired) {
      await deps.save(null)
      return { state: 'expired', records, failed: ['history-rescan-required'] }
    }
    await upload(changes.upsertionChanges.map(c => c.record), changes.deletionChanges.map(c => c.recordId))
    token = changes.nextChangesToken
    // Commit cursor only after server acknowledgement; failed write => replay, not loss.
    await deps.save({ token, permissions: [...types] })
    if (!changes.hasMore) break
  }
  return { state: granted.length < RECORD_TYPES.length ? 'partial' : records ? 'success' : 'empty', records, failed }
}
