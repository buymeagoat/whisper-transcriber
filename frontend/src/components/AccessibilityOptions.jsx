/**
 * T030 User Preferences Enhancement: Accessibility Options Component
 * React component for comprehensive accessibility preferences management
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Eye, EyeOff, Volume2, VolumeX, MousePointer, Keyboard, Brain,
  Monitor, Settings, TestTube, Save, RotateCcw, Download, Upload,
  Check, AlertTriangle, Info, ChevronDown, ChevronUp, Play, Pause,
  Accessibility, Focus, Type, Contrast, Palette, Hand, Ear, BookOpen
} from 'lucide-react';
import accessibilityOptionsService from '../services/accessibilityOptionsService.js';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const AccessibilityOptions = ({ 
  isOpen = false,
  onClose,
  className = ''
}) => {
  const [preferences, setPreferences] = useState(accessibilityOptionsService.getPreferences());
  const [activeCategory, setActiveCategory] = useState('vision');
  const [expandedSections, setExpandedSections] = useState(new Set(['basic']));
  const [isTestingConfig, setIsTestingConfig] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [usageStats, setUsageStats] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const fileInputRef = useRef(null);
  const demoTextRef = useRef(null);

  useEffect(() => {
    // Subscribe to preference changes
    const unsubscribe = accessibilityOptionsService.subscribe((event, data) => {
      switch (event) {
        case 'preferences-updated':
          setPreferences(data);
          break;
        case 'preferences-reset':
          setPreferences(data);
          setTestResults(null);
          break;
      }
    });

    // Load usage statistics
    setUsageStats(accessibilityOptionsService.getUsageStatistics());

    return unsubscribe;
  }, []);

  const updateVisionSetting = (key, value) => {
    accessibilityOptionsService.updateVisionPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
    
    if (previewMode) {
      setTimeout(() => {
        accessibilityOptionsService.updateVisionPreferences({ [key]: !value });
      }, 2000);
    }
  };

  const updateMotorSetting = (key, value) => {
    accessibilityOptionsService.updateMotorPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateCognitiveSetting = (key, value) => {
    accessibilityOptionsService.updateCognitivePreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateAudioSetting = (key, value) => {
    accessibilityOptionsService.updateAudioPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateScreenReaderSetting = (key, value) => {
    accessibilityOptionsService.updateScreenReaderPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const updateContentSetting = (key, value) => {
    accessibilityOptionsService.updateContentPreferences({ [key]: value });
    mobileInterfaceService.hapticFeedback('light');
  };

  const testConfiguration = async () => {
    setIsTestingConfig(true);
    try {
      const results = await accessibilityOptionsService.testConfiguration();
      setTestResults(results);
      mobileInterfaceService.hapticFeedback('success');
      
      // Announce results to screen reader
      accessibilityOptionsService.announceToScreenReader(
        `Accessibility test completed. Overall score: ${results.overall_score}%`
      );
    } catch (error) {
      console.error('Accessibility test failed:', error);
      mobileInterfaceService.hapticFeedback('error');
    } finally {
      setIsTestingConfig(false);
    }
  };

  const resetPreferences = () => {
    if (confirm('Are you sure you want to reset all accessibility preferences to defaults?')) {
      accessibilityOptionsService.resetPreferences();
      mobileInterfaceService.hapticFeedback('medium');
    }
  };

  const exportPreferences = () => {
    accessibilityOptionsService.exportPreferences();
    mobileInterfaceService.hapticFeedback('success');
  };

  const importPreferences = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const result = await accessibilityOptionsService.importPreferences(file);
      mobileInterfaceService.hapticFeedback('success');
      alert('Accessibility preferences imported successfully!');
    } catch (error) {
      console.error('Error importing preferences:', error);
      mobileInterfaceService.hapticFeedback('error');
      alert(`Failed to import preferences: ${error.message}`);
    }
  };

  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const playDemoAudio = (type) => {
    accessibilityOptionsService.playSoundEffect(type);
  };

  const announceToUser = (message) => {
    accessibilityOptionsService.announceToScreenReader(message);
  };

  const Toggle = ({ enabled, onChange, disabled = false, ariaLabel }) => (
    <button
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-pressed={enabled}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
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

  const SliderControl = ({ label, value, min, max, step = 0.1, onChange, unit = '', ariaLabel }) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <div className="flex items-center space-x-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          aria-label={ariaLabel || label}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem] text-right">
          {value}{unit}
        </span>
      </div>
    </div>
  );

  const CategoryHeader = ({ category, title, icon: Icon, description }) => (
    <button
      onClick={() => setActiveCategory(category)}
      className={`
        w-full flex items-center space-x-3 p-4 rounded-lg border-2 transition-all text-left
        ${activeCategory === category 
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
        }
      `}
      aria-pressed={activeCategory === category}
    >
      <Icon className={`
        w-6 h-6 
        ${activeCategory === category ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}
      `} />
      <div className="flex-1">
        <h3 className={`
          font-medium
          ${activeCategory === category ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-white'}
        `}>
          {title}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {description}
        </p>
      </div>
    </button>
  );

  const ExpandableSection = ({ title, id, children, defaultExpanded = false }) => {
    const isExpanded = expandedSections.has(id);
    
    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          aria-expanded={isExpanded}
        >
          <h4 className="font-medium text-gray-900 dark:text-white">{title}</h4>
          {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
        
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700">
            {children}
          </div>
        )}
      </div>
    );
  };

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();

  if (!isOpen) return null;

  const categories = [
    { id: 'vision', title: 'Vision & Display', icon: Eye, description: 'Visual accessibility options' },
    { id: 'motor', title: 'Motor & Input', icon: MousePointer, description: 'Motor accessibility options' },
    { id: 'cognitive', title: 'Cognitive & Learning', icon: Brain, description: 'Cognitive accessibility options' },
    { id: 'audio', title: 'Audio & Sound', icon: Volume2, description: 'Audio accessibility options' },
    { id: 'screen_reader', title: 'Screen Reader', icon: Accessibility, description: 'Screen reader options' },
    { id: 'content', title: 'Content & Language', icon: BookOpen, description: 'Content accessibility options' }
  ];

  return (
    <div className={`
      fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50
      ${className}
    `}>
      <div className={`
        bg-white dark:bg-gray-800 rounded-lg shadow-xl overflow-hidden
        ${isMobileBreakpoint ? 'w-full h-full m-4' : 'w-full max-w-7xl max-h-[90vh] m-8'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Accessibility className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Accessibility Options
            </h2>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={testConfiguration}
              disabled={isTestingConfig}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
              aria-label="Test accessibility configuration"
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
              onClick={() => setPreviewMode(!previewMode)}
              className={`
                p-2 rounded-lg transition-colors
                ${previewMode 
                  ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' 
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
                }
              `}
              title="Preview mode"
              aria-label="Toggle preview mode"
              aria-pressed={previewMode}
            >
              {previewMode ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            
            <button
              onClick={exportPreferences}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Export preferences"
              aria-label="Export accessibility preferences"
            >
              <Download className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              title="Import preferences"
              aria-label="Import accessibility preferences"
            >
              <Upload className="w-5 h-5" />
            </button>
            
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              aria-label="Close accessibility options"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Test Results */}
        {testResults && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800 p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <h3 className="font-medium text-blue-800 dark:text-blue-200">
                  Accessibility Test Results
                </h3>
                <p className="text-blue-700 dark:text-blue-300">
                  Overall Score: {testResults.overall_score}%
                </p>
                {testResults.recommendations.length > 0 && (
                  <ul className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                    {testResults.recommendations.slice(0, 3).map((rec, index) => (
                      <li key={index}>• {rec}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}

        <div className={`flex ${isMobileBreakpoint ? 'flex-col' : 'flex-row'} h-full`}>
          {/* Category Sidebar */}
          <div className={`
            border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900
            ${isMobileBreakpoint ? 'border-r-0 border-b' : 'w-80'}
          `}>
            <div className="p-4 space-y-2">
              {categories.map((category) => (
                <CategoryHeader
                  key={category.id}
                  category={category.id}
                  title={category.title}
                  icon={category.icon}
                  description={category.description}
                />
              ))}
            </div>
          </div>

          {/* Content */}
          <div className={`
            flex-1 p-6 overflow-y-auto
            ${isMobileBreakpoint ? 'h-full' : 'max-h-[60vh]'}
          `}>
            {/* Vision & Display */}
            {activeCategory === 'vision' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Vision & Display Settings
                </h3>
                
                <ExpandableSection title="Basic Display Options" id="vision-basic" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          High Contrast Mode
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Increase contrast for better visibility
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.vision.high_contrast}
                        onChange={(value) => updateVisionSetting('high_contrast', value)}
                        ariaLabel="Toggle high contrast mode"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Reduce Motion
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Minimize animations and transitions
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.vision.reduce_motion}
                        onChange={(value) => updateVisionSetting('reduce_motion', value)}
                        ariaLabel="Toggle reduced motion"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Remove Animations
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Completely disable all animations
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.vision.remove_animations}
                        onChange={(value) => updateVisionSetting('remove_animations', value)}
                        ariaLabel="Toggle remove animations"
                      />
                    </div>
                  </div>
                </ExpandableSection>
                
                <ExpandableSection title="Text & Typography" id="vision-text">
                  <div className="space-y-4 pt-4">
                    <SliderControl
                      label="Font Size Scale"
                      value={preferences.vision.font_size_scale}
                      min={0.8}
                      max={2.0}
                      step={0.1}
                      unit="x"
                      onChange={(value) => updateVisionSetting('font_size_scale', value)}
                      ariaLabel="Adjust font size scale"
                    />
                    
                    <SliderControl
                      label="Line Height Scale"
                      value={preferences.vision.line_height_scale}
                      min={1.0}
                      max={2.0}
                      step={0.1}
                      unit="x"
                      onChange={(value) => updateVisionSetting('line_height_scale', value)}
                      ariaLabel="Adjust line height scale"
                    />
                    
                    <SliderControl
                      label="Letter Spacing"
                      value={preferences.vision.letter_spacing}
                      min={-0.05}
                      max={0.1}
                      step={0.01}
                      unit="em"
                      onChange={(value) => updateVisionSetting('letter_spacing', value)}
                      ariaLabel="Adjust letter spacing"
                    />
                  </div>
                </ExpandableSection>
                
                <ExpandableSection title="Color & Vision Support" id="vision-color">
                  <div className="space-y-4 pt-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Color Blind Support
                      </label>
                      <select
                        value={preferences.vision.color_blind_mode}
                        onChange={(e) => updateVisionSetting('color_blind_mode', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        aria-label="Select color blind support mode"
                      >
                        <option value="none">None</option>
                        <option value="protanopia">Protanopia (Red-blind)</option>
                        <option value="deuteranopia">Deuteranopia (Green-blind)</option>
                        <option value="tritanopia">Tritanopia (Blue-blind)</option>
                        <option value="monochrome">Monochrome</option>
                      </select>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Reduce Transparency
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Make transparent elements more opaque
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.vision.reduce_transparency}
                        onChange={(value) => updateVisionSetting('reduce_transparency', value)}
                        ariaLabel="Toggle reduce transparency"
                      />
                    </div>
                  </div>
                </ExpandableSection>
              </div>
            )}

            {/* Motor & Input */}
            {activeCategory === 'motor' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Motor & Input Settings
                </h3>
                
                <ExpandableSection title="Keyboard Navigation" id="motor-keyboard" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Keyboard Navigation Only
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Optimize interface for keyboard-only navigation
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.motor.keyboard_navigation_only}
                        onChange={(value) => updateMotorSetting('keyboard_navigation_only', value)}
                        ariaLabel="Toggle keyboard navigation only"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Sticky Keys
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Allow modifier keys to be pressed sequentially
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.motor.sticky_keys}
                        onChange={(value) => updateMotorSetting('sticky_keys', value)}
                        ariaLabel="Toggle sticky keys"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Slow Keys
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Add delay before key presses are registered
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.motor.slow_keys}
                        onChange={(value) => updateMotorSetting('slow_keys', value)}
                        ariaLabel="Toggle slow keys"
                      />
                    </div>
                    
                    {preferences.motor.slow_keys && (
                      <SliderControl
                        label="Slow Keys Delay"
                        value={preferences.motor.slow_keys_delay}
                        min={100}
                        max={2000}
                        step={100}
                        unit="ms"
                        onChange={(value) => updateMotorSetting('slow_keys_delay', value)}
                        ariaLabel="Adjust slow keys delay"
                      />
                    )}
                  </div>
                </ExpandableSection>
                
                <ExpandableSection title="Touch & Click Settings" id="motor-touch">
                  <div className="space-y-4 pt-4">
                    <SliderControl
                      label="Touch Target Size"
                      value={preferences.motor.touch_target_size}
                      min={24}
                      max={64}
                      step={2}
                      unit="px"
                      onChange={(value) => updateMotorSetting('touch_target_size', value)}
                      ariaLabel="Adjust touch target size"
                    />
                    
                    <SliderControl
                      label="Click Timeout"
                      value={preferences.motor.click_timeout}
                      min={500}
                      max={3000}
                      step={100}
                      unit="ms"
                      onChange={(value) => updateMotorSetting('click_timeout', value)}
                      ariaLabel="Adjust click timeout"
                    />
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Smooth Scrolling
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Enable smooth page scrolling animations
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.motor.smooth_scrolling}
                        onChange={(value) => updateMotorSetting('smooth_scrolling', value)}
                        ariaLabel="Toggle smooth scrolling"
                      />
                    </div>
                  </div>
                </ExpandableSection>
              </div>
            )}

            {/* Cognitive & Learning */}
            {activeCategory === 'cognitive' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Cognitive & Learning Settings
                </h3>
                
                <ExpandableSection title="Interface Simplification" id="cognitive-simple" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Simplified Interface
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Show only essential interface elements
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.simplified_interface}
                        onChange={(value) => updateCognitiveSetting('simplified_interface', value)}
                        ariaLabel="Toggle simplified interface"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Reduce Cognitive Load
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Minimize distracting elements and information
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.reduce_cognitive_load}
                        onChange={(value) => updateCognitiveSetting('reduce_cognitive_load', value)}
                        ariaLabel="Toggle reduce cognitive load"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Distraction Free Mode
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Hide non-essential UI elements during tasks
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.distraction_free_mode}
                        onChange={(value) => updateCognitiveSetting('distraction_free_mode', value)}
                        ariaLabel="Toggle distraction free mode"
                      />
                    </div>
                  </div>
                </ExpandableSection>
                
                <ExpandableSection title="Reading & Comprehension" id="cognitive-reading">
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Reading Guide
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Show a reading guide line to help focus
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.reading_guide}
                        onChange={(value) => updateCognitiveSetting('reading_guide', value)}
                        ariaLabel="Toggle reading guide"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Show Keyboard Shortcuts
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Display keyboard shortcuts in tooltips
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.show_keyboard_shortcuts}
                        onChange={(value) => updateCognitiveSetting('show_keyboard_shortcuts', value)}
                        ariaLabel="Toggle show keyboard shortcuts"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Extended Time Limits
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Increase timeout periods for better accessibility
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.cognitive.time_limits_extended}
                        onChange={(value) => updateCognitiveSetting('time_limits_extended', value)}
                        ariaLabel="Toggle extended time limits"
                      />
                    </div>
                  </div>
                </ExpandableSection>
              </div>
            )}

            {/* Audio & Sound */}
            {activeCategory === 'audio' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Audio & Sound Settings
                </h3>
                
                <ExpandableSection title="Sound Effects" id="audio-effects" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Sound Effects
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Play sounds for user interface interactions
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.audio.sound_effects}
                        onChange={(value) => updateAudioSetting('sound_effects', value)}
                        ariaLabel="Toggle sound effects"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Audio Feedback
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Provide audio feedback for actions and states
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.audio.audio_feedback}
                        onChange={(value) => updateAudioSetting('audio_feedback', value)}
                        ariaLabel="Toggle audio feedback"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <button
                        onClick={() => playDemoAudio('success')}
                        className="px-3 py-2 bg-green-100 text-green-800 rounded hover:bg-green-200 transition-colors"
                        aria-label="Play success sound demo"
                      >
                        <Volume2 className="w-4 h-4 inline mr-1" />
                        Success Sound
                      </button>
                      
                      <button
                        onClick={() => playDemoAudio('error')}
                        className="px-3 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200 transition-colors"
                        aria-label="Play error sound demo"
                      >
                        <Volume2 className="w-4 h-4 inline mr-1" />
                        Error Sound
                      </button>
                    </div>
                  </div>
                </ExpandableSection>
                
                <ExpandableSection title="Captions & Subtitles" id="audio-captions">
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Enable Captions
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Show captions for audio and video content
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.audio.captions_enabled}
                        onChange={(value) => updateAudioSetting('captions_enabled', value)}
                        ariaLabel="Toggle captions"
                      />
                    </div>
                    
                    {preferences.audio.captions_enabled && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Caption Size
                          </label>
                          <select
                            value={preferences.audio.captions_size}
                            onChange={(e) => updateAudioSetting('captions_size', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            aria-label="Select caption size"
                          >
                            <option value="small">Small</option>
                            <option value="medium">Medium</option>
                            <option value="large">Large</option>
                            <option value="extra-large">Extra Large</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Caption Position
                          </label>
                          <select
                            value={preferences.audio.captions_position}
                            onChange={(e) => updateAudioSetting('captions_position', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            aria-label="Select caption position"
                          >
                            <option value="bottom">Bottom</option>
                            <option value="top">Top</option>
                            <option value="overlay">Overlay</option>
                          </select>
                        </div>
                      </>
                    )}
                  </div>
                </ExpandableSection>
              </div>
            )}

            {/* Screen Reader */}
            {activeCategory === 'screen_reader' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Screen Reader Settings
                </h3>
                
                <ExpandableSection title="Basic Settings" id="sr-basic" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Screen Reader Enabled
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Optimize interface for screen reader use
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.screen_reader.enabled}
                        onChange={(value) => updateScreenReaderSetting('enabled', value)}
                        ariaLabel="Toggle screen reader support"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Announce Live Regions
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Announce dynamic content changes
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.screen_reader.announce_live_regions}
                        onChange={(value) => updateScreenReaderSetting('announce_live_regions', value)}
                        ariaLabel="Toggle live region announcements"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Announce Page Changes
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Announce when navigating to new pages
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.screen_reader.announce_page_changes}
                        onChange={(value) => updateScreenReaderSetting('announce_page_changes', value)}
                        ariaLabel="Toggle page change announcements"
                      />
                    </div>
                    
                    <button
                      onClick={() => announceToUser('This is a test announcement for screen readers')}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      aria-label="Test screen reader announcement"
                    >
                      Test Announcement
                    </button>
                  </div>
                </ExpandableSection>
              </div>
            )}

            {/* Content & Language */}
            {activeCategory === 'content' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Content & Language Settings
                </h3>
                
                <ExpandableSection title="Content Structure" id="content-structure" defaultExpanded>
                  <div className="space-y-4 pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Plain Language Mode
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Use simpler language and shorter sentences
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.content.plain_language_mode}
                        onChange={(value) => updateContentSetting('plain_language_mode', value)}
                        ariaLabel="Toggle plain language mode"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Form Labels Always Visible
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Keep form labels visible instead of placeholders
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.content.form_labels_always_visible}
                        onChange={(value) => updateContentSetting('form_labels_always_visible', value)}
                        ariaLabel="Toggle form labels always visible"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900 dark:text-white">
                          Show Context Help
                        </label>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Display helpful context and explanations
                        </p>
                      </div>
                      <Toggle
                        enabled={preferences.content.context_help}
                        onChange={(value) => updateContentSetting('context_help', value)}
                        ariaLabel="Toggle context help"
                      />
                    </div>
                  </div>
                </ExpandableSection>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {usageStats && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Accessibility Score: {usageStats.accessibility_score}% •{' '}
                  {usageStats.preferences_updated} updates
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={resetPreferences}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                aria-label="Reset all accessibility preferences"
              >
                <RotateCcw className="w-4 h-4 inline mr-1" />
                Reset All
              </button>
            </div>
          </div>
        </div>

        {/* Demo Content for Testing */}
        <div ref={demoTextRef} className="sr-only" aria-live="polite" aria-atomic="true">
          {/* Screen reader announcements will appear here */}
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

export default AccessibilityOptions;