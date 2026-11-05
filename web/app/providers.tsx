'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { useAuthStore } from '@/lib/store'

export default function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 5 * 60 * 1000, retry: false } },
  }))
  useEffect(() => useAuthStore.subscribe((state, previous) => {
    if (state.sessionVersion !== previous.sessionVersion) qc.clear()
  }), [qc])
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}
