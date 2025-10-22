/**
 * T030 User Preferences Enhancement: Settings Migration Management Component
 * React component for managing settings migrations, backups, and version compatibility
 */

import React, { useState, useEffect, useCallback } from 'react';
import settingsMigrationService from '../services/settingsMigrationService.js';
import './settings-migration.css';

const SettingsMigrationManager = ({ onClose }) => {
  const [migrationStatus, setMigrationStatus] = useState(null);
  const [migrationHistory, setMigrationHistory] = useState([]);
  const [availableBackups, setAvailableBackups] = useState([]);
  const [activeTab, setActiveTab] = useState('status');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);
  
  // Load initial data
  useEffect(() => {
    loadMigrationData();
    
    // Subscribe to migration events
    const unsubscribe = settingsMigrationService.subscribe(handleMigrationEvent);
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  const loadMigrationData = async () => {
    try {
      setIsLoading(true);
      const status = settingsMigrationService.getMigrationStatus();
      const history = settingsMigrationService.getMigrationHistory();
      const backups = settingsMigrationService.getAvailableBackups();
      
      setMigrationStatus(status);
      setMigrationHistory(history);
      setAvailableBackups(backups);
    } catch (error) {
      setError('Failed to load migration data: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleMigrationEvent = useCallback((event, data) => {
    switch (event) {
      case 'migration-needed':
        setError(null);
        setSuccess(`Migration available: ${data.from} → ${data.to}`);
        break;
        
      case 'migration-started':
        setError(null);
        setSuccess('Migration started...');
        setIsLoading(true);
        break;
        
      case 'migration-completed':
        setSuccess(`Migration completed successfully: ${data.fromVersion} → ${data.toVersion}`);
        setIsLoading(false);
        loadMigrationData();
        break;
        
      case 'migration-failed':
        setError('Migration failed: ' + data.error);
        setIsLoading(false);
        loadMigrationData();
        break;
        
      case 'migration-rolled-back':
        setSuccess(`Migration rolled back to version ${data.restoredVersion}`);
        setIsLoading(false);
        loadMigrationData();
        break;
        
      case 'backup-created':
        setSuccess('Backup created successfully');
        loadMigrationData();
        break;
        
      case 'backup-restored':
        setSuccess(`Backup restored: ${data.restoredVersion}`);
        loadMigrationData();
        break;
        
      case 'validation-failed':
        setError('Settings validation failed: ' + data.errors.join(', '));
        break;
    }
  }, []);
  
  const handleForceMigration = async () => {
    if (!migrationStatus) return;
    
    setConfirmDialog({
      title: 'Force Migration',
      message: `This will migrate your settings from ${migrationStatus.currentVersion} to ${migrationStatus.targetVersion}. A backup will be created automatically.`,
      onConfirm: async () => {
        try {
          setError(null);
          await settingsMigrationService.forceMigration();
        } catch (error) {
          setError('Force migration failed: ' + error.message);
        }
        setConfirmDialog(null);
      },
      onCancel: () => setConfirmDialog(null)
    });
  };
  
  const handleCreateBackup = async () => {
    try {
      setError(null);
      setIsLoading(true);
      await settingsMigrationService.createMigrationBackup();
    } catch (error) {
      setError('Failed to create backup: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRestoreBackup = (backup) => {
    setConfirmDialog({
      title: 'Restore Backup',
      message: `This will restore your settings to version ${backup.version} from ${new Date(backup.timestamp).toLocaleString()}. Your current settings will be backed up first.`,
      onConfirm: async () => {
        try {
          setError(null);
          setIsLoading(true);
          await settingsMigrationService.restoreFromBackup(backup.key);
        } catch (error) {
          setError('Failed to restore backup: ' + error.message);
        } finally {
          setIsLoading(false);
        }
        setConfirmDialog(null);
      },
      onCancel: () => setConfirmDialog(null)
    });
  };
  
  const handleToggleAutoMigrate = () => {
    const newValue = !migrationStatus.autoMigrate;
    settingsMigrationService.setAutoMigrate(newValue);
    setMigrationStatus(prev => ({ ...prev, autoMigrate: newValue }));
    setSuccess(`Auto-migration ${newValue ? 'enabled' : 'disabled'}`);
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'idle': return 'success';
      case 'running': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'danger';
      default: return 'secondary';
    }
  };
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'idle': return '✓';
      case 'running': return '⟳';
      case 'completed': return '✓';
      case 'failed': return '✗';
      default: return '?';
    }
  };
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };
  
  const renderStatusTab = () => (
    <div className="migration-status-tab">
      <div className="status-overview">
        <h3>Migration Status</h3>
        
        {migrationStatus && (
          <div className="status-grid">
            <div className="status-item">
              <label>Current Version:</label>
              <span className="status-version">{migrationStatus.currentVersion}</span>
            </div>
            
            <div className="status-item">
              <label>Target Version:</label>
              <span className="status-version">{migrationStatus.targetVersion}</span>
            </div>
            
            <div className="status-item">
              <label>Status:</label>
              <span className={`status-badge status-${getStatusColor(migrationStatus.status)}`}>
                {getStatusIcon(migrationStatus.status)} {migrationStatus.status}
              </span>
            </div>
            
            <div className="status-item">
              <label>Auto-Migration:</label>
              <span className={`status-toggle ${migrationStatus.autoMigrate ? 'enabled' : 'disabled'}`}>
                {migrationStatus.autoMigrate ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        )}
        
        {migrationStatus?.lastMigration && (
          <div className="last-migration">
            <h4>Last Migration</h4>
            <div className="migration-details">
              <p>
                <strong>Version:</strong> {migrationStatus.lastMigration.fromVersion} → {migrationStatus.lastMigration.toVersion}
              </p>
              <p>
                <strong>Date:</strong> {new Date(migrationStatus.lastMigration.timestamp).toLocaleString()}
              </p>
              <p>
                <strong>Steps:</strong> {migrationStatus.lastMigration.steps}
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="migration-actions">
        <h3>Actions</h3>
        
        <div className="action-buttons">
          {migrationStatus && migrationStatus.currentVersion !== migrationStatus.targetVersion && (
            <button
              onClick={handleForceMigration}
              disabled={isLoading || migrationStatus.status === 'running'}
              className="btn btn-primary"
            >
              <span className="btn-icon">⬆</span>
              Force Migration
            </button>
          )}
          
          <button
            onClick={handleCreateBackup}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            <span className="btn-icon">💾</span>
            Create Backup
          </button>
          
          <button
            onClick={handleToggleAutoMigrate}
            disabled={isLoading}
            className={`btn ${migrationStatus?.autoMigrate ? 'btn-warning' : 'btn-success'}`}
          >
            <span className="btn-icon">{migrationStatus?.autoMigrate ? '⏸' : '▶'}</span>
            {migrationStatus?.autoMigrate ? 'Disable' : 'Enable'} Auto-Migration
          </button>
          
          <button
            onClick={loadMigrationData}
            disabled={isLoading}
            className="btn btn-outline"
          >
            <span className="btn-icon">🔄</span>
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
  
  const renderHistoryTab = () => (
    <div className="migration-history-tab">
      <h3>Migration History</h3>
      
      {migrationHistory.length === 0 ? (
        <div className="empty-state">
          <p>No migration history available.</p>
        </div>
      ) : (
        <div className="history-list">
          {migrationHistory.map((entry, index) => (
            <div key={index} className={`history-item ${entry.status}`}>
              <div className="history-header">
                <span className="history-version">
                  {entry.fromVersion} → {entry.toVersion}
                </span>
                <span className={`history-status status-${entry.status}`}>
                  {getStatusIcon(entry.status)} {entry.status}
                </span>
              </div>
              
              <div className="history-details">
                <p className="history-timestamp">
                  {new Date(entry.timestamp).toLocaleString()}
                </p>
                {entry.error && (
                  <p className="history-error">Error: {entry.error}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
  
  const renderBackupsTab = () => (
    <div className="migration-backups-tab">
      <h3>Available Backups</h3>
      
      {availableBackups.length === 0 ? (
        <div className="empty-state">
          <p>No backups available.</p>
          <button
            onClick={handleCreateBackup}
            disabled={isLoading}
            className="btn btn-primary"
          >
            Create First Backup
          </button>
        </div>
      ) : (
        <div className="backups-list">
          {availableBackups.map((backup, index) => (
            <div key={backup.key} className="backup-item">
              <div className="backup-header">
                <span className="backup-version">Version {backup.version}</span>
                <span className="backup-size">{formatFileSize(backup.size)}</span>
              </div>
              
              <div className="backup-details">
                <p className="backup-timestamp">
                  Created: {new Date(backup.timestamp).toLocaleString()}
                </p>
                {backup.created && (
                  <p className="backup-created">
                    {new Date(backup.created).toLocaleString()}
                  </p>
                )}
              </div>
              
              <div className="backup-actions">
                <button
                  onClick={() => handleRestoreBackup(backup)}
                  disabled={isLoading}
                  className="btn btn-sm btn-primary"
                >
                  Restore
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
  
  const renderConfirmDialog = () => {
    if (!confirmDialog) return null;
    
    return (
      <div className="confirm-overlay">
        <div className="confirm-dialog">
          <h3>{confirmDialog.title}</h3>
          <p>{confirmDialog.message}</p>
          
          <div className="confirm-actions">
            <button
              onClick={confirmDialog.onCancel}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={confirmDialog.onConfirm}
              className="btn btn-danger"
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="settings-migration-manager">
      <div className="migration-header">
        <h2>Settings Migration Manager</h2>
        <button onClick={onClose} className="close-btn" aria-label="Close">
          ✕
        </button>
      </div>
      
      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠</span>
          {error}
          <button onClick={() => setError(null)} className="alert-close">✕</button>
        </div>
      )}
      
      {success && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          {success}
          <button onClick={() => setSuccess(null)} className="alert-close">✕</button>
        </div>
      )}
      
      <div className="migration-tabs">
        <button
          onClick={() => setActiveTab('status')}
          className={`tab-btn ${activeTab === 'status' ? 'active' : ''}`}
        >
          Status
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
        >
          History ({migrationHistory.length})
        </button>
        <button
          onClick={() => setActiveTab('backups')}
          className={`tab-btn ${activeTab === 'backups' ? 'active' : ''}`}
        >
          Backups ({availableBackups.length})
        </button>
      </div>
      
      <div className="migration-content">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Processing migration...</p>
          </div>
        )}
        
        {activeTab === 'status' && renderStatusTab()}
        {activeTab === 'history' && renderHistoryTab()}
        {activeTab === 'backups' && renderBackupsTab()}
      </div>
      
      {renderConfirmDialog()}
    </div>
  );
};

export default SettingsMigrationManager;