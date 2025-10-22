/**
 * T020: Batch Progress Tracker Component
 * Component for monitoring batch upload progress with detailed job status
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  Schedule as QueuedIcon,
  Settings as ProcessingIcon,
  Cancel as CancelledIcon
} from '@mui/icons-material';

import batchUploadService, { BATCH_STATUS, JOB_STATUS } from '../services/batchUploadService';

const BatchProgressTracker = ({ 
  batchId, 
  onComplete, 
  onError,
  autoRefresh = true,
  showActions = true 
}) => {
  const [batchData, setBatchData] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshTimer, setRefreshTimer] = useState(null);

  // Load batch data
  const loadBatchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const progress = await batchUploadService.getBatchProgress(batchId);
      setBatchData(progress);

      // Handle completion
      if (progress.status === BATCH_STATUS.COMPLETED && onComplete) {
        onComplete(progress);
      } else if (progress.status === BATCH_STATUS.FAILED && onError) {
        onError(new Error('Batch upload failed'));
      }

    } catch (err) {
      console.error('Error loading batch data:', err);
      setError(err.message);
      if (onError) {
        onError(err);
      }
    } finally {
      setLoading(false);
    }
  };

  // Set up auto-refresh
  useEffect(() => {
    if (!batchId) return;

    // Initial load
    loadBatchData();

    // Set up auto-refresh for active batches
    if (autoRefresh) {
      const timer = setInterval(() => {
        if (batchData && 
            [BATCH_STATUS.PENDING, BATCH_STATUS.PROCESSING].includes(batchData.status)) {
          loadBatchData();
        }
      }, 2000);

      setRefreshTimer(timer);

      return () => {
        if (timer) {
          clearInterval(timer);
        }
      };
    }
  }, [batchId, autoRefresh]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
    };
  }, [refreshTimer]);

  // Handle cancel batch
  const handleCancel = async () => {
    try {
      await batchUploadService.cancelBatchUpload(batchId);
      await loadBatchData(); // Refresh to show cancelled status
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle delete batch
  const handleDelete = async () => {
    try {
      await batchUploadService.deleteBatchUpload(batchId);
      // Parent component should handle removal from list
    } catch (err) {
      setError(err.message);
    }
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case BATCH_STATUS.PENDING:
      case JOB_STATUS.QUEUED:
        return <QueuedIcon />;
      case BATCH_STATUS.PROCESSING:
      case JOB_STATUS.PROCESSING:
        return <ProcessingIcon />;
      case BATCH_STATUS.COMPLETED:
      case JOB_STATUS.COMPLETED:
        return <CompletedIcon />;
      case BATCH_STATUS.FAILED:
      case JOB_STATUS.FAILED:
        return <ErrorIcon />;
      case BATCH_STATUS.CANCELLED:
      case JOB_STATUS.SKIPPED:
        return <CancelledIcon />;
      default:
        return <QueuedIcon />;
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    return batchUploadService.getStatusColor(status);
  };

  // Format time
  const formatTime = (dateString) => {
    if (!dateString) return '--';
    return new Date(dateString).toLocaleString();
  };

  if (!batchData && loading) {
    return (
      <Card>
        <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={24} />
          <Typography>Loading batch information...</Typography>
        </CardContent>
      </Card>
    );
  }

  if (error && !batchData) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error" action={
            <Button size="small" onClick={loadBatchData}>
              Retry
            </Button>
          }>
            {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!batchData) {
    return null;
  }

  const isActive = [BATCH_STATUS.PENDING, BATCH_STATUS.PROCESSING].includes(batchData.status);
  const canCancel = batchData.status === BATCH_STATUS.PROCESSING;
  const canDelete = !isActive;

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Typography variant="h6" component="span">
                Batch {batchId.substring(0, 8)}...
              </Typography>
              <Chip
                icon={getStatusIcon(batchData.status)}
                label={batchData.status.toUpperCase()}
                color={getStatusColor(batchData.status)}
                size="small"
              />
              {loading && <CircularProgress size={16} />}
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              {batchData.total_files} files • {batchData.completed_files} completed • {batchData.failed_files} failed
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            {showActions && (
              <>
                <Tooltip title="Refresh">
                  <IconButton size="small" onClick={loadBatchData}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                
                {canCancel && (
                  <Tooltip title="Cancel Batch">
                    <IconButton size="small" onClick={handleCancel} color="error">
                      <StopIcon />
                    </IconButton>
                  </Tooltip>
                )}

                {canDelete && (
                  <Tooltip title="Delete Batch">
                    <IconButton size="small" onClick={handleDelete} color="error">
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </>
            )}

            <IconButton 
              size="small" 
              onClick={() => setExpanded(!expanded)}
              aria-label="expand"
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        {/* Progress Bar */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2">
              Progress: {Math.round(batchData.progress)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Success Rate: {Math.round(batchData.success_rate)}%
            </Typography>
          </Box>
          
          <LinearProgress 
            variant="determinate" 
            value={batchData.progress}
            color={batchData.status === BATCH_STATUS.FAILED ? 'error' : 'primary'}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Expandable Job Details */}
        <Collapse in={expanded}>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Job Details ({batchData.jobs?.length || 0} jobs)
            </Typography>
            
            {batchData.jobs && batchData.jobs.length > 0 ? (
              <List dense>
                {batchData.jobs.map((job, index) => (
                  <ListItem key={job.job_id || index} divider>
                    <ListItemIcon>
                      {getStatusIcon(job.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2" component="span" noWrap>
                            {job.filename}
                          </Typography>
                          <Chip
                            label={job.status.toUpperCase()}
                            color={getStatusColor(job.status)}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          {job.progress !== undefined && (
                            <LinearProgress
                              variant="determinate"
                              value={job.progress}
                              size="small"
                              sx={{ mt: 0.5, mb: 0.5, height: 3 }}
                            />
                          )}
                          {job.error_message && (
                            <Typography variant="caption" color="error">
                              Error: {job.error_message}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
                No job details available
              </Typography>
            )}

            {/* Batch Statistics */}
            <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
              <Typography variant="caption" color="text.secondary" display="block">
                Batch Statistics
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={2} mt={1}>
                <Typography variant="caption">
                  <strong>Total:</strong> {batchData.total_files}
                </Typography>
                <Typography variant="caption">
                  <strong>Completed:</strong> {batchData.completed_files}
                </Typography>
                <Typography variant="caption">
                  <strong>Failed:</strong> {batchData.failed_files}
                </Typography>
                <Typography variant="caption">
                  <strong>Success Rate:</strong> {Math.round(batchData.success_rate)}%
                </Typography>
              </Box>
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default BatchProgressTracker;