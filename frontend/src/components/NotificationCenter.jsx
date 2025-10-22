/**
 * T029 Enhanced User Experience: Real-time Notification Component
 * React component for displaying and managing real-time notifications
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, 
  X, 
  CheckCircle, 
  AlertCircle, 
  Info, 
  AlertTriangle,
  Eye,
  Trash2,
  Settings,
  Wifi,
  WifiOff,
  Download,
  ExternalLink
} from 'lucide-react';
import notificationService from '../services/notificationService';

const NotificationCenter = ({ className = '' }) => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState({ connected: false });
  const [showSettings, setShowSettings] = useState(false);
  const [permissionStatus, setPermissionStatus] = useState('default');
  const [filter, setFilter] = useState('all');

  const dropdownRef = useRef(null);
  const subscriptionRef = useRef(null);

  useEffect(() => {
    // Load initial notifications
    setNotifications(notificationService.getNotifications());
    setUnreadCount(notificationService.getUnreadCount());
    setConnectionStatus(notificationService.getConnectionStatus());
    setPermissionStatus(notificationService.getPermissionStatus());

    // Subscribe to notification events
    subscriptionRef.current = notificationService.subscribe((event, data) => {
      switch (event) {
        case 'new_notification':
          setNotifications(notificationService.getNotifications());
          setUnreadCount(notificationService.getUnreadCount());
          break;
          
        case 'notification_read':
        case 'all_notifications_read':
        case 'notification_removed':
        case 'notifications_cleared':
          setNotifications(notificationService.getNotifications());
          setUnreadCount(notificationService.getUnreadCount());
          break;
          
        case 'connection':
          setConnectionStatus(notificationService.getConnectionStatus());
          break;
          
        case 'notification_action':
          handleNotificationAction(data);
          break;
          
        default:
          // Update for any other events
          setNotifications(notificationService.getNotifications());
          setUnreadCount(notificationService.getUnreadCount());
      }
    });

    // Click outside handler
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setShowSettings(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      if (subscriptionRef.current) {
        notificationService.unsubscribe(subscriptionRef.current);
      }
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleNotificationAction = (action) => {
    switch (action.action) {
      case 'view_job':
        window.location.href = `/jobs/${action.job_id}`;
        break;
      case 'download_job':
        // Trigger download
        console.log('Download job:', action.job_id);
        break;
      case 'retry_job':
        // Retry job
        console.log('Retry job:', action.job_id);
        break;
      case 'view_batch':
        window.location.href = `/batch-upload?batch=${action.batch_id}`;
        break;
      case 'download_batch':
        // Trigger batch download
        console.log('Download batch:', action.batch_id);
        break;
      default:
        console.log('Unknown action:', action);
    }
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
    setShowSettings(false);
    
    // Mark notifications as read when opened
    if (!isOpen && unreadCount > 0) {
      setTimeout(() => {
        notificationService.markAllAsRead();
      }, 1000);
    }
  };

  const handleMarkAsRead = (notificationId) => {
    notificationService.markAsRead(notificationId);
  };

  const handleRemoveNotification = (notificationId) => {
    notificationService.removeNotification(notificationId);
  };

  const handleClearAll = () => {
    notificationService.clearAll();
  };

  const handleRequestPermission = async () => {
    const granted = await notificationService.requestPermission();
    setPermissionStatus(granted ? 'granted' : 'denied');
  };

  const getNotificationIcon = (level) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getNotificationColor = (level) => {
    switch (level) {
      case 'success':
        return 'border-l-green-500 bg-green-50';
      case 'error':
        return 'border-l-red-500 bg-red-50';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50';
      default:
        return 'border-l-blue-500 bg-blue-50';
    }
  };

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return timestamp.toLocaleDateString();
  };

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !notification.read;
    return notification.type === filter;
  });

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Notification Bell */}
      <button
        onClick={toggleDropdown}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        title={`${unreadCount} unread notifications`}
      >
        <Bell className="w-6 h-6" />
        
        {/* Unread Count Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Connection Status Indicator */}
        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${
          connectionStatus.connected ? 'bg-green-500' : 'bg-red-500'
        }`} />
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          {showSettings ? (
            /* Settings Panel */
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Notification Settings</h3>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Browser Permissions */}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Browser Notifications</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      permissionStatus === 'granted' 
                        ? 'bg-green-100 text-green-800' 
                        : permissionStatus === 'denied'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {permissionStatus}
                    </span>
                  </div>
                  {permissionStatus !== 'granted' && (
                    <button
                      onClick={handleRequestPermission}
                      className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                    >
                      Enable Notifications
                    </button>
                  )}
                </div>

                {/* Connection Status */}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Real-time Connection</span>
                    <div className="flex items-center">
                      {connectionStatus.connected ? (
                        <>
                          <Wifi className="w-4 h-4 text-green-500 mr-1" />
                          <span className="text-xs text-green-600">Connected</span>
                        </>
                      ) : (
                        <>
                          <WifiOff className="w-4 h-4 text-red-500 mr-1" />
                          <span className="text-xs text-red-600">Disconnected</span>
                        </>
                      )}
                    </div>
                  </div>
                  {connectionStatus.reconnectAttempts > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      Reconnection attempts: {connectionStatus.reconnectAttempts}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* Notifications Panel */
            <>
              {/* Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    Notifications {unreadCount > 0 && `(${unreadCount})`}
                  </h3>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setShowSettings(true)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Settings"
                    >
                      <Settings className="w-5 h-5" />
                    </button>
                    {notifications.length > 0 && (
                      <button
                        onClick={handleClearAll}
                        className="text-gray-400 hover:text-gray-600"
                        title="Clear All"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Filter Tabs */}
                <div className="flex space-x-1 mt-3">
                  {[
                    { key: 'all', label: 'All' },
                    { key: 'unread', label: 'Unread' },
                    { key: 'job_update', label: 'Jobs' },
                    { key: 'batch_update', label: 'Batches' },
                    { key: 'system_alert', label: 'System' }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setFilter(tab.key)}
                      className={`px-3 py-1 text-xs rounded-full transition-colors ${
                        filter === tab.key
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Notifications List */}
              <div className="max-h-80 overflow-y-auto">
                {filteredNotifications.length === 0 ? (
                  <div className="p-8 text-center">
                    <Bell className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">No notifications</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {filteredNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-4 hover:bg-gray-50 transition-colors ${
                          !notification.read ? 'border-l-4 ' + getNotificationColor(notification.level) : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3 flex-1">
                            {getNotificationIcon(notification.level)}
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h4 className={`text-sm font-medium ${
                                  !notification.read ? 'text-gray-900' : 'text-gray-600'
                                }`}>
                                  {notification.title}
                                </h4>
                                <span className="text-xs text-gray-500 ml-2">
                                  {formatTimestamp(notification.timestamp)}
                                </span>
                              </div>
                              
                              <p className="text-sm text-gray-600 mt-1">
                                {notification.message}
                              </p>
                              
                              {/* Progress bar for job updates */}
                              {notification.type === 'job_update' && notification.progress && (
                                <div className="mt-2">
                                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                                    <span>Progress</span>
                                    <span>{Math.round(notification.progress)}%</span>
                                  </div>
                                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                                    <div 
                                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                      style={{ width: `${notification.progress}%` }}
                                    />
                                  </div>
                                </div>
                              )}
                              
                              {/* Action buttons */}
                              {notification.actions && notification.actions.length > 0 && (
                                <div className="flex space-x-2 mt-2">
                                  {notification.actions.map((action, index) => (
                                    <button
                                      key={index}
                                      onClick={() => handleNotificationAction(action)}
                                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                                    >
                                      {action.action.includes('download') && (
                                        <Download className="w-3 h-3 mr-1" />
                                      )}
                                      {action.action.includes('view') && (
                                        <ExternalLink className="w-3 h-3 mr-1" />
                                      )}
                                      {action.label}
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* Notification controls */}
                          <div className="flex items-center space-x-1 ml-2">
                            {!notification.read && (
                              <button
                                onClick={() => handleMarkAsRead(notification.id)}
                                className="text-gray-400 hover:text-gray-600"
                                title="Mark as read"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleRemoveNotification(notification.id)}
                              className="text-gray-400 hover:text-gray-600"
                              title="Remove"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;