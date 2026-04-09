import { Stack, useRouter, useSegments } from 'expo-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StatusBar } from 'expo-status-bar'
import { useEffect } from 'react'
import { useAuthStore } from '../src/store/authStore'

const queryClient = new QueryClient()

function AuthGate() {
  const isConnected = useAuthStore((s) => s.isConnected)
  const router = useRouter()
  const segments = useSegments()

  useEffect(() => {
    const inDashboard = segments[0] === '(dashboard)'
    const inLogin = segments[0] === 'login'

    if (!isConnected && !inLogin) {
      router.replace('/login')
    } else if (isConnected && inLogin) {
      router.replace('/(dashboard)')
    }
  }, [isConnected, segments])

  return null
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" />
      <AuthGate />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#0f172a' } }} />
    </QueryClientProvider>
  )
}
