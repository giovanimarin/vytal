import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type {
  ModalityReadinessResponse,
  MuscleRecoveryResponse,
  MuscleSuggestion,
  Workout,
  WorkoutInput,
  ExerciseCatalogItem,
} from '../types/health'

export function useModalityReadiness(userId: string | null, date?: string) {
  return useQuery<ModalityReadinessResponse>({
    queryKey: ['modality-readiness', userId, date],
    queryFn: async () => {
      const params = date ? `?date=${date}` : ''
      const { data } = await api.get(`/readiness/modalities/${userId}${params}`)
      return data
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useMuscleRecovery(userId: string | null, date?: string) {
  return useQuery<MuscleRecoveryResponse>({
    queryKey: ['muscle-recovery', userId, date],
    queryFn: async () => {
      const params = date ? `?date=${date}` : ''
      const { data } = await api.get(`/muscles/${userId}/recovery${params}`)
      return data
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useMuscleSuggestion(userId: string | null, date?: string) {
  return useQuery<MuscleSuggestion>({
    queryKey: ['muscle-suggestion', userId, date],
    queryFn: async () => {
      const params = date ? `?date=${date}` : ''
      const { data } = await api.get(`/muscles/${userId}/suggestion${params}`)
      return data
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useWorkoutHistory(userId: string | null, startDate: string, endDate: string) {
  return useQuery<Workout[]>({
    queryKey: ['workouts', userId, startDate, endDate],
    queryFn: async () => {
      const { data } = await api.get(
        `/workouts/${userId}?start_date=${startDate}&end_date=${endDate}`
      )
      return data
    },
    enabled: !!userId,
  })
}

export function useExerciseCatalog() {
  return useQuery<ExerciseCatalogItem[]>({
    queryKey: ['exercise-catalog'],
    queryFn: async () => {
      const { data } = await api.get('/workouts/exercises/catalog')
      return data
    },
    staleTime: 60 * 60 * 1000, // catálogo muda raramente
  })
}

export function useRegisterWorkout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: WorkoutInput) => {
      const { data } = await api.post('/workouts', payload)
      return data as Workout
    },
    onSuccess: (_, { user_id, date }) => {
      queryClient.invalidateQueries({ queryKey: ['workouts', user_id] })
      queryClient.invalidateQueries({ queryKey: ['muscle-recovery', user_id] })
      queryClient.invalidateQueries({ queryKey: ['muscle-suggestion', user_id] })
      queryClient.invalidateQueries({ queryKey: ['modality-readiness', user_id] })
    },
  })
}
