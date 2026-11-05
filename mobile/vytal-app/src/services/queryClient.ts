import { QueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'

export const queryClient = new QueryClient()

// A shared client outlives screens; account changes must evict the old account's data.
useAuthStore.subscribe((state, previous) => {
  if (state.userId !== previous.userId) queryClient.clear()
})
