import apiClient from './apiClient'

export const jobsService = {
  async listJobs(skip = 0, limit = 100) {
    try {
      const response = await apiClient.get('/jobs/', {
        params: { skip, limit }
      })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch jobs')
    }
  },

  async getJob(jobId) {
    try {
      const response = await apiClient.get(`/jobs/${jobId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch job')
    }
  },

  async createJob(file, model = 'small', language = null) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('model', model)
      if (language) {
        formData.append('language', language)
      }

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

  async deleteJob(jobId) {
    try {
      const response = await apiClient.delete(`/jobs/${jobId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete job')
    }
  },

  async getJobProgress(jobId) {
    try {
      const response = await apiClient.get(`/progress/${jobId}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get job progress')
    }
  },
}
