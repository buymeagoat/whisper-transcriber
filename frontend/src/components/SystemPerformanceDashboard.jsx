import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Tab,
  Tabs,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  NetworkCheck as NetworkIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Computer as ComputerIcon
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';
import { systemPerformanceService } from '../services/systemPerformanceService';
import { formatBytes, formatDuration, formatNumber } from '../utils/formatters';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

const SystemPerformanceDashboard = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // System metrics state
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: { usage: 0, cores: 0, frequency: 0 },
    memory: { used: 0, total: 0, percentage: 0 },
    disk: { used: 0, total: 0, percentage: 0 },
    network: { rx: 0, tx: 0, connections: 0 }
  });
  
  const [applicationMetrics, setApplicationMetrics] = useState({
    activeJobs: 0,
    queueSize: 0,
    errorRate: 0,
    responseTime: 0,
    throughput: 0,
    uptime: 0
  });
  
  const [historicalData, setHistoricalData] = useState({
    labels: [],
    cpuData: [],
    memoryData: [],
    diskData: [],
    networkData: []
  });
  
  const [alerts, setAlerts] = useState([]);
  const [services, setServices] = useState([]);

  // Fetch system metrics
  const fetchSystemMetrics = useCallback(async () => {
    try {
      const response = await systemPerformanceService.getSystemMetrics();
      setSystemMetrics(response.data.system);
      setApplicationMetrics(response.data.application);
      
      // Update historical data
      const now = new Date().toLocaleTimeString();
      setHistoricalData(prev => {
        const newLabels = [...prev.labels, now].slice(-20); // Keep last 20 points
        const newCpuData = [...prev.cpuData, response.data.system.cpu.usage].slice(-20);
        const newMemoryData = [...prev.memoryData, response.data.system.memory.percentage].slice(-20);
        const newDiskData = [...prev.diskData, response.data.system.disk.percentage].slice(-20);
        const newNetworkData = [...prev.networkData, response.data.system.network.rx + response.data.system.network.tx].slice(-20);
        
        return {
          labels: newLabels,
          cpuData: newCpuData,
          memoryData: newMemoryData,
          diskData: newDiskData,
          networkData: newNetworkData
        };
      });
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch system metrics:', err);
      setError('Failed to fetch system metrics');
    }
  }, []);

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await systemPerformanceService.getActiveAlerts();
      setAlerts(response.data.alerts);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  }, []);

  // Fetch service status
  const fetchServiceStatus = useCallback(async () => {
    try {
      const response = await systemPerformanceService.getServiceStatus();
      setServices(response.data.services);
    } catch (err) {
      console.error('Failed to fetch service status:', err);
    }
  }, []);

  // Load all data
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemMetrics(),
        fetchAlerts(),
        fetchServiceStatus()
      ]);
    } finally {
      setLoading(false);
    }
  }, [fetchSystemMetrics, fetchAlerts, fetchServiceStatus]);

  // Auto-refresh effect
  useEffect(() => {
    let interval;
    
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchSystemMetrics();
        fetchAlerts();
        fetchServiceStatus();
      }, refreshInterval);
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh, refreshInterval, fetchSystemMetrics, fetchAlerts, fetchServiceStatus]);

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Chart configurations
  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top'
      },
      title: {
        display: true,
        text: 'System Performance Trends'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100
      }
    },
    animation: {
      duration: 300
    }
  };

  const lineChartData = {
    labels: historicalData.labels,
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: historicalData.cpuData,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.1
      },
      {
        label: 'Memory Usage (%)',
        data: historicalData.memoryData,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        tension: 0.1
      },
      {
        label: 'Disk Usage (%)',
        data: historicalData.diskData,
        borderColor: 'rgb(255, 205, 86)',
        backgroundColor: 'rgba(255, 205, 86, 0.2)',
        tension: 0.1
      }
    ]
  };

  const doughnutChartData = {
    labels: ['Used', 'Free'],
    datasets: [
      {
        data: [systemMetrics.memory.used, systemMetrics.memory.total - systemMetrics.memory.used],
        backgroundColor: ['#FF6384', '#36A2EB'],
        hoverBackgroundColor: ['#FF6384', '#36A2EB']
      }
    ]
  };

  // Utility functions
  const getStatusColor = (percentage) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 75) return 'warning';
    return 'success';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <ComputerIcon />;
    }
  };

  // Render system overview cards
  const renderSystemOverview = () => (
    <Grid container spacing={3}>
      {/* CPU Usage Card */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardHeader
            avatar={<SpeedIcon color="primary" />}
            title="CPU Usage"
            subheader={`${systemMetrics.cpu.cores} cores @ ${systemMetrics.cpu.frequency}GHz`}
          />
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Box flexGrow={1}>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics.cpu.usage}
                  color={getStatusColor(systemMetrics.cpu.usage)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Typography variant="h6" sx={{ ml: 2 }}>
                {systemMetrics.cpu.usage.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              Current CPU utilization
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Memory Usage Card */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardHeader
            avatar={<MemoryIcon color="primary" />}
            title="Memory Usage"
            subheader={`${formatBytes(systemMetrics.memory.total)} total`}
          />
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Box flexGrow={1}>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics.memory.percentage}
                  color={getStatusColor(systemMetrics.memory.percentage)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Typography variant="h6" sx={{ ml: 2 }}>
                {systemMetrics.memory.percentage.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {formatBytes(systemMetrics.memory.used)} used
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Disk Usage Card */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardHeader
            avatar={<StorageIcon color="primary" />}
            title="Disk Usage"
            subheader={`${formatBytes(systemMetrics.disk.total)} total`}
          />
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Box flexGrow={1}>
                <LinearProgress
                  variant="determinate"
                  value={systemMetrics.disk.percentage}
                  color={getStatusColor(systemMetrics.disk.percentage)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Typography variant="h6" sx={{ ml: 2 }}>
                {systemMetrics.disk.percentage.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {formatBytes(systemMetrics.disk.used)} used
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Network Usage Card */}
      <Grid item xs={12} md={3}>
        <Card>
          <CardHeader
            avatar={<NetworkIcon color="primary" />}
            title="Network"
            subheader={`${systemMetrics.network.connections} connections`}
          />
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              RX: {formatBytes(systemMetrics.network.rx)}/s
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              TX: {formatBytes(systemMetrics.network.tx)}/s
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total: {formatBytes(systemMetrics.network.rx + systemMetrics.network.tx)}/s
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Render application metrics
  const renderApplicationMetrics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader title="Application Performance" />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="h4" color="primary">
                  {applicationMetrics.activeJobs}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Jobs
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="primary">
                  {applicationMetrics.queueSize}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Queue Size
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="primary">
                  {applicationMetrics.errorRate.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Error Rate
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="h4" color="primary">
                  {applicationMetrics.responseTime}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader title="System Information" />
          <CardContent>
            <Typography variant="body1" gutterBottom>
              <strong>Uptime:</strong> {formatDuration(applicationMetrics.uptime)}
            </Typography>
            <Typography variant="body1" gutterBottom>
              <strong>Throughput:</strong> {formatNumber(applicationMetrics.throughput)} req/min
            </Typography>
            <Typography variant="body1" gutterBottom>
              <strong>Memory Usage:</strong> {formatBytes(systemMetrics.memory.used)} / {formatBytes(systemMetrics.memory.total)}
            </Typography>
            <Typography variant="body1">
              <strong>CPU Cores:</strong> {systemMetrics.cpu.cores} @ {systemMetrics.cpu.frequency}GHz
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Render alerts panel
  const renderAlerts = () => (
    <Card>
      <CardHeader
        title="Active Alerts"
        subheader={`${alerts.length} active alert(s)`}
      />
      <CardContent>
        {alerts.length === 0 ? (
          <Alert severity="success">
            <CheckCircleIcon sx={{ mr: 1 }} />
            No active alerts - system is healthy
          </Alert>
        ) : (
          <List>
            {alerts.map((alert, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemIcon>
                    {getStatusIcon(alert.severity)}
                  </ListItemIcon>
                  <ListItemText
                    primary={alert.title}
                    secondary={`${alert.description} - ${new Date(alert.timestamp).toLocaleString()}`}
                  />
                  <Chip
                    label={alert.severity}
                    color={alert.severity === 'error' ? 'error' : 'warning'}
                    size="small"
                  />
                </ListItem>
                {index < alerts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );

  // Render service status
  const renderServiceStatus = () => (
    <Card>
      <CardHeader title="Service Status" />
      <CardContent>
        <List>
          {services.map((service, index) => (
            <React.Fragment key={index}>
              <ListItem>
                <ListItemIcon>
                  {getStatusIcon(service.status)}
                </ListItemIcon>
                <ListItemText
                  primary={service.name}
                  secondary={`${service.description} - Last check: ${new Date(service.lastCheck).toLocaleString()}`}
                />
                <Chip
                  label={service.status}
                  color={service.status === 'healthy' ? 'success' : service.status === 'warning' ? 'warning' : 'error'}
                  size="small"
                />
              </ListItem>
              {index < services.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );

  // Tab change handler
  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading system performance data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          <DashboardIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
          System Performance Dashboard
        </Typography>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          
          <Tooltip title="Refresh Now">
            <IconButton
              onClick={loadDashboardData}
              disabled={loading}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Settings">
            <IconButton>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Performance Trends" />
          <Tab label="Alerts & Status" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {currentTab === 0 && (
        <Box>
          {renderSystemOverview()}
          <Box mt={3}>
            {renderApplicationMetrics()}
          </Box>
        </Box>
      )}

      {currentTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title="Performance Trends" />
              <CardContent>
                <Line data={lineChartData} options={lineChartOptions} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="Memory Distribution" />
              <CardContent>
                <Doughnut data={doughnutChartData} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {currentTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            {renderAlerts()}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderServiceStatus()}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default SystemPerformanceDashboard;