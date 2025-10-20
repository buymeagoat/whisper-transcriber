import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Database, Server, Activity, Users } from 'lucide-react';

interface ServiceInfo {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  message: string;
  last_check?: string;
  response_time?: number;
}

interface ServiceStatusData {
  services: ServiceInfo[];
  overall_status: 'healthy' | 'warning' | 'error';
  last_updated: string;
}

interface ServiceStatusProps {
  data: ServiceStatusData | null;
  loading?: boolean;
}

const ServiceStatus: React.FC<ServiceStatusProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Status</h3>
        <div className="animate-pulse space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center space-x-3">
              <div className="h-4 w-4 bg-gray-200 rounded-full"></div>
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Status</h3>
        <div className="text-center py-4">
          <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-2" />
          <p className="text-gray-500">Unable to load service status</p>
        </div>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName.toLowerCase()) {
      case 'database':
        return <Database className="h-4 w-4 text-blue-500" />;
      case 'api':
        return <Server className="h-4 w-4 text-green-500" />;
      case 'queue':
        return <Activity className="h-4 w-4 text-purple-500" />;
      case 'worker':
        return <Users className="h-4 w-4 text-orange-500" />;
      default:
        return <Server className="h-4 w-4 text-gray-500" />;
    }
  };

  const getOverallStatusColor = () => {
    switch (data.overall_status) {
      case 'healthy':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getOverallStatusText = () => {
    switch (data.overall_status) {
      case 'healthy':
        return 'All Systems Operational';
      case 'warning':
        return 'Some Issues Detected';
      case 'error':
        return 'Service Disruption';
      default:
        return 'Status Unknown';
    }
  };

  const formatResponseTime = (time?: number): string => {
    if (time === undefined) return 'N/A';
    if (time < 1000) return `${time}ms`;
    return `${(time / 1000).toFixed(2)}s`;
  };

  const formatLastCheck = (timestamp?: string): string => {
    if (!timestamp) return 'Never';
    
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSeconds = Math.floor(diffMs / 1000);
      const diffMinutes = Math.floor(diffSeconds / 60);
      const diffHours = Math.floor(diffMinutes / 60);

      if (diffSeconds < 60) return `${diffSeconds}s ago`;
      if (diffMinutes < 60) return `${diffMinutes}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">Service Status</h3>
      
      {/* Overall Status */}
      <div className={`rounded-lg border-2 p-4 mb-6 ${getOverallStatusColor()}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(data.overall_status)}
            <div>
              <h4 className="font-semibold text-gray-900">{getOverallStatusText()}</h4>
              <p className="text-sm text-gray-600">
                Last updated: {formatLastCheck(data.last_updated)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Services */}
      <div className="space-y-4">
        {data.services.map((service, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors duration-150"
          >
            <div className="flex items-center space-x-3">
              {getServiceIcon(service.name)}
              <div>
                <div className="flex items-center space-x-2">
                  <h5 className="font-medium text-gray-900 capitalize">{service.name}</h5>
                  {getStatusIcon(service.status)}
                </div>
                <p className="text-sm text-gray-600">{service.message}</p>
              </div>
            </div>

            <div className="text-right">
              {service.response_time && (
                <div className="text-sm text-gray-500">
                  {formatResponseTime(service.response_time)}
                </div>
              )}
              <div className="text-xs text-gray-400">
                {formatLastCheck(service.last_check)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Service Count Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Total Services: {data.services.length}</span>
          <div className="space-x-4">
            <span className="text-green-600">
              Healthy: {data.services.filter(s => s.status === 'healthy').length}
            </span>
            <span className="text-yellow-600">
              Warning: {data.services.filter(s => s.status === 'warning').length}
            </span>
            <span className="text-red-600">
              Error: {data.services.filter(s => s.status === 'error').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServiceStatus;
