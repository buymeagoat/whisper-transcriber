/**
 * Search Filters Component - T021: Implement transcript search functionality
 * 
 * Advanced filtering interface for transcript search with date ranges, duration, 
 * language selection, model filtering, and metadata options.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Chip,
  Slider,
  TextField,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Button,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const SearchFilters = ({
  filters = {},
  onFiltersChange,
  availableFilters = {},
  loading = false
}) => {
  const [localFilters, setLocalFilters] = useState(filters);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Apply filters
  const applyFilters = () => {
    onFiltersChange(localFilters);
  };

  // Clear all filters
  const clearFilters = () => {
    const emptyFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  // Update a specific filter
  const updateFilter = (key, value) => {
    const updatedFilters = {
      ...localFilters,
      [key]: value === null || value === undefined || value === '' ? undefined : value
    };
    
    // Remove undefined values
    Object.keys(updatedFilters).forEach(key => {
      if (updatedFilters[key] === undefined) {
        delete updatedFilters[key];
      }
    });
    
    setLocalFilters(updatedFilters);
  };

  // Check if filters have changes
  const hasChanges = JSON.stringify(filters) !== JSON.stringify(localFilters);

  // Count active filters
  const activeFilterCount = Object.keys(localFilters).length;

  // Format duration for display
  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h`;
  };

  return (
    <Paper elevation={2} sx={{ p: 2 }}>
      {/* Filter Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center" gap={1}>
          <FilterIcon color="primary" />
          <Typography variant="h6">Filters</Typography>
          {activeFilterCount > 0 && (
            <Chip
              label={activeFilterCount}
              size="small"
              color="primary"
            />
          )}
        </Box>
        
        <Button
          size="small"
          startIcon={<ClearIcon />}
          onClick={clearFilters}
          disabled={activeFilterCount === 0}
        >
          Clear
        </Button>
      </Box>

      {/* Language Filter */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Language</Typography>
          {localFilters.languages && localFilters.languages.length > 0 && (
            <Chip
              size="small"
              label={localFilters.languages.length}
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormControl fullWidth size="small">
            <InputLabel>Languages</InputLabel>
            <Select
              multiple
              value={localFilters.languages || []}
              onChange={(e) => updateFilter('languages', e.target.value)}
              input={<OutlinedInput label="Languages" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value.toUpperCase()} size="small" />
                  ))}
                </Box>
              )}
            >
              {(availableFilters.languages || []).map((language) => (
                <MenuItem key={language} value={language}>
                  {language.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </AccordionDetails>
      </Accordion>

      {/* Model Filter */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Whisper Model</Typography>
          {localFilters.models && localFilters.models.length > 0 && (
            <Chip
              size="small"
              label={localFilters.models.length}
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormControl fullWidth size="small">
            <InputLabel>Models</InputLabel>
            <Select
              multiple
              value={localFilters.models || []}
              onChange={(e) => updateFilter('models', e.target.value)}
              input={<OutlinedInput label="Models" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {(availableFilters.models || []).map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </AccordionDetails>
      </Accordion>

      {/* Date Range Filter */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Date Range</Typography>
          {(localFilters.date_from || localFilters.date_to) && (
            <Chip size="small" label="Set" sx={{ ml: 1 }} />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <DatePicker
                  label="From Date"
                  value={localFilters.date_from ? new Date(localFilters.date_from) : null}
                  onChange={(date) => updateFilter('date_from', date?.toISOString())}
                  renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                  maxDate={localFilters.date_to ? new Date(localFilters.date_to) : new Date()}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <DatePicker
                  label="To Date"
                  value={localFilters.date_to ? new Date(localFilters.date_to) : null}
                  onChange={(date) => updateFilter('date_to', date?.toISOString())}
                  renderInput={(params) => <TextField {...params} size="small" fullWidth />}
                  minDate={localFilters.date_from ? new Date(localFilters.date_from) : null}
                  maxDate={new Date()}
                />
              </Grid>
            </Grid>
          </LocalizationProvider>
        </AccordionDetails>
      </Accordion>

      {/* Duration Filter */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Duration</Typography>
          {(localFilters.duration_min || localFilters.duration_max) && (
            <Chip size="small" label="Set" sx={{ ml: 1 }} />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ px: 1 }}>
            <Typography gutterBottom variant="body2">
              Duration Range
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={4}>
                <TextField
                  size="small"
                  label="Min (sec)"
                  type="number"
                  value={localFilters.duration_min || ''}
                  onChange={(e) => updateFilter('duration_min', e.target.value ? parseInt(e.target.value) : null)}
                  inputProps={{ min: 0 }}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  size="small"
                  label="Max (sec)"
                  type="number"
                  value={localFilters.duration_max || ''}
                  onChange={(e) => updateFilter('duration_max', e.target.value ? parseInt(e.target.value) : null)}
                  inputProps={{ min: 0 }}
                />
              </Grid>
              <Grid item xs={4}>
                <Typography variant="caption" color="text.secondary">
                  {availableFilters.duration_range && (
                    `Range: ${formatDuration(availableFilters.duration_range.min)} - ${formatDuration(availableFilters.duration_range.max)}`
                  )}
                </Typography>
              </Grid>
            </Grid>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Sentiment Filter */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Sentiment</Typography>
          {(localFilters.sentiment_min !== null || localFilters.sentiment_max !== null) && (
            <Chip size="small" label="Set" sx={{ ml: 1 }} />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ px: 1 }}>
            <Typography gutterBottom variant="body2">
              Sentiment Score Range (-1 to +1)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  size="small"
                  label="Min Sentiment"
                  type="number"
                  value={localFilters.sentiment_min || ''}
                  onChange={(e) => updateFilter('sentiment_min', e.target.value ? parseFloat(e.target.value) : null)}
                  inputProps={{ min: -1, max: 1, step: 0.1 }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  size="small"
                  label="Max Sentiment"
                  type="number"
                  value={localFilters.sentiment_max || ''}
                  onChange={(e) => updateFilter('sentiment_max', e.target.value ? parseFloat(e.target.value) : null)}
                  inputProps={{ min: -1, max: 1, step: 0.1 }}
                />
              </Grid>
            </Grid>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Metadata Filters */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Content Features</Typography>
          {(localFilters.has_keywords || localFilters.has_summary) && (
            <Chip size="small" label="Set" sx={{ ml: 1 }} />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormGroup>
            <FormControlLabel
              control={
                <Checkbox
                  checked={localFilters.has_keywords === true}
                  onChange={(e) => updateFilter('has_keywords', e.target.checked ? true : null)}
                />
              }
              label="Has Keywords"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={localFilters.has_summary === true}
                  onChange={(e) => updateFilter('has_summary', e.target.checked ? true : null)}
                />
              }
              label="Has Summary"
            />
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* Apply Filters Button */}
      {hasChanges && (
        <>
          <Divider sx={{ my: 2 }} />
          <Button
            fullWidth
            variant="contained"
            onClick={applyFilters}
            disabled={loading}
          >
            Apply Filters
          </Button>
        </>
      )}

      {/* Filter Summary */}
      {activeFilterCount > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">
            {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
          </Typography>
        </>
      )}
    </Paper>
  );
};

export default SearchFilters;