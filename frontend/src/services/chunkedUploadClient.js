/**
 * Chunked Upload Client for T025 Phase 5: File Upload Optimization
 * 
 * Provides chunked file upload capabilities with progress tracking,
 * resume functionality, and error handling on the frontend.
 */

import apiClient from './apiClient'

class ChunkedUploadClient {
  constructor() {
    this.chunkSize = 1024 * 1024 // 1MB chunks (matches backend)
    this.maxParallelChunks = 4
    this.activeUploads = new Map()
    this.websocketConnections = new Map()
  }

  /**
   * Initialize a new chunked upload session
   */
  async initializeUpload(file, options = {}) {
    try {
      const { model = 'small', language = null } = options
      
      const response = await apiClient.post('/uploads/initialize', {
        filename: file.name,
        file_size: file.size,
        file_hash: options.fileHash || null,
        model_name: model,
        language
      })

      const session = {
        sessionId: response.data.session_id,
        file,
        totalChunks: response.data.total_chunks,
        chunkSize: response.data.chunk_size,
        uploadedChunks: new Set(),
        progress: 0,
        status: 'initialized',
        errors: [],
        startTime: Date.now(),
        model,
        language
      }

      this.activeUploads.set(session.sessionId, session)
      return session
    } catch (error) {
      throw new Error(`Failed to initialize upload: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Upload a single chunk
   */
  async uploadChunk(sessionId, chunkNumber, chunkData) {
    try {
      const formData = new FormData()
      const blob = new Blob([chunkData])
      formData.append('chunk_data', blob)

      const response = await apiClient.post(
        `/uploads/${sessionId}/chunks/${chunkNumber}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      return response.data
    } catch (error) {
      throw new Error(`Failed to upload chunk ${chunkNumber}: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Upload file in chunks with progress tracking
   */
  async uploadFile(sessionId, progressCallback = null, errorCallback = null) {
    const session = this.activeUploads.get(sessionId)
    if (!session) {
      throw new Error('Upload session not found')
    }

    try {
      session.status = 'uploading'
      const { file, totalChunks } = session
      
      // Connect to WebSocket for real-time progress
      this.connectWebSocket(sessionId, progressCallback)

      // Create chunks
      const chunks = []
      for (let i = 0; i < totalChunks; i++) {
        const start = i * this.chunkSize
        const end = Math.min(start + this.chunkSize, file.size)
        chunks.push({
          number: i,
          data: file.slice(start, end)
        })
      }

      // Upload chunks in parallel batches
      await this.uploadChunksInBatches(sessionId, chunks, progressCallback, errorCallback)

      // Finalize upload
      const result = await this.finalizeUpload(sessionId)
      
      session.status = 'completed'
      session.jobId = result.job_id
      
      // Disconnect WebSocket
      this.disconnectWebSocket(sessionId)
      
      return result
    } catch (error) {
      session.status = 'failed'
      session.errors.push(error.message)
      
      if (errorCallback) {
        errorCallback(error, session)
      }
      
      throw error
    }
  }

  /**
   * Upload chunks in parallel batches
   */
  async uploadChunksInBatches(sessionId, chunks, progressCallback, errorCallback) {
    const session = this.activeUploads.get(sessionId)
    const batchSize = this.maxParallelChunks
    
    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, i + batchSize)
      
      // Upload batch in parallel
      const uploadPromises = batch.map(async (chunk) => {
        // Skip if already uploaded (for resume functionality)
        if (session.uploadedChunks.has(chunk.number)) {
          return { chunk_number: chunk.number, status: 'already_uploaded' }
        }

        try {
          const result = await this.uploadChunk(sessionId, chunk.number, chunk.data)
          session.uploadedChunks.add(chunk.number)
          
          // Update progress
          session.progress = (session.uploadedChunks.size / session.totalChunks) * 100
          
          if (progressCallback) {
            progressCallback({
              sessionId,
              chunkNumber: chunk.number,
              progress: session.progress,
              uploadedChunks: session.uploadedChunks.size,
              totalChunks: session.totalChunks,
              bytesUploaded: session.uploadedChunks.size * session.chunkSize,
              totalBytes: session.file.size,
              speed: this.calculateUploadSpeed(session)
            })
          }

          return result
        } catch (error) {
          session.errors.push(`Chunk ${chunk.number}: ${error.message}`)
          
          if (errorCallback) {
            errorCallback(error, { sessionId, chunkNumber: chunk.number })
          }
          
          throw error
        }
      })

      // Wait for batch to complete
      await Promise.all(uploadPromises)
    }
  }

  /**
   * Finalize upload by assembling chunks
   */
  async finalizeUpload(sessionId) {
    try {
      const response = await apiClient.post(`/uploads/${sessionId}/finalize`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to finalize upload: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Get upload status
   */
  async getUploadStatus(sessionId) {
    try {
      const response = await apiClient.get(`/uploads/${sessionId}/status`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to get upload status: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Resume an interrupted upload
   */
  async resumeUpload(sessionId, progressCallback = null, errorCallback = null) {
    try {
      // Get current status
      const status = await this.getUploadStatus(sessionId)
      
      if (status.status !== 'active') {
        throw new Error(`Cannot resume upload with status: ${status.status}`)
      }

      // Update local session state
      const session = this.activeUploads.get(sessionId)
      if (session) {
        // Mark already uploaded chunks
        for (let i = 0; i < status.total_chunks; i++) {
          if (!status.missing_chunks.includes(i)) {
            session.uploadedChunks.add(i)
          }
        }
        session.progress = (session.uploadedChunks.size / session.totalChunks) * 100
        session.status = 'resuming'
      }

      // Continue upload with missing chunks only
      return await this.uploadFile(sessionId, progressCallback, errorCallback)
    } catch (error) {
      throw new Error(`Failed to resume upload: ${error.message}`)
    }
  }

  /**
   * Cancel an upload
   */
  async cancelUpload(sessionId) {
    try {
      // Disconnect WebSocket
      this.disconnectWebSocket(sessionId)
      
      // Cancel on server
      const response = await apiClient.delete(`/uploads/${sessionId}`)
      
      // Remove from local state
      this.activeUploads.delete(sessionId)
      
      return response.data
    } catch (error) {
      throw new Error(`Failed to cancel upload: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Connect WebSocket for real-time progress updates
   */
  connectWebSocket(sessionId, progressCallback) {
    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/uploads/${sessionId}/progress`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log(`WebSocket connected for upload session ${sessionId}`)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'chunk_uploaded' && progressCallback) {
            progressCallback({
              sessionId,
              type: 'chunk_uploaded',
              ...data.data
            })
          } else if (data.type === 'assembly_started' && progressCallback) {
            progressCallback({
              sessionId,
              type: 'assembly_started',
              message: 'Assembling file...'
            })
          } else if (data.type === 'upload_completed' && progressCallback) {
            progressCallback({
              sessionId,
              type: 'upload_completed',
              jobId: data.job_id
            })
          } else if (data.type === 'upload_failed' && progressCallback) {
            progressCallback({
              sessionId,
              type: 'upload_failed',
              error: data.error
            })
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log(`WebSocket disconnected for upload session ${sessionId}`)
      }

      this.websocketConnections.set(sessionId, ws)
    } catch (error) {
      console.warn('Failed to connect WebSocket for progress updates:', error)
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket(sessionId) {
    const ws = this.websocketConnections.get(sessionId)
    if (ws) {
      ws.close()
      this.websocketConnections.delete(sessionId)
    }
  }

  /**
   * Calculate upload speed
   */
  calculateUploadSpeed(session) {
    const elapsed = (Date.now() - session.startTime) / 1000 // seconds
    const bytesUploaded = session.uploadedChunks.size * session.chunkSize
    return bytesUploaded / elapsed // bytes per second
  }

  /**
   * Format upload speed for display
   */
  formatSpeed(bytesPerSecond) {
    if (bytesPerSecond < 1024) {
      return `${bytesPerSecond.toFixed(0)} B/s`
    } else if (bytesPerSecond < 1024 * 1024) {
      return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`
    } else {
      return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`
    }
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes) {
    if (bytes < 1024) {
      return `${bytes} B`
    } else if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    } else if (bytes < 1024 * 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    } else {
      return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
    }
  }

  /**
   * Get active upload sessions
   */
  getActiveUploads() {
    return Array.from(this.activeUploads.values())
  }

  /**
   * Get upload session by ID
   */
  getUploadSession(sessionId) {
    return this.activeUploads.get(sessionId)
  }

  /**
   * Clean up completed or failed uploads
   */
  cleanup() {
    // Close all WebSocket connections
    for (const ws of this.websocketConnections.values()) {
      ws.close()
    }
    this.websocketConnections.clear()
    
    // Remove completed/failed uploads from active uploads
    for (const [sessionId, session] of this.activeUploads.entries()) {
      if (session.status === 'completed' || session.status === 'failed') {
        this.activeUploads.delete(sessionId)
      }
    }
  }
}

// Global instance
export const chunkedUploadClient = new ChunkedUploadClient()
export default chunkedUploadClient
