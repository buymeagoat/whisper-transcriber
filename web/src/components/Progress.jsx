import React, { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Clock, Download, Loader2, Copy, Share2 } from 'lucide-react'
import toast from 'react-hot-toast'

const ProgressComponent = ({ jobId, onComplete }) => {
  const [job, setJob] = useState(null)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [transcript, setTranscript] = useState('')
  const [ws, setWs] = useState(null)

  useEffect(() => {
    if (!jobId) return

    // Fetch initial job status
    fetchJobStatus()

    // Connect to WebSocket for real-time updates
    const websocket = new WebSocket(`ws://localhost:8000/ws/jobs/${jobId}`)
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
      setWs(websocket)
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setProgress(data.progress || 0)
      setMessage(data.message || '')
      
      if (data.status === 'completed' && data.transcript) {
        setTranscript(data.transcript)
        toast.success('Transcription completed!')
        onComplete?.()
      } else if (data.status === 'failed') {
        toast.error('Transcription failed')
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    return () => {
      websocket.close()
    }
  }, [jobId])

  const fetchJobStatus = async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`)
      if (response.ok) {
        const jobData = await response.json()
        setJob(jobData)
      }
    } catch (error) {
      console.error('Failed to fetch job status:', error)
    }
  }

  const downloadTranscript = async (format = 'txt') => {
    try {
      const response = await fetch(`/api/jobs/${jobId}/download?format=${format}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `transcript.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        toast.success('Download started')
      }
    } catch (error) {
      toast.error('Download failed')
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(transcript)
    toast.success('Copied to clipboard')
  }

  const shareTranscript = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Audio Transcript',
        text: transcript,
      })
    } else {
      copyToClipboard()
    }
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        <span className="ml-2 text-gray-600">Loading job details...</span>
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (job.status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />
      case 'processing':
        return <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
      default:
        return <Clock className="w-6 h-6 text-yellow-500" />
    }
  }

  const getStatusColor = () => {
    switch (job.status) {
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      case 'processing': return 'bg-primary-500'
      default: return 'bg-yellow-500'
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Job Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{job.filename}</h2>
              <p className="text-sm text-gray-500">
                Model: {job.model_used} • {job.file_size ? `${(job.file_size / 1024 / 1024).toFixed(1)} MB` : ''}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900 capitalize">{job.status}</p>
            <p className="text-xs text-gray-500">
              {new Date(job.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        {job.status === 'processing' && (
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{message}</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${getStatusColor()}`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Message */}
        {job.status === 'failed' && job.error_message && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{job.error_message}</p>
          </div>
        )}
      </div>

      {/* Transcript */}
      {transcript && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Transcript</h3>
            <div className="flex space-x-2">
              <button
                onClick={copyToClipboard}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <Copy className="w-4 h-4" />
                <span>Copy</span>
              </button>
              <button
                onClick={shareTranscript}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <Share2 className="w-4 h-4" />
                <span>Share</span>
              </button>
              <button
                onClick={() => downloadTranscript('txt')}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download</span>
              </button>
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {transcript}
            </p>
          </div>

          {/* Download Options */}
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={() => downloadTranscript('txt')}
              className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Download as TXT
            </button>
            <button
              onClick={() => downloadTranscript('json')}
              className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Download as JSON
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProgressComponent
