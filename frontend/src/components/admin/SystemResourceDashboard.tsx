/**
 * T013: System Resource Usage Dashboard
 * Comprehensive resource monitoring interface with detailed analytics
 * for storage, processes, memory, CPU, and network usage
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  LinearProgress,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Computer as CPUIcon,
  NetworkCheck as NetworkIcon,
  PlaylistPlay as ProcessIcon,
  Dataset as DatabaseIcon,  // Use Dataset instead of Database
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  DataUsage as DataUsageIcon
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
  ArcElement,
  BarElement
} from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';

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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`resource-tabpanel-${index}`}
      aria-labelledby={`resource-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SystemResourceDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Resource data state
  const [storageData, setStorageData] = useState<any>(null);
  const [processData, setProcessData] = useState<any>(null);
  const [memoryData, setMemoryData] = useState<any>(null);
  const [cpuData, setCpuData] = useState<any>(null);
  const [networkData, setNetworkData] = useState<any>(null);
  const [applicationData, setApplicationData] = useState<any>(null);

  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch resource data functions
  const fetchStorageData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/storage', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setStorageData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch storage data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching storage data:', err);
      setError(`Storage data error: ${err.message}`);
    }
  };

  const fetchProcessData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/processes', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setProcessData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch process data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching process data:', err);
      setError(`Process data error: ${err.message}`);
    }
  };

  const fetchMemoryData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/memory', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setMemoryData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch memory data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching memory data:', err);
      setError(`Memory data error: ${err.message}`);
    }
  };

  const fetchCpuData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/cpu', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setCpuData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch CPU data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching CPU data:', err);
      setError(`CPU data error: ${err.message}`);
    }
  };

  const fetchNetworkData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/network', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setNetworkData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch network data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching network data:', err);
      setError(`Network data error: ${err.message}`);
    }
  };

  const fetchApplicationData = async () => {
    try {
      const response = await fetch('/api/admin/system/resources/application', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setApplicationData(result.data);
        } else {
          throw new Error(result.error || 'Failed to fetch application data');
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err: any) {
      console.error('Error fetching application data:', err);
      setError(`Application data error: ${err.message}`);
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchStorageData(),
        fetchProcessData(),
        fetchMemoryData(),
        fetchCpuData(),
        fetchNetworkData(),
        fetchApplicationData()
      ]);
    } catch (err: any) {
      setError(`Failed to fetch resource data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchAllData();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAutoRefreshToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAutoRefresh(event.target.checked);
  };

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      refreshIntervalRef.current = setInterval(fetchAllData, refreshInterval);
    } else {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval]);

  // Initial data fetch
  useEffect(() => {
    fetchAllData();
  }, []);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  // Storage Usage Panel
  const renderStoragePanel = () => (
    <Grid container spacing={3}>
      {/* System Storage Overview */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader 
            title="System Storage" 
            avatar={<StorageIcon color="primary" />}
          />
          <CardContent>
            {storageData?.storage?.system && (
              <>
                <Typography variant="h4" color="primary" gutterBottom>
                  {storageData.storage.system.percentage.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={storageData.storage.system.percentage} 
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Used: {formatBytes(storageData.storage.system.used)} / {formatBytes(storageData.storage.system.total)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Free: {formatBytes(storageData.storage.system.free)}
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Application Directories */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader 
            title="Application Storage" 
            avatar={<DataUsageIcon color="secondary" />}
          />
          <CardContent>
            <List dense>
              {storageData?.storage && Object.entries(storageData.storage)
                .filter(([key]) => key !== 'system')
                .map(([name, data]: [string, any]) => (
                  <ListItem key={name}>
                    <ListItemText
                      primary={name.charAt(0).toUpperCase() + name.slice(1)}
                      secondary={data.human_readable || data.size ? formatBytes(data.size) : data.error || 'N/A'}
                    />
                  </ListItem>
                ))}
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Database Files */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Database Storage" 
            avatar={<DatabaseIcon color="info" />}
          />
          <CardContent>
            {storageData?.storage?.database_files && (
              <>
                <Typography variant="h6" gutterBottom>
                  Total Database Size: {storageData.storage.database_files.human_readable}
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(storageData.storage.database_files.files).map(([file, data]: [string, any]) => (
                    <Grid item xs={12} sm={6} md={4} key={file}>
                      <Paper elevation={1} sx={{ p: 2 }}>
                        <Typography variant="subtitle2">{file}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {data.human_readable}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Process Management Panel
  const renderProcessPanel = () => (
    <Grid container spacing={3}>
      {/* Process Summary */}
      <Grid item xs={12} md={4}>
        <Card>
          <CardHeader 
            title="Process Summary" 
            avatar={<ProcessIcon color="primary" />}
          />
          <CardContent>
            {processData && (
              <>
                <Typography variant="h4" color="primary" gutterBottom>
                  {processData.total_processes}
                </Typography>
                <Typography variant="body1" gutterBottom>Total Processes</Typography>
                
                <Typography variant="h6" sx={{ mt: 2 }}>System Load</Typography>
                <Typography variant="body2">
                  1min: {processData.load_average?.['1_min'] || 0}
                </Typography>
                <Typography variant="body2">
                  5min: {processData.load_average?.['5_min'] || 0}
                </Typography>
                <Typography variant="body2">
                  15min: {processData.load_average?.['15_min'] || 0}
                </Typography>

                <Typography variant="h6" sx={{ mt: 2 }}>System Uptime</Typography>
                <Typography variant="body2">
                  {processData.system_uptime?.human_readable || 'N/A'}
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Top Processes */}
      <Grid item xs={12} md={8}>
        <Card>
          <CardHeader title="Top Processes by CPU Usage" />
          <CardContent>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>PID</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell align="right">CPU %</TableCell>
                    <TableCell align="right">Memory %</TableCell>
                    <TableCell align="right">Memory (MB)</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {processData?.processes?.slice(0, 10).map((process: any) => (
                    <TableRow key={process.pid}>
                      <TableCell>{process.pid}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          {process.name}
                          {process.is_current && (
                            <Chip 
                              label="Current" 
                              size="small" 
                              color="primary" 
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">{process.cpu_percent?.toFixed(1) || 0}</TableCell>
                      <TableCell align="right">{process.memory_percent?.toFixed(1) || 0}</TableCell>
                      <TableCell align="right">{process.memory_mb?.toFixed(1) || 0}</TableCell>
                      <TableCell>
                        <Chip 
                          label={process.status} 
                          size="small" 
                          color={process.status === 'running' ? 'success' : 'default'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Memory Details Panel
  const renderMemoryPanel = () => {
    const memoryChartData = memoryData?.virtual_memory ? {
      labels: ['Used', 'Available', 'Cached', 'Buffers'],
      datasets: [{
        data: [
          memoryData.virtual_memory.used,
          memoryData.virtual_memory.available,
          memoryData.virtual_memory.cached || 0,
          memoryData.virtual_memory.buffers || 0
        ],
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
        borderWidth: 2
      }]
    } : null;

    return (
      <Grid container spacing={3}>
        {/* Memory Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Memory Usage" 
              avatar={<MemoryIcon color="primary" />}
            />
            <CardContent>
              {memoryData?.virtual_memory && (
                <>
                  <Typography variant="h4" color="primary" gutterBottom>
                    {memoryData.virtual_memory.percentage.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={memoryData.virtual_memory.percentage} 
                    sx={{ mb: 2, height: 8, borderRadius: 4 }}
                    color={memoryData.virtual_memory.percentage > 80 ? 'error' : 'primary'}
                  />
                  <Typography variant="body2">
                    Used: {formatBytes(memoryData.virtual_memory.used)}
                  </Typography>
                  <Typography variant="body2">
                    Available: {formatBytes(memoryData.virtual_memory.available)}
                  </Typography>
                  <Typography variant="body2">
                    Total: {formatBytes(memoryData.virtual_memory.total)}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Memory Distribution Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Memory Distribution" />
            <CardContent>
              {memoryChartData && (
                <Box height={300}>
                  <Doughnut 
                    data={memoryChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom'
                        }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Swap Memory */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Swap Memory" />
            <CardContent>
              {memoryData?.swap_memory && (
                <>
                  <Typography variant="h5" color="secondary" gutterBottom>
                    {memoryData.swap_memory.percentage.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={memoryData.swap_memory.percentage} 
                    sx={{ mb: 2, height: 8, borderRadius: 4 }}
                    color="secondary"
                  />
                  <Typography variant="body2">
                    Used: {formatBytes(memoryData.swap_memory.used)}
                  </Typography>
                  <Typography variant="body2">
                    Free: {formatBytes(memoryData.swap_memory.free)}
                  </Typography>
                  <Typography variant="body2">
                    Total: {formatBytes(memoryData.swap_memory.total)}
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top Memory Processes */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Top Memory Consumers" />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Process</TableCell>
                      <TableCell align="right">Memory %</TableCell>
                      <TableCell align="right">Memory (MB)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {memoryData?.top_memory_processes?.slice(0, 5).map((process: any) => (
                      <TableRow key={process.pid}>
                        <TableCell>{process.name}</TableCell>
                        <TableCell align="right">{process.memory_percent?.toFixed(1)}</TableCell>
                        <TableCell align="right">{process.memory_mb?.toFixed(1)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  // CPU Details Panel
  const renderCpuPanel = () => {
    const cpuCoreData = cpuData?.cpu_percent_per_core ? {
      labels: cpuData.cpu_percent_per_core.map((_: any, index: number) => `Core ${index + 1}`),
      datasets: [{
        label: 'CPU Usage %',
        data: cpuData.cpu_percent_per_core,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    } : null;

    return (
      <Grid container spacing={3}>
        {/* CPU Overview */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="CPU Usage" 
              avatar={<CPUIcon color="primary" />}
            />
            <CardContent>
              {cpuData && (
                <>
                  <Typography variant="h4" color="primary" gutterBottom>
                    {cpuData.cpu_percent_total?.toFixed(1) || 0}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={cpuData.cpu_percent_total || 0} 
                    sx={{ mb: 2, height: 8, borderRadius: 4 }}
                    color={cpuData.cpu_percent_total > 80 ? 'error' : 'primary'}
                  />
                  <Typography variant="body2">
                    Logical Cores: {cpuData.cpu_count?.logical || 0}
                  </Typography>
                  <Typography variant="body2">
                    Physical Cores: {cpuData.cpu_count?.physical || 0}
                  </Typography>
                  <Typography variant="body2">
                    Frequency: {cpuData.cpu_frequency?.current?.toFixed(0) || 0} MHz
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* CPU Per Core Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="CPU Usage Per Core" />
            <CardContent>
              {cpuCoreData && (
                <Box height={300}>
                  <Bar 
                    data={cpuCoreData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100
                        }
                      }
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* CPU Statistics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="CPU Statistics" />
            <CardContent>
              {cpuData?.cpu_stats && (
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Context Switches" 
                      secondary={cpuData.cpu_stats.ctx_switches?.toLocaleString() || 0}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Interrupts" 
                      secondary={cpuData.cpu_stats.interrupts?.toLocaleString() || 0}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="Soft Interrupts" 
                      secondary={cpuData.cpu_stats.soft_interrupts?.toLocaleString() || 0}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText 
                      primary="System Calls" 
                      secondary={cpuData.cpu_stats.syscalls?.toLocaleString() || 0}
                    />
                  </ListItem>
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top CPU Processes */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Top CPU Consumers" />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Process</TableCell>
                      <TableCell align="right">CPU %</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {cpuData?.top_cpu_processes?.slice(0, 8).map((process: any) => (
                      <TableRow key={process.pid}>
                        <TableCell>{process.name}</TableCell>
                        <TableCell align="right">{process.cpu_percent?.toFixed(1)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  // Network Details Panel
  const renderNetworkPanel = () => (
    <Grid container spacing={3}>
      {/* Network Interfaces */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Network Interfaces" 
            avatar={<NetworkIcon color="primary" />}
          />
          <CardContent>
            {networkData?.interfaces && Object.entries(networkData.interfaces).map(([name, data]: [string, any]) => (
              <Accordion key={name}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">{name}</Typography>
                  <Chip 
                    label={data.is_up ? 'UP' : 'DOWN'}
                    color={data.is_up ? 'success' : 'error'}
                    size="small"
                    sx={{ ml: 2 }}
                  />
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2">Addresses:</Typography>
                      {data.addresses?.map((addr: any, index: number) => (
                        <Typography key={index} variant="body2">
                          {addr.family}: {addr.address}
                        </Typography>
                      ))}
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2">Speed: {data.speed || 0} Mbps</Typography>
                      <Typography variant="body2">MTU: {data.mtu || 0}</Typography>
                      <Typography variant="body2">Duplex: {data.duplex || 'unknown'}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="subtitle2">Traffic:</Typography>
                      <Typography variant="body2">
                        Sent: {formatBytes(data.bytes_sent || 0)} ({data.packets_sent || 0} packets)
                      </Typography>
                      <Typography variant="body2">
                        Received: {formatBytes(data.bytes_recv || 0)} ({data.packets_recv || 0} packets)
                      </Typography>
                      <Typography variant="body2">
                        Errors: In={data.errors_in || 0}, Out={data.errors_out || 0}
                      </Typography>
                      <Typography variant="body2">
                        Dropped: In={data.dropped_in || 0}, Out={data.dropped_out || 0}
                      </Typography>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Active Connections */}
      <Grid item xs={12}>
        <Card>
          <CardHeader title="Active Network Connections" />
          <CardContent>
            <Typography variant="body2" gutterBottom>
              Total Connections: {networkData?.total_connections || 0}
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Local Address</TableCell>
                    <TableCell>Remote Address</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>PID</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {networkData?.active_connections?.map((conn: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell>{conn.local_address}</TableCell>
                      <TableCell>{conn.remote_address}</TableCell>
                      <TableCell>
                        <Chip 
                          label={conn.status} 
                          size="small" 
                          color={conn.status === 'ESTABLISHED' ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>{conn.type}</TableCell>
                      <TableCell>{conn.pid || 'N/A'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  // Application Resources Panel
  const renderApplicationPanel = () => (
    <Grid container spacing={3}>
      {/* Database Statistics */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader 
            title="Database Statistics" 
            avatar={<DatabaseIcon color="primary" />}
          />
          <CardContent>
            {applicationData?.database && (
              <>
                <Typography variant="h6" gutterBottom>
                  Database Size: {applicationData.database.file_size_human || 'N/A'}
                </Typography>
                
                {applicationData.database.tables && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }}>Table Records:</Typography>
                    <List dense>
                      {Object.entries(applicationData.database.tables).map(([table, count]: [string, any]) => (
                        <ListItem key={table}>
                          <ListItemText 
                            primary={table} 
                            secondary={`${count.toLocaleString()} records`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}

                {applicationData.database.pages && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }}>Page Information:</Typography>
                    <Typography variant="body2">
                      Pages: {applicationData.database.pages.count?.toLocaleString()}
                    </Typography>
                    <Typography variant="body2">
                      Page Size: {applicationData.database.pages.size} bytes
                    </Typography>
                    <Typography variant="body2">
                      Auto Vacuum: {applicationData.database.auto_vacuum ? 'Enabled' : 'Disabled'}
                    </Typography>
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Job Statistics */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader 
            title="Job Statistics" 
            avatar={<AssessmentIcon color="secondary" />}
          />
          <CardContent>
            {applicationData?.jobs && (
              <>
                <Typography variant="h6" gutterBottom>
                  Jobs (Last 24h): {applicationData.jobs.jobs_last_24h || 0}
                </Typography>
                
                {applicationData.jobs.by_status && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 2 }}>Jobs by Status:</Typography>
                    {Object.entries(applicationData.jobs.by_status).map(([status, count]: [string, any]) => (
                      <Box key={status} display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="body2">{status}:</Typography>
                        <Chip 
                          label={count.toString()} 
                          size="small"
                          color={status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'default'}
                        />
                      </Box>
                    ))}
                  </>
                )}

                <Typography variant="body2" sx={{ mt: 2 }}>
                  Avg Duration: {applicationData.jobs.avg_duration_seconds ? 
                    formatUptime(applicationData.jobs.avg_duration_seconds) : 'N/A'}
                </Typography>
              </>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Application Memory Usage */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Application Memory Usage" 
            avatar={<SpeedIcon color="info" />}
          />
          <CardContent>
            {applicationData?.application_memory && (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2">RSS Memory</Typography>
                    <Typography variant="h6">
                      {applicationData.application_memory.rss_human || 'N/A'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2">Virtual Memory</Typography>
                    <Typography variant="h6">
                      {applicationData.application_memory.vms_human || 'N/A'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="subtitle2">Memory %</Typography>
                    <Typography variant="h6">
                      {applicationData.application_memory.percent?.toFixed(2) || 0}%
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  if (loading && !storageData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading system resource data...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          System Resource Usage Dashboard
        </Typography>
        
        <Box display="flex" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={handleAutoRefreshToggle}
                color="primary"
              />
            }
            label="Auto Refresh"
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

      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Storage" icon={<StorageIcon />} />
          <Tab label="Processes" icon={<ProcessIcon />} />
          <Tab label="Memory" icon={<MemoryIcon />} />
          <Tab label="CPU" icon={<CPUIcon />} />
          <Tab label="Network" icon={<NetworkIcon />} />
          <Tab label="Application" icon={<DatabaseIcon />} />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {renderStoragePanel()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderProcessPanel()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderMemoryPanel()}
      </TabPanel>
      <TabPanel value={tabValue} index={3}>
        {renderCpuPanel()}
      </TabPanel>
      <TabPanel value={tabValue} index={4}>
        {renderNetworkPanel()}
      </TabPanel>
      <TabPanel value={tabValue} index={5}>
        {renderApplicationPanel()}
      </TabPanel>
    </Box>
  );
};

export default SystemResourceDashboard;