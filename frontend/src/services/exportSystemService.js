/**
 * Frontend service for T034 Multi-Format Export System
 * 
 * Provides comprehensive API integration for export operations including:
 * - Format and template management
 * - Individual and batch export operations
 * - Export history and progress tracking
 * - File downloads and status monitoring
 */

import axios from 'axios';

class ExportSystemService {
  constructor() {
    this.baseURL = '/api/exports';
  }

  // Export Format Operations
  async getAvailableFormats() {
    try {
      const response = await axios.get(`${this.baseURL}/formats`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch export formats:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch export formats');
    }
  }

  async getFormatDetails(format) {
    try {
      const response = await axios.get(`${this.baseURL}/formats/${format}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch format details for ${format}:`, error);
      throw new Error(error.response?.data?.detail || `Failed to fetch format details`);
    }
  }

  // Template Operations
  async getTemplates(formatFilter = null, systemOnly = false) {
    try {
      const params = new URLSearchParams();
      if (formatFilter) params.append('format_filter', formatFilter);
      if (systemOnly) params.append('system_only', 'true');
      
      const response = await axios.get(`${this.baseURL}/templates?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch templates');
    }
  }

  async getTemplate(templateId) {
    try {
      const response = await axios.get(`${this.baseURL}/templates/${templateId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch template ${templateId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch template');
    }
  }

  async createTemplate(templateData) {
    try {
      const response = await axios.post(`${this.baseURL}/templates`, templateData);
      return response.data;
    } catch (error) {
      console.error('Failed to create template:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create template');
    }
  }

  async deleteTemplate(templateId) {
    try {
      const response = await axios.delete(`${this.baseURL}/templates/${templateId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to delete template ${templateId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to delete template');
    }
  }

  // Individual Export Job Operations
  async createExportJob(exportData) {
    try {
      const response = await axios.post(`${this.baseURL}/jobs`, exportData);
      return response.data;
    } catch (error) {
      console.error('Failed to create export job:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create export job');
    }
  }

  async getExportJob(exportJobId) {
    try {
      const response = await axios.get(`${this.baseURL}/jobs/${exportJobId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch export job ${exportJobId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch export job');
    }
  }

  async getUserExportJobs(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.statusFilter) params.append('status_filter', options.statusFilter);
      if (options.formatFilter) params.append('format_filter', options.formatFilter);
      if (options.page) params.append('page', options.page);
      if (options.pageSize) params.append('page_size', options.pageSize);
      
      const response = await axios.get(`${this.baseURL}/jobs?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user export jobs:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch export jobs');
    }
  }

  async downloadExport(exportJobId) {
    try {
      const response = await axios.get(`${this.baseURL}/jobs/${exportJobId}/download`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      // Get filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'export';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      return { success: true, filename };
    } catch (error) {
      console.error(`Failed to download export ${exportJobId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to download export');
    }
  }

  // Batch Export Operations
  async createBatchExport(batchData) {
    try {
      const response = await axios.post(`${this.baseURL}/batch`, batchData);
      return response.data;
    } catch (error) {
      console.error('Failed to create batch export:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create batch export');
    }
  }

  async getBatchExport(batchExportId) {
    try {
      const response = await axios.get(`${this.baseURL}/batch/${batchExportId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch batch export ${batchExportId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch batch export');
    }
  }

  async getUserBatchExports(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.statusFilter) params.append('status_filter', options.statusFilter);
      if (options.formatFilter) params.append('format_filter', options.formatFilter);
      if (options.page) params.append('page', options.page);
      if (options.pageSize) params.append('page_size', options.pageSize);
      
      const response = await axios.get(`${this.baseURL}/batch?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user batch exports:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch batch exports');
    }
  }

  async downloadBatchExport(batchExportId) {
    try {
      const response = await axios.get(`${this.baseURL}/batch/${batchExportId}/download`, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      // Get filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'batch_export.zip';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      return { success: true, filename };
    } catch (error) {
      console.error(`Failed to download batch export ${batchExportId}:`, error);
      throw new Error(error.response?.data?.detail || 'Failed to download batch export');
    }
  }

  // Export History Operations
  async getExportHistory(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.exportType) params.append('export_type', options.exportType);
      if (options.formatFilter) params.append('format_filter', options.formatFilter);
      if (options.successOnly) params.append('success_only', 'true');
      if (options.page) params.append('page', options.page);
      if (options.pageSize) params.append('page_size', options.pageSize);
      
      const response = await axios.get(`${this.baseURL}/history?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch export history:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch export history');
    }
  }

  // Admin Operations (require admin privileges)
  async getExportStatistics() {
    try {
      const response = await axios.get(`${this.baseURL}/admin/stats`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch export statistics:', error);
      throw new Error(error.response?.data?.detail || 'Failed to fetch export statistics');
    }
  }

  async createDefaultTemplates() {
    try {
      const response = await axios.post(`${this.baseURL}/admin/templates/create-defaults`);
      return response.data;
    } catch (error) {
      console.error('Failed to create default templates:', error);
      throw new Error(error.response?.data?.detail || 'Failed to create default templates');
    }
  }

  async cleanupExpiredExports() {
    try {
      const response = await axios.delete(`${this.baseURL}/admin/cleanup-expired`);
      return response.data;
    } catch (error) {
      console.error('Failed to cleanup expired exports:', error);
      throw new Error(error.response?.data?.detail || 'Failed to cleanup expired exports');
    }
  }

  // Utility Methods
  getStatusColor(status) {
    const statusColors = {
      pending: '#ff9800',      // orange
      processing: '#2196f3',   // blue  
      completed: '#4caf50',    // green
      failed: '#f44336',       // red
      cancelled: '#9e9e9e',    // grey
      created: '#ff9800',      // orange
      queued: '#ff9800',       // orange
      partial: '#ff5722'       // deep orange
    };
    return statusColors[status] || '#9e9e9e';
  }

  getStatusIcon(status) {
    const statusIcons = {
      pending: 'schedule',
      processing: 'autorenew',
      completed: 'check_circle',
      failed: 'error',
      cancelled: 'cancel',
      created: 'schedule',
      queued: 'queue',
      partial: 'warning'
    };
    return statusIcons[status] || 'help';
  }

  formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDuration(seconds) {
    if (!seconds) return 'N/A';
    
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes < 60) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    return `${hours}h ${remainingMinutes}m`;
  }

  formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (error) {
      return 'Invalid Date';
    }
  }

  // Mock Data for Development and Testing
  getMockFormats() {
    return [
      {
        format: 'srt',
        display_name: 'SubRip Subtitle (SRT)',
        file_extension: '.srt',
        mime_type: 'application/x-subrip',
        supports_timestamps: true,
        supports_styling: false,
        supports_metadata: false,
        max_file_size_mb: 10,
        default_config: {
          include_timestamps: true,
          timestamp_format: 'HH:MM:SS,mmm',
          line_breaks: '\\n',
          max_line_length: 80,
          speaker_labels: false
        }
      },
      {
        format: 'vtt',
        display_name: 'WebVTT Subtitle',
        file_extension: '.vtt',
        mime_type: 'text/vtt',
        supports_timestamps: true,
        supports_styling: true,
        supports_metadata: false,
        max_file_size_mb: 10,
        default_config: {
          include_timestamps: true,
          timestamp_format: 'HH:MM:SS.mmm',
          line_breaks: '\\n',
          max_line_length: 80,
          speaker_labels: true,
          include_header: true,
          header_text: 'WEBVTT'
        }
      },
      {
        format: 'docx',
        display_name: 'Microsoft Word Document',
        file_extension: '.docx',
        mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        supports_timestamps: true,
        supports_styling: true,
        supports_metadata: true,
        max_file_size_mb: 25,
        default_config: {
          include_timestamps: true,
          include_metadata: true,
          paragraph_spacing: 1.15,
          show_speaker_labels: true,
          timestamp_in_margin: false
        }
      },
      {
        format: 'pdf',
        display_name: 'Portable Document Format (PDF)',
        file_extension: '.pdf',
        mime_type: 'application/pdf',
        supports_timestamps: true,
        supports_styling: true,
        supports_metadata: true,
        max_file_size_mb: 25,
        default_config: {
          include_timestamps: true,
          include_metadata: true,
          show_speaker_labels: true,
          page_size: 'letter',
          font_family: 'Helvetica',
          font_size: 11
        }
      },
      {
        format: 'json',
        display_name: 'JSON Structured Data',
        file_extension: '.json',
        mime_type: 'application/json',
        supports_timestamps: true,
        supports_styling: false,
        supports_metadata: true,
        max_file_size_mb: 50,
        default_config: {
          include_metadata: true,
          include_timestamps: true,
          segment_level: 'sentence',
          include_confidence: true,
          include_speaker_info: true,
          pretty_print: true
        }
      },
      {
        format: 'txt',
        display_name: 'Plain Text',
        file_extension: '.txt',
        mime_type: 'text/plain',
        supports_timestamps: true,
        supports_styling: false,
        supports_metadata: true,
        max_file_size_mb: 10,
        default_config: {
          include_timestamps: true,
          include_metadata: true,
          show_speaker_labels: true,
          line_spacing: 'single'
        }
      }
    ];
  }

  getMockTemplates() {
    return [
      {
        id: 1,
        name: 'Standard SRT',
        description: 'Default SRT subtitle template with timestamps',
        template_type: 'subtitle',
        supported_formats: ['srt'],
        template_config: {
          include_timestamps: true,
          timestamp_format: 'HH:MM:SS,mmm',
          line_breaks: '\\n',
          max_line_length: 80,
          speaker_labels: false
        },
        styling_config: null,
        layout_config: null,
        created_by: 'system',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: null,
        is_system_template: true,
        is_active: true,
        usage_count: 42,
        last_used_at: '2025-01-15T10:30:00Z'
      },
      {
        id: 2,
        name: 'Enhanced WebVTT',
        description: 'WebVTT template with speaker styling',
        template_type: 'subtitle',
        supported_formats: ['vtt'],
        template_config: {
          include_timestamps: true,
          timestamp_format: 'HH:MM:SS.mmm',
          speaker_labels: true,
          include_header: true,
          header_text: 'WEBVTT\\n\\nNOTE Enhanced template with speaker styling'
        },
        styling_config: {
          speaker_color: '#0066cc',
          text_color: '#333333'
        },
        layout_config: null,
        created_by: 'admin',
        created_at: '2025-01-02T00:00:00Z',
        updated_at: '2025-01-10T15:45:00Z',
        is_system_template: false,
        is_active: true,
        usage_count: 23,
        last_used_at: '2025-01-14T14:20:00Z'
      }
    ];
  }

  getMockExportJobs() {
    return [
      {
        id: 1,
        job_id: 'job_123',
        batch_export_id: null,
        format: 'srt',
        template_id: 1,
        custom_config: null,
        status: 'completed',
        progress_percentage: 100.0,
        output_filename: 'transcript_job_123.srt',
        output_path: '/exports/1/transcript_job_123.srt',
        output_url: '/api/exports/jobs/1/download',
        output_size_bytes: 2048,
        processing_started_at: '2025-01-15T10:00:00Z',
        processing_completed_at: '2025-01-15T10:00:45Z',
        processing_duration_seconds: 45.2,
        error_message: null,
        retry_count: 0,
        max_retries: 3,
        created_by: 'user123',
        created_at: '2025-01-15T10:00:00Z',
        expires_at: '2025-01-22T10:00:00Z'
      },
      {
        id: 2,
        job_id: 'job_124',
        batch_export_id: null,
        format: 'pdf',
        template_id: null,
        custom_config: { include_metadata: true },
        status: 'processing',
        progress_percentage: 65.0,
        output_filename: null,
        output_path: null,
        output_url: null,
        output_size_bytes: null,
        processing_started_at: '2025-01-15T10:05:00Z',
        processing_completed_at: null,
        processing_duration_seconds: null,
        error_message: null,
        retry_count: 0,
        max_retries: 3,
        created_by: 'user123',
        created_at: '2025-01-15T10:05:00Z',
        expires_at: '2025-01-22T10:05:00Z'
      }
    ];
  }

  getMockBatchExports() {
    return [
      {
        id: 1,
        name: 'Weekly Transcripts Export',
        description: 'All transcripts from this week in SRT format',
        export_format: 'srt',
        template_id: 1,
        batch_config: { include_timestamps: true },
        job_ids: ['job_123', 'job_124', 'job_125'],
        filter_criteria: null,
        status: 'completed',
        total_jobs: 3,
        completed_jobs: 3,
        failed_jobs: 0,
        progress_percentage: 100.0,
        archive_filename: 'weekly_transcripts_srt_batch.zip',
        archive_path: '/exports/batches/1/weekly_transcripts_srt_batch.zip',
        archive_size_bytes: 15360,
        download_url: '/api/exports/batch/1/download',
        started_at: '2025-01-15T09:00:00Z',
        completed_at: '2025-01-15T09:05:30Z',
        processing_duration_seconds: 330.5,
        error_message: null,
        partial_success: false,
        created_by: 'user123',
        created_at: '2025-01-15T09:00:00Z',
        expires_at: '2025-01-29T09:00:00Z'
      }
    ];
  }

  getMockExportHistory() {
    return [
      {
        id: 1,
        export_job_id: 1,
        batch_export_id: null,
        export_type: 'single',
        format: 'srt',
        template_name: 'Standard SRT',
        user_id: 'user123',
        user_email: 'user@example.com',
        processing_time_seconds: 45.2,
        output_size_bytes: 2048,
        job_count: 1,
        success: true,
        error_type: null,
        error_details: null,
        exported_at: '2025-01-15T10:00:45Z',
        downloaded_at: '2025-01-15T10:15:00Z'
      },
      {
        id: 2,
        export_job_id: null,
        batch_export_id: 1,
        export_type: 'batch',
        format: 'srt',
        template_name: 'Standard SRT',
        user_id: 'user123',
        user_email: 'user@example.com',
        processing_time_seconds: 330.5,
        output_size_bytes: 15360,
        job_count: 3,
        success: true,
        error_type: null,
        error_details: null,
        exported_at: '2025-01-15T09:05:30Z',
        downloaded_at: null
      }
    ];
  }
}

// Create and export singleton instance
const exportSystemService = new ExportSystemService();
export { exportSystemService };