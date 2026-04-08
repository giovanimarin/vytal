import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import type { HealthSummary } from '../types/health'

export function useHealthSummary(userId: string | null, date: string) {
  return useQuery<HealthSummary>({
    queryKey: ['health-summary', userId, date],
    queryFn: async () => {
      const { data } = await api.get(`/health-data/${userId}/summary?date=${date}`)
      return data
    },
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
  })
}
