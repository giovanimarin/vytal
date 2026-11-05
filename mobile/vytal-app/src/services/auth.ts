import { isAxiosError } from 'axios'
import { api } from './api'
import { useAuthStore } from '../store/authStore'
import { sessionFromResponse } from '../types/auth'

export async function login(email: string, password: string): Promise<void> {
  const previous = useAuthStore.getState()
  const { data } = await api.post('/auth/login', { email: email.trim(), password })
  if (useAuthStore.getState() !== previous) throw new Error('A sessão mudou.')
  await useAuthStore.getState().setSession(sessionFromResponse(data))
}

export async function register(name: string, email: string, password: string): Promise<void> {
  const previous = useAuthStore.getState()
  const { data } = await api.post('/auth/register', { name: name.trim(), email: email.trim(), password })
  if (useAuthStore.getState() !== previous) throw new Error('A sessão mudou.')
  await useAuthStore.getState().setSession(sessionFromResponse(data))
}

export async function getHealthAuthUrl(provider: string): Promise<{ auth_url: string; state: string }> {
  const { userId, accessToken, isAuthenticated } = useAuthStore.getState()
  if (!isAuthenticated || !userId || !accessToken) throw new Error('Entre na sua conta para conectar uma fonte.')
  const { data } = await api.get(`/connect/${provider}/auth-url`, { params: { user_id: userId } })
  return data
}

export function authErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: unknown }>(error) && typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail
  }
  return error instanceof Error ? error.message : 'Erro desconhecido'
}

export function logout() {
  const refresh = useAuthStore.getState().refreshToken
  useAuthStore.getState().logout()
  if (refresh) void api.post('/auth/logout', { refresh_token: refresh }).catch(() => {})
}
