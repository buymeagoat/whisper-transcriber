/**
 * I003 Frontend Testing Coverage: Unified Jest Configuration
 * Comprehensive Jest configuration for all React components
 * Extends existing T030 configuration while adding comprehensive component testing
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/setupTests.js'
  ],
  
  // Module name mapping for path aliases and styles
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@config/(.*)$': '<rootDir>/src/config/$1',
    '^@context/(.*)$': '<rootDir>/src/context/$1',
    '^@api/(.*)$': '<rootDir>/src/api/$1',
    '^@styles/(.*)$': '<rootDir>/src/styles/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/src/__mocks__/fileMock.js'
  },
  
  // Test patterns - comprehensive coverage
  testMatch: [
    '<rootDir>/src/**/*.test.{js,jsx}',
    '<rootDir>/src/**/*.spec.{js,jsx}',
    '<rootDir>/src/**/__tests__/**/*.{js,jsx}'
  ],
  
  // Ignore patterns
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/build/',
    '<rootDir>/dist/',
    '<rootDir>/coverage/',
    '<rootDir>/src/components/__tests__/globalSetup.js',
    '<rootDir>/src/components/__tests__/globalTeardown.js',
    '<rootDir>/src/components/__tests__/run-t030-tests.sh'
  ],
  
  // Coverage configuration
  collectCoverage: false, // Enable only when needed to avoid slowdown
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: [
    'text',
    'text-summary',
    'lcov',
    'html',
    'json-summary',
    'cobertura'
  ],
  
  // Comprehensive coverage collection
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/**/*.test.{js,jsx}',
    '!src/**/*.spec.{js,jsx}',
    '!src/**/__tests__/**',
    '!src/**/*.stories.{js,jsx}',
    '!src/index.js',
    '!src/main.jsx',
    '!src/App.jsx',
    '!src/setupTests.js',
    '!src/__mocks__/**',
    '!src/vite-env.d.ts'
  ],
  
  // Coverage thresholds for comprehensive testing
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // Transform configuration
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { 
          targets: { node: 'current' },
          modules: 'commonjs'
        }],
        ['@babel/preset-react', { 
          runtime: 'automatic',
          importSource: 'react'
        }]
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
    'ts',
    'tsx',
    'json',
    'node'
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Verbose output for comprehensive testing
  verbose: true,
  
  // Clean setup between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
  
  // Reset modules between tests
  resetModules: true,
  
  // Test environment options
  testEnvironmentOptions: {
    url: 'http://localhost:3002',
    userAgent: 'FrontendTestAgent/1.0'
  },
  
  // Performance optimization
  maxWorkers: '50%',
  
  // Transform ignore patterns
  transformIgnorePatterns: [
    'node_modules/(?!(react-dropzone|@mui|lucide-react|chart.js|react-chartjs-2)/)'
  ],
  
  // Mock configuration for external dependencies
  moduleDirectories: ['node_modules', '<rootDir>/src'],
  
  // Additional setup for comprehensive testing
  setupFiles: [
    '<rootDir>/src/__mocks__/browserMocks.js'
  ]
};