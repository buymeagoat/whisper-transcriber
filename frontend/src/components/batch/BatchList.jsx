/**
 * T020: Batch List Management Component
 * Component for displaying and managing multiple batch uploads
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Tabs,
  Tab,
  Badge,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  MoreVert as MoreIcon
} from '@mui/icons-material';

import BatchProgressTracker from './BatchProgressTracker';
import BatchUploadDialog from './BatchUploadDialog';
import batchUploadService, { BATCH_STATUS } from '../services/batchUploadService';

const BatchList = ({ 
  onBatchComplete,
  onBatchError,
  maxDisplayBatches = 10
}) => {
  const [batches, setBatches] = useState([]);
  const [filteredBatches, setFilteredBatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showDialog, setShowDialog] = useState(false);
  const [refreshTimer, setRefreshTimer] = useState(null);
  
  // Menu states
  const [filterMenuAnchor, setFilterMenuAnchor] = useState(null);
  const [sortMenuAnchor, setSortMenuAnchor] = useState(null);

  // Load all batches
  const loadBatches = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const batchList = await batchUploadService.listBatchUploads();
      setBatches(batchList);
      
    } catch (err) {
      console.error('Error loading batches:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort batches
  useEffect(() => {
    let filtered = [...batches];

    // Apply search filter
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(batch => 
        batch.batch_id.toLowerCase().includes(term) ||
        (batch.name && batch.name.toLowerCase().includes(term)) ||
        batch.files.some(file => file.filename.toLowerCase().includes(term))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(batch => batch.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];

      // Handle special sorting cases
      if (sortBy === 'progress') {
        aVal = (a.completed_files / a.total_files) * 100;
        bVal = (b.completed_files / b.total_files) * 100;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    // Limit display count
    if (maxDisplayBatches > 0) {
      filtered = filtered.slice(0, maxDisplayBatches);
    }

    setFilteredBatches(filtered);
  }, [batches, searchTerm, statusFilter, sortBy, sortOrder, maxDisplayBatches]);

  // Initial load and auto-refresh setup
  useEffect(() => {
    loadBatches();

    // Set up auto-refresh for active batches
    const timer = setInterval(() => {
      const hasActiveBatches = batches.some(batch => 
        [BATCH_STATUS.PENDING, BATCH_STATUS.PROCESSING].includes(batch.status)
      );
      
      if (hasActiveBatches) {
        loadBatches();
      }
    }, 5000);

    setRefreshTimer(timer);

    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
    };
  }, [refreshTimer]);

  // Handle batch creation
  const handleBatchCreated = (batchId) => {
    setShowDialog(false);
    loadBatches(); // Refresh the list
  };

  // Handle batch completion
  const handleBatchComplete = (batchData) => {
    loadBatches(); // Refresh the list
    if (onBatchComplete) {
      onBatchComplete(batchData);
    }
  };

  // Handle batch error
  const handleBatchError = (error) => {
    loadBatches(); // Refresh the list
    if (onBatchError) {
      onBatchError(error);
    }
  };

  // Get status counts for tabs
  const getStatusCounts = () => {
    const counts = {
      all: batches.length,
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
      cancelled: 0
    };

    batches.forEach(batch => {
      if (counts[batch.status] !== undefined) {
        counts[batch.status]++;
      }
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  // Render tab with badge
  const renderTabWithBadge = (label, count, value) => (
    <Tab 
      label={
        <Badge badgeContent={count} color="primary" max={999}>
          {label}
        </Badge>
      }
      value={value}
    />
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Batch Uploads
        </Typography>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadBatches} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowDialog(true)}
          >
            New Batch
          </Button>
        </Box>
      </Box>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            {/* Search */}
            <TextField
              placeholder="Search batches..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
              sx={{ minWidth: 250 }}
            />

            {/* Status Filter Tabs */}
            <Box flex={1}>
              <Tabs 
                value={statusFilter} 
                onChange={(e, value) => setStatusFilter(value)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {renderTabWithBadge('All', statusCounts.all, 'all')}
                {renderTabWithBadge('Processing', statusCounts.processing, BATCH_STATUS.PROCESSING)}
                {renderTabWithBadge('Pending', statusCounts.pending, BATCH_STATUS.PENDING)}
                {renderTabWithBadge('Completed', statusCounts.completed, BATCH_STATUS.COMPLETED)}
                {renderTabWithBadge('Failed', statusCounts.failed, BATCH_STATUS.FAILED)}
                {renderTabWithBadge('Cancelled', statusCounts.cancelled, BATCH_STATUS.CANCELLED)}
              </Tabs>
            </Box>

            {/* Sort Menu */}
            <Tooltip title="Sort Options">
              <IconButton
                onClick={(e) => setSortMenuAnchor(e.currentTarget)}
                size="small"
              >
                <SortIcon />
              </IconButton>
            </Tooltip>

            <Menu
              anchorEl={sortMenuAnchor}
              open={Boolean(sortMenuAnchor)}
              onClose={() => setSortMenuAnchor(null)}
            >
              <MenuItem onClick={() => { setSortBy('created_at'); setSortOrder('desc'); setSortMenuAnchor(null); }}>
                Newest First
              </MenuItem>
              <MenuItem onClick={() => { setSortBy('created_at'); setSortOrder('asc'); setSortMenuAnchor(null); }}>
                Oldest First
              </MenuItem>
              <MenuItem onClick={() => { setSortBy('progress'); setSortOrder('desc'); setSortMenuAnchor(null); }}>
                Progress (High to Low)
              </MenuItem>
              <MenuItem onClick={() => { setSortBy('total_files'); setSortOrder('desc'); setSortMenuAnchor(null); }}>
                File Count (High to Low)
              </MenuItem>
            </Menu>
          </Box>

          {/* Active Filters */}
          {(statusFilter !== 'all' || searchTerm.trim()) && (
            <Box mt={2}>
              <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                Active Filters:
              </Typography>
              <Stack direction="row" spacing={1}>
                {statusFilter !== 'all' && (
                  <Chip
                    label={`Status: ${statusFilter.toUpperCase()}`}
                    size="small"
                    onDelete={() => setStatusFilter('all')}
                  />
                )}
                {searchTerm.trim() && (
                  <Chip
                    label={`Search: "${searchTerm}"`}
                    size="small"
                    onDelete={() => setSearchTerm('')}
                  />
                )}
              </Stack>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Batch List */}
      <Box>
        {loading && filteredBatches.length === 0 ? (
          <Card>
            <CardContent>
              <Typography textAlign="center" color="text.secondary">
                Loading batches...
              </Typography>
            </CardContent>
          </Card>
        ) : filteredBatches.length === 0 ? (
          <Card>
            <CardContent>
              <Typography textAlign="center" color="text.secondary">
                {batches.length === 0 
                  ? "No batch uploads yet. Click 'New Batch' to get started!"
                  : "No batches match your current filters."
                }
              </Typography>
              {batches.length === 0 && (
                <Box textAlign="center" mt={2}>
                  <Button 
                    variant="outlined" 
                    startIcon={<AddIcon />}
                    onClick={() => setShowDialog(true)}
                  >
                    Create First Batch
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        ) : (
          <Stack spacing={2}>
            {filteredBatches.map((batch) => (
              <BatchProgressTracker
                key={batch.batch_id}
                batchId={batch.batch_id}
                onComplete={handleBatchComplete}
                onError={handleBatchError}
                autoRefresh={true}
                showActions={true}
              />
            ))}
            
            {maxDisplayBatches > 0 && batches.length > maxDisplayBatches && (
              <Card>
                <CardContent>
                  <Typography textAlign="center" color="text.secondary">
                    Showing {maxDisplayBatches} of {batches.length} batches.
                    {statusFilter !== 'all' || searchTerm.trim() ? 
                      ' Use filters to refine your search.' : 
                      ' Use search or filters to find specific batches.'
                    }
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Stack>
        )}
      </Box>

      {/* Batch Upload Dialog */}
      <BatchUploadDialog
        open={showDialog}
        onClose={() => setShowDialog(false)}
        onBatchCreated={handleBatchCreated}
      />
    </Box>
  );
};

export default BatchList;