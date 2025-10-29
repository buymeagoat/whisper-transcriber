import apiClient from './apiClient'

export const authService = {
  async login(email, password) {
    try {
      // Use JSON format as per backend API spec
      const response = await apiClient.post('/auth/login', {
        username: email,  // Backend expects 'username' field
        password: password,
      })
      
      const { access_token, token_type, expires_in } = response.data
      
      if (!access_token) {
        throw new Error('No access token received')
      }
      
      // Store token expiration time
      localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
      
      // Get user info with the token
      const userResponse = await apiClient.get('/auth/me', {
        headers: {
          Authorization: `${token_type} ${access_token}`,
        },
      })
      
      return {
        user: userResponse.data,
        token: access_token,
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
      const response = await apiClient.get('/auth/me')
      return response.data
    } catch (error) {
      throw new Error('Failed to get user information')
    }
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_expires_at')
    }
  },

  async refreshToken() {
    try {
      const response = await apiClient.post('/auth/refresh')
      const { access_token, expires_in } = response.data
      
      if (access_token) {
        localStorage.setItem('auth_token', access_token)
        localStorage.setItem('token_expires_at', Date.now() + (expires_in * 1000))
        return access_token
      }
    } catch (error) {
      // If refresh fails, clear tokens and force logout
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
      const response = await apiClient.put('/auth/user', profileData)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Profile update failed')
    }
  },

  isTokenExpired() {
    const expiresAt = localStorage.getItem('token_expires_at')
    if (!expiresAt) return true
    
    // Add 5 minute buffer before expiration
    const fiveMinutes = 5 * 60 * 1000
    return Date.now() >= (parseInt(expiresAt) - fiveMinutes)
  },

  hasValidToken() {
    const token = localStorage.getItem('auth_token')
    return token && !this.isTokenExpired()
  },

  async ensureValidToken() {
    if (!this.hasValidToken()) {
      const token = localStorage.getItem('auth_token')
      if (token) {
        // Try to refresh the token
        try {
          await this.refreshToken()
          return true
        } catch (error) {
          return false
        }
      }
      return false
    }
    return true
  },
}
