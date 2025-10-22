/**
 * T030 User Preferences Enhancement: Settings Migration System
 * Comprehensive migration system for handling settings version compatibility and updates
 */

class SettingsMigrationService {
  constructor() {
    this.subscribers = new Set();
    this.currentVersion = '1.0.0';
    this.migrationHistory = [];
    this.backupBeforeMigration = true;
    this.validateAfterMigration = true;
    this.rollbackOnFailure = true;
    
    this.migrations = new Map();
    this.validationRules = new Map();
    this.migrationStatus = 'idle'; // idle, running, completed, failed
    this.lastMigration = null;
    
    this.setupMigrationRules();
    this.loadMigrationHistory();
    this.initializeMigrationSystem();
  }
  
  initializeMigrationSystem() {
    this.checkForPendingMigrations();
    this.setupEventListeners();
    this.validateCurrentSettings();
  }
  
  setupEventListeners() {
    // Listen for settings updates that might need migration
    window.addEventListener('storage', this.handleStorageChange.bind(this));
    
    // Listen for version changes
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkForVersionUpdates();
      }
    });
  }
  
  setupMigrationRules() {
    // Define migration paths between versions
    this.registerMigration('0.9.0', '1.0.0', this.migrateFrom090To100.bind(this));
    this.registerMigration('1.0.0', '1.1.0', this.migrateFrom100To110.bind(this));
    this.registerMigration('1.1.0', '1.2.0', this.migrateFrom110To120.bind(this));
    
    // Define validation rules for each version
    this.registerValidationRule('1.0.0', this.validateVersion100.bind(this));
    this.registerValidationRule('1.1.0', this.validateVersion110.bind(this));
    this.registerValidationRule('1.2.0', this.validateVersion120.bind(this));
  }
  
  registerMigration(fromVersion, toVersion, migrationFunction) {
    const key = `${fromVersion}->${toVersion}`;
    this.migrations.set(key, {
      fromVersion,
      toVersion,
      migrate: migrationFunction,
      timestamp: new Date().toISOString()
    });
  }
  
  registerValidationRule(version, validationFunction) {
    this.validationRules.set(version, validationFunction);
  }
  
  // Version detection and comparison
  getCurrentSettingsVersion() {
    try {
      // Check theme settings version
      const themeData = localStorage.getItem('whisper_theme_preferences');
      if (themeData) {
        const parsed = JSON.parse(themeData);
        if (parsed.metadata?.version) {
          return parsed.metadata.version;
        }
      }
      
      // Check notification settings version
      const notificationData = localStorage.getItem('whisper_notification_preferences');
      if (notificationData) {
        const parsed = JSON.parse(notificationData);
        if (parsed.metadata?.version) {
          return parsed.metadata.version;
        }
      }
      
      // Check for legacy version indicator
      const legacyVersion = localStorage.getItem('whisper_settings_version');
      if (legacyVersion) {
        return legacyVersion;
      }
      
      // Default to oldest supported version if no version found
      return '0.9.0';
    } catch (error) {
      console.warn('Failed to detect settings version:', error);
      return '0.9.0';
    }
  }
  
  compareVersions(version1, version2) {
    const v1Parts = version1.split('.').map(Number);
    const v2Parts = version2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(v1Parts.length, v2Parts.length); i++) {
      const v1Part = v1Parts[i] || 0;
      const v2Part = v2Parts[i] || 0;
      
      if (v1Part < v2Part) return -1;
      if (v1Part > v2Part) return 1;
    }
    
    return 0;
  }
  
  isUpgradeNeeded(currentVersion, targetVersion = this.currentVersion) {
    return this.compareVersions(currentVersion, targetVersion) < 0;
  }
  
  // Migration execution
  async checkForPendingMigrations() {
    const currentVersion = this.getCurrentSettingsVersion();
    
    if (this.isUpgradeNeeded(currentVersion)) {
      const migrationPath = this.findMigrationPath(currentVersion, this.currentVersion);
      
      if (migrationPath.length > 0) {
        this.notifySubscribers('migration-needed', {
          from: currentVersion,
          to: this.currentVersion,
          path: migrationPath
        });
        
        // Auto-migrate if configured
        if (this.shouldAutoMigrate()) {
          await this.executeMigrationPath(migrationPath);
        }
      }
    }
  }
  
  findMigrationPath(fromVersion, toVersion) {
    // Simple linear path for now - could be enhanced with graph traversal
    const path = [];
    let currentVersion = fromVersion;
    
    while (this.compareVersions(currentVersion, toVersion) < 0) {
      const nextMigration = this.findNextMigration(currentVersion);
      if (!nextMigration) {
        break;
      }
      
      path.push(nextMigration);
      currentVersion = nextMigration.toVersion;
    }
    
    return path;
  }
  
  findNextMigration(fromVersion) {
    for (const [key, migration] of this.migrations) {
      if (migration.fromVersion === fromVersion) {
        return migration;
      }
    }
    return null;
  }
  
  async executeMigrationPath(migrationPath) {
    if (this.migrationStatus !== 'idle') {
      throw new Error('Migration already in progress');
    }
    
    this.migrationStatus = 'running';
    this.notifySubscribers('migration-started', { path: migrationPath });
    
    try {
      // Create backup before migration
      if (this.backupBeforeMigration) {
        await this.createMigrationBackup();
      }
      
      // Execute each migration step
      for (const migration of migrationPath) {
        await this.executeSingleMigration(migration);
      }
      
      // Validate final result
      if (this.validateAfterMigration) {
        const validationResult = await this.validateMigratedSettings();
        if (!validationResult.valid) {
          throw new Error(`Migration validation failed: ${validationResult.errors.join(', ')}`);
        }
      }
      
      // Update version indicator
      this.updateSettingsVersion(this.currentVersion);
      
      this.migrationStatus = 'completed';
      this.lastMigration = {
        timestamp: new Date().toISOString(),
        fromVersion: migrationPath[0].fromVersion,
        toVersion: migrationPath[migrationPath.length - 1].toVersion,
        steps: migrationPath.length
      };
      
      this.saveMigrationHistory();
      this.notifySubscribers('migration-completed', this.lastMigration);
      
    } catch (error) {
      console.error('Migration failed:', error);
      this.migrationStatus = 'failed';
      
      // Rollback if configured
      if (this.rollbackOnFailure) {
        await this.rollbackMigration();
      }
      
      this.notifySubscribers('migration-failed', { error: error.message });
      throw error;
    }
  }
  
  async executeSingleMigration(migration) {
    try {
      console.log(`Migrating from ${migration.fromVersion} to ${migration.toVersion}`);
      
      // Get current settings
      const currentSettings = await this.getAllCurrentSettings();
      
      // Execute migration
      const migratedSettings = await migration.migrate(currentSettings);
      
      // Apply migrated settings
      await this.applyMigratedSettings(migratedSettings);
      
      // Record migration step
      this.migrationHistory.push({
        timestamp: new Date().toISOString(),
        fromVersion: migration.fromVersion,
        toVersion: migration.toVersion,
        status: 'completed'
      });
      
    } catch (error) {
      this.migrationHistory.push({
        timestamp: new Date().toISOString(),
        fromVersion: migration.fromVersion,
        toVersion: migration.toVersion,
        status: 'failed',
        error: error.message
      });
      throw error;
    }
  }
  
  // Specific migration implementations
  async migrateFrom090To100(settings) {
    console.log('Migrating from 0.9.0 to 1.0.0');
    
    const migrated = { ...settings };
    
    // Theme settings migration
    if (migrated.theme) {
      // Convert old theme format to new format
      if (typeof migrated.theme.darkMode === 'boolean') {
        migrated.theme.appearance = {
          theme: migrated.theme.darkMode ? 'dark' : 'light',
          auto_theme_switching: false,
          custom_themes: migrated.theme.customThemes || {}
        };
        delete migrated.theme.darkMode;
        delete migrated.theme.customThemes;
      }
      
      // Add metadata
      migrated.theme.metadata = {
        version: '1.0.0',
        lastModified: new Date().toISOString(),
        migrated: true
      };
    }
    
    // Notification settings migration
    if (migrated.notifications) {
      // Convert old notification format
      if (migrated.notifications.enabled !== undefined) {
        migrated.notifications.categories = {
          transcription: { enabled: migrated.notifications.enabled },
          batch: { enabled: migrated.notifications.enabled },
          system: { enabled: migrated.notifications.enabled },
          account: { enabled: migrated.notifications.enabled }
        };
        delete migrated.notifications.enabled;
      }
      
      // Add new fields with defaults
      migrated.notifications.delivery_methods = {
        browser: true,
        email: false,
        push: false
      };
      
      migrated.notifications.metadata = {
        version: '1.0.0',
        lastModified: new Date().toISOString(),
        migrated: true
      };
    }
    
    return migrated;
  }
  
  async migrateFrom100To110(settings) {
    console.log('Migrating from 1.0.0 to 1.1.0');
    
    const migrated = { ...settings };
    
    // Add upload preferences (new in 1.1.0)
    if (!migrated.upload) {
      migrated.upload = {
        general: {
          auto_upload: false,
          max_simultaneous_uploads: 3,
          chunk_size: 1048576,
          show_previews: true
        },
        file_handling: {
          accepted_formats: ['audio/mpeg', 'audio/wav', 'audio/mp4'],
          max_file_size: 104857600,
          auto_validate_files: true
        },
        metadata: {
          version: '1.1.0',
          lastModified: new Date().toISOString(),
          migrated: true
        }
      };
    }
    
    // Update existing metadata versions
    if (migrated.theme?.metadata) {
      migrated.theme.metadata.version = '1.1.0';
      migrated.theme.metadata.lastModified = new Date().toISOString();
    }
    
    if (migrated.notifications?.metadata) {
      migrated.notifications.metadata.version = '1.1.0';
      migrated.notifications.metadata.lastModified = new Date().toISOString();
    }
    
    return migrated;
  }
  
  async migrateFrom110To120(settings) {
    console.log('Migrating from 1.1.0 to 1.2.0');
    
    const migrated = { ...settings };
    
    // Add accessibility preferences (new in 1.2.0)
    if (!migrated.accessibility) {
      migrated.accessibility = {
        vision: {
          high_contrast: false,
          font_size_scale: 1.0,
          reduce_motion: false
        },
        motor: {
          keyboard_navigation_only: false,
          touch_target_size: 44
        },
        cognitive: {
          simplified_interface: false,
          reduce_cognitive_load: false
        },
        metadata: {
          version: '1.2.0',
          lastModified: new Date().toISOString(),
          migrated: true
        }
      };
    }
    
    // Add persistence settings (new in 1.2.0)
    if (!migrated.persistence) {
      migrated.persistence = {
        storage: {
          enable_cloud_sync: false,
          auto_sync_interval: 300000,
          enable_backup: true
        },
        sync: {
          conflict_resolution: 'merge',
          offline_support: true
        },
        metadata: {
          version: '1.2.0',
          lastModified: new Date().toISOString(),
          migrated: true
        }
      };
    }
    
    // Update all metadata versions
    Object.keys(migrated).forEach(key => {
      if (migrated[key]?.metadata) {
        migrated[key].metadata.version = '1.2.0';
        migrated[key].metadata.lastModified = new Date().toISOString();
      }
    });
    
    return migrated;
  }
  
  // Validation implementations
  validateVersion100(settings) {
    const errors = [];
    
    // Validate theme settings
    if (settings.theme) {
      if (!settings.theme.appearance) {
        errors.push('Theme appearance settings missing');
      }
      if (!settings.theme.metadata?.version) {
        errors.push('Theme metadata version missing');
      }
    }
    
    // Validate notification settings
    if (settings.notifications) {
      if (!settings.notifications.categories) {
        errors.push('Notification categories missing');
      }
      if (!settings.notifications.delivery_methods) {
        errors.push('Notification delivery methods missing');
      }
    }
    
    return {
      valid: errors.length === 0,
      errors,
      version: '1.0.0'
    };
  }
  
  validateVersion110(settings) {
    const v100Validation = this.validateVersion100(settings);
    const errors = [...v100Validation.errors];
    
    // Additional validations for 1.1.0
    if (!settings.upload) {
      errors.push('Upload preferences missing');
    } else {
      if (!settings.upload.general) {
        errors.push('Upload general settings missing');
      }
      if (!settings.upload.file_handling) {
        errors.push('Upload file handling settings missing');
      }
    }
    
    return {
      valid: errors.length === 0,
      errors,
      version: '1.1.0'
    };
  }
  
  validateVersion120(settings) {
    const v110Validation = this.validateVersion110(settings);
    const errors = [...v110Validation.errors];
    
    // Additional validations for 1.2.0
    if (!settings.accessibility) {
      errors.push('Accessibility preferences missing');
    }
    
    if (!settings.persistence) {
      errors.push('Persistence settings missing');
    }
    
    return {
      valid: errors.length === 0,
      errors,
      version: '1.2.0'
    };
  }
  
  // Backup and rollback functionality
  async createMigrationBackup() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupKey = `whisper_migration_backup_${timestamp}`;
    
    try {
      const currentSettings = await this.getAllCurrentSettings();
      const backup = {
        timestamp,
        version: this.getCurrentSettingsVersion(),
        settings: currentSettings,
        metadata: {
          created: new Date().toISOString(),
          reason: 'pre-migration-backup',
          size: JSON.stringify(currentSettings).length
        }
      };
      
      localStorage.setItem(backupKey, JSON.stringify(backup));
      
      // Clean up old backups (keep last 5)
      this.cleanupOldBackups('whisper_migration_backup_');
      
      this.notifySubscribers('backup-created', { key: backupKey, backup });
      return backupKey;
      
    } catch (error) {
      console.error('Failed to create migration backup:', error);
      throw error;
    }
  }
  
  async rollbackMigration() {
    try {
      const latestBackup = this.findLatestBackup('whisper_migration_backup_');
      
      if (!latestBackup) {
        throw new Error('No migration backup found for rollback');
      }
      
      console.log('Rolling back migration using backup:', latestBackup.key);
      
      // Restore from backup
      await this.applyMigratedSettings(latestBackup.backup.settings);
      
      // Update version
      this.updateSettingsVersion(latestBackup.backup.version);
      
      this.notifySubscribers('migration-rolled-back', {
        backupTimestamp: latestBackup.backup.timestamp,
        restoredVersion: latestBackup.backup.version
      });
      
      this.migrationStatus = 'idle';
      
    } catch (error) {
      console.error('Migration rollback failed:', error);
      throw error;
    }
  }
  
  findLatestBackup(prefix) {
    const backupKeys = Object.keys(localStorage)
      .filter(key => key.startsWith(prefix))
      .sort()
      .reverse();
    
    if (backupKeys.length === 0) {
      return null;
    }
    
    try {
      const latestKey = backupKeys[0];
      const backup = JSON.parse(localStorage.getItem(latestKey));
      return { key: latestKey, backup };
    } catch (error) {
      console.warn('Failed to parse latest backup:', error);
      return null;
    }
  }
  
  cleanupOldBackups(prefix, maxBackups = 5) {
    const backupKeys = Object.keys(localStorage)
      .filter(key => key.startsWith(prefix))
      .sort()
      .reverse();
    
    if (backupKeys.length > maxBackups) {
      const toDelete = backupKeys.slice(maxBackups);
      toDelete.forEach(key => {
        localStorage.removeItem(key);
      });
    }
  }
  
  // Settings management utilities
  async getAllCurrentSettings() {
    const settings = {};
    
    // Get theme settings
    try {
      const themeData = localStorage.getItem('whisper_theme_preferences');
      if (themeData) {
        settings.theme = JSON.parse(themeData);
      }
    } catch (error) {
      console.warn('Failed to load theme settings:', error);
    }
    
    // Get notification settings
    try {
      const notificationData = localStorage.getItem('whisper_notification_preferences');
      if (notificationData) {
        settings.notifications = JSON.parse(notificationData);
      }
    } catch (error) {
      console.warn('Failed to load notification settings:', error);
    }
    
    // Get upload settings
    try {
      const uploadData = localStorage.getItem('whisper_upload_preferences');
      if (uploadData) {
        settings.upload = JSON.parse(uploadData);
      }
    } catch (error) {
      console.warn('Failed to load upload settings:', error);
    }
    
    // Get accessibility settings
    try {
      const accessibilityData = localStorage.getItem('whisper_accessibility_preferences');
      if (accessibilityData) {
        settings.accessibility = JSON.parse(accessibilityData);
      }
    } catch (error) {
      console.warn('Failed to load accessibility settings:', error);
    }
    
    // Get persistence settings
    try {
      const persistenceData = localStorage.getItem('whisper_settings_persistence');
      if (persistenceData) {
        settings.persistence = JSON.parse(persistenceData);
      }
    } catch (error) {
      console.warn('Failed to load persistence settings:', error);
    }
    
    return settings;
  }
  
  async applyMigratedSettings(settings) {
    // Apply theme settings
    if (settings.theme) {
      localStorage.setItem('whisper_theme_preferences', JSON.stringify(settings.theme));
    }
    
    // Apply notification settings
    if (settings.notifications) {
      localStorage.setItem('whisper_notification_preferences', JSON.stringify(settings.notifications));
    }
    
    // Apply upload settings
    if (settings.upload) {
      localStorage.setItem('whisper_upload_preferences', JSON.stringify(settings.upload));
    }
    
    // Apply accessibility settings
    if (settings.accessibility) {
      localStorage.setItem('whisper_accessibility_preferences', JSON.stringify(settings.accessibility));
    }
    
    // Apply persistence settings
    if (settings.persistence) {
      localStorage.setItem('whisper_settings_persistence', JSON.stringify(settings.persistence));
    }
  }
  
  updateSettingsVersion(version) {
    localStorage.setItem('whisper_settings_version', version);
  }
  
  async validateMigratedSettings() {
    const currentVersion = this.currentVersion;
    const validator = this.validationRules.get(currentVersion);
    
    if (!validator) {
      return { valid: true, errors: [] };
    }
    
    const settings = await this.getAllCurrentSettings();
    return validator(settings);
  }
  
  // Configuration and utilities
  shouldAutoMigrate() {
    // Check user preference for auto-migration
    const autoMigrate = localStorage.getItem('whisper_auto_migrate');
    return autoMigrate === null || autoMigrate === 'true';
  }
  
  setAutoMigrate(enabled) {
    localStorage.setItem('whisper_auto_migrate', enabled.toString());
  }
  
  checkForVersionUpdates() {
    const lastCheckedVersion = localStorage.getItem('whisper_last_checked_version');
    const currentAppVersion = this.getAppVersion();
    
    if (lastCheckedVersion !== currentAppVersion) {
      localStorage.setItem('whisper_last_checked_version', currentAppVersion);
      this.checkForPendingMigrations();
    }
  }
  
  getAppVersion() {
    // Get version from package.json or build info
    return window.APP_VERSION || this.currentVersion;
  }
  
  handleStorageChange(event) {
    if (event.key && event.key.startsWith('whisper_')) {
      // Settings changed, might need validation
      setTimeout(() => {
        this.validateCurrentSettings();
      }, 100);
    }
  }
  
  async validateCurrentSettings() {
    try {
      const validation = await this.validateMigratedSettings();
      if (!validation.valid) {
        this.notifySubscribers('validation-failed', validation);
      }
    } catch (error) {
      console.warn('Settings validation failed:', error);
    }
  }
  
  loadMigrationHistory() {
    try {
      const stored = localStorage.getItem('whisper_migration_history');
      if (stored) {
        this.migrationHistory = JSON.parse(stored);
      }
    } catch (error) {
      console.warn('Failed to load migration history:', error);
      this.migrationHistory = [];
    }
  }
  
  saveMigrationHistory() {
    try {
      localStorage.setItem('whisper_migration_history', JSON.stringify(this.migrationHistory));
    } catch (error) {
      console.warn('Failed to save migration history:', error);
    }
  }
  
  // Public API
  getMigrationStatus() {
    return {
      status: this.migrationStatus,
      currentVersion: this.getCurrentSettingsVersion(),
      targetVersion: this.currentVersion,
      lastMigration: this.lastMigration,
      historyCount: this.migrationHistory.length,
      autoMigrate: this.shouldAutoMigrate()
    };
  }
  
  getMigrationHistory() {
    return [...this.migrationHistory];
  }
  
  async forceMigration(targetVersion = this.currentVersion) {
    const currentVersion = this.getCurrentSettingsVersion();
    
    if (!this.isUpgradeNeeded(currentVersion, targetVersion)) {
      throw new Error('No migration needed');
    }
    
    const migrationPath = this.findMigrationPath(currentVersion, targetVersion);
    
    if (migrationPath.length === 0) {
      throw new Error('No migration path found');
    }
    
    return this.executeMigrationPath(migrationPath);
  }
  
  getAvailableBackups() {
    const backupKeys = Object.keys(localStorage)
      .filter(key => key.startsWith('whisper_migration_backup_'))
      .sort()
      .reverse();
    
    return backupKeys.map(key => {
      try {
        const backup = JSON.parse(localStorage.getItem(key));
        return {
          key,
          timestamp: backup.timestamp,
          version: backup.version,
          size: backup.metadata?.size || 0,
          created: backup.metadata?.created
        };
      } catch (error) {
        return null;
      }
    }).filter(Boolean);
  }
  
  async restoreFromBackup(backupKey) {
    try {
      const backup = JSON.parse(localStorage.getItem(backupKey));
      
      if (!backup) {
        throw new Error('Backup not found');
      }
      
      // Create current state backup before restore
      await this.createMigrationBackup();
      
      // Restore from backup
      await this.applyMigratedSettings(backup.settings);
      this.updateSettingsVersion(backup.version);
      
      this.notifySubscribers('backup-restored', {
        backupKey,
        restoredVersion: backup.version,
        timestamp: backup.timestamp
      });
      
      return true;
    } catch (error) {
      console.error('Backup restoration failed:', error);
      throw error;
    }
  }
  
  // Event management
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }
  
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in migration service subscriber:', error);
      }
    });
  }
  
  // Cleanup
  destroy() {
    window.removeEventListener('storage', this.handleStorageChange);
    this.subscribers.clear();
  }
}

// Create and export singleton instance
const settingsMigrationService = new SettingsMigrationService();
export default settingsMigrationService;