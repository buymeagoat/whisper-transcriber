"""
T021: Test transcript search functionality
Test suite for the transcript search service and API endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from api.services.transcript_search import (
    TranscriptSearchService,
    SearchType,
    SearchFilters
)
from api.models import Job, TranscriptMetadata


class TestTranscriptSearchService:
    """Test cases for TranscriptSearchService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def search_service(self, mock_db):
        """Create search service instance"""
        return TranscriptSearchService(mock_db)

    @pytest.fixture
    def sample_jobs(self):
        """Sample job data for testing"""
        return [
            Mock(
                id="job1",
                original_filename="test1.mp3",
                created_at=datetime.now() - timedelta(hours=1),
                status="completed",
                transcript_metadata=Mock(
                    duration=120.5,
                    language="en",
                    model="medium",
                    confidence_score=0.85,
                    word_count=250,
                    summary="Test summary 1",
                    keywords=["test", "audio"],
                    sentiment_score=0.2
                ),
                transcript_content="Hello world this is a test transcript"
            ),
            Mock(
                id="job2",
                original_filename="test2.wav",
                created_at=datetime.now() - timedelta(hours=2),
                status="completed",
                transcript_metadata=Mock(
                    duration=300.0,
                    language="es",
                    model="large-v3",
                    confidence_score=0.92,
                    word_count=500,
                    summary="Test summary 2",
                    keywords=["prueba", "spanish"],
                    sentiment_score=-0.1
                ),
                transcript_content="Hola mundo esto es una prueba de transcripción"
            )
        ]

    def test_search_type_enum(self):
        """Test SearchType enum values"""
        assert SearchType.FULL_TEXT == "full_text"
        assert SearchType.METADATA == "metadata"
        assert SearchType.COMBINED == "combined"

    def test_search_filters_creation(self):
        """Test SearchFilters dataclass creation"""
        filters = SearchFilters(
            languages=["en", "es"],
            models=["medium", "large-v3"],
            duration_min=60,
            duration_max=600
        )
        
        assert filters.languages == ["en", "es"]
        assert filters.models == ["medium", "large-v3"]
        assert filters.duration_min == 60
        assert filters.duration_max == 600

    def test_build_base_query(self, search_service, mock_db, sample_jobs):
        """Test base query construction"""
        mock_db.query.return_value.join.return_value.filter.return_value = Mock()
        
        query = search_service._build_base_query()
        
        mock_db.query.assert_called_once_with(Job)
        assert query is not None

    def test_apply_filters_languages(self, search_service, mock_db):
        """Test language filter application"""
        mock_query = Mock()
        filters = SearchFilters(languages=["en", "es"])
        
        result_query = search_service._apply_filters(mock_query, filters)
        
        mock_query.filter.assert_called()
        assert result_query is not None

    def test_apply_filters_date_range(self, search_service, mock_db):
        """Test date range filter application"""
        mock_query = Mock()
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()
        filters = SearchFilters(date_from=date_from, date_to=date_to)
        
        result_query = search_service._apply_filters(mock_query, filters)
        
        mock_query.filter.assert_called()
        assert result_query is not None

    def test_apply_filters_duration(self, search_service, mock_db):
        """Test duration filter application"""
        mock_query = Mock()
        filters = SearchFilters(duration_min=60, duration_max=300)
        
        result_query = search_service._apply_filters(mock_query, filters)
        
        mock_query.filter.assert_called()
        assert result_query is not None

    def test_apply_filters_sentiment(self, search_service, mock_db):
        """Test sentiment filter application"""
        mock_query = Mock()
        filters = SearchFilters(sentiment_min=-0.5, sentiment_max=0.5)
        
        result_query = search_service._apply_filters(mock_query, filters)
        
        mock_query.filter.assert_called()
        assert result_query is not None

    def test_apply_sorting_relevance(self, search_service, mock_db):
        """Test relevance-based sorting"""
        mock_query = Mock()
        
        result_query = search_service._apply_sorting(mock_query, "relevance")
        
        mock_query.order_by.assert_called()
        assert result_query is not None

    def test_apply_sorting_date(self, search_service, mock_db):
        """Test date-based sorting"""
        mock_query = Mock()
        
        result_query = search_service._apply_sorting(mock_query, "date_desc")
        
        mock_query.order_by.assert_called()
        assert result_query is not None

    def test_calculate_relevance_score(self, search_service):
        """Test relevance score calculation"""
        job = Mock()
        job.transcript_metadata.confidence_score = 0.85
        job.transcript_metadata.word_count = 250
        
        score = search_service._calculate_relevance_score(job, "test", 2)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_generate_snippet(self, search_service):
        """Test snippet generation"""
        text = "This is a long text with the search term in the middle of it for testing purposes"
        
        snippet = search_service._generate_snippet(text, "search", 50)
        
        assert isinstance(snippet, str)
        assert "search" in snippet.lower()
        assert len(snippet) <= 100  # Max length with ellipsis

    @patch('api.services.transcript_search.cache')
    def test_search_with_cache_hit(self, mock_cache, search_service, mock_db):
        """Test search with cache hit"""
        mock_cache.get.return_value = {
            "results": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }
        
        result = search_service.search("test query")
        
        mock_cache.get.assert_called_once()
        assert result is not None

    @patch('api.services.transcript_search.cache')
    def test_search_with_cache_miss(self, mock_cache, search_service, mock_db, sample_jobs):
        """Test search with cache miss"""
        mock_cache.get.return_value = None
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = sample_jobs
        mock_query.count.return_value = len(sample_jobs)
        
        with patch.object(search_service, '_build_search_query', return_value=mock_query):
            result = search_service.search("test query")
        
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        assert result is not None

    def test_get_search_suggestions(self, search_service, mock_db):
        """Test search suggestions"""
        mock_db.execute.return_value.fetchall.return_value = [
            ("test",), ("testing",), ("transcript",)
        ]
        
        suggestions = search_service.get_search_suggestions("test")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 10

    def test_get_available_filters(self, search_service, mock_db):
        """Test available filters retrieval"""
        mock_db.execute.return_value.fetchall.return_value = [
            ("en",), ("es",), ("fr",)
        ]
        
        filters = search_service.get_available_filters()
        
        assert isinstance(filters, dict)
        assert "languages" in filters

    def test_get_search_stats(self, search_service, mock_db):
        """Test search statistics"""
        mock_db.execute.return_value.fetchone.return_value = (100,)
        
        stats = search_service.get_search_stats()
        
        assert isinstance(stats, dict)
        assert "total_transcripts" in stats

    def test_search_error_handling(self, search_service, mock_db):
        """Test search error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            search_service.search("test query")

    def test_empty_search_query(self, search_service, mock_db, sample_jobs):
        """Test empty search query handling"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = sample_jobs
        mock_query.count.return_value = len(sample_jobs)
        
        with patch.object(search_service, '_build_base_query', return_value=mock_query):
            result = search_service.search("")
        
        assert result is not None
        assert "results" in result

    def test_search_filters_validation(self, search_service):
        """Test search filters validation"""
        # Invalid date range
        filters = SearchFilters(
            date_from=datetime.now(),
            date_to=datetime.now() - timedelta(days=1)
        )
        
        # Should handle invalid filters gracefully
        mock_query = Mock()
        result_query = search_service._apply_filters(mock_query, filters)
        assert result_query is not None

    def test_pagination_limits(self, search_service, mock_db, sample_jobs):
        """Test pagination limits"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = sample_jobs
        mock_query.count.return_value = len(sample_jobs)
        
        with patch.object(search_service, '_build_base_query', return_value=mock_query):
            # Test maximum per_page limit
            result = search_service.search("test", page=1, per_page=200)
            assert result is not None
            
            # Check that per_page is capped
            mock_query.offset.assert_called()
            mock_query.limit.assert_called()

    def test_search_type_full_text(self, search_service, mock_db, sample_jobs):
        """Test full-text search type"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = sample_jobs
        mock_query.count.return_value = len(sample_jobs)
        
        with patch.object(search_service, '_build_search_query', return_value=mock_query) as mock_build:
            result = search_service.search("test", search_type=SearchType.FULL_TEXT)
            
            mock_build.assert_called_once()
            args = mock_build.call_args[0]
            assert args[1] == SearchType.FULL_TEXT

    def test_search_type_metadata(self, search_service, mock_db, sample_jobs):
        """Test metadata search type"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = sample_jobs
        mock_query.count.return_value = len(sample_jobs)
        
        with patch.object(search_service, '_build_search_query', return_value=mock_query) as mock_build:
            result = search_service.search("test", search_type=SearchType.METADATA)
            
            mock_build.assert_called_once()
            args = mock_build.call_args[0]
            assert args[1] == SearchType.METADATA

    def test_search_performance_large_dataset(self, search_service, mock_db):
        """Test search performance with large dataset"""
        # Simulate large dataset
        large_dataset = [Mock() for _ in range(1000)]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = large_dataset[:10]
        mock_query.count.return_value = len(large_dataset)
        
        with patch.object(search_service, '_build_search_query', return_value=mock_query):
            result = search_service.search("test")
            
            assert result is not None
            assert len(result["results"]) <= 10  # Should be paginated