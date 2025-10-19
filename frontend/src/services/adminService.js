import apiClient from './apiClient'

export const adminService = {
  async getStats() {
    try {
      const response = await apiClient.get('/admin/stats')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch stats')
    }
  },

  async getAuditEvents(params = {}) {
    try {
      const response = await apiClient.get('/admin/events', { params })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch audit events')
    }
  },

  async getAuditSummary() {
    try {
      const response = await apiClient.get('/admin/summary')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch audit summary')
    }
  },

  async getBackupStatus() {
    try {
      const response = await apiClient.get('/admin/backup/status')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch backup status')
    }
  },

  async createBackup(backupType = 'full', uploadToStorage = true) {
    try {
      const response = await apiClient.post('/admin/backup/create', {
        backup_type: backupType,
        upload_to_storage: uploadToStorage,
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create backup')
    }
  },

  async listUsers() {
    try {
      const response = await apiClient.get('/users/')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch users')
    }
  },

  async triggerCleanup() {
    try {
      const response = await apiClient.post('/admin/cleanup')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to trigger cleanup')
    }
  },

  async getCacheStats() {
    try {
      const response = await apiClient.get('/admin/stats')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch cache stats')
    }
  },

  async clearCache(pattern = '*') {
    try {
      const response = await apiClient.post('/admin/clear', null, {
        params: { pattern }
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to clear cache')
    }
  },
}
