import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Switch,
  Slider,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  LinearProgress,
  Chip,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
  Paper,
  Divider
} from '@mui/material';
import {
  CloudUpload,
  AudioFile,
  Settings,
  Analytics,
  Download,
  PlayArrow,
  Stop,
  ExpandMore,
  Info,
  TuneRounded,
  GraphicEq,
  VolumeUp,
  CleaningServices
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

import audioProcessingService from '../services/audioProcessingService';

const AudioProcessingSystem = () => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileAnalysis, setFileAnalysis] = useState(null);
  const [processingConfig, setProcessingConfig] = useState(null);
  const [recommendedConfig, setRecommendedConfig] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingResult, setProcessingResult] = useState(null);
  const [configOptions, setConfigOptions] = useState(null);
  const [customConfig, setCustomConfig] = useState({
    enable_noise_reduction: true,
    noise_reduction_method: 'spectral_gating',
    noise_reduction_strength: 0.5,
    enable_normalization: true,
    enable_compression: true,
    enable_eq: false,
    high_pass_cutoff: 80.0,
    low_pass_cutoff: 8000.0,
    target_sample_rate: 16000,
    target_channels: 1,
    quality_level: 'medium',
    preserve_dynamics: true
  });

  // Load configuration options on mount
  useEffect(() => {
    loadConfigOptions();
  }, []);

  const loadConfigOptions = async () => {
    try {
      const config = await audioProcessingService.getProcessingConfig();
      setConfigOptions(config);
      setCustomConfig(config.default_config);
    } catch (error) {
      console.error('Failed to load config options:', error);
    }
  };

  // File upload handling
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
      setFileAnalysis(null);
      setProcessingResult(null);
      await analyzeFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac', '.opus']
    },
    maxFiles: 1
  });

  const analyzeFile = async (file) => {
    setIsAnalyzing(true);
    try {
      const analysis = await audioProcessingService.analyzeAudio(file);
      setFileAnalysis(analysis);

      // Get recommendations
      const recommendations = await audioProcessingService.getProcessingRecommendations(file);
      setRecommendedConfig(recommendations.recommended_config);
    } catch (error) {
      console.error('Failed to analyze file:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const processAudioFile = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    try {
      const result = await audioProcessingService.processAudio(selectedFile, customConfig);
      setProcessingResult(result);
    } catch (error) {
      console.error('Failed to process audio:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const applyRecommendedConfig = () => {
    if (recommendedConfig) {
      setCustomConfig(recommendedConfig);
    }
  };

  const resetToDefaultConfig = () => {
    if (configOptions?.default_config) {
      setCustomConfig(configOptions.default_config);
    }
  };

  // Render quality score with color coding
  const renderQualityScore = (score) => {
    const getColor = (score) => {
      if (score >= 0.8) return 'success';
      if (score >= 0.6) return 'info';
      if (score >= 0.4) return 'warning';
      return 'error';
    };

    const getLabel = (score) => {
      if (score >= 0.8) return 'Excellent';
      if (score >= 0.6) return 'Good';
      if (score >= 0.4) return 'Fair';
      return 'Poor';
    };

    return (
      <Chip
        label={`${getLabel(score)} (${(score * 100).toFixed(1)}%)`}
        color={getColor(score)}
        variant="filled"
      />
    );
  };

  // File Upload Tab
  const FileUploadTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <AudioFile sx={{ mr: 1, verticalAlign: 'middle' }} />
          Audio File Upload & Analysis
        </Typography>

        {/* File Drop Zone */}
        <Paper
          {...getRootProps()}
          sx={{
            p: 4,
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            backgroundColor: isDragActive ? 'action.hover' : 'background.default',
            cursor: 'pointer',
            textAlign: 'center',
            mb: 3
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'grey.500', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop the audio file here' : 'Drag & drop an audio file here'}
          </Typography>
          <Typography color="textSecondary">
            or click to select a file
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Supported formats: WAV, MP3, FLAC, M4A, OGG, AAC, OPUS
          </Typography>
        </Paper>

        {/* Selected File Info */}
        {selectedFile && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Selected File:</Typography>
            <Typography variant="body2">
              {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </Typography>
          </Alert>
        )}

        {/* Analysis Progress */}
        {isAnalyzing && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Analyzing audio quality...
            </Typography>
            <LinearProgress />
          </Box>
        )}

        {/* Analysis Results */}
        {fileAnalysis && (
          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Analytics sx={{ mr: 1, verticalAlign: 'middle' }} />
                Audio Analysis Results
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Basic Properties</Typography>
                  <Typography variant="body2">Duration: {fileAnalysis.duration.toFixed(2)}s</Typography>
                  <Typography variant="body2">Sample Rate: {fileAnalysis.sample_rate} Hz</Typography>
                  <Typography variant="body2">Channels: {fileAnalysis.channels}</Typography>
                  <Typography variant="body2">Format: {fileAnalysis.format}</Typography>
                  {fileAnalysis.bitrate && (
                    <Typography variant="body2">Bitrate: {fileAnalysis.bitrate} bps</Typography>
                  )}
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Quality Metrics</Typography>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">Overall Quality:</Typography>
                    {renderQualityScore(fileAnalysis.quality_score)}
                  </Box>
                  <Typography variant="body2">
                    SNR Estimate: {fileAnalysis.snr_estimate.toFixed(1)} dB
                  </Typography>
                  <Typography variant="body2">
                    Peak Level: {(fileAnalysis.peak_level * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    Dynamic Range: {fileAnalysis.dynamic_range.toFixed(3)}
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2">Recommendations</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {fileAnalysis.recommended_noise_reduction && (
                      <Chip label="Noise Reduction Recommended" color="warning" size="small" />
                    )}
                    {fileAnalysis.recommended_normalization && (
                      <Chip label="Normalization Recommended" color="info" size="small" />
                    )}
                    {!fileAnalysis.recommended_noise_reduction && !fileAnalysis.recommended_normalization && (
                      <Chip label="Good Quality - Minimal Processing Needed" color="success" size="small" />
                    )}
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );

  // Processing Configuration Tab
  const ProcessingConfigTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <TuneRounded sx={{ mr: 1, verticalAlign: 'middle' }} />
          Processing Configuration
        </Typography>

        {/* Quick Actions */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button 
            variant="outlined" 
            onClick={applyRecommendedConfig}
            disabled={!recommendedConfig}
          >
            Apply Recommended Settings
          </Button>
          <Button variant="outlined" onClick={resetToDefaultConfig}>
            Reset to Defaults
          </Button>
        </Box>

        {/* Noise Reduction Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle1">
              <CleaningServices sx={{ mr: 1, verticalAlign: 'middle' }} />
              Noise Reduction
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={customConfig.enable_noise_reduction}
                      onChange={(e) => setCustomConfig({
                        ...customConfig,
                        enable_noise_reduction: e.target.checked
                      })}
                    />
                  }
                  label="Enable Noise Reduction"
                />
              </Grid>

              {customConfig.enable_noise_reduction && (
                <>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Noise Reduction Method</InputLabel>
                      <Select
                        value={customConfig.noise_reduction_method}
                        onChange={(e) => setCustomConfig({
                          ...customConfig,
                          noise_reduction_method: e.target.value
                        })}
                      >
                        {configOptions?.noise_reduction_methods?.map((method) => (
                          <MenuItem key={method} value={method}>
                            {method.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>
                      Noise Reduction Strength: {customConfig.noise_reduction_strength.toFixed(2)}
                    </Typography>
                    <Slider
                      value={customConfig.noise_reduction_strength}
                      onChange={(e, value) => setCustomConfig({
                        ...customConfig,
                        noise_reduction_strength: value
                      })}
                      min={0}
                      max={1}
                      step={0.1}
                      marks={[
                        { value: 0, label: 'Mild' },
                        { value: 0.5, label: 'Medium' },
                        { value: 1, label: 'Strong' }
                      ]}
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Audio Enhancement Settings */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle1">
              <VolumeUp sx={{ mr: 1, verticalAlign: 'middle' }} />
              Audio Enhancement
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={customConfig.enable_normalization}
                      onChange={(e) => setCustomConfig({
                        ...customConfig,
                        enable_normalization: e.target.checked
                      })}
                    />
                  }
                  label="Normalization"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={customConfig.enable_compression}
                      onChange={(e) => setCustomConfig({
                        ...customConfig,
                        enable_compression: e.target.checked
                      })}
                    />
                  }
                  label="Compression"
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={customConfig.preserve_dynamics}
                      onChange={(e) => setCustomConfig({
                        ...customConfig,
                        preserve_dynamics: e.target.checked
                      })}
                    />
                  }
                  label="Preserve Dynamics"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* EQ Settings */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle1">
              <GraphicEq sx={{ mr: 1, verticalAlign: 'middle' }} />
              Equalization & Filtering
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={customConfig.enable_eq}
                      onChange={(e) => setCustomConfig({
                        ...customConfig,
                        enable_eq: e.target.checked
                      })}
                    />
                  }
                  label="Enable EQ Processing"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography gutterBottom>
                  High-Pass Filter: {customConfig.high_pass_cutoff} Hz
                </Typography>
                <Slider
                  value={customConfig.high_pass_cutoff}
                  onChange={(e, value) => setCustomConfig({
                    ...customConfig,
                    high_pass_cutoff: value
                  })}
                  min={20}
                  max={200}
                  step={10}
                  marks={[
                    { value: 20, label: '20Hz' },
                    { value: 80, label: '80Hz' },
                    { value: 200, label: '200Hz' }
                  ]}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography gutterBottom>
                  Low-Pass Filter: {customConfig.low_pass_cutoff} Hz
                </Typography>
                <Slider
                  value={customConfig.low_pass_cutoff}
                  onChange={(e, value) => setCustomConfig({
                    ...customConfig,
                    low_pass_cutoff: value
                  })}
                  min={4000}
                  max={20000}
                  step={500}
                  marks={[
                    { value: 4000, label: '4kHz' },
                    { value: 8000, label: '8kHz' },
                    { value: 20000, label: '20kHz' }
                  ]}
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Output Settings */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle1">
              <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
              Output Settings
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Sample Rate</InputLabel>
                  <Select
                    value={customConfig.target_sample_rate}
                    onChange={(e) => setCustomConfig({
                      ...customConfig,
                      target_sample_rate: e.target.value
                    })}
                  >
                    <MenuItem value={8000}>8 kHz</MenuItem>
                    <MenuItem value={16000}>16 kHz (Recommended)</MenuItem>
                    <MenuItem value={22050}>22.05 kHz</MenuItem>
                    <MenuItem value={44100}>44.1 kHz</MenuItem>
                    <MenuItem value={48000}>48 kHz</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Channels</InputLabel>
                  <Select
                    value={customConfig.target_channels}
                    onChange={(e) => setCustomConfig({
                      ...customConfig,
                      target_channels: e.target.value
                    })}
                  >
                    <MenuItem value={1}>Mono (Recommended)</MenuItem>
                    <MenuItem value={2}>Stereo</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Quality Level</InputLabel>
                  <Select
                    value={customConfig.quality_level}
                    onChange={(e) => setCustomConfig({
                      ...customConfig,
                      quality_level: e.target.value
                    })}
                  >
                    {configOptions?.quality_levels?.map((level) => (
                      <MenuItem key={level} value={level}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Process Button */}
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={processAudioFile}
            disabled={!selectedFile || isProcessing}
            startIcon={isProcessing ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            {isProcessing ? 'Processing Audio...' : 'Process Audio'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  // Processing Results Tab
  const ProcessingResultsTab = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          <Analytics sx={{ mr: 1, verticalAlign: 'middle' }} />
          Processing Results
        </Typography>

        {!processingResult ? (
          <Alert severity="info">
            No processing results yet. Upload and process an audio file to see results.
          </Alert>
        ) : (
          <>
            {/* Processing Summary */}
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Processing Summary</Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2">
                      Processing Time: {processingResult.processing_time.toFixed(2)}s
                    </Typography>
                    <Typography variant="body2">
                      Original Size: {(processingResult.file_size_original / 1024 / 1024).toFixed(2)} MB
                    </Typography>
                    <Typography variant="body2">
                      Processed Size: {(processingResult.file_size_processed / 1024 / 1024).toFixed(2)} MB
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2">
                      Size Change: {processingResult.improvements.size_change_percent > 0 ? '+' : ''}
                      {processingResult.improvements.size_change_percent.toFixed(1)}%
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">Quality Score:</Typography>
                      {renderQualityScore(processingResult.analysis.quality_score)}
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Applied Improvements */}
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Applied Improvements</Typography>
                
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {processingResult.improvements.noise_reduction_applied && (
                    <Chip label="Noise Reduction" color="primary" size="small" />
                  )}
                  {processingResult.improvements.normalization_applied && (
                    <Chip label="Normalization" color="primary" size="small" />
                  )}
                  {processingResult.improvements.compression_applied && (
                    <Chip label="Compression" color="primary" size="small" />
                  )}
                  {processingResult.improvements.eq_applied && (
                    <Chip label="EQ Processing" color="primary" size="small" />
                  )}
                </Box>
              </CardContent>
            </Card>

            {/* Download Section */}
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>Download Processed Audio</Typography>
                
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    The processed audio is optimized for transcription with improved signal quality.
                  </Typography>
                </Alert>

                <Button
                  variant="contained"
                  startIcon={<Download />}
                  onClick={() => {
                    // In a real implementation, this would trigger the download
                    alert('Download functionality would be implemented here');
                  }}
                  disabled={!processingResult.download_url}
                >
                  Download Processed Audio
                </Button>
              </CardContent>
            </Card>
          </>
        )}
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Audio Processing System
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Enhance audio quality for improved transcription accuracy with noise reduction, 
        normalization, and format optimization.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Upload & Analysis" />
          <Tab label="Processing Configuration" />
          <Tab label="Results" />
        </Tabs>
      </Box>

      {activeTab === 0 && <FileUploadTab />}
      {activeTab === 1 && <ProcessingConfigTab />}
      {activeTab === 2 && <ProcessingResultsTab />}
    </Box>
  );
};

export default AudioProcessingSystem;