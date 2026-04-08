export type ReadinessCategory = 'rest' | 'light' | 'moderate' | 'intense'

export interface AdvancedMetricsResponse {
  user_id: string
  date: string
  social_jetlag: {
    value_hours: number
    interpretation: string
  } | null
  recovery_curve: {
    days_to_full_recovery: number
    interpretation: string
  } | null
  signal_quality: {
    quality_score: number
    quality_label: 'good' | 'moderate' | 'poor'
    interpretation: string
  } | null
}

export interface WellnessFeedback {
  user_id: string
  date: string
  feeling_score: number
  trained_today: boolean | null
  workout_worth_it: boolean | null
  submitted_at: string
}

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

export interface HealthSummary {
  user_id: string
  date: string
  sleep: SleepData | null
  steps: { total_steps: number } | null
  heart_rate: HeartRateData | null
  activity: ActivityData[]
  stress: { stress_score: number | null; available: boolean } | null
}
