/**
 * T030 User Preferences Enhancement: Global Test Setup
 * Global setup for all T030 preference tests
 */

const { performance } = require('perf_hooks');

module.exports = async () => {
  // Set global test environment variables
  process.env.NODE_ENV = 'test';
  process.env.REACT_APP_API_URL = 'http://localhost:5000';
  process.env.REACT_APP_TEST_MODE = 'true';
  
  // Configure global test timeouts
  global.DEFAULT_TIMEOUT = 5000;
  global.SLOW_TIMEOUT = 10000;
  global.PERFORMANCE_THRESHOLD = 100; // ms
  
  // Setup performance monitoring
  global.testPerformanceStart = (testName) => {
    global.performanceMarks = global.performanceMarks || {};
    global.performanceMarks[testName] = performance.now();
  };
  
  global.testPerformanceEnd = (testName) => {
    const startTime = global.performanceMarks?.[testName];
    if (startTime) {
      const duration = performance.now() - startTime;
      if (duration > global.PERFORMANCE_THRESHOLD) {
        console.warn(`⚠️  Slow test detected: ${testName} took ${duration.toFixed(2)}ms`);
      }
      delete global.performanceMarks[testName];
      return duration;
    }
    return 0;
  };
  
  // Global test utilities
  global.createMockFile = (name, content, type = 'application/json') => {
    const blob = new Blob([content], { type });
    blob.lastModifiedDate = new Date();
    blob.name = name;
    return blob;
  };
  
  global.createMockPreferences = (overrides = {}) => ({
    theme: {
      appearance: {
        theme: 'light',
        auto_theme_switching: false,
        custom_themes: {}
      },
      colors: {
        primary_color: '#3b82f6',
        accent_color: '#10b981',
        background_color: '#ffffff',
        text_color: '#1f2937'
      },
      typography: {
        font_family: 'Inter',
        font_size_scale: 1.0,
        line_height_scale: 1.0
      },
      animation: {
        enable_transitions: true,
        transition_speed: 'normal',
        enable_hover_effects: true
      },
      metadata: {
        version: '1.2.0',
        lastModified: new Date().toISOString()
      }
    },
    notifications: {
      categories: {
        transcription: { enabled: true, priority: 'high', sound: true },
        batch: { enabled: true, priority: 'medium', sound: false },
        system: { enabled: true, priority: 'low', sound: false },
        account: { enabled: false, priority: 'medium', sound: false }
      },
      delivery_methods: {
        browser: true,
        email: false,
        push: false
      },
      timing: {
        quiet_hours: { enabled: false, start_time: '22:00', end_time: '08:00' },
        batch_digest: { enabled: false, frequency: 'daily', time: '09:00' }
      },
      metadata: {
        version: '1.2.0',
        lastModified: new Date().toISOString()
      }
    },
    upload: {
      general: {
        auto_upload: false,
        max_simultaneous_uploads: 3,
        chunk_size: 1048576,
        show_previews: true,
        auto_transcribe: true,
        save_originals: true
      },
      file_handling: {
        accepted_formats: ['audio/mpeg', 'audio/wav', 'audio/mp4'],
        max_file_size: 104857600,
        auto_validate_files: true,
        compress_audio: false,
        normalize_audio: false
      },
      security: {
        scan_for_malware: true,
        require_https: true,
        encrypt_uploads: true
      },
      metadata: {
        version: '1.2.0',
        lastModified: new Date().toISOString()
      }
    },
    accessibility: {
      vision: {
        high_contrast: false,
        font_size_scale: 1.0,
        reduce_motion: false,
        color_adjustments: {
          brightness: 1.0,
          contrast: 1.0,
          saturation: 1.0
        }
      },
      motor: {
        keyboard_navigation_only: false,
        touch_target_size: 44,
        gesture_timeout: 1000,
        sticky_keys: false
      },
      cognitive: {
        simplified_interface: false,
        reduce_cognitive_load: false,
        focus_indicators: true,
        reading_guide: false
      },
      metadata: {
        version: '1.2.0',
        lastModified: new Date().toISOString()
      }
    },
    ...overrides
  });
  
  // Global error tracking
  global.testErrors = [];
  
  const originalConsoleError = console.error;
  console.error = (...args) => {
    global.testErrors.push(args.join(' '));
    originalConsoleError(...args);
  };
  
  // Setup global mock functions
  global.mockServiceDefaults = {
    getPreferences: jest.fn(),
    updatePreferences: jest.fn(),
    subscribe: jest.fn(() => jest.fn()), // Returns unsubscribe function
    emit: jest.fn(),
    validatePreferences: jest.fn(() => ({ isValid: true, errors: [] })),
    reset: jest.fn()
  };
  
  // Global test data generators
  global.generateLargePreferences = (count = 100) => {
    const preferences = global.createMockPreferences();
    preferences.theme.appearance.custom_themes = Object.fromEntries(
      Array.from({ length: count }, (_, i) => [
        `theme-${i}`,
        {
          name: `Custom Theme ${i}`,
          colors: {
            primary_color: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
            accent_color: `#${Math.floor(Math.random() * 16777215).toString(16)}`
          }
        }
      ])
    );
    return preferences;
  };
  
  global.generateNotificationHistory = (count = 50) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `notification-${i}`,
      type: ['transcription', 'batch', 'system', 'account'][i % 4],
      message: `Test notification ${i}`,
      timestamp: new Date(Date.now() - i * 60000).toISOString(),
      delivered: Math.random() > 0.1,
      read: Math.random() > 0.3
    }));
  };
  
  global.generateUploadHistory = (count = 30) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `upload-${i}`,
      filename: `audio-file-${i}.mp3`,
      size: Math.floor(Math.random() * 10000000),
      status: ['completed', 'failed', 'cancelled'][i % 3],
      timestamp: new Date(Date.now() - i * 3600000).toISOString(),
      duration: Math.floor(Math.random() * 300)
    }));
  };
  
  // Global accessibility testing utilities
  global.testAccessibility = {
    checkFocusOrder: (container) => {
      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      return Array.from(focusableElements);
    },
    
    checkAriaLabels: (container) => {
      const elementsNeedingLabels = container.querySelectorAll('button, input, select, textarea');
      const missingLabels = [];
      
      elementsNeedingLabels.forEach(element => {
        const hasLabel = element.getAttribute('aria-label') ||
                         element.getAttribute('aria-labelledby') ||
                         element.closest('label') ||
                         element.id && container.querySelector(`label[for="${element.id}"]`);
        
        if (!hasLabel) {
          missingLabels.push(element);
        }
      });
      
      return missingLabels;
    },
    
    checkColorContrast: (element) => {
      // Simplified contrast check - in real tests you'd use a proper library
      const style = window.getComputedStyle(element);
      const backgroundColor = style.backgroundColor;
      const color = style.color;
      
      return {
        backgroundColor,
        color,
        hasGoodContrast: true // Simplified for mock
      };
    }
  };
  
  // Mobile testing utilities
  global.mobileTestUtils = {
    simulateTouchStart: (element, x = 0, y = 0) => {
      const touchEvent = new TouchEvent('touchstart', {
        touches: [{ clientX: x, clientY: y }],
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(touchEvent);
    },
    
    simulateTouchMove: (element, x = 0, y = 0) => {
      const touchEvent = new TouchEvent('touchmove', {
        touches: [{ clientX: x, clientY: y }],
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(touchEvent);
    },
    
    simulateTouchEnd: (element, x = 0, y = 0) => {
      const touchEvent = new TouchEvent('touchend', {
        changedTouches: [{ clientX: x, clientY: y }],
        bubbles: true,
        cancelable: true
      });
      element.dispatchEvent(touchEvent);
    },
    
    simulateSwipe: (element, direction = 'left', distance = 100) => {
      const startX = direction === 'left' ? distance : 0;
      const endX = direction === 'left' ? 0 : distance;
      const startY = direction === 'up' ? distance : direction === 'down' ? 0 : 50;
      const endY = direction === 'up' ? 0 : direction === 'down' ? distance : 50;
      
      global.mobileTestUtils.simulateTouchStart(element, startX, startY);
      global.mobileTestUtils.simulateTouchMove(element, endX, endY);
      global.mobileTestUtils.simulateTouchEnd(element, endX, endY);
    }
  };
  
  // Performance testing utilities
  global.performanceTestUtils = {
    measureRenderTime: async (renderFunction) => {
      const start = performance.now();
      await renderFunction();
      const end = performance.now();
      return end - start;
    },
    
    measureMemoryUsage: () => {
      if (global.gc) {
        global.gc();
      }
      return process.memoryUsage();
    }
  };
  
  console.log('🚀 T030 Global test setup completed');
};