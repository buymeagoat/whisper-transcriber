/**
 * T030 User Preferences Enhancement: Jest Configuration
 * Complete Jest configuration for comprehensive preference testing
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/components/__tests__/setup.js'
  ],
  
  // Module paths
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  
  // Test patterns
  testMatch: [
    '<rootDir>/src/components/__tests__/**/*.test.{js,jsx}',
    '<rootDir>/src/services/__tests__/**/*.test.{js,jsx}',
    '<rootDir>/src/utils/__tests__/**/*.test.{js,jsx}',
    '<rootDir>/src/hooks/__tests__/**/*.test.{js,jsx}'
  ],
  
  // Coverage configuration
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json'
  ],
  collectCoverageFrom: [
    'src/components/**/*.{js,jsx}',
    'src/services/**/*.{js,jsx}',
    'src/utils/**/*.{js,jsx}',
    'src/hooks/**/*.{js,jsx}',
    '!src/**/*.test.{js,jsx}',
    '!src/**/__tests__/**',
    '!src/**/*.stories.{js,jsx}',
    '!src/index.js',
    '!src/App.js'
  ],
  
  // Coverage thresholds for T030 components
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    './src/components/ThemePreferences.jsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/components/NotificationPreferences.jsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/components/UploadPreferences.jsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/components/AccessibilityOptions.jsx': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/components/MobileSettingsInterface.jsx': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    },
    './src/components/SettingsMigrationManager.jsx': {
      branches: 88,
      functions: 88,
      lines: 88,
      statements: 88
    },
    './src/services/themeService.js': {
      branches: 92,
      functions: 92,
      lines: 92,
      statements: 92
    },
    './src/services/notificationService.js': {
      branches: 92,
      functions: 92,
      lines: 92,
      statements: 92
    },
    './src/services/uploadService.js': {
      branches: 92,
      functions: 92,
      lines: 92,
      statements: 92
    },
    './src/services/accessibilityService.js': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    './src/services/settingsPersistenceService.js': {
      branches: 88,
      functions: 88,
      lines: 88,
      statements: 88
    },
    './src/services/settingsMigrationService.js': {
      branches: 88,
      functions: 88,
      lines: 88,
      statements: 88
    },
    './src/services/mobileInterfaceService.js': {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  
  // Transform configuration
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ],
      plugins: [
        '@babel/plugin-proposal-class-properties',
        '@babel/plugin-transform-runtime'
      ]
    }]
  },
  
  // Module file extensions
  moduleFileExtensions: [
    'js',
    'jsx',
    'json',
    'node'
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output
  verbose: true,
  
  // Clear mocks between tests
  clearMocks: true,
  
  // Reset modules between tests
  resetModules: true,
  
  // Performance monitoring
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: '<rootDir>/test-results',
      outputName: 'jest-results.xml',
      suiteName: 'T030 User Preferences Enhancement Tests'
    }],
    ['jest-html-reporters', {
      publicPath: '<rootDir>/test-results',
      filename: 'test-report.html',
      expand: true,
      hideIcon: false,
      pageTitle: 'T030 Test Results'
    }]
  ],
  
  // Error handling
  errorOnDeprecated: true,
  
  // Watch mode configuration
  watchman: true,
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/build/',
    '<rootDir>/dist/',
    '<rootDir>/coverage/'
  ],
  
  // Custom test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:3000',
    userAgent: 'T030TestAgent/1.0'
  },
  
  // Global setup and teardown
  globalSetup: '<rootDir>/src/components/__tests__/globalSetup.js',
  globalTeardown: '<rootDir>/src/components/__tests__/globalTeardown.js',
  
  // Mock configuration
  clearMocks: true,
  restoreMocks: true,
  
  // Performance optimization
  maxWorkers: '50%',
  
  // Test result processing
  collectCoverageOnlyFrom: {
    './src/components/ThemePreferences.jsx': true,
    './src/components/NotificationPreferences.jsx': true,
    './src/components/UploadPreferences.jsx': true,
    './src/components/AccessibilityOptions.jsx': true,
    './src/components/MobileSettingsInterface.jsx': true,
    './src/components/SettingsMigrationManager.jsx': true,
    './src/components/MigrationIntegration.jsx': true,
    './src/services/themeService.js': true,
    './src/services/notificationService.js': true,
    './src/services/uploadService.js': true,
    './src/services/accessibilityService.js': true,
    './src/services/settingsPersistenceService.js': true,
    './src/services/settingsMigrationService.js': true,
    './src/services/mobileInterfaceService.js': true
  }
};