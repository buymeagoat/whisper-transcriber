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
      const response = await apiClient.post('/register', {
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
    // For now, just clear local storage
    // Backend doesn't seem to have explicit logout endpoint
    localStorage.removeItem('auth_token')
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
}
