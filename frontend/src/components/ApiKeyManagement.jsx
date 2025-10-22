/**
 * T028 Frontend Implementation: API Key Management Component
 * React component for managing user API keys with full CRUD operations
 */

import React, { useState, useEffect } from 'react';
import apiKeyService from '../services/apiKeyService';

const ApiKeyManagement = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const [stats, setStats] = useState(null);

  // Form states
  const [newKeyData, setNewKeyData] = useState({
    name: '',
    permissions: [],
    expires_at: '',
    description: ''
  });

  const [copyNotification, setCopyNotification] = useState('');

  useEffect(() => {
    loadApiKeys();
    loadStats();
  }, []);

  const loadApiKeys = async () => {
    setLoading(true);
    const result = await apiKeyService.getUserApiKeys();
    if (result.success) {
      setApiKeys(result.data);
      setError(null);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    const result = await apiKeyService.getUserApiKeyStats();
    if (result.success) {
      setStats(result.data);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await apiKeyService.createApiKey(newKeyData);
    if (result.success) {
      await loadApiKeys();
      await loadStats();
      setShowCreateForm(false);
      setNewKeyData({ name: '', permissions: [], expires_at: '', description: '' });
      setSelectedKey(result.data); // Show the new key for copying
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleRevokeKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    const result = await apiKeyService.revokeApiKey(keyId);
    if (result.success) {
      await loadApiKeys();
      await loadStats();
      setSelectedKey(null);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleRegenerateKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to regenerate this API key? The old key will become invalid.')) {
      return;
    }

    setLoading(true);
    const result = await apiKeyService.regenerateApiKey(keyId);
    if (result.success) {
      await loadApiKeys();
      setSelectedKey(result.data); // Show the new key for copying
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key).then(() => {
      setCopyNotification('API key copied to clipboard!');
      setTimeout(() => setCopyNotification(''), 3000);
    });
  };

  const handlePermissionChange = (permission) => {
    setNewKeyData(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission]
    }));
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (key) => {
    const expiration = apiKeyService.getExpirationStatus(key.expires_at);
    const colorClasses = {
      red: 'bg-red-100 text-red-800',
      orange: 'bg-orange-100 text-orange-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      green: 'bg-green-100 text-green-800',
      gray: 'bg-gray-100 text-gray-800'
    };

    if (!key.is_active) {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Revoked</span>;
    }

    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colorClasses[expiration.color]}`}>
        {expiration.message}
      </span>
    );
  };

  const availablePermissions = apiKeyService.getAvailablePermissions();

  if (loading && !apiKeys.length) {
    return (
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">API Key Management</h2>
            <p className="text-gray-600 mt-1">Create and manage API keys for programmatic access</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Create New Key
          </button>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{stats.total_keys}</div>
              <div className="text-sm text-gray-600">Total Keys</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.active_keys}</div>
              <div className="text-sm text-gray-600">Active Keys</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_requests}</div>
              <div className="text-sm text-gray-600">Total Requests</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.requests_this_month}</div>
              <div className="text-sm text-gray-600">This Month</div>
            </div>
          </div>
        )}
      </div>

      {/* Error notification */}
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

      {/* Copy notification */}
      {copyNotification && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="text-green-400">
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">{copyNotification}</p>
            </div>
          </div>
        </div>
      )}

      {/* Create form modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <form onSubmit={handleCreateKey}>
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New API Key</h3>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Key Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newKeyData.name}
                    onChange={(e) => setNewKeyData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="My API Key"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newKeyData.description}
                    onChange={(e) => setNewKeyData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="2"
                    placeholder="Optional description"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Permissions
                  </label>
                  <div className="space-y-2">
                    {availablePermissions.map(permission => (
                      <label key={permission.value} className="flex items-start">
                        <input
                          type="checkbox"
                          checked={newKeyData.permissions.includes(permission.value)}
                          onChange={() => handlePermissionChange(permission.value)}
                          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div className="ml-2">
                          <div className="text-sm font-medium text-gray-900">{permission.label}</div>
                          <div className="text-xs text-gray-500">{permission.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expiration Date
                  </label>
                  <input
                    type="datetime-local"
                    value={newKeyData.expires_at}
                    onChange={(e) => setNewKeyData(prev => ({ ...prev, expires_at: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Leave empty for no expiration</p>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !newKeyData.name || newKeyData.permissions.length === 0}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New key display modal */}
      {selectedKey && selectedKey.key && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">New API Key Created</h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> This is the only time you'll see the full API key. 
                  Make sure to copy it now and store it securely.
                </p>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <div className="flex">
                  <input
                    type="text"
                    readOnly
                    value={selectedKey.key}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md bg-gray-50 font-mono text-sm"
                  />
                  <button
                    onClick={() => handleCopyKey(selectedKey.key)}
                    className="px-3 py-2 bg-blue-600 text-white border border-blue-600 rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedKey(null)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys list */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Your API Keys</h3>
        </div>
        
        {apiKeys.length === 0 ? (
          <div className="p-6 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m0 0a2 2 0 012 2m-2-2h-3m-3 0h3m0 0h3m-3 0v3m0-3V7a2 2 0 00-2-2m2 2a2 2 0 00-2-2M9 12h3m3 0h3" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating your first API key.</p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Create API Key
              </button>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {apiKeys.map((key) => (
              <div key={key.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <h4 className="text-sm font-medium text-gray-900">{key.name}</h4>
                      {getStatusBadge(key)}
                    </div>
                    <div className="mt-1 text-sm text-gray-600">
                      Key: {apiKeyService.formatKeyForDisplay(key.key_preview || key.key)}
                    </div>
                    {key.description && (
                      <div className="mt-1 text-sm text-gray-500">{key.description}</div>
                    )}
                    <div className="mt-2 flex space-x-4 text-xs text-gray-500">
                      <span>Created: {formatDate(key.created_at)}</span>
                      <span>Expires: {formatDate(key.expires_at)}</span>
                      <span>Last used: {formatDate(key.last_used_at)}</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      Permissions: {key.permissions?.join(', ') || 'None'}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    {key.is_active && (
                      <>
                        <button
                          onClick={() => handleRegenerateKey(key.id)}
                          className="text-blue-600 hover:text-blue-900 text-sm"
                        >
                          Regenerate
                        </button>
                        <button
                          onClick={() => handleRevokeKey(key.id)}
                          className="text-red-600 hover:text-red-900 text-sm"
                        >
                          Revoke
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiKeyManagement;