export const RECORD_TYPES = ['ExerciseSession', 'Steps', 'Distance', 'ActiveCaloriesBurned', 'TotalCaloriesBurned',
  'HeartRate', 'RestingHeartRate', 'SleepSession', 'Weight', 'Speed', 'ElevationGained'] as const
export type Category = typeof RECORD_TYPES[number]
export interface ImportedRecord {
  category: Category
  id: string
  origin: string
  start: string
  end: string
  values: Record<string, unknown>
  metadata: Record<string, unknown>
  native: Record<string, unknown>
  aliases?: { id: string; origin: string }[]
}
export interface Changes {
  upsertionChanges: { record: Record<string, unknown> }[]
  deletionChanges: { recordId: string }[]
  nextChangesToken: string
  changesTokenExpired: boolean
  hasMore: boolean
}
export interface Reader {
  permissions(): Promise<string[]>
  page(type: Category, start: string, end: string, pageToken?: string): Promise<{ records: Record<string, unknown>[]; pageToken?: string }>
  changes(token: string | undefined, types: Category[]): Promise<Changes>
}
