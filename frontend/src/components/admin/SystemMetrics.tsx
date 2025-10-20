import React from 'react';
import { Cpu, HardDrive, Monitor, AlertTriangle } from 'lucide-react';

interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  memory_used: number;
  memory_total: number;
  disk_percent: number;
  disk_used: number;
  disk_total: number;
  load_average: number[];
  uptime: number;
}

interface SystemMetricsProps {
  metrics: SystemMetrics | null;
  loading?: boolean;
}

const SystemMetrics: React.FC<SystemMetricsProps> = ({ metrics, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Metrics</h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Metrics</h3>
        <div className="text-center py-4">
          <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-2" />
          <p className="text-gray-500">Unable to load system metrics</p>
        </div>
      </div>
    );
  }

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / (24 * 3600));
    const hours = Math.floor((seconds % (24 * 3600)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getStatusColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTextColor = (percentage: number): string => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  const MetricBar: React.FC<{ percentage: number; label: string; icon: React.ReactNode }> = ({ 
    percentage, 
    label, 
    icon 
  }) => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {icon}
          <span className="text-sm font-medium text-gray-700">{label}</span>
        </div>
        <span className={`text-sm font-semibold ${getTextColor(percentage)}`}>
          {percentage.toFixed(1)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${getStatusColor(percentage)}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">System Metrics</h3>
      
      <div className="space-y-6">
        {/* CPU Usage */}
        <MetricBar
          percentage={metrics.cpu_percent}
          label="CPU Usage"
          icon={<Cpu className="h-4 w-4 text-blue-500" />}
        />

        {/* Memory Usage */}
        <div className="space-y-2">
          <MetricBar
            percentage={metrics.memory_percent}
            label="Memory Usage"
            icon={<Monitor className="h-4 w-4 text-purple-500" />}
          />
          <div className="text-xs text-gray-500 ml-6">
            {formatBytes(metrics.memory_used)} / {formatBytes(metrics.memory_total)}
          </div>
        </div>

        {/* Disk Usage */}
        <div className="space-y-2">
          <MetricBar
            percentage={metrics.disk_percent}
            label="Disk Usage"
            icon={<HardDrive className="h-4 w-4 text-orange-500" />}
          />
          <div className="text-xs text-gray-500 ml-6">
            {formatBytes(metrics.disk_used)} / {formatBytes(metrics.disk_total)}
          </div>
        </div>

        {/* Load Average */}
        <div className="border-t pt-4 mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Load Average</span>
            <div className="text-sm text-gray-600">
              {metrics.load_average.map((load, index) => (
                <span key={index} className="ml-2">
                  {load.toFixed(2)}
                </span>
              ))}
            </div>
          </div>
          <div className="text-xs text-gray-500">1m / 5m / 15m</div>
        </div>

        {/* Uptime */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">System Uptime</span>
            <span className="text-sm text-gray-600">{formatUptime(metrics.uptime)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMetrics;
