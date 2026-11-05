import { api } from './api'
import { useAuthStore } from './store'

interface AuthResponse {
  user_id: string; email: string; name?: string
  access_token: string; refresh_token: string; password?: string
}
async function authenticate(url: string, body?: { email: string; password: string; name?: string }) {
  const version = useAuthStore.getState().sessionVersion
  const { data } = await api.post<AuthResponse>(url, body)
  if (useAuthStore.getState().sessionVersion !== version) throw new Error('A sessão mudou.')
  if (typeof data.refresh_token !== 'string' || !data.refresh_token.trim()) throw new Error('Sessão inválida.')
  useAuthStore.getState().setAuth(data.user_id, data.email, data.name || 'Usuário', data.access_token, data.refresh_token)
  const established = useAuthStore.getState().sessionVersion
  try {
    const { data: me } = await api.get('/users/me')
    useAuthStore.getState().setProfile({ gender: me.gender, preferredModalities: me.preferred_modalities ?? [] })
  } catch {
    // A profile network failure does not invalidate valid credentials. A definitive
    // 401 is handled by the adapter and changes the session version below.
  }
  if (useAuthStore.getState().sessionVersion !== established) throw new Error('A sessão mudou.')
  return data
}
export const login = (email: string, password: string) => authenticate('/auth/login', { email, password })
export const register = (name: string, email: string, password: string) => authenticate('/auth/register', { name, email, password })
export const seedDemo = () => authenticate('/dev/seed')
export function logout() {
  const refresh = useAuthStore.getState().refreshToken
  useAuthStore.getState().clear()
  if (refresh) void api.post('/auth/logout', { refresh_token: refresh }).catch(() => {})
}
