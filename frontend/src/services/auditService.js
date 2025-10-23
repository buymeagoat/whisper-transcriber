import axios from 'axios'

const API_URL = '/api/admin/security'

class AuditService {
  async getAuditLogs(params = {}) {
    try {
      const response = await axios.get(`${API_URL}/audit-logs`, {
        params,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching audit logs:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch audit logs')
    }
  }

  async getAuditLogById(id) {
    try {
      const response = await axios.get(`${API_URL}/audit-logs/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching audit log:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      if (error.response?.status === 404) {
        throw new Error('Audit log not found')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch audit log')
    }
  }

  async getSecurityDashboard(hours = 24) {
    try {
      const response = await axios.get(`${API_URL}/dashboard`, {
        params: { hours },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching security dashboard:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch security dashboard')
    }
  }

  async getSecurityIncidents(params = {}) {
    try {
      const response = await axios.get(`${API_URL}/incidents`, {
        params,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching security incidents:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch security incidents')
    }
  }

  async createSecurityIncident(incidentData) {
    try {
      const response = await axios.post(`${API_URL}/incidents`, incidentData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error creating security incident:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to create security incident')
    }
  }

  async updateSecurityIncident(id, updateData) {
    try {
      const response = await axios.put(`${API_URL}/incidents/${id}`, updateData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error updating security incident:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      if (error.response?.status === 404) {
        throw new Error('Security incident not found')
      }
      throw new Error(error.response?.data?.detail || 'Failed to update security incident')
    }
  }

  async getAPIKeys() {
    try {
      const response = await axios.get(`${API_URL}/api-keys`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching API keys:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch API keys')
    }
  }

  async createAPIKey(keyData) {
    try {
      const response = await axios.post(`${API_URL}/api-keys`, keyData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error creating API key:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to create API key')
    }
  }

  async revokeAPIKey(keyId) {
    try {
      const response = await axios.delete(`${API_URL}/api-keys/${keyId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error revoking API key:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      if (error.response?.status === 404) {
        throw new Error('API key not found')
      }
      throw new Error(error.response?.data?.detail || 'Failed to revoke API key')
    }
  }

  async getAuditStatistics(hours = 24) {
    try {
      const response = await axios.get(`${API_URL}/audit-stats`, {
        params: { hours },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching audit statistics:', error)
      if (error.response?.status === 401) {
        throw new Error('Unauthorized access')
      }
      throw new Error(error.response?.data?.detail || 'Failed to fetch audit statistics')
    }
  }

  // Helper method to format event types for display
  getEventTypeLabel(eventType) {
    const labels = {
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
    return labels[eventType] || eventType
  }

  // Helper method to get severity color class
  getSeverityColorClass(severity) {
    const colors = {
      low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    }
    return colors[severity] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
  }

  // Helper method to format risk score for display
  formatRiskScore(score) {
    if (!score) return '-'
    if (score >= 80) return { value: score, level: 'Critical', color: 'text-red-600 font-bold' }
    if (score >= 60) return { value: score, level: 'High', color: 'text-orange-600 font-semibold' }
    if (score >= 40) return { value: score, level: 'Medium', color: 'text-yellow-600' }
    return { value: score, level: 'Low', color: 'text-green-600' }
  }
}

export const auditService = new AuditService()
export default auditService