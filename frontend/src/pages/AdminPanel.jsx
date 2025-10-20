import React, { useState } from 'react';
import SystemHealth from '../components/SystemHealth';
import BackupManagement from '../components/BackupManagement';

/**
 * AdminPanel - Main administrative interface for system management
 * Provides access to system health, user management, job administration, and maintenance tools
 */
const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('health');

  const tabs = [
    { id: 'health', name: 'System Health', icon: '🏥' },
    { id: 'users', name: 'User Management', icon: '👥' },
    { id: 'jobs', name: 'Job Management', icon: '📋' },
    { id: 'backups', name: 'Backups', icon: '💾' },
    { id: 'maintenance', name: 'Maintenance', icon: '🔧' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'health':
        return <SystemHealth />;
      case 'users':
        return <UserManagement />;
      case 'jobs':
        return <JobAdministration />;
      case 'backups':
        return <BackupManagement />;
      case 'maintenance':
        return <MaintenanceTools />;
      default:
        return <SystemHealth />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Admin Panel
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            System administration and management tools
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex items-center space-x-2
                    ${activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

// Placeholder components for future implementation
const UserManagement = () => (
  <div className="p-6">
    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
      User Management
    </h2>
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
      <p className="text-yellow-800 dark:text-yellow-200">
        🚧 User management interface coming soon (T008)
      </p>
    </div>
  </div>
);

const JobAdministration = () => (
  <div className="p-6">
    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
      Job Administration
    </h2>
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
      <p className="text-yellow-800 dark:text-yellow-200">
        🚧 Job administration interface coming soon (T006 Phase 2)
      </p>
    </div>
  </div>
);

// BackupManagement component is now imported and used directly

const MaintenanceTools = () => (
  <div className="p-6">
    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
      Maintenance Tools
    </h2>
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
      <p className="text-yellow-800 dark:text-yellow-200">
        🚧 Maintenance tools coming soon
      </p>
    </div>
  </div>
);

export default AdminPanel;
