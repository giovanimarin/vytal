import axios from 'axios'

// Em desenvolvimento, aponta para o backend local
// Em produção, trocar para a URL do Cloud Run / API Gateway
const PROD_URL = 'https://vytal-backend-production-368456539470.us-central1.run.app/api/v1'

const BASE_URL = typeof window !== 'undefined'
  ? (__DEV__ ? 'http://localhost:8002/api/v1' : PROD_URL)
  : __DEV__
    ? 'http://192.168.2.59:8001/api/v1'
    : PROD_URL

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
