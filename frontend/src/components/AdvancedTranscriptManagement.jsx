import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Card,
  CardContent,
  IconButton,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  Checkbox,
  ListItemText,
  Stack,
  Divider,
  Tooltip,
  Alert,
  LinearProgress,
  Autocomplete,
  Badge
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  LocalOffer as TagIcon,
  BookmarkAdd as BookmarkIcon,
  History as HistoryIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  Check as CheckIcon,
  GetApp as ExportIcon,
  ViewList as BatchIcon
} from '@mui/icons-material';

import { transcriptManagementService } from '../services/transcriptManagementService';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const AdvancedTranscriptManagement = () => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [searchResults, setSearchResults] = useState({ results: [], total_count: 0 });
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState([]);
  const [filterSummary, setFilterSummary] = useState({});
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    tags: [],
    status_filter: [],
    model_filter: [],
    language_filter: [],
    date_from: null,
    date_to: null,
    duration_min: null,
    duration_max: null
  });
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  // Dialog states
  const [createTagDialog, setCreateTagDialog] = useState(false);
  const [batchOperationDialog, setBatchOperationDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);
  const [versionDialog, setVersionDialog] = useState({ open: false, jobId: null });
  
  // Form states
  const [newTag, setNewTag] = useState({ name: '', color: '#3B82F6' });
  const [batchOperation, setBatchOperation] = useState({ type: 'tag', parameters: {} });
  const [exportSettings, setExportSettings] = useState({ format: 'srt', options: {} });

  // Load initial data
  useEffect(() => {
    loadFilterSummary();
    performSearch();
  }, []);

  // Perform search when filters change
  useEffect(() => {
    if (searchQuery || Object.values(filters).some(v => v && (Array.isArray(v) ? v.length > 0 : true))) {
      performSearch();
    }
  }, [searchQuery, filters, sortBy, sortOrder, currentPage, pageSize]);

  const loadFilterSummary = async () => {
    try {
      const summary = await transcriptManagementService.getFilterSummary();
      setFilterSummary(summary);
    } catch (error) {
      console.error('Error loading filter summary:', error);
    }
  };

  const performSearch = async () => {
    setLoading(true);
    try {
      const searchRequest = {
        query: searchQuery || undefined,
        tags: filters.tags.length > 0 ? filters.tags : undefined,
        status_filter: filters.status_filter.length > 0 ? filters.status_filter : undefined,
        model_filter: filters.model_filter.length > 0 ? filters.model_filter : undefined,
        language_filter: filters.language_filter.length > 0 ? filters.language_filter : undefined,
        date_from: filters.date_from || undefined,
        date_to: filters.date_to || undefined,
        duration_min: filters.duration_min || undefined,
        duration_max: filters.duration_max || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: currentPage,
        page_size: pageSize
      };

      const results = await transcriptManagementService.searchTranscripts(searchRequest);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      tags: [],
      status_filter: [],
      model_filter: [],
      language_filter: [],
      date_from: null,
      date_to: null,
      duration_min: null,
      duration_max: null
    });
    setSearchQuery('');
    setCurrentPage(1);
  };

  const handleJobSelection = (jobId, selected) => {
    if (selected) {
      setSelectedJobs(prev => [...prev, jobId]);
    } else {
      setSelectedJobs(prev => prev.filter(id => id !== jobId));
    }
  };

  const handleSelectAll = () => {
    if (selectedJobs.length === searchResults.results.length) {
      setSelectedJobs([]);
    } else {
      setSelectedJobs(searchResults.results.map(job => job.id));
    }
  };

  const handleCreateTag = async () => {
    try {
      await transcriptManagementService.createTag(newTag);
      setCreateTagDialog(false);
      setNewTag({ name: '', color: '#3B82F6' });
      loadFilterSummary();
    } catch (error) {
      console.error('Error creating tag:', error);
    }
  };

  const handleBatchOperation = async () => {
    try {
      await transcriptManagementService.createBatchOperation({
        operation_type: batchOperation.type,
        job_ids: selectedJobs,
        parameters: batchOperation.parameters
      });
      setBatchOperationDialog(false);
      setSelectedJobs([]);
      // Refresh data
      performSearch();
    } catch (error) {
      console.error('Error creating batch operation:', error);
    }
  };

  const handleExport = async () => {
    try {
      await transcriptManagementService.createExport({
        job_ids: selectedJobs,
        export_format: exportSettings.format,
        export_options: exportSettings.options
      });
      setExportDialog(false);
      setSelectedJobs([]);
    } catch (error) {
      console.error('Error creating export:', error);
    }
  };

  const SearchAndFilterSection = () => (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Grid container spacing={3}>
        {/* Search Bar */}
        <Grid item xs={12}>
          <TextField
            fullWidth
            placeholder="Search transcripts, metadata, keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ color: 'action.active', mr: 1 }} />,
              endAdornment: searchQuery && (
                <IconButton onClick={() => setSearchQuery('')}>
                  <ClearIcon />
                </IconButton>
              )
            }}
          />
        </Grid>

        {/* Filters Row 1 */}
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Tags</InputLabel>
            <Select
              multiple
              value={filters.tags}
              onChange={(e) => handleFilterChange('tags', e.target.value)}
              input={<OutlinedInput label="Tags" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => {
                    const tag = filterSummary.tags?.find(t => t.name === value);
                    return (
                      <Chip
                        key={value}
                        label={value}
                        size="small"
                        style={{ backgroundColor: tag?.color || '#3B82F6', color: 'white' }}
                      />
                    );
                  })}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              {filterSummary.tags?.map((tag) => (
                <MenuItem key={tag.name} value={tag.name}>
                  <Checkbox checked={filters.tags.indexOf(tag.name) > -1} />
                  <ListItemText primary={tag.name} />
                  <Chip
                    size="small"
                    style={{ backgroundColor: tag.color, color: 'white', marginLeft: 8 }}
                  />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              multiple
              value={filters.status_filter}
              onChange={(e) => handleFilterChange('status_filter', e.target.value)}
              input={<OutlinedInput label="Status" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {filterSummary.statuses?.map((status) => (
                <MenuItem key={status.status} value={status.status}>
                  <Checkbox checked={filters.status_filter.indexOf(status.status) > -1} />
                  <ListItemText primary={`${status.status} (${status.count})`} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Model</InputLabel>
            <Select
              multiple
              value={filters.model_filter}
              onChange={(e) => handleFilterChange('model_filter', e.target.value)}
              input={<OutlinedInput label="Model" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {filterSummary.models?.map((model) => (
                <MenuItem key={model} value={model}>
                  <Checkbox checked={filters.model_filter.indexOf(model) > -1} />
                  <ListItemText primary={model} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Language</InputLabel>
            <Select
              multiple
              value={filters.language_filter}
              onChange={(e) => handleFilterChange('language_filter', e.target.value)}
              input={<OutlinedInput label="Language" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {filterSummary.languages?.map((language) => (
                <MenuItem key={language} value={language}>
                  <Checkbox checked={filters.language_filter.indexOf(language) > -1} />
                  <ListItemText primary={language} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Filter Actions */}
        <Grid item xs={12}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              disabled={!searchQuery && Object.values(filters).every(v => !v || (Array.isArray(v) && v.length === 0))}
            >
              Clear Filters
            </Button>
            <Typography variant="body2" color="textSecondary">
              {searchResults.total_count} transcripts found
            </Typography>
          </Stack>
        </Grid>
      </Grid>
    </Paper>
  );

  const ResultsSection = () => (
    <Paper sx={{ p: 3 }}>
      {/* Batch Actions */}
      {selectedJobs.length > 0 && (
        <Box sx={{ mb: 2, p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="body2">
              {selectedJobs.length} transcript{selectedJobs.length !== 1 ? 's' : ''} selected
            </Typography>
            <Button
              size="small"
              startIcon={<TagIcon />}
              onClick={() => setBatchOperationDialog(true)}
            >
              Batch Tag
            </Button>
            <Button
              size="small"
              startIcon={<ExportIcon />}
              onClick={() => setExportDialog(true)}
            >
              Export Selected
            </Button>
            <Button
              size="small"
              startIcon={<DeleteIcon />}
              color="error"
              onClick={() => {
                setBatchOperation({ type: 'delete', parameters: {} });
                setBatchOperationDialog(true);
              }}
            >
              Delete Selected
            </Button>
          </Stack>
        </Box>
      )}

      {/* Results Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Checkbox
            checked={selectedJobs.length === searchResults.results.length && searchResults.results.length > 0}
            indeterminate={selectedJobs.length > 0 && selectedJobs.length < searchResults.results.length}
            onChange={handleSelectAll}
          />
          <Typography variant="h6">
            Transcripts ({searchResults.total_count})
          </Typography>
        </Stack>
        
        <Stack direction="row" spacing={1}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Sort by</InputLabel>
            <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} label="Sort by">
              <MenuItem value="created_at">Created</MenuItem>
              <MenuItem value="original_filename">Filename</MenuItem>
              <MenuItem value="duration">Duration</MenuItem>
              <MenuItem value="status">Status</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </Button>
        </Stack>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Results Grid */}
      <Grid container spacing={2}>
        {searchResults.results.map((job) => (
          <Grid item xs={12} key={job.id}>
            <TranscriptCard
              job={job}
              selected={selectedJobs.includes(job.id)}
              onSelectionChange={(selected) => handleJobSelection(job.id, selected)}
              onVersions={() => setVersionDialog({ open: true, jobId: job.id })}
            />
          </Grid>
        ))}
      </Grid>

      {/* Pagination */}
      {searchResults.total_pages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              Previous
            </Button>
            <Typography>
              Page {currentPage} of {searchResults.total_pages}
            </Typography>
            <Button
              disabled={currentPage === searchResults.total_pages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Next
            </Button>
          </Stack>
        </Box>
      )}
    </Paper>
  );

  const TranscriptCard = ({ job, selected, onSelectionChange, onVersions }) => {
    const [anchorEl, setAnchorEl] = useState(null);

    const formatDuration = (seconds) => {
      if (!seconds) return 'N/A';
      const hrs = Math.floor(seconds / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;
      return hrs > 0 ? `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}` 
                     : `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getStatusColor = (status) => {
      switch (status) {
        case 'completed': return 'success';
        case 'failed': return 'error';
        case 'processing': return 'warning';
        default: return 'default';
      }
    };

    return (
      <Card sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
        <Checkbox
          checked={selected}
          onChange={(e) => onSelectionChange(e.target.checked)}
        />
        
        <CardContent sx={{ flex: 1, py: 1 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" noWrap>
                {job.original_filename}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {job.id}
              </Typography>
            </Grid>
            
            <Grid item xs={6} md={2}>
              <Chip
                label={job.status}
                color={getStatusColor(job.status)}
                size="small"
              />
            </Grid>
            
            <Grid item xs={6} md={2}>
              <Typography variant="body2">
                {formatDuration(job.duration)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {job.tokens} tokens
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {job.tags?.slice(0, 3).map((tag) => (
                  <Chip
                    key={tag.name}
                    label={tag.name}
                    size="small"
                    style={{ backgroundColor: tag.color, color: 'white' }}
                  />
                ))}
                {job.tags?.length > 3 && (
                  <Chip label={`+${job.tags.length - 3}`} size="small" variant="outlined" />
                )}
              </Box>
            </Grid>
            
            <Grid item xs={12} md={1}>
              <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
                <MoreIcon />
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={() => setAnchorEl(null)}
              >
                <MenuItem onClick={() => {
                  onVersions();
                  setAnchorEl(null);
                }}>
                  <HistoryIcon sx={{ mr: 1 }} />
                  View Versions
                </MenuItem>
                <MenuItem onClick={() => setAnchorEl(null)}>
                  <BookmarkIcon sx={{ mr: 1 }} />
                  Add Bookmark
                </MenuItem>
                <MenuItem onClick={() => setAnchorEl(null)}>
                  <EditIcon sx={{ mr: 1 }} />
                  Edit Metadata
                </MenuItem>
                <MenuItem onClick={() => setAnchorEl(null)}>
                  <DownloadIcon sx={{ mr: 1 }} />
                  Download
                </MenuItem>
              </Menu>
            </Grid>
          </Grid>
          
          {job.abstract && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              {job.abstract}
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Advanced Transcript Management
        </Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setCreateTagDialog(true)}
          >
            Create Tag
          </Button>
        </Stack>
      </Box>

      <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
        <Tab label="Search & Browse" />
        <Tab label="Batch Operations" />
        <Tab label="Export History" />
      </Tabs>

      {activeTab === 0 && (
        <>
          <SearchAndFilterSection />
          <ResultsSection />
        </>
      )}

      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Batch Operations
          </Typography>
          <Typography color="textSecondary">
            Batch operations functionality will be displayed here.
          </Typography>
        </Paper>
      )}

      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Export History
          </Typography>
          <Typography color="textSecondary">
            Export history and download functionality will be displayed here.
          </Typography>
        </Paper>
      )}

      {/* Create Tag Dialog */}
      <Dialog open={createTagDialog} onClose={() => setCreateTagDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Tag</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Tag Name"
              value={newTag.name}
              onChange={(e) => setNewTag(prev => ({ ...prev, name: e.target.value }))}
            />
            <Box>
              <Typography variant="subtitle2" gutterBottom>Color</Typography>
              <input
                type="color"
                value={newTag.color}
                onChange={(e) => setNewTag(prev => ({ ...prev, color: e.target.value }))}
                style={{ width: '100%', height: 40, border: 'none', borderRadius: 4 }}
              />
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTagDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTag}
            variant="contained"
            disabled={!newTag.name.trim()}
          >
            Create Tag
          </Button>
        </DialogActions>
      </Dialog>

      {/* Version Dialog Placeholder */}
      <Dialog
        open={versionDialog.open}
        onClose={() => setVersionDialog({ open: false, jobId: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Transcript Versions</DialogTitle>
        <DialogContent>
          <Typography>
            Version management interface for job: {versionDialog.jobId}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVersionDialog({ open: false, jobId: null })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdvancedTranscriptManagement;