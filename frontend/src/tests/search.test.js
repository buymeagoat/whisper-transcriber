/**
 * T021: Test transcript search frontend components
 * Test suite for React search components and functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import '@testing-library/jest-dom';

import TranscriptSearchPage from '../src/pages/TranscriptSearchPage';
import SearchInput from '../src/components/search/SearchInput';
import SearchResults from '../src/components/search/SearchResults';
import SearchFilters from '../src/components/search/SearchFilters';
import * as transcriptSearchService from '../src/services/transcriptSearchService';

// Mock the search service
jest.mock('../src/services/transcriptSearchService', () => ({
  search: jest.fn(),
  getSearchSuggestions: jest.fn(),
  getSearchFilters: jest.fn(),
  getSearchStats: jest.fn(),
  quickSearch: jest.fn()
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useLocation: jest.fn(() => ({ search: '', pathname: '/search' }))
}));

const theme = createTheme();

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider theme={theme}>
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe('TranscriptSearchPage', () => {
  const mockSearchResults = {
    results: [
      {
        job_id: 'job1',
        filename: 'test1.mp3',
        content: 'Hello world this is a test transcript',
        snippet: 'Hello world this is a test transcript',
        metadata: {
          duration: 120.5,
          language: 'en',
          model: 'medium',
          confidence_score: 0.85,
          word_count: 250,
          summary: 'Test summary',
          keywords: ['test', 'hello'],
          sentiment_score: 0.2
        },
        relevance_score: 0.92,
        match_count: 2,
        created_at: '2024-01-01T10:00:00Z'
      }
    ],
    total: 1,
    page: 1,
    per_page: 10,
    total_pages: 1
  };

  const mockAvailableFilters = {
    languages: ['en', 'es', 'fr'],
    models: ['tiny', 'base', 'small', 'medium', 'large-v3'],
    duration_range: { min: 1.0, max: 3600.0 }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    transcriptSearchService.search.mockResolvedValue(mockSearchResults);
    transcriptSearchService.getSearchFilters.mockResolvedValue(mockAvailableFilters);
    transcriptSearchService.getSearchSuggestions.mockResolvedValue(['test', 'testing']);
    transcriptSearchService.getSearchStats.mockResolvedValue({
      total_transcripts: 100,
      languages: { en: 80, es: 20 },
      models: { medium: 60, 'large-v3': 40 }
    });
  });

  test('renders search page with main components', async () => {
    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    // Check for main page elements
    expect(screen.getByText('Transcript Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search transcripts/i)).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  test('performs search when query is entered', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search transcripts/i);
    
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(transcriptSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'test query'
        })
      );
    });
  });

  test('displays search results correctly', async () => {
    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('test1.mp3')).toBeInTheDocument();
      expect(screen.getByText('Hello world this is a test transcript')).toBeInTheDocument();
      expect(screen.getByText('2m 0s')).toBeInTheDocument(); // Duration
      expect(screen.getByText('EN')).toBeInTheDocument(); // Language
    });
  });

  test('handles empty search results', async () => {
    transcriptSearchService.search.mockResolvedValue({
      results: [],
      total: 0,
      page: 1,
      per_page: 10,
      total_pages: 0
    });

    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no transcripts found/i)).toBeInTheDocument();
    });
  });

  test('handles search errors', async () => {
    transcriptSearchService.search.mockRejectedValue(new Error('Search failed'));

    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error performing search/i)).toBeInTheDocument();
    });
  });

  test('pagination works correctly', async () => {
    const user = userEvent.setup();
    const multiPageResults = {
      ...mockSearchResults,
      total: 25,
      total_pages: 3
    };

    transcriptSearchService.search.mockResolvedValue(multiPageResults);

    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    // Wait for results to load
    await waitFor(() => {
      expect(screen.getByText('test1.mp3')).toBeInTheDocument();
    });

    // Find and click page 2
    const page2Button = screen.getByRole('button', { name: '2' });
    await user.click(page2Button);

    await waitFor(() => {
      expect(transcriptSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      );
    });
  });
});

describe('SearchInput Component', () => {
  const mockProps = {
    query: '',
    onQueryChange: jest.fn(),
    onSearch: jest.fn(),
    loading: false,
    placeholder: 'Search transcripts...'
  };

  test('renders search input with placeholder', () => {
    render(
      <TestWrapper>
        <SearchInput {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText('Search transcripts...')).toBeInTheDocument();
  });

  test('calls onQueryChange when typing', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <SearchInput {...mockProps} />
      </TestWrapper>
    );

    const input = screen.getByPlaceholderText('Search transcripts...');
    await user.type(input, 'test');

    expect(mockProps.onQueryChange).toHaveBeenCalledWith('test');
  });

  test('calls onSearch when Enter is pressed', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <SearchInput {...mockProps} query="test query" />
      </TestWrapper>
    );

    const input = screen.getByPlaceholderText('Search transcripts...');
    await user.click(input);
    await user.keyboard('{Enter}');

    expect(mockProps.onSearch).toHaveBeenCalled();
  });

  test('shows loading state', () => {
    render(
      <TestWrapper>
        <SearchInput {...mockProps} loading={true} />
      </TestWrapper>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays search suggestions', async () => {
    const user = userEvent.setup();
    transcriptSearchService.getSearchSuggestions.mockResolvedValue(['test', 'testing', 'transcript']);

    render(
      <TestWrapper>
        <SearchInput {...mockProps} />
      </TestWrapper>
    );

    const input = screen.getByPlaceholderText('Search transcripts...');
    await user.type(input, 'test');

    await waitFor(() => {
      expect(screen.getByText('testing')).toBeInTheDocument();
      expect(screen.getByText('transcript')).toBeInTheDocument();
    });
  });
});

describe('SearchResults Component', () => {
  const mockResults = {
    results: [
      {
        job_id: 'job1',
        filename: 'test1.mp3',
        content: 'Hello world this is a test transcript',
        snippet: 'Hello world this is a test transcript',
        metadata: {
          duration: 120.5,
          language: 'en',
          model: 'medium',
          confidence_score: 0.85,
          word_count: 250,
          summary: 'Test summary',
          keywords: ['test', 'hello'],
          sentiment_score: 0.2
        },
        relevance_score: 0.92,
        match_count: 2,
        created_at: '2024-01-01T10:00:00Z'
      }
    ],
    total: 1,
    loading: false
  };

  test('renders search results correctly', () => {
    render(
      <TestWrapper>
        <SearchResults {...mockResults} />
      </TestWrapper>
    );

    expect(screen.getByText('test1.mp3')).toBeInTheDocument();
    expect(screen.getByText('Hello world this is a test transcript')).toBeInTheDocument();
    expect(screen.getByText('2m 0s')).toBeInTheDocument();
    expect(screen.getByText('EN')).toBeInTheDocument();
    expect(screen.getByText('medium')).toBeInTheDocument();
  });

  test('displays result metadata correctly', () => {
    render(
      <TestWrapper>
        <SearchResults {...mockResults} />
      </TestWrapper>
    );

    // Check for metadata chips
    expect(screen.getByText('250 words')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // Confidence
    expect(screen.getByText('92%')).toBeInTheDocument(); // Relevance
  });

  test('shows action buttons', () => {
    render(
      <TestWrapper>
        <SearchResults {...mockResults} />
      </TestWrapper>
    );

    expect(screen.getByLabelText('View transcript')).toBeInTheDocument();
    expect(screen.getByLabelText('Download')).toBeInTheDocument();
    expect(screen.getByLabelText('Share')).toBeInTheDocument();
  });

  test('displays keywords as chips', () => {
    render(
      <TestWrapper>
        <SearchResults {...mockResults} />
      </TestWrapper>
    );

    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('hello')).toBeInTheDocument();
  });

  test('shows sentiment indicator', () => {
    render(
      <TestWrapper>
        <SearchResults {...mockResults} />
      </TestWrapper>
    );

    // Should show positive sentiment (0.2 > 0)
    expect(screen.getByText('😊')).toBeInTheDocument();
  });

  test('handles empty results', () => {
    render(
      <TestWrapper>
        <SearchResults results={[]} total={0} loading={false} />
      </TestWrapper>
    );

    expect(screen.getByText(/no transcripts found/i)).toBeInTheDocument();
  });

  test('shows loading state', () => {
    render(
      <TestWrapper>
        <SearchResults results={[]} total={0} loading={true} />
      </TestWrapper>
    );

    // Should show skeleton loaders
    expect(screen.getAllByTestId('search-result-skeleton')).toHaveLength(3);
  });
});

describe('SearchFilters Component', () => {
  const mockProps = {
    filters: {},
    onFiltersChange: jest.fn(),
    availableFilters: {
      languages: ['en', 'es', 'fr'],
      models: ['tiny', 'base', 'small', 'medium', 'large-v3'],
      duration_range: { min: 1.0, max: 3600.0 }
    },
    loading: false
  };

  test('renders filter sections', () => {
    render(
      <TestWrapper>
        <SearchFilters {...mockProps} />
      </TestWrapper>
    );

    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByText('Whisper Model')).toBeInTheDocument();
    expect(screen.getByText('Date Range')).toBeInTheDocument();
    expect(screen.getByText('Duration')).toBeInTheDocument();
  });

  test('allows language selection', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <SearchFilters {...mockProps} />
      </TestWrapper>
    );

    // Expand language section
    const languageSection = screen.getByText('Language');
    await user.click(languageSection);

    // Select languages
    const languageSelect = screen.getByLabelText('Languages');
    await user.click(languageSelect);
    
    await user.click(screen.getByText('EN'));
    await user.click(screen.getByText('ES'));

    // Should show selected languages as chips
    await waitFor(() => {
      expect(screen.getByText('EN')).toBeInTheDocument();
      expect(screen.getByText('ES')).toBeInTheDocument();
    });
  });

  test('applies filters when Apply button is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <SearchFilters {...mockProps} />
      </TestWrapper>
    );

    // Make a filter change
    const languageSection = screen.getByText('Language');
    await user.click(languageSection);

    const languageSelect = screen.getByLabelText('Languages');
    await user.click(languageSelect);
    await user.click(screen.getByText('EN'));

    // Apply filters button should appear
    const applyButton = await screen.findByText('Apply Filters');
    await user.click(applyButton);

    expect(mockProps.onFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({
        languages: ['en']
      })
    );
  });

  test('clears all filters', async () => {
    const user = userEvent.setup();
    
    const propsWithFilters = {
      ...mockProps,
      filters: { languages: ['en'], models: ['medium'] }
    };

    render(
      <TestWrapper>
        <SearchFilters {...propsWithFilters} />
      </TestWrapper>
    );

    const clearButton = screen.getByText('Clear');
    await user.click(clearButton);

    expect(mockProps.onFiltersChange).toHaveBeenCalledWith({});
  });

  test('shows active filter count', () => {
    const propsWithFilters = {
      ...mockProps,
      filters: { languages: ['en'], models: ['medium'] }
    };

    render(
      <TestWrapper>
        <SearchFilters {...propsWithFilters} />
      </TestWrapper>
    );

    expect(screen.getByText('2')).toBeInTheDocument(); // Filter count chip
  });
});

describe('Search Integration Tests', () => {
  test('full search workflow', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    // Enter search query
    const searchInput = screen.getByPlaceholderText(/search transcripts/i);
    await user.type(searchInput, 'test query');

    // Apply filters
    const languageSection = screen.getByText('Language');
    await user.click(languageSection);

    const languageSelect = screen.getByLabelText('Languages');
    await user.click(languageSelect);
    await user.click(screen.getByText('EN'));

    // Perform search
    await user.keyboard('{Enter}');

    // Verify search was called with correct parameters
    await waitFor(() => {
      expect(transcriptSearchService.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'test query',
          filters: expect.objectContaining({
            languages: ['en']
          })
        })
      );
    });

    // Verify results are displayed
    expect(screen.getByText('test1.mp3')).toBeInTheDocument();
  });

  test('search persistence in URL', async () => {
    const mockNavigate = jest.fn();
    require('react-router-dom').useNavigate.mockReturnValue(mockNavigate);

    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TranscriptSearchPage />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText(/search transcripts/i);
    await user.type(searchInput, 'test query');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        expect.stringContaining('q=test%20query')
      );
    });
  });
});