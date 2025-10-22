/**
 * T012: Real-Time Performance Monitoring Service
 * Service for managing real-time performance data connections with WebSocket fallback to polling
 */

class RealTimePerformanceService {
  constructor() {
    this.ws = null;
    this.pollingInterval = null;
    this.listeners = new Map();
    this.isConnected = false;
    this.useWebSocket = true;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.pollingIntervalMs = 5000; // 5 seconds
    this.wsReconnectDelay = 1000; // Start with 1 second
  }

  /**
   * Subscribe to real-time performance updates
   * @param {string} eventType - Type of performance data (metrics, alerts, etc.)
   * @param {Function} callback - Callback function to handle updates
   * @returns {string} - Subscription ID for unsubscribing
   */
  subscribe(eventType, callback) {
    const subscriptionId = `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Map());
    }
    
    this.listeners.get(eventType).set(subscriptionId, callback);
    
    // Start connection if this is the first subscription
    if (this.getTotalSubscriptions() === 1) {
      this.startConnection();
    }
    
    return subscriptionId;
  }

  /**
   * Unsubscribe from performance updates
   * @param {string} eventType - Type of performance data
   * @param {string} subscriptionId - Subscription ID to remove
   */
  unsubscribe(eventType, subscriptionId) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).delete(subscriptionId);
      
      // Remove empty event type maps
      if (this.listeners.get(eventType).size === 0) {
        this.listeners.delete(eventType);
      }
    }
    
    // Stop connection if no more subscriptions
    if (this.getTotalSubscriptions() === 0) {
      this.stopConnection();
    }
  }

  /**
   * Get total number of active subscriptions
   * @returns {number} - Total subscription count
   */
  getTotalSubscriptions() {
    let total = 0;
    for (const eventMap of this.listeners.values()) {
      total += eventMap.size;
    }
    return total;
  }

  /**
   * Start the real-time connection (WebSocket first, fallback to polling)
   */
  async startConnection() {
    if (this.isConnected) {
      return;
    }

    console.log('[Performance Monitor] Starting real-time connection...');

    // Try WebSocket first
    if (this.useWebSocket) {
      try {
        await this.initWebSocket();
      } catch (error) {
        console.warn('[Performance Monitor] WebSocket failed, falling back to polling:', error);
        this.useWebSocket = false;
        this.startPolling();
      }
    } else {
      this.startPolling();
    }
  }

  /**
   * Stop the real-time connection
   */
  stopConnection() {
    console.log('[Performance Monitor] Stopping real-time connection...');
    
    this.isConnected = false;
    
    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    // Clear polling
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  /**
   * Initialize WebSocket connection
   */
  async initWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/performance`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
          console.log('[Performance Monitor] WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.wsReconnectDelay = 1000;
          
          // Send authentication token
          const token = localStorage.getItem('token');
          if (token) {
            this.ws.send(JSON.stringify({
              type: 'auth',
              token: token
            }));
          }
          
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
          } catch (error) {
            console.error('[Performance Monitor] Error parsing WebSocket message:', error);
          }
        };
        
        this.ws.onclose = (event) => {
          console.log('[Performance Monitor] WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          
          // Attempt to reconnect if not manually closed
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptWebSocketReconnect();
          } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('[Performance Monitor] Max WebSocket reconnect attempts reached, falling back to polling');
            this.useWebSocket = false;
            this.startPolling();
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('[Performance Monitor] WebSocket error:', error);
          reject(error);
        };
        
