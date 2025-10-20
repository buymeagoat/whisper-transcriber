import React, { useState } from 'react'
import { Download, Trash2, Eye, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { jobService } from '../services/jobService'

const JobList = ({ jobs, onJobAction, loading = false, showPagination = false }) => {
  const [deletingJobs, setDeletingJobs] = useState(new Set())
  const [downloadingJobs, setDownloadingJobs] = useState(new Set())
  const [filter, setFilter] = useState('all') // all, completed, processing, failed
  const [currentPage, setCurrentPage] = useState(1)
  const [jobsPerPage] = useState(10)

  // Filter jobs based on status
  const filteredJobs = jobs.filter(job => {
    if (filter === 'all') return true
    if (filter === 'completed') return job.status === 'completed'
    if (filter === 'processing') return job.status === 'running' || job.status === 'pending'
    if (filter === 'failed') return job.status === 'failed'
    return true
  })

  // Pagination
  const indexOfLastJob = currentPage * jobsPerPage
  const indexOfFirstJob = indexOfLastJob - jobsPerPage
  const currentJobs = showPagination 
    ? filteredJobs.slice(indexOfFirstJob, indexOfLastJob)
    : filteredJobs
  const totalPages = Math.ceil(filteredJobs.length / jobsPerPage)

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'running':
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-600 animate-spin" />
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      case 'running':
        return 'Processing'
      case 'pending':
        return 'Pending'
      default:
        return 'Unknown'
    }
  }

  const handleDownload = async (jobId, filename) => {
    setDownloadingJobs(prev => new Set([...prev, jobId]))
    try {
      const blob = await jobService.downloadJob(jobId)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || `transcription-${jobId}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
      if (onJobAction) onJobAction('download', jobId)
    } catch (error) {
      console.error('Download failed:', error)
      // Could add toast notification here
    } finally {
      setDownloadingJobs(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job?')) {
      return
    }

    setDeletingJobs(prev => new Set([...prev, jobId]))
    try {
      await jobService.deleteJob(jobId)
      if (onJobAction) onJobAction('delete', jobId)
    } catch (error) {
      console.error('Delete failed:', error)
      // Could add toast notification here
    } finally {
      setDeletingJobs(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown'
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Jobs
        </h2>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="border-b border-gray-200 dark:border-gray-700 pb-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Jobs
        </h2>
        <div className="text-center py-12">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            No transcription jobs yet. Start by uploading your first audio file!
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 sm:mb-0">
          Recent Jobs ({filteredJobs.length})
        </h2>
        
        {jobs.length > 0 && (
          <div className="flex space-x-2">
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value)
                setCurrentPage(1)
              }}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            >
              <option value="all">All Jobs</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        )}
      </div>
      
      <div className="space-y-4">
        {currentJobs.map(job => (
          <div key={job.job_id} className="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-b-0">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {job.original_filename || `Job ${job.job_id}`}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {getStatusText(job.status)} • {formatDate(job.created_at)}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {job.status === 'completed' && (
                  <button
                    onClick={() => handleDownload(job.job_id, job.original_filename)}
                    disabled={downloadingJobs.has(job.job_id)}
                    className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors disabled:opacity-50"
                    title="Download"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
                
                <button
                  onClick={() => handleDelete(job.job_id)}
                  disabled={deletingJobs.has(job.job_id)}
                  className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Showing {indexOfFirstJob + 1} to {Math.min(indexOfLastJob, filteredJobs.length)} of {filteredJobs.length} jobs
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-900 dark:text-white">
              {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default JobList
