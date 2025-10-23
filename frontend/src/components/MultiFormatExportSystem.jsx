import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Checkbox,
  FormControlLabel,
  Chip,
  LinearProgress,
  Alert,
  AlertTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  Slider,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Snackbar
} from '@mui/material';
import {
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  Settings as SettingsIcon,
  PlaylistAdd as PlaylistAddIcon,
  History as HistoryIcon,
  ExpandMore as ExpandMoreIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  GetApp as GetAppIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon
} from '@mui/icons-material';

import { exportSystemService } from '../services/exportSystemService';

/**
 * T034 Multi-Format Export System
 * 
 * Comprehensive export interface supporting:
 * - Multiple formats (SRT, VTT, DOCX, PDF, JSON, TXT)
 * - Customizable templates and styling
 * - Individual and batch export operations
 * - Export history and progress tracking
 * - Template management and configuration
 */
const MultiFormatExportSystem = ({ transcriptJob, onClose }) => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [exportFormats, setExportFormats] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [exportJobs, setExportJobs] = useState([]);
  const [batchExports, setBatchExports] = useState([]);
  const [exportHistory, setExportHistory] = useState([]);
  
  // Export dialog state
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [customConfig, setCustomConfig] = useState({});
  const [exportType, setExportType] = useState('single'); // single or batch
  const [selectedJobs, setSelectedJobs] = useState([]);
  
  // Batch export dialog state
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  const [batchName, setBatchName] = useState('');
  const [batchDescription, setBatchDescription] = useState('');
  
  // Template management state
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [templateFormData, setTemplateFormData] = useState({
    name: '',
    description: '',
    template_type: 'subtitle',
    supported_formats: [],
    template_config: {},
    styling_config: {},
    layout_config: {}
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [refreshInterval, setRefreshInterval] = useState(null);
  
  // Refs
  const pollingRef = useRef(null);

  // Load initial data
  useEffect(() => {
    loadExportFormats();
    loadTemplates();
    loadExportJobs();
    loadBatchExports();
    loadExportHistory();
    
    // Set up polling for active exports
    startPolling();
    
    return () => stopPolling();
  }, []);

  // Data loading functions
  const loadExportFormats = async () => {
    try {
      const formats = await exportSystemService.getAvailableFormats();
      setExportFormats(formats);
    } catch (err) {
      setError('Failed to load export formats');
    }
  };

  const loadTemplates = async () => {
    try {
      const templatesData = await exportSystemService.getTemplates();
      setTemplates(templatesData);
    } catch (err) {
      setError('Failed to load templates');
    }
  };

  const loadExportJobs = async () => {
    try {
      const jobs = await exportSystemService.getUserExportJobs();
      setExportJobs(jobs);
    } catch (err) {
      setError('Failed to load export jobs');
    }
  };

  const loadBatchExports = async () => {
    try {
      const batches = await exportSystemService.getUserBatchExports();
      setBatchExports(batches);
    } catch (err) {
      setError('Failed to load batch exports');
    }
  };

  const loadExportHistory = async () => {
    try {
      const history = await exportSystemService.getExportHistory();
      setExportHistory(history);
    } catch (err) {
      setError('Failed to load export history');
    }
  };

  // Polling for active exports
  const startPolling = () => {
    pollingRef.current = setInterval(() => {
      loadExportJobs();
      loadBatchExports();
    }, 3000); // Poll every 3 seconds
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  // Export operations
  const handleSingleExport = async () => {
    try {
      setLoading(true);
      
      const exportData = {
        job_id: transcriptJob.id,
        format: selectedFormat,
        template_id: selectedTemplate || undefined,
        custom_config: Object.keys(customConfig).length > 0 ? customConfig : undefined
      };

      await exportSystemService.createExportJob(exportData);
      
      setNotification({
        open: true,
        message: `Export job created for ${selectedFormat.toUpperCase()} format`,
        severity: 'success'
      });
      
      setExportDialogOpen(false);
      resetExportForm();
      loadExportJobs();
      
    } catch (err) {
      setError(`Failed to create export job: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchExport = async () => {
    try {
      setLoading(true);
      
      const batchData = {
        name: batchName,
        description: batchDescription,
        job_ids: selectedJobs,
        export_format: selectedFormat,
        template_id: selectedTemplate || undefined,
        batch_config: Object.keys(customConfig).length > 0 ? customConfig : undefined
      };

      await exportSystemService.createBatchExport(batchData);
      
      setNotification({
        open: true,
        message: `Batch export "${batchName}" created with ${selectedJobs.length} jobs`,
        severity: 'success'
      });
      
      setBatchDialogOpen(false);
      resetBatchForm();
      loadBatchExports();
      
    } catch (err) {
      setError(`Failed to create batch export: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (exportJob) => {
    try {
      await exportSystemService.downloadExport(exportJob.id);
      
      setNotification({
        open: true,
        message: `Downloading ${exportJob.format.toUpperCase()} export`,
        severity: 'success'
      });
      
    } catch (err) {
      setError(`Download failed: ${err.message}`);
    }
  };

  const handleBatchDownload = async (batchExport) => {
    try {
      await exportSystemService.downloadBatchExport(batchExport.id);
      
      setNotification({
        open: true,
        message: `Downloading batch export "${batchExport.name}"`,
        severity: 'success'
      });
      
    } catch (err) {
      setError(`Batch download failed: ${err.message}`);
    }
  };

  // Template operations
  const handleCreateTemplate = async () => {
    try {
      setLoading(true);
      
      await exportSystemService.createTemplate(templateFormData);
      
      setNotification({
        open: true,
        message: `Template "${templateFormData.name}" created successfully`,
        severity: 'success'
      });
      
      setTemplateDialogOpen(false);
      resetTemplateForm();
      loadTemplates();
      
    } catch (err) {
      setError(`Failed to create template: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Form reset functions
  const resetExportForm = () => {
    setSelectedFormat('');
    setSelectedTemplate('');
    setCustomConfig({});
    setExportType('single');
    setSelectedJobs([]);
  };

  const resetBatchForm = () => {
    setBatchName('');
    setBatchDescription('');
    resetExportForm();
  };

  const resetTemplateForm = () => {
    setTemplateFormData({
      name: '',
      description: '',
      template_type: 'subtitle',
      supported_formats: [],
      template_config: {},
      styling_config: {},
      layout_config: {}
    });
  };

  // Helper functions
  const getStatusColor = (status) => {
    const statusColors = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
      cancelled: 'default'
    };
    return statusColors[status] || 'default';
  };

  const getStatusIcon = (status) => {
    const statusIcons = {
      pending: <ScheduleIcon />,
      processing: <RefreshIcon />,
      completed: <CheckCircleIcon />,
      failed: <ErrorIcon />,
      cancelled: <CloseIcon />
    };
    return statusIcons[status] || <ScheduleIcon />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(0);
    return `${minutes}m ${remainingSeconds}s`;
  };

  // Tab content components
  const SingleExportTab = () => (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Current Transcript
              </Typography>
              
              {transcriptJob && (
                <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Source Transcript
                  </Typography>
                  <Typography variant="body1">
                    {transcriptJob.original_filename || `Job ${transcriptJob.id}`}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Duration: {transcriptJob.duration ? `${transcriptJob.duration}s` : 'Unknown'} • 
                    Model: {transcriptJob.model || 'Unknown'} • 
                    Status: {transcriptJob.status}
                  </Typography>
                </Box>
              )}

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Export Format</InputLabel>
                    <Select
                      value={selectedFormat}
                      onChange={(e) => setSelectedFormat(e.target.value)}
                      label="Export Format"
                    >
                      {exportFormats.map((format) => (
                        <MenuItem key={format.format} value={format.format}>
                          <Box>
                            <Typography variant="body1">
                              {format.display_name}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {format.file_extension} • Max: {format.max_file_size_mb}MB
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Template (Optional)</InputLabel>
                    <Select
                      value={selectedTemplate}
                      onChange={(e) => setSelectedTemplate(e.target.value)}
                      label="Template (Optional)"
                    >
                      <MenuItem value="">
                        <em>Use default settings</em>
                      </MenuItem>
                      {templates
                        .filter(template => 
                          template.supported_formats.includes(selectedFormat)
                        )
                        .map((template) => (
                          <MenuItem key={template.id} value={template.id}>
                            <Box>
                              <Typography variant="body1">
                                {template.name}
                                {template.is_system_template && (
                                  <Chip size="small" label="System" sx={{ ml: 1 }} />
                                )}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                {template.description}
                              </Typography>
                            </Box>
                          </MenuItem>
                        ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              {selectedFormat && (
                <ExportConfigurationPanel
                  format={selectedFormat}
                  formatConfig={exportFormats.find(f => f.format === selectedFormat)}
                  config={customConfig}
                  onChange={setCustomConfig}
                />
              )}

              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  onClick={handleSingleExport}
                  disabled={!selectedFormat || loading}
                  startIcon={<FileDownloadIcon />}
                >
                  Create Export
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <ExportJobsList 
            jobs={exportJobs}
            onDownload={handleDownload}
            onRefresh={loadExportJobs}
          />
        </Grid>
      </Grid>
    </Box>
  );

  const BatchExportTab = () => (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  Batch Export Operations
                </Typography>
                <Button
                  variant="contained"
                  onClick={() => setBatchDialogOpen(true)}
                  startIcon={<PlaylistAddIcon />}
                >
                  New Batch Export
                </Button>
              </Box>

              <BatchExportsList
                batches={batchExports}
                onDownload={handleBatchDownload}
                onRefresh={loadBatchExports}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Batch Export Guide
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Select Multiple Transcripts"
                    secondary="Choose up to 100 jobs for batch processing"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Consistent Format"
                    secondary="All jobs exported in the same format"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="ZIP Archive"
                    secondary="Downloads as compressed archive"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const TemplateManagementTab = () => (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  Export Templates
                </Typography>
                <Button
                  variant="contained"
                  onClick={() => setTemplateDialogOpen(true)}
                  startIcon={<SettingsIcon />}
                >
                  Create Template
                </Button>
              </Box>

              <TemplatesList
                templates={templates}
                onEdit={(template) => {
                  setTemplateFormData(template);
                  setTemplateDialogOpen(true);
                }}
                onRefresh={loadTemplates}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Template Types
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <SettingsIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Subtitle Templates"
                    secondary="For SRT and VTT formats"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SettingsIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Document Templates"
                    secondary="For DOCX and PDF formats"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <SettingsIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Structured Templates"
                    secondary="For JSON format"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const ExportHistoryTab = () => (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Export History
            </Typography>
            <Button
              variant="outlined"
              onClick={loadExportHistory}
              startIcon={<RefreshIcon />}
            >
              Refresh
            </Button>
          </Box>

          <ExportHistoryTable history={exportHistory} />
        </CardContent>
      </Card>
    </Box>
  );

  return (
    <Dialog
      open={true}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">
            Multi-Format Export System
          </Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Single Export" icon={<FileDownloadIcon />} />
            <Tab label="Batch Export" icon={<PlaylistAddIcon />} />
            <Tab label="Templates" icon={<SettingsIcon />} />
            <Tab label="History" icon={<HistoryIcon />} />
          </Tabs>
        </Box>

        <Box sx={{ mt: 2 }}>
          {activeTab === 0 && <SingleExportTab />}
          {activeTab === 1 && <BatchExportTab />}
          {activeTab === 2 && <TemplateManagementTab />}
          {activeTab === 3 && <ExportHistoryTab />}
        </Box>
      </DialogContent>

      {/* Export Configuration Dialog */}
      <ExportDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        onConfirm={exportType === 'single' ? handleSingleExport : handleBatchExport}
        format={selectedFormat}
        template={selectedTemplate}
        config={customConfig}
        loading={loading}
      />

      {/* Batch Export Dialog */}
      <BatchExportDialog
        open={batchDialogOpen}
        onClose={() => setBatchDialogOpen(false)}
        onConfirm={handleBatchExport}
        batchName={batchName}
        setBatchName={setBatchName}
        batchDescription={batchDescription}
        setBatchDescription={setBatchDescription}
        selectedFormat={selectedFormat}
        setSelectedFormat={setSelectedFormat}
        selectedTemplate={selectedTemplate}
        setSelectedTemplate={setSelectedTemplate}
        selectedJobs={selectedJobs}
        setSelectedJobs={setSelectedJobs}
        exportFormats={exportFormats}
        templates={templates}
        customConfig={customConfig}
        setCustomConfig={setCustomConfig}
        loading={loading}
      />

      {/* Template Creation Dialog */}
      <TemplateDialog
        open={templateDialogOpen}
        onClose={() => setTemplateDialogOpen(false)}
        onConfirm={handleCreateTemplate}
        templateData={templateFormData}
        setTemplateData={setTemplateFormData}
        exportFormats={exportFormats}
        loading={loading}
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert
          severity={notification.severity}
          onClose={() => setNotification({ ...notification, open: false })}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Dialog>
  );
};

// Export Configuration Panel Component
const ExportConfigurationPanel = ({ format, formatConfig, config, onChange }) => {
  if (!formatConfig) return null;

  const handleConfigChange = (key, value) => {
    onChange({
      ...config,
      [key]: value
    });
  };

  const renderConfigOption = (key, defaultValue, type = 'text') => {
    const currentValue = config[key] !== undefined ? config[key] : defaultValue;

    switch (type) {
      case 'boolean':
        return (
          <FormControlLabel
            control={
              <Switch
                checked={currentValue}
                onChange={(e) => handleConfigChange(key, e.target.checked)}
              />
            }
            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          />
        );
      
      case 'number':
        return (
          <TextField
            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            type="number"
            value={currentValue}
            onChange={(e) => handleConfigChange(key, parseInt(e.target.value))}
            size="small"
            sx={{ minWidth: 120 }}
          />
        );
      
      case 'slider':
        return (
          <Box>
            <Typography gutterBottom>
              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Typography>
            <Slider
              value={currentValue}
              onChange={(e, value) => handleConfigChange(key, value)}
              min={0.5}
              max={3.0}
              step={0.1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        );
      
      default:
        return (
          <TextField
            label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            value={currentValue}
            onChange={(e) => handleConfigChange(key, e.target.value)}
            size="small"
            sx={{ minWidth: 120 }}
          />
        );
    }
  };

  return (
    <Accordion sx={{ mt: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">
          Export Configuration
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          {Object.entries(formatConfig.default_config).map(([key, defaultValue]) => (
            <Grid item xs={12} sm={6} md={4} key={key}>
              {renderConfigOption(
                key,
                defaultValue,
                typeof defaultValue === 'boolean' ? 'boolean' :
                typeof defaultValue === 'number' ? 'number' :
                key.includes('spacing') || key.includes('size') ? 'slider' : 'text'
              )}
            </Grid>
          ))}
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
};

// Export Jobs List Component
const ExportJobsList = ({ jobs, onDownload, onRefresh }) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Active Exports
        </Typography>
        <IconButton onClick={onRefresh} size="small">
          <RefreshIcon />
        </IconButton>
      </Box>
      
      {jobs.length === 0 ? (
        <Typography color="textSecondary" align="center" sx={{ py: 2 }}>
          No active export jobs
        </Typography>
      ) : (
        <List dense>
          {jobs.slice(0, 5).map((job) => (
            <ListItem key={job.id} divider>
              <ListItemIcon>
                {getStatusIcon(job.status)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">
                      {job.format.toUpperCase()}
                    </Typography>
                    <Chip
                      size="small"
                      label={job.status}
                      color={getStatusColor(job.status)}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <LinearProgress
                      variant="determinate"
                      value={job.progress_percentage}
                      sx={{ mt: 0.5, mb: 0.5 }}
                    />
                    <Typography variant="caption">
                      {job.progress_percentage.toFixed(1)}%
                    </Typography>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                {job.status === 'completed' && (
                  <IconButton
                    onClick={() => onDownload(job)}
                    size="small"
                    color="primary"
                  >
                    <GetAppIcon />
                  </IconButton>
                )}
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}
    </CardContent>
  </Card>
);

// Additional helper components would continue here...
// (BatchExportsList, TemplatesList, ExportHistoryTable, etc.)

export default MultiFormatExportSystem;