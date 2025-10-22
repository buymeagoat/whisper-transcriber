import React, { useState } from 'react';
import SystemHealth from '../components/SystemHealth';
import BackupManagement from '../components/BackupManagement';
import UserManagement from '../components/UserManagement';
import AdminJobManagement from '../components/admin/AdminJobManagement';
import SystemPerformanceDashboard from '../components/SystemPerformanceDashboard';

/**
 * AdminPanel - Main administrative interface for system management
 * Provides access to system health, user management, job administration, and maintenance tools
 */
const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('health');

  const tabs = [
    { id: 'health', name: 'System Health', icon: '🏥' },
    { id: 'performance', name: 'Performance Dashboard', icon: '📊' },
    { id: 'users', name: 'User Management', icon: '👥' },
    { id: 'jobs', name: 'Job Management', icon: '📋' },
    { id: 'backups', name: 'Backups', icon: '💾' },
    { id: 'maintenance', name: 'Maintenance', icon: '🔧' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'health':
        return <SystemHealth />;
      case 'performance':
        return <SystemPerformanceDashboard />;
      case 'users':
        return <UserManagement />;
      case 'jobs':
        return <AdminJobManagement />;
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

// All admin components are now imported and used directly

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
