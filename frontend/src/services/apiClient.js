import axios from 'axios'
import { API_CONFIG, isDebugEnabled } from '../config'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request/response logging in development
if (isDebugEnabled) {
  apiClient.interceptors.request.use(
    (config) => {
      console.log('🌐 API Request:', config.method?.toUpperCase(), config.url)
      return config
    },
    (error) => {
      console.error('❌ API Request Error:', error)
      return Promise.reject(error)
    }
  )

  apiClient.interceptors.response.use(
    (response) => {
      console.log('✅ API Response:', response.config.method?.toUpperCase(), response.config.url, response.status)
      return response
    },
    (error) => {
      console.error('❌ API Response Error:', error.config?.method?.toUpperCase(), error.config?.url, error.response?.status)
      return Promise.reject(error)
    }
  )
}

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      localStorage.removeItem('auth_token')
      // Redirect to login if needed
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
