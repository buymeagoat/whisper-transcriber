/**
 * T029 Enhanced User Experience: Status Dashboard Component
 * Comprehensive status overview with real-time updates and mobile optimization
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, Server, Clock, Users, Zap, AlertTriangle,
  CheckCircle, XCircle, Pause, RefreshCw, TrendingUp,
  Database, Wifi, WifiOff, Cpu, MemoryStick, HardDrive
} from 'lucide-react';
import enhancedStatusService from '../services/enhancedStatusService.js';
import EnhancedProgressBar from './EnhancedProgressBar.jsx';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const StatusDashboard = ({ 
  jobIds = [],
  showSystemStatus = true,
  showActiveJobs = true,
  showQueue = true,
  autoRefresh = true,
  className = ''
}) => {
  const [systemStatus, setSystemStatus] = useState(enhancedStatusService.getSystemStatus());
  const [activeJobs, setActiveJobs] = useState(new Map());
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [statusSummary, setStatusSummary] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const refreshIntervalRef = useRef(null);

  useEffect(() => {
    // Get initial status
    updateStatusSummary();

    // Subscribe to system status updates
    const unsubscribeSystem = enhancedStatusService.subscribe('system', (status) => {
      if (status.type === 'connection') {
        setConnectionStatus(status.status);
      } else {
        setSystemStatus(status);
      }
      updateStatusSummary();
    });

    // Subscribe to job updates
    const unsubscribeJobs = enhancedStatusService.subscribe('jobs', () => {
      setActiveJobs(new Map(enhancedStatusService.getActiveJobs()));
      updateStatusSummary();
    });

    // Subscribe to queue updates
    const unsubscribeQueue = enhancedStatusService.subscribe('queue', () => {
      updateStatusSummary();
    });

    // Setup auto-refresh if enabled
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(() => {
        refreshStatus();
      }, 30000); // Refresh every 30 seconds
    }

    return () => {
      unsubscribeSystem();
      unsubscribeJobs();
      unsubscribeQueue();
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh]);

  const updateStatusSummary = () => {
    const summary = enhancedStatusService.getStatusSummary();
    setStatusSummary(summary);
    setActiveJobs(new Map(summary.activeJobs.map(job => [job.jobId || Date.now(), job])));
    setLastRefresh(new Date());
  };

  const refreshStatus = async () => {
    setIsRefreshing(true);
    try {
      await enhancedStatusService.fetchSystemStatus();
      await enhancedStatusService.fetchActiveJobStatuses();
      updateStatusSummary();
      mobileInterfaceService.hapticFeedback('light');
    } catch (error) {
      console.error('Error refreshing status:', error);
      mobileInterfaceService.hapticFeedback('error');
    } finally {
      setIsRefreshing(false);
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'unhealthy':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          System Status
        </h2>
        
        <div className="flex items-center space-x-3">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {connectionStatus === 'connected' ? (
              <Wifi className="w-5 h-5 text-green-600 dark:text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-600 dark:text-red-400" />
            )}
            <span className={`text-sm font-medium ${
              connectionStatus === 'connected' 
                ? 'text-green-600 dark:text-green-400' 
                : 'text-red-600 dark:text-red-400'
            }`}>
              {connectionStatus === 'connected' ? 'Live' : 'Offline'}
            </span>
          </div>
          
          {/* Refresh Button */}
          <button
            onClick={refreshStatus}
            disabled={isRefreshing}
            className={`
              p-2 rounded-lg transition-colors
              ${isRefreshing 
                ? 'text-gray-400 cursor-not-allowed' 
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800'
              }
            `}
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      {showSystemStatus && systemStatus && (
        <div className={`grid gap-4 ${isMobileBreakpoint ? 'grid-cols-1' : 'grid-cols-2 lg:grid-cols-4'}`}>
          {/* Health Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Health</p>
                <p className={`text-lg font-semibold ${getHealthColor(systemStatus.health)}`}>
                  {systemStatus.health?.charAt(0).toUpperCase() + systemStatus.health?.slice(1)}
                </p>
              </div>
              {getHealthIcon(systemStatus.health)}
            </div>
          </div>

          {/* Active Jobs */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Jobs</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {systemStatus.activeJobs || 0}
                </p>
              </div>
              <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>

          {/* Queue Size */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Queue</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {systemStatus.queueSize || 0}
                </p>
              </div>
              <Users className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
          </div>

          {/* System Load */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Load</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {Math.round((systemStatus.load || 0) * 100)}%
                </p>
              </div>
              <Cpu className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      )}

      {/* Detailed System Metrics */}
      {showSystemStatus && !isMobileBreakpoint && systemStatus && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Metrics
          </h3>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemStatus.totalProcessed || 0}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Total Processed</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemStatus.averageProcessingTime ? 
                  enhancedStatusService.formatDuration(systemStatus.averageProcessingTime) : 
                  'N/A'
                }
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Avg Processing Time</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemStatus.uptime ? formatUptime(systemStatus.uptime) : 'N/A'}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Uptime</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemStatus.memoryUsage ? formatBytes(systemStatus.memoryUsage) : 'N/A'}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Memory Usage</div>
            </div>
          </div>
        </div>
      )}

      {/* Active Jobs */}
      {showActiveJobs && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Active Jobs ({activeJobs.size})
          </h3>
          
          {activeJobs.size === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
              <Pause className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">No active jobs</p>
            </div>
          ) : (
            <div className="space-y-4">
              {Array.from(activeJobs.values()).map((job, index) => (
                <EnhancedProgressBar
                  key={job.jobId || index}
                  jobId={job.jobId}
                  showDetails={!isMobileBreakpoint}
                  showQueue={showQueue}
                  showETA={true}
                  compact={isMobileBreakpoint}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Specific Job IDs */}
      {jobIds.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Tracked Jobs
          </h3>
          
          <div className="space-y-4">
            {jobIds.map(jobId => (
              <EnhancedProgressBar
                key={jobId}
                jobId={jobId}
                showDetails={!isMobileBreakpoint}
                showQueue={showQueue}
                showETA={true}
                compact={isMobileBreakpoint}
              />
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Last updated: {lastRefresh.toLocaleTimeString()}
        {autoRefresh && (
          <span className="ml-2">• Auto-refresh enabled</span>
        )}
      </div>
    </div>
  );
};

export default StatusDashboard;