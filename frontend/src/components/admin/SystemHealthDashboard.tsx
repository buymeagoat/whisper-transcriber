import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import SystemMetrics from './SystemMetrics';
import ServiceStatus from './ServiceStatus';
import SystemLogs from './SystemLogs';

interface SystemHealthDashboardProps {
  className?: string;
}

const SystemHealthDashboard: React.FC<SystemHealthDashboardProps> = ({ className = '' }) => {
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);
  const [systemLogs, setSystemLogs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch system metrics
      const metricsResponse = await fetch('/api/admin/health/system', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      // Fetch service status
      const servicesResponse = await fetch('/api/admin/health/services', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      // Fetch system logs
      const logsResponse = await fetch('/api/admin/health/logs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setSystemMetrics(metricsData);
      }

      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json();
        setServiceStatus(servicesData);
      }

      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setSystemLogs(logsData);
      }

    } catch (err) {
      console.error('Failed to fetch health data:', err);
      setError('Failed to load system health data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    // Set up periodic refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    fetchHealthData();
  };

  const handleLogSearch = (query: string) => {
    // Implement log search functionality
    console.log('Searching logs for:', query);
  };

  const handleLogExport = () => {
    // Implement log export functionality
    console.log('Exporting logs...');
  };

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="text-center py-8">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Health Data</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">System Health Dashboard</h2>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SystemMetrics metrics={systemMetrics} loading={loading} />
        <ServiceStatus data={serviceStatus} loading={loading} />
      </div>

      {/* System Logs */}
      <div className="w-full">
        <SystemLogs 
          data={systemLogs} 
          loading={loading}
          onRefresh={handleRefresh}
          onSearch={handleLogSearch}
          onExport={handleLogExport}
        />
      </div>
    </div>
  );
};

export default SystemHealthDashboard;
