/**
 * T020: Batch Upload Dialog Component
 * Modal dialog for batch file upload with drag-and-drop support
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  IconButton,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Divider
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Error as ErrorIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';

import batchUploadService, { BatchUploadConfig, BATCH_STATUS } from '../services/batchUploadService';

const BatchUploadDialog = ({ 
  open, 
  onClose, 
  onSuccess 
}) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [batchId, setBatchId] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [config, setConfig] = useState(new BatchUploadConfig());
  
  const fileInputRef = useRef(null);

  // Handle file selection
  const handleFileSelect = useCallback((selectedFiles) => {
    const fileArray = Array.from(selectedFiles);
    
    // Validate files
    try {
      const newConfig = new BatchUploadConfig({
        ...config,
        maxFiles: Math.max(config.maxFiles, files.length + fileArray.length)
      });
      
      batchUploadService.validateFiles([...files, ...fileArray], newConfig);
      
      // Add files with metadata
      const filesWithMetadata = fileArray.map(file => ({
        file,
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'ready'
      }));
      
      setFiles(prev => [...prev, ...filesWithMetadata]);
      setError(null);
      
    } catch (error) {
      setError(error.message);
    }
  }, [files, config]);

  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles);
    }
  }, [handleFileSelect]);

  // File input handler
  const handleFileInputChange = (e) => {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
  };

  // Remove file
  const handleRemoveFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Clear all files
  const handleClearFiles = () => {
    setFiles([]);
    setError(null);
  };

  // Configuration handlers
  const handleConfigChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Start batch upload
  const handleStartUpload = async () => {
    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      // Extract files from metadata objects
      const fileList = files.map(f => f.file);
      
      // Create batch upload
      const newBatchId = await batchUploadService.createBatchUpload(fileList, config);
      setBatchId(newBatchId);

      // Start processing
      await batchUploadService.startBatchProcessing(newBatchId);

      // Set up progress monitoring
      const stopPolling = batchUploadService.startProgressPolling(newBatchId, 1000);
      
      batchUploadService.onProgress(newBatchId, (progress) => {
        setUploadProgress(progress.progress);
        
        // Update file statuses
        setFiles(prev => prev.map(file => {
          const job = progress.jobs.find(j => j.filename === file.name);
          if (job) {
            return { ...file, status: job.status };
          }
          return file;
        }));

        // Handle completion
        if (progress.status === BATCH_STATUS.COMPLETED) {
          stopPolling();
          setUploading(false);
          
          if (onSuccess) {
            onSuccess(newBatchId, progress);
          }
          
          // Auto-close after successful upload
          setTimeout(() => {
            handleClose();
          }, 2000);
        } else if (progress.status === BATCH_STATUS.FAILED) {
          stopPolling();
          setUploading(false);
          setError('Batch upload failed. Please try again.');
        }
      });

    } catch (error) {
      console.error('Upload error:', error);
      setError(error.message);
      setUploading(false);
    }
  };

  // Cancel upload
  const handleCancelUpload = async () => {
    if (batchId) {
      try {
        await batchUploadService.cancelBatchUpload(batchId);
        setUploading(false);
        setBatchId(null);
        setUploadProgress(0);
      } catch (error) {
        console.error('Cancel error:', error);
        setError('Failed to cancel upload');
      }
    }
  };

  // Close dialog
  const handleClose = () => {
    if (!uploading) {
      setFiles([]);
      setError(null);
      setUploadProgress(0);
      setBatchId(null);
      onClose();
    }
  };

  // Format file size
  const formatFileSize = (bytes) => {
    return batchUploadService.formatFileSize(bytes);
  };

  // Calculate totals
  const totalFiles = files.length;
  const totalSize = files.reduce((sum, f) => sum + f.size, 0);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle>
        Batch Upload Files
        <Typography variant="body2" color="text.secondary">
          Upload multiple audio files for transcription
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Upload Configuration */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>Upload Settings</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Whisper Model</InputLabel>
                  <Select
                    value={config.whisperModel}
                    onChange={(e) => handleConfigChange('whisperModel', e.target.value)}
                    disabled={uploading}
                  >
                    <MenuItem value="tiny">Tiny (Fast)</MenuItem>
                    <MenuItem value="base">Base (Balanced)</MenuItem>
                    <MenuItem value="small">Small (Better Quality)</MenuItem>
                    <MenuItem value="medium">Medium (High Quality)</MenuItem>
                    <MenuItem value="large-v3">Large-v3 (Best Quality)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Language (optional)"
                  placeholder="auto-detect"
                  value={config.language || ''}
                  onChange={(e) => handleConfigChange('language', e.target.value || null)}
                  disabled={uploading}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* File Drop Zone */}
        <Card
          variant="outlined"
          sx={{
            border: dragOver ? '2px dashed #2196f3' : '2px dashed #ddd',
            backgroundColor: dragOver ? '#f3f9ff' : 'transparent',
            cursor: uploading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            flex: 1,
            display: 'flex',
            flexDirection: 'column'
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !uploading && fileInputRef.current?.click()}
        >
          <CardContent sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column',
            justifyContent: files.length > 0 ? 'flex-start' : 'center'
          }}>
            {files.length === 0 ? (
              <Box textAlign="center">
                <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Drag & drop files here
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  or click to browse files
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Supported formats: MP3, WAV, M4A, FLAC, OGG, WebM, MP4
                </Typography>
              </Box>
            ) : (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Selected Files ({totalFiles})
                  </Typography>
                  <Box display="flex" gap={1} alignItems="center">
                    <Chip 
                      label={`Total: ${formatFileSize(totalSize)}`} 
                      size="small" 
                      color="primary" 
                    />
                    {!uploading && (
                      <IconButton size="small" onClick={handleClearFiles}>
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </Box>
                </Box>

                {/* File List */}
                <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {files.map((fileObj) => (
                    <Card key={fileObj.id} variant="outlined" sx={{ mb: 1 }}>
                      <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Box flex={1}>
                            <Typography variant="body2" noWrap>
                              {fileObj.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {formatFileSize(fileObj.size)}
                            </Typography>
                          </Box>
                          <Box display="flex" alignItems="center" gap={1}>
                            {fileObj.status === 'completed' && (
                              <CheckIcon color="success" fontSize="small" />
                            )}
                            {fileObj.status === 'failed' && (
                              <ErrorIcon color="error" fontSize="small" />
                            )}
                            {fileObj.status === 'processing' && (
                              <Box sx={{ width: 20, height: 20 }}>
                                <LinearProgress size={20} />
                              </Box>
                            )}
                            {!uploading && (
                              <IconButton 
                                size="small" 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleRemoveFile(fileObj.id);
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            )}
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>

                {!uploading && (
                  <Button
                    startIcon={<AddIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      fileInputRef.current?.click();
                    }}
                    sx={{ mt: 1 }}
                  >
                    Add More Files
                  </Button>
                )}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Progress */}
        {uploading && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" gutterBottom>
                Upload Progress: {Math.round(uploadProgress)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={uploadProgress}
                sx={{ mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                Processing {totalFiles} files...
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Error Message */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="audio/*,.mp3,.wav,.m4a,.flac,.ogg,.webm,.mp4"
          style={{ display: 'none' }}
          onChange={handleFileInputChange}
        />
      </DialogContent>

      <Divider />

      <DialogActions sx={{ p: 2 }}>
        {!uploading ? (
          <>
            <Button onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleStartUpload}
              disabled={files.length === 0}
              startIcon={<UploadIcon />}
            >
              Start Upload ({totalFiles} files)
            </Button>
          </>
        ) : (
          <>
            <Button onClick={handleCancelUpload} startIcon={<CancelIcon />}>
              Cancel Upload
            </Button>
            <Button disabled>
              Processing...
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default BatchUploadDialog;