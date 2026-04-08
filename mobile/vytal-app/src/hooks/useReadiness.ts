import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type { ReadinessData } from '../types/health'

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
