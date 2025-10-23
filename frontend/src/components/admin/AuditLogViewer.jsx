import React, { useState, useEffect, useCallback } from 'react'
import { auditService } from '../../services/auditService'

// Event type mapping for display
const EVENT_TYPE_LABELS = {
  auth_success: 'Auth Success',
  auth_failure: 'Auth Failure',
  auth_logout: 'Logout',
  password_change: 'Password Change',
  rate_limit_violation: 'Rate Limit',
  suspicious_input: 'Suspicious Input',
  suspicious_header: 'Suspicious Header',
  file_upload: 'File Upload',
  file_download: 'File Download',
  api_access: 'API Access',
  admin_action: 'Admin Action',
  data_export: 'Data Export',
  system_access: 'System Access',
  security_violation: 'Security Violation'
}

// Severity level colors
const SEVERITY_COLORS = {
  low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
}

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedLog, setSelectedLog] = useState(null)
  const [filters, setFilters] = useState({
    event_type: '',
    severity: '',
    user_id: '',
    client_ip: '',
    hours: 24
  })
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    hasMore: true
  })

  // Load audit logs
  const loadAuditLogs = useCallback(async (resetPagination = false) => {
    try {
      setLoading(true)
      setError(null)

      const newOffset = resetPagination ? 0 : pagination.offset
      const params = {
        ...filters,
        limit: pagination.limit,
        offset: newOffset
      }

      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })

      const response = await auditService.getAuditLogs(params)
      
      if (resetPagination) {
        setLogs(response)
        setPagination(prev => ({ ...prev, offset: 0, hasMore: response.length === pagination.limit }))
      } else {
        setLogs(prev => [...prev, ...response])
        setPagination(prev => ({ 
          ...prev, 
          offset: prev.offset + response.length,
          hasMore: response.length === pagination.limit
        }))
      }
    } catch (err) {
      setError(`Failed to load audit logs: ${err.message}`)
      console.error('Audit logs error:', err)
    } finally {
      setLoading(false)
    }
  }, [filters, pagination.limit, pagination.offset])

  // Load more logs
  const loadMore = () => {
    if (!loading && pagination.hasMore) {
      loadAuditLogs(false)
    }
  }

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, offset: 0 }))
  }

  // Apply filters
  const applyFilters = () => {
    loadAuditLogs(true)
  }

  // Clear filters
  const clearFilters = () => {
    setFilters({
      event_type: '',
      severity: '',
      user_id: '',
      client_ip: '',
      hours: 24
    })
    setPagination({ limit: 50, offset: 0, hasMore: true })
  }

  // Load initial data
  useEffect(() => {
    loadAuditLogs(true)
  }, [])

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // Get risk score color
  const getRiskScoreColor = (score) => {
    if (!score) return 'text-gray-500'
    if (score >= 80) return 'text-red-600 font-bold'
    if (score >= 60) return 'text-orange-600 font-semibold'
    if (score >= 40) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Audit Log Viewer
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Monitor security events and system access logs
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => loadAuditLogs(true)}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Filter Audit Logs
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-4">
          {/* Event Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Event Type
            </label>
            <select
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Types</option>
              {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>

          {/* Severity Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Severity
            </label>
            <select
              value={filters.severity}
              onChange={(e) => handleFilterChange('severity', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* User ID Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              User ID
            </label>
            <input
              type="text"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              placeholder="Enter user ID"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            />
          </div>

          {/* Client IP Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Client IP
            </label>
            <input
              type="text"
              value={filters.client_ip}
              onChange={(e) => handleFilterChange('client_ip', e.target.value)}
              placeholder="Enter IP address"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            />
          </div>

          {/* Time Range Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Time Range (hours)
            </label>
            <select
              value={filters.hours}
              onChange={(e) => handleFilterChange('hours', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value={1}>Last 1 hour</option>
              <option value={6}>Last 6 hours</option>
              <option value={24}>Last 24 hours</option>
              <option value={72}>Last 3 days</option>
              <option value={168}>Last 7 days</option>
            </select>
          </div>

          {/* Filter Actions */}
          <div className="flex flex-col justify-end space-y-2">
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
            >
              Apply Filters
            </button>
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm"
            >
              Clear All
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400 dark:text-red-300" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Audit Logs ({logs.length} entries)
          </h3>
        </div>

        {loading && logs.length === 0 ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading audit logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">No audit logs found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Event Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Client IP
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {logs.map((log) => (
                  <tr 
                    key={log.id} 
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${log.blocked ? 'bg-red-50 dark:bg-red-900/20' : ''}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                        {EVENT_TYPE_LABELS[log.event_type] || log.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${SEVERITY_COLORS[log.severity] || 'bg-gray-100 text-gray-800'}`}>
                        {log.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {log.user_id || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-mono">
                      {log.client_ip || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white max-w-xs truncate">
                      {log.event_description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={getRiskScoreColor(log.risk_score)}>
                        {log.risk_score || '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                      >
                        View Details
                      </button>
                      {log.blocked && (
                        <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                          BLOCKED
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Load More Button */}
        {logs.length > 0 && pagination.hasMore && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 text-center">
            <button
              onClick={loadMore}
              disabled={loading}
              className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          </div>
        )}
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={() => setSelectedLog(null)}
            ></div>

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
                      Audit Log Details
                    </h3>
                    
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">ID</label>
                        <p className="text-sm text-gray-900 dark:text-white">{selectedLog.id}</p>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Timestamp</label>
                        <p className="text-sm text-gray-900 dark:text-white">{formatTimestamp(selectedLog.timestamp)}</p>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Event Type</label>
                        <p className="text-sm text-gray-900 dark:text-white">{EVENT_TYPE_LABELS[selectedLog.event_type] || selectedLog.event_type}</p>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Severity</label>
                        <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${SEVERITY_COLORS[selectedLog.severity]}`}>
                          {selectedLog.severity.toUpperCase()}
                        </span>
                      </div>
                      
                      {selectedLog.user_id && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">User ID</label>
                          <p className="text-sm text-gray-900 dark:text-white">{selectedLog.user_id}</p>
                        </div>
                      )}
                      
                      {selectedLog.client_ip && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Client IP</label>
                          <p className="text-sm text-gray-900 dark:text-white font-mono">{selectedLog.client_ip}</p>
                        </div>
                      )}
                      
                      {selectedLog.request_method && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Request Method</label>
                          <p className="text-sm text-gray-900 dark:text-white">{selectedLog.request_method}</p>
                        </div>
                      )}
                      
                      {selectedLog.request_url && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Request URL</label>
                          <p className="text-sm text-gray-900 dark:text-white break-all">{selectedLog.request_url}</p>
                        </div>
                      )}
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
                        <p className="text-sm text-gray-900 dark:text-white">{selectedLog.event_description}</p>
                      </div>
                      
                      {selectedLog.risk_score !== null && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Risk Score</label>
                          <p className={`text-sm ${getRiskScoreColor(selectedLog.risk_score)}`}>{selectedLog.risk_score}</p>
                        </div>
                      )}
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Blocked</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {selectedLog.blocked ? (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                              YES
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                              NO
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setSelectedLog(null)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AuditLogViewer