import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';

/**
 * SystemHealth - Real-time system health monitoring component
 * Displays server status, database connectivity, queue health, and resource usage
 */
const SystemHealth = () => {
  const [healthData, setHealthData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchHealthData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [health, stats] = await Promise.all([
        adminService.getHealth(),
        adminService.getStats()
      ]);
      
      setHealthData(health);
      setStatsData(stats);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch health data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'ok':
        return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'error':
      case 'db_error':
        return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  const StatusCard = ({ title, status, details, icon }) => (
    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-900 dark:text-white flex items-center space-x-2">
          <span>{icon}</span>
          <span>{title}</span>
        </h3>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(status)}`}>
          {status}
        </span>
      </div>
      {details && (
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          {typeof details === 'object' ? (
            Object.entries(details).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-mono">{String(value)}</span>
              </div>
            ))
          ) : (
            <p>{details}</p>
          )}
        </div>
      )}
    </div>
  );

  const StatCard = ({ title, value, subtitle, icon, trend }) => (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-500">{subtitle}</p>
          )}
        </div>
        <div className="text-2xl">{icon}</div>
      </div>
      {trend && (
        <div className="mt-2 flex items-center text-xs">
          <span className={trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-500'}>
            {trend > 0 ? '↗' : trend < 0 ? '↘' : '→'} {Math.abs(trend)}%
          </span>
        </div>
      )}
    </div>
  );

  if (loading && !healthData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading system health...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4">
          <h3 className="text-red-800 dark:text-red-200 font-medium mb-2">
            ⚠️ Failed to Load System Health
          </h3>
          <p className="text-red-700 dark:text-red-300 text-sm mb-4">{error}</p>
          <button
            onClick={fetchHealthData}
            className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          System Health Monitor
        </h2>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchHealthData}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      {statsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Jobs"
            value={statsData.job_queue?.total_jobs || '0'}
            subtitle="All time"
            icon="📊"
          />
          <StatCard
            title="Active Jobs"
            value={statsData.job_queue?.active_jobs || '0'}
            subtitle="Currently running"
            icon="🔄"
          />
          <StatCard
            title="App Version"
            value={statsData.settings?.version || 'Unknown'}
            subtitle={statsData.settings?.app_name || 'Whisper Transcriber'}
            icon="🏷️"
          />
          <StatCard
            title="Debug Mode"
            value={statsData.settings?.debug ? 'ON' : 'OFF'}
            subtitle={statsData.settings?.default_model || 'Default model'}
            icon="🔧"
          />
        </div>
      )}

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <StatusCard
          title="API Server"
          status={healthData?.status || 'unknown'}
          details={{
            service: healthData?.service || 'whisper-transcriber',
            version: healthData?.version || 'Unknown'
          }}
          icon="🖥️"
        />
        
        <StatusCard
          title="Database"
          status={statsData?.database ? 'healthy' : 'unknown'}
          details={statsData?.database || 'No database info available'}
          icon="🗄️"
        />
        
        {statsData?.job_queue && (
          <StatusCard
            title="Job Queue"
            status={statsData.job_queue.total_jobs >= 0 ? 'healthy' : 'warning'}
            details={{
              total_jobs: statsData.job_queue.total_jobs,
              active_jobs: statsData.job_queue.active_jobs,
              queue_status: statsData.job_queue.active_jobs > 0 ? 'Processing' : 'Idle'
            }}
            icon="📋"
          />
        )}
        
        {statsData?.app_state && (
          <StatusCard
            title="Application State"
            status="healthy"
            details={statsData.app_state}
            icon="⚙️"
          />
        )}
      </div>

      {/* System Information */}
      {statsData?.settings && (
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
            <span>📋</span>
            <span>System Configuration</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {Object.entries(statsData.settings).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center py-1">
                <span className="text-gray-600 dark:text-gray-400 capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="font-mono text-gray-900 dark:text-white">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemHealth;
