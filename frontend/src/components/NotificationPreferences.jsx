/**
 * T030 User Preferences Enhancement: Notification Preferences Component
 * React component for managing notification preferences with granular controls
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bell, BellOff, Volume2, VolumeX, Smartphone, Monitor,
  Mail, Clock, Settings, TestTube, Download, Upload,
  ToggleLeft, ToggleRight, Sliders, AlertCircle,
  CheckCircle, Info, Zap, Users, Shield, User
} from 'lucide-react';
import notificationPreferencesService from '../services/notificationPreferencesService.js';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const NotificationPreferences = ({ 
  isOpen = false,
  onClose,
  className = ''
}) => {
  const [preferences, setPreferences] = useState(notificationPreferencesService.getPreferences());
  const [permission, setPermission] = useState(Notification?.permission || 'default');
  const [isQuietHours, setIsQuietHours] = useState(false);
  const [testingCategory, setTestingCategory] = useState(null);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Subscribe to preference changes
    const unsubscribe = notificationPreferencesService.subscribe((event, data) => {
      switch (event) {
        case 'preferences-updated':
          setPreferences(data);
          break;
        case 'permission-changed':
          setPermission(data);
          break;
        case 'quiet-hours-changed':
          setIsQuietHours(data);
          break;
        case 'test-notification':
          setTestingCategory(null);
          break;
      }
    });

    // Load initial data
    setStats(notificationPreferencesService.getNotificationStats());
    setIsQuietHours(notificationPreferencesService.isQuietHours());

    return unsubscribe;
  }, []);

  const requestPermission = async () => {
    try {
      await notificationPreferencesService.requestPermission();
      mobileInterfaceService.hapticFeedback('success');
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      mobileInterfaceService.hapticFeedback('error');
    }
  };

  const updateGlobalSetting = (key, value) => {
    notificationPreferencesService.updateGlobalPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateQuietHours = (updates) => {
    notificationPreferencesService.updateGlobalPreferences({
      quiet_hours: {
        ...preferences.global.quiet_hours,
        ...updates
      }
    });
  };

  const updateCategoryEnabled = (category, enabled) => {
    notificationPreferencesService.updateCategoryPreferences(category, { enabled });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateCategoryDelivery = (category, method, enabled) => {
    const currentDelivery = preferences.categories[category]?.delivery || {};
    notificationPreferencesService.updateCategoryPreferences(category, {
      delivery: {
        ...currentDelivery,
        [method]: enabled
      }
    });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateEventSetting = (category, event, setting, value) => {
    const currentEvent = preferences.categories[category]?.events[event] || {};
    notificationPreferencesService.updateEventPreferences(category, event, {
      ...currentEvent,
      [setting]: value
    });
    mobileInterfaceService.hapticFeedback('light');
  };

  const testNotification = async (category) => {
    setTestingCategory(category);
    try {
      await notificationPreferencesService.testNotification(category);
      mobileInterfaceService.hapticFeedback('success');
    } catch (error) {
      console.error('Error testing notification:', error);
      mobileInterfaceService.hapticFeedback('error');
      setTestingCategory(null);
    }
  };

  const exportPreferences = () => {
    notificationPreferencesService.exportPreferences();
    mobileInterfaceService.hapticFeedback('success');
  };

  const importPreferences = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      await notificationPreferencesService.importPreferences(file);
      mobileInterfaceService.hapticFeedback('success');
      alert('Preferences imported successfully!');
    } catch (error) {
      console.error('Error importing preferences:', error);
      mobileInterfaceService.hapticFeedback('error');
      alert(`Failed to import preferences: ${error.message}`);
    }
  };

  const resetPreferences = () => {
    if (confirm('Are you sure you want to reset all notification preferences to defaults?')) {
      notificationPreferencesService.resetPreferences();
      mobileInterfaceService.hapticFeedback('medium');
    }
  };

  const Toggle = ({ enabled, onChange, disabled = false }) => {
    const ToggleIcon = enabled ? ToggleRight : ToggleLeft;
    return (
      <button
        onClick={() => !disabled && onChange(!enabled)}
        disabled={disabled}
        className={`
          transition-colors
          ${enabled ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'}
        `}
      >
        <ToggleIcon className="w-6 h-6" />
      </button>
    );
  };

  const CategoryIcon = ({ category }) => {
    const icons = {
      transcription: Zap,
      batch: Users,
      system: Settings,
      account: User,
      social: Users
    };
    const Icon = icons[category] || Bell;
    return <Icon className="w-5 h-5" />;
  };

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();

  if (!isOpen) return null;

  const categories = Object.keys(preferences.categories);
  const tabs = [
    { id: 'general', label: 'General', icon: Bell },
    { id: 'categories', label: 'Categories', icon: Sliders },
    { id: 'advanced', label: 'Advanced', icon: Settings }
  ];

  return (
    <div className={`
      fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50
      ${className}
    `}>
      <div className={`
        bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden
        ${isMobileBreakpoint ? 'w-full h-full m-4' : 'w-full max-w-4xl max-h-[90vh] m-8'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Notification Preferences
            </h2>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={exportPreferences}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Export preferences"
            >
              <Download className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Import preferences"
            >
              <Upload className="w-5 h-5" />
            </button>
            
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 border-b-2 transition-colors
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className={`
          p-6 overflow-y-auto
          ${isMobileBreakpoint ? 'h-full' : 'max-h-[60vh]'}
        `}>
          {/* General Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              {/* Permission Status */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {permission === 'granted' ? (
                      <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                    )}
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        Browser Permission
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {permission === 'granted' 
                          ? 'Notifications are enabled'
                          : 'Click to enable browser notifications'
                        }
                      </p>
                    </div>
                  </div>
                  
                  {permission !== 'granted' && (
                    <button
                      onClick={requestPermission}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Enable
                    </button>
                  )}
                </div>
              </div>

              {/* Global Settings */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Global Settings
                </h3>
                
                <div className="grid gap-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Bell className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          Enable Notifications
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Master switch for all notifications
                        </div>
                      </div>
                    </div>
                    <Toggle
                      enabled={preferences.global.enabled}
                      onChange={(value) => updateGlobalSetting('enabled', value)}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Volume2 className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          Sound
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Play notification sounds
                        </div>
                      </div>
                    </div>
                    <Toggle
                      enabled={preferences.global.sound}
                      onChange={(value) => updateGlobalSetting('sound', value)}
                      disabled={!preferences.global.enabled}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Smartphone className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          Vibration
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Vibrate on mobile devices
                        </div>
                      </div>
                    </div>
                    <Toggle
                      enabled={preferences.global.vibration}
                      onChange={(value) => updateGlobalSetting('vibration', value)}
                      disabled={!preferences.global.enabled}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Monitor className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          Desktop Notifications
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Show browser notifications
                        </div>
                      </div>
                    </div>
                    <Toggle
                      enabled={preferences.global.desktop}
                      onChange={(value) => updateGlobalSetting('desktop', value)}
                      disabled={!preferences.global.enabled}
                    />
                  </div>
                </div>
              </div>

              {/* Quiet Hours */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                    <Clock className="w-5 h-5 mr-2" />
                    Quiet Hours
                    {isQuietHours && (
                      <span className="ml-2 px-2 py-1 text-xs bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 rounded">
                        Active
                      </span>
                    )}
                  </h3>
                  <Toggle
                    enabled={preferences.global.quiet_hours.enabled}
                    onChange={(value) => updateQuietHours({ enabled: value })}
                  />
                </div>
                
                {preferences.global.quiet_hours.enabled && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Start Time
                      </label>
                      <input
                        type="time"
                        value={preferences.global.quiet_hours.start}
                        onChange={(e) => updateQuietHours({ start: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        End Time
                      </label>
                      <input
                        type="time"
                        value={preferences.global.quiet_hours.end}
                        onChange={(e) => updateQuietHours({ end: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Categories Tab */}
          {activeTab === 'categories' && (
            <div className="space-y-6">
              {categories.map((category) => {
                const categoryPrefs = preferences.categories[category];
                return (
                  <div key={category} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <CategoryIcon category={category} />
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white capitalize">
                            {category}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Priority: {categoryPrefs.priority}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => testNotification(category)}
                          disabled={testingCategory === category}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                          {testingCategory === category ? (
                            <div className="flex items-center space-x-1">
                              <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                              <span>Testing...</span>
                            </div>
                          ) : (
                            <div className="flex items-center space-x-1">
                              <TestTube className="w-3 h-3" />
                              <span>Test</span>
                            </div>
                          )}
                        </button>
                        <Toggle
                          enabled={categoryPrefs.enabled}
                          onChange={(value) => updateCategoryEnabled(category, value)}
                        />
                      </div>
                    </div>
                    
                    {categoryPrefs.enabled && (
                      <div className="space-y-4">
                        {/* Delivery Methods */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Delivery Methods
                          </h4>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(categoryPrefs.delivery).map(([method, enabled]) => (
                              <div key={method} className="flex items-center justify-between">
                                <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                                  {method}
                                </span>
                                <Toggle
                                  enabled={enabled}
                                  onChange={(value) => updateCategoryDelivery(category, method, value)}
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        {/* Events */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Events
                          </h4>
                          <div className="space-y-2">
                            {Object.entries(categoryPrefs.events).map(([event, eventPrefs]) => (
                              <div key={event} className="flex items-center justify-between text-sm">
                                <span className="text-gray-600 dark:text-gray-400 capitalize">
                                  {event.replace('_', ' ')}
                                </span>
                                <div className="flex items-center space-x-2">
                                  {eventPrefs.interval && (
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                      {eventPrefs.interval}%
                                    </span>
                                  )}
                                  <Toggle
                                    enabled={eventPrefs.enabled}
                                    onChange={(value) => updateEventSetting(category, event, 'enabled', value)}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Advanced Tab */}
          {activeTab === 'advanced' && (
            <div className="space-y-6">
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Info className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-yellow-800 dark:text-yellow-200">
                      Advanced Settings
                    </h3>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      These settings affect notification behavior and performance. Change with caution.
                    </p>
                  </div>
                </div>
              </div>

              {/* Reset Section */}
              <div className="border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      Reset Preferences
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Reset all notification preferences to default values
                    </p>
                  </div>
                  <button
                    onClick={resetPreferences}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Reset All
                  </button>
                </div>
              </div>

              {/* Statistics */}
              {stats && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Statistics
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {stats.total_sent}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Total Notifications
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {stats.recent_activity.length}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Last 24 Hours
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Hidden file input for preferences import */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={importPreferences}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default NotificationPreferences;