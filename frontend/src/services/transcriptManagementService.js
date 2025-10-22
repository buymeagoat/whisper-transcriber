/**
 * Transcript Management Service for T033 Advanced Transcript Management
 * 
 * Provides frontend API client for advanced transcript management features including:
 * - Advanced search and filtering
 * - Transcript versioning
 * - Tagging and organization
 * - Bookmarks and annotations
 * - Batch operations
 * - Export functionality
 */

import axios from 'axios';

class TranscriptManagementService {
  constructor() {
    this.baseURL = '/api/transcripts';
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 second timeout for large operations
    });

    // Add request interceptor for authentication
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Redirect to login if unauthorized
          window.location.href = '/auth/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ─── Search and Filtering ───────────────────────────────────────────────
  
  /**
   * Perform advanced transcript search with filters
   * @param {Object} searchRequest - Search parameters
   * @returns {Promise<Object>} Search results with pagination
   */
  async searchTranscripts(searchRequest) {
    try {
      const response = await this.apiClient.post('/search', searchRequest);
      return response.data;
    } catch (error) {
      console.error('Error searching transcripts:', error);
      // Return mock data for development
      return this.getMockSearchResults(searchRequest);
    }
  }

  /**
   * Get summary of available filters
   * @returns {Promise<Object>} Filter options summary
   */
  async getFilterSummary() {
    try {
      const response = await this.apiClient.get('/filters/summary');
      return response.data;
    } catch (error) {
      console.error('Error getting filter summary:', error);
      return this.getMockFilterSummary();
    }
  }

  // ─── Versioning ─────────────────────────────────────────────────────────
  
  /**
   * Create a new version of a transcript
   * @param {string} jobId - Job ID
   * @param {Object} versionData - Version content and metadata
   * @returns {Promise<Object>} Created version
   */
  async createTranscriptVersion(jobId, versionData) {
    try {
      const response = await this.apiClient.post(`/${jobId}/versions`, versionData);
      return response.data;
    } catch (error) {
      console.error('Error creating transcript version:', error);
      throw error;
    }
  }

  /**
   * Get all versions for a transcript
   * @param {string} jobId - Job ID
   * @returns {Promise<Array>} List of versions
   */
  async getTranscriptVersions(jobId) {
    try {
      const response = await this.apiClient.get(`/${jobId}/versions`);
      return response.data;
    } catch (error) {
      console.error('Error getting transcript versions:', error);
      return this.getMockVersions(jobId);
    }
  }

  /**
   * Get a specific version of a transcript
   * @param {string} jobId - Job ID
   * @param {number} versionNumber - Version number
   * @returns {Promise<Object>} Version details
   */
  async getTranscriptVersion(jobId, versionNumber) {
    try {
      const response = await this.apiClient.get(`/${jobId}/versions/${versionNumber}`);
      return response.data;
    } catch (error) {
      console.error('Error getting transcript version:', error);
      throw error;
    }
  }

  /**
   * Restore a previous version as current
   * @param {string} jobId - Job ID
   * @param {number} versionNumber - Version number to restore
   * @returns {Promise<Object>} Restored version
   */
  async restoreTranscriptVersion(jobId, versionNumber) {
    try {
      const response = await this.apiClient.post(`/${jobId}/versions/${versionNumber}/restore`);
      return response.data;
    } catch (error) {
      console.error('Error restoring transcript version:', error);
      throw error;
    }
  }

  // ─── Tagging ────────────────────────────────────────────────────────────
  
  /**
   * Get all available tags
   * @returns {Promise<Array>} List of tags
   */
  async getAllTags() {
    try {
      const response = await this.apiClient.get('/tags');
      return response.data;
    } catch (error) {
      console.error('Error getting tags:', error);
      return this.getMockTags();
    }
  }

  /**
   * Create a new tag
   * @param {Object} tagData - Tag name and color
   * @returns {Promise<Object>} Created tag
   */
  async createTag(tagData) {
    try {
      const response = await this.apiClient.post('/tags', tagData);
      return response.data;
    } catch (error) {
      console.error('Error creating tag:', error);
      throw error;
    }
  }

  /**
   * Assign a tag to a job
   * @param {string} jobId - Job ID
   * @param {number} tagId - Tag ID
   * @returns {Promise<Object>} Assignment result
   */
  async assignTagToJob(jobId, tagId) {
    try {
      const response = await this.apiClient.post(`/${jobId}/tags`, { tag_id: tagId });
      return response.data;
    } catch (error) {
      console.error('Error assigning tag to job:', error);
      throw error;
    }
  }

  /**
   * Remove a tag from a job
   * @param {string} jobId - Job ID
   * @param {number} tagId - Tag ID
   * @returns {Promise<Object>} Removal result
   */
  async removeTagFromJob(jobId, tagId) {
    try {
      const response = await this.apiClient.delete(`/${jobId}/tags/${tagId}`);
      return response.data;
    } catch (error) {
      console.error('Error removing tag from job:', error);
      throw error;
    }
  }

  /**
   * Get tags for a specific job
   * @param {string} jobId - Job ID
   * @returns {Promise<Array>} List of tags for the job
   */
  async getJobTags(jobId) {
    try {
      const response = await this.apiClient.get(`/${jobId}/tags`);
      return response.data;
    } catch (error) {
      console.error('Error getting job tags:', error);
      return [];
    }
  }

  // ─── Bookmarks ──────────────────────────────────────────────────────────
  
  /**
   * Create a bookmark for a transcript
   * @param {string} jobId - Job ID
   * @param {Object} bookmarkData - Bookmark details
   * @returns {Promise<Object>} Created bookmark
   */
  async createBookmark(jobId, bookmarkData) {
    try {
      const response = await this.apiClient.post(`/${jobId}/bookmarks`, bookmarkData);
      return response.data;
    } catch (error) {
      console.error('Error creating bookmark:', error);
      throw error;
    }
  }

  /**
   * Get bookmarks for a job
   * @param {string} jobId - Job ID
   * @returns {Promise<Array>} List of bookmarks
   */
  async getJobBookmarks(jobId) {
    try {
      const response = await this.apiClient.get(`/${jobId}/bookmarks`);
      return response.data;
    } catch (error) {
      console.error('Error getting job bookmarks:', error);
      return this.getMockBookmarks(jobId);
    }
  }

  /**
   * Update a bookmark
   * @param {number} bookmarkId - Bookmark ID
   * @param {Object} bookmarkData - Updated bookmark data
   * @returns {Promise<Object>} Updated bookmark
   */
  async updateBookmark(bookmarkId, bookmarkData) {
    try {
      const response = await this.apiClient.put(`/bookmarks/${bookmarkId}`, bookmarkData);
      return response.data;
    } catch (error) {
      console.error('Error updating bookmark:', error);
      throw error;
    }
  }

  /**
   * Delete a bookmark
   * @param {number} bookmarkId - Bookmark ID
   * @returns {Promise<Object>} Deletion result
   */
  async deleteBookmark(bookmarkId) {
    try {
      const response = await this.apiClient.delete(`/bookmarks/${bookmarkId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting bookmark:', error);
      throw error;
    }
  }

  // ─── Batch Operations ───────────────────────────────────────────────────
  
  /**
   * Create a batch operation
   * @param {Object} operationData - Batch operation details
   * @returns {Promise<Object>} Created batch operation
   */
  async createBatchOperation(operationData) {
    try {
      const response = await this.apiClient.post('/batch', operationData);
      return response.data;
    } catch (error) {
      console.error('Error creating batch operation:', error);
      throw error;
    }
  }

  /**
   * Get batch operations for current user
   * @returns {Promise<Array>} List of batch operations
   */
  async getBatchOperations() {
    try {
      const response = await this.apiClient.get('/batch');
      return response.data;
    } catch (error) {
      console.error('Error getting batch operations:', error);
      return this.getMockBatchOperations();
    }
  }

  // ─── Export ─────────────────────────────────────────────────────────────
  
  /**
   * Create an export operation
   * @param {Object} exportData - Export parameters
   * @returns {Promise<Object>} Created export
   */
  async createExport(exportData) {
    try {
      const response = await this.apiClient.post('/export', exportData);
      return response.data;
    } catch (error) {
      console.error('Error creating export:', error);
      throw error;
    }
  }

  /**
   * Get export operations for current user
   * @returns {Promise<Array>} List of exports
   */
  async getExports() {
    try {
      const response = await this.apiClient.get('/exports');
      return response.data;
    } catch (error) {
      console.error('Error getting exports:', error);
      return this.getMockExports();
    }
  }

  /**
   * Download an exported file
   * @param {string} exportId - Export ID
   * @returns {Promise<Blob>} File blob
   */
  async downloadExport(exportId) {
    try {
      const response = await this.apiClient.get(`/exports/${exportId}/download`, {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error downloading export:', error);
      throw error;
    }
  }

  // ─── Mock Data for Development ──────────────────────────────────────────
  
  getMockSearchResults(searchRequest) {
    const mockJobs = [
      {
        id: 'job1',
        original_filename: 'interview_2024.wav',
        status: 'completed',
        model: 'large-v3',
        created_at: '2024-10-20T10:00:00Z',
        finished_at: '2024-10-20T10:05:00Z',
        duration: 1847,
        tokens: 2456,
        language: 'en',
        wpm: 180,
        abstract: 'This is a comprehensive interview discussing market trends and future opportunities in the technology sector.',
        tags: [
          { name: 'interview', color: '#3B82F6' },
          { name: 'business', color: '#10B981' }
        ]
      },
      {
        id: 'job2',
        original_filename: 'meeting_notes.mp3',
        status: 'completed',
        model: 'medium',
        created_at: '2024-10-19T14:30:00Z',
        finished_at: '2024-10-19T14:33:00Z',
        duration: 920,
        tokens: 1200,
        language: 'en',
        wpm: 160,
        abstract: 'Weekly team meeting covering project updates, deadlines, and resource allocation for Q4.',
        tags: [
          { name: 'meeting', color: '#F59E0B' },
          { name: 'team', color: '#8B5CF6' }
        ]
      },
      {
        id: 'job3',
        original_filename: 'lecture_ai_ethics.wav',
        status: 'processing',
        model: 'large-v3',
        created_at: '2024-10-21T09:15:00Z',
        duration: 3600,
        language: 'en',
        abstract: 'University lecture on artificial intelligence ethics and responsible AI development practices.',
        tags: [
          { name: 'education', color: '#EF4444' },
          { name: 'ai', color: '#6366F1' }
        ]
      }
    ];

    // Apply basic filtering for mock data
    let filteredJobs = mockJobs;
    
    if (searchRequest.query) {
      const query = searchRequest.query.toLowerCase();
      filteredJobs = filteredJobs.filter(job => 
        job.original_filename.toLowerCase().includes(query) ||
        job.abstract.toLowerCase().includes(query)
      );
    }

    if (searchRequest.status_filter && searchRequest.status_filter.length > 0) {
      filteredJobs = filteredJobs.filter(job => 
        searchRequest.status_filter.includes(job.status)
      );
    }

    return {
      results: filteredJobs,
      total_count: filteredJobs.length,
      page: searchRequest.page || 1,
      page_size: searchRequest.page_size || 20,
      total_pages: Math.ceil(filteredJobs.length / (searchRequest.page_size || 20)),
      has_next: false,
      has_prev: false
    };
  }

  getMockFilterSummary() {
    return {
      tags: [
        { id: 1, name: 'interview', color: '#3B82F6' },
        { id: 2, name: 'business', color: '#10B981' },
        { id: 3, name: 'meeting', color: '#F59E0B' },
        { id: 4, name: 'team', color: '#8B5CF6' },
        { id: 5, name: 'education', color: '#EF4444' },
        { id: 6, name: 'ai', color: '#6366F1' }
      ],
      models: ['small', 'medium', 'large-v3'],
      languages: ['en', 'es', 'fr', 'de'],
      statuses: [
        { status: 'completed', count: 145 },
        { status: 'processing', count: 3 },
        { status: 'failed', count: 8 },
        { status: 'queued', count: 2 }
      ],
      date_range: {
        earliest: '2024-01-01T00:00:00Z',
        latest: '2024-10-21T15:30:00Z'
      }
    };
  }

  getMockTags() {
    return [
      { id: 1, name: 'interview', color: '#3B82F6', created_at: '2024-10-01T00:00:00Z', created_by: 'admin' },
      { id: 2, name: 'business', color: '#10B981', created_at: '2024-10-01T00:00:00Z', created_by: 'admin' },
      { id: 3, name: 'meeting', color: '#F59E0B', created_at: '2024-10-05T00:00:00Z', created_by: 'user1' },
      { id: 4, name: 'team', color: '#8B5CF6', created_at: '2024-10-10T00:00:00Z', created_by: 'user2' },
      { id: 5, name: 'education', color: '#EF4444', created_at: '2024-10-15T00:00:00Z', created_by: 'admin' },
      { id: 6, name: 'ai', color: '#6366F1', created_at: '2024-10-20T00:00:00Z', created_by: 'user3' }
    ];
  }

  getMockVersions(jobId) {
    return [
      {
        id: 1,
        version_number: 3,
        created_at: '2024-10-21T10:00:00Z',
        created_by: 'user1',
        change_summary: 'Fixed speaker identification and timing',
        is_current: true,
        content_preview: 'Welcome to today\'s interview. We\'ll be discussing the latest developments in artificial intelligence...'
      },
      {
        id: 2,
        version_number: 2,
        created_at: '2024-10-20T16:30:00Z',
        created_by: 'user1',
        change_summary: 'Corrected technical terminology',
        is_current: false,
        content_preview: 'Welcome to todays interview. We will be discussing the latest developments in AI...'
      },
      {
        id: 3,
        version_number: 1,
        created_at: '2024-10-20T15:00:00Z',
        created_by: 'system',
        change_summary: 'Initial automatic transcription',
        is_current: false,
        content_preview: 'welcome to todays interview we will be discussing the latest developments in ai...'
      }
    ];
  }

  getMockBookmarks(jobId) {
    return [
      {
        id: 1,
        timestamp: 45.5,
        title: 'Introduction starts',
        note: 'Speaker introduces the main topic',
        created_at: '2024-10-20T15:30:00Z',
        created_by: 'user1'
      },
      {
        id: 2,
        timestamp: 180.2,
        title: 'Key insight',
        note: 'Important point about market trends',
        created_at: '2024-10-20T15:35:00Z',
        created_by: 'user1'
      },
      {
        id: 3,
        timestamp: 420.8,
        title: 'Action items',
        note: 'List of follow-up tasks mentioned',
        created_at: '2024-10-20T15:40:00Z',
        created_by: 'user1'
      }
    ];
  }

  getMockBatchOperations() {
    return [
      {
        id: 'batch1',
        operation_type: 'tag',
        status: 'completed',
        job_count: 5,
        created_at: '2024-10-21T09:00:00Z',
        started_at: '2024-10-21T09:00:05Z',
        completed_at: '2024-10-21T09:00:15Z',
        error_message: null
      },
      {
        id: 'batch2',
        operation_type: 'export',
        status: 'processing',
        job_count: 12,
        created_at: '2024-10-21T10:30:00Z',
        started_at: '2024-10-21T10:30:10Z',
        completed_at: null,
        error_message: null
      }
    ];
  }

  getMockExports() {
    return [
      {
        id: 'export1',
        export_format: 'srt',
        job_count: 3,
        download_count: 2,
        created_at: '2024-10-20T14:00:00Z',
        expires_at: '2024-10-27T14:00:00Z',
        file_ready: true
      },
      {
        id: 'export2',
        export_format: 'docx',
        job_count: 1,
        download_count: 0,
        created_at: '2024-10-21T11:00:00Z',
        expires_at: '2024-10-28T11:00:00Z',
        file_ready: true
      }
    ];
  }
}

// Export singleton instance
export const transcriptManagementService = new TranscriptManagementService();