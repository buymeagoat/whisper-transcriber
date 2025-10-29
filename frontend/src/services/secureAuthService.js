import apiClient from './apiClient'

export const secureAuthService = {
  async login(email, password) {
    try {
      // Use JSON format as per backend API spec
      const response = await apiClient.post('/auth/login', {
        username: email,  // Backend expects 'username' field
        password: password,
      }, {
        // Include CSRF protection header
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      
      const { access_token, token_type, expires_in } = response.data
      
      if (!access_token) {
        throw new Error('No access token received')
      }
      
      // Note: Token is now stored in secure httpOnly cookie by the server
      // We only store expiration time in sessionStorage (not localStorage)
      sessionStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
      
      // Get user info (token will come from cookie automatically)
      const userResponse = await apiClient.get('/auth/me', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      
      return {
        user: userResponse.data,
        // Don't return the actual token since it's in httpOnly cookie
        tokenExpiry: Date.now() + (expires_in * 1000)
      }
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Invalid email or password')
      }
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  },

  async register(email, password, fullName) {
    try {
      const response = await apiClient.post('/auth/register', {
        username: email,  // Backend expects 'username' field
        password: password,
        email: email,     // Also send as email field
      }, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      
      // Auto-login after registration
      return this.login(email, password)
    } catch (error) {
      if (error.response?.status === 400) {
        throw new Error(error.response.data?.detail || 'Registration failed')
      }
      throw new Error('Registration failed')
    }
  },

  async getCurrentUser() {
    try {
      const response = await apiClient.get('/auth/me', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      return response.data
    } catch (error) {
      throw new Error('Failed to get user information')
    }
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout', {}, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear session storage (cookies cleared by server)
      sessionStorage.removeItem('token_expires_at')
      
      // Clear any remaining localStorage items
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_expires_at')
    }
  },

  async refreshToken() {
    try {
      const response = await apiClient.post('/auth/refresh', {}, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      const { access_token, expires_in } = response.data
      
      if (access_token) {
        // Update expiration time (token automatically updated in cookie)
        sessionStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
        return true
      }
    } catch (error) {
      // If refresh fails, clear session data
      sessionStorage.removeItem('token_expires_at')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_expires_at')
      throw new Error('Session expired. Please login again.')
    }
  },

  async changePassword(currentPassword, newPassword) {
    try {
      const response = await apiClient.post('/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      }, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      return response.data
    } catch (error) {
      if (error.response?.status === 400) {
        throw new Error(error.response.data?.detail || 'Password change failed')
      }
      throw new Error('Password change failed')
    }
  },

  async updateProfile(profileData) {
    try {
      const response = await apiClient.put('/auth/user', profileData, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Profile update failed')
    }
  },

  isTokenExpired() {
    // Check both sessionStorage and localStorage for backwards compatibility
    const expiresAt = sessionStorage.getItem('token_expires_at') || 
                     localStorage.getItem('token_expires_at')
    if (!expiresAt) return true
    
    // Add 5 minute buffer before expiration
    const fiveMinutes = 5 * 60 * 1000
    return Date.now() >= (parseInt(expiresAt) - fiveMinutes)
  },

  hasValidSession() {
    // With httpOnly cookies, we can't directly check the token
    // We rely on the expiration time and let the API handle validation
    return !this.isTokenExpired()
  },

  async ensureValidSession() {
    if (!this.hasValidSession()) {
      try {
        // Try to refresh the session
        await this.refreshToken()
        return true
      } catch (error) {
        return false
      }
    }
    return true
  },

  // Security helper methods
  sanitizeInput(input) {
    if (typeof input !== 'string') return input
    
    // Basic XSS prevention
    return input
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
      .replace(/\//g, '&#x2F;')
  },

  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  validatePassword(password) {
    // Minimum 8 characters, at least one letter and one number
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/
    return passwordRegex.test(password)
  },

  // Session security validation
  validateSessionSecurity() {
    const checks = {
      hasSecureContext: window.isSecureContext,
      hasCSRFProtection: this._hasCSRFProtection(),
      validUserAgent: this._hasValidUserAgent(),
      secureConnection: location.protocol === 'https:' || location.hostname === 'localhost'
    }

    return {
      isSecure: Object.values(checks).every(Boolean),
      checks
    }
  },

  _hasCSRFProtection() {
    // Check if we're sending CSRF protection headers
    return true // We always send X-Requested-With header
  },

  _hasValidUserAgent() {
    return navigator.userAgent && navigator.userAgent.length > 10
  }
}

export default secureAuthService