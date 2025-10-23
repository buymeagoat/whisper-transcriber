/**
 * I003 Frontend Testing Coverage: Main Test Setup
 * Comprehensive test setup and configuration for all React components
 * Builds upon existing T030 setup while extending for full component coverage
 */

import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { cleanup } from '@testing-library/react';

// Configure testing library
configure({
  testIdAttribute: 'data-testid',
  asyncUtilTimeout: 5000,
  computedStyleSupportsPseudoElements: true
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver for components using lazy loading
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock ResizeObserver for responsive components
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock requestAnimationFrame and cancelAnimationFrame
global.requestAnimationFrame = (callback) => {
  return setTimeout(callback, 0);
};

global.cancelAnimationFrame = (id) => {
  clearTimeout(id);
};

// Mock localStorage and sessionStorage
const createStorageMock = () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
});

Object.defineProperty(window, 'localStorage', {
  value: createStorageMock()
});

Object.defineProperty(window, 'sessionStorage', {
  value: createStorageMock()
});

// Mock CSS.supports for CSS feature detection
if (!global.CSS?.supports) {
  global.CSS = {
    supports: jest.fn(() => true)
  };
}

// Mock Notification API
global.Notification = {
  requestPermission: jest.fn(() => Promise.resolve('granted')),
  permission: 'granted'
};

Object.defineProperty(Notification, 'permission', {
  value: 'granted',
  writable: true
});

// Mock File API for upload components
global.File = class File {
  constructor(bits, filename, options = {}) {
    this.bits = bits;
    this.name = filename;
    this.size = bits.reduce((acc, bit) => acc + (bit.length || bit.byteLength || 0), 0);
    this.type = options.type || '';
    this.lastModified = options.lastModified || Date.now();
    this.webkitRelativePath = options.webkitRelativePath || '';
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
      this.result = Array.isArray(file.bits) ? file.bits.join('') : file.bits;
      if (this.onload) this.onload({ target: this });
      if (this.onloadend) this.onloadend({ target: this });
    }, 0);
  }

  readAsDataURL(file) {
    setTimeout(() => {
      this.readyState = 2;
      const content = Array.isArray(file.bits) ? file.bits.join('') : file.bits;
      this.result = `data:${file.type};base64,${btoa(content)}`;
      if (this.onload) this.onload({ target: this });
      if (this.onloadend) this.onloadend({ target: this });
    }, 0);
  }

  readAsArrayBuffer(file) {
    setTimeout(() => {
      this.readyState = 2;
      this.result = new ArrayBuffer(8);
      if (this.onload) this.onload({ target: this });
      if (this.onloadend) this.onloadend({ target: this });
    }, 0);
  }

  abort() {
    this.readyState = 2;
    if (this.onabort) this.onabort();
  }
};

// Mock Web Audio API for audio processing components
global.AudioContext = jest.fn(() => ({
  createAnalyser: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    frequencyBinCount: 1024,
    fftSize: 2048,
    getByteFrequencyData: jest.fn(),
    getFloatFrequencyData: jest.fn()
  })),
  createGain: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    gain: { value: 1, setValueAtTime: jest.fn() }
  })),
  createOscillator: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    start: jest.fn(),
    stop: jest.fn(),
    frequency: { value: 440, setValueAtTime: jest.fn() }
  })),
  decodeAudioData: jest.fn(() => Promise.resolve({
    duration: 10,
    numberOfChannels: 2,
    sampleRate: 44100
  })),
  close: jest.fn(),
  suspend: jest.fn(),
  resume: jest.fn(),
  state: 'running'
}));

// Mock navigator.vibrate for haptic feedback
Object.defineProperty(navigator, 'vibrate', {
  value: jest.fn(() => true),
  writable: true
});

// Mock navigator.mediaDevices for media upload
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: jest.fn(() => Promise.resolve({
      getTracks: () => [],
      getVideoTracks: () => [],
      getAudioTracks: () => []
    })),
    enumerateDevices: jest.fn(() => Promise.resolve([]))
  },
  writable: true
});

// Mock touch support for mobile components
Object.defineProperty(navigator, 'maxTouchPoints', {
  value: 5,
  writable: true
});

// Mock screen orientation
Object.defineProperty(screen, 'orientation', {
  value: {
    angle: 0,
    type: 'portrait-primary',
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
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
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByType: jest.fn(() => []),
    getEntriesByName: jest.fn(() => []),
    timing: {
      navigationStart: Date.now() - 1000,
      loadEventEnd: Date.now()
    }
  }
});

