/**
 * T030 User Preferences Enhancement: Settings Persistence Service
 * Comprehensive preferences persistence with cloud sync and local storage fallback
 */

class SettingsPersistenceService {
  constructor() {
    this.subscribers = new Set();
    this.storageKey = 'whisper_settings_persistence';
    this.cloudEndpoint = '/api/user/preferences';
    this.syncIntervals = new Map();
    this.conflictResolution = 'merge'; // merge, local, remote, manual
    this.encryptionKey = null;
    this.offlineQueue = [];
    this.syncStatus = 'offline'; // offline, syncing, synced, error
    this.lastSync = null;
    
    this.defaultSettings = {
      // Storage Options
      storage: {
        enable_cloud_sync: false,
        cloud_provider: 'whisper_cloud', // whisper_cloud, google_drive, dropbox, custom
        auto_sync_interval: 300000, // 5 minutes in milliseconds
        sync_on_change: true,
        enable_backup: true,
        backup_frequency: 'daily', // hourly, daily, weekly
        max_backups: 10,
        compression_enabled: true,
        encryption_enabled: false
      },
      
      // Sync Behavior
      sync: {
        conflict_resolution: 'merge', // merge, local, remote, manual
        sync_timeout: 30000, // 30 seconds
        retry_attempts: 3,
        retry_delay: 5000, // 5 seconds
        batch_size: 50, // preferences per batch
        incremental_sync: true,
        sync_metadata: true,
        offline_support: true,
        background_sync: true
      },
      
      // Data Management
      data: {
        include_theme_preferences: true,
        include_notification_preferences: true,
        include_upload_preferences: true,
        include_accessibility_preferences: true,
        include_usage_statistics: false,
        include_cached_data: false,
        data_retention_days: 365,
        auto_cleanup_enabled: true,
        version_history_length: 5
      },
      
      // Security & Privacy
      security: {
        require_authentication: true,
        enable_end_to_end_encryption: false,
        encryption_algorithm: 'AES-256-GCM',
        key_derivation: 'PBKDF2',
        secure_transmission: true,
        data_anonymization: false,
        share_usage_analytics: false,
        gdpr_compliance: true
      },
      
      // Import/Export
      import_export: {
        auto_export_enabled: false,
        export_frequency: 'weekly',
        export_format: 'json', // json, encrypted, csv
        include_metadata: true,
        validate_imports: true,
        backup_before_import: true,
        import_conflict_resolution: 'prompt',
        export_location: 'downloads'
      }
    };
    
    this.settings = this.loadSettings();
    this.initializePersistence();
    this.setupEventListeners();
    this.loadSyncMetadata();
  }
  
