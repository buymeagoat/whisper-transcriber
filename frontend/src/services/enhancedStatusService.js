/**
 * T029 Enhanced User Experience: Enhanced Status Service
 * Comprehensive status tracking with real-time updates and progress monitoring
 */

class EnhancedStatusService {
  constructor() {
    this.statusSubscribers = new Map();
    this.jobStatuses = new Map();
    this.batchStatuses = new Map();
    this.systemStatus = {
      health: 'healthy',
      load: 0,
      queueSize: 0,
      activeJobs: 0,
      totalProcessed: 0,
      averageProcessingTime: 0,
      lastUpdated: new Date()
    };
    
    this.progressStages = {
      'uploading': { order: 1, label: 'Uploading', description: 'Transferring file to server' },
      'queued': { order: 2, label: 'Queued', description: 'Waiting in processing queue' },
      'preprocessing': { order: 3, label: 'Preprocessing', description: 'Preparing audio for transcription' },
      'transcribing': { order: 4, label: 'Transcribing', description: 'Converting speech to text' },
      'postprocessing': { order: 5, label: 'Postprocessing', description: 'Formatting and finalizing results' },
      'completed': { order: 6, label: 'Completed', description: 'Transcription finished successfully' },
      'failed': { order: 0, label: 'Failed', description: 'Processing encountered an error' },
      'cancelled': { order: 0, label: 'Cancelled', description: 'Processing was cancelled' }
    };

    this.wsConnection = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    
    this.initializeWebSocket();
    this.setupPeriodicUpdates();
  }

