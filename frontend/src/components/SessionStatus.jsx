import React, { useState, useEffect } from 'react'
import { Clock, Wifi, WifiOff } from 'lucide-react'
import { authService } from '../services/authService'

const SessionStatus = () => {
  const [timeRemaining, setTimeRemaining] = useState(null)
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    // Update online status
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Update session time remaining
    const updateTimeRemaining = () => {
      const expiresAt = localStorage.getItem('token_expires_at')
      if (expiresAt) {
        const remaining = parseInt(expiresAt) - Date.now()
        if (remaining > 0) {
          setTimeRemaining(remaining)
        } else {
          setTimeRemaining(0)
        }
      } else {
        setTimeRemaining(null)
      }
    }

    updateTimeRemaining()
    const interval = setInterval(updateTimeRemaining, 60000) // Update every minute

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      clearInterval(interval)
    }
  }, [])

  const formatTimeRemaining = (ms) => {
    if (!ms || ms <= 0) return 'Expired'
    
    const minutes = Math.floor(ms / (1000 * 60))
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      const remainingMinutes = minutes % 60
      return `${hours}h ${remainingMinutes}m`
    }
    return `${minutes}m`
  }

  const getStatusColor = () => {
    if (!timeRemaining || timeRemaining <= 0) return 'text-red-500'
    if (timeRemaining <= 5 * 60 * 1000) return 'text-orange-500' // 5 minutes
    return 'text-green-500'
  }

  return (
    <div className="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
      {/* Connection status */}
      <div className="flex items-center space-x-1">
        {isOnline ? (
          <Wifi className="w-3 h-3 text-green-500" />
        ) : (
          <WifiOff className="w-3 h-3 text-red-500" />
        )}
        <span>{isOnline ? 'Online' : 'Offline'}</span>
      </div>

      {/* Session status */}
      {timeRemaining !== null && (
        <div className="flex items-center space-x-1">
          <Clock className={`w-3 h-3 ${getStatusColor()}`} />
          <span className={getStatusColor()}>
            Session: {formatTimeRemaining(timeRemaining)}
          </span>
        </div>
      )}
    </div>
  )
}

export default SessionStatus
