import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'

export function useUserProfile() {
  return useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const { data } = await api.get('/users/me')
      return data
    },
    staleTime: 10 * 60 * 1000,
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  const setProfile = useAuthStore((s) => s.setProfile)
  return useMutation({
    mutationFn: async (
      fields: Partial<{
        name: string
        birth_date: string
        weight_kg: number
        height_cm: number
        goal: string
      }>
    ) => {
      const { data } = await api.patch('/users/me', fields)
      return data
    },
    onSuccess: (data) => {
      setProfile(data)
      queryClient.invalidateQueries({ queryKey: ['user-profile'] })
    },
  })
}
