import axios from 'axios'
import { API_CONFIG, isDebugEnabled } from '../config'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  withCredentials: true,  // Include cookies in all requests
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

// Request interceptor to add auth token and security headers
apiClient.interceptors.request.use(
  async (config) => {
    // Add CSRF protection header for all requests
    config.headers['X-Requested-With'] = 'XMLHttpRequest'
    
    // Skip auth token for certain endpoints (cookies will be sent automatically)
    if (config.url?.includes('/auth/login') || 
      config.url?.includes('/health')) {
      return config
    }

    // For backwards compatibility, still check localStorage for legacy tokens
    const legacyToken = localStorage.getItem('auth_token')
    if (legacyToken) {
      config.headers.Authorization = `Bearer ${legacyToken}`
      
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
              headers: { 
                Authorization: `Bearer ${legacyToken}`,
                'X-Requested-With': 'XMLHttpRequest'
              }
            })
            
            const { access_token, expires_in } = refreshResponse.data
            
            // Migrate to sessionStorage and clear localStorage
            sessionStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
            localStorage.removeItem('auth_token')
            localStorage.removeItem('token_expires_at')
            
            // Don't update header - let cookies handle it
          } catch (refreshError) {
            console.warn('Token refresh failed during migration:', refreshError)
            // Clear legacy tokens
            localStorage.removeItem('auth_token')
            localStorage.removeItem('token_expires_at')
          }
        }
      }
    }
    
    // Note: httpOnly cookies are sent automatically by the browser
    // No need to manually add them to headers
    
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
        try {
          // Try to refresh using secure cookies
          const refreshResponse = await axios.post('/auth/refresh', {}, {
            baseURL: apiClient.defaults.baseURL,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            withCredentials: true  // Include cookies
          })

          const { expires_in } = refreshResponse.data
          
          // Update session storage with new expiration
          sessionStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))

          // Retry the original request (cookies will be included automatically)
          return apiClient(originalRequest)
        } catch (refreshError) {
          // Refresh failed, clear session data
          sessionStorage.removeItem('token_expires_at')
          localStorage.removeItem('auth_token')
          localStorage.removeItem('token_expires_at')
        }
      }

      // If we get here, authentication failed
      sessionStorage.removeItem('token_expires_at')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_expires_at')
      
      // Only redirect if not already on auth pages
        if (!window.location.pathname.includes('/login')) {
        
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
