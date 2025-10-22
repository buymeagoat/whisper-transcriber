/**
 * T030 User Preferences Enhancement: Test Setup and Configuration
 * Comprehensive testing configuration for all preference components
 */

import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { expect, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Configure testing library
configure({
  testIdAttribute: 'data-testid',
  asyncUtilTimeout: 5000,
  computedStyleSupportsPseudoElements: true
});

// Setup MSW server for API mocking
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn'
  });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {}
  })
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback) => {
  return setTimeout(callback, 0);
};

global.cancelAnimationFrame = (id) => {
  clearTimeout(id);
};

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock
});

// Mock CSS custom properties support
if (!CSS?.supports) {
  global.CSS = {
    supports: () => true
  };
}

// Mock Notification API
global.Notification = {
  requestPermission: vi.fn(() => Promise.resolve('granted')),
  permission: 'granted'
};

// Mock Web Audio API for upload tests
global.AudioContext = vi.fn(() => ({
  createAnalyser: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn()
  })),
  createGain: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    gain: { value: 1 }
  })),
  createOscillator: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    frequency: { value: 440 }
  })),
  close: vi.fn(),
  suspend: vi.fn(),
  resume: vi.fn()
}));

// Mock File API
global.File = class File {
  constructor(bits, filename, options = {}) {
    this.bits = bits;
    this.name = filename;
    this.size = bits.reduce((acc, bit) => acc + (bit.length || bit.byteLength || 0), 0);
    this.type = options.type || '';
    this.lastModified = options.lastModified || Date.now();
  }
};

global.FileReader = class FileReader {
  constructor() {
    this.readyState = 0;
    this.result = null;
    this.error = null;
    this.onload = null;
    this.onerror = null;
    this.onabort = null;
    this.onloadstart = null;
    this.onloadend = null;
    this.onprogress = null;
  }

  readAsText(file) {
    setTimeout(() => {
      this.readyState = 2;
      this.result = file.bits.join('');
      if (this.onload) this.onload({ target: this });
    }, 0);
  }

  readAsDataURL(file) {
    setTimeout(() => {
      this.readyState = 2;
      this.result = `data:${file.type};base64,${btoa(file.bits.join(''))}`;
      if (this.onload) this.onload({ target: this });
    }, 0);
  }

  abort() {
    this.readyState = 2;
    if (this.onabort) this.onabort();
  }
};

// Mock navigator.vibrate for haptic feedback tests
Object.defineProperty(navigator, 'vibrate', {
  value: vi.fn(() => true),
  writable: true
});

// Mock navigator.mediaDevices for upload tests
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn(() => Promise.resolve({
      getTracks: () => [],
      getVideoTracks: () => [],
      getAudioTracks: () => []
    }))
  },
  writable: true
});

// Mock touch support
Object.defineProperty(navigator, 'maxTouchPoints', {
  value: 5,
  writable: true
});

// Mock screen orientation
Object.defineProperty(screen, 'orientation', {
  value: {
    angle: 0,
    type: 'portrait-primary',
    addEventListener: vi.fn(),
    removeEventListener: vi.fn()
  },
  writable: true
});

// Mock crypto for UUID generation
Object.defineProperty(window, 'crypto', {
  value: {
    getRandomValues: (arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    },
    randomUUID: () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    })
  }
});

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByType: vi.fn(() => []),
    getEntriesByName: vi.fn(() => [])
  }
});

// Mock URL.createObjectURL for file tests
Object.defineProperty(URL, 'createObjectURL', {
  value: vi.fn(() => 'blob:mock-url'),
  writable: true
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: vi.fn(),
  writable: true
});

// Error handling for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Global test utilities
global.testUtils = {
  // Mock service responses
  mockServiceSuccess: (service, method, response) => {
    service[method] = vi.fn().mockResolvedValue(response);
  },

  mockServiceError: (service, method, error) => {
    service[method] = vi.fn().mockRejectedValue(new Error(error));
  },

  // Mock component props
  createMockProps: (overrides = {}) => ({
    onClose: vi.fn(),
    onSave: vi.fn(),
    onCancel: vi.fn(),
    onChange: vi.fn(),
    onError: vi.fn(),
    ...overrides
  }),

  // Create mock preferences
  createMockPreferences: (type, overrides = {}) => {
    const defaults = {
      theme: {
        appearance: { theme: 'light', auto_theme_switching: false },
        colors: { primary_color: '#3b82f6' },
        metadata: { version: '1.2.0' }
      },
      notifications: {
        categories: { transcription: { enabled: true } },
        delivery_methods: { browser: true },
        metadata: { version: '1.2.0' }
      },
      upload: {
        general: { auto_upload: false, max_simultaneous_uploads: 3 },
        file_handling: { accepted_formats: ['audio/mpeg'] },
        metadata: { version: '1.2.0' }
      },
      accessibility: {
        vision: { high_contrast: false, font_size_scale: 1.0 },
        motor: { keyboard_navigation_only: false },
        metadata: { version: '1.2.0' }
      }
    };

    return {
      ...defaults[type],
      ...overrides
    };
  },

  // Mock file objects
  createMockFile: (name, type, size = 1000, content = 'mock content') => {
    const file = new File([content], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  },

  // Wait for async operations
  waitForCondition: async (condition, timeout = 5000) => {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error(`Condition not met within ${timeout}ms`);
  },

  // Mock touch events
  createTouchEvent: (type, touches) => {
    return new TouchEvent(type, {
      touches: touches.map(touch => ({
        identifier: touch.id || 0,
        target: touch.target || document.body,
        clientX: touch.x || 0,
        clientY: touch.y || 0,
        pageX: touch.x || 0,
        pageY: touch.y || 0,
        screenX: touch.x || 0,
        screenY: touch.y || 0
      }))
    });
  },

  // Performance testing
  measurePerformance: async (fn, name = 'test') => {
    const start = performance.now();
    await fn();
    const end = performance.now();
    const duration = end - start;
    
    if (duration > 100) {
      console.warn(`Performance warning: ${name} took ${duration.toFixed(2)}ms`);
    }
    
    return duration;
  }
};

// Console overrides for cleaner test output
const originalError = console.error;
console.error = (...args) => {
  // Suppress known warnings/errors during tests
  const message = args[0];
  
  if (
    typeof message === 'string' &&
    (
      message.includes('Warning: ReactDOM.render is no longer supported') ||
      message.includes('Warning: An invalid form control') ||
      message.includes('Not implemented: HTMLCanvasElement.prototype.getContext')
    )
  ) {
    return;
  }
  
  originalError.call(console, ...args);
};

export default global;