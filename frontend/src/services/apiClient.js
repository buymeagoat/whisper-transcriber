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
  async (config) => {
    // Skip auth for certain endpoints
    if (config.url?.includes('/auth/login') || 
        config.url?.includes('/register') || 
        config.url?.includes('/health')) {
      return config
    }

    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      
      // Check if token needs refresh (but avoid circular dependency)
      const expiresAt = localStorage.getItem('token_expires_at')
      if (expiresAt) {
        const fiveMinutes = 5 * 60 * 1000
        const isExpiringSoon = Date.now() >= (parseInt(expiresAt) - fiveMinutes)
        
        if (isExpiringSoon && !config.url?.includes('/auth/refresh')) {
          try {
            // Try to refresh token
            const refreshResponse = await axios.post('/auth/refresh', {}, {
              baseURL: apiClient.defaults.baseURL,
              headers: { Authorization: `Bearer ${token}` }
            })
            
            const { access_token, expires_in } = refreshResponse.data
            localStorage.setItem('auth_token', access_token)
            localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
            
            // Update the current request with new token
            config.headers.Authorization = `Bearer ${access_token}`
          } catch (refreshError) {
            // If refresh fails, let the request continue with old token
            console.warn('Token refresh failed:', refreshError)
          }
        }
      }
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
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Try to refresh token if this isn't already a refresh request
      if (!originalRequest.url?.includes('/auth/refresh')) {
        const token = localStorage.getItem('auth_token')
        if (token) {
          try {
            const refreshResponse = await axios.post('/auth/refresh', {}, {
              baseURL: apiClient.defaults.baseURL,
              headers: { Authorization: `Bearer ${token}` }
            })

            const { access_token, expires_in } = refreshResponse.data
            localStorage.setItem('auth_token', access_token)
            localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))

            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return apiClient(originalRequest)
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect
            localStorage.removeItem('auth_token')
            localStorage.removeItem('token_expires_at')
          }
        }
      }

      // If we get here, authentication failed
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_expires_at')
      
      // Only redirect if not already on auth pages
      if (!window.location.pathname.includes('/login') && 
          !window.location.pathname.includes('/register')) {
        
        // Dispatch custom event for auth context to handle
        window.dispatchEvent(new CustomEvent('auth:expired', {
          detail: { message: 'Your session has expired. Please login again.' }
        }))
        
        // Redirect after a short delay to allow UI to show message
        setTimeout(() => {
          window.location.href = '/login'
        }, 2000)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
