/**
 * Transcript Search Page Component - T021: Implement transcript search functionality
 * 
 * Main search interface component providing comprehensive transcript search capabilities
 * with advanced filtering, sorting, and result display features.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Chip,
  Pagination,
  Alert,
  Skeleton,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  AccessTime as TimeIcon,
  Language as LanguageIcon,
  Psychology as BrainIcon
} from '@mui/icons-material';

import SearchInput from '../components/search/SearchInput';
import SearchFilters from '../components/search/SearchFilters';
import SearchResults from '../components/search/SearchResults';
import SearchStats from '../components/search/SearchStats';
import { transcriptSearchService, searchTypes, sortOrders } from '../services/transcriptSearchService';

const TranscriptSearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Search state
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState(searchTypes.COMBINED);
  const [sortOrder, setSortOrder] = useState(sortOrders.RELEVANCE);
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Results state
  const [results, setResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);
  const [searchTime, setSearchTime] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [availableFilters, setAvailableFilters] = useState(null);
  const [searchStats, setSearchStats] = useState(null);

  // Initialize from URL parameters on mount
  useEffect(() => {
    const searchParams = transcriptSearchService.parseSearchUrl(location.search);
    setQuery(searchParams.query);
    setSearchType(searchParams.searchType);
    setSortOrder(searchParams.sortOrder);
    setPage(searchParams.page);
    setPageSize(searchParams.pageSize);
    setFilters(searchParams.filters);

    // Load initial data
    loadAvailableFilters();
    loadSearchStats();

    // Perform search if query exists
    if (searchParams.query) {
      performSearch(searchParams);
    }
  }, [location.search]);

  // Load available filter options
  const loadAvailableFilters = useCallback(async () => {
    try {
      const response = await transcriptSearchService.getSearchFilters();
      if (response.success) {
        setAvailableFilters(response.data);
      }
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  }, []);

  // Load search statistics
  const loadSearchStats = useCallback(async () => {
    try {
      const response = await transcriptSearchService.getSearchStatistics();
      if (response.success) {
        setSearchStats(response.data);
      }
    } catch (error) {
      console.error('Failed to load search stats:', error);
    }
  }, []);

  // Perform search with current parameters
  const performSearch = useCallback(async (searchParams = null) => {
    const params = searchParams || {
      query,
      searchType,
      sortOrder,
      page,
      pageSize,
      filters
    };

    // Validate query
    const validation = transcriptSearchService.validateQuery(params.query);
    if (!validation.isValid) {
      setError(validation.errors.join(', '));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await transcriptSearchService.searchTranscripts(params);
      
      if (response.success) {
        const formattedResults = transcriptSearchService.formatSearchResults(response.data.results);
        setResults(formattedResults);
        setTotalResults(response.data.total_results);
        setSearchTime(response.data.search_time_ms);
        
        // Update URL without causing navigation
        const searchUrl = transcriptSearchService.buildSearchUrl(params);
        window.history.replaceState(null, '', searchUrl);
      } else {
        setError(response.error);
        setResults([]);
        setTotalResults(0);
      }
    } catch (error) {
      setError('Search failed. Please try again.');
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  }, [query, searchType, sortOrder, page, pageSize, filters]);

  // Handle search input changes with debouncing
  const debouncedSearch = useCallback(
    transcriptSearchService.createDebouncedSearch(performSearch, 500),
    [performSearch]
  );

  const handleQueryChange = (newQuery) => {
    setQuery(newQuery);
    setPage(1); // Reset to first page
    
    if (newQuery.trim()) {
      debouncedSearch();
    } else {
      setResults([]);
      setTotalResults(0);
    }
  };

  // Handle search type change
  const handleSearchTypeChange = (newType) => {
    setSearchType(newType);
    setPage(1);
    if (query.trim()) {
      performSearch();
    }
  };

  // Handle sort order change
  const handleSortOrderChange = (newOrder) => {
    setSortOrder(newOrder);
    if (query.trim()) {
      performSearch();
    }
  };

  // Handle filter changes
  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setPage(1);
    if (query.trim()) {
      performSearch();
    }
  };

  // Handle pagination
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
    performSearch();
  };

  // Get search suggestions
  const getSuggestions = useCallback(async (partialQuery) => {
    if (partialQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await transcriptSearchService.getSearchSuggestions(partialQuery);
      if (response.success) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {
      console.error('Failed to get suggestions:', error);
      setSuggestions([]);
    }
  }, []);

  // Share search results
  const handleShare = () => {
    const searchUrl = window.location.href;
    navigator.clipboard.writeText(searchUrl).then(() => {
      // Could show a snackbar notification here
      console.log('Search URL copied to clipboard');
    });
  };

  // Calculate total pages
  const totalPages = Math.ceil(totalResults / pageSize);

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Page Header */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <SearchIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              Search Transcripts
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Tooltip title="Toggle Filters">
              <IconButton 
                onClick={() => setShowFilters(!showFilters)}
                color={showFilters ? 'primary' : 'default'}
              >
                <FilterIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Share Search">
              <IconButton onClick={handleShare}>
                <ShareIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Search Statistics */}
        {searchStats && (
          <Box display="flex" gap={2} mb={2}>
            <Chip
              icon={<BrainIcon />}
              label={`${searchStats.total_searchable_transcripts} Searchable Transcripts`}
              variant="outlined"
              size="small"
            />
            {searchTime > 0 && (
              <Chip
                icon={<TimeIcon />}
                label={`Search completed in ${searchTime.toFixed(0)}ms`}
                variant="outlined"
                size="small"
                color="success"
              />
            )}
          </Box>
        )}

        {/* Main Search Input */}
        <SearchInput
          value={query}
          onChange={handleQueryChange}
          onSearch={() => performSearch()}
          suggestions={suggestions}
          onGetSuggestions={getSuggestions}
          searchType={searchType}
          onSearchTypeChange={handleSearchTypeChange}
          sortOrder={sortOrder}
          onSortOrderChange={handleSortOrderChange}
          availableOptions={availableFilters}
          loading={loading}
        />
      </Paper>

      <Grid container spacing={3}>
        {/* Search Filters Panel */}
        {showFilters && (
          <Grid item xs={12} md={3}>
            <SearchFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              availableFilters={availableFilters}
              loading={loading}
            />
          </Grid>
        )}

        {/* Search Results */}
        <Grid item xs={12} md={showFilters ? 9 : 12}>
          {/* Results Header */}
          {(query.trim() || results.length > 0) && (
            <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">
                  {loading ? 'Searching...' : `${totalResults.toLocaleString()} results`}
                  {query && ` for "${query}"`}
                </Typography>
                {results.length > 0 && (
                  <Box display="flex" gap={1}>
                    <Chip
                      label={`Page ${page} of ${totalPages}`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                )}
              </Box>
            </Paper>
          )}

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Search Results or Loading */}
          {loading ? (
            <Box>
              {[...Array(5)].map((_, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Skeleton variant="text" width="60%" height={32} />
                    <Skeleton variant="text" width="100%" height={20} sx={{ mt: 1 }} />
                    <Skeleton variant="text" width="80%" height={20} />
                    <Box display="flex" gap={1} mt={2}>
                      <Skeleton variant="rounded" width={80} height={24} />
                      <Skeleton variant="rounded" width={100} height={24} />
                      <Skeleton variant="rounded" width={60} height={24} />
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          ) : results.length > 0 ? (
            <>
              <SearchResults
                results={results}
                query={query}
                onResultClick={(result) => {
                  // Navigate to transcript detail or download
                  console.log('Result clicked:', result);
                }}
                loading={loading}
              />

              {/* Pagination */}
              {totalPages > 1 && (
                <Box display="flex" justifyContent="center" mt={3}>
                  <Pagination
                    count={totalPages}
                    page={page}
                    onChange={handlePageChange}
                    color="primary"
                    size="large"
                    showFirstButton
                    showLastButton
                  />
                </Box>
              )}
            </>
          ) : query.trim() && !loading ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <SearchIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No results found
              </Typography>
              <Typography color="text.secondary">
                Try adjusting your search terms or filters
              </Typography>
            </Paper>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <SearchIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Search your transcripts
              </Typography>
              <Typography color="text.secondary">
                Enter a search query to find relevant transcripts
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default TranscriptSearchPage;