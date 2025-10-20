import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';

/**
 * UserManagement - Comprehensive user management interface for administrators
 * Provides user listing, details, role management, and user actions
 */
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await adminService.listUsers();
      setUsers(response.users || []);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm || 
      user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRole = filterRole === 'all' || 
      (filterRole === 'admin' && user.is_admin) ||
      (filterRole === 'user' && !user.is_admin);
    
    return matchesSearch && matchesRole;
  });

  const getUserRoleBadge = (user) => {
    if (user.is_admin) {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400">
          Admin
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
        User
      </span>
    );
  };

  const getUserStatusBadge = (user) => {
    if (user.is_active) {
      return (
        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
          Active
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
        Inactive
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const handleUserAction = async (action, userId) => {
    // Placeholder for user actions - to be implemented when backend supports it
    console.log(`Action ${action} for user ${userId}`);
    alert(`User action "${action}" would be performed here when backend supports it.`);
  };

  const UserCard = ({ user }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="font-medium text-gray-900 dark:text-white">
              {user.username || 'Unknown User'}
            </h3>
            {getUserRoleBadge(user)}
            {getUserStatusBadge(user)}
          </div>
          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <p>📧 {user.email || 'No email'}</p>
            <p>📅 Created: {formatDate(user.created_at)}</p>
            <p>🔄 Last active: {formatDate(user.last_active)}</p>
            <p>📊 Jobs: {user.job_count || 0}</p>
          </div>
        </div>
        <div className="flex flex-col space-y-1">
          <button
            onClick={() => setSelectedUser(user)}
            className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            View Details
          </button>
          <button
            onClick={() => handleUserAction('toggle_status', user.id)}
            className={`text-xs px-2 py-1 rounded transition-colors ${
              user.is_active 
                ? 'bg-red-600 text-white hover:bg-red-700' 
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {user.is_active ? 'Deactivate' : 'Activate'}
          </button>
          {!user.is_admin && (
            <button
              onClick={() => handleUserAction('make_admin', user.id)}
              className="text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            >
              Make Admin
            </button>
          )}
        </div>
      </div>
    </div>
  );

  const UserDetailsModal = ({ user, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              User Details: {user.username}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Basic Information</h3>
                <div className="space-y-2 text-sm">
                  <p><strong>ID:</strong> {user.id}</p>
                  <p><strong>Username:</strong> {user.username}</p>
                  <p><strong>Email:</strong> {user.email || 'Not provided'}</p>
                  <p><strong>Role:</strong> {user.is_admin ? 'Administrator' : 'User'}</p>
                  <p><strong>Status:</strong> {user.is_active ? 'Active' : 'Inactive'}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Activity</h3>
                <div className="space-y-2 text-sm">
                  <p><strong>Created:</strong> {formatDate(user.created_at)}</p>
                  <p><strong>Last Active:</strong> {formatDate(user.last_active)}</p>
                  <p><strong>Total Jobs:</strong> {user.job_count || 0}</p>
                  <p><strong>Successful Jobs:</strong> {user.successful_jobs || 0}</p>
                  <p><strong>Failed Jobs:</strong> {user.failed_jobs || 0}</p>
                </div>
              </div>
            </div>
            
            {user.permissions && (
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Permissions</h3>
                <div className="flex flex-wrap gap-2">
                  {user.permissions.map((permission, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded"
                    >
                      {permission}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => handleUserAction('reset_password', user.id)}
                className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
              >
                Reset Password
              </button>
              <button
                onClick={() => handleUserAction('view_jobs', user.id)}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
              >
                View Jobs
              </button>
              <button
                onClick={() => handleUserAction('send_notification', user.id)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Send Message
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading && users.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-500 dark:text-gray-400">Loading users...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            User Management
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage user accounts and permissions
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchUsers}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '⟳' : '🔄'} Refresh
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-6">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search users by username or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
          </div>
          <div>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value="all">All Roles</option>
              <option value="admin">Admins</option>
              <option value="user">Users</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Users</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{users.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Admins</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {users.filter(u => u.is_admin).length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Users</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {users.filter(u => u.is_active).length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">Filtered Results</h3>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{filteredUsers.length}</p>
        </div>
      </div>

      {/* Users List */}
      {filteredUsers.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
          <div className="text-gray-400 dark:text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {users.length === 0 ? 'No Users Found' : 'No Matching Users'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {users.length === 0 
                ? 'No users have been created yet. Users will appear here once they register.'
                : 'Try adjusting your search criteria or filters.'
              }
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredUsers.map((user) => (
            <UserCard key={user.id || user.username} user={user} />
          ))}
        </div>
      )}

      {/* User Details Modal */}
      {selectedUser && (
        <UserDetailsModal
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </div>
  );
};

export default UserManagement;
