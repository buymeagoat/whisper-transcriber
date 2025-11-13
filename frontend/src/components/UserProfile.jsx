import React, { useEffect, useState } from 'react'
import { User, Mail, Calendar, Shield } from 'lucide-react'
import { authService } from '../services/authService'

const UserProfile = () => {
  const [userInfo, setUserInfo] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await authService.getCurrentUser()
        setUserInfo(user)
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [])

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
      <div className="flex items-center mb-4">
        <User className="w-5 h-5 text-gray-600 dark:text-gray-400 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Admin Profile
        </h2>
      </div>

      <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">
        The application currently runs in single-user mode. These details describe the built-in administrator account.
      </p>

      <div className="space-y-4">
        <div className="flex items-center">
          <User className="w-4 h-4 text-gray-500 mr-3" />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Username</p>
            <p className="text-gray-900 dark:text-white">{userInfo?.username || 'admin'}</p>
          </div>
        </div>

        <div className="flex items-center">
          <Mail className="w-4 h-4 text-gray-500 mr-3" />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</p>
            <p className="text-gray-900 dark:text-white">{userInfo?.email || 'admin@admin.admin'}</p>
          </div>
        </div>

        <div className="flex items-center">
          <Shield className="w-4 h-4 text-gray-500 mr-3" />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Account Role</p>
            <span className="inline-flex px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
              Administrator
            </span>
          </div>
        </div>

        <div className="flex items-center">
          <Calendar className="w-4 h-4 text-gray-500 mr-3" />
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">User ID</p>
            <p className="text-gray-900 dark:text-white">{userInfo?.id || '1'}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserProfile
