/**
 * T028 Frontend Implementation: Batch Upload Component
 * React component for batch transcription with drag-drop interface
 */

import React, { useState, useEffect, useRef } from 'react';
import batchUploadService from '../services/batchUploadService';

const BatchUpload = () => {
  const [files, setFiles] = useState([]);
  const [batchOptions, setBatchOptions] = useState({
    model: 'base',
    language: 'auto',
    priority: 'normal',
    batch_name: '',
    callback_url: ''
  });
  const [validation, setValidation] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [batchDetails, setBatchDetails] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

  const availableOptions = batchUploadService.getBatchOptions();

  useEffect(() => {
    loadBatches();
  }, []);

  useEffect(() => {
    if (files.length > 0) {
      const validationResult = batchUploadService.validateFiles(files);
      setValidation(validationResult);
    } else {
      setValidation(null);
    }
  }, [files]);

  const loadBatches = async () => {
    const result = await batchUploadService.getUserBatches();
    if (result.success) {
      setBatches(result.data);
    }
  };

  const loadBatchDetails = async (batchId) => {
    const result = await batchUploadService.getBatchDetails(batchId);
    if (result.success) {
      setBatchDetails(result.data);
      // Start progress monitoring if batch is active
      if (result.data.status === 'processing' || result.data.status === 'pending') {
        batchUploadService.startProgressMonitoring(batchId, (progress) => {
          setBatchDetails(prev => ({ ...prev, ...progress }));
        });
      }
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      addFiles(droppedFiles);
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      addFiles(selectedFiles);
    }
  };

  const addFiles = (newFiles) => {
    // Filter out duplicates based on name and size
    const uniqueFiles = newFiles.filter(newFile => 
      !files.some(existingFile => 
        existingFile.name === newFile.name && existingFile.size === newFile.size
      )
    );
    
    setFiles(prev => [...prev, ...uniqueFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    setFiles([]);
    setValidation(null);
  };

  const handleSubmitBatch = async () => {
    if (!validation?.isValid || files.length === 0) return;

    setUploading(true);
    setError(null);
    setUploadProgress(0);

    const result = await batchUploadService.submitBatch(files, batchOptions);
    
    if (result.success) {
      setSuccess(`Batch submitted successfully! Batch ID: ${result.data.batch_id}`);
      setFiles([]);
      setValidation(null);
      await loadBatches();
      
      // Start monitoring the new batch
      batchUploadService.startProgressMonitoring(result.data.batch_id, (progress) => {
        if (selectedBatch === result.data.batch_id) {
          setBatchDetails(prev => ({ ...prev, ...progress }));
        }
      });
    } else {
      setError(result.error);
    }

    setUploading(false);
    setUploadProgress(0);
  };

  const handleCancelBatch = async (batchId) => {
    if (!window.confirm('Are you sure you want to cancel this batch? This action cannot be undone.')) {
      return;
    }

    const result = await batchUploadService.cancelBatch(batchId);
    if (result.success) {
      await loadBatches();
      if (selectedBatch === batchId) {
        setSelectedBatch(null);
        setBatchDetails(null);
      }
    } else {
      setError(result.error);
    }
  };

  const handleDownloadResults = async (batchId) => {
    const result = await batchUploadService.downloadBatchResults(batchId);
    if (!result.success) {
      setError(result.error);
    }
  };

  const formatFileSize = batchUploadService.formatFileSize;
  const getBatchStatusInfo = batchUploadService.getBatchStatusInfo;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Batch Upload</h2>
        <p className="text-gray-600">Upload multiple files for batch transcription processing</p>
      </div>

      {/* Error/Success notifications */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-400">
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="text-green-400">
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="space-y-6">
          {/* File Drop Zone */}
          <div className="bg-white shadow-sm rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Select Files</h3>
            
            <div
              ref={dropZoneRef}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-400 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="audio/*,video/*"
                onChange={handleFileSelect}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              
              <div className="space-y-2">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="text-gray-600">
                  <span className="font-medium text-blue-600 hover:text-blue-500">Click to upload</span>
                  {' '}or drag and drop
                </div>
                <p className="text-xs text-gray-500">
                  Audio files (MP3, WAV, FLAC, M4A, OGG) or video files (MP4, MOV, AVI)
                </p>
                <p className="text-xs text-gray-500">
                  Maximum 50 files, 100MB per file
                </p>
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mt-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-medium text-gray-900">
                    Selected Files ({files.length})
                  </h4>
                  <button
                    onClick={clearFiles}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Clear All
                  </button>
                </div>
                
                <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md">
                  {files.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-2 border-b border-gray-200 last:border-b-0">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="ml-2 text-red-600 hover:text-red-800"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>

                {/* Validation Summary */}
                {validation && (
                  <div className="mt-3">
                    <div className="text-sm text-gray-600">
                      Total: {validation.fileCount} files, {formatFileSize(validation.totalSize)}
                    </div>
                    
                    {validation.errors.length > 0 && (
                      <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
                        <h5 className="text-sm font-medium text-red-800 mb-1">Errors:</h5>
                        <ul className="text-xs text-red-700 space-y-1">
                          {validation.errors.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {validation.warnings.length > 0 && (
                      <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                        <h5 className="text-sm font-medium text-yellow-800 mb-1">Warnings:</h5>
                        <ul className="text-xs text-yellow-700 space-y-1">
                          {validation.warnings.map((warning, index) => (
                            <li key={index}>• {warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Batch Options */}
          {files.length > 0 && (
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Batch Options</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model
                  </label>
                  <select
                    value={batchOptions.model}
                    onChange={(e) => setBatchOptions(prev => ({ ...prev, model: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {availableOptions.models.map(model => (
                      <option key={model.value} value={model.value}>
                        {model.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Language
                  </label>
                  <select
                    value={batchOptions.language}
                    onChange={(e) => setBatchOptions(prev => ({ ...prev, language: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {availableOptions.languages.map(lang => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={batchOptions.priority}
                    onChange={(e) => setBatchOptions(prev => ({ ...prev, priority: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {availableOptions.priorities.map(priority => (
                      <option key={priority.value} value={priority.value}>
                        {priority.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Name
                  </label>
                  <input
                    type="text"
                    value={batchOptions.batch_name}
                    onChange={(e) => setBatchOptions(prev => ({ ...prev, batch_name: e.target.value }))}
                    placeholder="Optional batch name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Callback URL (Optional)
                </label>
                <input
                  type="url"
                  value={batchOptions.callback_url}
                  onChange={(e) => setBatchOptions(prev => ({ ...prev, callback_url: e.target.value }))}
                  placeholder="https://your-app.com/webhook"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Receive notifications when batch processing is complete
                </p>
              </div>

              <div className="mt-6">
                <button
                  onClick={handleSubmitBatch}
                  disabled={!validation?.isValid || uploading}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Uploading...' : `Submit Batch (${files.length} files)`}
                </button>
                
                {uploading && uploadProgress > 0 && (
                  <div className="mt-2">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      Uploading: {uploadProgress}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Batch History */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Batch History</h3>
          
          {batches.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No batches</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by uploading your first batch.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {batches.map((batch) => {
                const statusInfo = getBatchStatusInfo(batch.status);
                return (
                  <div 
                    key={batch.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedBatch === batch.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => {
                      setSelectedBatch(batch.id);
                      loadBatchDetails(batch.id);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <h4 className="text-sm font-medium text-gray-900">
                            {batch.name || `Batch ${batch.id}`}
                          </h4>
                          <span className={`ml-2 px-2 py-1 text-xs rounded-full ${statusInfo.bgColor} ${statusInfo.textColor}`}>
                            {batch.status}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {batch.total_files} files • Created {new Date(batch.created_at).toLocaleDateString()}
                        </div>
                        {batch.completed_files > 0 && (
                          <div className="text-xs text-gray-500">
                            Progress: {batch.completed_files}/{batch.total_files} completed
                          </div>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        {batch.status === 'completed' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadResults(batch.id);
                            }}
                            className="text-blue-600 hover:text-blue-800 text-xs"
                          >
                            Download
                          </button>
                        )}
                        {(batch.status === 'processing' || batch.status === 'pending') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCancelBatch(batch.id);
                            }}
                            className="text-red-600 hover:text-red-800 text-xs"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Batch Details */}
          {batchDetails && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Batch Details: {batchDetails.name || `Batch ${batchDetails.id}`}
              </h4>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Status:</span>
                  <span className="ml-2 font-medium">{batchDetails.status}</span>
                </div>
                <div>
                  <span className="text-gray-500">Model:</span>
                  <span className="ml-2 font-medium">{batchDetails.model}</span>
                </div>
                <div>
                  <span className="text-gray-500">Files:</span>
                  <span className="ml-2 font-medium">
                    {batchDetails.completed_files || 0}/{batchDetails.total_files}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Created:</span>
                  <span className="ml-2 font-medium">
                    {new Date(batchDetails.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {batchDetails.progress_percentage !== undefined && (
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{Math.round(batchDetails.progress_percentage)}%</span>
                  </div>
                  <div className="bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${batchDetails.progress_percentage}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {batchDetails.error_message && (
                <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                  Error: {batchDetails.error_message}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BatchUpload;