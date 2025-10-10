/**
 * Centralized Error Handling Service
 * 
 * Provides consistent error messaging, logging, and user feedback
 * across the entire frontend application.
 */

import { store } from '../store';
import { addToast } from '../store';

// Error types for consistent categorization
export const ERROR_TYPES = {
  NETWORK: 'network',
  VALIDATION: 'validation',
  AUTHENTICATION: 'authentication',
  AUTHORIZATION: 'authorization',
  SERVER: 'server',
  FILE_UPLOAD: 'file_upload',
  NOT_FOUND: 'not_found',
  UNKNOWN: 'unknown'
};

// User-friendly error messages
const ERROR_MESSAGES = {
  // Network errors
  'NetworkError': 'Network connection failed. Please check your internet connection.',
  'TypeError: Failed to fetch': 'Unable to connect to server. Please check your connection.',
  'fetch failed': 'Network request failed. Please try again.',
  
  // Authentication errors
  'Incorrect username or password': 'Invalid login credentials. Please check your username and password.',
  'Not authenticated': 'You need to log in to access this feature.',
  'Token expired': 'Your session has expired. Please log in again.',
  'Invalid token': 'Authentication error. Please log in again.',
  
  // Authorization errors
  'Insufficient permissions': 'You don\'t have permission to perform this action.',
  'Admin access required': 'Administrator privileges required for this action.',
  
  // File upload errors
  'File too large': 'File size exceeds the maximum allowed limit.',
  'Unsupported file type': 'This file type is not supported. Please use a valid audio file.',
  'File validation failed': 'File validation failed. Please check the file format and try again.',
  
  // Server errors
  'Internal Server Error': 'Server error occurred. Please try again later.',
  'Service Unavailable': 'Service is temporarily unavailable. Please try again later.',
  'Bad Gateway': 'Server connection error. Please try again later.',
  
  // Generic errors
  'Request failed': 'Request failed. Please try again.',
  'Operation failed': 'Operation could not be completed. Please try again.',
};

/**
 * Extracts error type from error message or response
 */
function getErrorType(error, response) {
  const message = error?.message || error || '';
  const status = response?.status;
  
  if (status === 401 || message.toLowerCase().includes('auth')) {
    return ERROR_TYPES.AUTHENTICATION;
  }
  
  if (status === 403 || message.toLowerCase().includes('permission')) {
    return ERROR_TYPES.AUTHORIZATION;
  }
  
  if (status === 404) {
    return ERROR_TYPES.NOT_FOUND;
  }
  
  if (status >= 500) {
    return ERROR_TYPES.SERVER;
  }
  
  if (message.toLowerCase().includes('network') || message.toLowerCase().includes('fetch')) {
    return ERROR_TYPES.NETWORK;
  }
  
  if (message.toLowerCase().includes('file') || message.toLowerCase().includes('upload')) {
    return ERROR_TYPES.FILE_UPLOAD;
  }
  
  if (status >= 400 && status < 500) {
    return ERROR_TYPES.VALIDATION;
  }
  
  return ERROR_TYPES.UNKNOWN;
}

/**
 * Gets user-friendly error message
 */
function getUserFriendlyMessage(error, errorType) {
  const message = error?.message || error || '';
  
  // Check for exact matches first
  for (const [key, value] of Object.entries(ERROR_MESSAGES)) {
    if (message.includes(key)) {
      return value;
    }
  }
  
  // Fallback based on error type
  switch (errorType) {
    case ERROR_TYPES.NETWORK:
      return 'Network connection problem. Please check your internet connection and try again.';
    case ERROR_TYPES.AUTHENTICATION:
      return 'Authentication failed. Please log in again.';
    case ERROR_TYPES.AUTHORIZATION:
      return 'You don\'t have permission to perform this action.';
    case ERROR_TYPES.NOT_FOUND:
      return 'The requested resource was not found.';
    case ERROR_TYPES.SERVER:
      return 'Server error occurred. Please try again later.';
    case ERROR_TYPES.FILE_UPLOAD:
      return 'File upload failed. Please check the file and try again.';
    case ERROR_TYPES.VALIDATION:
      return 'Invalid input. Please check your data and try again.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
}

/**
 * Enhanced error parsing from API responses
 */
export function parseApiError(error, response = null) {
  // Extract error details
  let message = '';
  let details = '';
  
  if (typeof error === 'string') {
    message = error;
  } else if (error?.message) {
    message = error.message;
  } else if (error?.detail) {
    message = error.detail;
  } else if (error?.error) {
    message = error.error;
  } else {
    message = 'Unknown error occurred';
  }
  
  // Extract additional details if available
  if (error?.details) {
    details = error.details;
  } else if (typeof error === 'object' && error !== null) {
    // Try to extract meaningful details from error object
    const errorInfo = Object.entries(error)
      .filter(([key, value]) => key !== 'message' && key !== 'detail' && value)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');
    if (errorInfo) {
      details = errorInfo;
    }
  }
  
  const errorType = getErrorType(error, response);
  const userMessage = getUserFriendlyMessage({ message }, errorType);
  
  return {
    type: errorType,
    originalMessage: message,
    userMessage,
    details,
    status: response?.status,
    timestamp: new Date().toISOString()
  };
}

/**
 * Standard error handler that shows toast notifications
 */
export function handleError(error, context = '', showToast = true) {
  const errorInfo = parseApiError(error);
  
  // Log error for debugging
  console.error(`Error in ${context}:`, {
    original: error,
    parsed: errorInfo
  });
  
  // Show user-friendly toast notification
  if (showToast) {
    const toastMessage = context 
      ? `${context}: ${errorInfo.userMessage}`
      : errorInfo.userMessage;
      
    store.dispatch(addToast(toastMessage, 'error'));
  }
  
  return errorInfo;
}

/**
 * Async operation wrapper with standardized error handling
 */
export async function withErrorHandling(
  operation, 
  context = '', 
  options = { showToast: true, rethrow: false }
) {
  try {
    return await operation();
  } catch (error) {
    const errorInfo = handleError(error, context, options.showToast);
    
    if (options.rethrow) {
      throw errorInfo;
    }
    
    return null;
  }
}

/**
 * React hook for consistent error handling in components
 */
export function useErrorHandler() {
  return {
    handleError: (error, context = '') => handleError(error, context),
    withErrorHandling: (operation, context = '', options = {}) => 
      withErrorHandling(operation, context, options),
    parseError: (error, response = null) => parseApiError(error, response)
  };
}

/**
 * Enhanced API error handler for common HTTP status codes
 */
export function handleApiResponse(response, data) {
  if (response.ok) {
    return data;
  }
  
  const error = {
    message: data?.detail || data?.error || data || 'Request failed',
    status: response.status,
    statusText: response.statusText,
    url: response.url
  };
  
  // Add specific handling for common status codes
  switch (response.status) {
    case 401:
      // Handle authentication errors
      if (error.message.includes('token') || error.message.includes('auth')) {
        // Could trigger automatic logout here
        error.message = 'Your session has expired. Please log in again.';
      }
      break;
      
    case 403:
      error.message = 'You don\'t have permission to perform this action.';
      break;
      
    case 404:
      error.message = 'The requested resource was not found.';
      break;
      
    case 413:
      error.message = 'File or request is too large.';
      break;
      
    case 429:
      error.message = 'Too many requests. Please wait a moment and try again.';
      break;
      
    case 500:
      error.message = 'Server error occurred. Please try again later.';
      break;
      
    case 502:
    case 503:
    case 504:
      error.message = 'Service is temporarily unavailable. Please try again later.';
      break;
  }
  
  throw error;
}
