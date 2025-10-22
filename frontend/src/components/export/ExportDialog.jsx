/**
 * T022: Multi-Format Export System - Export Dialog Component
 * 
 * Modal dialog for selecting export format, template, and options
 * for transcript export functionality.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Paper,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Preview as PreviewIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
  Info as InfoIcon
} from '@mui/icons-material';

import transcriptExportService, { EXPORT_FORMATS } from '../services/transcriptExportService';

const ExportDialog = ({
  open,
  onClose,
  jobId,
  jobFilename,
  onExportComplete
}) => {
  // State management
  const [selectedFormat, setSelectedFormat] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [customFilename, setCustomFilename] = useState('');
  const [availableFormats, setAvailableFormats] = useState([]);
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [exportOptions, setExportOptions] = useState({});
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [exportStats, setExportStats] = useState(null);

  // Load data on mount
  useEffect(() => {
    if (open) {
      loadFormatsAndTemplates();
      loadExportStats();
    }
  }, [open]);

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setSelectedFormat('');
      setSelectedTemplate('');
      setCustomFilename('');
      setExportOptions({});
      setPreview(null);
      setError('');
      setActiveTab(0);
    }
  }, [open, jobId]);

  const loadFormatsAndTemplates = async () => {
    try {
      const [formatsData, templatesData] = await Promise.all([
        transcriptExportService.getAvailableFormats(),
        transcriptExportService.getExportTemplates()
      ]);
      
      setAvailableFormats(formatsData);
      setAvailableTemplates(templatesData);
    } catch (error) {
      setError('Failed to load export options');
      console.error('Error loading export data:', error);
    }
  };

  const loadExportStats = async () => {
    try {
      const stats = await transcriptExportService.getExportStats();
      setExportStats(stats);
    } catch (error) {
      console.error('Error loading export stats:', error);
    }
  };

  const handleFormatChange = async (format) => {
    setSelectedFormat(format);
    setSelectedTemplate('');
    setPreview(null);
    
    // Load templates for selected format
    try {
      const templates = await transcriptExportService.getExportTemplates(format);
      setAvailableTemplates(templates);
      
      // Auto-select first template
      if (templates.length > 0) {
        setSelectedTemplate(templates[0].name);
      }
    } catch (error) {
      console.error('Error loading templates for format:', error);
    }
  };

  const handleTemplateChange = (template) => {
    setSelectedTemplate(template);
    setPreview(null);
  };

  const generatePreview = async () => {
    if (!selectedFormat || !jobId) return;
    
    setPreviewLoading(true);
    try {
      const previewData = await transcriptExportService.previewExport(jobId, selectedFormat, {
        template: selectedTemplate,
        previewLines: 10
      });
      setPreview(previewData);
      setError('');
    } catch (error) {
      setError(error.message);
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExport = async () => {
    if (!selectedFormat || !jobId) return;
    
    const validation = transcriptExportService.validateExportOptions(selectedFormat, {
      filename: customFilename,
      customOptions: exportOptions
    });
    
    if (!validation.isValid) {
      setError(validation.errors.join(', '));
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await transcriptExportService.downloadExport(jobId, selectedFormat, {
        template: selectedTemplate,
        filename: customFilename,
        customOptions: exportOptions
      });
      
      if (onExportComplete) {
        onExportComplete(selectedFormat, selectedTemplate);
      }
      
      onClose();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getFormatInfo = (formatId) => {
    return availableFormats.find(f => f.format === formatId) || {};
  };

  const getTemplateInfo = (templateName) => {
    return availableTemplates.find(t => t.name === templateName) || {};
  };

  const generateSuggestedFilename = () => {
    if (!selectedFormat || !jobFilename) return '';
    return transcriptExportService.generateFilename(jobFilename, selectedFormat);
  };

  const renderFormatSelection = () => (
    <Grid container spacing={2}>
      {Object.entries(EXPORT_FORMATS).map(([key, format]) => {
        const formatInfo = getFormatInfo(format.id);
        const isAvailable = transcriptExportService.isFormatAvailable(formatInfo);
        
        return (
          <Grid item xs={12} sm={6} md={4} key={key}>
            <Card 
              elevation={selectedFormat === format.id ? 3 : 1}
              sx={{
                border: selectedFormat === format.id ? 2 : 0,
                borderColor: selectedFormat === format.id ? 'primary.main' : 'transparent',
                opacity: isAvailable ? 1 : 0.6
              }}
            >
              <CardActionArea
                onClick={() => isAvailable && handleFormatChange(format.id)}
                disabled={!isAvailable}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Typography variant="h6" sx={{ mr: 1 }}>
                      {transcriptExportService.getFormatIcon(format.id)}
                    </Typography>
                    <Typography variant="h6" component="div">
                      {format.name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {format.description}
                  </Typography>
                  {!isAvailable && formatInfo.requires && (
                    <Chip 
                      label="Requires additional dependencies" 
                      size="small" 
                      color="warning"
                      sx={{ mt: 1 }}
                    />
                  )}
                  {isAvailable && (
                    <Chip 
                      label="Available" 
                      size="small" 
                      color="success" 
                      sx={{ mt: 1 }}
                    />
                  )}
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );

  const renderTemplateSelection = () => {
    const formatTemplates = availableTemplates.filter(t => t.format === selectedFormat);
    
    if (formatTemplates.length === 0) {
      return (
        <Alert severity="info">
          No templates available for selected format
        </Alert>
      );
    }
    
    return (
      <FormControl fullWidth>
        <InputLabel>Template</InputLabel>
        <Select
          value={selectedTemplate}
          onChange={(e) => handleTemplateChange(e.target.value)}
          label="Template"
        >
          {formatTemplates.map((template) => (
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
    );
  };

  const renderAdvancedOptions = () => {
    const templateInfo = getTemplateInfo(selectedTemplate);
    
    return (
      <Box sx={{ mt: 2 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Advanced Options</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Custom Filename"
                  value={customFilename}
                  onChange={(e) => setCustomFilename(e.target.value)}
                  placeholder={generateSuggestedFilename()}
                  helperText="Leave empty to use auto-generated filename"
                />
              </Grid>
              
              {templateInfo.include_timestamps && (
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Timestamp Format</InputLabel>
                    <Select
                      value={exportOptions.timestamp_format || 'HH:MM:SS'}
                      onChange={(e) => setExportOptions({
                        ...exportOptions,
                        timestamp_format: e.target.value
                      })}
                      label="Timestamp Format"
                    >
                      <MenuItem value="HH:MM:SS">HH:MM:SS</MenuItem>
                      <MenuItem value="HH:MM:SS.mmm">HH:MM:SS.mmm</MenuItem>
                      <MenuItem value="seconds">Seconds</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              )}
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Font Size"
                  value={exportOptions.font_size || 12}
                  onChange={(e) => setExportOptions({
                    ...exportOptions,
                    font_size: parseInt(e.target.value)
                  })}
                  inputProps={{ min: 8, max: 24 }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Font Family"
                  value={exportOptions.font_family || 'Arial'}
                  onChange={(e) => setExportOptions({
                    ...exportOptions,
                    font_family: e.target.value
                  })}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Line Spacing"
                  value={exportOptions.line_spacing || 1.5}
                  onChange={(e) => setExportOptions({
                    ...exportOptions,
                    line_spacing: parseFloat(e.target.value)
                  })}
                  inputProps={{ min: 1.0, max: 3.0, step: 0.1 }}
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  const renderPreview = () => (
    <Paper sx={{ p: 2, mt: 2, backgroundColor: 'grey.50' }}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">Preview</Typography>
        <Button
          size="small"
          startIcon={<PreviewIcon />}
          onClick={generatePreview}
          disabled={!selectedFormat || previewLoading}
        >
          {previewLoading ? <CircularProgress size={20} /> : 'Generate Preview'}
        </Button>
      </Box>
      
      {preview ? (
        <Box>
          <Typography variant="body2" gutterBottom>
            Format: <strong>{preview.format.toUpperCase()}</strong> | 
            Lines shown: <strong>{preview.lines_shown}</strong> | 
            Estimated size: <strong>{transcriptExportService.formatFileSize(preview.total_estimated_size)}</strong>
          </Typography>
          <Paper 
            sx={{ 
              p: 1, 
              mt: 1, 
              backgroundColor: 'white',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              maxHeight: 300,
              overflow: 'auto'
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {preview.preview}
            </pre>
          </Paper>
        </Box>
      ) : (
        <Alert severity="info">
          Click "Generate Preview" to see how your export will look
        </Alert>
      )}
    </Paper>
  );

  const renderStats = () => {
    if (!exportStats) return null;
    
    return (
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Export Statistics</Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Typography variant="body2" color="text.secondary">Available Jobs</Typography>
            <Typography variant="h5">{exportStats.available_jobs}</Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="body2" color="text.secondary">Formats</Typography>
            <Typography variant="h5">{exportStats.available_formats}</Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="body2" color="text.secondary">Templates</Typography>
            <Typography variant="h5">{exportStats.available_templates}</Typography>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Typography variant="body2" color="text.secondary">Batch Limit</Typography>
            <Typography variant="h5">{exportStats.batch_limit}</Typography>
          </Grid>
        </Grid>
      </Paper>
    );
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Export Transcript</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        {jobFilename && (
          <Typography variant="body2" color="text.secondary">
            {jobFilename}
          </Typography>
        )}
      </DialogTitle>
      
      <DialogContent dividers>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ mb: 3 }}
        >
          <Tab label="Format" />
          <Tab label="Template & Options" disabled={!selectedFormat} />
          <Tab label="Preview" disabled={!selectedFormat} />
          <Tab label="Stats" />
        </Tabs>
        
        {activeTab === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Select Export Format
            </Typography>
            {renderFormatSelection()}
          </Box>
        )}
        
        {activeTab === 1 && selectedFormat && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Template & Options
            </Typography>
            {renderTemplateSelection()}
            {renderAdvancedOptions()}
          </Box>
        )}
        
        {activeTab === 2 && selectedFormat && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Export Preview
            </Typography>
            {renderPreview()}
          </Box>
        )}
        
        {activeTab === 3 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Export Statistics
            </Typography>
            {renderStats()}
          </Box>
        )}
      </DialogContent>
      
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
          onClick={handleExport}
          disabled={!selectedFormat || loading}
        >
          {loading ? 'Exporting...' : 'Export & Download'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExportDialog;