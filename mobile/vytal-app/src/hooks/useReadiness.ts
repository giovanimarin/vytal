import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type { ReadinessData, AdvancedMetricsResponse, WellnessFeedback } from '../types/health'

export function useReadiness(userId: string | null, date?: string) {
  return useQuery<ReadinessData>({
    queryKey: ['readiness', userId, date],
    queryFn: async () => {
      const params = date ? `?date=${date}` : ''
      const { data } = await api.get(`/readiness/${userId}${params}`)
      return data
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 min
    retry: false,
  })
}

export function useReadinessHistory(userId: string | null, startDate: string, endDate: string) {
  return useQuery<ReadinessData[]>({
    queryKey: ['readiness-history', userId, startDate, endDate],
    queryFn: async () => {
      const { data } = await api.get(
        `/readiness/${userId}/history?start_date=${startDate}&end_date=${endDate}`
      )
      return data
    },
    enabled: !!userId,
  })
}

export function useAdvancedMetrics(userId: string | null, date: string) {
  return useQuery<AdvancedMetricsResponse>({
    queryKey: ['advanced-metrics', userId, date],
    queryFn: async () => {
      const { data } = await api.get(`/readiness/${userId}/advanced?date=${date}`)
      return data
    },
    enabled: !!userId && !!date,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useWellnessFeedback(userId: string | null, date: string) {
  return useQuery<WellnessFeedback | null>({
    queryKey: ['wellness-feedback', userId, date],
    queryFn: async () => {
      const { data } = await api.get(`/wellness-feedback/${userId}?date=${date}`)
      return data
    },
    enabled: !!userId && !!date,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useSubmitWellnessFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: {
      user_id: string
      date: string
      feeling_score: number
      trained_today: boolean | null
      workout_worth_it: boolean | null
    }) => {
      const { data } = await api.post('/wellness-feedback', payload)
      return data
    },
    onSuccess: (_, { user_id, date }) => {
      queryClient.invalidateQueries({ queryKey: ['wellness-feedback', user_id, date] })
    },
  })
}

export function useSyncHealthData() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      userId,
      startDate,
      endDate,
    }: {
      userId: string
      startDate: string
      endDate: string
    }) => {
      const { data } = await api.post('/health-data/sync', {
        user_id: userId,
        provider: 'google_fit',
        start_date: startDate,
        end_date: endDate,
      })
      return data
    },
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: ['readiness', userId] })
      queryClient.invalidateQueries({ queryKey: ['health-summary', userId] })
    },
  })
}
