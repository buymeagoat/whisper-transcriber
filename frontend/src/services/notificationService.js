/**
 * T029 Enhanced User Experience: Real-time Notification Service
 * Service for managing real-time notifications via WebSocket with persistent history
 */

import { v4 as uuidv4 } from 'uuid';

class NotificationService {
  constructor() {
    this.notifications = [];
    this.subscribers = new Map();
    this.websocket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnected = false;
    this.lastHeartbeat = null;
    this.heartbeatInterval = null;
    this.notificationHistory = this.loadNotificationHistory();
    
    this.initializeWebSocket();
    this.startHeartbeat();
  }

  /**
   * Initialize WebSocket connection for real-time notifications
   */
  initializeWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/notifications`;
      
      this.websocket = new WebSocket(wsUrl);
      
      this.websocket.onopen = () => {
        console.log('Notification WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Send authentication token if available
        const token = localStorage.getItem('token');
        if (token) {
          this.websocket.send(JSON.stringify({
            type: 'auth',
            token: token
          }));
        }
        
        this.notifySubscribers('connection', { status: 'connected' });
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.websocket.onclose = (event) => {
        console.log('Notification WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.notifySubscribers('connection', { status: 'disconnected' });
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
      
      this.websocket.onerror = (error) => {
        console.error('Notification WebSocket error:', error);
        this.notifySubscribers('connection', { status: 'error', error });
      };
      
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleWebSocketMessage(data) {
    this.lastHeartbeat = Date.now();
    
    switch (data.type) {
      case 'notification':
        this.addNotification(data.notification);
        break;
        
      case 'job_update':
        this.handleJobUpdate(data);
        break;
        
      case 'batch_update':
        this.handleBatchUpdate(data);
        break;
        
      case 'system_alert':
        this.handleSystemAlert(data);
        break;
        
      case 'heartbeat':
        // Respond to server heartbeat
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({ type: 'heartbeat_response' }));
        }
        break;
        
      case 'auth_response':
        if (data.success) {
          console.log('WebSocket authentication successful');
        } else {
          console.error('WebSocket authentication failed:', data.error);
        }
        break;
        
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  /**
   * Handle job status updates
   */
  handleJobUpdate(data) {
    const { job_id, status, progress, error, result } = data;
    
    let notification = {
      id: uuidv4(),
      type: 'job_update',
      timestamp: new Date(),
      job_id,
      status,
      progress,
      read: false
    };

    switch (status) {
      case 'completed':
        notification.title = 'Transcription Complete';
        notification.message = `Job ${job_id} has been completed successfully`;
        notification.level = 'success';
        notification.actions = [
          { label: 'View Result', action: 'view_job', job_id },
          { label: 'Download', action: 'download_job', job_id }
        ];
        break;
        
      case 'failed':
        notification.title = 'Transcription Failed';
        notification.message = `Job ${job_id} failed: ${error || 'Unknown error'}`;
        notification.level = 'error';
        notification.actions = [
          { label: 'View Details', action: 'view_job', job_id },
          { label: 'Retry', action: 'retry_job', job_id }
        ];
        break;
        
      case 'processing':
        notification.title = 'Transcription Started';
        notification.message = `Job ${job_id} is now being processed`;
        notification.level = 'info';
        notification.actions = [
          { label: 'View Progress', action: 'view_job', job_id }
        ];
        break;
        
      case 'queued':
        notification.title = 'Job Queued';
        notification.message = `Job ${job_id} has been added to the processing queue`;
        notification.level = 'info';
        break;
        
      default:
        notification.title = 'Job Update';
        notification.message = `Job ${job_id} status: ${status}`;
        notification.level = 'info';
    }

    this.addNotification(notification);
    this.notifySubscribers('job_update', data);
  }

  /**
   * Handle batch processing updates
   */
  handleBatchUpdate(data) {
    const { batch_id, status, completed_files, total_files, failed_files } = data;
    
    const notification = {
      id: uuidv4(),
      type: 'batch_update',
      timestamp: new Date(),
      batch_id,
      status,
      read: false
    };

    switch (status) {
      case 'completed':
        notification.title = 'Batch Processing Complete';
        notification.message = `Batch ${batch_id} completed: ${completed_files}/${total_files} files processed`;
        notification.level = failed_files > 0 ? 'warning' : 'success';
        notification.actions = [
          { label: 'View Results', action: 'view_batch', batch_id },
          { label: 'Download All', action: 'download_batch', batch_id }
        ];
        break;
        
      case 'failed':
        notification.title = 'Batch Processing Failed';
        notification.message = `Batch ${batch_id} failed to process`;
        notification.level = 'error';
        notification.actions = [
          { label: 'View Details', action: 'view_batch', batch_id }
        ];
        break;
        
      case 'processing':
        notification.title = 'Batch Processing';
        notification.message = `Batch ${batch_id}: ${completed_files}/${total_files} files completed`;
        notification.level = 'info';
        notification.actions = [
          { label: 'View Progress', action: 'view_batch', batch_id }
        ];
        break;
        
      default:
        notification.title = 'Batch Update';
        notification.message = `Batch ${batch_id} status: ${status}`;
        notification.level = 'info';
    }

    this.addNotification(notification);
    this.notifySubscribers('batch_update', data);
  }

  /**
   * Handle system alerts
   */
  handleSystemAlert(data) {
    const { level, title, message, actions } = data;
    
    const notification = {
      id: uuidv4(),
      type: 'system_alert',
      timestamp: new Date(),
      title: title || 'System Alert',
      message: message || 'System notification',
      level: level || 'info',
      actions: actions || [],
      read: false,
      persistent: level === 'error' || level === 'warning'
    };

    this.addNotification(notification);
    this.notifySubscribers('system_alert', data);
  }

  /**
   * Add notification to the list and persist
   */
  addNotification(notification) {
    // Ensure notification has required fields
    if (!notification.id) notification.id = uuidv4();
    if (!notification.timestamp) notification.timestamp = new Date();
    if (!notification.read) notification.read = false;
    if (!notification.level) notification.level = 'info';

    // Add to beginning of list
    this.notifications.unshift(notification);
    
    // Limit to 100 notifications in memory
    if (this.notifications.length > 100) {
      this.notifications = this.notifications.slice(0, 100);
    }

    // Persist to localStorage
    this.saveNotificationHistory();
    
    // Notify subscribers
    this.notifySubscribers('new_notification', notification);
    
    // Show browser notification if permitted
    this.showBrowserNotification(notification);
  }

  /**
   * Show browser notification
   */
  showBrowserNotification(notification) {
    if ('Notification' in window && Notification.permission === 'granted') {
      const options = {
        body: notification.message,
        icon: '/icon-192x192.png',
        tag: notification.id,
        badge: '/icon-72x72.png',
        requireInteraction: notification.persistent || notification.level === 'error'
      };

      const browserNotification = new Notification(notification.title, options);
      
      browserNotification.onclick = () => {
        window.focus();
        
        // Handle notification actions
        if (notification.actions && notification.actions.length > 0) {
          const primaryAction = notification.actions[0];
          this.handleNotificationAction(primaryAction);
        }
        
        browserNotification.close();
      };

      // Auto-close after 5 seconds unless it requires interaction
      if (!options.requireInteraction) {
        setTimeout(() => browserNotification.close(), 5000);
      }
    }
  }

  /**
   * Handle notification action
   */
  handleNotificationAction(action) {
    this.notifySubscribers('notification_action', action);
  }

  /**
   * Mark notification as read
   */
  markAsRead(notificationId) {
    const notification = this.notifications.find(n => n.id === notificationId);
    if (notification) {
      notification.read = true;
      this.saveNotificationHistory();
      this.notifySubscribers('notification_read', { id: notificationId });
    }
  }

  /**
   * Mark all notifications as read
   */
  markAllAsRead() {
    this.notifications.forEach(n => n.read = true);
    this.saveNotificationHistory();
    this.notifySubscribers('all_notifications_read', {});
  }

  /**
   * Remove notification
   */
  removeNotification(notificationId) {
    this.notifications = this.notifications.filter(n => n.id !== notificationId);
    this.saveNotificationHistory();
    this.notifySubscribers('notification_removed', { id: notificationId });
  }

  /**
   * Clear all notifications
   */
  clearAll() {
    this.notifications = [];
    this.saveNotificationHistory();
    this.notifySubscribers('notifications_cleared', {});
  }

  /**
   * Get all notifications
   */
  getNotifications() {
    return this.notifications;
  }

  /**
   * Get unread notifications count
   */
  getUnreadCount() {
    return this.notifications.filter(n => !n.read).length;
  }

  /**
   * Get notifications by type
   */
  getNotificationsByType(type) {
    return this.notifications.filter(n => n.type === type);
  }

  /**
   * Subscribe to notification events
   */
  subscribe(callback) {
    const id = uuidv4();
    this.subscribers.set(id, callback);
    return id;
  }

  /**
   * Unsubscribe from notification events
   */
  unsubscribe(id) {
    this.subscribers.delete(id);
  }

  /**
   * Notify all subscribers
   */
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in notification subscriber:', error);
      }
    });
  }

  /**
   * Schedule WebSocket reconnection
   */
  scheduleReconnect() {
    this.reconnectAttempts++;
    
    setTimeout(() => {
      console.log(`Attempting to reconnect WebSocket (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.initializeWebSocket();
    }, this.reconnectDelay);
    
    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  /**
   * Start heartbeat monitoring
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.lastHeartbeat) {
        const timeSinceLastHeartbeat = Date.now() - this.lastHeartbeat;
        
        // If no heartbeat for more than 30 seconds, consider connection stale
        if (timeSinceLastHeartbeat > 30000) {
          console.warn('WebSocket heartbeat timeout, attempting reconnection');
          this.websocket.close();
        }
      }
    }, 10000); // Check every 10 seconds
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }

  /**
   * Get notification permission status
   */
  getPermissionStatus() {
    if ('Notification' in window) {
      return Notification.permission;
    }
    return 'unsupported';
  }

  /**
   * Save notification history to localStorage
   */
  saveNotificationHistory() {
    try {
      // Only save last 50 notifications to localStorage
      const toSave = this.notifications.slice(0, 50).map(n => ({
        ...n,
        timestamp: n.timestamp.toISOString() // Convert Date to string
      }));
      
      localStorage.setItem('notification_history', JSON.stringify(toSave));
    } catch (error) {
      console.error('Failed to save notification history:', error);
    }
  }

  /**
   * Load notification history from localStorage
   */
  loadNotificationHistory() {
    try {
      const saved = localStorage.getItem('notification_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.map(n => ({
          ...n,
          timestamp: new Date(n.timestamp) // Convert string back to Date
        }));
      }
    } catch (error) {
      console.error('Failed to load notification history:', error);
    }
    return [];
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      lastHeartbeat: this.lastHeartbeat
    };
  }

  /**
   * Cleanup resources
   */
  destroy() {
    if (this.websocket) {
      this.websocket.close(1000, 'Service destroyed');
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    this.subscribers.clear();
  }
}

// Create singleton instance
const notificationService = new NotificationService();

export default notificationService;