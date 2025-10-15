import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, Loader2, Mic } from 'lucide-react'
import toast from 'react-hot-toast'

const UploadComponent = ({ onUploadStart }) => {
  const [isUploading, setIsUploading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('small')

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    
    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 100MB.')
      return
    }

    setIsUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('model', selectedModel)

      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      toast.success('Upload successful! Transcription started.')
      onUploadStart(result.job_id)
      
    } catch (error) {
      toast.error('Upload failed. Please try again.')
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
    }
  }, [selectedModel, onUploadStart])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma']
    },
    multiple: false,
    disabled: isUploading
  })

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      {/* Model Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Transcription Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={isUploading}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
        >
          <option value="tiny">Tiny (Fastest, Lower Quality)</option>
          <option value="small">Small (Balanced)</option>
          <option value="medium">Medium (Better Quality)</option>
          <option value="large-v3">Large (Best Quality, Slower)</option>
        </select>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50 scale-105' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isUploading ? (
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
          ) : (
            <div className="relative">
              <Upload className="w-12 h-12 text-gray-400" />
              <Mic className="w-6 h-6 text-primary-500 absolute -bottom-1 -right-1 bg-white rounded-full p-1" />
            </div>
          )}
          
          <div>
            <p className="text-lg font-medium text-gray-900 mb-1">
              {isUploading 
                ? 'Uploading...' 
                : isDragActive 
                  ? 'Drop your audio file here' 
                  : 'Upload Audio File'
              }
            </p>
            <p className="text-sm text-gray-500">
              {isUploading 
                ? 'Please wait while we process your file'
                : 'Drag & drop or click to select • MP3, WAV, M4A, FLAC'
              }
            </p>
          </div>
          
          {!isUploading && (
            <button
              type="button"
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Choose File
            </button>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-gray-50 rounded-lg">
          <File className="w-5 h-5 text-primary-500 mx-auto mb-1" />
          <p className="text-xs font-medium text-gray-700">Multiple Formats</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <Loader2 className="w-5 h-5 text-primary-500 mx-auto mb-1" />
          <p className="text-xs font-medium text-gray-700">Real-time Progress</p>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <Mic className="w-5 h-5 text-primary-500 mx-auto mb-1" />
          <p className="text-xs font-medium text-gray-700">High Accuracy</p>
        </div>
      </div>
    </div>
  )
}

export default UploadComponent
