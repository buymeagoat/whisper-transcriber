import React from 'react'
import { Settings } from 'lucide-react'
import UserProfile from '../../components/UserProfile'
import PasswordChangeForm from '../../components/PasswordChangeForm'

const SettingsPage = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center mb-6">
          <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400 mr-3" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Account Settings
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Manage your account information and security settings.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
        <UserProfile />
        <PasswordChangeForm />
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Preferences
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Email Notifications
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Receive notifications about transcription completion
              </p>
            </div>
            <input
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              defaultChecked
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Auto-delete files
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Automatically delete audio files after 30 days
              </p>
            </div>
            <input
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Dark Mode
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Use dark theme for the interface
              </p>
            </div>
            <input
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
