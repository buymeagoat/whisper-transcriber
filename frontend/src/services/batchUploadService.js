/**
 * T020: Batch Upload Service - Frontend API client
 * Updated service for handling batch upload API communication and progress tracking
 */

import apiClient from './apiClient';

// Batch upload status enum
export const BATCH_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

// Job status enum
export const JOB_STATUS = {
  QUEUED: 'queued',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  SKIPPED: 'skipped'
};

/**
 * Configuration for batch upload
 */
export class BatchUploadConfig {
  constructor({
    maxFiles = 50,
    maxFileSize = 1024 * 1024 * 1024, // 1GB
    maxTotalSize = 5 * 1024 * 1024 * 1024, // 5GB
    whisperModel = 'base',
    language = null,
    concurrentJobs = 3
  } = {}) {
    this.maxFiles = maxFiles;
    this.maxFileSize = maxFileSize;
    this.maxTotalSize = maxTotalSize;
    this.whisperModel = whisperModel;
    this.language = language;
    this.concurrentJobs = concurrentJobs;
  }

  toJSON() {
    return {
      max_files: this.maxFiles,
      max_file_size: this.maxFileSize,
      max_total_size: this.maxTotalSize,
      whisper_model: this.whisperModel,
      language: this.language,
      concurrent_jobs: this.concurrentJobs
    };
  }
}

class BatchUploadService {
  constructor() {
    this.activeBatches = new Map();
    this.progressCallbacks = new Map();
    this.uploadProgress = new Map(); // Keep for compatibility
    this.batchJobs = new Map(); // Keep for compatibility
  }

  /**
   * Create a new batch upload
   * @param {File[]} files - Array of files to upload
   * @param {BatchUploadConfig} config - Upload configuration
   * @returns {Promise<string>} Batch ID
   */
  async createBatchUpload(files, config = new BatchUploadConfig()) {
    try {
      // Validate files before upload
      this.validateFiles(files, config);

      // Create FormData with files and configuration
      const formData = new FormData();
      
      files.forEach((file, index) => {
        formData.append('files', file);
      });
      
      formData.append('config_json', JSON.stringify(config.toJSON()));

      // Create batch upload with progress tracking
      const response = await apiClient.post('/batch-upload/create', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          this.updateUploadProgress('batch_upload', progress);
        }
      });

      const batchData = response.data;
      
