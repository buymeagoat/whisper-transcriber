/**
 * I003 Frontend Testing Coverage: Browser Mocks
 * Mock browser APIs and globals for Jest testing environment
 */

// Mock window methods
Object.defineProperty(window, 'scrollTo', {
  value: jest.fn(),
  writable: true
});

Object.defineProperty(window, 'scroll', {
  value: jest.fn(),
  writable: true
});

Object.defineProperty(window, 'scrollBy', {
  value: jest.fn(),
  writable: true
});

// Mock focus and blur
HTMLElement.prototype.scrollIntoView = jest.fn();
HTMLElement.prototype.focus = jest.fn();
HTMLElement.prototype.blur = jest.fn();

// Mock element dimensions
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  get: function() { return 100; }
});

Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  get: function() { return 100; }
});

Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  get: function() { return 100; }
});

Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  get: function() { return 100; }
});

Object.defineProperty(HTMLElement.prototype, 'scrollHeight', {
  get: function() { return 200; }
});

Object.defineProperty(HTMLElement.prototype, 'scrollWidth', {
  get: function() { return 200; }
});

// Mock getBoundingClientRect
HTMLElement.prototype.getBoundingClientRect = jest.fn(() => ({
  top: 0,
  left: 0,
  bottom: 100,
  right: 100,
  width: 100,
  height: 100,
  x: 0,
  y: 0
}));

// Mock getComputedStyle
window.getComputedStyle = jest.fn(() => ({
  getPropertyValue: jest.fn(() => ''),
  display: 'block',
  visibility: 'visible',
  opacity: '1'
}));

// Mock MutationObserver
global.MutationObserver = class MutationObserver {
  constructor(callback) {
    this.callback = callback;
  }
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
};

// Mock DOMParser
global.DOMParser = class DOMParser {
  parseFromString(str, contentType) {
    const doc = document.implementation.createHTMLDocument('');
    doc.documentElement.innerHTML = str;
    return doc;
  }
};

// Mock clipboard API
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn(() => Promise.resolve()),
    readText: jest.fn(() => Promise.resolve('mock text')),
    write: jest.fn(() => Promise.resolve()),
    read: jest.fn(() => Promise.resolve([]))
  },
  writable: true
});

// Mock geolocation
Object.defineProperty(navigator, 'geolocation', {
  value: {
    getCurrentPosition: jest.fn((success) => success({
      coords: {
        latitude: 40.7128,
        longitude: -74.0060,
        accuracy: 10
      }
    })),
    watchPosition: jest.fn(() => 1),
    clearWatch: jest.fn()
  },
  writable: true
});

// Mock connection info
Object.defineProperty(navigator, 'connection', {
  value: {
    effectiveType: '4g',
    downlink: 10,
    rtt: 50,
    saveData: false
  },
  writable: true
});

// Mock battery API
Object.defineProperty(navigator, 'getBattery', {
  value: jest.fn(() => Promise.resolve({
    level: 0.8,
    charging: true,
    chargingTime: 3600,
    dischargingTime: Infinity
  })),
  writable: true
});

// Mock service worker
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: jest.fn(() => Promise.resolve({
      scope: '/',
      active: null,
      installing: null,
      waiting: null,
      update: jest.fn(() => Promise.resolve())
    })),
    ready: Promise.resolve({
      scope: '/',
      active: null,
      installing: null,
      waiting: null,
      update: jest.fn(() => Promise.resolve())
    }),
    controller: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
  },
  writable: true
});

// Mock web share API
Object.defineProperty(navigator, 'share', {
  value: jest.fn(() => Promise.resolve()),
  writable: true
});

Object.defineProperty(navigator, 'canShare', {
  value: jest.fn(() => true),
  writable: true
});

// Mock permissions API
Object.defineProperty(navigator, 'permissions', {
  value: {
    query: jest.fn(() => Promise.resolve({
      state: 'granted',
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    }))
  },
  writable: true
});

// Mock fullscreen API
document.exitFullscreen = jest.fn(() => Promise.resolve());
HTMLElement.prototype.requestFullscreen = jest.fn(() => Promise.resolve());

Object.defineProperty(document, 'fullscreenElement', {
  value: null,
  writable: true
});

Object.defineProperty(document, 'fullscreenEnabled', {
  value: true,
  writable: true
});

// Mock picture-in-picture
HTMLVideoElement.prototype.requestPictureInPicture = jest.fn(() => Promise.resolve({}));
document.exitPictureInPicture = jest.fn(() => Promise.resolve());

Object.defineProperty(document, 'pictureInPictureElement', {
  value: null,
  writable: true
});

Object.defineProperty(document, 'pictureInPictureEnabled', {
  value: true,
  writable: true
});

// Mock drag and drop
const createDataTransfer = () => ({
  dropEffect: 'none',
  effectAllowed: 'all',
  files: [],
  items: [],
  types: [],
  clearData: jest.fn(),
  getData: jest.fn(() => ''),
  setData: jest.fn(),
  setDragImage: jest.fn()
});

Object.defineProperty(window, 'DataTransfer', {
  value: jest.fn(() => createDataTransfer()),
  writable: true
});

// Mock custom elements
Object.defineProperty(window, 'customElements', {
  value: {
    define: jest.fn(),
    get: jest.fn(),
    upgrade: jest.fn(),
    whenDefined: jest.fn(() => Promise.resolve())
  },
  writable: true
});

export {};