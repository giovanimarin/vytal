import { Platform } from 'react-native'
import { Category, Reader } from './types'

// Lazy native import keeps unsupported platforms/Expo Go on an explicit unavailable path.
const sdk = () => import('react-native-health-connect')
export async function connectHealthConnect() {
  if (Platform.OS !== 'android') throw new Error('Health Connect requer Android')
  const native = await sdk()
  if (await native.getSdkStatus() !== 3 || !await native.initialize()) throw new Error('Health Connect indisponível: instale/atualize a Conexão Saúde e use development build')
  const { RECORD_TYPES } = await import('./types')
  return native.requestPermission(RECORD_TYPES.map(recordType => ({ accessType: 'read' as const, recordType })))
}
export const healthConnectReader: Reader = {
  async permissions() {
    const native = await sdk()
    if (!await native.initialize()) throw new Error('Health Connect não inicializado')
    return (await native.getGrantedPermissions()).filter(p => p.accessType === 'read' && 'recordType' in p).map(p => (p as { recordType: string }).recordType)
  },
  async page(type: Category, start, end, pageToken) {
    const native = await sdk()
    const page = await native.readRecords(type, { timeRangeFilter: { operator: 'between', startTime: start, endTime: end }, pageSize: 200, pageToken })
    return { records: page.records as unknown as Record<string, unknown>[], pageToken: page.pageToken }
  },
  async changes(token, types) {
    const native = await sdk()
    return await native.getChanges({ changesToken: token, recordTypes: types }) as unknown as Awaited<ReturnType<Reader['changes']>>
  },
}
