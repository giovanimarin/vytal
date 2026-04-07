import axios from 'axios'

// Em desenvolvimento, aponta para o backend local
// Em produção, trocar para a URL do Cloud Run / API Gateway
const BASE_URL = __DEV__
  ? 'http://192.168.2.59:8001/api/v1'
  : 'https://api.vytal.app/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor para log de erros em desenvolvimento
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (__DEV__) {
      console.error('[API Error]', error.response?.status, error.response?.data)
    }
    return Promise.reject(error)
  }
)
