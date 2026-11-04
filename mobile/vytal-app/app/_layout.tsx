import { Stack, useRouter, useSegments } from 'expo-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StatusBar } from 'expo-status-bar'
import { useEffect, useState } from 'react'
import { useAuthStore } from '../src/store/authStore'

const queryClient = new QueryClient()

// Screens that do not require authentication
const PUBLIC_SEGMENTS = ['login', 'register', 'profile-setup']

function AuthGate() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const initFromStorage = useAuthStore((s) => s.initFromStorage)
  const router = useRouter()
  const segments = useSegments()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    initFromStorage().then(() => {
      const t = setTimeout(() => setReady(true), 100)
      return () => clearTimeout(t)
    })
  }, [])

  useEffect(() => {
    if (!ready) return
    const currentSegment = segments[0] as string | undefined
    const isPublic = currentSegment ? PUBLIC_SEGMENTS.includes(currentSegment) : false

    if (!isAuthenticated && !isPublic) {
      router.replace('/login')
    } else if (isAuthenticated && (currentSegment === 'login' || currentSegment === 'register')) {
      router.replace('/(dashboard)')
    }
  }, [ready, isAuthenticated, segments])

  return null
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" />
      <AuthGate />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: '#0f172a' } }}>
        <Stack.Screen name="login" />
        <Stack.Screen name="register" />
        <Stack.Screen name="profile-setup" />
        <Stack.Screen name="(dashboard)" />
      </Stack>
    </QueryClientProvider>
  )
}
