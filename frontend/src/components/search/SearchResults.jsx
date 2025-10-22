/**
 * Search Results Component - T021: Implement transcript search functionality
 * 
 * Displays search results with highlighting, metadata, and action buttons.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  IconButton,
  Button,
  Grid,
  Avatar,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  AccessTime as TimeIcon,
  Language as LanguageIcon,
  Psychology as BrainIcon,
  SentimentSatisfied as SentimentPositiveIcon,
  SentimentNeutral as SentimentNeutralIcon,
  SentimentDissatisfied as SentimentNegativeIcon,
  AudioFile as AudioIcon,
  Share as ShareIcon
} from '@mui/icons-material';

const SearchResults = ({
  results = [],
  query,
  onResultClick,
  loading = false
}) => {

  // Get sentiment icon based on score
  const getSentimentIcon = (sentiment) => {
    if (sentiment === null || sentiment === undefined) return null;
    
    if (sentiment > 0.1) return <SentimentPositiveIcon color="success" />;
    if (sentiment < -0.1) return <SentimentNegativeIcon color="error" />;
    return <SentimentNeutralIcon color="warning" />;
  };

  // Format relevance score for display
  const formatRelevanceScore = (score) => {
    return (score * 100).toFixed(1);
  };

  // Create snippet with highlighting
  const createHighlightedSnippet = (snippet, highlightedSnippet) => {
    if (highlightedSnippet) {
      return (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            lineHeight: 1.6,
            '& .search-highlight': {
              backgroundColor: 'warning.light',
              color: 'warning.contrastText',
              padding: '2px 4px',
              borderRadius: '3px',
              fontWeight: 'bold'
            }
          }}
          dangerouslySetInnerHTML={{ __html: highlightedSnippet }}
        />
      );
    }

    return (
      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
        {snippet}
      </Typography>
    );
  };

  // Handle result actions
  const handleDownload = (result, event) => {
    event.stopPropagation();
    // Implementation would download the transcript file
    console.log('Download transcript:', result.job_id);
  };

  const handleView = (result, event) => {
    event.stopPropagation();
    // Implementation would open transcript viewer
    onResultClick(result);
  };

  const handleShare = (result, event) => {
    event.stopPropagation();
    // Implementation would share the transcript
    const shareUrl = `${window.location.origin}/transcript/${result.job_id}`;
    navigator.clipboard.writeText(shareUrl);
  };

  if (results.length === 0) {
    return null;
  }

  return (
    <Box>
      {results.map((result, index) => (
        <Card
          key={result.job_id}
          elevation={1}
          sx={{
            mb: 2,
            cursor: 'pointer',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              elevation: 3,
              transform: 'translateY(-1px)',
              '& .result-actions': {
                opacity: 1
              }
            }
          }}
          onClick={() => onResultClick(result)}
        >
          <CardContent>
            {/* Result Header */}
            <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
              <Box flex={1}>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <AudioIcon color="primary" />
                  <Typography
                    variant="h6"
                    component="h3"
                    sx={{
                      fontWeight: 'medium',
                      color: 'primary.main',
                      '&:hover': { textDecoration: 'underline' }
                    }}
                  >
                    {result.filename}
                  </Typography>
                  <Chip
                    label={`${formatRelevanceScore(result.relevance_score)}% match`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </Box>

                {/* Metadata Row */}
                <Box display="flex" flexWrap="wrap" gap={1} mb={1}>
                  {result.formattedDate && (
                    <Chip
                      icon={<TimeIcon />}
                      label={result.formattedDate}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  
                  {result.formattedDuration && (
                    <Chip
                      label={result.formattedDuration}
                      size="small"
                      variant="outlined"
                    />
                  )}

                  {result.language && (
                    <Chip
                      icon={<LanguageIcon />}
                      label={result.language.toUpperCase()}
                      size="small"
                      variant="outlined"
                    />
                  )}

                  {result.model && (
                    <Chip
                      icon={<BrainIcon />}
                      label={result.model}
                      size="small"
                      variant="outlined"
                    />
                  )}

                  {result.sentiment !== null && result.sentiment !== undefined && (
                    <Tooltip title={`Sentiment: ${result.sentiment.toFixed(2)}`}>
                      <Chip
                        icon={getSentimentIcon(result.sentiment)}
                        label={result.sentiment > 0 ? 'Positive' : result.sentiment < 0 ? 'Negative' : 'Neutral'}
                        size="small"
                        variant="outlined"
                      />
                    </Tooltip>
                  )}
                </Box>
              </Box>

              {/* Action Buttons */}
              <Box 
                className="result-actions"
                sx={{ 
                  opacity: 0.7,
                  transition: 'opacity 0.2s ease-in-out',
                  display: 'flex',
                  gap: 0.5
                }}
              >
                <Tooltip title="View Transcript">
                  <IconButton 
                    size="small" 
                    onClick={(e) => handleView(result, e)}
                    color="primary"
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Download">
                  <IconButton 
                    size="small" 
                    onClick={(e) => handleDownload(result, e)}
                    color="primary"
                  >
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Share">
                  <IconButton 
                    size="small" 
                    onClick={(e) => handleShare(result, e)}
                    color="primary"
                  >
                    <ShareIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            {/* Transcript Snippet */}
            <Box mb={2}>
              {createHighlightedSnippet(result.transcript_snippet, result.highlightedSnippet)}
            </Box>

            {/* Keywords */}
            {result.keywordsList && result.keywordsList.length > 0 && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                  Keywords:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {result.keywordsList.slice(0, 8).map((keyword, idx) => (
                    <Chip
                      key={idx}
                      label={keyword}
                      size="small"
                      sx={{
                        fontSize: '0.75rem',
                        height: '20px',
                        backgroundColor: 'action.hover',
                        '&:hover': {
                          backgroundColor: 'action.selected'
                        }
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        // Could trigger a new search with this keyword
                        console.log('Search for keyword:', keyword);
                      }}
                    />
                  ))}
                  {result.keywordsList.length > 8 && (
                    <Chip
                      label={`+${result.keywordsList.length - 8} more`}
                      size="small"
                      sx={{ fontSize: '0.75rem', height: '20px' }}
                      variant="outlined"
                    />
                  )}
                </Box>
              </Box>
            )}

            {/* Summary (if available and different from snippet) */}
            {result.summary && result.summary !== result.transcript_snippet && (
              <>
                <Divider sx={{ my: 2 }} />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                    Summary:
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    {result.summary.length > 200 ? `${result.summary.substring(0, 200)}...` : result.summary}
                  </Typography>
                </Box>
              </>
            )}
          </CardContent>

          {/* Match Details (if available) */}
          {result.matches && result.matches.length > 0 && (
            <CardActions sx={{ pt: 0, pb: 2, px: 2 }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                  Matches found in:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {result.matches.map((match, idx) => (
                    <Chip
                      key={idx}
                      label={`${match.field || 'content'} (${match.matches?.[0]?.count || match.count || 0})`}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  ))}
                </Box>
              </Box>
            </CardActions>
          )}
        </Card>
      ))}
    </Box>
  );
};

export default SearchResults;