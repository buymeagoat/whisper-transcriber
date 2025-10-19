import React from 'react'
import { FileText } from 'lucide-react'

const JobsPage = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          My Jobs
        </h1>
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            Job management interface coming soon...
          </p>
        </div>
      </div>
    </div>
  )
}

export default JobsPage
