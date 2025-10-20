import React, { useState, useEffect } from 'react'
import { User, Mail, Calendar, Shield, AlertCircle, CheckCircle } from 'lucide-react'
import { authService } from '../services/authService'

const UserProfile = () => {
  const [userInfo, setUserInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: ''
  })

  useEffect(() => {
    loadUserInfo()
  }, [])

  const loadUserInfo = async () => {
    try {
      setLoading(true)
      const user = await authService.getCurrentUser()
      setUserInfo(user)
      setFormData({
        username: user.username || '',
        email: user.email || user.username || ''
      })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load user information' })
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    
    try {
      setLoading(true)
      await authService.updateProfile(formData)
      await loadUserInfo() // Reload user info
      setEditMode(false)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  const handleCancelEdit = () => {
    setEditMode(false)
    setFormData({
      username: userInfo?.username || '',
      email: userInfo?.email || userInfo?.username || ''
    })
    setMessage({ type: '', text: '' })
  }

  if (loading && !userInfo) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="flex items-center mb-4">
            <div className="w-5 h-5 bg-gray-300 rounded mr-2"></div>
            <div className="h-6 bg-gray-300 rounded w-32"></div>
          </div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            <div className="h-10 bg-gray-300 rounded"></div>
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
            <div className="h-10 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <User className="w-5 h-5 text-gray-600 dark:text-gray-400 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            User Profile
          </h2>
        </div>
        {!editMode && (
          <button
            onClick={() => setEditMode(true)}
            className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
          >
            Edit Profile
          </button>
        )}
      </div>

      {message.text && (
        <div className={`mb-4 p-3 rounded-md flex items-center ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200 dark:bg-green-900 dark:text-green-300' 
            : 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-900 dark:text-red-300'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 mr-2" />
          ) : (
            <AlertCircle className="w-4 h-4 mr-2" />
          )}
          {message.text}
        </div>
      )}

      {editMode ? (
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="Enter your username"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="Enter your email"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              } transition duration-150 ease-in-out`}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={handleCancelEdit}
              className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-600 transition duration-150 ease-in-out"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center">
            <User className="w-4 h-4 text-gray-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Username</p>
              <p className="text-gray-900 dark:text-white">{userInfo?.username || 'Not set'}</p>
            </div>
          </div>

          <div className="flex items-center">
            <Mail className="w-4 h-4 text-gray-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</p>
              <p className="text-gray-900 dark:text-white">{userInfo?.email || userInfo?.username || 'Not set'}</p>
            </div>
          </div>

          <div className="flex items-center">
            <Shield className="w-4 h-4 text-gray-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Account Status</p>
              <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                userInfo?.is_active 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
                {userInfo?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          <div className="flex items-center">
            <Calendar className="w-4 h-4 text-gray-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">User ID</p>
              <p className="text-gray-900 dark:text-white">{userInfo?.id || 'Unknown'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserProfile
