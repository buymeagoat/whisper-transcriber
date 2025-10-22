/**
 * T030 User Preferences Enhancement: Notification Preferences Service
 * Comprehensive notification management with granular controls and delivery options
 */

class NotificationPreferencesService {
  constructor() {
    this.preferences = {
      global: {
        enabled: true,
        sound: true,
        vibration: true,
        desktop: true,
        mobile: true,
        email: false,
        quiet_hours: {
          enabled: false,
          start: '22:00',
          end: '08:00',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      },
      categories: {
        transcription: {
          enabled: true,
          priority: 'normal',
          delivery: {
            push: true,
            desktop: true,
            sound: true,
            vibration: true,
            email: false
          },
          events: {
            job_started: { enabled: true, immediate: false },
            job_progress: { enabled: true, immediate: false, interval: 25 }, // Every 25%
            job_completed: { enabled: true, immediate: true },
            job_failed: { enabled: true, immediate: true },
            job_cancelled: { enabled: true, immediate: false }
          }
        },
        batch: {
          enabled: true,
          priority: 'normal',
          delivery: {
            push: true,
            desktop: true,
            sound: true,
            vibration: false,
            email: false
          },
          events: {
            batch_started: { enabled: true, immediate: false },
            batch_progress: { enabled: true, immediate: false, interval: 50 }, // Every 50%
            batch_completed: { enabled: true, immediate: true },
            batch_failed: { enabled: true, immediate: true },
            batch_cancelled: { enabled: false, immediate: false }
          }
        },
        system: {
          enabled: true,
          priority: 'high',
          delivery: {
            push: true,
            desktop: true,
            sound: false,
            vibration: false,
            email: false
          },
          events: {
            system_maintenance: { enabled: true, immediate: true },
            system_error: { enabled: true, immediate: true },
            system_update: { enabled: true, immediate: false },
            quota_warning: { enabled: true, immediate: true },
            quota_exceeded: { enabled: true, immediate: true },
            security_alert: { enabled: true, immediate: true }
          }
        },
        account: {
          enabled: true,
          priority: 'high',
          delivery: {
            push: true,
            desktop: true,
            sound: true,
            vibration: true,
            email: true
          },
          events: {
            login_new_device: { enabled: true, immediate: true },
            password_changed: { enabled: true, immediate: true },
            api_key_created: { enabled: true, immediate: false },
            api_key_expired: { enabled: true, immediate: true },
            subscription_changed: { enabled: true, immediate: false }
          }
        },
        social: {
          enabled: false,
          priority: 'low',
          delivery: {
            push: false,
            desktop: false,
            sound: false,
            vibration: false,
            email: false
          },
          events: {
            share_received: { enabled: false, immediate: false },
            comment_received: { enabled: false, immediate: false },
            mention_received: { enabled: false, immediate: false }
          }
        }
      },
      advanced: {
        grouping: {
          enabled: true,
          timeout: 30000, // 30 seconds
          max_group_size: 5
        },
        rate_limiting: {
          enabled: true,
          max_per_minute: 10,
          max_per_hour: 100
        },
        persistence: {
          enabled: true,
          max_history: 1000,
          auto_cleanup_days: 30
        },
        delivery_retry: {
          enabled: true,
          max_attempts: 3,
          retry_delay: 5000, // 5 seconds
          exponential_backoff: true
        }
      }
    };

    this.subscribers = new Set();
    this.notificationHistory = [];
    this.loadPreferences();
    this.setupEventListeners();
  }

  /**
   * Load notification preferences from storage
   */
  loadPreferences() {
    try {
      const stored = localStorage.getItem('whisper-notification-preferences');
      if (stored) {
        const storedPrefs = JSON.parse(stored);
        this.preferences = this.mergePreferences(this.preferences, storedPrefs);
      }
    } catch (error) {
      console.error('Error loading notification preferences:', error);
    }
  }

  /**
   * Save notification preferences to storage
   */
  savePreferences() {
    try {
      localStorage.setItem('whisper-notification-preferences', JSON.stringify(this.preferences));
      this.notifySubscribers('preferences-updated', this.preferences);
    } catch (error) {
      console.error('Error saving notification preferences:', error);
    }
  }

  /**
   * Merge preferences with validation
   */
  mergePreferences(defaultPrefs, userPrefs) {
    const merged = JSON.parse(JSON.stringify(defaultPrefs));
    
    // Merge global settings
    if (userPrefs.global) {
      Object.assign(merged.global, userPrefs.global);
    }
    
    // Merge category settings
    if (userPrefs.categories) {
      Object.keys(userPrefs.categories).forEach(category => {
        if (merged.categories[category]) {
          Object.assign(merged.categories[category], userPrefs.categories[category]);
        }
      });
    }
    
    // Merge advanced settings
    if (userPrefs.advanced) {
      Object.assign(merged.advanced, userPrefs.advanced);
    }
    
    return merged;
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for permission changes
    if ('Notification' in window) {
      // Check permission status periodically
      setInterval(() => {
        const permission = Notification.permission;
        if (permission !== this.lastPermissionStatus) {
          this.lastPermissionStatus = permission;
          this.notifySubscribers('permission-changed', permission);
        }
      }, 5000);
    }

    // Listen for storage changes (multi-tab sync)
    window.addEventListener('storage', (e) => {
      if (e.key === 'whisper-notification-preferences' && e.newValue) {
        try {
          const preferences = JSON.parse(e.newValue);
          this.preferences = preferences;
          this.notifySubscribers('preferences-updated', preferences);
        } catch (error) {
          console.error('Error parsing notification preferences from storage:', error);
        }
      }
    });

    // Listen for visibility changes (for quiet hours)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkQuietHours();
      }
    });
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if (!('Notification' in window)) {
      throw new Error('This browser does not support notifications');
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      throw new Error('Notification permission denied');
    }

    const permission = await Notification.requestPermission();
    this.notifySubscribers('permission-changed', permission);
    return permission;
  }

  /**
   * Check if notifications are enabled for a category and event
   */
  isNotificationEnabled(category, event = null) {
    // Check global settings
    if (!this.preferences.global.enabled) {
      return false;
    }

    // Check category settings
    const categoryPrefs = this.preferences.categories[category];
    if (!categoryPrefs || !categoryPrefs.enabled) {
      return false;
    }

    // Check event settings
    if (event && categoryPrefs.events[event]) {
      return categoryPrefs.events[event].enabled;
    }

    return true;
  }

  /**
   * Check if currently in quiet hours
   */
  isQuietHours() {
    if (!this.preferences.global.quiet_hours.enabled) {
      return false;
    }

    const now = new Date();
    const timezone = this.preferences.global.quiet_hours.timezone;
    const timeString = now.toLocaleTimeString('en-US', { 
      hour12: false, 
      timeZone: timezone,
      hour: '2-digit',
      minute: '2-digit'
    });

    const currentTime = timeString;
    const startTime = this.preferences.global.quiet_hours.start;
    const endTime = this.preferences.global.quiet_hours.end;

    // Handle overnight quiet hours (e.g., 22:00 to 08:00)
    if (startTime > endTime) {
      return currentTime >= startTime || currentTime <= endTime;
    } else {
      return currentTime >= startTime && currentTime <= endTime;
    }
  }

  /**
   * Check quiet hours and notify subscribers
   */
  checkQuietHours() {
    const inQuietHours = this.isQuietHours();
    this.notifySubscribers('quiet-hours-changed', inQuietHours);
  }

  /**
   * Get delivery methods for a notification
   */
  getDeliveryMethods(category, priority = 'normal') {
    const categoryPrefs = this.preferences.categories[category];
    if (!categoryPrefs) {
      return { push: false, desktop: false, sound: false, vibration: false, email: false };
    }

    const delivery = { ...categoryPrefs.delivery };

    // Adjust for quiet hours
    if (this.isQuietHours()) {
      delivery.sound = false;
      delivery.vibration = false;
      
      // Only allow high priority notifications during quiet hours
      if (priority !== 'high') {
        delivery.push = false;
        delivery.desktop = false;
      }
    }

    // Check global overrides
    if (!this.preferences.global.sound) delivery.sound = false;
    if (!this.preferences.global.vibration) delivery.vibration = false;
    if (!this.preferences.global.desktop) delivery.desktop = false;
    if (!this.preferences.global.mobile) delivery.push = false;

    return delivery;
  }

  /**
   * Should show notification immediately
   */
  shouldShowImmediate(category, event) {
    const categoryPrefs = this.preferences.categories[category];
    if (!categoryPrefs || !categoryPrefs.events[event]) {
      return true;
    }

    return categoryPrefs.events[event].immediate;
  }

  /**
   * Get progress notification interval
   */
  getProgressInterval(category, event) {
    const categoryPrefs = this.preferences.categories[category];
    if (!categoryPrefs || !categoryPrefs.events[event]) {
      return 25; // Default 25%
    }

    return categoryPrefs.events[event].interval || 25;
  }

  /**
   * Update global preferences
   */
  updateGlobalPreferences(updates) {
    this.preferences.global = {
      ...this.preferences.global,
      ...updates
    };
    this.savePreferences();
  }

  /**
   * Update category preferences
   */
  updateCategoryPreferences(category, updates) {
    if (!this.preferences.categories[category]) {
      console.error(`Category '${category}' not found`);
      return;
    }

    this.preferences.categories[category] = {
      ...this.preferences.categories[category],
      ...updates
    };
    this.savePreferences();
  }

  /**
   * Update event preferences
   */
  updateEventPreferences(category, event, updates) {
    if (!this.preferences.categories[category] || !this.preferences.categories[category].events[event]) {
      console.error(`Event '${event}' in category '${category}' not found`);
      return;
    }

    this.preferences.categories[category].events[event] = {
      ...this.preferences.categories[category].events[event],
      ...updates
    };
    this.savePreferences();
  }

  /**
   * Update advanced preferences
   */
  updateAdvancedPreferences(updates) {
    this.preferences.advanced = {
      ...this.preferences.advanced,
      ...updates
    };
    this.savePreferences();
  }

  /**
   * Reset preferences to defaults
   */
  resetPreferences() {
    // Store current preferences as backup
    const backup = JSON.stringify(this.preferences);
    localStorage.setItem('whisper-notification-preferences-backup', backup);

    // Reset to defaults
    this.preferences = {
      global: {
        enabled: true,
        sound: true,
        vibration: true,
        desktop: true,
        mobile: true,
        email: false,
        quiet_hours: {
          enabled: false,
          start: '22:00',
          end: '08:00',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      },
      categories: {
        transcription: {
          enabled: true,
          priority: 'normal',
          delivery: {
            push: true,
            desktop: true,
            sound: true,
            vibration: true,
            email: false
          },
          events: {
            job_started: { enabled: true, immediate: false },
            job_progress: { enabled: true, immediate: false, interval: 25 },
            job_completed: { enabled: true, immediate: true },
            job_failed: { enabled: true, immediate: true },
            job_cancelled: { enabled: true, immediate: false }
          }
        },
        // ... other categories would be reset too
      },
      advanced: {
        grouping: {
          enabled: true,
          timeout: 30000,
          max_group_size: 5
        },
        rate_limiting: {
          enabled: true,
          max_per_minute: 10,
          max_per_hour: 100
        },
        persistence: {
          enabled: true,
          max_history: 1000,
          auto_cleanup_days: 30
        },
        delivery_retry: {
          enabled: true,
          max_attempts: 3,
          retry_delay: 5000,
          exponential_backoff: true
        }
      }
    };

    this.savePreferences();
  }

  /**
   * Export preferences
   */
  exportPreferences() {
    const exportData = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      preferences: this.preferences
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `whisper-notification-preferences-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Import preferences
   */
  async importPreferences(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const importData = JSON.parse(e.target.result);
          
          if (!importData.preferences) {
            throw new Error('Invalid preferences file format');
          }
          
          // Validate and merge preferences
          const merged = this.mergePreferences(this.preferences, importData.preferences);
          this.preferences = merged;
          this.savePreferences();
          
          resolve(importData);
        } catch (error) {
          reject(new Error(`Failed to import preferences: ${error.message}`));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read preferences file'));
      };
      
      reader.readAsText(file);
    });
  }

  /**
   * Get notification statistics
   */
  getNotificationStats() {
    const stats = {
      total_sent: 0,
      by_category: {},
      by_delivery_method: {
        push: 0,
        desktop: 0,
        sound: 0,
        vibration: 0,
        email: 0
      },
      recent_activity: []
    };

    // Calculate from stored history
    this.notificationHistory.forEach(notification => {
      stats.total_sent++;
      
      if (!stats.by_category[notification.category]) {
        stats.by_category[notification.category] = 0;
      }
      stats.by_category[notification.category]++;
      
      Object.keys(notification.delivery_methods).forEach(method => {
        if (notification.delivery_methods[method]) {
          stats.by_delivery_method[method]++;
        }
      });
    });

    // Recent activity (last 24 hours)
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    stats.recent_activity = this.notificationHistory.filter(
      notification => new Date(notification.timestamp) > yesterday
    );

    return stats;
  }

  /**
   * Subscribe to preference changes
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notify subscribers
   */
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in notification preference subscriber:', error);
      }
    });
  }

  /**
   * Get current preferences
   */
  getPreferences() {
    return JSON.parse(JSON.stringify(this.preferences));
  }

  /**
   * Get available categories
   */
  getCategories() {
    return Object.keys(this.preferences.categories);
  }

  /**
   * Get available events for a category
   */
  getEvents(category) {
    if (!this.preferences.categories[category]) {
      return [];
    }
    
    return Object.keys(this.preferences.categories[category].events);
  }

  /**
   * Test notification delivery
   */
  async testNotification(category = 'system', deliveryMethods = null) {
    const methods = deliveryMethods || this.getDeliveryMethods(category, 'normal');
    
    const testNotification = {
      id: `test-${Date.now()}`,
      category,
      event: 'test',
      title: 'Test Notification',
      message: 'This is a test notification to verify your preferences.',
      timestamp: new Date().toISOString(),
      delivery_methods: methods,
      priority: 'normal'
    };

    // Add to history
    this.notificationHistory.push(testNotification);
    
    // Trigger test delivery
    this.notifySubscribers('test-notification', testNotification);
    
    return testNotification;
  }
}

// Create singleton instance
const notificationPreferencesService = new NotificationPreferencesService();

export default notificationPreferencesService;