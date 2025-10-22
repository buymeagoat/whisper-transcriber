#!/usr/bin/env node

/**
 * T030 User Preferences Enhancement: Settings Migration CLI Utility
 * Command-line tool for managing settings migrations, backups, and version compatibility
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SettingsMigrationCLI {
  constructor() {
    this.currentVersion = '1.2.0';
    this.settingsPath = process.env.SETTINGS_PATH || './frontend/src/data';
    this.backupPath = process.env.BACKUP_PATH || './temp/settings-backups';
    
    this.ensureDirectories();
  }
  
  ensureDirectories() {
    if (!fs.existsSync(this.settingsPath)) {
      fs.mkdirSync(this.settingsPath, { recursive: true });
    }
    
    if (!fs.existsSync(this.backupPath)) {
      fs.mkdirSync(this.backupPath, { recursive: true });
    }
  }
  
  // Command handlers
  async handleCommand(command, args) {
    switch (command) {
      case 'status':
        return this.showStatus();
      case 'migrate':
        return this.runMigration(args);
      case 'backup':
        return this.createBackup(args);
      case 'restore':
        return this.restoreBackup(args);
      case 'validate':
        return this.validateSettings(args);
      case 'clean':
        return this.cleanupBackups(args);
      case 'init':
        return this.initializeSettings(args);
      case 'help':
      default:
        return this.showHelp();
    }
  }
  
  showStatus() {
    console.log('🔍 Settings Migration Status');
    console.log('============================');
    
    try {
      const currentVersion = this.detectCurrentVersion();
      const backups = this.getAvailableBackups();
      const validationResult = this.validateCurrentSettings();
      
      console.log(`📦 Current Version: ${currentVersion}`);
      console.log(`🎯 Target Version: ${this.currentVersion}`);
      console.log(`🔄 Migration Needed: ${currentVersion !== this.currentVersion ? 'Yes' : 'No'}`);
      console.log(`💾 Available Backups: ${backups.length}`);
      console.log(`✅ Settings Valid: ${validationResult.valid ? 'Yes' : 'No'}`);
      
      if (!validationResult.valid) {
        console.log('❌ Validation Errors:');
        validationResult.errors.forEach(error => {
          console.log(`   - ${error}`);
        });
      }
      
      if (backups.length > 0) {
        console.log('\n📁 Recent Backups:');
        backups.slice(0, 3).forEach(backup => {
          console.log(`   - ${backup.filename} (${backup.version}, ${backup.size})`);
        });
      }
      
    } catch (error) {
      console.error('❌ Failed to get status:', error.message);
      process.exit(1);
    }
  }
  
  async runMigration(args) {
    const targetVersion = args[0] || this.currentVersion;
    const force = args.includes('--force');
    const noBackup = args.includes('--no-backup');
    
    console.log(`🔄 Starting migration to version ${targetVersion}`);
    
    try {
      const currentVersion = this.detectCurrentVersion();
      
      if (currentVersion === targetVersion && !force) {
        console.log('✅ Already at target version');
        return;
      }
      
      // Create backup unless disabled
      let backupFile = null;
      if (!noBackup) {
        console.log('💾 Creating pre-migration backup...');
        backupFile = await this.createBackupInternal();
        console.log(`✅ Backup created: ${backupFile}`);
      }
      
      // Determine migration path
      const migrationPath = this.findMigrationPath(currentVersion, targetVersion);
      
      if (migrationPath.length === 0) {
        throw new Error(`No migration path found from ${currentVersion} to ${targetVersion}`);
      }
      
      console.log(`📋 Migration path: ${migrationPath.map(m => `${m.from}→${m.to}`).join(' → ')}`);
      
      // Execute migrations
      for (const migration of migrationPath) {
        console.log(`⚡ Migrating ${migration.from} → ${migration.to}...`);
        await this.executeMigration(migration);
      }
      
      // Validate result
      const validationResult = this.validateCurrentSettings();
      if (!validationResult.valid) {
        throw new Error(`Migration validation failed: ${validationResult.errors.join(', ')}`);
      }
      
      console.log('✅ Migration completed successfully');
      
    } catch (error) {
      console.error('❌ Migration failed:', error.message);
      
      if (backupFile && !noBackup) {
        console.log(`🔄 Restoring from backup: ${backupFile}`);
        try {
          await this.restoreBackupInternal(backupFile);
          console.log('✅ Rollback completed');
        } catch (restoreError) {
          console.error('❌ Rollback failed:', restoreError.message);
        }
      }
      
      process.exit(1);
    }
  }
  
  async createBackup(args) {
    const label = args[0] || 'manual';
    
    console.log('💾 Creating settings backup...');
    
    try {
      const backupFile = await this.createBackupInternal(label);
      console.log(`✅ Backup created: ${backupFile}`);
    } catch (error) {
      console.error('❌ Backup failed:', error.message);
      process.exit(1);
    }
  }
  
  async restoreBackup(args) {
    const backupFile = args[0];
    
    if (!backupFile) {
      const backups = this.getAvailableBackups();
      if (backups.length === 0) {
        console.log('❌ No backups available');
        return;
      }
      
      console.log('📁 Available backups:');
      backups.forEach((backup, index) => {
        console.log(`   ${index + 1}. ${backup.filename} (${backup.version}, ${backup.created})`);
      });
      console.log('\nUsage: npm run migrate restore <backup-filename>');
      return;
    }
    
    console.log(`🔄 Restoring from backup: ${backupFile}`);
    
    try {
      await this.restoreBackupInternal(backupFile);
      console.log('✅ Restore completed successfully');
    } catch (error) {
      console.error('❌ Restore failed:', error.message);
      process.exit(1);
    }
  }
  
  validateSettings(args) {
    const version = args[0] || this.currentVersion;
    
    console.log(`🔍 Validating settings for version ${version}...`);
    
    try {
      const result = this.validateCurrentSettings(version);
      
      if (result.valid) {
        console.log('✅ All settings are valid');
      } else {
        console.log('❌ Validation failed:');
        result.errors.forEach(error => {
          console.log(`   - ${error}`);
        });
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ Validation error:', error.message);
      process.exit(1);
    }
  }
  
  cleanupBackups(args) {
    const maxBackups = parseInt(args[0]) || 5;
    
    console.log(`🧹 Cleaning up old backups (keeping ${maxBackups})...`);
    
    try {
      const backups = this.getAvailableBackups();
      
      if (backups.length <= maxBackups) {
        console.log('✅ No cleanup needed');
        return;
      }
      
      const toDelete = backups.slice(maxBackups);
      
      toDelete.forEach(backup => {
        const backupPath = path.join(this.backupPath, backup.filename);
        fs.unlinkSync(backupPath);
        console.log(`🗑️  Deleted: ${backup.filename}`);
      });
      
      console.log(`✅ Cleaned up ${toDelete.length} old backups`);
      
    } catch (error) {
      console.error('❌ Cleanup failed:', error.message);
      process.exit(1);
    }
  }
  
  initializeSettings(args) {
    const version = args[0] || this.currentVersion;
    
    console.log(`🚀 Initializing settings for version ${version}...`);
    
    try {
      const defaultSettings = this.generateDefaultSettings(version);
      
      Object.entries(defaultSettings).forEach(([key, value]) => {
        const filePath = path.join(this.settingsPath, `${key}.json`);
        fs.writeFileSync(filePath, JSON.stringify(value, null, 2));
        console.log(`✅ Created: ${key}.json`);
      });
      
      console.log('✅ Settings initialization completed');
      
    } catch (error) {
      console.error('❌ Initialization failed:', error.message);
      process.exit(1);
    }
  }
  
  showHelp() {
    console.log(`
🔧 Settings Migration CLI Utility
=================================

USAGE:
  npm run migrate <command> [options]

COMMANDS:
  status                 Show current migration status
  migrate [version]      Migrate to target version (default: ${this.currentVersion})
  backup [label]         Create a settings backup
  restore [filename]     Restore from backup (lists backups if no filename)
  validate [version]     Validate current settings
  clean [count]          Clean up old backups (default: keep 5)
  init [version]         Initialize default settings
  help                   Show this help

MIGRATION OPTIONS:
  --force               Force migration even if already at target version
  --no-backup           Skip pre-migration backup

EXAMPLES:
  npm run migrate status
  npm run migrate migrate 1.2.0
  npm run migrate backup manual-backup
  npm run migrate restore backup-20231215-143022.json
  npm run migrate clean 3
  npm run migrate validate 1.2.0
  npm run migrate init 1.2.0

ENVIRONMENT VARIABLES:
  SETTINGS_PATH         Path to settings files (default: ./frontend/src/data)
  BACKUP_PATH           Path for backups (default: ./temp/settings-backups)
`);
  }
  
  // Internal implementation methods
  detectCurrentVersion() {
    try {
      // Check for version file
      const versionFile = path.join(this.settingsPath, 'version.json');
      if (fs.existsSync(versionFile)) {
        const versionData = JSON.parse(fs.readFileSync(versionFile, 'utf8'));
        return versionData.version;
      }
      
      // Check theme settings for version
      const themeFile = path.join(this.settingsPath, 'theme.json');
      if (fs.existsSync(themeFile)) {
        const themeData = JSON.parse(fs.readFileSync(themeFile, 'utf8'));
        if (themeData.metadata?.version) {
          return themeData.metadata.version;
        }
      }
      
      // Default to oldest supported version
      return '1.0.0';
    } catch (error) {
      console.warn('Warning: Could not detect current version, assuming 1.0.0');
      return '1.0.0';
    }
  }
  
  findMigrationPath(fromVersion, toVersion) {
    const migrations = [
      { from: '1.0.0', to: '1.1.0' },
      { from: '1.1.0', to: '1.2.0' }
    ];
    
    const path = [];
    let currentVersion = fromVersion;
    
    while (this.compareVersions(currentVersion, toVersion) < 0) {
      const nextMigration = migrations.find(m => m.from === currentVersion);
      if (!nextMigration) {
        break;
      }
      
      path.push(nextMigration);
      currentVersion = nextMigration.to;
    }
    
    return path;
  }
  
  compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
      const part1 = parts1[i] || 0;
      const part2 = parts2[i] || 0;
      
      if (part1 < part2) return -1;
      if (part1 > part2) return 1;
    }
    
    return 0;
  }
  
  async executeMigration(migration) {
    // Load current settings
    const settings = this.loadAllSettings();
    
    // Apply migration
    const migrated = await this.applyMigration(settings, migration);
    
    // Save migrated settings
    this.saveAllSettings(migrated);
    
    // Update version
    this.updateVersion(migration.to);
  }
  
  applyMigration(settings, migration) {
    // Implementation would depend on specific migration logic
    // For now, return settings with updated metadata
    const migrated = { ...settings };
    
    Object.keys(migrated).forEach(key => {
      if (migrated[key] && typeof migrated[key] === 'object') {
        if (!migrated[key].metadata) {
          migrated[key].metadata = {};
        }
        migrated[key].metadata.version = migration.to;
        migrated[key].metadata.lastModified = new Date().toISOString();
        migrated[key].metadata.migrated = true;
      }
    });
    
    return migrated;
  }
  
  loadAllSettings() {
    const settings = {};
    const settingsFiles = ['theme', 'notifications', 'upload', 'accessibility', 'persistence'];
    
    settingsFiles.forEach(file => {
      const filePath = path.join(this.settingsPath, `${file}.json`);
      if (fs.existsSync(filePath)) {
        try {
          settings[file] = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        } catch (error) {
          console.warn(`Warning: Could not load ${file}.json`);
        }
      }
    });
    
    return settings;
  }
  
  saveAllSettings(settings) {
    Object.entries(settings).forEach(([key, value]) => {
      const filePath = path.join(this.settingsPath, `${key}.json`);
      fs.writeFileSync(filePath, JSON.stringify(value, null, 2));
    });
  }
  
  updateVersion(version) {
    const versionFile = path.join(this.settingsPath, 'version.json');
    const versionData = {
      version,
      updated: new Date().toISOString(),
      tool: 'migration-cli'
    };
    fs.writeFileSync(versionFile, JSON.stringify(versionData, null, 2));
  }
  
  async createBackupInternal(label = 'auto') {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `backup-${timestamp}-${label}.json`;
    const backupPath = path.join(this.backupPath, filename);
    
    const settings = this.loadAllSettings();
    const backup = {
      timestamp: new Date().toISOString(),
      version: this.detectCurrentVersion(),
      label,
      settings,
      metadata: {
        created: new Date().toISOString(),
        tool: 'migration-cli',
        size: JSON.stringify(settings).length
      }
    };
    
    fs.writeFileSync(backupPath, JSON.stringify(backup, null, 2));
    return filename;
  }
  
  async restoreBackupInternal(filename) {
    const backupPath = path.join(this.backupPath, filename);
    
    if (!fs.existsSync(backupPath)) {
      throw new Error(`Backup file not found: ${filename}`);
    }
    
    const backup = JSON.parse(fs.readFileSync(backupPath, 'utf8'));
    
    // Create current state backup before restore
    await this.createBackupInternal('pre-restore');
    
    // Restore settings
    this.saveAllSettings(backup.settings);
    this.updateVersion(backup.version);
  }
  
  getAvailableBackups() {
    if (!fs.existsSync(this.backupPath)) {
      return [];
    }
    
    return fs.readdirSync(this.backupPath)
      .filter(file => file.endsWith('.json'))
      .map(filename => {
        const filePath = path.join(this.backupPath, filename);
        const stats = fs.statSync(filePath);
        
        try {
          const backup = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          return {
            filename,
            version: backup.version,
            created: backup.timestamp,
            size: this.formatFileSize(stats.size),
            timestamp: backup.timestamp
          };
        } catch (error) {
          return {
            filename,
            version: 'unknown',
            created: stats.mtime.toISOString(),
            size: this.formatFileSize(stats.size),
            timestamp: stats.mtime.toISOString()
          };
        }
      })
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }
  
  validateCurrentSettings(version = this.currentVersion) {
    const settings = this.loadAllSettings();
    const errors = [];
    
    // Basic validation rules
    if (version >= '1.0.0') {
      if (!settings.theme) {
        errors.push('Theme settings missing');
      }
      if (!settings.notifications) {
        errors.push('Notification settings missing');
      }
    }
    
    if (version >= '1.1.0') {
      if (!settings.upload) {
        errors.push('Upload settings missing');
      }
    }
    
    if (version >= '1.2.0') {
      if (!settings.accessibility) {
        errors.push('Accessibility settings missing');
      }
      if (!settings.persistence) {
        errors.push('Persistence settings missing');
      }
    }
    
    // Validate metadata versions
    Object.entries(settings).forEach(([key, value]) => {
      if (value && value.metadata) {
        if (!value.metadata.version) {
          errors.push(`${key}: metadata version missing`);
        } else if (this.compareVersions(value.metadata.version, version) < 0) {
          errors.push(`${key}: outdated version ${value.metadata.version}`);
        }
      }
    });
    
    return {
      valid: errors.length === 0,
      errors,
      version
    };
  }
  
  generateDefaultSettings(version) {
    const defaults = {
      theme: {
        appearance: {
          theme: 'light',
          auto_theme_switching: false,
          custom_themes: {}
        },
        metadata: {
          version,
          lastModified: new Date().toISOString(),
          initialized: true
        }
      },
      notifications: {
        categories: {
          transcription: { enabled: true },
          batch: { enabled: true },
          system: { enabled: true },
          account: { enabled: true }
        },
        delivery_methods: {
          browser: true,
          email: false,
          push: false
        },
        metadata: {
          version,
          lastModified: new Date().toISOString(),
          initialized: true
        }
      }
    };
    
    if (this.compareVersions(version, '1.1.0') >= 0) {
      defaults.upload = {
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
          version,
          lastModified: new Date().toISOString(),
          initialized: true
        }
      };
    }
    
    if (this.compareVersions(version, '1.2.0') >= 0) {
      defaults.accessibility = {
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
          version,
          lastModified: new Date().toISOString(),
          initialized: true
        }
      };
      
      defaults.persistence = {
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
          version,
          lastModified: new Date().toISOString(),
          initialized: true
        }
      };
    }
    
    return defaults;
  }
  
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

// CLI entry point
if (require.main === module) {
  const cli = new SettingsMigrationCLI();
  const [,, command, ...args] = process.argv;
  
  cli.handleCommand(command, args).catch(error => {
    console.error('❌ CLI Error:', error.message);
    process.exit(1);
  });
}

module.exports = SettingsMigrationCLI;