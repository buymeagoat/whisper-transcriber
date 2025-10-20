import apiClient from './apiClient'

export const statsService = {
  /**
   * Get system statistics (requires admin access)
   */
  async getSystemStats() {
    try {
      const response = await apiClient.get('/admin/stats')
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch system stats')
    }
  },

  /**
   * Get user dashboard statistics
   */
  async getUserStats() {
    try {
      // For now, we'll compute user stats from jobs data
      // In the future, there might be a dedicated endpoint
      const jobs = await apiClient.get('/jobs/?limit=1000')
      const jobsData = jobs.data.jobs || []

      const stats = {
        totalJobs: jobsData.length,
        completedJobs: jobsData.filter(job => job.status === 'completed').length,
        processingJobs: jobsData.filter(job => job.status === 'running' || job.status === 'pending').length,
        failedJobs: jobsData.filter(job => job.status === 'failed').length,
        thisMonth: this.getThisMonthJobs(jobsData)
      }

      return stats
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch user stats')
    }
  },

  /**
   * Get jobs created this month
   */
  getThisMonthJobs(jobs) {
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()

    return jobs.filter(job => {
      if (!job.created_at) return false
      const jobDate = new Date(job.created_at)
      return jobDate.getMonth() === currentMonth && jobDate.getFullYear() === currentYear
    }).length
  },

  /**
   * Calculate success rate from jobs data
   */
  calculateSuccessRate(jobs) {
    if (!jobs || jobs.length === 0) return 0
    const completed = jobs.filter(job => job.status === 'completed').length
    return Math.round((completed / jobs.length) * 100)
  }
}

export default statsService
