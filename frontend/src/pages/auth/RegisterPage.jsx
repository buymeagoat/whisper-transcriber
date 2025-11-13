import React from 'react'
import { Link, Navigate } from 'react-router-dom'
import { Lock, Mic } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const RegisterPage = () => {
  const { user } = useAuth()

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Mic className="w-12 h-12 text-blue-600" />
        </div>
        <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
          Single-User Mode Active
        </h1>
        <p className="mt-4 text-center text-gray-600 dark:text-gray-300">
          This deployment is intentionally locked to the built-in <strong>admin</strong> account. 
          Additional user registration is disabled while we focus on personal workflows.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-gray-800 py-8 px-6 shadow sm:rounded-lg">
          <div className="flex items-center justify-center mb-6">
            <Lock className="w-10 h-10 text-blue-600" />
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-center mb-6">
            Use the credentials <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">admin</code>
            and your configured password to access the application (default 
            <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">super-secret-password-!123</code>).
            You can rotate the password from the admin dashboard at any time.
          </p>
          <Link
            to="/login"
            className="block text-center w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </Link>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
