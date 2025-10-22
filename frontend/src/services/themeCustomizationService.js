/**
 * T030 User Preferences Enhancement: Theme Customization Service
 * Comprehensive theme management with dark/light modes and dynamic customization
 */

class ThemeCustomizationService {
  constructor() {
    this.themes = new Map();
    this.currentTheme = null;
    this.systemPreference = null;
    this.subscribers = new Set();
    this.cssVariables = new Map();
    this.customThemes = new Map();
    
    this.initializeDefaultThemes();
    this.detectSystemPreference();
    this.loadUserPreferences();
    this.setupEventListeners();
  }

  /**
   * Initialize default theme configurations
   */
  initializeDefaultThemes() {
    // Light theme
    this.themes.set('light', {
      id: 'light',
      name: 'Light',
      type: 'light',
      colors: {
        // Primary colors
        primary: '#3b82f6',
        primaryHover: '#2563eb',
        primaryText: '#ffffff',
        
        // Secondary colors
        secondary: '#6b7280',
        secondaryHover: '#4b5563',
        secondaryText: '#ffffff',
        
        // Background colors
        background: '#ffffff',
        backgroundSecondary: '#f9fafb',
        backgroundTertiary: '#f3f4f6',
        
        // Surface colors
        surface: '#ffffff',
        surfaceHover: '#f9fafb',
        surfaceBorder: '#e5e7eb',
        
        // Text colors
        textPrimary: '#111827',
        textSecondary: '#6b7280',
        textTertiary: '#9ca3af',
        textInverse: '#ffffff',
        
        // Status colors
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6',
        
        // Interactive colors
        accent: '#8b5cf6',
        accentHover: '#7c3aed',
        link: '#3b82f6',
        linkHover: '#2563eb'
      },
      typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem'
        },
        fontWeight: {
          light: '300',
          normal: '400',
          medium: '500',
          semibold: '600',
          bold: '700'
        },
        lineHeight: {
          tight: '1.25',
          normal: '1.5',
          relaxed: '1.75'
        }
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '3rem'
      },
      borderRadius: {
        sm: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        full: '9999px'
      },
      shadows: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }
    });

    // Dark theme
    this.themes.set('dark', {
      id: 'dark',
      name: 'Dark',
      type: 'dark',
      colors: {
        // Primary colors
        primary: '#3b82f6',
        primaryHover: '#2563eb',
        primaryText: '#ffffff',
        
        // Secondary colors
        secondary: '#6b7280',
        secondaryHover: '#9ca3af',
        secondaryText: '#ffffff',
        
        // Background colors
        background: '#111827',
        backgroundSecondary: '#1f2937',
        backgroundTertiary: '#374151',
        
        // Surface colors
        surface: '#1f2937',
        surfaceHover: '#374151',
        surfaceBorder: '#4b5563',
        
        // Text colors
        textPrimary: '#f9fafb',
        textSecondary: '#d1d5db',
        textTertiary: '#9ca3af',
        textInverse: '#111827',
        
        // Status colors
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6',
        
        // Interactive colors
        accent: '#8b5cf6',
        accentHover: '#7c3aed',
        link: '#60a5fa',
        linkHover: '#3b82f6'
      },
      typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: {
          xs: '0.75rem',
          sm: '0.875rem',
          base: '1rem',
          lg: '1.125rem',
          xl: '1.25rem',
          '2xl': '1.5rem',
          '3xl': '1.875rem',
          '4xl': '2.25rem'
        },
        fontWeight: {
          light: '300',
          normal: '400',
          medium: '500',
          semibold: '600',
          bold: '700'
        },
        lineHeight: {
          tight: '1.25',
          normal: '1.5',
          relaxed: '1.75'
        }
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '3rem'
      },
      borderRadius: {
        sm: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        full: '9999px'
      },
      shadows: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)'
      }
    });

    // High contrast theme
    this.themes.set('high-contrast', {
      id: 'high-contrast',
      name: 'High Contrast',
      type: 'high-contrast',
      colors: {
        primary: '#000000',
        primaryHover: '#333333',
        primaryText: '#ffffff',
        secondary: '#666666',
        secondaryHover: '#999999',
        secondaryText: '#ffffff',
        background: '#ffffff',
        backgroundSecondary: '#f0f0f0',
        backgroundTertiary: '#e0e0e0',
        surface: '#ffffff',
        surfaceHover: '#f0f0f0',
        surfaceBorder: '#000000',
        textPrimary: '#000000',
        textSecondary: '#333333',
        textTertiary: '#666666',
        textInverse: '#ffffff',
        success: '#008000',
        warning: '#ff8c00',
        error: '#ff0000',
        info: '#0000ff',
        accent: '#800080',
        accentHover: '#600060',
        link: '#0000ff',
        linkHover: '#000080'
      },
      typography: {
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: {
          xs: '0.875rem',
          sm: '1rem',
          base: '1.125rem',
          lg: '1.25rem',
          xl: '1.375rem',
          '2xl': '1.625rem',
          '3xl': '2rem',
          '4xl': '2.5rem'
        },
        fontWeight: {
          light: '400',
          normal: '600',
          medium: '700',
          semibold: '700',
          bold: '800'
        },
        lineHeight: {
          tight: '1.3',
          normal: '1.6',
          relaxed: '1.8'
        }
      },
      spacing: {
        xs: '0.375rem',
        sm: '0.75rem',
        md: '1.25rem',
        lg: '1.75rem',
        xl: '2.25rem',
        '2xl': '3.5rem'
      },
      borderRadius: {
        sm: '0.125rem',
        md: '0.25rem',
        lg: '0.375rem',
        xl: '0.5rem',
        full: '9999px'
      },
      shadows: {
        sm: '0 2px 4px 0 rgba(0, 0, 0, 0.3)',
        md: '0 4px 8px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
        lg: '0 8px 16px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
        xl: '0 16px 32px -5px rgba(0, 0, 0, 0.4), 0 8px 16px -5px rgba(0, 0, 0, 0.3)'
      }
    });
  }

  /**
   * Detect system color scheme preference
   */
  detectSystemPreference() {
    if (window.matchMedia) {
      const darkQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
      
      this.systemPreference = {
        colorScheme: darkQuery.matches ? 'dark' : 'light',
        highContrast: highContrastQuery.matches,
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
      };
      
      // Listen for system preference changes
      darkQuery.addEventListener('change', (e) => {
        this.systemPreference.colorScheme = e.matches ? 'dark' : 'light';
        this.notifySubscribers('system-preference-change', this.systemPreference);
        
        // Auto-switch if user has automatic mode enabled
        const userPrefs = this.getUserPreferences();
        if (userPrefs.themeMode === 'auto') {
          this.applyTheme(this.systemPreference.colorScheme);
        }
      });
      
      highContrastQuery.addEventListener('change', (e) => {
        this.systemPreference.highContrast = e.matches;
        this.notifySubscribers('system-preference-change', this.systemPreference);
        
        // Auto-apply high contrast if enabled
        if (e.matches) {
          this.applyTheme('high-contrast');
        }
      });
    }
  }

  /**
   * Load user preferences from storage
   */
  loadUserPreferences() {
    try {
      const stored = localStorage.getItem('whisper-theme-preferences');
      if (stored) {
        const preferences = JSON.parse(stored);
        this.applyUserPreferences(preferences);
      } else {
        // Use system preference as default
        const defaultTheme = this.systemPreference?.colorScheme || 'light';
        this.applyTheme(defaultTheme);
      }
    } catch (error) {
      console.error('Error loading theme preferences:', error);
      this.applyTheme('light'); // Fallback to light theme
    }
  }

  /**
   * Apply user preferences
   */
  applyUserPreferences(preferences) {
    const { themeMode, customizations } = preferences;
    
    let themeToApply;
    if (themeMode === 'auto') {
      themeToApply = this.systemPreference?.highContrast ? 'high-contrast' : 
                    this.systemPreference?.colorScheme || 'light';
    } else {
      themeToApply = themeMode;
    }
    
    this.applyTheme(themeToApply, customizations);
  }

  /**
   * Apply a theme to the document
   */
  applyTheme(themeId, customizations = {}) {
    const theme = this.themes.get(themeId);
    if (!theme) {
      console.error(`Theme '${themeId}' not found`);
      return;
    }

    this.currentTheme = { ...theme };
    
    // Apply customizations
    if (customizations && Object.keys(customizations).length > 0) {
      this.applyCustomizations(customizations);
    }

    // Generate CSS variables
    this.generateCSSVariables();
    
    // Apply to document
    this.applyCSSVariables();
    
    // Update body classes
    this.updateBodyClasses();
    
    // Notify subscribers
    this.notifySubscribers('theme-change', {
      theme: this.currentTheme,
      customizations
    });
  }

  /**
   * Apply customizations to current theme
   */
  applyCustomizations(customizations) {
    if (customizations.colors) {
      this.currentTheme.colors = {
        ...this.currentTheme.colors,
        ...customizations.colors
      };
    }
    
    if (customizations.typography) {
      this.currentTheme.typography = {
        ...this.currentTheme.typography,
        ...customizations.typography
      };
    }
    
    if (customizations.spacing) {
      this.currentTheme.spacing = {
        ...this.currentTheme.spacing,
        ...customizations.spacing
      };
    }
    
    if (customizations.borderRadius) {
      this.currentTheme.borderRadius = {
        ...this.currentTheme.borderRadius,
        ...customizations.borderRadius
      };
    }
  }

  /**
   * Generate CSS variables from theme
   */
  generateCSSVariables() {
    this.cssVariables.clear();
    
    // Colors
    Object.entries(this.currentTheme.colors).forEach(([key, value]) => {
      this.cssVariables.set(`--color-${this.kebabCase(key)}`, value);
    });
    
    // Typography
    Object.entries(this.currentTheme.typography.fontSize).forEach(([key, value]) => {
      this.cssVariables.set(`--font-size-${key}`, value);
    });
    
    Object.entries(this.currentTheme.typography.fontWeight).forEach(([key, value]) => {
      this.cssVariables.set(`--font-weight-${key}`, value);
    });
    
    Object.entries(this.currentTheme.typography.lineHeight).forEach(([key, value]) => {
      this.cssVariables.set(`--line-height-${key}`, value);
    });
    
    this.cssVariables.set('--font-family', this.currentTheme.typography.fontFamily);
    
    // Spacing
    Object.entries(this.currentTheme.spacing).forEach(([key, value]) => {
      this.cssVariables.set(`--spacing-${key}`, value);
    });
    
    // Border radius
    Object.entries(this.currentTheme.borderRadius).forEach(([key, value]) => {
      this.cssVariables.set(`--border-radius-${key}`, value);
    });
    
    // Shadows
    Object.entries(this.currentTheme.shadows).forEach(([key, value]) => {
      this.cssVariables.set(`--shadow-${key}`, value);
    });
  }

  /**
   * Apply CSS variables to document
   */
  applyCSSVariables() {
    const root = document.documentElement;
    
    // Clear existing theme variables
    Array.from(root.style).forEach(property => {
      if (property.startsWith('--color-') || 
          property.startsWith('--font-') || 
          property.startsWith('--spacing-') || 
          property.startsWith('--border-radius-') || 
          property.startsWith('--shadow-') ||
          property.startsWith('--line-height-')) {
        root.style.removeProperty(property);
      }
    });
    
    // Apply new variables
    this.cssVariables.forEach((value, property) => {
      root.style.setProperty(property, value);
    });
  }

  /**
   * Update body classes for theme
   */
  updateBodyClasses() {
    const body = document.body;
    
    // Remove existing theme classes
    body.className = body.className
      .split(' ')
      .filter(cls => !cls.startsWith('theme-'))
      .join(' ');
    
    // Add current theme classes
    body.classList.add(`theme-${this.currentTheme.id}`);
    body.classList.add(`theme-type-${this.currentTheme.type}`);
    
    // Add system preference classes
    if (this.systemPreference?.reducedMotion) {
      body.classList.add('prefers-reduced-motion');
    }
    
    if (this.systemPreference?.highContrast) {
      body.classList.add('prefers-high-contrast');
    }
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Listen for storage changes (multi-tab sync)
    window.addEventListener('storage', (e) => {
      if (e.key === 'whisper-theme-preferences' && e.newValue) {
        try {
          const preferences = JSON.parse(e.newValue);
          this.applyUserPreferences(preferences);
        } catch (error) {
          console.error('Error parsing theme preferences from storage:', error);
        }
      }
    });
  }

  /**
   * Save user preferences
   */
  saveUserPreferences(preferences) {
    try {
      localStorage.setItem('whisper-theme-preferences', JSON.stringify(preferences));
      this.applyUserPreferences(preferences);
    } catch (error) {
      console.error('Error saving theme preferences:', error);
    }
  }

  /**
   * Get user preferences
   */
  getUserPreferences() {
    try {
      const stored = localStorage.getItem('whisper-theme-preferences');
      return stored ? JSON.parse(stored) : {
        themeMode: 'auto',
        customizations: {}
      };
    } catch (error) {
      console.error('Error getting theme preferences:', error);
      return {
        themeMode: 'auto',
        customizations: {}
      };
    }
  }

  /**
   * Create custom theme
   */
  createCustomTheme(name, baseThemeId, customizations) {
    const baseTheme = this.themes.get(baseThemeId);
    if (!baseTheme) {
      throw new Error(`Base theme '${baseThemeId}' not found`);
    }

    const customTheme = {
      id: `custom-${Date.now()}`,
      name,
      type: baseTheme.type,
      isCustom: true,
      baseTheme: baseThemeId,
      ...JSON.parse(JSON.stringify(baseTheme)) // Deep clone
    };

    // Apply customizations
    Object.assign(customTheme, customizations);
    
    this.customThemes.set(customTheme.id, customTheme);
    this.saveCustomThemes();
    
    return customTheme;
  }

  /**
   * Load custom themes
   */
  loadCustomThemes() {
    try {
      const stored = localStorage.getItem('whisper-custom-themes');
      if (stored) {
        const customThemes = JSON.parse(stored);
        customThemes.forEach(theme => {
          this.customThemes.set(theme.id, theme);
        });
      }
    } catch (error) {
      console.error('Error loading custom themes:', error);
    }
  }

  /**
   * Save custom themes
   */
  saveCustomThemes() {
    try {
      const customThemes = Array.from(this.customThemes.values());
      localStorage.setItem('whisper-custom-themes', JSON.stringify(customThemes));
    } catch (error) {
      console.error('Error saving custom themes:', error);
    }
  }

  /**
   * Get all available themes
   */
  getAllThemes() {
    const allThemes = new Map();
    
    // Add default themes
    this.themes.forEach((theme, id) => {
      allThemes.set(id, theme);
    });
    
    // Add custom themes
    this.customThemes.forEach((theme, id) => {
      allThemes.set(id, theme);
    });
    
    return allThemes;
  }

  /**
   * Subscribe to theme changes
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notify subscribers
   */
  notifySubscribers(event, data) {
    this.subscribers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in theme subscriber:', error);
      }
    });
  }

  /**
   * Utility: Convert camelCase to kebab-case
   */
  kebabCase(str) {
    return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
  }

  /**
   * Get current theme information
   */
  getCurrentTheme() {
    return this.currentTheme;
  }

  /**
   * Check if dark mode is active
   */
  isDarkMode() {
    return this.currentTheme?.type === 'dark';
  }

  /**
   * Check if high contrast mode is active
   */
  isHighContrast() {
    return this.currentTheme?.type === 'high-contrast';
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    const currentId = this.currentTheme?.id;
    const newTheme = currentId === 'dark' ? 'light' : 'dark';
    
    this.applyTheme(newTheme);
    this.saveUserPreferences({
      themeMode: newTheme,
      customizations: this.getUserPreferences().customizations
    });
  }

  /**
   * Export theme configuration
   */
  exportTheme(themeId) {
    const theme = this.getAllThemes().get(themeId);
    if (!theme) {
      throw new Error(`Theme '${themeId}' not found`);
    }
    
    return JSON.stringify(theme, null, 2);
  }

  /**
   * Import theme configuration
   */
  importTheme(themeConfig) {
    try {
      const theme = typeof themeConfig === 'string' ? 
        JSON.parse(themeConfig) : themeConfig;
      
      if (!theme.id || !theme.name || !theme.colors) {
        throw new Error('Invalid theme configuration');
      }
      
      theme.isCustom = true;
      theme.id = `imported-${Date.now()}`;
      
      this.customThemes.set(theme.id, theme);
      this.saveCustomThemes();
      
      return theme;
    } catch (error) {
      console.error('Error importing theme:', error);
      throw error;
    }
  }
}

// Create singleton instance
const themeCustomizationService = new ThemeCustomizationService();

export default themeCustomizationService;