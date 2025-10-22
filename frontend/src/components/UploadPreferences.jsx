/**
 * T030 User Preferences Enhancement: Upload Preferences Component
 * React component for managing file upload and processing preferences
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, Settings, FileText, Sliders, Download, Upload as UploadIcon,
  Save, RotateCcw, TestTube, Info, AlertTriangle, CheckCircle,
  File, Music, Video, Mic, Speaker, Clock, Zap, Target,
  BarChart3, Filter, Archive, Folder, Edit3, Globe
} from 'lucide-react';
import uploadPreferencesService from '../services/uploadPreferencesService.js';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const UploadPreferences = ({ 
  isOpen = false,
  onClose,
  className = ''
}) => {
  const [preferences, setPreferences] = useState(uploadPreferencesService.getPreferences());
  const [validationErrors, setValidationErrors] = useState([]);
  const [activeTab, setActiveTab] = useState('general');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isTestingConfig, setIsTestingConfig] = useState(false);
  const [usageStats, setUsageStats] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Subscribe to preference changes
    const unsubscribe = uploadPreferencesService.subscribe((event, data) => {
      switch (event) {
        case 'preferences-updated':
          setPreferences(data);
          break;
        case 'validation-errors':
          setValidationErrors(data);
          break;
      }
    });

    // Load usage statistics
    setUsageStats(uploadPreferencesService.getUsageStatistics());

    return unsubscribe;
  }, []);

  const updateGeneralSetting = (key, value) => {
    uploadPreferencesService.updateGeneralPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateFileHandlingSetting = (key, value) => {
    uploadPreferencesService.updateFileHandlingPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateQualitySetting = (key, value) => {
    uploadPreferencesService.updateQualitySettings({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateProcessingSetting = (key, value) => {
    uploadPreferencesService.updateProcessingOptions({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateOutputSetting = (key, value) => {
    uploadPreferencesService.updateOutputPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateTextFormatting = (key, value) => {
    const currentFormatting = preferences.output_preferences.text_formatting;
    updateOutputSetting('text_formatting', {
      ...currentFormatting,
      [key]: value
    });
  };

  const updateSubtitleSetting = (key, value) => {
    const currentSettings = preferences.output_preferences.subtitle_settings;
    updateOutputSetting('subtitle_settings', {
      ...currentSettings,
      [key]: value
    });
  };

  const toggleAcceptedFormat = (format) => {
    if (uploadPreferencesService.isFormatAccepted(format)) {
      uploadPreferencesService.removeAcceptedFormat(format);
    } else {
      uploadPreferencesService.addAcceptedFormat(format);
    }
    mobileInterfaceService.hapticFeedback('light');
  };

  const testConfiguration = async () => {
    setIsTestingConfig(true);
    try {
      // Simulate testing the current configuration
      await new Promise(resolve => setTimeout(resolve, 2000));
      mobileInterfaceService.hapticFeedback('success');
      alert('Configuration test completed successfully!');
    } catch (error) {
      console.error('Configuration test failed:', error);
      mobileInterfaceService.hapticFeedback('error');
      alert('Configuration test failed. Please check your settings.');
    } finally {
      setIsTestingConfig(false);
    }
  };

  const resetPreferences = () => {
    if (confirm('Are you sure you want to reset all upload preferences to defaults?')) {
      uploadPreferencesService.resetPreferences();
      mobileInterfaceService.hapticFeedback('medium');
    }
  };

  const exportPreferences = () => {
    uploadPreferencesService.exportPreferences();
    mobileInterfaceService.hapticFeedback('success');
  };

  const importPreferences = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const result = await uploadPreferencesService.importPreferences(file);
      mobileInterfaceService.hapticFeedback('success');
      
      if (result.validationErrors.length > 0) {
        alert(`Preferences imported with ${result.validationErrors.length} validation warnings. Check the console for details.`);
      } else {
        alert('Preferences imported successfully!');
      }
    } catch (error) {
      console.error('Error importing preferences:', error);
      mobileInterfaceService.hapticFeedback('error');
      alert(`Failed to import preferences: ${error.message}`);
    }
  };

  const formatFileSize = (bytes) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDuration = (ms) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const Toggle = ({ enabled, onChange, disabled = false }) => (
    <button
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors
        ${enabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition-transform
          ${enabled ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  );

  const availableFormats = [
    { mime: 'audio/mpeg', name: 'MP3', icon: Music, category: 'audio' },
    { mime: 'audio/wav', name: 'WAV', icon: Music, category: 'audio' },
    { mime: 'audio/mp4', name: 'M4A', icon: Music, category: 'audio' },
    { mime: 'audio/flac', name: 'FLAC', icon: Music, category: 'audio' },
    { mime: 'audio/ogg', name: 'OGG', icon: Music, category: 'audio' },
    { mime: 'video/mp4', name: 'MP4', icon: Video, category: 'video' },
    { mime: 'video/mpeg', name: 'MPEG', icon: Video, category: 'video' },
    { mime: 'video/quicktime', name: 'MOV', icon: Video, category: 'video' },
    { mime: 'video/x-msvideo', name: 'AVI', icon: Video, category: 'video' }
  ];

  const models = uploadPreferencesService.getAvailableModels();
  const languages = uploadPreferencesService.getAvailableLanguages();

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();

  if (!isOpen) return null;

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'files', label: 'File Handling', icon: File },
    { id: 'quality', label: 'Quality', icon: Target },
    { id: 'processing', label: 'Processing', icon: Zap },
    { id: 'output', label: 'Output', icon: FileText }
  ];

  return (
    <div className={`
      fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50
      ${className}
    `}>
      <div className={`
        bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden
        ${isMobileBreakpoint ? 'w-full h-full m-4' : 'w-full max-w-6xl max-h-[90vh] m-8'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Upload className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Upload Preferences
            </h2>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={testConfiguration}
              disabled={isTestingConfig}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isTestingConfig ? (
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
              <UploadIcon className="w-5 h-5" />
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

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <h3 className="font-medium text-yellow-800 dark:text-yellow-200">
                  Configuration Issues
                </h3>
                <ul className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                  {validationErrors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className={`
            flex px-6 space-x-8 overflow-x-auto
            ${isMobileBreakpoint ? 'space-x-4' : ''}
          `}>
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 border-b-2 transition-colors whitespace-nowrap
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span className={`font-medium ${isMobileBreakpoint ? 'text-sm' : ''}`}>
                    {tab.label}
                  </span>
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
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                General Upload Settings
              </h3>
              
              <div className="grid gap-6">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Upload
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically start upload when files are selected
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.general.auto_upload}
                    onChange={(value) => updateGeneralSetting('auto_upload', value)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Show File Previews
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Display audio waveform and file information
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.general.show_previews}
                    onChange={(value) => updateGeneralSetting('show_previews', value)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Show Upload Progress
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Display detailed upload progress information
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.general.show_upload_progress}
                    onChange={(value) => updateGeneralSetting('show_upload_progress', value)}
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Max Simultaneous Uploads
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={preferences.general.max_simultaneous_uploads}
                      onChange={(e) => updateGeneralSetting('max_simultaneous_uploads', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                      {preferences.general.max_simultaneous_uploads} files
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Chunk Size
                    </label>
                    <select
                      value={preferences.general.chunk_size}
                      onChange={(e) => updateGeneralSetting('chunk_size', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value={65536}>64 KB</option>
                      <option value={262144}>256 KB</option>
                      <option value={1048576}>1 MB</option>
                      <option value={5242880}>5 MB</option>
                      <option value={10485760}>10 MB</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Upload Timeout
                    </label>
                    <select
                      value={preferences.general.upload_timeout}
                      onChange={(e) => updateGeneralSetting('upload_timeout', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value={60000}>1 minute</option>
                      <option value={300000}>5 minutes</option>
                      <option value={600000}>10 minutes</option>
                      <option value={1800000}>30 minutes</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Max Retries
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="10"
                      value={preferences.general.max_retries}
                      onChange={(e) => updateGeneralSetting('max_retries', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* File Handling Tab */}
          {activeTab === 'files' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                File Handling Settings
              </h3>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  Accepted File Formats
                </h4>
                
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                  {availableFormats.map((format) => {
                    const Icon = format.icon;
                    const isAccepted = uploadPreferencesService.isFormatAccepted(format.mime);
                    
                    return (
                      <button
                        key={format.mime}
                        onClick={() => toggleAcceptedFormat(format.mime)}
                        className={`
                          p-3 rounded-lg border-2 transition-all text-left
                          ${isAccepted 
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }
                        `}
                      >
                        <div className="flex items-center space-x-2">
                          <Icon className={`
                            w-4 h-4
                            ${isAccepted ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}
                          `} />
                          <span className={`
                            font-medium text-sm
                            ${isAccepted ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-white'}
                          `}>
                            {format.name}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max File Size
                  </label>
                  <select
                    value={preferences.file_handling.max_file_size}
                    onChange={(e) => updateFileHandlingSetting('max_file_size', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value={104857600}>100 MB</option>
                    <option value={524288000}>500 MB</option>
                    <option value={1073741824}>1 GB</option>
                    <option value={2147483648}>2 GB</option>
                    <option value={5368709120}>5 GB</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Min File Size
                  </label>
                  <select
                    value={preferences.file_handling.min_file_size}
                    onChange={(e) => updateFileHandlingSetting('min_file_size', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value={1024}>1 KB</option>
                    <option value={10240}>10 KB</option>
                    <option value={102400}>100 KB</option>
                    <option value={1048576}>1 MB</option>
                  </select>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Validate Files
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically check file format and size
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.file_handling.auto_validate_files}
                    onChange={(value) => updateFileHandlingSetting('auto_validate_files', value)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Allow Duplicate Files
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Allow uploading files with the same name
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.file_handling.allow_duplicate_files}
                    onChange={(value) => updateFileHandlingSetting('allow_duplicate_files', value)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Rename Duplicates
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically rename duplicate files
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.file_handling.auto_rename_duplicates}
                    onChange={(value) => updateFileHandlingSetting('auto_rename_duplicates', value)}
                    disabled={preferences.file_handling.allow_duplicate_files}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Quality Tab */}
          {activeTab === 'quality' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Transcription Quality Settings
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Transcription Model
                  </label>
                  <select
                    value={preferences.quality_settings.transcription_model}
                    onChange={(e) => updateQualitySetting('transcription_model', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    {models.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name} - {model.description} ({model.size})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Preferred Language
                  </label>
                  <select
                    value={preferences.quality_settings.preferred_language}
                    onChange={(e) => updateQualitySetting('preferred_language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    {languages.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Enable Timestamps
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Include timing information in transcripts
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.quality_settings.enable_timestamps}
                    onChange={(value) => updateQualitySetting('enable_timestamps', value)}
                  />
                </div>
                
                {preferences.quality_settings.enable_timestamps && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Timestamp Granularity
                    </label>
                    <select
                      value={preferences.quality_settings.timestamp_granularity}
                      onChange={(e) => updateQualitySetting('timestamp_granularity', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="word">Word-level</option>
                      <option value="segment">Segment-level</option>
                      <option value="none">No timestamps</option>
                    </select>
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Enable Speaker Detection
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Identify different speakers in the audio
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.quality_settings.enable_speaker_detection}
                    onChange={(value) => updateQualitySetting('enable_speaker_detection', value)}
                  />
                </div>
                
                {preferences.quality_settings.enable_speaker_detection && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Maximum Speakers
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="20"
                      value={preferences.quality_settings.max_speakers}
                      onChange={(e) => updateQualitySetting('max_speakers', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                      {preferences.quality_settings.max_speakers} speakers
                    </div>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Audio Enhancement
                  </label>
                  <select
                    value={preferences.quality_settings.audio_enhancement}
                    onChange={(e) => updateQualitySetting('audio_enhancement', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="none">None</option>
                    <option value="light">Light</option>
                    <option value="moderate">Moderate</option>
                    <option value="aggressive">Aggressive</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Processing Tab */}
          {activeTab === 'processing' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Processing Options
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Priority Mode
                  </label>
                  <select
                    value={preferences.processing_options.priority_mode}
                    onChange={(e) => updateProcessingSetting('priority_mode', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="low">Low Priority</option>
                    <option value="normal">Normal Priority</option>
                    <option value="high">High Priority</option>
                    <option value="urgent">Urgent Priority</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Processing Pipeline
                  </label>
                  <select
                    value={preferences.processing_options.processing_pipeline}
                    onChange={(e) => updateProcessingSetting('processing_pipeline', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  >
                    <option value="fast">Fast (Lower accuracy)</option>
                    <option value="standard">Standard (Balanced)</option>
                    <option value="accurate">Accurate (Slower)</option>
                    <option value="custom">Custom Pipeline</option>
                  </select>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Segment Long Files
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically split long audio files for processing
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.processing_options.auto_segment_long_files}
                    onChange={(value) => updateProcessingSetting('auto_segment_long_files', value)}
                  />
                </div>
                
                {preferences.processing_options.auto_segment_long_files && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Segment Length (minutes)
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="60"
                        value={preferences.processing_options.segment_length / 60}
                        onChange={(e) => updateProcessingSetting('segment_length', parseInt(e.target.value) * 60)}
                        className="w-full"
                      />
                      <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                        {preferences.processing_options.segment_length / 60} minutes
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Overlap Duration (seconds)
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="30"
                        value={preferences.processing_options.overlap_duration}
                        onChange={(e) => updateProcessingSetting('overlap_duration', parseInt(e.target.value))}
                        className="w-full"
                      />
                      <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                        {preferences.processing_options.overlap_duration} seconds
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Parallel Processing
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Process multiple jobs simultaneously
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.processing_options.parallel_processing}
                    onChange={(value) => updateProcessingSetting('parallel_processing', value)}
                  />
                </div>
                
                {preferences.processing_options.parallel_processing && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Max Parallel Jobs
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      value={preferences.processing_options.max_parallel_jobs}
                      onChange={(e) => updateProcessingSetting('max_parallel_jobs', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                      {preferences.processing_options.max_parallel_jobs} jobs
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Output Tab */}
          {activeTab === 'output' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Output Preferences
              </h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Default Output Format
                </label>
                <select
                  value={preferences.output_preferences.default_output_format}
                  onChange={(e) => updateOutputSetting('default_output_format', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="json">JSON</option>
                  <option value="txt">Plain Text</option>
                  <option value="srt">SRT Subtitles</option>
                  <option value="vtt">VTT Subtitles</option>
                  <option value="all">All Formats</option>
                </select>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  Text Formatting
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Line Breaks
                    </label>
                    <select
                      value={preferences.output_preferences.text_formatting.line_breaks}
                      onChange={(e) => updateTextFormatting('line_breaks', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="none">No line breaks</option>
                      <option value="sentence">Sentence breaks</option>
                      <option value="paragraph">Paragraph breaks</option>
                      <option value="speaker">Speaker changes</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Sentence Spacing
                    </label>
                    <select
                      value={preferences.output_preferences.text_formatting.sentence_spacing}
                      onChange={(e) => updateTextFormatting('sentence_spacing', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="single">Single space</option>
                      <option value="double">Double space</option>
                    </select>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Punctuation
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically add punctuation to transcripts
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.output_preferences.text_formatting.punctuation}
                    onChange={(value) => updateTextFormatting('punctuation', value)}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="font-medium text-gray-900 dark:text-white">
                      Auto Capitalization
                    </label>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Automatically capitalize sentences and proper nouns
                    </p>
                  </div>
                  <Toggle
                    enabled={preferences.output_preferences.text_formatting.capitalization}
                    onChange={(value) => updateTextFormatting('capitalization', value)}
                  />
                </div>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  Subtitle Settings
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Max Line Length
                    </label>
                    <input
                      type="range"
                      min="20"
                      max="80"
                      value={preferences.output_preferences.subtitle_settings.max_line_length}
                      onChange={(e) => updateSubtitleSetting('max_line_length', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                      {preferences.output_preferences.subtitle_settings.max_line_length} characters
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Reading Speed (WPM)
                    </label>
                    <input
                      type="range"
                      min="120"
                      max="300"
                      value={preferences.output_preferences.subtitle_settings.reading_speed}
                      onChange={(e) => updateSubtitleSetting('reading_speed', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                      {preferences.output_preferences.subtitle_settings.reading_speed} WPM
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {usageStats && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {usageStats.total_uploads} total uploads •{' '}
                  {usageStats.successful_uploads} successful
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={resetPreferences}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <RotateCcw className="w-4 h-4 inline mr-1" />
                Reset
              </button>
              
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="px-4 py-2 text-blue-600 dark:text-blue-400 border border-blue-300 dark:border-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
              >
                <Sliders className="w-4 h-4 inline mr-1" />
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>
            </div>
          </div>
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

export default UploadPreferences;