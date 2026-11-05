import axios, { InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from './store'
import { createSessionRefresh } from './sessionRefresh'

export const api = axios.create({
  baseURL: '/api/v1', timeout: 15000, headers: { 'Content-Type': 'application/json' },
})
function redirectToLogin() {
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') window.location.href = '/login'
}
interface SessionRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
  _sessionVersion?: number
  _accountId?: string | null
  _accessToken?: string | null
}
const isAuthEndpoint = (url = '') => /^\/?auth\/(login|register|refresh|logout)(\?|$)/.test(url) || url === '/dev/seed'
const renewOnce = createSessionRefresh()

api.interceptors.request.use((config: SessionRequest) => {
  if (isAuthEndpoint(config.url)) return config
  if (config._sessionVersion !== undefined && config._sessionVersion !== useAuthStore.getState().sessionVersion) {
    throw new Error('A sessão mudou.')
  }
  config._sessionVersion = useAuthStore.getState().sessionVersion
  const state = useAuthStore.getState()
  if (!state.accessToken) throw new Error('Entre na sua conta.')
  if (config._accountId !== undefined && config._accountId !== state.userId) {
    throw new Error('A sessão mudou.')
  }
  config._accountId = state.userId
  config._accessToken = state.accessToken
  config.headers.Authorization = `Bearer ${state.accessToken}`
  return config
})

async function refreshSession(): Promise<void> {
  const previous = useAuthStore.getState()
  if (!previous.accessToken || !previous.refreshToken) {
    previous.clear()
    redirectToLogin()
    throw new Error('Sessão expirada.')
  }
  const version = useAuthStore.getState().sessionVersion
  return renewOnce(`${version}:${previous.accessToken}`, async () => {
    try {
      // Auth endpoints never recursively refresh, including a rejected refresh.
      const { data } = await api.post('/auth/refresh', { refresh_token: previous.refreshToken })
      const current = useAuthStore.getState()
      if (useAuthStore.getState().sessionVersion !== version || current.accessToken !== previous.accessToken || current.refreshToken !== previous.refreshToken
          || current.userId !== previous.userId) throw new Error('A sessão mudou.')
      if (typeof data.access_token !== 'string' || !data.access_token.trim()
          || typeof data.refresh_token !== 'string' || !data.refresh_token.trim()) {
        throw new Error('Resposta de autenticação inválida.')
      }
      current.setTokens(data.access_token, data.refresh_token)
    } catch (error) {
      const current = useAuthStore.getState()
      if (useAuthStore.getState().sessionVersion === version && current.accessToken === previous.accessToken && current.refreshToken === previous.refreshToken) {
        current.clear()
        redirectToLogin()
      }
      throw error
    }
  })
}

api.interceptors.response.use(
  (response) => {
    const config = response.config as SessionRequest
    if (!isAuthEndpoint(config.url) && (config._sessionVersion !== useAuthStore.getState().sessionVersion
        || config._accountId !== useAuthStore.getState().userId)) {
      throw new Error('A sessão mudou.')
    }
    return response
  },
  async (error) => {
    const original = error.config as SessionRequest | undefined
    if (!original || isAuthEndpoint(original.url) || error.response?.status !== 401) {
      return Promise.reject(error)
    }
    const state = useAuthStore.getState()
    if (original._sessionVersion !== useAuthStore.getState().sessionVersion || state.userId !== original._accountId || !state.accessToken) return Promise.reject(error)
    if (original._retry) {
      if (state.accessToken === original._accessToken) { state.clear(); redirectToLogin() }
      return Promise.reject(error)
    }
    original._retry = true
    // Another request may already have completed the same refresh.
    if (state.accessToken === original._accessToken) await refreshSession()
    return api(original)
  },
)
