import React, { useState, useEffect, useRef } from 'react';
import { Search, Download, RefreshCw, AlertTriangle, Info, AlertCircle, XCircle } from 'lucide-react';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG' | 'CRITICAL';
  message: string;
  source?: string;
}

interface SystemLogsData {
  logs: LogEntry[];
  total_count: number;
  has_more: boolean;
}

interface SystemLogsProps {
  data: SystemLogsData | null;
  loading?: boolean;
  onRefresh?: () => void;
  onSearch?: (query: string) => void;
  onExport?: () => void;
}

const SystemLogs: React.FC<SystemLogsProps> = ({ 
  data, 
  loading, 
  onRefresh, 
  onSearch, 
  onExport 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let interval: number;
    if (autoRefresh && onRefresh) {
      interval = setInterval(onRefresh, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, onRefresh]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (onSearch) {
      onSearch(query);
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'INFO':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'ERROR':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      case 'CRITICAL':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'DEBUG':
        return <Info className="h-4 w-4 text-gray-500" />;
      default:
        return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'INFO':
        return 'text-blue-600 bg-blue-50';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50';
      case 'ERROR':
        return 'text-orange-600 bg-orange-50';
      case 'CRITICAL':
        return 'text-red-600 bg-red-50';
      case 'DEBUG':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const filteredLogs = data?.logs.filter(log => {
    const matchesSearch = searchQuery === '' || 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.source && log.source.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesLevel = selectedLevel === 'all' || log.level === selectedLevel;
    
    return matchesSearch && matchesLevel;
  }) || [];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Logs</h3>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex space-x-3">
              <div className="h-4 w-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">System Logs</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 text-sm rounded-md border transition-colors ${
              autoRefresh 
                ? 'bg-green-100 text-green-700 border-green-300' 
                : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
            }`}
          >
            Auto Refresh
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50"
              title="Refresh logs"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          )}
          {onExport && (
            <button
              onClick={onExport}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              title="Export logs"
            >
              <Download className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <select
          value={selectedLevel}
          onChange={(e) => setSelectedLevel(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Levels</option>
          <option value="DEBUG">Debug</option>
          <option value="INFO">Info</option>
          <option value="WARNING">Warning</option>
          <option value="ERROR">Error</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>

      {/* Log Statistics */}
      {data && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              Showing {filteredLogs.length} of {data.total_count} logs
              {data.has_more && ' (more available)'}
            </span>
            <div className="flex space-x-4">
              {['INFO', 'WARNING', 'ERROR', 'CRITICAL'].map(level => {
                const count = data.logs.filter(log => log.level === level).length;
                if (count === 0) return null;
                return (
                  <span key={level} className={`px-2 py-1 rounded text-xs ${getLevelColor(level)}`}>
                    {level}: {count}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Logs Container */}
      <div 
        ref={logsContainerRef}
        className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {data?.logs.length === 0 ? 'No logs available' : 'No logs match the current filters'}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLogs.map((log, index) => (
              <div key={index} className="p-3 hover:bg-gray-50 transition-colors">
                <div className="flex items-start space-x-3">
                  {getLevelIcon(log.level)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      {log.source && (
                        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                          {log.source}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900 whitespace-pre-wrap break-words">
                      {log.message}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemLogs;
