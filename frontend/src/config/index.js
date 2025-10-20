/**
 * Application configuration using Vite environment variables
 */

// API Configuration
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
}

// App Configuration
export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'Whisper Transcriber',
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  debug: import.meta.env.VITE_DEBUG === 'true',
  nodeEnv: import.meta.env.VITE_NODE_ENV || import.meta.env.MODE || 'development',
}

// Feature Flags
export const FEATURE_FLAGS = {
  analytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  debugTools: import.meta.env.VITE_ENABLE_DEBUG_TOOLS === 'true',
  mockAPI: import.meta.env.VITE_ENABLE_MOCK_API === 'true',
}

// Upload Configuration
export const UPLOAD_CONFIG = {
  maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE) || 104857600, // 100MB
  allowedTypes: (import.meta.env.VITE_ALLOWED_FILE_TYPES || 'audio/wav,audio/mp3,audio/m4a,audio/flac').split(','),
  maxFileSizeText: '100MB',
}

// Development helpers
export const isDevelopment = APP_CONFIG.nodeEnv === 'development'
export const isProduction = APP_CONFIG.nodeEnv === 'production'
export const isDebugEnabled = APP_CONFIG.debug

// Log configuration in development
if (isDevelopment && isDebugEnabled) {
  console.log('🔧 App Configuration:', {
    API_CONFIG,
    APP_CONFIG,
    FEATURE_FLAGS,
    UPLOAD_CONFIG,
  })
}