        // Timeout for connection
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);
        
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Handle WebSocket message
   * @param {Object} data - Parsed message data
   */
  handleWebSocketMessage(data) {
    const { type, payload } = data;
    
    if (this.listeners.has(type)) {
      for (const callback of this.listeners.get(type).values()) {
        try {
          callback(payload);
        } catch (error) {
          console.error(`[Performance Monitor] Error in ${type} callback:`, error);
        }
      }
    }
  }

  /**
   * Attempt WebSocket reconnection with exponential backoff
   */
  attemptWebSocketReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.wsReconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`[Performance Monitor] Attempting WebSocket reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(async () => {
      try {
        await this.initWebSocket();
      } catch (error) {
        console.error('[Performance Monitor] WebSocket reconnect failed:', error);
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptWebSocketReconnect();
        }
      }
    }, delay);
  }

  /**
   * Start polling-based updates as fallback
   */
  startPolling() {
    if (this.pollingInterval) {
      return;
    }

    console.log('[Performance Monitor] Starting polling mode...');
    this.isConnected = true;

    // Initial fetch
    this.pollMetrics();

    // Set up interval
    this.pollingInterval = setInterval(() => {
      this.pollMetrics();
    }, this.pollingIntervalMs);
  }

  /**
   * Poll metrics from REST API
   */
  async pollMetrics() {
    try {
      // Fetch metrics if we have listeners
      if (this.listeners.has('metrics')) {
        const metricsData = await this.fetchMetrics();
        this.emit('metrics', metricsData);
      }

      // Fetch alerts if we have listeners
      if (this.listeners.has('alerts')) {
        const alertsData = await this.fetchAlerts();
        this.emit('alerts', alertsData);
      }

      // Fetch service status if we have listeners
      if (this.listeners.has('services')) {
        const servicesData = await this.fetchServices();
        this.emit('services', servicesData);
      }

    } catch (error) {
      console.error('[Performance Monitor] Polling error:', error);
      this.emit('error', { message: error.message, type: 'polling_error' });
    }
  }

  /**
   * Fetch metrics from API
   */
  async fetchMetrics() {
    const response = await fetch('/api/admin/system/metrics', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to fetch metrics');
    }

    return result.data;
  }

  /**
   * Fetch alerts from API
   */
  async fetchAlerts() {
    const response = await fetch('/api/admin/system/alerts', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to fetch alerts');
    }

    return result.data;
  }

  /**
   * Fetch service status from API
   */
  async fetchServices() {
    const response = await fetch('/api/admin/system/services', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to fetch services');
    }

    return result.data;
  }

  /**
   * Emit event to all listeners
   * @param {string} eventType - Event type
   * @param {any} data - Event data
   */
  emit(eventType, data) {
    if (this.listeners.has(eventType)) {
      for (const callback of this.listeners.get(eventType).values()) {
        try {
          callback(data);
        } catch (error) {
          console.error(`[Performance Monitor] Error in ${eventType} callback:`, error);
        }
      }
    }
  }

  /**
   * Request historical data
   * @param {string} timeRange - Time range (1h, 6h, 24h, 7d)
   * @returns {Promise<Object>} - Historical data
   */
  async getHistoricalData(timeRange = '1h') {
    const response = await fetch(`/api/admin/system/metrics/historical?timeRange=${timeRange}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || 'Failed to fetch historical data');
    }

    return result.data;
  }

  /**
   * Get connection status
   * @returns {Object} - Connection status information
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      connectionType: this.useWebSocket ? 'websocket' : 'polling',
      reconnectAttempts: this.reconnectAttempts,
      totalSubscriptions: this.getTotalSubscriptions()
    };
  }

  /**
   * Force reconnection
   */
  async reconnect() {
    this.stopConnection();
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
    await this.startConnection();
  }

  /**
   * Update polling interval
   * @param {number} intervalMs - New interval in milliseconds
   */
  setPollingInterval(intervalMs) {
    this.pollingIntervalMs = intervalMs;
    
    if (!this.useWebSocket && this.pollingInterval) {
      // Restart polling with new interval
      clearInterval(this.pollingInterval);
      this.pollingInterval = setInterval(() => {
        this.pollMetrics();
      }, this.pollingIntervalMs);
    }
  }
}

// Create singleton instance
const realTimePerformanceService = new RealTimePerformanceService();

export default realTimePerformanceService;