  loadSettings() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        return this.mergeWithDefaults(parsed);
      }
    } catch (error) {
      console.warn('Failed to load persistence settings:', error);
    }
    return { ...this.defaultSettings };
  }
  
  mergeWithDefaults(stored) {
    const merged = { ...this.defaultSettings };
    
    for (const category in stored) {
      if (merged[category]) {
        merged[category] = { ...merged[category], ...stored[category] };
      }
    }
    
    return merged;
  }
  
  saveSettings() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.settings));
      this.notifySubscribers('settings-updated', this.settings);
      
      if (this.settings.sync.sync_on_change) {
        this.queueSync();
      }
    } catch (error) {
      console.error('Failed to save persistence settings:', error);
      this.notifySubscribers('save-error', error);
    }
  }
  
  initializePersistence() {
    this.setupEncryption();
    this.initializeCloudSync();
    this.setupBackupSystem();
    this.initializeOfflineSupport();
    this.startBackgroundSync();
  }
  
  setupEventListeners() {
    // Online/offline detection
    window.addEventListener('online', this.handleOnline.bind(this));
    window.addEventListener('offline', this.handleOffline.bind(this));
    
    // Visibility change for background sync
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    
    // Before unload to ensure sync
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    
    // Storage events for cross-tab sync
    window.addEventListener('storage', this.handleStorageChange.bind(this));
  }
  
  // Storage Settings Management
  updateStorageSettings(updates) {
    this.settings.storage = { ...this.settings.storage, ...updates };
    this.saveSettings();
    this.reinitializePersistence();
  }
  
  updateSyncSettings(updates) {
    this.settings.sync = { ...this.settings.sync, ...updates };
    this.saveSettings();
    this.reinitializePersistence();
  }
  
  updateDataSettings(updates) {
    this.settings.data = { ...this.settings.data, ...updates };
    this.saveSettings();
  }
  
  updateSecuritySettings(updates) {
    this.settings.security = { ...this.settings.security, ...updates };
    this.saveSettings();
    this.setupEncryption();
  }
  
  updateImportExportSettings(updates) {
    this.settings.import_export = { ...this.settings.import_export, ...updates };
    this.saveSettings();
  }
  
  reinitializePersistence() {
    this.clearSyncIntervals();
    this.initializePersistence();
  }
  
  // Cloud Sync Implementation
  initializeCloudSync() {
    if (!this.settings.storage.enable_cloud_sync) {
      this.setSyncStatus('offline');
      return;
    }
    
    this.validateCloudConnection()
      .then(() => {
        this.setSyncStatus('synced');
        this.scheduleAutoSync();
      })
      .catch((error) => {
        console.warn('Cloud sync initialization failed:', error);
        this.setSyncStatus('error');
      });
  }
  
  async validateCloudConnection() {
    try {
      const response = await fetch(`${this.cloudEndpoint}/health`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
        timeout: 5000
      });
      
      if (!response.ok) {
        throw new Error(`Cloud validation failed: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      throw new Error(`Cloud connection failed: ${error.message}`);
    }
  }
  
  scheduleAutoSync() {
    if (this.syncIntervals.has('auto')) {
      clearInterval(this.syncIntervals.get('auto'));
    }
    
    if (this.settings.storage.auto_sync_interval > 0) {
      const interval = setInterval(() => {
        this.performSync();
      }, this.settings.storage.auto_sync_interval);
      
      this.syncIntervals.set('auto', interval);
    }
  }
  
  async performSync(options = {}) {
    if (!this.settings.storage.enable_cloud_sync || this.syncStatus === 'syncing') {
      return;
    }
    
    this.setSyncStatus('syncing');
    
    try {
      // Get all preference services data
      const allPreferences = await this.gatherAllPreferences();
      
      // Check for remote changes
      const remoteData = await this.fetchRemotePreferences();
      
      // Resolve conflicts if necessary
      const mergedData = await this.resolveConflicts(allPreferences, remoteData);
      
      // Upload merged data
      await this.uploadPreferences(mergedData);
      
      // Update local storage with merged data
      await this.updateLocalPreferences(mergedData);
      
      this.lastSync = new Date().toISOString();
      this.setSyncStatus('synced');
      
      // Process offline queue
      await this.processOfflineQueue();
      
      this.notifySubscribers('sync-completed', {
        timestamp: this.lastSync,
        preferences: mergedData
      });
      
    } catch (error) {
      console.error('Sync failed:', error);
      this.setSyncStatus('error');
      this.notifySubscribers('sync-error', error);
      
      // Queue for retry if offline
      if (!navigator.onLine) {
        this.queueForOfflineSync(allPreferences);
      }
    }
  }
  
  async gatherAllPreferences() {
    const preferences = {};
    
    // Import all preference services dynamically
    const services = [
      { key: 'theme', service: 'themeCustomizationService' },
      { key: 'notifications', service: 'notificationPreferencesService' },
      { key: 'upload', service: 'uploadPreferencesService' },
      { key: 'accessibility', service: 'accessibilityOptionsService' }
    ];
    
    for (const { key, service } of services) {
      try {
        const serviceModule = await import(`../${service}.js`);
        const serviceInstance = serviceModule.default;
        
        if (this.settings.data[`include_${key}_preferences`]) {
          preferences[key] = {
            data: serviceInstance.getPreferences(),
            metadata: {
              version: serviceInstance.getVersion?.() || '1.0.0',
              lastModified: serviceInstance.getLastModified?.() || new Date().toISOString(),
              checksum: this.calculateChecksum(serviceInstance.getPreferences())
            }
          };
          
          if (this.settings.data.include_usage_statistics) {
            preferences[key].usage = serviceInstance.getUsageStatistics?.() || {};
          }
        }
      } catch (error) {
        console.warn(`Failed to gather ${key} preferences:`, error);
      }
    }
    
    return {
      preferences,
      metadata: {
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        client: 'whisper-transcriber-web',
        checksum: this.calculateChecksum(preferences)
      }
    };
  }
  
  async fetchRemotePreferences() {
    const response = await fetch(this.cloudEndpoint, {
      method: 'GET',
      headers: this.getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch remote preferences: ${response.status}`);
    }
    
    const data = await response.json();
    return this.settings.security.enable_end_to_end_encryption ? 
           await this.decryptData(data) : data;
  }
  
  async uploadPreferences(data) {
    const payload = this.settings.security.enable_end_to_end_encryption ? 
                   await this.encryptData(data) : data;
    
    const response = await fetch(this.cloudEndpoint, {
      method: 'POST',
      headers: {
        ...this.getAuthHeaders(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to upload preferences: ${response.status}`);
    }
    
    return response.json();
  }
  
  async resolveConflicts(localData, remoteData) {
    if (!remoteData || !remoteData.metadata) {
      return localData;
    }
    
    const localTimestamp = new Date(localData.metadata.timestamp);
    const remoteTimestamp = new Date(remoteData.metadata.timestamp);
    
    switch (this.settings.sync.conflict_resolution) {
      case 'local':
        return localData;
        
      case 'remote':
        return remoteData;
        
      case 'merge':
        return this.mergePreferences(localData, remoteData);
        
      case 'manual':
        return await this.promptConflictResolution(localData, remoteData);
        
      default:
        // Use newer timestamp as default
        return localTimestamp > remoteTimestamp ? localData : remoteData;
    }
  }
  
  mergePreferences(localData, remoteData) {
    const merged = {
      preferences: {},
      metadata: {
        ...localData.metadata,
        timestamp: new Date().toISOString(),
        mergedFrom: [localData.metadata.timestamp, remoteData.metadata.timestamp]
      }
    };
    
    // Merge each preference category
    const allKeys = new Set([
      ...Object.keys(localData.preferences || {}),
      ...Object.keys(remoteData.preferences || {})
    ]);
    
    for (const key of allKeys) {
      const localPrefs = localData.preferences[key];
      const remotePrefs = remoteData.preferences[key];
      
      if (!localPrefs) {
        merged.preferences[key] = remotePrefs;
      } else if (!remotePrefs) {
        merged.preferences[key] = localPrefs;
      } else {
        // Merge based on modification timestamps
        const localMod = new Date(localPrefs.metadata?.lastModified || 0);
        const remoteMod = new Date(remotePrefs.metadata?.lastModified || 0);
        
        merged.preferences[key] = localMod > remoteMod ? localPrefs : remotePrefs;
      }
    }
    
    merged.metadata.checksum = this.calculateChecksum(merged.preferences);
    return merged;
  }
  
  async promptConflictResolution(localData, remoteData) {
    return new Promise((resolve) => {
      this.notifySubscribers('conflict-detected', {
        local: localData,
        remote: remoteData,
        resolve: (choice) => {
          switch (choice) {
            case 'local':
              resolve(localData);
              break;
            case 'remote':
              resolve(remoteData);
              break;
            case 'merge':
              resolve(this.mergePreferences(localData, remoteData));
              break;
            default:
              resolve(localData);
          }
        }
      });
    });
  }
  
  // Encryption Implementation
  setupEncryption() {
    if (!this.settings.security.enable_end_to_end_encryption) {
      this.encryptionKey = null;
      return;
    }
    
    // Generate or retrieve encryption key
    this.encryptionKey = this.getOrCreateEncryptionKey();
  }
  
  getOrCreateEncryptionKey() {
    const storedKey = localStorage.getItem('whisper_encryption_key');
    if (storedKey) {
      return storedKey;
    }
    
    // Generate new key
    const key = this.generateEncryptionKey();
    localStorage.setItem('whisper_encryption_key', key);
    return key;
  }
  
  generateEncryptionKey() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  async encryptData(data) {
    if (!this.encryptionKey) {
      return data;
    }
    
    try {
      const jsonString = JSON.stringify(data);
      const encoder = new TextEncoder();
      const dataBytes = encoder.encode(jsonString);
      
      const key = await crypto.subtle.importKey(
        'raw',
        new Uint8Array(this.encryptionKey.match(/.{2}/g).map(byte => parseInt(byte, 16))),
        { name: 'AES-GCM' },
        false,
        ['encrypt']
      );
      
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv },
        key,
        dataBytes
      );
      
      return {
        encrypted: true,
        algorithm: 'AES-256-GCM',
        iv: Array.from(iv),
        data: Array.from(new Uint8Array(encrypted))
      };
    } catch (error) {
      console.error('Encryption failed:', error);
      return data; // Fallback to unencrypted
    }
  }
  
  async decryptData(encryptedData) {
    if (!encryptedData.encrypted || !this.encryptionKey) {
      return encryptedData;
    }
    
    try {
      const key = await crypto.subtle.importKey(
        'raw',
        new Uint8Array(this.encryptionKey.match(/.{2}/g).map(byte => parseInt(byte, 16))),
        { name: 'AES-GCM' },
        false,
        ['decrypt']
      );
      
      const iv = new Uint8Array(encryptedData.iv);
      const data = new Uint8Array(encryptedData.data);
      
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        data
      );
      
      const decoder = new TextDecoder();
      const jsonString = decoder.decode(decrypted);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt preferences data');
    }
  }
  
  // Backup System
  setupBackupSystem() {
    if (!this.settings.storage.enable_backup) {
      return;
    }
    
    this.scheduleBackups();
  }
  
  scheduleBackups() {
    if (this.syncIntervals.has('backup')) {
      clearInterval(this.syncIntervals.get('backup'));
    }
    
    const frequency = this.settings.storage.backup_frequency;
    const intervals = {
      hourly: 3600000,
      daily: 86400000,
      weekly: 604800000
    };
    
    if (intervals[frequency]) {
      const interval = setInterval(() => {
        this.createBackup();
      }, intervals[frequency]);
      
      this.syncIntervals.set('backup', interval);
    }
  }
  
  async createBackup() {
    try {
      const preferences = await this.gatherAllPreferences();
      const backup = {
        ...preferences,
        backup: {
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          type: 'automatic'
        }
      };
      
      const backupKey = `whisper_backup_${Date.now()}`;
      localStorage.setItem(backupKey, JSON.stringify(backup));
      
      // Clean up old backups
      this.cleanupOldBackups();
      
      this.notifySubscribers('backup-created', backup);
    } catch (error) {
      console.error('Backup creation failed:', error);
      this.notifySubscribers('backup-error', error);
    }
  }
  
  cleanupOldBackups() {
    const backupKeys = Object.keys(localStorage)
      .filter(key => key.startsWith('whisper_backup_'))
      .sort()
      .reverse();
    
    const maxBackups = this.settings.storage.max_backups;
    if (backupKeys.length > maxBackups) {
      const toDelete = backupKeys.slice(maxBackups);
      toDelete.forEach(key => localStorage.removeItem(key));
    }
  }
  
  getBackups() {
    const backupKeys = Object.keys(localStorage)
      .filter(key => key.startsWith('whisper_backup_'))
      .sort()
      .reverse();
    
    return backupKeys.map(key => {
      try {
        const backup = JSON.parse(localStorage.getItem(key));
        return {
          id: key,
          timestamp: backup.backup?.timestamp,
          size: JSON.stringify(backup).length,
          encrypted: !!backup.encrypted
        };
      } catch (error) {
        return null;
      }
    }).filter(Boolean);
  }
  
  async restoreBackup(backupId) {
    try {
      const backup = JSON.parse(localStorage.getItem(backupId));
      if (!backup) {
        throw new Error('Backup not found');
      }
      
      // Create current state backup before restore
      await this.createBackup();
      
      // Restore preferences to all services
      await this.updateLocalPreferences(backup);
      
      this.notifySubscribers('backup-restored', {
        backupId,
        timestamp: backup.backup?.timestamp
      });
      
      return true;
    } catch (error) {
      console.error('Backup restoration failed:', error);
      this.notifySubscribers('backup-restore-error', error);
      throw error;
    }
  }
  
  // Offline Support
  initializeOfflineSupport() {
    if (!this.settings.sync.offline_support) {
      return;
    }
    
    this.loadOfflineQueue();
  }
  
  loadOfflineQueue() {
    try {
      const stored = localStorage.getItem('whisper_offline_queue');
      this.offlineQueue = stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Failed to load offline queue:', error);
      this.offlineQueue = [];
    }
  }
  
  saveOfflineQueue() {
    try {
      localStorage.setItem('whisper_offline_queue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.warn('Failed to save offline queue:', error);
    }
  }
  
  queueForOfflineSync(data) {
    this.offlineQueue.push({
      data,
      timestamp: new Date().toISOString(),
      type: 'preferences_update'
    });
    
    this.saveOfflineQueue();
  }
  
  async processOfflineQueue() {
    if (this.offlineQueue.length === 0) {
      return;
    }
    
    const batch = this.offlineQueue.splice(0, this.settings.sync.batch_size);
    
    for (const item of batch) {
      try {
        await this.uploadPreferences(item.data);
      } catch (error) {
        console.warn('Failed to process offline queue item:', error);
        // Re-queue failed items
        this.offlineQueue.unshift(item);
        break;
      }
    }
    
    this.saveOfflineQueue();
  }
  
  // Event Handlers
  handleOnline() {
    if (this.settings.storage.enable_cloud_sync) {
      this.performSync();
    }
  }
  
  handleOffline() {
    this.setSyncStatus('offline');
  }
  
  handleVisibilityChange() {
    if (!document.hidden && this.settings.sync.background_sync) {
      this.queueSync();
    }
  }
  
  handleBeforeUnload() {
    if (this.offlineQueue.length > 0) {
      this.saveOfflineQueue();
    }
  }
  
  handleStorageChange(event) {
    if (event.key && event.key.startsWith('whisper_')) {
      this.notifySubscribers('cross-tab-update', {
        key: event.key,
        oldValue: event.oldValue,
        newValue: event.newValue
      });
    }
  }
  
  // Import/Export System
  async exportAllPreferences(format = 'json') {
    const preferences = await this.gatherAllPreferences();
    const exportData = {
      ...preferences,
      export: {
        timestamp: new Date().toISOString(),
        format,
        source: 'whisper-transcriber-web',
        version: '1.0.0'
      }
    };
    
    let filename, blob;
    
    switch (format) {
      case 'json':
        filename = `whisper-preferences-${new Date().toISOString().split('T')[0]}.json`;
        blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        break;
        
      case 'encrypted':
        const encrypted = await this.encryptData(exportData);
        filename = `whisper-preferences-encrypted-${new Date().toISOString().split('T')[0]}.enc`;
        blob = new Blob([JSON.stringify(encrypted)], { type: 'application/octet-stream' });
        break;
        
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    URL.revokeObjectURL(url);
    
    this.notifySubscribers('preferences-exported', {
      format,
      filename,
      size: blob.size
    });
  }
  
  async importAllPreferences(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          let data = JSON.parse(e.target.result);
          
          // Decrypt if necessary
          if (data.encrypted) {
            data = await this.decryptData(data);
          }
          
          // Validate import data
          if (!this.validateImportData(data)) {
            throw new Error('Invalid import data format');
          }
          
          // Backup current state if requested
          if (this.settings.import_export.backup_before_import) {
            await this.createBackup();
          }
          
          // Update all preferences
          await this.updateLocalPreferences(data);
          
          this.notifySubscribers('preferences-imported', {
            timestamp: data.export?.timestamp,
            source: data.export?.source
          });
          
          resolve(data);
        } catch (error) {
          reject(new Error(`Failed to import preferences: ${error.message}`));
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }
  
  validateImportData(data) {
    return data && 
           typeof data === 'object' && 
           data.preferences && 
           typeof data.preferences === 'object' &&
           data.metadata &&
           typeof data.metadata === 'object';
  }
  
  async updateLocalPreferences(data) {
    const services = [
      { key: 'theme', service: 'themeCustomizationService' },
      { key: 'notifications', service: 'notificationPreferencesService' },
      { key: 'upload', service: 'uploadPreferencesService' },
      { key: 'accessibility', service: 'accessibilityOptionsService' }
    ];
    
    for (const { key, service } of services) {
      if (data.preferences[key]) {
        try {
          const serviceModule = await import(`../${service}.js`);
          const serviceInstance = serviceModule.default;
          
          if (serviceInstance.updatePreferences) {
            serviceInstance.updatePreferences(data.preferences[key].data);
          }
        } catch (error) {
          console.warn(`Failed to update ${key} preferences:`, error);
        }
      }
    }
  }
  
  // Utility Methods
  calculateChecksum(data) {
    const str = JSON.stringify(data);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(16);
  }
  
  getAuthHeaders() {
    const headers = {
      'Accept': 'application/json'
    };
    
    // Add authentication headers if available
    const token = localStorage.getItem('whisper_auth_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }
  
  setSyncStatus(status) {
    this.syncStatus = status;
    this.notifySubscribers('sync-status-changed', status);
  }
  
  queueSync() {
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }
    
    this.syncTimeout = setTimeout(() => {
      this.performSync();
    }, 1000); // Debounce sync calls
  }
  
  clearSyncIntervals() {
    this.syncIntervals.forEach(interval => clearInterval(interval));
    this.syncIntervals.clear();
  }
  
  // Public API
  getSettings() {
    return { ...this.settings };
  }
  
  getSyncStatus() {
    return {
      status: this.syncStatus,
      lastSync: this.lastSync,
      offlineQueueSize: this.offlineQueue.length,
      cloudSyncEnabled: this.settings.storage.enable_cloud_sync
    };
  }
  
  async forceSync() {
    return this.performSync({ force: true });
  }
  
  resetSettings() {
    this.settings = { ...this.defaultSettings };
    this.saveSettings();
    this.reinitializePersistence();
    this.notifySubscribers('settings-reset', this.settings);
  }
  
  loadSyncMetadata() {
    try {
      const stored = localStorage.getItem('whisper_sync_metadata');
      if (stored) {
        const metadata = JSON.parse(stored);
        this.lastSync = metadata.lastSync;
      }
    } catch (error) {
      console.warn('Failed to load sync metadata:', error);
    }
  }
  
  saveSyncMetadata() {
    try {
      const metadata = {
        lastSync: this.lastSync,
        syncStatus: this.syncStatus
      };
      localStorage.setItem('whisper_sync_metadata', JSON.stringify(metadata));
    } catch (error) {
      console.warn('Failed to save sync metadata:', error);
    }
  }
  
  startBackgroundSync() {
    if (!this.settings.sync.background_sync) {
      return;
    }
    
    // Start background sync worker if available
    if ('serviceWorker' in navigator) {
      this.registerSyncWorker();
    }
  }
  
  async registerSyncWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/sw-sync.js');
      
      if ('sync' in window.ServiceWorkerRegistration.prototype) {
        await registration.sync.register('preferences-sync');
      }
    } catch (error) {
      console.warn('Background sync registration failed:', error);
    }
  }
  
  // Event Management
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }
  
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in persistence service subscriber:', error);
      }
    });
  }
  
  // Cleanup
  destroy() {
    this.clearSyncIntervals();
    
    if (this.syncTimeout) {
      clearTimeout(this.syncTimeout);
    }
    
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
    window.removeEventListener('storage', this.handleStorageChange);
    
    this.subscribers.clear();
  }
}

// Create and export singleton instance
const settingsPersistenceService = new SettingsPersistenceService();
export default settingsPersistenceService;