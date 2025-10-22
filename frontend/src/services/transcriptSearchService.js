/**
 * Transcript Search Service - T021: Implement transcript search functionality
 * 
 * JavaScript client service for interacting with the transcript search API.
 * Provides methods for searching, filtering, and managing search operations.
 */

import apiClient from './apiClient';

export const searchTypes = {
  COMBINED: 'combined',
  FULL_TEXT: 'full_text',
  METADATA: 'metadata',
  ADVANCED: 'advanced'
};

export const sortOrders = {
  RELEVANCE: 'relevance',
  DATE_DESC: 'date_desc',
  DATE_ASC: 'date_asc',
  DURATION_DESC: 'duration_desc',
  DURATION_ASC: 'duration_asc',
  FILENAME: 'filename'
};

class TranscriptSearchService {
  /**
   * Search transcripts with advanced options
   * @param {Object} searchParams - Search parameters
   * @returns {Promise} Search response with results
   */
  async searchTranscripts(searchParams) {
    const {
      query,
      searchType = searchTypes.COMBINED,
      sortOrder = sortOrders.RELEVANCE,
      page = 1,
      pageSize = 20,
      filters = {}
    } = searchParams;

    const requestData = {
      query,
      search_type: searchType,
      sort_order: sortOrder,
      page,
      page_size: pageSize,
      ...filters
    };

    try {
      const response = await apiClient.post('/search/', requestData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Search transcripts error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Search failed'
      };
    }
  }

  /**
   * Get search suggestions based on partial query
   * @param {string} partialQuery - Partial search query
   * @param {number} limit - Maximum number of suggestions
   * @returns {Promise} Search suggestions
   */
  async getSearchSuggestions(partialQuery, limit = 10) {
    try {
      const response = await apiClient.get('/search/suggestions', {
        params: { q: partialQuery, limit }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get search suggestions error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get suggestions'
      };
    }
  }

  /**
   * Quick search for autocomplete and instant results
   * @param {string} query - Search query
   * @param {number} limit - Maximum number of results
   * @returns {Promise} Quick search results
   */
  async quickSearch(query, limit = 10) {
    try {
      const response = await apiClient.get('/search/quick', {
        params: { q: query, limit }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Quick search error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Quick search failed'
      };
    }
  }

  /**
   * Get search statistics and analytics
   * @returns {Promise} Search statistics
   */
  async getSearchStatistics() {
    try {
      const response = await apiClient.get('/search/stats');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get search statistics error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get search statistics'
      };
    }
  }

  /**
   * Get available search filter options
   * @returns {Promise} Filter options
   */
  async getSearchFilters() {
    try {
      const response = await apiClient.get('/search/filters');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get search filters error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get search filters'
      };
    }
  }

  /**
   * Format search results for display
   * @param {Array} results - Raw search results
   * @returns {Array} Formatted results
   */
  formatSearchResults(results) {
    return results.map(result => ({
      ...result,
      formattedDate: result.created_at ? new Date(result.created_at).toLocaleDateString() : 'Unknown',
      formattedDuration: result.duration ? this.formatDuration(result.duration) : 'Unknown',
      highlightedSnippet: this.highlightMatches(result.transcript_snippet, result.matches),
      keywordsList: Array.isArray(result.keywords) ? result.keywords : []
    }));
  }

