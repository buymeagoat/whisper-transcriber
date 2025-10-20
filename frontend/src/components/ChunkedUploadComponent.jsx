/**
 * Chunked Upload Component for T025 Phase 5: File Upload Optimization
 * 
 * React component that provides chunked file upload with progress bars,
 * resume functionality, and error handling.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Upload, X, Pause, Play, RotateCcw, CheckCircle, AlertCircle } from 'lucide-react'
import chunkedUploadClient from '../services/chunkedUploadClient'

const ChunkedUploadComponent = ({ 
  onUploadStart, 
  onUploadProgress, 
  onUploadComplete, 
  onUploadError,
  maxFileSize = 1024 * 1024 * 1024, // 1GB default
  allowedTypes = ['audio/wav', 'audio/mp3', 'audio/m4a', 'audio/flac'],
  className = ''
}) => {
  const [uploads, setUploads] = useState([])
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      chunkedUploadClient.cleanup()
    }
  }, [])

  const handleFileSelect = useCallback((files) => {
    Array.from(files).forEach(file => {
      // Validate file
      if (file.size > maxFileSize) {
        onUploadError && onUploadError(new Error(`File too large: ${file.name}`), null)
        return
      }

      if (!allowedTypes.includes(file.type)) {
        onUploadError && onUploadError(new Error(`Invalid file type: ${file.name}`), null)
        return
      }

      startUpload(file)
    })
  }, [maxFileSize, allowedTypes, onUploadError])

  const startUpload = async (file, model = 'small', language = null) => {
    try {
      // Initialize upload
      const session = await chunkedUploadClient.initializeUpload(file, { model, language })
      
      // Add to local state
      const uploadState = {
        sessionId: session.sessionId,
        filename: file.name,
        fileSize: file.size,
        progress: 0,
        status: 'uploading',
        speed: 0,
        eta: null,
        error: null,
        startTime: Date.now(),
        model,
        language,
        isPaused: false,
        canResume: false
      }
      
      setUploads(prev => [...prev, uploadState])
      onUploadStart && onUploadStart(uploadState)

      // Start upload with progress tracking
      const progressCallback = (progressData) => {
        setUploads(prev => prev.map(upload => {
          if (upload.sessionId === session.sessionId) {
            const updated = {
              ...upload,
              progress: progressData.progress || upload.progress,
              speed: progressData.speed || upload.speed
            }

            // Calculate ETA
            if (progressData.speed && progressData.progress < 100) {
              const remainingBytes = upload.fileSize * (1 - progressData.progress / 100)
              updated.eta = remainingBytes / progressData.speed
            }

            // Handle different event types
            if (progressData.type === 'assembly_started') {
              updated.status = 'assembling'
              updated.progress = 100 // Assembly is the final step
            } else if (progressData.type === 'upload_completed') {
              updated.status = 'completed'
              updated.progress = 100
              updated.jobId = progressData.jobId
            } else if (progressData.type === 'upload_failed') {
              updated.status = 'failed'
              updated.error = progressData.error
            }

            return updated
          }
          return upload
        }))

        onUploadProgress && onUploadProgress(progressData)
      }

      const errorCallback = (error, context) => {
        setUploads(prev => prev.map(upload => {
          if (upload.sessionId === session.sessionId) {
            return {
              ...upload,
              status: 'failed',
              error: error.message,
              canResume: true
            }
          }
          return upload
        }))

        onUploadError && onUploadError(error, context)
      }

      // Start the upload
      const result = await chunkedUploadClient.uploadFile(
        session.sessionId,
        progressCallback,
        errorCallback
      )

      // Mark as completed
      setUploads(prev => prev.map(upload => {
        if (upload.sessionId === session.sessionId) {
          return {
            ...upload,
            status: 'completed',
            progress: 100,
            jobId: result.job_id
          }
        }
        return upload
      }))

      onUploadComplete && onUploadComplete(result, uploadState)

    } catch (error) {
      // Handle initialization errors
      setUploads(prev => prev.map(upload => {
        if (upload.sessionId === session?.sessionId) {
          return {
            ...upload,
            status: 'failed',
            error: error.message
          }
        }
        return upload
      }))

      onUploadError && onUploadError(error, { file })
    }
  }

  const resumeUpload = async (sessionId) => {
    const upload = uploads.find(u => u.sessionId === sessionId)
    if (!upload) return

    try {
      setUploads(prev => prev.map(u => 
        u.sessionId === sessionId 
          ? { ...u, status: 'uploading', isPaused: false, error: null }
          : u
      ))

      const progressCallback = (progressData) => {
        setUploads(prev => prev.map(u => {
          if (u.sessionId === sessionId) {
            return {
              ...u,
              progress: progressData.progress || u.progress,
              speed: progressData.speed || u.speed
            }
          }
          return u
        }))
      }

      const result = await chunkedUploadClient.resumeUpload(
        sessionId,
        progressCallback
      )

      setUploads(prev => prev.map(u => 
        u.sessionId === sessionId 
          ? { ...u, status: 'completed', progress: 100, jobId: result.job_id }
          : u
      ))

      onUploadComplete && onUploadComplete(result, upload)

    } catch (error) {
      setUploads(prev => prev.map(u => 
        u.sessionId === sessionId 
          ? { ...u, status: 'failed', error: error.message }
          : u
      ))

      onUploadError && onUploadError(error, { sessionId })
    }
  }

  const cancelUpload = async (sessionId) => {
    try {
      await chunkedUploadClient.cancelUpload(sessionId)
      setUploads(prev => prev.filter(u => u.sessionId !== sessionId))
    } catch (error) {
      console.error('Failed to cancel upload:', error)
    }
  }

  const removeUpload = (sessionId) => {
    setUploads(prev => prev.filter(u => u.sessionId !== sessionId))
  }

  const formatTime = (seconds) => {
    if (!seconds || !isFinite(seconds)) return '--:--'
    
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files)
    }
  }, [handleFileSelect])

  const handleFileInputChange = useCallback((e) => {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files)
    }
  }, [handleFileSelect])

  return (
    <div className={`chunked-upload-component ${className}`}>
      {/* Upload Drop Zone */}
      <div
        className={`upload-drop-zone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="upload-icon" size={48} />
        <div className="upload-text">
          <h3>Drop files here or click to upload</h3>
          <p>Supports large files up to 1GB with automatic resume</p>
          <p>Supported formats: MP3, WAV, M4A, FLAC</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowedTypes.join(',')}
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* Upload List */}
      {uploads.length > 0 && (
        <div className="upload-list">
          <h4>Uploads</h4>
          {uploads.map((upload) => (
            <UploadItem
              key={upload.sessionId}
              upload={upload}
              onResume={() => resumeUpload(upload.sessionId)}
              onCancel={() => cancelUpload(upload.sessionId)}
              onRemove={() => removeUpload(upload.sessionId)}
              formatTime={formatTime}
            />
          ))}
        </div>
      )}

      <style jsx>{`
        .chunked-upload-component {
          width: 100%;
          max-width: 800px;
          margin: 0 auto;
        }

        .upload-drop-zone {
          border: 2px dashed #cbd5e0;
          border-radius: 8px;
          padding: 40px 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          background: #f7fafc;
        }

        .upload-drop-zone:hover,
        .upload-drop-zone.drag-over {
          border-color: #4299e1;
          background: #ebf8ff;
        }

        .upload-icon {
          color: #718096;
          margin-bottom: 16px;
        }

        .upload-text h3 {
          margin: 0 0 8px 0;
          color: #2d3748;
          font-size: 18px;
          font-weight: 600;
        }

        .upload-text p {
          margin: 4px 0;
          color: #718096;
          font-size: 14px;
        }

        .upload-list {
          margin-top: 24px;
        }

        .upload-list h4 {
          margin: 0 0 16px 0;
          color: #2d3748;
          font-size: 16px;
          font-weight: 600;
        }
      `}</style>
    </div>
  )
}

const UploadItem = ({ upload, onResume, onCancel, onRemove, formatTime }) => {
  const getStatusIcon = () => {
    switch (upload.status) {
      case 'completed':
        return <CheckCircle className="status-icon completed" size={20} />
      case 'failed':
        return <AlertCircle className="status-icon failed" size={20} />
      case 'uploading':
      case 'assembling':
        return <div className="spinner" />
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (upload.status) {
      case 'uploading':
        return 'Uploading...'
      case 'assembling':
        return 'Assembling file...'
      case 'completed':
        return 'Completed'
      case 'failed':
        return upload.error || 'Upload failed'
      default:
        return upload.status
    }
  }

  return (
    <div className="upload-item">
      <div className="upload-header">
        <div className="file-info">
          {getStatusIcon()}
          <div className="file-details">
            <div className="filename">{upload.filename}</div>
            <div className="file-meta">
              {chunkedUploadClient.formatFileSize(upload.fileSize)} • {upload.model}
              {upload.language && ` • ${upload.language}`}
            </div>
          </div>
        </div>
        
        <div className="upload-actions">
          {upload.status === 'failed' && upload.canResume && (
            <button onClick={onResume} className="action-btn resume" title="Resume">
              <Play size={16} />
            </button>
          )}
          
          {(upload.status === 'uploading' || upload.status === 'failed') && (
            <button onClick={onCancel} className="action-btn cancel" title="Cancel">
              <X size={16} />
            </button>
          )}
          
          {(upload.status === 'completed' || upload.status === 'failed') && (
            <button onClick={onRemove} className="action-btn remove" title="Remove">
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      <div className="upload-progress">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${upload.progress}%` }}
          />
        </div>
        
        <div className="progress-info">
          <span className="status-text">{getStatusText()}</span>
          
          {upload.status === 'uploading' && (
            <span className="upload-stats">
              {upload.progress.toFixed(1)}% • 
              {upload.speed && chunkedUploadClient.formatSpeed(upload.speed)} •
              ETA {formatTime(upload.eta)}
            </span>
          )}
          
          {upload.status === 'completed' && upload.jobId && (
            <span className="job-id">Job ID: {upload.jobId}</span>
          )}
        </div>
      </div>

      <style jsx>{`
        .upload-item {
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          padding: 16px;
          margin-bottom: 12px;
          background: white;
        }

        .upload-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }

        .file-info {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          flex: 1;
        }

        .status-icon {
          margin-top: 2px;
        }

        .status-icon.completed {
          color: #38a169;
        }

        .status-icon.failed {
          color: #e53e3e;
        }

        .spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #e2e8f0;
          border-top: 2px solid #4299e1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .file-details {
          flex: 1;
        }

        .filename {
          font-weight: 600;
          color: #2d3748;
          margin-bottom: 4px;
        }

        .file-meta {
          font-size: 14px;
          color: #718096;
        }

        .upload-actions {
          display: flex;
          gap: 8px;
        }

        .action-btn {
          padding: 6px;
          border: 1px solid #e2e8f0;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .action-btn:hover {
          background: #f7fafc;
        }

        .action-btn.resume {
          color: #38a169;
          border-color: #38a169;
        }

        .action-btn.cancel,
        .action-btn.remove {
          color: #e53e3e;
          border-color: #e53e3e;
        }

        .upload-progress {
          space-y: 8px;
        }

        .progress-bar {
          width: 100%;
          height: 6px;
          background: #e2e8f0;
          border-radius: 3px;
          overflow: hidden;
          margin-bottom: 8px;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #4299e1, #3182ce);
          transition: width 0.3s ease;
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 14px;
        }

        .status-text {
          color: #2d3748;
          font-weight: 500;
        }

        .upload-stats,
        .job-id {
          color: #718096;
        }
      `}</style>
    </div>
  )
}

export default ChunkedUploadComponent