      // Store batch info locally
      this.activeBatches.set(batchData.batch_id, {
        ...batchData,
        files: files.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type
        })),
        config
      });

      return batchData.batch_id;

    } catch (error) {
      console.error('Error creating batch upload:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to create batch upload'
      );
    }
  }

  /**
   * Legacy method for compatibility - redirects to createBatchUpload
   */
  async submitBatch(files, options = {}) {
    try {
      const config = new BatchUploadConfig({
        whisperModel: options.model || 'base',
        language: options.language || null
      });

      const batchId = await this.createBatchUpload(files, config);
      await this.startBatchProcessing(batchId);

      return {
        success: true,
        data: { batch_id: batchId }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Failed to submit batch'
      };
    }
  }

  /**
   * Start processing a batch upload
   * @param {string} batchId - Batch ID
   * @returns {Promise<void>}
   */
  async startBatchProcessing(batchId) {
    try {
      await apiClient.post(`/batch-upload/${batchId}/start`);
      
      // Update local batch info
      const batchInfo = this.activeBatches.get(batchId);
      if (batchInfo) {
        batchInfo.status = BATCH_STATUS.PROCESSING;
      }

    } catch (error) {
      console.error('Error starting batch processing:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to start batch processing'
      );
    }
  }

  /**
   * Get all user's batch jobs
   */
  async getUserBatches() {
    try {
      const response = await apiClient.get('/batch-upload/list');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch batches'
      };
    }
  }

  /**
   * Get batch upload progress
   * @param {string} batchId - Batch ID
   * @returns {Promise<Object>} Progress information
   */
  async getBatchProgress(batchId) {
    try {
      const response = await apiClient.get(`/batch-upload/${batchId}/progress`);
      const progressData = response.data;

      // Update local batch info
      const batchInfo = this.activeBatches.get(batchId);
      if (batchInfo) {
        Object.assign(batchInfo, progressData);
      }

      // Trigger progress callback if registered
      const callback = this.progressCallbacks.get(batchId);
      if (callback) {
        callback(progressData);
      }

      return progressData;

    } catch (error) {
      console.error('Error getting batch progress:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to get batch progress'
      );
    }
  }

  /**
   * Get specific batch details and job statuses
   */
  async getBatchDetails(batchId) {
    try {
      const response = await apiClient.get(`/batch-upload/${batchId}/status`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch batch details'
      };
    }
  }

  /**
   * Cancel a batch upload
   * @param {string} batchId - Batch ID
   * @returns {Promise<void>}
   */
  async cancelBatchUpload(batchId) {
    try {
      await apiClient.post(`/batch-upload/${batchId}/cancel`);
      
      // Update local batch info
      const batchInfo = this.activeBatches.get(batchId);
      if (batchInfo) {
        batchInfo.status = BATCH_STATUS.CANCELLED;
      }

    } catch (error) {
      console.error('Error cancelling batch upload:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to cancel batch upload'
      );
    }
  }

  /**
   * Cancel a batch job (legacy method for compatibility)
   */
  async cancelBatch(batchId) {
    try {
      await this.cancelBatchUpload(batchId);
      return {
        success: true,
        data: { message: 'Batch cancelled successfully' }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Failed to cancel batch'
      };
    }
  }

  /**
   * Download batch results as ZIP
   */
  async downloadBatchResults(batchId) {
    try {
      const response = await apiClient.get(`/api/v1/batches/${batchId}/download`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `batch_${batchId}_results.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      return {
        success: true,
        data: 'Download started'
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to download batch results'
      };
    }
  }

  /**
   * Get batch progress and statistics
   */
  async getBatchProgress(batchId) {
    try {
      const response = await apiClient.get(`/api/v1/batches/${batchId}/progress`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch batch progress'
      };
    }
  }

  /**
   * Validate files before upload (updated for T020)
   * @param {File[]} files - Files to validate
   * @param {BatchUploadConfig} config - Upload configuration
   */
  validateFiles(files, config = new BatchUploadConfig()) {
    if (!files || files.length === 0) {
      throw new Error('No files provided');
    }

    if (files.length > config.maxFiles) {
      throw new Error(`Too many files. Maximum ${config.maxFiles} files allowed`);
    }

    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    if (totalSize > config.maxTotalSize) {
      throw new Error(`Total file size too large. Maximum ${this.formatFileSize(config.maxTotalSize)} allowed`);
    }

    const allowedFormats = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm', 'mp4'];
    
    for (const file of files) {
      if (file.size > config.maxFileSize) {
        throw new Error(`File "${file.name}" too large. Maximum ${this.formatFileSize(config.maxFileSize)} per file`);
      }

      const fileExt = file.name.split('.').pop().toLowerCase();
      if (!allowedFormats.includes(fileExt)) {
        throw new Error(`File "${file.name}" has unsupported format. Allowed: ${allowedFormats.join(', ')}`);
      }
    }
  }

  /**
   * Legacy validate files method for compatibility
   */
  validateFilesLegacy(files) {
    const errors = [];
    const warnings = [];
    const supportedFormats = ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'wma', 'mp4', 'mov', 'avi'];
    const maxFileSize = 100 * 1024 * 1024; // 100MB
    const maxBatchSize = 50;

    // Check batch size
    if (files.length === 0) {
      errors.push('Please select at least one file');
    } else if (files.length > maxBatchSize) {
      errors.push(`Maximum ${maxBatchSize} files allowed per batch`);
    }

    // Validate each file
    files.forEach((file, index) => {
      const fileName = file.name;
      const fileSize = file.size;
      const fileExtension = fileName.split('.').pop()?.toLowerCase();

      // Check file extension
      if (!supportedFormats.includes(fileExtension)) {
        errors.push(`File "${fileName}": Unsupported format. Supported: ${supportedFormats.join(', ')}`);
      }

      // Check file size
      if (fileSize > maxFileSize) {
        errors.push(`File "${fileName}": File size exceeds 100MB limit`);
      }

      // Check for duplicates
      const duplicates = files.filter(f => f.name === fileName);
      if (duplicates.length > 1) {
        warnings.push(`Duplicate file name detected: "${fileName}"`);
      }

      // Warn about very small files
      if (fileSize < 1024) {
        warnings.push(`File "${fileName}": Very small file size (${fileSize} bytes)`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      fileCount: files.length,
      totalSize: files.reduce((sum, file) => sum + file.size, 0)
    };
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Format duration for display
   */
  formatDuration(seconds) {
    if (!seconds || seconds < 0) return '--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  }

  /**
   * Get batch status color and icon
   */
  getBatchStatusInfo(status) {
    const statusMap = {
      'pending': {
        color: 'yellow',
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        icon: 'clock'
      },
      'processing': {
        color: 'blue',
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        icon: 'cog'
      },
      'completed': {
        color: 'green',
        bgColor: 'bg-green-100',
        textColor: 'text-green-800',
        icon: 'check'
      },
      'failed': {
        color: 'red',
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        icon: 'exclamation'
      },
      'cancelled': {
        color: 'gray',
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-800',
        icon: 'ban'
      },
      'partial': {
        color: 'orange',
        bgColor: 'bg-orange-100',
        textColor: 'text-orange-800',
        icon: 'warning'
      }
    };

    return statusMap[status] || statusMap['pending'];
  }

  /**
   * Calculate estimated completion time
   */
  calculateEstimatedTime(filesCount, averageFileSize) {
    // Base processing time estimates (in seconds per MB)
    const processingTimePerMB = 30; // 30 seconds per MB
    const baseOverhead = 60; // 1 minute base overhead
    const fileOverhead = 10; // 10 seconds per file

    const totalSizeMB = averageFileSize * filesCount / (1024 * 1024);
    const estimatedSeconds = (totalSizeMB * processingTimePerMB) + baseOverhead + (filesCount * fileOverhead);

    return Math.ceil(estimatedSeconds);
  }

  /**
   * Start real-time progress monitoring for a batch
   */
  startProgressMonitoring(batchId, callback) {
    this.progressCallbacks.set(batchId, callback);
    
    const monitor = async () => {
      const result = await this.getBatchProgress(batchId);
      if (result.success) {
        const progress = result.data;
        callback(progress);
        
        // Continue monitoring if batch is still processing
        if (progress.status === 'processing' || progress.status === 'pending') {
          setTimeout(monitor, 2000); // Check every 2 seconds
        } else {
          // Final update and cleanup
          this.progressCallbacks.delete(batchId);
        }
      }
    };

    // Start monitoring after a short delay
    setTimeout(monitor, 1000);
  }

  /**
   * Stop progress monitoring for a batch
   */
  stopProgressMonitoring(batchId) {
    this.progressCallbacks.delete(batchId);
  }

  /**
   * Update upload progress
   */
  updateUploadProgress(id, progress) {
    this.uploadProgress.set(id, progress);
    const callback = this.progressCallbacks.get(id);
    if (callback) {
      callback({ uploadProgress: progress });
    }
  }

  /**
   * Get available batch processing options
   */
  getBatchOptions() {
    return {
      models: [
        { value: 'tiny', label: 'Tiny (Fast, lower accuracy)', size: '39 MB' },
        { value: 'base', label: 'Base (Balanced)', size: '74 MB' },
        { value: 'small', label: 'Small (Good quality)', size: '244 MB' },
        { value: 'medium', label: 'Medium (Better quality)', size: '769 MB' },
        { value: 'large-v3', label: 'Large-v3 (Best quality)', size: '1550 MB' }
      ],
      priorities: [
        { value: 'low', label: 'Low Priority', description: 'Process when resources available' },
        { value: 'normal', label: 'Normal Priority', description: 'Standard processing queue' },
        { value: 'high', label: 'High Priority', description: 'Process ahead of normal jobs' }
      ],
      languages: [
        { value: 'auto', label: 'Auto-detect' },
        { value: 'en', label: 'English' },
        { value: 'es', label: 'Spanish' },
        { value: 'fr', label: 'French' },
        { value: 'de', label: 'German' },
        { value: 'it', label: 'Italian' },
        { value: 'pt', label: 'Portuguese' },
        { value: 'zh', label: 'Chinese' },
        { value: 'ja', label: 'Japanese' },
        { value: 'ko', label: 'Korean' }
      ]
    };
  }

  /**
   * Prepare files for batch processing (with chunking if needed)
   */
  async prepareFilesForBatch(files) {
    const preparedFiles = [];
    
    for (const file of files) {
      // For very large files, we might want to pre-process or chunk them
      if (file.size > 50 * 1024 * 1024) { // > 50MB
        // Add metadata for large file handling
        preparedFiles.push({
          file,
          requiresChunking: true,
          originalSize: file.size,
          estimatedChunks: Math.ceil(file.size / (25 * 1024 * 1024)) // 25MB chunks
        });
      } else {
        preparedFiles.push({
          file,
          requiresChunking: false,
          originalSize: file.size
        });
      }
    }

    return preparedFiles;
  }

  // ========== T020 Specific Methods ==========

  /**
   * Get batch jobs information
   * @param {string} batchId - Batch ID
   * @returns {Promise<Object>} Jobs information
   */
  async getBatchJobs(batchId) {
    try {
      const response = await apiClient.get(`/batch-upload/${batchId}/jobs`);
      return response.data;

    } catch (error) {
      console.error('Error getting batch jobs:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to get batch jobs'
      );
    }
  }

  /**
   * Delete a batch upload
   * @param {string} batchId - Batch ID
   * @returns {Promise<void>}
   */
  async deleteBatchUpload(batchId) {
    try {
      await apiClient.delete(`/batch-upload/${batchId}`);
      
      // Remove from local storage
      this.activeBatches.delete(batchId);
      this.progressCallbacks.delete(batchId);

    } catch (error) {
      console.error('Error deleting batch upload:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to delete batch upload'
      );
    }
  }

  /**
   * Get batch upload statistics
   * @returns {Promise<Object>} Statistics
   */
  async getBatchStats() {
    try {
      const response = await apiClient.get('/batch-upload/stats');
      return response.data;

    } catch (error) {
      console.error('Error getting batch stats:', error);
      throw new Error(
        error.response?.data?.detail || 
        'Failed to get batch statistics'
      );
    }
  }

  /**
   * Register progress callback for a batch
   * @param {string} batchId - Batch ID
   * @param {Function} callback - Progress callback function
   */
  onProgress(batchId, callback) {
    this.progressCallbacks.set(batchId, callback);
  }

  /**
   * Start polling for batch progress
   * @param {string} batchId - Batch ID
   * @param {number} interval - Polling interval in milliseconds (default: 2000)
   * @returns {Function} Stop polling function
   */
  startProgressPolling(batchId, interval = 2000) {
    const pollProgress = async () => {
      try {
        const progress = await this.getBatchProgress(batchId);
        
        // Stop polling if batch is completed, failed, or cancelled
        if ([BATCH_STATUS.COMPLETED, BATCH_STATUS.FAILED, BATCH_STATUS.CANCELLED].includes(progress.status)) {
          clearInterval(intervalId);
        }
        
      } catch (error) {
        console.error('Error polling batch progress:', error);
        clearInterval(intervalId);
      }
    };

    const intervalId = setInterval(pollProgress, interval);

    // Return stop function
    return () => clearInterval(intervalId);
  }

  /**
   * Get status color for UI
   * @param {string} status - Batch or job status
   * @returns {string} Color name
   */
  getStatusColor(status) {
    switch (status) {
      case BATCH_STATUS.PENDING:
      case JOB_STATUS.QUEUED:
        return 'warning';
      case BATCH_STATUS.PROCESSING:
      case JOB_STATUS.PROCESSING:
        return 'info';
      case BATCH_STATUS.COMPLETED:
      case JOB_STATUS.COMPLETED:
        return 'success';
      case BATCH_STATUS.FAILED:
      case JOB_STATUS.FAILED:
        return 'error';
      case BATCH_STATUS.CANCELLED:
      case JOB_STATUS.SKIPPED:
        return 'secondary';
      default:
        return 'default';
    }
  }

  /**
   * Get local batch info
   * @param {string} batchId - Batch ID
   * @returns {Object|null} Local batch information
   */
  getLocalBatchInfo(batchId) {
    return this.activeBatches.get(batchId) || null;
  }
}

export default new BatchUploadService();