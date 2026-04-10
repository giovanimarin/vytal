import axios from 'axios'
import { useAuthStore } from '../store/authStore'

declare const __DEV__: boolean

// Em desenvolvimento, aponta para o backend local
// Em produção, trocar para a URL do Cloud Run / API Gateway
const PROD_URL = 'https://vytal-backend-production-368456539470.us-central1.run.app/api/v1'

const BASE_URL =
  typeof window !== 'undefined'
    ? __DEV__
      ? 'http://localhost:8002/api/v1'
      : PROD_URL
    : __DEV__
    ? 'http://192.168.2.59:8001/api/v1'
    : PROD_URL

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Track refresh state to prevent concurrent refreshes
let isRefreshing = false
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = []

function processQueue(error: any, token: string | null) {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)))
  failedQueue = []
}

// Request interceptor: attach access token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }
      originalRequest._retry = true
      isRefreshing = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (!refreshToken) {
        useAuthStore.getState().logout()
        isRefreshing = false
        return Promise.reject(error)
      }
      try {
        const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken })
        useAuthStore.getState().setTokens(data.access_token, data.refresh_token)
        processQueue(null, data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        useAuthStore.getState().logout()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    if (__DEV__) {
      console.error('[API Error]', error.response?.status, error.response?.data)
    }
    return Promise.reject(error)
  }
)
