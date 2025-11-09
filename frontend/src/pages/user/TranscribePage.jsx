import React, { useState, useCallback, useRef } from 'react'
import { Upload, X, Download, RefreshCw } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import cn from 'classnames'
import { toast } from 'react-hot-toast'

const CHUNK_SIZE = 1024 * 1024 // 1MB chunks
const SUPPORTED_FORMATS = [
  'audio/wav',
  'audio/x-wav',
  'audio/mp3',
  'audio/mpeg',
  'audio/ogg',
  'audio/x-m4a',
  'audio/aac',
  'audio/flac'
]

const TranscribePage = () => {
  const [file, setFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [transcriptionStatus, setTranscriptionStatus] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('small')
  const [language, setLanguage] = useState('')
  const abortControllerRef = useRef(null)

  const resetState = () => {
    setFile(null)
    setUploadProgress(0)
    setTranscriptionStatus(null)
    setTranscript(null)
    setIsUploading(false)
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (!SUPPORTED_FORMATS.includes(file.type)) {
      toast.error('Unsupported file format. Please upload an audio file.')
      return
    }

    setFile(file)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: SUPPORTED_FORMATS.join(','),
    multiple: false
  })

  const uploadChunked = async (file) => {
    try {
      setIsUploading(true)
      abortControllerRef.current = new AbortController()

      // Initialize upload
      const initResponse = await axios.post('/uploads/initialize', {
        filename: file.name,
        file_size: file.size,
        model_name: selectedModel,
        language: language || undefined
      })

      const { session_id, chunk_size, total_chunks } = initResponse.data
      const effectiveChunkSize = chunk_size || CHUNK_SIZE
      const chunks = Math.ceil(file.size / effectiveChunkSize)

      for (let i = 0; i < chunks; i++) {
        if (abortControllerRef.current.signal.aborted) {
          throw new Error('Upload cancelled')
        }

        const start = i * effectiveChunkSize
        const end = Math.min(start + effectiveChunkSize, file.size)
        const chunk = file.slice(start, end)

        const formData = new FormData()
        formData.append('chunk_data', chunk)

        await axios.post(`/uploads/${session_id}/chunks/${i}`, formData, {
          signal: abortControllerRef.current.signal
        })

        const progress = Math.round(((i + 1) / chunks) * 100)
        setUploadProgress(progress)
      }

      // Finalize upload
      const finalizeResponse = await axios.post(`/uploads/${session_id}/finalize`, null, {
        signal: abortControllerRef.current.signal
      })
      const { job_id } = finalizeResponse.data

      // Start polling for transcription status
      pollTranscriptionStatus(job_id)

    } catch (error) {
      if (error.message === 'Upload cancelled') {
        toast.error('Upload cancelled')
      } else {
        console.error('Upload failed:', error)
        toast.error('Upload failed. Please try again.')
      }
      setIsUploading(false)
    }
  }

  const uploadDirect = async (file) => {
    try {
      setIsUploading(true)
      abortControllerRef.current = new AbortController()

      const formData = new FormData()
      formData.append('file', file)
      formData.append('model', selectedModel)
      if (language) {
        formData.append('language', language)
      }

      const response = await axios.post('/jobs/', formData, {
        signal: abortControllerRef.current.signal,
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded / progressEvent.total) * 100
          )
          setUploadProgress(progress)
        }
      })

      const { job_id } = response.data
      pollTranscriptionStatus(job_id)

    } catch (error) {
      if (error.name === 'AbortError') {
        toast.error('Upload cancelled')
      } else {
        console.error('Upload failed:', error)
        toast.error('Upload failed. Please try again.')
      }
      setIsUploading(false)
    }
  }

  const pollTranscriptionStatus = async (jobId) => {
    try {
      const interval = setInterval(async () => {
        const response = await axios.get(`/jobs/${jobId}`)
        const {
          status,
          transcript,
          transcript_path: transcriptPath,
          transcript_download_url: transcriptDownloadUrl
        } = response.data

        const normalizedStatus = typeof status === 'string' ? status.toUpperCase() : status

        setTranscriptionStatus(normalizedStatus)

        if (normalizedStatus === 'COMPLETED') {
          clearInterval(interval)
          if (transcript) {
            setTranscript(transcript)
          } else if (transcriptDownloadUrl || transcriptPath) {
            try {
              const downloadTarget = transcriptDownloadUrl || transcriptPath
              const transcriptResponse = await axios.get(downloadTarget, {
                responseType: 'text'
              })
              setTranscript(transcriptResponse.data)
            } catch (transcriptError) {
              console.error('Failed to fetch transcript file:', transcriptError)
              toast.error('Transcript ready but could not be downloaded automatically.')
            }
          }
          setIsUploading(false)
          toast.success('Transcription completed!')
        } else if (normalizedStatus === 'FAILED') {
          clearInterval(interval)
          setIsUploading(false)
          toast.error('Transcription failed. Please try again.')
        }
      }, 2000)

      return () => clearInterval(interval)
    } catch (error) {
      console.error('Error polling status:', error)
      toast.error('Error checking transcription status')
      setIsUploading(false)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    if (file.size > 100 * 1024 * 1024) {
      await uploadChunked(file)
    } else {
      await uploadDirect(file)
    }
  }

  const handleDownload = () => {
    if (!transcript) return

    const blob = new Blob([transcript], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcript_${file.name}.txt`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    resetState()
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Transcribe Audio
        </h1>

        {/* Model and Language Selection */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700"
              disabled={isUploading}
            >
              <option value="tiny">Tiny (fast, less accurate)</option>
              <option value="base">Base</option>
              <option value="small">Small (recommended)</option>
              <option value="medium">Medium</option>
              <option value="large-v3">Large (slow, most accurate)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Language (optional)
            </label>
            <input
              type="text"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              placeholder="e.g., en, fr, de"
              className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700"
              disabled={isUploading}
            />
          </div>
        </div>

        {/* Upload Area */}
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
            {
              'border-blue-500 bg-blue-50 dark:bg-blue-900/20': isDragActive,
              'border-gray-300 dark:border-gray-600': !isDragActive,
              'pointer-events-none opacity-50': isUploading
            }
          )}
        >
          <input {...getInputProps()} />
          <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {file
              ? file.name
              : 'Drag and drop an audio file, or click to select'}
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
            Supported formats: WAV, MP3, OGG, M4A, AAC, FLAC
          </p>
        </div>

        {/* Progress and Actions */}
        {file && (
          <div className="mt-4 space-y-4">
            {isUploading && (
              <div>
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                  <span>
                    {transcriptionStatus
                      ? 'Transcribing...'
                      : 'Uploading...'}
                  </span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              {!isUploading ? (
                <>
                  <button
                    onClick={handleUpload}
                    className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Start Transcription
                  </button>
                  <button
                    onClick={resetState}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        )}

        {/* Transcript Display */}
        {transcript && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Transcript
              </h2>
              <button
                onClick={handleDownload}
                className="flex items-center px-3 py-2 text-sm text-blue-500 hover:text-blue-600"
              >
                <Download className="w-4 h-4 mr-2" />
                Download
              </button>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200">
                {transcript}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TranscribePage
