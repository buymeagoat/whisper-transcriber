import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';

/**
 * BackupManagement - Comprehensive backup management interface for administrators
 * Provides backup creation, status monitoring, and restore functionality
 */
const BackupManagement = () => {
  const [backupStatus, setBackupStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createBackupLoading, setCreateBackupLoading] = useState(false);
  const [backupType, setBackupType] = useState('incremental');
  const [uploadToStorage, setUploadToStorage] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchBackupStatus();
    // Refresh every 30 seconds to show real-time updates
    const interval = setInterval(fetchBackupStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchBackupStatus = async () => {
    try {
      setError(null);
      const status = await adminService.getBackupStatus();
      setBackupStatus(status);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch backup status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    setCreateBackupLoading(true);
    setError(null);
    
    try {
      const result = await adminService.createBackup(backupType, uploadToStorage);
      // Refresh status after creating backup
      await fetchBackupStatus();
      alert(`Backup created successfully! ${result.message || ''}`);
    } catch (err) {
      console.error('Failed to create backup:', err);
      setError(err.message);
    } finally {
      setCreateBackupLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'successful':
      case 'healthy':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
      case 'running':
      case 'in-progress':
        return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400';
      case 'failed':
      case 'error':
        return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const StatCard = ({ title, value, subtitle, icon, status }) => (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</h3>
        <span className="text-xl">{icon}</span>
      </div>
      <div className="flex items-center space-x-2">
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        {status && (
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
            {status}
          </span>
        )}
      </div>
      {subtitle && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
      )}
    </div>
  );

  if (loading && !backupStatus) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading backup status...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !backupStatus) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
          <h3 className="text-red-800 dark:text-red-200 font-medium mb-2">
            ⚠️ Failed to Load Backup Status
          </h3>
          <p className="text-red-700 dark:text-red-300 text-sm mb-4">{error}</p>
          <button
            onClick={fetchBackupStatus}
            className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const stats = backupStatus?.backup_system?.orchestrator?.statistics || {};
  const dbStats = backupStatus?.backup_system?.database || {};
  const fileStats = backupStatus?.backup_system?.files || {};

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Backup Management
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Monitor and manage system backups
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchBackupStatus}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-6">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Create Backup Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Create New Backup
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Backup Type
            </label>
            <select
              value={backupType}
              onChange={(e) => setBackupType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value="incremental">Incremental Backup</option>
              <option value="full">Full Backup</option>
            </select>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="uploadToStorage"
              checked={uploadToStorage}
              onChange={(e) => setUploadToStorage(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="uploadToStorage" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Upload to storage
            </label>
          </div>
          <div>
            <button
              onClick={handleCreateBackup}
              disabled={createBackupLoading}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {createBackupLoading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Creating...
                </span>
              ) : (
                '📦 Create Backup'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Backup Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Backups"
          value={stats.total_backups || 0}
          subtitle={`${stats.successful_backups || 0} successful, ${stats.failed_backups || 0} failed`}
          icon="📊"
        />
        <StatCard
          title="Database Backups"
          value={dbStats.total_backups || 0}
          subtitle={`${formatFileSize(dbStats.total_backup_size || 0)}`}
          icon="🗄️"
        />
        <StatCard
          title="Files Tracked"
          value={fileStats.total_files_tracked || 0}
          subtitle={`${formatFileSize(fileStats.total_backup_size || 0)} backed up`}
          icon="📁"
        />
        <StatCard
          title="Storage Efficiency"
          value={fileStats.storage_efficiency ? `${(fileStats.storage_efficiency * 100).toFixed(1)}%` : 'N/A'}
          subtitle="Compression ratio"
          icon="📈"
        />
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Service Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <span className="mr-2">🔧</span>
            Service Status
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Backup Service</span>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${backupStatus?.service_running ? getStatusColor('healthy') : getStatusColor('error')}`}>
                {backupStatus?.service_running ? 'Running' : 'Stopped'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Real-time Monitoring</span>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${fileStats.realtime_monitoring_enabled ? getStatusColor('healthy') : getStatusColor('error')}`}>
                {fileStats.realtime_monitoring_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Compression</span>
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${backupStatus?.backup_system?.compression?.zstd_available ? getStatusColor('healthy') : getStatusColor('error')}`}>
                {backupStatus?.backup_system?.compression?.compression_method?.toUpperCase() || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <span className="mr-2">📋</span>
            Recent Activity
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Last Full Backup</span>
              <span className="text-sm font-mono text-gray-900 dark:text-white">
                {formatDate(stats.last_full_backup)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Last Incremental</span>
              <span className="text-sm font-mono text-gray-900 dark:text-white">
                {formatDate(stats.last_incremental_backup)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Total Data Backed Up</span>
              <span className="text-sm font-mono text-gray-900 dark:text-white">
                {formatFileSize(stats.total_size_backed_up || 0)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Current Operations */}
      {backupStatus?.backup_system?.current_operations && Object.keys(backupStatus.backup_system.current_operations).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <span className="mr-2">⚡</span>
            Recent Operations ({Object.keys(backupStatus.backup_system.current_operations).length})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">Operation</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">Type</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">Started</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">Progress</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(backupStatus.backup_system.current_operations)
                  .slice(0, 10) // Show last 10 operations
                  .map(([operationId, operation]) => (
                  <tr key={operationId} className="border-b border-gray-100 dark:border-gray-700/50">
                    <td className="py-2 font-mono text-xs text-gray-900 dark:text-white">
                      {operationId.replace(/^(incremental_backup_|full_backup_)/, '')}
                    </td>
                    <td className="py-2 text-gray-600 dark:text-gray-400">
                      {operation.type?.replace('_', ' ')}
                    </td>
                    <td className="py-2 text-gray-600 dark:text-gray-400">
                      {formatDate(operation.started)}
                    </td>
                    <td className="py-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                          <div 
                            className="bg-indigo-600 h-2 rounded-full transition-all" 
                            style={{ width: `${operation.progress || 0}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {operation.progress || 0}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(operation.status)}`}>
                        {operation.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default BackupManagement;
