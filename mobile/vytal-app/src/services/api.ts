import axios, { InternalAxiosRequestConfig } from 'axios'
import { getSessionVersion, useAuthStore } from '../store/authStore'

import { createSessionRefresh } from './sessionRefresh'

declare const __DEV__: boolean
const PROD_URL = 'https://vytal-backend-production-368456539470.us-central1.run.app/api/v1'
const BASE_URL = typeof window !== 'undefined' ? PROD_URL
  : __DEV__ ? 'http://192.168.2.59:8002/api/v1' : PROD_URL

export const api = axios.create({
  baseURL: BASE_URL, timeout: 15000, headers: { 'Content-Type': 'application/json' },
})
interface SessionRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
  _sessionVersion?: number
  _accountId?: string | null
  _accessToken?: string | null
}
const isAuthEndpoint = (url = '') => /^\/?auth\/(login|register|refresh|logout)(\?|$)/.test(url)
const renewOnce = createSessionRefresh()

api.interceptors.request.use((config: SessionRequest) => {
  if (isAuthEndpoint(config.url)) return config
  if (config._sessionVersion !== undefined && config._sessionVersion !== getSessionVersion()) {
    throw new Error('A sessão mudou.')
  }
  config._sessionVersion = getSessionVersion()
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

export async function refreshSession(): Promise<void> {
  const previous = useAuthStore.getState()
  if (!previous.accessToken || !previous.refreshToken) {
    previous.logout()
    throw new Error('Sessão expirada.')
  }
  const version = getSessionVersion()
  return renewOnce(`${version}:${previous.accessToken}`, async () => {
    try {
      if (getSessionVersion() !== version || useAuthStore.getState().accessToken !== previous.accessToken
          || useAuthStore.getState().refreshToken !== previous.refreshToken) throw new Error('A sessão mudou.')
      // Auth endpoints never recursively refresh, including a rejected refresh.
      const { data } = await api.post('/auth/refresh', { refresh_token: previous.refreshToken })
      const current = useAuthStore.getState()
      if (getSessionVersion() !== version || current.accessToken !== previous.accessToken || current.refreshToken !== previous.refreshToken
          || current.userId !== previous.userId) throw new Error('A sessão mudou.')
      if (typeof data.access_token !== 'string' || !data.access_token.trim()
          || typeof data.refresh_token !== 'string' || !data.refresh_token.trim()) {
        throw new Error('Resposta de autenticação inválida.')
      }
      current.setTokens(data.access_token, data.refresh_token)
    } catch (error) {
      const current = useAuthStore.getState()
      if (getSessionVersion() === version && current.accessToken === previous.accessToken && current.refreshToken === previous.refreshToken) {
        current.logout()
      }
      throw error
    }
  })
}

api.interceptors.response.use(
  (response) => {
    const config = response.config as SessionRequest
    if (!isAuthEndpoint(config.url) && (config._sessionVersion !== getSessionVersion()
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
    if (original._sessionVersion !== getSessionVersion() || state.userId !== original._accountId || !state.accessToken) return Promise.reject(error)
    if (original._retry) {
      if (state.accessToken === original._accessToken) state.logout()
      return Promise.reject(error)
    }
    original._retry = true
    // Another request may already have completed the same refresh.
    if (state.accessToken === original._accessToken) await refreshSession()
    return api(original)
  },
)
