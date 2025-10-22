"""
T021: Test transcript search API endpoints
Test suite for the search API routes and request handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from api.main import app
from api.services.transcript_search import SearchType, SearchFilters


class TestSearchAPI:
    """Test cases for search API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_search_service(self):
        """Mock search service"""
        return Mock()

    @pytest.fixture
    def sample_search_response(self):
        """Sample search response"""
        return {
            "results": [
                {
                    "job_id": "job1",
                    "filename": "test1.mp3",
                    "content": "Hello world test transcript",
                    "snippet": "Hello world test transcript",
                    "metadata": {
                        "duration": 120.5,
                        "language": "en",
                        "model": "medium",
                        "confidence_score": 0.85,
                        "word_count": 250,
                        "summary": "Test summary",
                        "keywords": ["test", "hello"],
                        "sentiment_score": 0.2
                    },
                    "relevance_score": 0.92,
                    "match_count": 2,
                    "created_at": "2024-01-01T10:00:00Z"
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "total_pages": 1
        }

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_endpoint_success(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test successful search request"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test query",
                "search_type": "full_text",
                "page": 1,
                "per_page": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] == 1
        mock_search_service.search.assert_called_once()

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_with_filters(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search with filters"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test",
                "filters": {
                    "languages": ["en"],
                    "models": ["medium"],
                    "duration_min": 60,
                    "duration_max": 300
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        
        # Verify filters were passed correctly
        call_args = mock_search_service.search.call_args
        assert "filters" in call_args.kwargs

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_with_date_filters(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search with date range filters"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        date_from = "2024-01-01T00:00:00Z"
        date_to = "2024-01-31T23:59:59Z"
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test",
                "filters": {
                    "date_from": date_from,
                    "date_to": date_to
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_invalid_request(self, mock_service_class, client, mock_search_service):
        """Test search with invalid request data"""
        mock_service_class.return_value = mock_search_service
        
        # Test with invalid search_type
        response = client.post(
            "/api/search/",
            json={
                "query": "test",
                "search_type": "invalid_type"
            }
        )
        
        assert response.status_code == 422  # Validation error

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_empty_query(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search with empty query"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        response = client.post(
            "/api/search/",
            json={
                "query": "",
                "page": 1,
                "per_page": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_service_error(self, mock_service_class, client, mock_search_service):
        """Test search service error handling"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.side_effect = Exception("Search service error")
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test"
            }
        )
        
        assert response.status_code == 500

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_suggestions_success(self, mock_service_class, client, mock_search_service):
        """Test search suggestions endpoint"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.get_search_suggestions.return_value = [
            "test", "testing", "transcript"
        ]
        
        response = client.get("/api/search/suggestions?query=test")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_suggestions_empty_query(self, mock_service_class, client, mock_search_service):
        """Test search suggestions with empty query"""
        mock_service_class.return_value = mock_search_service
        
        response = client.get("/api/search/suggestions?query=")
        
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []

    @patch('api.routes.search.TranscriptSearchService')
    def test_quick_search_success(self, mock_service_class, client, mock_search_service):
        """Test quick search endpoint"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = {
            "results": [{"job_id": "job1", "filename": "test.mp3"}],
            "total": 1
        }
        
        response = client.get("/api/search/quick?query=test&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_stats_success(self, mock_service_class, client, mock_search_service):
        """Test search statistics endpoint"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.get_search_stats.return_value = {
            "total_transcripts": 100,
            "languages": {"en": 80, "es": 20},
            "models": {"medium": 60, "large-v3": 40},
            "avg_duration": 180.5,
            "total_duration": 18050.0
        }
        
        response = client.get("/api/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_transcripts" in data
        assert "languages" in data
        assert "models" in data

    @patch('api.routes.search.TranscriptSearchService')
    def test_available_filters_success(self, mock_service_class, client, mock_search_service):
        """Test available filters endpoint"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.get_available_filters.return_value = {
            "languages": ["en", "es", "fr"],
            "models": ["tiny", "base", "small", "medium", "large-v3"],
            "duration_range": {"min": 1.0, "max": 3600.0}
        }
        
        response = client.get("/api/search/filters")
        
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert "models" in data
        assert "duration_range" in data

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_pagination_validation(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search pagination validation"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        # Test invalid page number
        response = client.post(
            "/api/search/",
            json={
                "query": "test",
                "page": 0,
                "per_page": 10
            }
        )
        
        assert response.status_code == 422

        # Test invalid per_page
        response = client.post(
            "/api/search/",
            json={
                "query": "test",
                "page": 1,
                "per_page": 0
            }
        )
        
        assert response.status_code == 422

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_sorting_options(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search sorting options"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        # Test valid sort options
        sort_options = ["relevance", "date_desc", "date_asc", "duration_desc", "duration_asc"]
        
        for sort_by in sort_options:
            response = client.post(
                "/api/search/",
                json={
                    "query": "test",
                    "sort_by": sort_by
                }
            )
            
            assert response.status_code == 200

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_type_validation(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search type validation"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        # Test valid search types
        search_types = ["full_text", "metadata", "combined"]
        
        for search_type in search_types:
            response = client.post(
                "/api/search/",
                json={
                    "query": "test",
                    "search_type": search_type
                }
            )
            
            assert response.status_code == 200

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_response_format(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search response format"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        
        # Check result format
        if data["results"]:
            result = data["results"][0]
            assert "job_id" in result
            assert "filename" in result
            assert "content" in result
            assert "metadata" in result
            assert "relevance_score" in result

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_filter_combinations(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test various filter combinations"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        # Test multiple filter combinations
        filter_combinations = [
            {
                "languages": ["en"],
                "models": ["medium"]
            },
            {
                "duration_min": 60,
                "duration_max": 300,
                "languages": ["en", "es"]
            },
            {
                "date_from": "2024-01-01T00:00:00Z",
                "sentiment_min": -0.5,
                "sentiment_max": 0.5
            },
            {
                "has_keywords": True,
                "has_summary": True
            }
        ]
        
        for filters in filter_combinations:
            response = client.post(
                "/api/search/",
                json={
                    "query": "test",
                    "filters": filters
                }
            )
            
            assert response.status_code == 200

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_performance_metrics(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search performance metrics"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        response = client.post(
            "/api/search/",
            json={
                "query": "test"
            }
        )
        
        assert response.status_code == 200
        
        # Check response time is reasonable (less than 1 second for test)
        assert response.elapsed.total_seconds() < 1.0

    @patch('api.routes.search.TranscriptSearchService')
    def test_search_audit_logging(self, mock_service_class, client, mock_search_service, sample_search_response):
        """Test search audit logging"""
        mock_service_class.return_value = mock_search_service
        mock_search_service.search.return_value = sample_search_response
        
        with patch('api.routes.search.logger') as mock_logger:
            response = client.post(
                "/api/search/",
                json={
                    "query": "test query"
                }
            )
            
            assert response.status_code == 200
            # Verify audit logging was called
            mock_logger.info.assert_called()