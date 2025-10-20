import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/authService'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Check for existing token on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          // Check if token is expired
          if (authService.isTokenExpired()) {
            // Try to refresh token
            try {
              await authService.refreshToken()
              const userData = await authService.getCurrentUser()
              setUser(userData)
            } catch (refreshError) {
              // Refresh failed, clear tokens
              localStorage.removeItem('auth_token')
              localStorage.removeItem('token_expires_at')
              setError('Your session has expired. Please login again.')
            }
          } else {
            // Token is still valid, get user info
            const userData = await authService.getCurrentUser()
            setUser(userData)
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('token_expires_at')
      } finally {
        setLoading(false)
      }
    }

    // Listen for auth expiration events from API client
    const handleAuthExpired = (event) => {
      setUser(null)
      setError(event.detail.message)
    }

    window.addEventListener('auth:expired', handleAuthExpired)
    initializeAuth()

    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired)
    }
  }, [])

  const login = async (email, password) => {
    try {
      setLoading(true)
      setError(null)
      
      const { user: userData, token } = await authService.login(email, password)
      
      // Store token (expiration time is already stored by authService)
      localStorage.setItem('auth_token', token)
      
      // Set user data
      setUser(userData)
      
      return userData
    } catch (error) {
      setError(error.message || 'Login failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const register = async (email, password, fullName) => {
    try {
      setLoading(true)
      setError(null)
      
      const { user: userData, token } = await authService.register(email, password, fullName)
      
      // Store token
      localStorage.setItem('auth_token', token)
      
      // Set user data
      setUser(userData)
      
      return userData
    } catch (error) {
      setError(error.message || 'Registration failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authService.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Always clear local state (authService.logout() clears tokens too)
      setUser(null)
      setError(null)
    }
  }

  const updateUser = (userData) => {
    setUser(prevUser => ({ ...prevUser, ...userData }))
  }

  const clearError = () => {
    setError(null)
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updateUser,
    clearError,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
