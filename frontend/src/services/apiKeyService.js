/**
 * T028 Frontend Implementation: API Key Service
 * Client-side service for managing API keys with the T027 backend
 */

import apiClient from './apiClient';

class ApiKeyService {
  /**
   * Get all API keys for the current user
   */
  async getUserApiKeys() {
    try {
      const response = await apiClient.get('/api/v1/keys');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch API keys'
      };
    }
  }

  /**
   * Create a new API key
   */
  async createApiKey(keyData) {
    try {
      const response = await apiClient.post('/api/v1/keys', keyData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create API key'
      };
    }
  }

  /**
   * Get API key details by ID
   */
  async getApiKey(keyId) {
    try {
      const response = await apiClient.get(`/api/v1/keys/${keyId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch API key details'
      };
    }
  }

  /**
   * Update API key (name, permissions, etc.)
   */
  async updateApiKey(keyId, updateData) {
    try {
      const response = await apiClient.put(`/api/v1/keys/${keyId}`, updateData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update API key'
      };
    }
  }

  /**
   * Revoke an API key
   */
  async revokeApiKey(keyId) {
    try {
      const response = await apiClient.delete(`/api/v1/keys/${keyId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to revoke API key'
      };
    }
  }

  /**
   * Regenerate API key
   */
  async regenerateApiKey(keyId) {
    try {
      const response = await apiClient.post(`/api/v1/keys/${keyId}/regenerate`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to regenerate API key'
      };
    }
  }

  /**
   * Get API key usage statistics
   */
  async getApiKeyStats(keyId) {
    try {
      const response = await apiClient.get(`/api/v1/keys/${keyId}/statistics`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch API key statistics'
      };
    }
  }

  /**
   * Get user's API key usage summary
   */
  async getUserApiKeyStats() {
    try {
      const response = await apiClient.get('/api/v1/keys/stats/summary');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch API key summary'
      };
    }
  }

  /**
   * Test API key validity
   */
  async testApiKey(apiKey) {
    try {
      const response = await apiClient.post('/api/v1/keys/test', { api_key: apiKey });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'API key test failed'
      };
    }
  }

  /**
   * Get available permissions for API keys
   */
  getAvailablePermissions() {
    return [
      {
        value: 'transcribe_audio',
        label: 'Transcribe Audio',
        description: 'Submit individual transcription jobs'
      },
      {
        value: 'batch_upload',
        label: 'Batch Upload',
        description: 'Submit batch transcription jobs'
      },
      {
        value: 'pwa_notifications',
        label: 'PWA Notifications',
        description: 'Manage push notifications and offline jobs'
      },
      {
        value: 'admin_access',
        label: 'Admin Access',
        description: 'Full administrative access (admin users only)'
      }
    ];
  }

  /**
   * Format API key for display (showing only first/last characters)
   */
  formatKeyForDisplay(key) {
    if (!key || key.length < 8) return key;
    const prefix = key.substring(0, 8);
    const suffix = key.substring(key.length - 4);
    const middle = '*'.repeat(Math.max(0, key.length - 12));
    return `${prefix}${middle}${suffix}`;
  }

  /**
   * Validate API key format
   */
  validateKeyFormat(key) {
    if (!key) return { valid: false, message: 'API key is required' };
    if (key.length < 32) return { valid: false, message: 'API key is too short' };
    if (!/^wt_[a-zA-Z0-9_]+$/.test(key)) {
      return { valid: false, message: 'Invalid API key format (should start with wt_)' };
    }
    return { valid: true };
  }

  /**
   * Get expiration status of API key
   */
  getExpirationStatus(expiresAt) {
    if (!expiresAt) return { status: 'never', message: 'Never expires', color: 'gray' };
    
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { status: 'expired', message: 'Expired', color: 'red' };
    } else if (diffDays <= 7) {
      return { status: 'expiring', message: `Expires in ${diffDays} days`, color: 'orange' };
    } else if (diffDays <= 30) {
      return { status: 'warning', message: `Expires in ${diffDays} days`, color: 'yellow' };
    } else {
      return { status: 'valid', message: `Expires in ${diffDays} days`, color: 'green' };
    }
  }
}

export default new ApiKeyService();