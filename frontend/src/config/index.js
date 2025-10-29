/**
 * Production application configuration
 */

// API Configuration
export const API_CONFIG = {
  baseURL: '',
  timeout: 30000,
}

// App Configuration
export const APP_CONFIG = {
  name: 'Whisper Transcriber',
  version: '1.0.0',
  nodeEnv: 'production',
}

// Feature Flags
export const FEATURE_FLAGS = {
  analytics: false,
  debugTools: false,
  mockAPI: false,
}

// Upload Configuration
export const UPLOAD_CONFIG = {
  maxFileSize: 104857600, // 100MB
  allowedTypes: ['audio/wav', 'audio/mp3', 'audio/m4a', 'audio/flac'],
  maxFileSizeText: '100MB',
}

// Production constants
export const isDevelopment = false
export const isProduction = true
export const isDebugEnabled = false
