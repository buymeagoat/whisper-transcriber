import React, { useState } from 'react'
import { Lock, AlertCircle, CheckCircle } from 'lucide-react'
import { authService } from '../services/authService'

const PasswordChangeForm = () => {
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [errors, setErrors] = useState({})

  const validatePassword = (password) => {
    const minLength = 8
    const hasUpper = /[A-Z]/.test(password)
    const hasLower = /[a-z]/.test(password)
    const hasNumber = /\d/.test(password)
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password)

    return {
      isValid: password.length >= minLength && hasUpper && hasLower && hasNumber,
      requirements: {
        minLength: password.length >= minLength,
        hasUpper,
        hasLower, 
        hasNumber,
        hasSpecial
      }
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
    
    // Clear message when user starts typing
    if (message.text) {
      setMessage({ type: '', text: '' })
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.currentPassword) {
      newErrors.currentPassword = 'Current password is required'
    }

    if (!formData.newPassword) {
      newErrors.newPassword = 'New password is required'
    } else {
      const passwordValidation = validatePassword(formData.newPassword)
      if (!passwordValidation.isValid) {
        newErrors.newPassword = 'Password must be at least 8 characters with uppercase, lowercase, and number'
      }
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your new password'
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    if (formData.currentPassword === formData.newPassword) {
      newErrors.newPassword = 'New password must be different from current password'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)
    try {
      await authService.changePassword(formData.currentPassword, formData.newPassword)
      setMessage({ type: 'success', text: 'Password changed successfully!' })
      
      // Clear form
      setFormData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  const passwordValidation = validatePassword(formData.newPassword)

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex items-center mb-4">
        <Lock className="w-5 h-5 text-gray-600 dark:text-gray-400 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Change Password
        </h2>
      </div>

      {message.text && (
        <div className={`mb-4 p-3 rounded-md flex items-center ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 mr-2" />
          ) : (
            <AlertCircle className="w-4 h-4 mr-2" />
          )}
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Current Password
          </label>
          <input
            type="password"
            id="currentPassword"
            name="currentPassword"
            value={formData.currentPassword}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
              errors.currentPassword ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your current password"
          />
          {errors.currentPassword && (
            <p className="mt-1 text-sm text-red-600">{errors.currentPassword}</p>
          )}
        </div>

        <div>
          <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            New Password
          </label>
          <input
            type="password"
            id="newPassword"
            name="newPassword"
            value={formData.newPassword}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
              errors.newPassword ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Enter your new password"
          />
          {errors.newPassword && (
            <p className="mt-1 text-sm text-red-600">{errors.newPassword}</p>
          )}
          
          {formData.newPassword && (
            <div className="mt-2 space-y-1">
              <p className="text-xs text-gray-600 dark:text-gray-400">Password requirements:</p>
              <div className="grid grid-cols-2 gap-1 text-xs">
                <div className={`flex items-center ${passwordValidation.requirements.minLength ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">•</span> At least 8 characters
                </div>
                <div className={`flex items-center ${passwordValidation.requirements.hasUpper ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">•</span> Uppercase letter
                </div>
                <div className={`flex items-center ${passwordValidation.requirements.hasLower ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">•</span> Lowercase letter
                </div>
                <div className={`flex items-center ${passwordValidation.requirements.hasNumber ? 'text-green-600' : 'text-gray-400'}`}>
                  <span className="mr-1">•</span> Number
                </div>
              </div>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Confirm New Password
          </label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
              errors.confirmPassword ? 'border-red-300' : 'border-gray-300'
            }`}
            placeholder="Confirm your new password"
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
          )}
          
          {formData.confirmPassword && formData.newPassword && formData.confirmPassword === formData.newPassword && (
            <p className="mt-1 text-sm text-green-600 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              Passwords match
            </p>
          )}
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={loading}
            className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
            } transition duration-150 ease-in-out`}
          >
            {loading ? 'Changing Password...' : 'Change Password'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default PasswordChangeForm
