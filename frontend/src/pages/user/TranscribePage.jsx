import React from 'react'
import { Upload } from 'lucide-react'

const TranscribePage = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Transcribe Audio
        </h1>
        <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
          <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            Audio transcription interface coming soon...
          </p>
        </div>
      </div>
    </div>
  )
}

export default TranscribePage