  /**
   * Format duration in seconds to readable format
   * @param {number} seconds - Duration in seconds
   * @returns {string} Formatted duration
   */
  formatDuration(seconds) {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  /**
   * Highlight search matches in text
   * @param {string} text - Original text
   * @param {Array} matches - Match information
   * @returns {string} Text with highlight markers
   */
  highlightMatches(text, matches) {
    if (!matches || matches.length === 0) {
      return text;
    }

    let highlightedText = text;
    const allPositions = [];

    // Collect all match positions
    matches.forEach(match => {
      if (match.positions) {
        match.positions.forEach(pos => {
          allPositions.push({
            start: pos.position,
            end: pos.position + pos.length,
            term: pos.term
          });
        });
      }
    });

    // Sort positions by start index (descending to avoid offset issues)
    allPositions.sort((a, b) => b.start - a.start);

    // Apply highlighting
    allPositions.forEach(pos => {
      const before = highlightedText.slice(0, pos.start);
      const match = highlightedText.slice(pos.start, pos.end);
      const after = highlightedText.slice(pos.end);
      highlightedText = before + `<mark class="search-highlight">${match}</mark>` + after;
    });

    return highlightedText;
  }

  /**
   * Build search URL with parameters for sharing
   * @param {Object} searchParams - Search parameters
   * @returns {string} Search URL
   */
  buildSearchUrl(searchParams) {
    const params = new URLSearchParams();
    
    if (searchParams.query) params.set('q', searchParams.query);
    if (searchParams.searchType) params.set('type', searchParams.searchType);
    if (searchParams.sortOrder) params.set('sort', searchParams.sortOrder);
    if (searchParams.page) params.set('page', searchParams.page.toString());
    if (searchParams.pageSize) params.set('size', searchParams.pageSize.toString());
    
    // Add filter parameters
    Object.entries(searchParams.filters || {}).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          params.set(key, value.join(','));
        } else {
          params.set(key, value.toString());
        }
      }
    });

    return `/search?${params.toString()}`;
  }

  /**
   * Parse search URL parameters
   * @param {string} searchString - URL search string
   * @returns {Object} Parsed search parameters
   */
  parseSearchUrl(searchString) {
    const params = new URLSearchParams(searchString);
    const searchParams = {
      query: params.get('q') || '',
      searchType: params.get('type') || searchTypes.COMBINED,
      sortOrder: params.get('sort') || sortOrders.RELEVANCE,
      page: parseInt(params.get('page')) || 1,
      pageSize: parseInt(params.get('size')) || 20,
      filters: {}
    };

    // Parse filter parameters
    const filterKeys = ['languages', 'models', 'date_from', 'date_to', 'duration_min', 'duration_max', 'sentiment_min', 'sentiment_max', 'has_keywords', 'has_summary'];
    
    filterKeys.forEach(key => {
      const value = params.get(key);
      if (value) {
        if (key === 'languages' || key === 'models') {
          searchParams.filters[key] = value.split(',');
        } else if (key === 'has_keywords' || key === 'has_summary') {
          searchParams.filters[key] = value === 'true';
        } else if (key.includes('_min') || key.includes('_max') || key === 'duration_min' || key === 'duration_max') {
          searchParams.filters[key] = parseFloat(value);
        } else {
          searchParams.filters[key] = value;
        }
      }
    });

    return searchParams;
  }

  /**
   * Validate search query
   * @param {string} query - Search query to validate
   * @returns {Object} Validation result
   */
  validateQuery(query) {
    const errors = [];
    
    if (!query || query.trim().length === 0) {
      errors.push('Search query cannot be empty');
    }
    
    if (query && query.length > 500) {
      errors.push('Search query must be less than 500 characters');
    }

    // Check for potentially problematic characters
    const dangerousChars = /[<>;"'`]/;
    if (query && dangerousChars.test(query)) {
      errors.push('Search query contains invalid characters');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Debounce function for search input
   * @param {Function} func - Function to debounce
   * @param {number} wait - Wait time in milliseconds
   * @returns {Function} Debounced function
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Create debounced search function
   * @param {Function} searchFunction - Search function to debounce
   * @param {number} delay - Debounce delay in milliseconds
   * @returns {Function} Debounced search function
   */
  createDebouncedSearch(searchFunction, delay = 300) {
    return this.debounce(searchFunction, delay);
  }
}

// Export singleton instance
export const transcriptSearchService = new TranscriptSearchService();
export default transcriptSearchService;