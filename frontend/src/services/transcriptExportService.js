/**
 * T022: Multi-Format Export System - Frontend Service
 * 
 * Service for handling transcript export functionality including
 * format selection, template management, and download operations.
 */

import apiClient from './apiClient';

/**
 * Export format information
 */
export const EXPORT_FORMATS = {
  SRT: { id: 'srt', name: 'SubRip (.srt)', description: 'Standard subtitle format' },
  VTT: { id: 'vtt', name: 'WebVTT (.vtt)', description: 'Web video text tracks' },
  DOCX: { id: 'docx', name: 'Word Document (.docx)', description: 'Microsoft Word format' },
  PDF: { id: 'pdf', name: 'PDF Document (.pdf)', description: 'Portable document format' },
  JSON: { id: 'json', name: 'JSON Data (.json)', description: 'Machine-readable format' },
  TXT: { id: 'txt', name: 'Plain Text (.txt)', description: 'Simple text format' }
};

/**
 * Default export options
 */
export const DEFAULT_EXPORT_OPTIONS = {
  include_header: true,
  include_footer: true,
  word_wrap: 80,
  font_size: 12,
  font_family: 'Arial',
  line_spacing: 1.5,
  page_margins: {
    top: 1.0,
    bottom: 1.0,
    left: 1.0,
    right: 1.0
  }
};

class TranscriptExportService {
  constructor() {
    this.baseUrl = '/api/export';
    this.cache = new Map();
    this.cacheTTL = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get available export formats
   */
  async getAvailableFormats() {
    const cacheKey = 'formats';
    const cached = this._getFromCache(cacheKey);
    if (cached) return cached;

    try {
      const response = await apiClient.get(`${this.baseUrl}/formats`);
      const formats = response.data;
      this._setCache(cacheKey, formats);
      return formats;
    } catch (error) {
      console.error('Error fetching export formats:', error);
      throw new Error('Failed to fetch export formats');
    }
  }

  /**
   * Get available export templates
   */
  async getExportTemplates(format = null) {
    const cacheKey = `templates_${format || 'all'}`;
    const cached = this._getFromCache(cacheKey);
    if (cached) return cached;

    try {
      const params = format ? { format } : {};
      const response = await apiClient.get(`${this.baseUrl}/templates`, { params });
      const templates = response.data;
      this._setCache(cacheKey, templates);
      return templates;
    } catch (error) {
      console.error('Error fetching export templates:', error);
      throw new Error('Failed to fetch export templates');
    }
  }

  /**
   * Export a single transcript
   */
  async exportTranscript(jobId, format, options = {}) {
    try {
      const exportData = {
        job_id: jobId,
        format: format.toLowerCase(),
        template_name: options.template,
        custom_filename: options.filename,
        options: {
          ...DEFAULT_EXPORT_OPTIONS,
          ...options.customOptions
        }
      };

      const response = await apiClient.post(`${this.baseUrl}/export`, exportData);
      return response.data;
    } catch (error) {
      console.error('Error exporting transcript:', error);
      throw new Error(error.response?.data?.detail || 'Export failed');
    }
  }

  /**
   * Download exported file
   */
  async downloadExport(jobId, format, options = {}) {
    try {
      const params = {};
      if (options.template) {
        params.template = options.template;
      }

      const response = await apiClient.get(
        `${this.baseUrl}/download/${jobId}/${format.toLowerCase()}`,
        {
          params,
          responseType: 'blob'
        }
      );

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = `transcript_${jobId}.${format.toLowerCase()}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return { success: true, filename };
    } catch (error) {
      console.error('Error downloading export:', error);
      throw new Error(error.response?.data?.detail || 'Download failed');
    }
  }

  /**
   * Export multiple transcripts in batch
   */
  async batchExport(jobIds, format, options = {}) {
    try {
      const batchData = {
        job_ids: jobIds,
        format: format.toLowerCase(),
        template_name: options.template,
        zip_filename: options.zipFilename
      };

      const response = await apiClient.post(`${this.baseUrl}/batch`, batchData);
      return response.data;
    } catch (error) {
      console.error('Error in batch export:', error);
      throw new Error(error.response?.data?.detail || 'Batch export failed');
    }
  }

  /**
   * Preview export format
   */
  async previewExport(jobId, format, options = {}) {
    try {
      const params = {
        lines: options.previewLines || 10
      };
      
      if (options.template) {
        params.template = options.template;
      }

      const response = await apiClient.get(
        `${this.baseUrl}/preview/${jobId}/${format.toLowerCase()}`,
        { params }
      );
      
      return response.data;
    } catch (error) {
      console.error('Error generating preview:', error);
      throw new Error(error.response?.data?.detail || 'Preview generation failed');
    }
  }

  /**
   * Get export statistics
   */
  async getExportStats() {
    try {
      const response = await apiClient.get(`${this.baseUrl}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching export stats:', error);
      throw new Error('Failed to fetch export statistics');
    }
  }

  /**
   * Validate export options
   */
  validateExportOptions(format, options = {}) {
    const errors = [];

    // Validate format
    if (!format) {
      errors.push('Export format is required');
    } else if (!Object.values(EXPORT_FORMATS).some(f => f.id === format.toLowerCase())) {
      errors.push('Invalid export format');
    }

    // Validate filename if provided
    if (options.filename && !/^[\w\-. ]+$/.test(options.filename)) {
      errors.push('Filename contains invalid characters');
    }

    // Validate custom options
    if (options.customOptions) {
      const { font_size, word_wrap, line_spacing } = options.customOptions;
      
      if (font_size && (font_size < 8 || font_size > 24)) {
        errors.push('Font size must be between 8 and 24');
      }
      
      if (word_wrap && (word_wrap < 40 || word_wrap > 120)) {
        errors.push('Word wrap must be between 40 and 120 characters');
      }
      
      if (line_spacing && (line_spacing < 1.0 || line_spacing > 3.0)) {
        errors.push('Line spacing must be between 1.0 and 3.0');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
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
   * Get format icon for UI display
   */
  getFormatIcon(format) {
    const icons = {
      srt: '📝',
      vtt: '🎬',
      docx: '📄',
      pdf: '📕',
      json: '🔧',
      txt: '📃'
    };
    
    return icons[format.toLowerCase()] || '📄';
  }

  /**
   * Get format color for UI styling
   */
  getFormatColor(format) {
    const colors = {
      srt: '#4CAF50',
      vtt: '#2196F3',
      docx: '#2E7D32',
      pdf: '#F44336',
      json: '#FF9800',
      txt: '#9E9E9E'
    };
    
    return colors[format.toLowerCase()] || '#9E9E9E';
  }

  /**
   * Check if format requires additional dependencies
   */
  isFormatAvailable(formatInfo) {
    return formatInfo.available && formatInfo.requires.length === 0;
  }

  /**
   * Generate export filename suggestion
   */
  generateFilename(originalFilename, format, includeTimestamp = true) {
    const baseName = originalFilename.replace(/\.[^/.]+$/, '');
    const timestamp = includeTimestamp ? `_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}` : '';
    return `${baseName}_transcript${timestamp}.${format.toLowerCase()}`;
  }

  /**
   * Cache management methods
   */
  _getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  _setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clearCache() {
    this.cache.clear();
  }
}

export default new TranscriptExportService();