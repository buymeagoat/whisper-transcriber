/**
 * T028 Frontend Implementation: PWA Settings Component
 * React component for managing Progressive Web App settings
 */

import React, { useState, useEffect } from 'react';
import pwaService from '../services/pwaService';
import { 
  Smartphone, 
  Bell, 
  Wifi, 
  Download, 
  Settings, 
  RefreshCw, 
  Trash2,
  CheckCircle,
  AlertCircle,
  Info
} from 'lucide-react';

const PWASettings = () => {
  const [settings, setSettings] = useState(null);
  const [installationStatus, setInstallationStatus] = useState(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [storageInfo, setStorageInfo] = useState(null);
  const [capabilities, setCapabilities] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadPWAData();
  }, []);

  const loadPWAData = async () => {
    setLoading(true);
    try {
      // Load all PWA-related data
      const [settingsResult, installResult, subscriptionResult, storageResult] = await Promise.all([
        pwaService.getPWASettings(),
        pwaService.getInstallationStatus(),
        pwaService.getPushSubscriptionStatus(),
        pwaService.getStorageInfo()
      ]);

      if (settingsResult.success) setSettings(settingsResult.data);
      if (installResult.success) setInstallationStatus(installResult.data);
      if (subscriptionResult.success) setSubscriptionStatus(subscriptionResult.data);
      if (storageResult.success) setStorageInfo(storageResult.data);

      setCapabilities(pwaService.getAppCapabilities());
    } catch (err) {
      setError('Failed to load PWA settings');
    }
    setLoading(false);
  };

  const handleSettingChange = async (settingKey, value) => {
    const newSettings = { ...settings, [settingKey]: value };
    setSettings(newSettings);

    const result = await pwaService.configurePWASettings(newSettings);
    if (result.success) {
      setSuccess('Settings updated successfully');
      setTimeout(() => setSuccess(null), 3000);
      
      // Reload subscription status if notifications were toggled
      if (settingKey === 'notifications') {
        const subResult = await pwaService.getPushSubscriptionStatus();
        if (subResult.success) setSubscriptionStatus(subResult.data);
      }
    } else {
      setError(result.error);
      // Revert the setting
      setSettings(prev => ({ ...prev, [settingKey]: !value }));
    }
  };

  const handleInstallApp = async () => {
    const result = await pwaService.promptInstall();
    if (result.success) {
      setSuccess('App installation prompted');
      await loadPWAData(); // Refresh installation status
    } else {
      setError(result.error);
    }
  };

  const handleSubscribeNotifications = async () => {
    const result = await pwaService.subscribeToPushNotifications();
    if (result.success) {
      setSuccess('Successfully subscribed to notifications');
      await loadPWAData();
    } else {
      setError(result.error);
    }
  };

  const handleUnsubscribeNotifications = async () => {
    const result = await pwaService.unsubscribeFromPushNotifications();
    if (result.success) {
      setSuccess('Successfully unsubscribed from notifications');
      await loadPWAData();
    } else {
      setError(result.error);
    }
  };

  const handleCheckUpdates = async () => {
    const result = await pwaService.checkForUpdates();
    if (result.success) {
      setSuccess('Checked for updates');
    } else {
      setError(result.error);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm('This will clear all app data including offline jobs. Are you sure?')) {
      return;
    }

    const result = await pwaService.clearAppData();
    if (result.success) {
      setSuccess('App data cleared successfully');
      await loadPWAData();
    } else {
      setError(result.error);
    }
  };

  const formatStorage = (bytes) => {
    if (!bytes) return '0 MB';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const getCapabilityStatus = (capability) => {
    return capabilities?.[capability] ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <AlertCircle className="w-4 h-4 text-red-500" />
    );
  };

  if (loading) {
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
      {/* Header */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Smartphone className="w-6 h-6 text-blue-600 mr-3" />
          <h2 className="text-2xl font-bold text-gray-900">PWA Settings</h2>
        </div>
        <p className="text-gray-600">
          Configure Progressive Web App features, offline capabilities, and notifications
        </p>
      </div>

      {/* Error/Success notifications */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Installation & Core Features */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">App Installation</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">App Installed</p>
                <p className="text-xs text-gray-500">
                  {installationStatus?.isInstalled ? 'App is installed as PWA' : 'Running in browser'}
                </p>
              </div>
              <div className="flex items-center">
                {installationStatus?.isInstalled ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <button
                    onClick={handleInstallApp}
                    disabled={!installationStatus?.isInstallable}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    Install
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Service Worker</p>
                <p className="text-xs text-gray-500">Background processing support</p>
              </div>
              {getCapabilityStatus('offline')}
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Offline Support</p>
                <p className="text-xs text-gray-500">Cache jobs for offline processing</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings?.offline_mode || false}
                  onChange={(e) => handleSettingChange('offline_mode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Push Notifications</p>
                <p className="text-xs text-gray-500">
                  {subscriptionStatus?.subscribed ? 'Subscribed to push notifications' : 'Not subscribed'}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {subscriptionStatus?.subscribed ? (
                  <button
                    onClick={handleUnsubscribeNotifications}
                    className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Unsubscribe
                  </button>
                ) : (
                  <button
                    onClick={handleSubscribeNotifications}
                    disabled={!installationStatus?.isNotificationSupported}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    Subscribe
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Job Completion Alerts</p>
                <p className="text-xs text-gray-500">Notify when transcription jobs complete</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings?.notifications || false}
                  onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Background Updates</p>
                <p className="text-xs text-gray-500">Check for job updates in background</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings?.background_updates || false}
                  onChange={(e) => handleSettingChange('background_updates', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Data Management</h3>
          
          <div className="space-y-4">
            {storageInfo && (
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-700">Storage Used</span>
                  <span className="font-medium">
                    {formatStorage(storageInfo.used)} / {formatStorage(storageInfo.available)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${Math.min(storageInfo.usedPercent, 100)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {storageInfo.usedPercent}% of available storage used
                </p>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Auto Sync</p>
                <p className="text-xs text-gray-500">Automatically sync when online</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings?.auto_sync || false}
                  onChange={(e) => handleSettingChange('auto_sync', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Data Saver Mode</p>
                <p className="text-xs text-gray-500">Reduce data usage for updates</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings?.data_saver || false}
                  onChange={(e) => handleSettingChange('data_saver', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* App Management */}
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">App Management</h3>
          
          <div className="space-y-3">
            <button
              onClick={handleCheckUpdates}
              className="w-full flex items-center justify-center px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Check for Updates
            </button>

            <button
              onClick={handleClearData}
              className="w-full flex items-center justify-center px-4 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear App Data
            </button>
          </div>
        </div>
      </div>

      {/* Capabilities Overview */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Device Capabilities</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('offline')}
            <span className="text-sm text-gray-700">Offline Mode</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('notifications')}
            <span className="text-sm text-gray-700">Notifications</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('background_sync')}
            <span className="text-sm text-gray-700">Background Sync</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('push_messaging')}
            <span className="text-sm text-gray-700">Push Messages</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('file_system_access')}
            <span className="text-sm text-gray-700">File Access</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('web_share')}
            <span className="text-sm text-gray-700">Web Share</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('fullscreen')}
            <span className="text-sm text-gray-700">Fullscreen</span>
          </div>
          <div className="flex items-center space-x-2">
            {getCapabilityStatus('vibration')}
            <span className="text-sm text-gray-700">Vibration</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PWASettings;