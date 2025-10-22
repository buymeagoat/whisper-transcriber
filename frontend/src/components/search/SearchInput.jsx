/**
 * Search Input Component - T021: Implement transcript search functionality
 * 
 * Advanced search input with autocomplete, search type selection, and sort options.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  ClickAwayListener,
  CircularProgress
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';

import { searchTypes, sortOrders } from '../../services/transcriptSearchService';

const SearchInput = ({
  value,
  onChange,
  onSearch,
  suggestions = [],
  onGetSuggestions,
  searchType,
  onSearchTypeChange,
  sortOrder,
  onSortOrderChange,
  availableOptions,
  loading = false
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const inputRef = useRef(null);

  // Handle input changes
  const handleInputChange = (event) => {
    const newValue = event.target.value;
    onChange(newValue);
    
    // Get suggestions for non-empty queries
    if (newValue.trim() && onGetSuggestions) {
      onGetSuggestions(newValue.trim());
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
    setSelectedSuggestion(-1);
  };

  // Handle key events for navigation and search
  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      if (selectedSuggestion >= 0 && suggestions[selectedSuggestion]) {
        // Use selected suggestion
        onChange(suggestions[selectedSuggestion]);
        setShowSuggestions(false);
      }
      onSearch();
      event.preventDefault();
    } else if (event.key === 'ArrowDown') {
      if (suggestions.length > 0) {
        setSelectedSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
      }
      event.preventDefault();
    } else if (event.key === 'ArrowUp') {
      if (suggestions.length > 0) {
        setSelectedSuggestion(prev => prev > 0 ? prev - 1 : -1);
      }
      event.preventDefault();
    } else if (event.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    onChange(suggestion);
    setShowSuggestions(false);
    onSearch();
    inputRef.current?.focus();
  };

  // Clear search
  const handleClear = () => {
    onChange('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Close suggestions when clicking away
  const handleClickAway = () => {
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
  };

  // Search type options
  const searchTypeOptions = [
    { value: searchTypes.COMBINED, label: 'Combined Search', description: 'Content + Metadata' },
    { value: searchTypes.FULL_TEXT, label: 'Full Text', description: 'Search content only' },
    { value: searchTypes.METADATA, label: 'Metadata', description: 'Keywords & summaries' },
    { value: searchTypes.ADVANCED, label: 'Advanced', description: 'Boolean operators' }
  ];

  // Sort order options
  const sortOrderOptions = availableOptions?.sort_options || [
    { value: sortOrders.RELEVANCE, label: 'Relevance' },
    { value: sortOrders.DATE_DESC, label: 'Newest First' },
    { value: sortOrders.DATE_ASC, label: 'Oldest First' },
    { value: sortOrders.DURATION_DESC, label: 'Longest First' },
    { value: sortOrders.DURATION_ASC, label: 'Shortest First' },
    { value: sortOrders.FILENAME, label: 'Filename A-Z' }
  ];

  return (
    <Box>
      {/* Main Search Input */}
      <ClickAwayListener onClickAway={handleClickAway}>
        <Box position="relative">
          <TextField
            ref={inputRef}
            fullWidth
            variant="outlined"
            placeholder="Search transcripts by content, keywords, filename..."
            value={value}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  {loading ? (
                    <CircularProgress size={20} />
                  ) : (
                    <SearchIcon color="action" />
                  )}
                </InputAdornment>
              ),
              endAdornment: value && (
                <InputAdornment position="end">
                  <IconButton
                    size="small"
                    onClick={handleClear}
                    edge="end"
                  >
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ),
              sx: {
                fontSize: '1.1rem',
                '& .MuiOutlinedInput-root': {
                  '&:hover fieldset': {
                    borderColor: 'primary.main',
                  },
                },
              }
            }}
            sx={{ mb: 2 }}
          />

          {/* Search Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <Paper
              elevation={3}
              sx={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                zIndex: 1000,
                maxHeight: 200,
                overflow: 'auto'
              }}
            >
              <List dense>
                {suggestions.map((suggestion, index) => (
                  <ListItem
                    key={index}
                    button
                    selected={index === selectedSuggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    sx={{
                      '&:hover': {
                        backgroundColor: 'action.hover'
                      }
                    }}
                  >
                    <AutoAwesomeIcon
                      sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }}
                    />
                    <ListItemText
                      primary={suggestion}
                      sx={{
                        '& .MuiListItemText-primary': {
                          fontSize: '0.9rem'
                        }
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>
      </ClickAwayListener>

      {/* Search Options */}
      <Grid container spacing={2} alignItems="center">
        {/* Search Type Selection */}
        <Grid item xs={12} sm={6} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Search Type</InputLabel>
            <Select
              value={searchType}
              label="Search Type"
              onChange={(e) => onSearchTypeChange(e.target.value)}
            >
              {searchTypeOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  <Box>
                    <Box component="span" sx={{ fontWeight: 'medium' }}>
                      {option.label}
                    </Box>
                    <Box 
                      component="span" 
                      sx={{ 
                        fontSize: '0.75rem', 
                        color: 'text.secondary',
                        display: 'block'
                      }}
                    >
                      {option.description}
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Sort Order Selection */}
        <Grid item xs={12} sm={6} md={4}>
          <FormControl fullWidth size="small">
            <InputLabel>Sort By</InputLabel>
            <Select
              value={sortOrder}
              label="Sort By"
              onChange={(e) => onSortOrderChange(e.target.value)}
            >
              {sortOrderOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Quick Search Tips */}
        <Grid item xs={12} md={4}>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            <Chip
              label="Tip: Use quotes for exact phrases"
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem' }}
            />
          </Box>
        </Grid>
      </Grid>

      {/* Search Examples or Help Text */}
      {!value && (
        <Box mt={1}>
          <Box component="span" sx={{ fontSize: '0.875rem', color: 'text.secondary' }}>
            Try searching for: 
            <Chip 
              label="meeting" 
              size="small" 
              variant="outlined" 
              sx={{ ml: 0.5, mr: 0.5, fontSize: '0.75rem' }}
              onClick={() => onChange('meeting')}
              clickable
            />
            <Chip 
              label="presentation" 
              size="small" 
              variant="outlined" 
              sx={{ mr: 0.5, fontSize: '0.75rem' }}
              onClick={() => onChange('presentation')}
              clickable
            />
            <Chip 
              label="interview" 
              size="small" 
              variant="outlined" 
              sx={{ fontSize: '0.75rem' }}
              onClick={() => onChange('interview')}
              clickable
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default SearchInput;