  /**
   * Initialize WebSocket connection for real-time status updates
   */
  initializeWebSocket() {
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/status`;
      
      this.wsConnection = new WebSocket(wsUrl);
      
      this.wsConnection.onopen = () => {
        console.log('Status WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifySubscribers('system', { type: 'connection', status: 'connected' });
      };
      
      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleStatusUpdate(data);
        } catch (error) {
          console.error('Error parsing status message:', error);
        }
      };
      
      this.wsConnection.onclose = () => {
        console.log('Status WebSocket disconnected');
        this.notifySubscribers('system', { type: 'connection', status: 'disconnected' });
        this.attemptReconnect();
      };
      
      this.wsConnection.onerror = (error) => {
        console.error('Status WebSocket error:', error);
        this.notifySubscribers('system', { type: 'connection', status: 'error', error });
      };
    } catch (error) {
      console.error('Failed to initialize status WebSocket:', error);
    }
  }

  /**
   * Attempt to reconnect WebSocket
   */
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Attempting to reconnect status WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.initializeWebSocket();
      }, delay);
    }
  }

  /**
   * Handle incoming status updates
   */
  handleStatusUpdate(data) {
    switch (data.type) {
      case 'job_status':
        this.updateJobStatus(data.jobId, data.status);
        break;
      case 'job_progress':
        this.updateJobProgress(data.jobId, data.progress);
        break;
      case 'batch_status':
        this.updateBatchStatus(data.batchId, data.status);
        break;
      case 'system_status':
        this.updateSystemStatus(data.status);
        break;
      case 'queue_update':
        this.updateQueueStatus(data.queue);
        break;
      default:
        console.warn('Unknown status update type:', data.type);
    }
  }

  /**
   * Setup periodic status updates as fallback
   */
  setupPeriodicUpdates() {
    // Update system status every 30 seconds
    setInterval(() => {
      this.fetchSystemStatus();
    }, 30000);

    // Update job statuses every 10 seconds
    setInterval(() => {
      this.fetchActiveJobStatuses();
    }, 10000);
  }

  /**
   * Subscribe to status updates
   */
  subscribe(id, callback) {
    if (!this.statusSubscribers.has(id)) {
      this.statusSubscribers.set(id, new Set());
    }
    this.statusSubscribers.get(id).add(callback);

    // Return unsubscribe function
    return () => {
      const subscribers = this.statusSubscribers.get(id);
      if (subscribers) {
        subscribers.delete(callback);
        if (subscribers.size === 0) {
          this.statusSubscribers.delete(id);
        }
      }
    };
  }

  /**
   * Notify subscribers of status changes
   */
  notifySubscribers(id, data) {
    const subscribers = this.statusSubscribers.get(id);
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in status subscriber callback:', error);
        }
      });
    }

    // Also notify global subscribers
    const globalSubscribers = this.statusSubscribers.get('*');
    if (globalSubscribers) {
      globalSubscribers.forEach(callback => {
        try {
          callback({ id, ...data });
        } catch (error) {
          console.error('Error in global status subscriber callback:', error);
        }
      });
    }
  }

  /**
   * Update job status
   */
  updateJobStatus(jobId, statusData) {
    const currentStatus = this.jobStatuses.get(jobId) || {};
    const updatedStatus = {
      ...currentStatus,
      ...statusData,
      lastUpdated: new Date(),
      stage: statusData.stage || currentStatus.stage,
      progress: statusData.progress !== undefined ? statusData.progress : currentStatus.progress
    };

    this.jobStatuses.set(jobId, updatedStatus);
    this.notifySubscribers(jobId, updatedStatus);
    this.notifySubscribers('jobs', { jobId, status: updatedStatus });
  }

  /**
   * Update job progress
   */
  updateJobProgress(jobId, progressData) {
    const currentStatus = this.jobStatuses.get(jobId) || {};
    const updatedStatus = {
      ...currentStatus,
      progress: progressData.percentage || 0,
      stage: progressData.stage || currentStatus.stage,
      estimatedTimeRemaining: progressData.estimatedTimeRemaining,
      processingSpeed: progressData.processingSpeed,
      lastUpdated: new Date()
    };

    this.jobStatuses.set(jobId, updatedStatus);
    this.notifySubscribers(jobId, updatedStatus);
  }

  /**
   * Update batch status
   */
  updateBatchStatus(batchId, statusData) {
    const currentStatus = this.batchStatuses.get(batchId) || {};
    const updatedStatus = {
      ...currentStatus,
      ...statusData,
      lastUpdated: new Date()
    };

    this.batchStatuses.set(batchId, updatedStatus);
    this.notifySubscribers(batchId, updatedStatus);
    this.notifySubscribers('batches', { batchId, status: updatedStatus });
  }

  /**
   * Update system status
   */
  updateSystemStatus(statusData) {
    this.systemStatus = {
      ...this.systemStatus,
      ...statusData,
      lastUpdated: new Date()
    };

    this.notifySubscribers('system', this.systemStatus);
  }

  /**
   * Update queue status
   */
  updateQueueStatus(queueData) {
    this.systemStatus.queueSize = queueData.size || 0;
    this.systemStatus.queuePosition = queueData.position;
    this.systemStatus.estimatedWaitTime = queueData.estimatedWaitTime;

    this.notifySubscribers('queue', queueData);
    this.notifySubscribers('system', this.systemStatus);
  }

  /**
   * Get job status
   */
  getJobStatus(jobId) {
    return this.jobStatuses.get(jobId) || null;
  }

  /**
   * Get batch status
   */
  getBatchStatus(batchId) {
    return this.batchStatuses.get(batchId) || null;
  }

  /**
   * Get system status
   */
  getSystemStatus() {
    return { ...this.systemStatus };
  }

  /**
   * Get all active jobs
   */
  getActiveJobs() {
    const activeJobs = new Map();
    
    for (const [jobId, status] of this.jobStatuses) {
      if (status.stage && !['completed', 'failed', 'cancelled'].includes(status.stage)) {
        activeJobs.set(jobId, status);
      }
    }
    
    return activeJobs;
  }

  /**
   * Calculate progress percentage for a stage
   */
  calculateStageProgress(stage, stageProgress = 0) {
    const stageInfo = this.progressStages[stage];
    if (!stageInfo) return 0;

    const totalStages = Object.values(this.progressStages)
      .filter(s => s.order > 0)
      .length;
    
    const stageWeight = 100 / totalStages;
    const completedStages = Math.max(0, stageInfo.order - 1);
    
    return (completedStages * stageWeight) + (stageProgress * stageWeight / 100);
  }

  /**
   * Get progress info for a job
   */
  getJobProgressInfo(jobId) {
    const status = this.getJobStatus(jobId);
    if (!status) return null;

    const stageInfo = this.progressStages[status.stage] || {};
    const overallProgress = this.calculateStageProgress(status.stage, status.progress);

    return {
      jobId,
      stage: status.stage,
      stageLabel: stageInfo.label || 'Unknown',
      stageDescription: stageInfo.description || '',
      stageProgress: status.progress || 0,
      overallProgress,
      estimatedTimeRemaining: status.estimatedTimeRemaining,
      processingSpeed: status.processingSpeed,
      queuePosition: status.queuePosition,
      startTime: status.startTime,
      lastUpdated: status.lastUpdated
    };
  }

  /**
   * Get queue position for a job
   */
  getQueuePosition(jobId) {
    const status = this.getJobStatus(jobId);
    return status?.queuePosition || null;
  }

  /**
   * Estimate completion time
   */
  estimateCompletionTime(jobId) {
    const status = this.getJobStatus(jobId);
    if (!status || !status.estimatedTimeRemaining) return null;

    const now = new Date();
    const completionTime = new Date(now.getTime() + status.estimatedTimeRemaining * 1000);
    
    return {
      estimatedCompletion: completionTime,
      remainingSeconds: status.estimatedTimeRemaining,
      remainingFormatted: this.formatDuration(status.estimatedTimeRemaining)
    };
  }

  /**
   * Format duration in seconds to human readable string
   */
  formatDuration(seconds) {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
  }

  /**
   * Fetch system status from API
   */
  async fetchSystemStatus() {
    try {
      const response = await fetch('/api/status/system');
      if (response.ok) {
        const statusData = await response.json();
        this.updateSystemStatus(statusData);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  }

  /**
   * Fetch active job statuses from API
   */
  async fetchActiveJobStatuses() {
    try {
      const response = await fetch('/api/status/jobs/active');
      if (response.ok) {
        const jobsData = await response.json();
        jobsData.forEach(job => {
          this.updateJobStatus(job.id, job);
        });
      }
    } catch (error) {
      console.error('Error fetching job statuses:', error);
    }
  }

  /**
   * Start tracking a new job
   */
  startJobTracking(jobId, initialStatus = {}) {
    const status = {
      stage: 'uploading',
      progress: 0,
      startTime: new Date(),
      ...initialStatus
    };
    
    this.updateJobStatus(jobId, status);
    return status;
  }

  /**
   * Stop tracking a job
   */
  stopJobTracking(jobId) {
    this.jobStatuses.delete(jobId);
    this.notifySubscribers(jobId, { removed: true });
  }

  /**
   * Get comprehensive status summary
   */
  getStatusSummary() {
    const activeJobs = this.getActiveJobs();
    const jobArray = Array.from(activeJobs.values());
    
    return {
      system: this.getSystemStatus(),
      activeJobsCount: activeJobs.size,
      activeJobs: jobArray,
      totalJobsTracked: this.jobStatuses.size,
      batchesTracked: this.batchStatuses.size,
      connectionStatus: this.wsConnection?.readyState === WebSocket.OPEN ? 'connected' : 'disconnected'
    };
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    if (this.wsConnection) {
      this.wsConnection.close();
    }
    
    this.statusSubscribers.clear();
    this.jobStatuses.clear();
    this.batchStatuses.clear();
  }
}

// Create singleton instance
const enhancedStatusService = new EnhancedStatusService();

export default enhancedStatusService;