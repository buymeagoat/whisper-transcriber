import React, { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { BarChart3, FileText, Clock, TrendingUp } from 'lucide-react'
import StatisticsCard from '../../components/StatisticsCard'
import JobList from '../../components/JobList'
import { jobService } from '../../services/jobService'
import { statsService } from '../../services/statsService'

const Dashboard = () => {
  const { user } = useAuth()
  const [jobs, setJobs] = useState([])
  const [stats, setStats] = useState({
    totalJobs: 0,
    completedJobs: 0,
    processingJobs: 0,
    thisMonth: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch jobs and stats
      const [jobsData, userStats] = await Promise.all([
        jobService.getJobs(0, 20), // Get first 20 jobs for recent activity
        statsService.getUserStats()
      ])
      
      setJobs(jobsData.jobs || [])
      setStats(userStats)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      // Only poll if there are processing jobs
      if (stats.processingJobs > 0) {
        fetchDashboardData()
      }
    }, 5000) // Poll every 5 seconds
    
    return () => clearInterval(interval)
  }, [stats.processingJobs])

  const handleJobAction = (action, jobId) => {
    // Refresh data after job actions
    if (action === 'delete') {
      setJobs(prevJobs => prevJobs.filter(job => job.job_id !== jobId))
      // Also refresh stats since job count changed
      statsService.getUserStats().then(setStats).catch(console.error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.username || user?.email}!
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Here's what's happening with your transcriptions today.
        </p>
        {error && (
          <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-red-600 dark:text-red-400 text-sm">
              {error}
            </p>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatisticsCard
          title="Total Jobs"
          value={stats.totalJobs}
          icon={FileText}
          color="blue"
          loading={loading}
        />
        
        <StatisticsCard
          title="Completed"
          value={stats.completedJobs}
          icon={Clock}
          color="green"
          loading={loading}
        />
        
        <StatisticsCard
          title="Processing"
          value={stats.processingJobs}
          icon={TrendingUp}
          color="yellow"
          loading={loading}
        />
        
        <StatisticsCard
          title="This Month"
          value={stats.thisMonth}
          icon={BarChart3}
          color="purple"
          loading={loading}
        />
      </div>

      {/* Recent Activity */}
      <JobList
        jobs={jobs}
        loading={loading}
        onJobAction={handleJobAction}
      />
    </div>
  )
}

export default Dashboard
