/**
 * T022: Multi-Format Export System - Batch Export Component
 * 
 * Component for exporting multiple transcripts in batch with
 * format selection and progress tracking.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Divider,
  IconButton,
  Collapse
} from '@mui/material';
import {
  Download as DownloadIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Archive as ArchiveIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';

import transcriptExportService, { EXPORT_FORMATS } from '../services/transcriptExportService';

const BatchExportDialog = ({
  open,
  onClose,
  selectedJobs,
  onExportComplete
}) => {
  // State management
  const [selectedFormat, setSelectedFormat] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [zipFilename, setZipFilename] = useState('');
  const [availableFormats, setAvailableFormats] = useState([]);
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exportProgress, setExportProgress] = useState(null);
  const [error, setError] = useState('');
  const [expandedJobs, setExpandedJobs] = useState(false);
  const [exportResult, setExportResult] = useState(null);

  // Load data on mount
  useEffect(() => {
    if (open) {
      loadFormatsAndTemplates();
      generateDefaultFilename();
    }
  }, [open]);

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setSelectedFormat('');
      setSelectedTemplate('');
      setError('');
      setExportProgress(null);
      setExportResult(null);
    }
  }, [open, selectedJobs]);

  const loadFormatsAndTemplates = async () => {
    try {
      const [formatsData, templatesData] = await Promise.all([
        transcriptExportService.getAvailableFormats(),
        transcriptExportService.getExportTemplates()
      ]);
      
      setAvailableFormats(formatsData.filter(f => transcriptExportService.isFormatAvailable(f)));
      setAvailableTemplates(templatesData);
    } catch (error) {
      setError('Failed to load export options');
      console.error('Error loading export data:', error);
    }
  };

  const generateDefaultFilename = () => {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    setZipFilename(`batch_export_${timestamp}.zip`);
  };

  const handleFormatChange = async (format) => {
    setSelectedFormat(format);
    setSelectedTemplate('');
    
    // Load templates for selected format
    try {
      const templates = await transcriptExportService.getExportTemplates(format);
      const formatTemplates = templates.filter(t => t.format === format);
      
      // Auto-select first template
      if (formatTemplates.length > 0) {
        setSelectedTemplate(formatTemplates[0].name);
      }
    } catch (error) {
      console.error('Error loading templates for format:', error);
    }
  };

  const handleBatchExport = async () => {
    if (!selectedFormat || selectedJobs.length === 0) return;
    
    setLoading(true);
    setError('');
    setExportProgress({ current: 0, total: selectedJobs.length });
    
    try {
      const jobIds = selectedJobs.map(job => job.id);
      
      const result = await transcriptExportService.batchExport(jobIds, selectedFormat, {
        template: selectedTemplate,
        zipFilename: zipFilename
      });
      
      setExportResult(result);
      setExportProgress({ current: result.successful_exports, total: result.total_jobs });
      
      if (onExportComplete) {
        onExportComplete(result);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotalSize = () => {
    return selectedJobs.reduce((total, job) => {
      // Rough estimation based on transcript content length
      const contentLength = job.transcript_content?.length || 0;
      let multiplier = 1;
      
      // Different formats have different size multipliers
      switch (selectedFormat) {
        case 'docx':
        case 'pdf':
          multiplier = 2.5;
          break;
        case 'json':
          multiplier = 1.8;
          break;
        case 'srt':
        case 'vtt':
          multiplier = 1.2;
          break;
        default:
          multiplier = 1;
      }
      
      return total + (contentLength * multiplier);
    }, 0);
  };

  const getFormatTemplates = () => {
    return availableTemplates.filter(t => t.format === selectedFormat);
  };

  const renderJobsList = () => (
    <Card variant="outlined">
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">
            Selected Jobs ({selectedJobs.length})
          </Typography>
          <IconButton onClick={() => setExpandedJobs(!expandedJobs)}>
            {expandedJobs ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
        
        <Collapse in={expandedJobs}>
          <List dense sx={{ mt: 1 }}>
            {selectedJobs.map((job, index) => (
              <ListItem key={job.id}>
                <ListItemIcon>
                  <DescriptionIcon />
                </ListItemIcon>
                <ListItemText
                  primary={job.original_filename}
                  secondary={`Job ID: ${job.id} | Status: ${job.status}`}
                />
                <Chip
                  label={job.status}
                  size="small"
                  color={job.status === 'completed' ? 'success' : 'default'}
                />
              </ListItem>
            ))}
          </List>
        </Collapse>
        
        <Box display="flex" gap={1} mt={2}>
          <Chip label={`${selectedJobs.length} jobs`} />
          {selectedFormat && (
            <Chip 
              label={`Est. ${transcriptExportService.formatFileSize(calculateTotalSize())}`}
              variant="outlined"
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const renderFormatSelection = () => (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <FormControl fullWidth>
          <InputLabel>Export Format</InputLabel>
          <Select
            value={selectedFormat}
            onChange={(e) => handleFormatChange(e.target.value)}
            label="Export Format"
          >
            {availableFormats.map((format) => (
              <MenuItem key={format.format} value={format.format}>
                <Box display="flex" alignItems="center" gap={1}>
                  <span>{transcriptExportService.getFormatIcon(format.format)}</span>
                  <Box>
                    <Typography variant="body1">{format.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {format.description}
                    </Typography>
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>
      
      {selectedFormat && (
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Template</InputLabel>
            <Select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              label="Template"
            >
              {getFormatTemplates().map((template) => (
                <MenuItem key={template.name} value={template.name}>
                  <Box>
                    <Typography variant="body1">{template.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {template.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      )}
      
      <Grid item xs={12}>
        <TextField
          fullWidth
          label="ZIP Archive Name"
          value={zipFilename}
          onChange={(e) => setZipFilename(e.target.value)}
          placeholder="batch_export.zip"
          helperText="Name for the ZIP file containing all exports"
        />
      </Grid>
    </Grid>
  );

  const renderProgress = () => {
    if (!exportProgress && !exportResult) return null;
    
    return (
      <Card variant="outlined" sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {loading ? 'Export Progress' : 'Export Complete'}
          </Typography>
          
          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }} align="center">
                Processing exports... {exportProgress?.current || 0} of {exportProgress?.total || 0}
              </Typography>
            </Box>
          )}
          
          {exportResult && (
            <Box>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <CheckCircleIcon color="success" />
                    <Typography variant="h6" color="success.main">
                      {exportResult.successful_exports}
                    </Typography>
                    <Typography variant="caption">Successful</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <ErrorIcon color="error" />
                    <Typography variant="h6" color="error.main">
                      {exportResult.failed_exports}
                    </Typography>
                    <Typography variant="caption">Failed</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <ArchiveIcon color="primary" />
                    <Typography variant="h6">
                      {transcriptExportService.formatFileSize(exportResult.zip_size)}
                    </Typography>
                    <Typography variant="caption">Archive Size</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <DescriptionIcon />
                    <Typography variant="h6">
                      {exportResult.total_jobs}
                    </Typography>
                    <Typography variant="caption">Total Jobs</Typography>
                  </Box>
                </Grid>
              </Grid>
              
              {exportResult.successful_exports > 0 && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    Batch export completed successfully! 
                    {exportResult.failed_exports > 0 && 
                      ` ${exportResult.failed_exports} job(s) failed to export.`
                    }
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<DownloadIcon />}
                    sx={{ mt: 1 }}
                    onClick={() => {
                      // In a real implementation, this would trigger the ZIP download
                      window.open(exportResult.download_url, '_blank');
                    }}
                  >
                    Download ZIP Archive
                  </Button>
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  const canExport = selectedFormat && selectedTemplate && selectedJobs.length > 0 && !loading;
  const completedJobs = selectedJobs.filter(job => job.status === 'completed');
  const hasInvalidJobs = completedJobs.length < selectedJobs.length;

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Batch Export Transcripts</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {hasInvalidJobs && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            Only completed jobs can be exported. {completedJobs.length} of {selectedJobs.length} jobs are ready for export.
          </Alert>
        )}
        
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {renderJobsList()}
          </Grid>
          
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Export Settings
            </Typography>
            {renderFormatSelection()}
          </Grid>
          
          <Grid item xs={12}>
            {renderProgress()}
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          {exportResult ? 'Close' : 'Cancel'}
        </Button>
        {!exportResult && (
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <ArchiveIcon />}
            onClick={handleBatchExport}
            disabled={!canExport}
          >
            {loading ? 'Creating Archive...' : `Export ${completedJobs.length} Jobs`}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default BatchExportDialog;