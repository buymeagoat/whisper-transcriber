import apiClient from './apiClient'

export const jobService = {
  /**
   * Get all jobs for the current user
   */
  async getJobs(skip = 0, limit = 100) {
    try {
      const response = await apiClient.get(`/jobs/?skip=${skip}&limit=${limit}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch jobs')
    }
  },

  /**
   * Get details for a specific job
   */
  async getJob(jobId) {
    try {
      const response = await apiClient.get(`/jobs/${jobId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch job details')
    }
  },

  /**
   * Create a new transcription job
   */
  async createJob(file, options = {}) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      if (options.model) formData.append('model', options.model)
      if (options.language) formData.append('language', options.language)

      const response = await apiClient.post('/jobs/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create job')
    }
  },

  /**
   * Delete a job
   */
  async deleteJob(jobId) {
    try {
      const response = await apiClient.delete(`/jobs/${jobId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete job')
    }
  },

  /**
   * Download transcription results
   */
  async downloadJob(jobId) {
    try {
      const response = await apiClient.get(`/jobs/${jobId}/download`, {
        responseType: 'blob',
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to download results')
    }
  }
}

export default jobService
