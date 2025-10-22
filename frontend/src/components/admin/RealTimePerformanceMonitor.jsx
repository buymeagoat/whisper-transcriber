/**
 * T012: Real-Time Performance Monitoring UI
 * React component for live system performance monitoring with charts and visualizations
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  Switch,
  FormControlLabel,
  Alert,
  LinearProgress,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  NetworkCheck as NetworkIcon,
  CheckCircle,
  Error as ErrorIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import realTimePerformanceService from '../../services/realTimePerformanceService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

const RealTimePerformanceMonitor = () => {
  // State management
  const [metrics, setMetrics] = useState(null);
  const [historicalData, setHistoricalData] = useState({
    labels: [],
    cpu: [],
    memory: [],
    disk: []
  });
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState({});
  
  // Subscription refs to manage service subscriptions
  const subscriptionsRef = useRef({
    metrics: null,
    alerts: null,
    services: null
  });

  // Real-time data handlers
  const handleMetricsUpdate = (newMetrics) => {
    setMetrics(newMetrics);
    updateHistoricalData(newMetrics);
    setError(null);
  };

  const handleAlertsUpdate = (newAlerts) => {
    setAlerts(newAlerts.alerts || []);
  };

  const handleConnectionError = (errorData) => {
    setError(`Connection error: ${errorData.message}`);
  };

  // Start/stop monitoring with real-time service
  const startMonitoring = () => {
    if (isMonitoring) return;

    // Subscribe to metrics updates
    subscriptionsRef.current.metrics = realTimePerformanceService.subscribe(
      'metrics',
      handleMetricsUpdate
    );

    // Subscribe to alerts updates
    subscriptionsRef.current.alerts = realTimePerformanceService.subscribe(
      'alerts',
      handleAlertsUpdate
    );

    // Subscribe to error events
    subscriptionsRef.current.error = realTimePerformanceService.subscribe(
      'error',
      handleConnectionError
    );

    setIsMonitoring(true);
    setLoading(false);
  };

  const stopMonitoring = () => {
    if (!isMonitoring) return;

    // Unsubscribe from all events
    if (subscriptionsRef.current.metrics) {
      realTimePerformanceService.unsubscribe('metrics', subscriptionsRef.current.metrics);
      subscriptionsRef.current.metrics = null;
    }

    if (subscriptionsRef.current.alerts) {
      realTimePerformanceService.unsubscribe('alerts', subscriptionsRef.current.alerts);
      subscriptionsRef.current.alerts = null;
    }

    if (subscriptionsRef.current.error) {
      realTimePerformanceService.unsubscribe('error', subscriptionsRef.current.error);
      subscriptionsRef.current.error = null;
    }

    setIsMonitoring(false);
  };

  // Manual refresh
  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Force a reconnection to get fresh data
      await realTimePerformanceService.reconnect();
      setError(null);
    } catch (err) {
      setError(`Refresh failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Update polling interval
  const handleIntervalChange = (newInterval) => {
    setRefreshInterval(newInterval);
    realTimePerformanceService.setPollingInterval(newInterval);
  };

  // Update historical data for charts
  const updateHistoricalData = (newMetrics) => {
    const now = new Date();
    const timeLabel = now.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });

    setHistoricalData(prev => {
      const maxPoints = 20; // Keep last 20 data points
      
      const newLabels = [...prev.labels, timeLabel].slice(-maxPoints);
      const newCpu = [...prev.cpu, newMetrics.cpu_usage].slice(-maxPoints);
      const newMemory = [...prev.memory, newMetrics.memory_percentage].slice(-maxPoints);
      const newDisk = [...prev.disk, newMetrics.disk_percentage].slice(-maxPoints);

      return {
        labels: newLabels,
        cpu: newCpu,
        memory: newMemory,
        disk: newDisk
      };
    });
  };

  // Effect to update connection status
  useEffect(() => {
    const updateConnectionStatus = () => {
      setConnectionStatus(realTimePerformanceService.getConnectionStatus());
    };

    const interval = setInterval(updateConnectionStatus, 1000);
    updateConnectionStatus(); // Initial update

    return () => clearInterval(interval);
  }, []);

  // Effect to manage monitoring lifecycle
  useEffect(() => {
    // Start monitoring when component mounts
    startMonitoring();

    // Cleanup on unmount
    return () => {
      stopMonitoring();
    };
  }, []);

  // Effect to handle monitoring state changes
  useEffect(() => {
    if (isMonitoring) {
      startMonitoring();
    } else {
      stopMonitoring();
    }
  }, [isMonitoring]);

  // Chart configurations
  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Real-Time System Performance'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%';
          }
        }
      },
      x: {
        ticks: {
          maxTicksLimit: 10
        }
      }
    },
    animation: {
      duration: 0 // Disable animation for real-time updates
    }
  };

  const lineChartData = {
    labels: historicalData.labels,
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: historicalData.cpu,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Memory Usage (%)',
        data: historicalData.memory,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Disk Usage (%)',
        data: historicalData.disk,
        borderColor: 'rgb(255, 206, 86)',
        backgroundColor: 'rgba(255, 206, 86, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  // Current metrics doughnut chart
  const doughnutChartData = metrics ? {
    labels: ['CPU', 'Memory', 'Disk'],
    datasets: [{
      data: [metrics.cpu_usage, metrics.memory_percentage, metrics.disk_percentage],
      backgroundColor: [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 206, 86, 0.8)'
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)'
      ],
      borderWidth: 2
    }]
  } : null;

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom'
      },
      title: {
        display: true,
        text: 'Current Resource Usage'
      }
    }
  };

  // Utility functions
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (percentage) => {
    if (percentage < 60) return 'success';
    if (percentage < 80) return 'warning';
    return 'error';
  };

  const getAlertSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  };

  if (loading && !metrics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading performance monitoring...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Real-Time Performance Monitor
        </Typography>
        
        <Box display="flex" alignItems="center" gap={2}>
          {/* Connection Status */}
          <Chip
            icon={connectionStatus.isConnected ? <CheckCircle /> : <ErrorIcon />}
            label={`${connectionStatus.connectionType || 'disconnected'}`}
            color={connectionStatus.isConnected ? "success" : "error"}
            variant="outlined"
            size="small"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={isMonitoring}
                onChange={(e) => setIsMonitoring(e.target.checked)}
                color="primary"
              />
            }
            label={isMonitoring ? "Live" : "Paused"}
          />
          
          <Chip
            icon={isMonitoring ? <PlayIcon /> : <PauseIcon />}
            label={`${refreshInterval / 1000}s interval`}
            color={isMonitoring ? "success" : "default"}
            variant="outlined"
          />

          <Tooltip title="Refresh Now">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <Box mb={3}>
          <Typography variant="h6" gutterBottom>
            Active Alerts ({alerts.length})
          </Typography>
          {alerts.map((alert, index) => (
            <Alert 
              key={alert.id || index} 
              severity={getAlertSeverityColor(alert.severity)}
              sx={{ mb: 1 }}
            >
              <Typography variant="subtitle2">{alert.title}</Typography>
              <Typography variant="body2">{alert.description}</Typography>
            </Alert>
          ))}
        </Box>
      )}

      {/* Current Metrics Overview */}
      {metrics && (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">CPU Usage</Typography>
                </Box>
                <Typography variant="h4" color={getStatusColor(metrics.cpu_usage)}>
                  {metrics.cpu_usage.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.cpu_usage} 
                  color={getStatusColor(metrics.cpu_usage)}
                  sx={{ mt: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {metrics.cpu_cores} cores @ {metrics.cpu_frequency} GHz
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MemoryIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Memory</Typography>
                </Box>
                <Typography variant="h4" color={getStatusColor(metrics.memory_percentage)}>
                  {metrics.memory_percentage.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.memory_percentage} 
                  color={getStatusColor(metrics.memory_percentage)}
                  sx={{ mt: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {formatBytes(metrics.memory_used)} / {formatBytes(metrics.memory_total)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <StorageIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Disk Usage</Typography>
                </Box>
                <Typography variant="h4" color={getStatusColor(metrics.disk_percentage)}>
                  {metrics.disk_percentage.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.disk_percentage} 
                  color={getStatusColor(metrics.disk_percentage)}
                  sx={{ mt: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {formatBytes(metrics.disk_used)} / {formatBytes(metrics.disk_total)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <NetworkIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Network</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {metrics.network_connections}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Connections
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  RX: {formatBytes(metrics.network_rx)} | TX: {formatBytes(metrics.network_tx)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Real-time Performance Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box height={400}>
                <Line data={lineChartData} options={lineChartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Usage Breakdown */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Box height={400}>
                {doughnutChartData && (
                  <Doughnut data={doughnutChartData} options={doughnutOptions} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Application Metrics */}
        {metrics && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Application Performance Metrics
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center" p={2}>
                      <Typography variant="h4" color="primary">
                        {metrics.active_jobs || 0}
                      </Typography>
                      <Typography variant="subtitle1">Active Jobs</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center" p={2}>
                      <Typography variant="h4" color="warning.main">
                        {metrics.queue_size || 0}
                      </Typography>
                      <Typography variant="subtitle1">Queue Size</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center" p={2}>
                      <Typography variant="h4" color={getStatusColor(metrics.error_rate || 0)}>
                        {(metrics.error_rate || 0).toFixed(1)}%
                      </Typography>
                      <Typography variant="subtitle1">Error Rate</Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box textAlign="center" p={2}>
                      <Typography variant="h4" color="info.main">
                        {metrics.avg_response_time || 0}ms
                      </Typography>
                      <Typography variant="subtitle1">Avg Response</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Footer Info */}
      <Box mt={3} textAlign="center">
        <Typography variant="caption" color="text.secondary">
          Last updated: {metrics ? new Date(metrics.timestamp).toLocaleString() : 'N/A'} | 
          Auto-refresh: {isMonitoring ? 'Enabled' : 'Disabled'} | 
          Interval: {refreshInterval / 1000}s
        </Typography>
      </Box>
    </Box>
  );
};

export default RealTimePerformanceMonitor;