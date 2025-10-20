import React, { useState } from 'react'
import { Bug, Settings, X } from 'lucide-react'
import { APP_CONFIG, FEATURE_FLAGS, API_CONFIG, isDebugEnabled } from '../config'

const DevTools = () => {
  const [isOpen, setIsOpen] = useState(false)
  
  // Only show in development with debug enabled
  if (!isDebugEnabled || !FEATURE_FLAGS.debugTools) {
    return null
  }

  const envInfo = {
    'App Version': APP_CONFIG.version,
    'Environment': APP_CONFIG.nodeEnv,
    'API Base URL': API_CONFIG.baseURL,
    'Debug Mode': APP_CONFIG.debug ? 'Enabled' : 'Disabled',
    'Build Time': new Date().toISOString(),
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 z-50 bg-purple-600 text-white p-3 rounded-full shadow-lg hover:bg-purple-700 transition-colors"
        title="Development Tools"
      >
        <Bug className="w-5 h-5" />
      </button>

      {/* Dev Tools Panel */}
      {isOpen && (
        <div className="fixed bottom-20 right-4 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl w-80 max-h-96 overflow-auto">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <Settings className="w-5 h-5 text-purple-600" />
              <h3 className="font-semibold text-gray-900 dark:text-white">Dev Tools</h3>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Environment Info */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Environment</h4>
              <div className="space-y-1">
                {Object.entries(envInfo).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">{key}:</span>
                    <span className="text-gray-900 dark:text-white font-mono text-xs">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Feature Flags */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Feature Flags</h4>
              <div className="space-y-1">
                {Object.entries(FEATURE_FLAGS).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">{key}:</span>
                    <span className={`text-xs font-medium px-2 py-1 rounded ${
                      value 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' 
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {value ? 'ON' : 'OFF'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Quick Actions</h4>
              <div className="space-y-2">
                <button
                  onClick={() => {
                    localStorage.clear()
                    window.location.reload()
                  }}
                  className="w-full text-left text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                >
                  Clear Local Storage & Reload
                </button>
                <button
                  onClick={() => console.clear()}
                  className="w-full text-left text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Clear Console
                </button>
                <button
                  onClick={() => {
                    const data = {
                      localStorage: {...localStorage},
                      userAgent: navigator.userAgent,
                      url: window.location.href,
                      timestamp: new Date().toISOString(),
                    }
                    console.log('🐛 Debug Info:', data)
                  }}
                  className="w-full text-left text-sm text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
                >
                  Log Debug Info
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default DevTools
