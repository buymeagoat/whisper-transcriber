import React, { useState, useEffect } from 'react'
import { Clock, Download, Trash2, FileText, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const HistoryComponent = ({ onSelectJob }) => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/jobs')
      if (response.ok) {
        const data = await response.json()
        setJobs(data.jobs)
      }
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
      toast.error('Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const deleteJob = async (jobId) => {
    if (!confirm('Are you sure you want to delete this job?')) return
    
    try {
      const response = await fetch(`/api/jobs/${jobId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setJobs(jobs.filter(job => job.job_id !== jobId))
        toast.success('Job deleted')
      }
    } catch (error) {
      toast.error('Failed to delete job')
    }
  }

  const downloadTranscript = async (jobId, filename) => {
    try {
      const response = await fetch(`/api/jobs/${jobId}/download`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `${filename}_transcript.txt`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        toast.success('Download started')
      }
    } catch (error) {
      toast.error('Download failed')
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'processing':
        return <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusBadge = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      processing: 'bg-primary-100 text-primary-800',
      pending: 'bg-yellow-100 text-yellow-800'
    }
    
    return `px-2 py-1 text-xs font-medium rounded-full ${colors[status] || colors.pending}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        <span className="ml-2 text-gray-600">Loading history...</span>
      </div>
    )
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center p-8">
        <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No transcriptions yet</h3>
        <p className="text-gray-500">Upload an audio file to get started!</p>
      </div>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Transcriptions</h2>
      
      <div className="space-y-3">
        {jobs.map((job) => (
          <div
            key={job.job_id}
            className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onSelectJob(job.job_id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                {getStatusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {job.filename}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={getStatusBadge(job.status)}>
                      {job.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {job.model_used}
                    </span>
                    {job.file_size && (
                      <span className="text-xs text-gray-500">
                        {(job.file_size / 1024 / 1024).toFixed(1)} MB
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-1 ml-4">
                <span className="text-xs text-gray-500">
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
                
                {job.status === 'completed' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      downloadTranscript(job.job_id, job.filename)
                    }}
                    className="p-1.5 text-gray-400 hover:text-primary-600 rounded-md hover:bg-gray-100 transition-colors"
                    title="Download transcript"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
                
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteJob(job.job_id)
                  }}
                  className="p-1.5 text-gray-400 hover:text-red-600 rounded-md hover:bg-gray-100 transition-colors"
                  title="Delete job"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {jobs.length >= 20 && (
        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            Showing last 20 transcriptions
          </p>
        </div>
      )}
    </div>
  )
}

export default HistoryComponent
