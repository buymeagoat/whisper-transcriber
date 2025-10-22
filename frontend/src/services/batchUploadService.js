/**
 * T028 Frontend Implementation: Batch Upload Service
 * Client-side service for handling batch transcription operations
 */

import apiClient from './apiClient';

class BatchUploadService {
  constructor() {
    this.uploadProgress = new Map();
    this.batchJobs = new Map();
    this.progressCallbacks = new Map();
  }

  /**
   * Submit a batch of files for transcription
   */
  async submitBatch(files, options = {}) {
    try {
      const formData = new FormData();
      
      // Add files to form data
      files.forEach((file, index) => {
        formData.append('files', file);
      });

      // Add batch options
      if (options.model) formData.append('model', options.model);
      if (options.language) formData.append('language', options.language);
      if (options.batch_name) formData.append('batch_name', options.batch_name);
      if (options.priority) formData.append('priority', options.priority);
      if (options.callback_url) formData.append('callback_url', options.callback_url);

      // Submit batch with progress tracking
      const response = await apiClient.post('/api/v1/batches', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          this.updateUploadProgress('batch_upload', progress);
        }
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to submit batch'
      };
    }
  }

  /**
   * Get all user's batch jobs
   */
  async getUserBatches() {
    try {
      const response = await apiClient.get('/api/v1/batches');
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
   * Get specific batch details and job statuses
   */
  async getBatchDetails(batchId) {
    try {
      const response = await apiClient.get(`/api/v1/batches/${batchId}`);
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
   * Cancel a batch job
   */
  async cancelBatch(batchId) {
    try {
      const response = await apiClient.post(`/api/v1/batches/${batchId}/cancel`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to cancel batch'
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
   * Validate files before batch upload
   */
  validateFiles(files) {
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
}

export default new BatchUploadService();