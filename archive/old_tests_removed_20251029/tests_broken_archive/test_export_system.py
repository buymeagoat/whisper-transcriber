"""
T022: Test Multi-Format Export System
Comprehensive test suite for transcript export functionality
"""

import pytest
import json
import io
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from api.services.transcript_export import (
    TranscriptExportService,
    ExportFormat,
    ExportOptions,
    ExportTemplate,
    ExportResult
)
from api.models import Job, TranscriptMetadata


class TestTranscriptExportService:
    """Test cases for TranscriptExportService"""

    @pytest.fixture
    def export_service(self):
        """Create export service instance"""
        return TranscriptExportService()

    @pytest.fixture
    def sample_job(self):
        """Sample job with transcript data"""
        job = Mock(spec=Job)
        job.id = "job123"
        job.original_filename = "test_audio.mp3"
        job.created_at = datetime.now()
        job.status = "completed"
        job.transcript_content = """Hello, this is a test transcript.
It contains multiple lines of text.
Each line represents a segment of the audio.
This is useful for testing export formats."""

        # Mock transcript metadata
        metadata = Mock(spec=TranscriptMetadata)
        metadata.duration = 125.5
        metadata.language = "en"
        metadata.model = "medium"
        metadata.confidence_score = 0.87
        metadata.word_count = 28
        metadata.summary = "A test transcript for export testing"
        metadata.keywords = ["test", "transcript", "export"]
        metadata.sentiment_score = 0.1
        metadata.file_size = 2048000
        metadata.audio_format = "mp3"
        metadata.sample_rate = 44100
        metadata.channels = 2

        job.transcript_metadata = metadata
        return job

    def test_export_format_enum(self):
        """Test ExportFormat enum values"""
        assert ExportFormat.SRT.value == "srt"
        assert ExportFormat.VTT.value == "vtt"
        assert ExportFormat.DOCX.value == "docx"
        assert ExportFormat.PDF.value == "pdf"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.TXT.value == "txt"

    def test_export_template_creation(self):
        """Test ExportTemplate dataclass"""
        template = ExportTemplate(
            name="Test Template",
            format=ExportFormat.SRT,
            description="Test template for SRT",
            include_timestamps=True,
            include_metadata=False
        )
        
        assert template.name == "Test Template"
        assert template.format == ExportFormat.SRT
        assert template.include_timestamps is True
        assert template.include_metadata is False

    def test_export_options_defaults(self):
        """Test ExportOptions with default values"""
        options = ExportOptions()
        
        assert options.include_header is True
        assert options.include_footer is True
        assert options.word_wrap == 80
        assert options.font_size == 12
        assert options.font_family == "Arial"
        assert options.line_spacing == 1.5
        assert options.page_margins == {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}

    def test_get_available_formats(self, export_service):
        """Test getting available export formats"""
        formats = export_service.get_available_formats()
        
        assert isinstance(formats, list)
        assert len(formats) >= 4  # At least SRT, VTT, JSON, TXT
        
        # Check format structure
        for fmt in formats:
            assert "format" in fmt
            assert "name" in fmt
            assert "available" in fmt
            assert "description" in fmt
            assert "requires" in fmt

    def test_get_templates(self, export_service):
        """Test getting export templates"""
        templates = export_service.get_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check template structure
        for template in templates:
            assert "name" in template
            assert "format" in template
            assert "description" in template
            assert "include_timestamps" in template
            assert "include_metadata" in template

    def test_get_templates_filtered(self, export_service):
        """Test getting templates filtered by format"""
        srt_templates = export_service.get_templates(ExportFormat.SRT)
        
        assert isinstance(srt_templates, list)
        for template in srt_templates:
            assert template["format"] == "srt"

    def test_export_srt_format(self, export_service, sample_job):
        """Test SRT format export"""
        result = export_service.export_transcript(sample_job, ExportFormat.SRT)
        
        assert result.success is True
        assert result.format == ExportFormat.SRT
        assert result.filename.endswith(".srt")
        assert result.content is not None
        
        # Check SRT format structure
        lines = result.content.split('\n')
        assert len(lines) > 0
        # Should contain subtitle numbers and timestamps
        assert any(line.strip().isdigit() for line in lines)
        assert any("-->" in line for line in lines)

    def test_export_vtt_format(self, export_service, sample_job):
        """Test VTT format export"""
        result = export_service.export_transcript(sample_job, ExportFormat.VTT)
        
        assert result.success is True
        assert result.format == ExportFormat.VTT
        assert result.filename.endswith(".vtt")
        assert result.content.startswith("WEBVTT")
        
        # Check for timestamps
        assert "-->" in result.content

    def test_export_json_format(self, export_service, sample_job):
        """Test JSON format export"""
        result = export_service.export_transcript(sample_job, ExportFormat.JSON)
        
        assert result.success is True
        assert result.format == ExportFormat.JSON
        assert result.filename.endswith(".json")
        
        # Parse JSON to verify structure
        data = json.loads(result.content)
        assert "job_id" in data
        assert "original_filename" in data
        assert "transcript_content" in data
        assert data["job_id"] == sample_job.id

    def test_export_txt_format(self, export_service, sample_job):
        """Test TXT format export"""
        result = export_service.export_transcript(sample_job, ExportFormat.TXT)
        
        assert result.success is True
        assert result.format == ExportFormat.TXT
        assert result.filename.endswith(".txt")
        assert sample_job.original_filename in result.content

    def test_export_with_custom_options(self, export_service, sample_job):
        """Test export with custom options"""
        options = ExportOptions(
            custom_filename="custom_export.srt",
            font_size=14,
            word_wrap=100
        )
        
        result = export_service.export_transcript(sample_job, ExportFormat.SRT, options)
        
        assert result.success is True
        assert "custom_export.srt" in result.filename

    def test_export_with_template(self, export_service, sample_job):
        """Test export with specific template"""
        template = ExportTemplate(
            name="Custom Template",
            format=ExportFormat.JSON,
            description="Custom JSON template",
            include_metadata=True,
            include_summary=True,
            include_keywords=True
        )
        
        options = ExportOptions(template=template)
        result = export_service.export_transcript(sample_job, ExportFormat.JSON, options)
        
        assert result.success is True
        data = json.loads(result.content)
        assert "metadata" in data
        assert "summary" in data["metadata"]
        assert "keywords" in data["metadata"]

    def test_export_without_transcript_content(self, export_service):
        """Test export fails when no transcript content"""
        job = Mock(spec=Job)
        job.transcript_content = None
        
        result = export_service.export_transcript(job, ExportFormat.SRT)
        
        assert result.success is False
        assert "No transcript content" in result.error

    def test_export_unsupported_format(self, export_service, sample_job):
        """Test export with unavailable format"""
        # Mock DOCX as unavailable
        with patch.object(export_service, 'export_handlers', {ExportFormat.SRT: export_service._export_srt}):
            result = export_service.export_transcript(sample_job, ExportFormat.DOCX)
            
            assert result.success is False
            assert "not available" in result.error

    def test_filename_generation(self, export_service, sample_job):
        """Test filename generation"""
        filename = export_service._generate_filename(sample_job, ExportFormat.SRT)
        
        assert filename.endswith(".srt")
        assert "test_audio" in filename
        assert "transcript" in filename

    def test_custom_filename_with_extension(self, export_service, sample_job):
        """Test custom filename with proper extension"""
        filename = export_service._generate_filename(
            sample_job, 
            ExportFormat.SRT, 
            "my_export.srt"
        )
        
        assert filename == "my_export.srt"

    def test_custom_filename_without_extension(self, export_service, sample_job):
        """Test custom filename gets proper extension"""
        filename = export_service._generate_filename(
            sample_job, 
            ExportFormat.SRT, 
            "my_export"
        )
        
        assert filename == "my_export.srt"

    def test_srt_time_formatting(self, export_service):
        """Test SRT time format conversion"""
        time_str = export_service._seconds_to_srt_time(125.5)
        assert time_str == "00:02:05,500"
        
        time_str = export_service._seconds_to_srt_time(3725.123)
        assert time_str == "01:02:05,123"

    def test_vtt_time_formatting(self, export_service):
        """Test VTT time format conversion"""
        time_str = export_service._seconds_to_vtt_time(125.5)
        assert time_str == "00:02:05.500"
        
        time_str = export_service._seconds_to_vtt_time(3725.123)
        assert time_str == "01:02:05.123"

    def test_duration_formatting(self, export_service):
        """Test duration formatting for display"""
        assert export_service._format_duration(65) == "01:05"
        assert export_service._format_duration(3665) == "01:01:05"
        assert export_service._format_duration(45) == "00:45"

    def test_export_metadata_creation(self, export_service, sample_job):
        """Test export metadata structure"""
        options = ExportOptions()
        metadata = export_service._create_export_metadata(sample_job, ExportFormat.SRT, options)
        
        assert metadata["job_id"] == sample_job.id
        assert metadata["original_filename"] == sample_job.original_filename
        assert metadata["export_format"] == "srt"
        assert "export_timestamp" in metadata
        assert "transcript_metadata" in metadata
        assert metadata["transcript_metadata"]["duration"] == 125.5

    @patch('api.services.transcript_export.Document')
    def test_docx_export_with_library(self, mock_document, export_service, sample_job):
        """Test DOCX export when library is available"""
        with patch('api.services.transcript_export.DOCX_AVAILABLE', True):
            # Mock document creation
            mock_doc = Mock()
            mock_document.return_value = mock_doc
            mock_doc.save = Mock()
            
            result = export_service.export_transcript(sample_job, ExportFormat.DOCX)
            
            # Should attempt to create document
            mock_document.assert_called_once()

    @patch('api.services.transcript_export.SimpleDocTemplate')
    def test_pdf_export_with_library(self, mock_doc_template, export_service, sample_job):
        """Test PDF export when library is available"""
        with patch('api.services.transcript_export.PDF_AVAILABLE', True):
            # Mock PDF creation
            mock_doc = Mock()
            mock_doc_template.return_value = mock_doc
            mock_doc.build = Mock()
            
            result = export_service.export_transcript(sample_job, ExportFormat.PDF)
            
            # Should attempt to create PDF
            mock_doc_template.assert_called_once()

    def test_export_result_structure(self, export_service, sample_job):
        """Test ExportResult structure and content"""
        result = export_service.export_transcript(sample_job, ExportFormat.JSON)
        
        assert isinstance(result, ExportResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'format')
        assert hasattr(result, 'filename')
        assert hasattr(result, 'file_size')
        assert hasattr(result, 'content')
        assert hasattr(result, 'metadata')
        
        assert result.success is True
        assert result.format == ExportFormat.JSON
        assert result.file_size > 0
        assert result.content is not None

    def test_export_with_missing_metadata(self, export_service):
        """Test export when transcript metadata is missing"""
        job = Mock(spec=Job)
        job.id = "job123"
        job.original_filename = "test.mp3"
        job.created_at = datetime.now()
        job.status = "completed"
        job.transcript_content = "Test content"
        job.transcript_metadata = None
        
        result = export_service.export_transcript(job, ExportFormat.TXT)
        
        assert result.success is True
        # Should handle missing metadata gracefully

    def test_export_service_singleton(self):
        """Test that export service singleton is properly configured"""
        from api.services.transcript_export import transcript_export_service
        
        assert isinstance(transcript_export_service, TranscriptExportService)
        assert hasattr(transcript_export_service, 'export_handlers')
        assert hasattr(transcript_export_service, 'default_templates')

    def test_word_wrapping_in_txt_export(self, export_service, sample_job):
        """Test word wrapping functionality in TXT export"""
        # Create job with long text
        sample_job.transcript_content = "This is a very long line of text that should be wrapped when the word wrap limit is exceeded in the text export format."
        
        options = ExportOptions(word_wrap=50)
        result = export_service.export_transcript(sample_job, ExportFormat.TXT, options)
        
        assert result.success is True
        lines = result.content.split('\n')
        # Find content lines (skip header)
        content_lines = [line for line in lines if "This is a very long" in line or "when the word wrap" in line]
        assert len(content_lines) > 1  # Should be split into multiple lines

    def test_template_filtering_by_format(self, export_service):
        """Test template filtering by export format"""
        all_templates = export_service.get_templates()
        srt_templates = export_service.get_templates(ExportFormat.SRT)
        
        assert len(srt_templates) <= len(all_templates)
        for template in srt_templates:
            assert template["format"] == "srt"

    def test_export_error_handling(self, export_service, sample_job):
        """Test error handling in export process"""
        # Mock an export method to raise an exception
        with patch.object(export_service, '_export_srt', side_effect=Exception("Test error")):
            result = export_service.export_transcript(sample_job, ExportFormat.SRT)
            
            assert result.success is False
            assert "Test error" in result.error