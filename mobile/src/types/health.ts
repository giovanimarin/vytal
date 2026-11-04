export type ReadinessCategory = 'rest' | 'light' | 'moderate' | 'intense'

export interface ReadinessContributions {
  sleep: number
  heart_rate: number
  activity: number
  stress: number | null
}

export interface ReadinessData {
  user_id: string
  date: string
  readiness_score: number
  readiness_category: ReadinessCategory
  sleep_score_contribution: number
  hr_score_contribution: number
  activity_score_contribution: number
  stress_score_contribution: number | null
  insight_text: string
  calculated_at: string
}

export interface SleepData {
  duration_minutes: number
  deep_sleep_minutes: number
  light_sleep_minutes: number
  rem_sleep_minutes: number
  awake_minutes: number
  sleep_score: number | null
}

export interface HeartRateData {
  resting_bpm: number
  average_bpm: number
  max_bpm: number
  min_bpm: number
}

export interface ActivityData {
  activity_type: string
  duration_minutes: number
  intensity: 'low' | 'moderate' | 'high'
  calories_burned: number
}

// ─── Modality Readiness ──────────────────────────────────────────────────────

export type ModalityStatus = 'green' | 'yellow' | 'red'

export interface ModalityReadiness {
  record_id: string
  user_id: string
  date: string
  modality: string
  score: number
  status: ModalityStatus
  recommendation: string
  hrv_available: boolean
  low_confidence: boolean
  calculated_at: string
}

export interface ModalityReadinessResponse {
  user_id: string
  date: string
  modalities: ModalityReadiness[]
}

// ─── Workouts ────────────────────────────────────────────────────────────────

export type WorkoutModality = 'crossfit' | 'corrida' | 'academia' | 'tenis' | 'pilates' | 'surfe' | 'yoga' | 'ciclismo'
export type WorkoutIntensity = 'leve' | 'moderado' | 'intenso'

export interface WorkoutExercise {
  exercise_id: string
  workout_id: string
  name: string
  muscle_groups: string[]
  sets: number | null
  reps: number | null
}

export interface Workout {
  workout_id: string
  user_id: string
  date: string
  modality: WorkoutModality
  intensity: WorkoutIntensity
  duration_min: number
  notes: string | null
  exercises: WorkoutExercise[]
  created_at: string
}

export interface WorkoutInput {
  user_id: string
  modality: WorkoutModality
  intensity: WorkoutIntensity
  duration_min: number
  date?: string
  notes?: string
  exercises?: { name: string; sets?: number; reps?: number }[]
  free_text?: string
}

export interface ExerciseCatalogItem {
  name: string
  primary: string[]
  secondary: string[]
}

// ─── Muscle Recovery ─────────────────────────────────────────────────────────

export type MuscleGroup =
  | 'chest' | 'front_shoulders' | 'rear_shoulders'
  | 'biceps' | 'triceps' | 'upper_back' | 'lower_back'
  | 'core' | 'glutes' | 'quads' | 'hamstrings' | 'calves' | 'hip_flexors'

export interface MuscleRecovery {
  record_id: string
  user_id: string
  date: string
  muscle_group: MuscleGroup
  recovery_score: number
  last_workout_id: string | null
  estimated_full_recovery_at: string | null
  updated_at: string
}

export interface MuscleRecoveryResponse {
  user_id: string
  date: string
  muscles: MuscleRecovery[]
}

export interface MuscleSuggestion {
  suggestion: MuscleGroup | null
  score?: number
  message: string
}

export interface HealthSummary {
  user_id: string
  date: string
  sleep: SleepData | null
  steps: { total_steps: number } | null
  heart_rate: HeartRateData | null
  activity: ActivityData[]
  stress: { stress_score: number | null; available: boolean } | null
}
