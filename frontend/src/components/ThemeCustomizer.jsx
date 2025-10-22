/**
 * T030 User Preferences Enhancement: Theme Customizer Component
 * React component for theme selection and customization with real-time preview
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Palette, Sun, Moon, Monitor, Eye, Settings, 
  Download, Upload, Save, RotateCcw, Check,
  Sliders, Zap, Contrast, Type, Layout
} from 'lucide-react';
import themeCustomizationService from '../services/themeCustomizationService.js';
import mobileInterfaceService from '../services/mobileInterfaceService.js';

const ThemeCustomizer = ({ 
  isOpen = false,
  onClose,
  showAdvanced = false,
  className = ''
}) => {
  const [currentTheme, setCurrentTheme] = useState(themeCustomizationService.getCurrentTheme());
  const [availableThemes, setAvailableThemes] = useState(new Map());
  const [userPreferences, setUserPreferences] = useState(themeCustomizationService.getUserPreferences());
  const [customizations, setCustomizations] = useState({});
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Load available themes
    setAvailableThemes(themeCustomizationService.getAllThemes());
    
    // Subscribe to theme changes
    const unsubscribe = themeCustomizationService.subscribe((event, data) => {
      if (event === 'theme-change') {
        setCurrentTheme(data.theme);
        setCustomizations(data.customizations || {});
      }
    });

    return unsubscribe;
  }, []);

  const themeOptions = [
    { id: 'auto', name: 'Auto (System)', icon: Monitor, description: 'Follow system preference' },
    { id: 'light', name: 'Light', icon: Sun, description: 'Light theme for daytime use' },
    { id: 'dark', name: 'Dark', icon: Moon, description: 'Dark theme for low-light environments' },
    { id: 'high-contrast', name: 'High Contrast', icon: Contrast, description: 'Enhanced contrast for accessibility' }
  ];

  const handleThemeChange = (themeId) => {
    const newPreferences = {
      ...userPreferences,
      themeMode: themeId,
      customizations: customizations
    };
    
    setUserPreferences(newPreferences);
    themeCustomizationService.saveUserPreferences(newPreferences);
    
    if (mobileInterfaceService.deviceInfo.device.isMobile) {
      mobileInterfaceService.hapticFeedback('light');
    }
  };

  const handleColorCustomization = (colorKey, value) => {
    const newCustomizations = {
      ...customizations,
      colors: {
        ...customizations.colors,
        [colorKey]: value
      }
    };
    
    setCustomizations(newCustomizations);
    
    if (previewMode) {
      themeCustomizationService.applyTheme(currentTheme.id, newCustomizations);
    }
  };

  const handleTypographyCustomization = (property, key, value) => {
    const newCustomizations = {
      ...customizations,
      typography: {
        ...customizations.typography,
        [property]: {
          ...customizations.typography?.[property],
          [key]: value
        }
      }
    };
    
    setCustomizations(newCustomizations);
    
    if (previewMode) {
      themeCustomizationService.applyTheme(currentTheme.id, newCustomizations);
    }
  };

  const handleSpacingCustomization = (key, value) => {
    const newCustomizations = {
      ...customizations,
      spacing: {
        ...customizations.spacing,
        [key]: value
      }
    };
    
    setCustomizations(newCustomizations);
    
    if (previewMode) {
      themeCustomizationService.applyTheme(currentTheme.id, newCustomizations);
    }
  };

  const saveCustomizations = () => {
    const newPreferences = {
      ...userPreferences,
      customizations: customizations
    };
    
    setUserPreferences(newPreferences);
    themeCustomizationService.saveUserPreferences(newPreferences);
    setIsCustomizing(false);
    
    if (mobileInterfaceService.deviceInfo.device.isMobile) {
      mobileInterfaceService.hapticFeedback('success');
    }
  };

  const resetCustomizations = () => {
    setCustomizations({});
    themeCustomizationService.applyTheme(currentTheme.id, {});
    
    if (mobileInterfaceService.deviceInfo.device.isMobile) {
      mobileInterfaceService.hapticFeedback('medium');
    }
  };

  const exportTheme = () => {
    try {
      const themeConfig = themeCustomizationService.exportTheme(currentTheme.id);
      const blob = new Blob([themeConfig], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentTheme.name.toLowerCase().replace(/\s+/g, '-')}-theme.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting theme:', error);
    }
  };

  const importTheme = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const themeConfig = e.target.result;
        const importedTheme = themeCustomizationService.importTheme(themeConfig);
        setAvailableThemes(themeCustomizationService.getAllThemes());
        handleThemeChange(importedTheme.id);
      } catch (error) {
        console.error('Error importing theme:', error);
        alert('Failed to import theme. Please check the file format.');
      }
    };
    reader.readAsText(file);
  };

  const ColorPicker = ({ label, colorKey, value, onChange }) => (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <div className="flex items-center space-x-2">
        <div
          className="w-8 h-8 rounded border border-gray-300 dark:border-gray-600 cursor-pointer"
          style={{ backgroundColor: value }}
          onClick={() => setShowColorPicker(showColorPicker === colorKey ? null : colorKey)}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(colorKey, e.target.value)}
          className="flex-1 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          placeholder="#000000"
        />
        {showColorPicker === colorKey && (
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(colorKey, e.target.value)}
            className="w-8 h-8 border-0 cursor-pointer"
          />
        )}
      </div>
    </div>
  );

  const isMobileBreakpoint = mobileInterfaceService.isMobileBreakpoint();

  if (!isOpen) return null;

  return (
    <div className={`
      fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50
      ${className}
    `}>
      <div className={`
        bg-white dark:bg-gray-800 rounded-lg shadow-xl max-h-[90vh] overflow-hidden
        ${isMobileBreakpoint ? 'w-full h-full m-4' : 'w-full max-w-4xl m-8'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Palette className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Theme Customizer
            </h2>
          </div>
          
          <div className="flex items-center space-x-2">
            {isCustomizing && (
              <>
                <button
                  onClick={() => setPreviewMode(!previewMode)}
                  className={`
                    px-3 py-1 text-sm rounded transition-colors
                    ${previewMode 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }
                  `}
                >
                  <Eye className="w-4 h-4 inline mr-1" />
                  Preview
                </button>
                
                <button
                  onClick={saveCustomizations}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                >
                  <Save className="w-4 h-4 inline mr-1" />
                  Save
                </button>
                
                <button
                  onClick={resetCustomizations}
                  className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                >
                  <RotateCcw className="w-4 h-4 inline mr-1" />
                  Reset
                </button>
              </>
            )}
            
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

        {/* Content */}
        <div className={`
          p-6 overflow-y-auto
          ${isMobileBreakpoint ? 'h-full' : 'max-h-[70vh]'}
        `}>
          <div className={`
            grid gap-6
            ${isMobileBreakpoint ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}
          `}>
            {/* Theme Selection */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Theme Selection
              </h3>
              
              <div className="grid gap-3">
                {themeOptions.map((option) => {
                  const Icon = option.icon;
                  const isSelected = userPreferences.themeMode === option.id;
                  
                  return (
                    <button
                      key={option.id}
                      onClick={() => handleThemeChange(option.id)}
                      className={`
                        p-4 rounded-lg border-2 transition-all text-left
                        ${isSelected 
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }
                      `}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className={`
                          w-5 h-5
                          ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}
                        `} />
                        <div className="flex-1">
                          <div className={`
                            font-medium
                            ${isSelected ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-white'}
                          `}>
                            {option.name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {option.description}
                          </div>
                        </div>
                        {isSelected && (
                          <Check className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Theme Actions */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                <Sliders className="w-5 h-5 mr-2" />
                Theme Actions
              </h3>
              
              <div className="grid gap-3">
                <button
                  onClick={() => setIsCustomizing(!isCustomizing)}
                  className={`
                    p-4 rounded-lg border-2 transition-all text-left
                    ${isCustomizing 
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }
                  `}
                >
                  <div className="flex items-center space-x-3">
                    <Zap className={`
                      w-5 h-5
                      ${isCustomizing ? 'text-purple-600 dark:text-purple-400' : 'text-gray-500 dark:text-gray-400'}
                    `} />
                    <div className="flex-1">
                      <div className={`
                        font-medium
                        ${isCustomizing ? 'text-purple-900 dark:text-purple-100' : 'text-gray-900 dark:text-white'}
                      `}>
                        Customize Theme
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Advanced color and typography customization
                      </div>
                    </div>
                  </div>
                </button>
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={exportTheme}
                    className="p-3 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Download className="w-4 h-4 mx-auto mb-1 text-gray-600 dark:text-gray-400" />
                    <div className="text-sm text-gray-900 dark:text-white">Export</div>
                  </button>
                  
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-3 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Upload className="w-4 h-4 mx-auto mb-1 text-gray-600 dark:text-gray-400" />
                    <div className="text-sm text-gray-900 dark:text-white">Import</div>
                  </button>
                </div>
              </div>
            </div>

            {/* Advanced Customization */}
            {isCustomizing && (
              <div className="lg:col-span-2 space-y-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
                  <Type className="w-5 h-5 mr-2" />
                  Advanced Customization
                </h3>
                
                <div className={`
                  grid gap-6
                  ${isMobileBreakpoint ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}
                `}>
                  {/* Color Customization */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Colors</h4>
                    <div className="space-y-3">
                      <ColorPicker
                        label="Primary"
                        colorKey="primary"
                        value={customizations.colors?.primary || currentTheme?.colors?.primary || '#3b82f6'}
                        onChange={handleColorCustomization}
                      />
                      <ColorPicker
                        label="Background"
                        colorKey="background"
                        value={customizations.colors?.background || currentTheme?.colors?.background || '#ffffff'}
                        onChange={handleColorCustomization}
                      />
                      <ColorPicker
                        label="Text Primary"
                        colorKey="textPrimary"
                        value={customizations.colors?.textPrimary || currentTheme?.colors?.textPrimary || '#111827'}
                        onChange={handleColorCustomization}
                      />
                    </div>
                  </div>
                  
                  {/* Typography */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Typography</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Base Font Size
                        </label>
                        <select
                          value={customizations.typography?.fontSize?.base || '1rem'}
                          onChange={(e) => handleTypographyCustomization('fontSize', 'base', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        >
                          <option value="0.875rem">Small (14px)</option>
                          <option value="1rem">Medium (16px)</option>
                          <option value="1.125rem">Large (18px)</option>
                          <option value="1.25rem">Extra Large (20px)</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Font Weight
                        </label>
                        <select
                          value={customizations.typography?.fontWeight?.normal || '400'}
                          onChange={(e) => handleTypographyCustomization('fontWeight', 'normal', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        >
                          <option value="300">Light</option>
                          <option value="400">Normal</option>
                          <option value="500">Medium</option>
                          <option value="600">Semibold</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  
                  {/* Spacing */}
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Spacing</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Base Spacing
                        </label>
                        <input
                          type="range"
                          min="0.5"
                          max="2"
                          step="0.1"
                          value={parseFloat(customizations.spacing?.md?.replace('rem', '') || '1')}
                          onChange={(e) => handleSpacingCustomization('md', `${e.target.value}rem`)}
                          className="w-full"
                        />
                        <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
                          {customizations.spacing?.md || '1rem'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Hidden file input for theme import */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={importTheme}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default ThemeCustomizer;