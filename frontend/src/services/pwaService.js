/**
 * T028 Frontend Implementation: PWA Enhancement Service
 * Client-side service for Progressive Web App features, offline capabilities, and push notifications
 */

import apiClient from './apiClient';

class PWAService {
  constructor() {
    this.serviceWorker = null;
    this.notificationPermission = 'default';
    this.isOnline = navigator.onLine;
    this.offlineQueue = [];
    this.syncCallbacks = new Map();
    this.notificationCallbacks = new Map();
    
    this.initializeEventListeners();
  }

  /**
   * Initialize PWA service with event listeners
   */
  initializeEventListeners() {
    // Online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processOfflineQueue();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });

    // Service worker messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.handleServiceWorkerMessage(event);
      });
    }
  }

  /**
   * Register service worker for PWA functionality
   */
  async registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      return {
        success: false,
        error: 'Service Worker not supported in this browser'
      };
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      this.serviceWorker = registration;
      
      // Listen for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New version available
            this.notifyUpdateAvailable();
          }
        });
      });

      return {
        success: true,
        data: registration
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to register service worker: ' + error.message
      };
    }
  }

  /**
   * Request notification permissions
   */
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      return {
        success: false,
        error: 'Notifications not supported in this browser'
      };
    }

    try {
      const permission = await Notification.requestPermission();
      this.notificationPermission = permission;
      
      return {
        success: permission === 'granted',
        data: permission
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to request notification permission: ' + error.message
      };
    }
  }

  /**
   * Subscribe to push notifications
   */
  async subscribeToPushNotifications() {
    if (!this.serviceWorker) {
      await this.registerServiceWorker();
    }

    if (this.notificationPermission !== 'granted') {
      const permissionResult = await this.requestNotificationPermission();
      if (!permissionResult.success) {
        return permissionResult;
      }
    }

    try {
      const subscription = await this.serviceWorker.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY)
      });

      // Send subscription to backend
      const result = await apiClient.post('/api/v1/pwa/subscribe', {
        subscription: subscription.toJSON()
      });

      return {
        success: true,
        data: subscription
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to subscribe to push notifications: ' + error.message
      };
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribeFromPushNotifications() {
    try {
      if (this.serviceWorker) {
        const subscription = await this.serviceWorker.pushManager.getSubscription();
        if (subscription) {
          await subscription.unsubscribe();
          
          // Notify backend
          await apiClient.post('/api/v1/pwa/unsubscribe', {
            endpoint: subscription.endpoint
          });
        }
      }

      return {
        success: true,
        data: 'Unsubscribed from push notifications'
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to unsubscribe from push notifications: ' + error.message
      };
    }
  }

  /**
   * Get current push subscription status
   */
  async getPushSubscriptionStatus() {
    try {
      if (!this.serviceWorker) {
        return {
          success: true,
          data: { subscribed: false, permission: this.notificationPermission }
        };
      }

      const subscription = await this.serviceWorker.pushManager.getSubscription();
      
      return {
        success: true,
        data: {
          subscribed: !!subscription,
          permission: this.notificationPermission,
          endpoint: subscription?.endpoint
        }
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to check push subscription status: ' + error.message
      };
    }
  }

  /**
   * Send local notification (for immediate feedback)
   */
  async sendLocalNotification(title, options = {}) {
    if (this.notificationPermission !== 'granted') {
      return {
        success: false,
        error: 'Notification permission not granted'
      };
    }

    try {
      const notification = new Notification(title, {
        icon: '/icon-192x192.png',
        badge: '/icon-72x72.png',
        ...options
      });

      // Auto-close after 5 seconds if not specified
      if (!options.requireInteraction) {
        setTimeout(() => notification.close(), 5000);
      }

      return {
        success: true,
        data: notification
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to send notification: ' + error.message
      };
    }
  }

  /**
   * Cache transcription job for offline processing
   */
  async cacheJobForOffline(jobData) {
    try {
      // Store in IndexedDB for offline access
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['offline_jobs'], 'readwrite');
      const store = transaction.objectStore('offline_jobs');
      
      const job = {
        id: jobData.id || Date.now(),
        ...jobData,
        cached_at: new Date().toISOString(),
        status: 'cached'
      };

      await store.add(job);

      return {
        success: true,
        data: job
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to cache job: ' + error.message
      };
    }
  }

  /**
   * Get cached offline jobs
   */
  async getCachedJobs() {
    try {
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['offline_jobs'], 'readonly');
      const store = transaction.objectStore('offline_jobs');
      const jobs = await store.getAll();

      return {
        success: true,
        data: jobs
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to get cached jobs: ' + error.message
      };
    }
  }

  /**
   * Submit offline job when online
   */
  async submitOfflineJob(jobId) {
    try {
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['offline_jobs'], 'readwrite');
      const store = transaction.objectStore('offline_jobs');
      const job = await store.get(jobId);

      if (!job) {
        return {
          success: false,
          error: 'Job not found in offline cache'
        };
      }

      // Submit to backend
      const result = await apiClient.post('/api/v1/jobs', job);
      
      if (result.data.success) {
        // Remove from offline cache
        await store.delete(jobId);
        
        // Send notification
        await this.sendLocalNotification('Job Submitted', {
          body: `Offline job "${job.filename || 'Untitled'}" has been submitted for processing`,
          tag: 'job-submitted'
        });
      }

      return {
        success: true,
        data: result.data
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to submit offline job: ' + error.message
      };
    }
  }

  /**
   * Process offline queue when connection is restored
   */
  async processOfflineQueue() {
    if (!this.isOnline) return;

    try {
      const cachedJobs = await this.getCachedJobs();
      if (cachedJobs.success && cachedJobs.data.length > 0) {
        for (const job of cachedJobs.data) {
          await this.submitOfflineJob(job.id);
        }

        await this.sendLocalNotification('Offline Jobs Processed', {
          body: `${cachedJobs.data.length} offline jobs have been submitted`,
          tag: 'offline-sync'
        });
      }
    } catch (error) {
      console.error('Failed to process offline queue:', error);
    }
  }

  /**
   * Check for app updates
   */
  async checkForUpdates() {
    if (!this.serviceWorker) {
      return {
        success: false,
        error: 'Service worker not registered'
      };
    }

    try {
      await this.serviceWorker.update();
      return {
        success: true,
        data: 'Update check completed'
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to check for updates: ' + error.message
      };
    }
  }

  /**
   * Install app update
   */
  async installUpdate() {
    if (!this.serviceWorker?.waiting) {
      return {
        success: false,
        error: 'No update available to install'
      };
    }

    try {
      this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
      
      return {
        success: true,
        data: 'Update installed, reloading app'
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to install update: ' + error.message
      };
    }
  }

  /**
   * Get PWA installation status
   */
  async getInstallationStatus() {
    return {
      success: true,
      data: {
        isInstallable: !!window.deferredPrompt,
        isInstalled: window.matchMedia('(display-mode: standalone)').matches,
        isServiceWorkerSupported: 'serviceWorker' in navigator,
        isNotificationSupported: 'Notification' in window,
        isPushSupported: 'PushManager' in window
      }
    };
  }

  /**
   * Prompt user to install PWA
   */
  async promptInstall() {
    if (!window.deferredPrompt) {
      return {
        success: false,
        error: 'App is not installable at this time'
      };
    }

    try {
      window.deferredPrompt.prompt();
      const { outcome } = await window.deferredPrompt.userChoice;
      window.deferredPrompt = null;

      return {
        success: outcome === 'accepted',
        data: outcome
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to prompt install: ' + error.message
      };
    }
  }

  /**
   * Get app capabilities and features
   */
  getAppCapabilities() {
    return {
      offline: this.isOnline === false && 'serviceWorker' in navigator,
      notifications: this.notificationPermission === 'granted',
      background_sync: 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype,
      push_messaging: 'serviceWorker' in navigator && 'PushManager' in window,
      file_system_access: 'showOpenFilePicker' in window,
      web_share: 'share' in navigator,
      fullscreen: 'requestFullscreen' in document.documentElement,
      vibration: 'vibrate' in navigator
    };
  }

  /**
   * Configure PWA settings
   */
  async configurePWASettings(settings) {
    try {
      // Store settings in localStorage
      localStorage.setItem('pwa_settings', JSON.stringify(settings));

      // Apply notification settings
      if (settings.notifications !== undefined) {
        if (settings.notifications && this.notificationPermission !== 'granted') {
          await this.requestNotificationPermission();
        } else if (!settings.notifications) {
          await this.unsubscribeFromPushNotifications();
        }
      }

      // Apply offline settings
      if (settings.offline_mode !== undefined) {
        localStorage.setItem('offline_mode_enabled', settings.offline_mode);
      }

      return {
        success: true,
        data: settings
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to configure PWA settings: ' + error.message
      };
    }
  }

  /**
   * Get current PWA settings
   */
  getPWASettings() {
    try {
      const settings = localStorage.getItem('pwa_settings');
      const defaultSettings = {
        notifications: false,
        offline_mode: true,
        auto_sync: true,
        background_updates: true,
        data_saver: false
      };

      return {
        success: true,
        data: settings ? { ...defaultSettings, ...JSON.parse(settings) } : defaultSettings
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to get PWA settings: ' + error.message
      };
    }
  }

  /**
   * Handle service worker messages
   */
  handleServiceWorkerMessage(event) {
    const { type, payload } = event.data;

    switch (type) {
      case 'JOB_COMPLETED':
        this.sendLocalNotification('Job Completed', {
          body: `Transcription job "${payload.filename}" has been completed`,
          tag: 'job-completed',
          data: payload
        });
        break;
      
      case 'BATCH_COMPLETED':
        this.sendLocalNotification('Batch Completed', {
          body: `Batch "${payload.batch_name}" with ${payload.total_files} files has been completed`,
          tag: 'batch-completed',
          data: payload
        });
        break;
      
      case 'SYNC_COMPLETE':
        this.sendLocalNotification('Sync Complete', {
          body: 'Background sync has completed successfully',
          tag: 'sync-complete'
        });
        break;

      default:
        console.log('Unknown service worker message:', type, payload);
    }
  }

  /**
   * Notify about app update availability
   */
  notifyUpdateAvailable() {
    this.sendLocalNotification('App Update Available', {
      body: 'A new version of the app is available. Tap to update.',
      tag: 'update-available',
      requireInteraction: true,
      actions: [
        { action: 'update', title: 'Update Now' },
        { action: 'dismiss', title: 'Later' }
      ]
    });
  }

  /**
   * Open IndexedDB for offline storage
   */
  openIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('whisper_pwa', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('offline_jobs')) {
          db.createObjectStore('offline_jobs', { keyPath: 'id' });
        }
      };
    });
  }

  /**
   * Convert VAPID key for push subscription
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/\-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  /**
   * Get storage usage information
   */
  async getStorageInfo() {
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        return {
          success: true,
          data: {
            used: estimate.usage,
            available: estimate.quota,
            usedPercent: Math.round((estimate.usage / estimate.quota) * 100)
          }
        };
      } else {
        return {
          success: false,
          error: 'Storage API not supported'
        };
      }
    } catch (error) {
      return {
        success: false,
        error: 'Failed to get storage info: ' + error.message
      };
    }
  }

  /**
   * Clear app cache and data
   */
  async clearAppData() {
    try {
      // Clear service worker cache
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
      }

      // Clear IndexedDB
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['offline_jobs'], 'readwrite');
      const store = transaction.objectStore('offline_jobs');
      await store.clear();

      // Clear localStorage PWA data
      localStorage.removeItem('pwa_settings');
      localStorage.removeItem('offline_mode_enabled');

      return {
        success: true,
        data: 'App data cleared successfully'
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to clear app data: ' + error.message
      };
    }
  }
}

export default new PWAService();