// Mock URL methods for file handling
Object.defineProperty(URL, 'createObjectURL', {
  value: jest.fn(() => 'blob:mock-url'),
  writable: true
});

Object.defineProperty(URL, 'revokeObjectURL', {
  value: jest.fn(),
  writable: true
});

// Mock XMLHttpRequest for upload progress
global.XMLHttpRequest = class XMLHttpRequest {
  constructor() {
    this.readyState = 0;
    this.status = 0;
    this.statusText = '';
    this.responseText = '';
    this.response = '';
    this.upload = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };
  }

  open() {
    this.readyState = 1;
  }

  send() {
    this.readyState = 4;
    this.status = 200;
    if (this.onload) this.onload();
  }

  setRequestHeader = jest.fn();
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
};

// Mock FormData for form submissions
global.FormData = class FormData {
  constructor() {
    this.data = new Map();
  }

  append(key, value) {
    this.data.set(key, value);
  }

  get(key) {
    return this.data.get(key);
  }

  has(key) {
    return this.data.has(key);
  }

  delete(key) {
    this.data.delete(key);
  }

  entries() {
    return this.data.entries();
  }
};

// Error handling for unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Global test utilities
global.testUtils = {
  // Mock service responses
  mockServiceSuccess: (service, method, response) => {
    service[method] = jest.fn().mockResolvedValue(response);
  },

  mockServiceError: (service, method, error) => {
    service[method] = jest.fn().mockRejectedValue(new Error(error));
  },

  // Mock component props
  createMockProps: (overrides = {}) => ({
    onClose: jest.fn(),
    onSave: jest.fn(),
    onCancel: jest.fn(),
    onChange: jest.fn(),
    onError: jest.fn(),
    onSubmit: jest.fn(),
    onSelect: jest.fn(),
    onDelete: jest.fn(),
    onEdit: jest.fn(),
    onView: jest.fn(),
    ...overrides
  }),

  // Create mock files
  createMockFile: (name, type, size = 1000, content = 'mock content') => {
    const file = new File([content], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  },

  // Create mock audio file
  createMockAudioFile: (name = 'test.mp3', size = 1024000) => {
    return global.testUtils.createMockFile(name, 'audio/mpeg', size, 'mock audio content');
  },

  // Create mock video file
  createMockVideoFile: (name = 'test.mp4', size = 5120000) => {
    return global.testUtils.createMockFile(name, 'video/mp4', size, 'mock video content');
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
    const event = new Event(type, { bubbles: true, cancelable: true });
    event.touches = touches.map(touch => ({
      identifier: touch.id || 0,
      target: touch.target || document.body,
      clientX: touch.x || 0,
      clientY: touch.y || 0,
      pageX: touch.x || 0,
      pageY: touch.y || 0,
      screenX: touch.x || 0,
      screenY: touch.y || 0
    }));
    return event;
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
  },

  // Mock React Router
  createMockRouter: (initialPath = '/') => ({
    navigate: jest.fn(),
    location: {
      pathname: initialPath,
      search: '',
      hash: '',
      state: null
    },
    params: {},
    search: '',
    hash: ''
  }),

  // Mock API responses
  createMockApiResponse: (data, status = 200) => ({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {}
  }),

  // Mock error response
  createMockApiError: (message, status = 500) => {
    const error = new Error(message);
    error.response = {
      data: { error: message },
      status,
      statusText: 'Internal Server Error'
    };
    return error;
  }
};

// Console overrides for cleaner test output
const originalError = console.error;
const originalWarn = console.warn;

console.error = (...args) => {
  const message = args[0];
  
  // Suppress known warnings/errors during tests
  if (
    typeof message === 'string' &&
    (
      message.includes('Warning: ReactDOM.render is no longer supported') ||
      message.includes('Warning: An invalid form control') ||
      message.includes('Not implemented: HTMLCanvasElement.prototype.getContext') ||
      message.includes('Warning: validateDOMNesting') ||
      message.includes('Warning: React does not recognize') ||
      message.includes('Warning: Failed prop type')
    )
  ) {
    return;
  }
  
  originalError.call(console, ...args);
};

console.warn = (...args) => {
  const message = args[0];
  
  // Suppress known warnings during tests
  if (
    typeof message === 'string' &&
    (
      message.includes('componentWillReceiveProps has been renamed') ||
      message.includes('componentWillMount has been renamed') ||
      message.includes('findDOMNode is deprecated')
    )
  ) {
    return;
  }
  
  originalWarn.call(console, ...args);
};

export default global;