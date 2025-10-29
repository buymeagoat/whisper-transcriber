import axios from 'axios';
import { API_CONFIG } from '../config';

class SystemPerformanceService {
  constructor() {
    this.apiClient = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: 10000,
    });

    // Add request interceptor for authentication
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid, redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get current system metrics (CPU, memory, disk, network)
   * @returns {Promise} System metrics data
   */
  async getSystemMetrics() {
    try {
      const response = await this.apiClient.get('/admin/system/metrics');
      return {
        data: {
          system: {
            cpu: {
              usage: response.data.cpu_usage || 0,
              cores: response.data.cpu_cores || 0,
              frequency: response.data.cpu_frequency || 0
            },
            memory: {
              used: response.data.memory_used || 0,
              total: response.data.memory_total || 0,
              percentage: response.data.memory_percentage || 0
            },
            disk: {
              used: response.data.disk_used || 0,
              total: response.data.disk_total || 0,
              percentage: response.data.disk_percentage || 0
            },
            network: {
              rx: response.data.network_rx || 0,
              tx: response.data.network_tx || 0,
              connections: response.data.network_connections || 0
            }
          },
          application: {
            activeJobs: response.data.active_jobs || 0,
            queueSize: response.data.queue_size || 0,
            errorRate: response.data.error_rate || 0,
            responseTime: response.data.avg_response_time || 0,
            throughput: response.data.throughput || 0,
            uptime: response.data.uptime || 0
          }
        }
      };
    } catch (error) {
      console.error('Error fetching system metrics:', error);
      // Return mock data for development/testing
      return this.getMockSystemMetrics();
    }
  }

  /**
   * Get historical performance data
   * @param {string} timeRange - Time range for historical data (1h, 6h, 24h, 7d)
   * @returns {Promise} Historical performance data
   */
  async getHistoricalMetrics(timeRange = '1h') {
    try {
      const response = await this.apiClient.get(`/admin/system/metrics/historical`, {
        params: { timeRange }
      });
      return response;
    } catch (error) {
      console.error('Error fetching historical metrics:', error);
      return this.getMockHistoricalMetrics();
    }
  }

  /**
   * Get active system alerts
   * @returns {Promise} Active alerts data
   */
  async getActiveAlerts() {
    try {
      const response = await this.apiClient.get('/admin/system/alerts');
      return {
        data: {
          alerts: response.data.alerts || []
        }
      };
    } catch (error) {
      console.error('Error fetching alerts:', error);
      return this.getMockAlerts();
    }
  }

  /**
   * Get service status information
   * @returns {Promise} Service status data
   */
  async getServiceStatus() {
    try {
      const response = await this.apiClient.get('/admin/system/services');
      return {
        data: {
          services: response.data.services || []
        }
      };
    } catch (error) {
      console.error('Error fetching service status:', error);
      return this.getMockServiceStatus();
    }
  }

  /**
   * Get performance analytics data
   * @returns {Promise} Performance analytics data
   */
  async getPerformanceAnalytics() {
    try {
      const response = await this.apiClient.get('/admin/system/analytics');
      return response;
    } catch (error) {
      console.error('Error fetching performance analytics:', error);
      return this.getMockPerformanceAnalytics();
    }
  }

  /**
   * Get resource usage by component
   * @returns {Promise} Component resource usage data
   */
  async getComponentResourceUsage() {
    try {
      const response = await this.apiClient.get('/admin/system/components');
      return response;
    } catch (error) {
      console.error('Error fetching component resource usage:', error);
      return this.getMockComponentResourceUsage();
    }
  }

  /**
   * Update alert configuration
   * @param {Object} alertConfig - Alert configuration data
   * @returns {Promise} Update response
   */
  async updateAlertConfiguration(alertConfig) {
    try {
      const response = await this.apiClient.put('/admin/system/alerts/config', alertConfig);
      return response;
    } catch (error) {
      console.error('Error updating alert configuration:', error);
      throw error;
    }
  }

  /**
   * Acknowledge alert
   * @param {string} alertId - Alert ID to acknowledge
   * @returns {Promise} Acknowledgment response
   */
  async acknowledgeAlert(alertId) {
    try {
      const response = await this.apiClient.post(`/admin/system/alerts/${alertId}/acknowledge`);
      return response;
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      throw error;
    }
  }

  /**
   * Get system optimization recommendations
   * @returns {Promise} Optimization recommendations
   */
  async getOptimizationRecommendations() {
    try {
      const response = await this.apiClient.get('/admin/system/optimization');
      return response;
    } catch (error) {
      console.error('Error fetching optimization recommendations:', error);
      return this.getMockOptimizationRecommendations();
    }
  }

  // Mock data methods for development/testing
  getMockSystemMetrics() {
    return {
      data: {
        system: {
          cpu: {
            usage: 45.2 + Math.random() * 10,
            cores: 8,
            frequency: 3.2
          },
          memory: {
            used: 6442450944, // ~6GB
            total: 17179869184, // ~16GB
            percentage: 37.5 + Math.random() * 10
          },
          disk: {
            used: 536870912000, // ~500GB
            total: 1099511627776, // ~1TB
            percentage: 48.8 + Math.random() * 5
          },
          network: {
            rx: 1048576 + Math.random() * 1048576, // 1-2 MB/s
            tx: 524288 + Math.random() * 524288, // 0.5-1 MB/s
            connections: 150 + Math.floor(Math.random() * 50)
          }
        },
        application: {
          activeJobs: Math.floor(Math.random() * 10),
          queueSize: Math.floor(Math.random() * 25),
          errorRate: Math.random() * 2,
          responseTime: 120 + Math.random() * 100,
          throughput: 1200 + Math.random() * 300,
          uptime: Date.now() - (Math.random() * 86400000 * 7) // Random uptime up to 7 days
        }
      }
    };
  }

  getMockHistoricalMetrics() {
    const now = new Date();
    const labels = [];
    const cpuData = [];
    const memoryData = [];
    const diskData = [];
    
    for (let i = 19; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 5 * 60 * 1000); // 5 minutes ago
      labels.push(time.toLocaleTimeString());
      cpuData.push(30 + Math.random() * 40);
      memoryData.push(25 + Math.random() * 30);
      diskData.push(45 + Math.random() * 10);
    }
    
    return {
      data: {
        labels,
        datasets: {
          cpu: cpuData,
          memory: memoryData,
          disk: diskData
        }
      }
    };
  }

  getMockAlerts() {
    const alerts = [];
    
    if (Math.random() > 0.7) {
      alerts.push({
        id: '1',
        title: 'High CPU Usage',
        description: 'CPU usage has exceeded 80% for the last 5 minutes',
        severity: 'warning',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        component: 'system'
      });
    }
    
    if (Math.random() > 0.8) {
      alerts.push({
        id: '2',
        title: 'Memory Usage Critical',
        description: 'Memory usage has exceeded 90%',
        severity: 'error',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        component: 'system'
      });
    }
    
    if (Math.random() > 0.9) {
      alerts.push({
        id: '3',
        title: 'High Error Rate',
        description: 'Application error rate is above 5%',
        severity: 'warning',
        timestamp: new Date(Date.now() - 900000).toISOString(),
        component: 'application'
      });
    }
    
    return {
      data: {
        alerts
      }
    };
  }

  getMockServiceStatus() {
    const services = [
      {
        name: 'Whisper Transcriber API',
        description: 'Main application server',
        status: 'healthy',
        lastCheck: new Date().toISOString(),
        uptime: '99.9%',
        responseTime: 120
      },
      {
        name: 'PostgreSQL Database',
        description: 'Primary database server',
        status: 'healthy',
        lastCheck: new Date().toISOString(),
        uptime: '99.95%',
        responseTime: 5
      },
      {
        name: 'Redis Cache',
        description: 'Cache and session storage',
        status: Math.random() > 0.9 ? 'warning' : 'healthy',
        lastCheck: new Date().toISOString(),
        uptime: '99.8%',
        responseTime: 2
      },
      {
        name: 'Celery Worker',
        description: 'Background job processor',
        status: 'healthy',
        lastCheck: new Date().toISOString(),
        uptime: '99.7%',
        responseTime: 0
      },
      {
        name: 'Nginx Load Balancer',
        description: 'Reverse proxy and load balancer',
        status: 'healthy',
        lastCheck: new Date().toISOString(),
        uptime: '99.99%',
        responseTime: 1
      }
    ];
    
    return {
      data: {
        services
      }
    };
  }

  getMockPerformanceAnalytics() {
    return {
      data: {
        trends: {
          responseTime: {
            current: 125,
            trend: 'stable',
            change: 2.1
          },
          throughput: {
            current: 1450,
            trend: 'up',
            change: 8.3
          },
          errorRate: {
            current: 1.2,
            trend: 'down',
            change: -15.7
          }
        },
        recommendations: [
          {
            type: 'performance',
            title: 'Optimize Database Queries',
            description: 'Several slow queries detected. Consider adding indexes.',
            priority: 'medium',
            impact: 'medium'
          },
          {
            type: 'capacity',
            title: 'Memory Usage Growing',
            description: 'Memory usage has increased 15% over the last week.',
            priority: 'low',
            impact: 'low'
          }
        ]
      }
    };
  }

  getMockComponentResourceUsage() {
    return {
      data: {
        components: [
          {
            name: 'API Server',
            cpu: 25.3,
            memory: 512 * 1024 * 1024,
            disk: 0,
            network: 1024 * 1024
          },
          {
            name: 'Database',
            cpu: 15.7,
            memory: 2 * 1024 * 1024 * 1024,
            disk: 50 * 1024 * 1024,
            network: 512 * 1024
          },
          {
            name: 'Cache',
            cpu: 5.2,
            memory: 256 * 1024 * 1024,
            disk: 0,
            network: 2 * 1024 * 1024
          },
          {
            name: 'Worker',
            cpu: 45.8,
            memory: 1024 * 1024 * 1024,
            disk: 10 * 1024 * 1024,
            network: 256 * 1024
          }
        ]
      }
    };
  }

  getMockOptimizationRecommendations() {
    return {
      data: {
        recommendations: [
          {
            category: 'performance',
            title: 'Enable Database Connection Pooling',
            description: 'Implement connection pooling to reduce database connection overhead',
            impact: 'high',
            effort: 'medium',
            estimatedImprovement: '20-30% response time improvement'
          },
          {
            category: 'memory',
            title: 'Optimize Cache Configuration',
            description: 'Adjust Redis memory allocation and eviction policies',
            impact: 'medium',
            effort: 'low',
            estimatedImprovement: '10-15% memory usage reduction'
          },
          {
            category: 'cpu',
            title: 'Implement CPU Affinity',
            description: 'Configure CPU affinity for critical processes',
            impact: 'low',
            effort: 'low',
            estimatedImprovement: '5-10% CPU efficiency improvement'
          }
        ]
      }
    };
  }
}

// Create a singleton instance
export const systemPerformanceService = new SystemPerformanceService();
export default systemPerformanceService;