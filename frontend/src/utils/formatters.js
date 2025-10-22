/**
 * Utility functions for formatting data in the system performance dashboard
 */

/**
 * Format bytes to human-readable format
 * @param {number} bytes - Number of bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted string
 */
export function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format duration from milliseconds to human-readable format
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(ms) {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    const remainingHours = hours % 24;
    const remainingMinutes = minutes % 60;
    return `${days}d ${remainingHours}h ${remainingMinutes}m`;
  } else if (hours > 0) {
    const remainingMinutes = minutes % 60;
    const remainingSeconds = seconds % 60;
    return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Format numbers with thousands separators
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export function formatNumber(num, decimals = 0) {
  if (num === null || num === undefined) return '0';
  
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * Format percentage with specific decimal places
 * @param {number} value - Value to format as percentage
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined) return '0%';
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format CPU frequency
 * @param {number} frequency - Frequency in GHz
 * @returns {string} Formatted frequency string
 */
export function formatFrequency(frequency) {
  if (frequency === null || frequency === undefined) return '0 GHz';
  
  if (frequency >= 1) {
    return `${frequency.toFixed(1)} GHz`;
  } else {
    return `${(frequency * 1000).toFixed(0)} MHz`;
  }
}

/**
 * Format network speed
 * @param {number} bytesPerSecond - Bytes per second
 * @returns {string} Formatted network speed
 */
export function formatNetworkSpeed(bytesPerSecond) {
  if (bytesPerSecond === 0) return '0 B/s';

  const k = 1024;
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));

  return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format timestamp to relative time
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Relative time string
 */
export function formatRelativeTime(timestamp) {
  const now = new Date();
  const time = new Date(timestamp);
  const diffMs = now - time;
  
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return time.toLocaleDateString();
  }
}

/**
 * Get status color based on percentage thresholds
 * @param {number} percentage - Percentage value
 * @param {Object} thresholds - Threshold configuration
 * @returns {string} Status color
 */
export function getStatusColor(percentage, thresholds = { warning: 75, critical: 90 }) {
  if (percentage >= thresholds.critical) return 'error';
  if (percentage >= thresholds.warning) return 'warning';
  return 'success';
}

/**
 * Get trend indicator based on change percentage
 * @param {number} change - Change percentage
 * @returns {Object} Trend object with direction and color
 */
export function getTrendIndicator(change) {
  if (change > 5) {
    return { direction: 'up', color: 'success', icon: '↗' };
  } else if (change < -5) {
    return { direction: 'down', color: 'error', icon: '↘' };
  } else {
    return { direction: 'stable', color: 'info', icon: '→' };
  }
}

/**
 * Calculate percentage from used and total values
 * @param {number} used - Used amount
 * @param {number} total - Total amount
 * @returns {number} Percentage
 */
export function calculatePercentage(used, total) {
  if (total === 0) return 0;
  return (used / total) * 100;
}

/**
 * Format response time with appropriate units
 * @param {number} ms - Response time in milliseconds
 * @returns {string} Formatted response time
 */
export function formatResponseTime(ms) {
  if (ms === null || ms === undefined) return '0ms';
  
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  } else {
    return `${(ms / 1000).toFixed(2)}s`;
  }
}

/**
 * Format uptime percentage
 * @param {number} uptime - Uptime as a decimal (0.999 = 99.9%)
 * @returns {string} Formatted uptime percentage
 */
export function formatUptime(uptime) {
  if (uptime === null || uptime === undefined) return '0%';
  
  if (typeof uptime === 'string') {
    return uptime; // Already formatted
  }
  
  return `${(uptime * 100).toFixed(2)}%`;
}

/**
 * Get severity color for alerts
 * @param {string} severity - Alert severity level
 * @returns {string} MUI color
 */
export function getSeverityColor(severity) {
  switch (severity?.toLowerCase()) {
    case 'critical':
    case 'error':
      return 'error';
    case 'warning':
      return 'warning';
    case 'info':
      return 'info';
    case 'success':
      return 'success';
    default:
      return 'default';
  }
}

/**
 * Format threshold values for display
 * @param {number} value - Threshold value
 * @param {string} unit - Unit of measurement
 * @returns {string} Formatted threshold
 */
export function formatThreshold(value, unit = '%') {
  if (value === null || value === undefined) return 'N/A';
  return `${value}${unit}`;
}

/**
 * Generate color palette for charts
 * @param {number} count - Number of colors needed
 * @returns {Array} Array of color strings
 */
export function generateChartColors(count) {
  const baseColors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
    '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
  ];
  
  const colors = [];
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length]);
  }
  
  return colors;
}

/**
 * Format API rate limit display
 * @param {number} current - Current usage
 * @param {number} limit - Rate limit
 * @param {string} window - Time window
 * @returns {string} Formatted rate limit string
 */
export function formatRateLimit(current, limit, window = 'hour') {
  return `${formatNumber(current)} / ${formatNumber(limit)} per ${window}`;
}

/**
 * Calculate and format growth rate
 * @param {number} current - Current value
 * @param {number} previous - Previous value
 * @returns {Object} Growth rate object with value and formatted string
 */
export function calculateGrowthRate(current, previous) {
  if (previous === 0) {
    return { value: 0, formatted: '0%', trend: 'stable' };
  }
  
  const growth = ((current - previous) / previous) * 100;
  const trend = growth > 0 ? 'up' : growth < 0 ? 'down' : 'stable';
  
  return {
    value: growth,
    formatted: `${growth > 0 ? '+' : ''}${growth.toFixed(1)}%`,
    trend
  };
}

/**
 * Format health score
 * @param {number} score - Health score (0-100)
 * @returns {Object} Health score object with status and color
 */
export function formatHealthScore(score) {
  let status, color;
  
  if (score >= 90) {
    status = 'Excellent';
    color = 'success';
  } else if (score >= 75) {
    status = 'Good';
    color = 'info';
  } else if (score >= 50) {
    status = 'Fair';
    color = 'warning';
  } else {
    status = 'Poor';
    color = 'error';
  }
  
  return {
    score: Math.round(score),
    status,
    color,
    formatted: `${Math.round(score)}% - ${status}`
  };
}