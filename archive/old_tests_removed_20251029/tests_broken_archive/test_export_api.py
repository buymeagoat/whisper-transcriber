"""
T022: Test Export API Endpoints
Test suite for export API routes and request handling
"""

import pytest
import json
import io
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app
from api.services.transcript_export import ExportFormat, ExportResult


class TestExportAPI:
    """Test cases for export API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        user = Mock()
        user.id = "user123"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_job(self):
        """Mock completed job"""
        job = Mock()
        job.id = "job123"
        job.user_id = "user123"
        job.status = "completed"
        job.original_filename = "test_audio.mp3"
        job.transcript_content = "Test transcript content"
        job.created_at = datetime.now()
        
        # Mock metadata
        metadata = Mock()
        metadata.duration = 120.5
        metadata.language = "en"
        metadata.model = "medium"
        metadata.confidence_score = 0.85
        job.transcript_metadata = metadata
        
        return job

    @pytest.fixture
    def mock_export_service(self):
        """Mock export service"""
        return Mock()

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    def test_get_available_formats(self, mock_service, mock_auth, client, mock_user):
        """Test getting available export formats"""
        mock_auth.return_value = mock_user
        mock_service.get_available_formats.return_value = [
            {
                "format": "srt",
                "name": "SRT",
                "available": True,
                "description": "SubRip subtitle format",
                "requires": []
            }
        ]
        
        response = client.get("/api/export/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["format"] == "srt"

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    def test_get_export_templates(self, mock_service, mock_auth, client, mock_user):
        """Test getting export templates"""
        mock_auth.return_value = mock_user
        mock_service.get_templates.return_value = [
            {
                "name": "Standard SRT",
                "format": "srt",
                "description": "Standard subtitle format",
                "include_timestamps": True,
                "include_metadata": False,
                "include_summary": False,
                "include_keywords": False
            }
        ]
        
        response = client.get("/api/export/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Standard SRT"

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_export_transcript_success(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test successful transcript export"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock successful export result
        export_result = ExportResult(
            success=True,
            format=ExportFormat.SRT,
            filename="test_export.srt",
            file_size=1024,
            content="Mock SRT content",
            metadata={"job_id": "job123"}
        )
        mock_service.export_transcript.return_value = export_result
        
        request_data = {
            "job_id": "job123",
            "format": "srt"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "srt"
        assert data["filename"] == "test_export.srt"
        assert data["file_size"] == 1024

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.get_db')
    def test_export_job_not_found(self, mock_db, mock_auth, client, mock_user):
        """Test export with non-existent job"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = None
        
        request_data = {
            "job_id": "nonexistent",
            "format": "srt"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.get_db')
    def test_export_job_not_completed(self, mock_db, mock_auth, client, mock_user, mock_job):
        """Test export with incomplete job"""
        mock_auth.return_value = mock_user
        mock_job.status = "processing"
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        request_data = {
            "job_id": "job123",
            "format": "srt"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"]

    @patch('api.routes.export.get_current_user')
    def test_export_invalid_format(self, mock_auth, client, mock_user):
        """Test export with invalid format"""
        mock_auth.return_value = mock_user
        
        request_data = {
            "job_id": "job123",
            "format": "invalid_format"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid export format" in response.json()["detail"]

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_download_export(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test downloading exported file"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock successful export result
        export_result = ExportResult(
            success=True,
            format=ExportFormat.SRT,
            filename="test_export.srt",
            file_size=1024,
            content="1\n00:00:00,000 --> 00:00:05,000\nTest content",
            metadata={}
        )
        mock_service.export_transcript.return_value = export_result
        
        response = client.get("/api/export/download/job123/srt")
        
        assert response.status_code == 200
        assert response.headers["content-disposition"]
        assert "test_export.srt" in response.headers["content-disposition"]

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_batch_export_success(self, mock_db, mock_service, mock_auth, client, mock_user):
        """Test successful batch export"""
        mock_auth.return_value = mock_user
        
        # Mock multiple jobs
        jobs = []
        for i in range(3):
            job = Mock()
            job.id = f"job{i}"
            job.user_id = "user123"
            job.status = "completed"
            job.original_filename = f"test{i}.mp3"
            jobs.append(job)
        
        mock_db.return_value.query.return_value.filter.return_value.all.return_value = jobs
        
        # Mock batch export result
        mock_service.batchExport = Mock()
        
        request_data = {
            "job_ids": ["job0", "job1", "job2"],
            "format": "srt"
        }
        
        with patch('zipfile.ZipFile'):
            response = client.post("/api/export/batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "batch_id" in data

    @patch('api.routes.export.get_current_user')
    def test_batch_export_too_many_jobs(self, mock_auth, client, mock_user):
        """Test batch export with too many jobs"""
        mock_auth.return_value = mock_user
        
        request_data = {
            "job_ids": [f"job{i}" for i in range(51)],  # 51 jobs (exceeds limit of 50)
            "format": "srt"
        }
        
        response = client.post("/api/export/batch", json=request_data)
        
        assert response.status_code == 400
        assert "Maximum 50 jobs" in response.json()["detail"]

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_preview_export(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test export preview generation"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock preview result
        export_result = ExportResult(
            success=True,
            format=ExportFormat.SRT,
            filename="preview.srt",
            file_size=512,
            content="1\n00:00:00,000 --> 00:00:05,000\nPreview content",
            metadata={}
        )
        mock_service.export_transcript.return_value = export_result
        
        response = client.get("/api/export/preview/job123/srt?lines=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["format"] == "srt"
        assert "preview" in data
        assert data["lines_shown"] == 5

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.get_db')
    def test_get_export_stats(self, mock_db, mock_auth, client, mock_user):
        """Test getting export statistics"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.count.return_value = 10
        
        with patch('api.routes.export.transcript_export_service') as mock_service:
            mock_service.get_available_formats.return_value = [
                {"format": "srt", "available": True, "requires": []},
                {"format": "vtt", "available": True, "requires": []}
            ]
            mock_service.get_templates.return_value = [
                {"name": "Template 1"}, {"name": "Template 2"}
            ]
            
            response = client.get("/api/export/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "available_jobs" in data
        assert "available_formats" in data
        assert "available_templates" in data
        assert "batch_limit" in data
        assert data["batch_limit"] == 50

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    def test_export_service_error(self, mock_service, mock_auth, client, mock_user):
        """Test handling of export service errors"""
        mock_auth.return_value = mock_user
        mock_service.get_available_formats.side_effect = Exception("Service error")
        
        response = client.get("/api/export/formats")
        
        assert response.status_code == 500

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_export_with_template(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test export with specific template"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock template lookup
        mock_service.get_templates.return_value = [
            {
                "name": "Custom Template",
                "format": "srt",
                "description": "Custom SRT template",
                "include_timestamps": True,
                "include_metadata": True,
                "include_summary": False,
                "include_keywords": False
            }
        ]
        
        # Mock successful export
        export_result = ExportResult(
            success=True,
            format=ExportFormat.SRT,
            filename="test_export.srt",
            file_size=1024,
            content="Mock content",
            metadata={}
        )
        mock_service.export_transcript.return_value = export_result
        
        request_data = {
            "job_id": "job123",
            "format": "srt",
            "template_name": "Custom Template"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 200
        # Verify template was used
        mock_service.export_transcript.assert_called_once()

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_export_with_custom_options(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test export with custom options"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock successful export
        export_result = ExportResult(
            success=True,
            format=ExportFormat.TXT,
            filename="custom_export.txt",
            file_size=2048,
            content="Custom formatted content",
            metadata={}
        )
        mock_service.export_transcript.return_value = export_result
        
        request_data = {
            "job_id": "job123",
            "format": "txt",
            "custom_filename": "my_custom_export.txt",
            "options": {
                "font_size": 14,
                "word_wrap": 100,
                "font_family": "Courier New"
            }
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch('api.routes.export.get_current_user')
    def test_templates_filtered_by_format(self, mock_auth, client, mock_user):
        """Test template filtering by format parameter"""
        mock_auth.return_value = mock_user
        
        with patch('api.routes.export.transcript_export_service') as mock_service:
            mock_service.get_templates.return_value = [
                {"name": "SRT Template", "format": "srt"}
            ]
            
            response = client.get("/api/export/templates?format=srt")
        
        assert response.status_code == 200
        mock_service.get_templates.assert_called_once()

    def test_request_validation(self, client):
        """Test request validation for export endpoints"""
        # Missing required fields
        response = client.post("/api/export/export", json={})
        assert response.status_code == 422
        
        # Invalid field types
        response = client.post("/api/export/export", json={
            "job_id": 123,  # Should be string
            "format": "srt"
        })
        assert response.status_code == 422

    @patch('api.routes.export.get_current_user')
    @patch('api.routes.export.transcript_export_service')
    @patch('api.routes.export.get_db')
    def test_export_failure_handling(self, mock_db, mock_service, mock_auth, client, mock_user, mock_job):
        """Test handling of export failures"""
        mock_auth.return_value = mock_user
        mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Mock failed export
        export_result = ExportResult(
            success=False,
            format=ExportFormat.SRT,
            filename="",
            file_size=0,
            error="Export processing failed"
        )
        mock_service.export_transcript.return_value = export_result
        
        request_data = {
            "job_id": "job123",
            "format": "srt"
        }
        
        response = client.post("/api/export/export", json=request_data)
        
        assert response.status_code == 500
        assert "Export failed" in response.json()["detail"]