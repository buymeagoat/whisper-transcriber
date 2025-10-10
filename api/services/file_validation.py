"""
File Upload Validation Service

Provides comprehensive validation for uploaded files including:
- MIME type checking
- File size validation
- Content validation
- File extension validation
- Security checks
"""

import magic
import os
from pathlib import Path
from typing import BinaryIO, Tuple, Optional
from fastapi import HTTPException, UploadFile
from api.settings import settings
from api.utils.logger import get_logger

logger = get_logger("file_validation")

# Allowed MIME types for audio files
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp3", "audio/x-mp3",
    "audio/mp4", "audio/m4a", "audio/x-m4a",
    "audio/flac", "audio/x-flac",
    "audio/ogg", "audio/vorbis",
    "audio/webm",
    "audio/aac",
    "video/mp4",  # MP4 containers with audio
    "video/quicktime",  # MOV files
    "video/x-msvideo",  # AVI files
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".mov", ".avi"
}

# Maximum file size (2GB by default)
MAX_FILE_SIZE = settings.max_upload_size

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

class FileValidator:
    """Comprehensive file validator for uploads"""
    
    def __init__(self):
        # Initialize libmagic for MIME type detection
        try:
            self.magic_mime = magic.Magic(mime=True)
        except Exception as e:
            logger.warning(f"Could not initialize libmagic: {e}. MIME type detection may be limited.")
            self.magic_mime = None
    
    def validate_file_size(self, file: UploadFile) -> None:
        """Validate file size doesn't exceed limits"""
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            # Get current position
            current_pos = file.file.tell()
            # Seek to end to get file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            # Reset to original position
            file.file.seek(current_pos)
            
            if file_size > MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = MAX_FILE_SIZE / (1024 * 1024)
                raise FileValidationError(
                    f"File size ({size_mb:.1f}MB) exceeds maximum allowed size ({max_mb:.1f}MB)"
                )
            
            if file_size == 0:
                raise FileValidationError("Empty files are not allowed")
    
    def validate_filename(self, filename: str) -> None:
        """Validate filename and extension"""
        if not filename:
            raise FileValidationError("Filename is required")
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in filename for char in dangerous_chars):
            raise FileValidationError("Filename contains invalid characters")
        
        # Check extension
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if not extension:
            raise FileValidationError("File must have an extension")
        
        if extension not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise FileValidationError(
                f"File extension '{extension}' not allowed. Allowed extensions: {allowed_list}"
            )
    
    def validate_mime_type(self, file_content: bytes, filename: str) -> str:
        """Validate MIME type using content analysis"""
        detected_mime = None
        
        if self.magic_mime:
            try:
                detected_mime = self.magic_mime.from_buffer(file_content[:1024])
            except Exception as e:
                logger.warning(f"MIME detection failed for {filename}: {e}")
        
        # Fallback to extension-based validation if libmagic fails
        if not detected_mime:
            extension = Path(filename).suffix.lower()
            extension_mime_map = {
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg",
                ".mp4": "audio/mp4",
                ".m4a": "audio/m4a",
                ".flac": "audio/flac",
                ".ogg": "audio/ogg",
                ".webm": "audio/webm",
                ".aac": "audio/aac",
                ".mov": "video/quicktime",
                ".avi": "video/x-msvideo"
            }
            detected_mime = extension_mime_map.get(extension)
        
        if not detected_mime or detected_mime not in ALLOWED_AUDIO_MIME_TYPES:
            allowed_types = ", ".join(sorted(ALLOWED_AUDIO_MIME_TYPES))
            raise FileValidationError(
                f"Invalid file type. Detected: {detected_mime}. Allowed types: {allowed_types}"
            )
        
        return detected_mime
    
    def validate_content_headers(self, file_content: bytes, filename: str) -> None:
        """Validate file content headers for common audio formats"""
        if len(file_content) < 12:
            raise FileValidationError("File too small to be a valid audio file")
        
        # Check for common audio file signatures
        header = file_content[:12]
        
        # WAV file signature
        if header.startswith(b'RIFF') and b'WAVE' in header:
            return
        
        # MP3 file signature (ID3v2 or MPEG frame)
        if (header.startswith(b'ID3') or 
            header.startswith(b'\xff\xfb') or 
            header.startswith(b'\xff\xfa')):
            return
        
        # MP4/M4A file signature
        if b'ftyp' in header[:12]:
            return
        
        # FLAC file signature
        if header.startswith(b'fLaC'):
            return
        
        # OGG file signature
        if header.startswith(b'OggS'):
            return
        
        # WebM signature
        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return
        
        # If we get here, the file doesn't match expected headers
        extension = Path(filename).suffix.lower()
        logger.warning(f"File {filename} with extension {extension} has unexpected content headers")
        # Don't fail here as some valid files might have non-standard headers
    
    def scan_for_malicious_content(self, file_content: bytes, filename: str) -> None:
        """Basic scan for potentially malicious content"""
        # Check for executable signatures
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'\xca\xfe\xba\xbe',  # Java class file
            b'PK\x03\x04',  # ZIP archive (could contain malicious files)
        ]
        
        header = file_content[:16]
        for sig in dangerous_signatures:
            if header.startswith(sig):
                raise FileValidationError(
                    f"File appears to contain executable content which is not allowed"
                )
    
    async def validate_upload(self, file: UploadFile) -> Tuple[str, str]:
        """
        Comprehensive validation of uploaded file
        
        Returns:
            Tuple of (validated_filename, detected_mime_type)
        
        Raises:
            FileValidationError: If validation fails
        """
        try:
            # Basic filename validation
            self.validate_filename(file.filename)
            
            # Size validation
            self.validate_file_size(file)
            
            # Read file content for analysis
            file_content = await file.read()
            
            # Reset file pointer for later use
            await file.seek(0)
            
            # MIME type validation
            detected_mime = self.validate_mime_type(file_content, file.filename)
            
            # Content header validation
            self.validate_content_headers(file_content, file.filename)
            
            # Security scan
            self.scan_for_malicious_content(file_content, file.filename)
            
            # Sanitize filename
            safe_filename = self._sanitize_filename(file.filename)
            
            logger.info(f"File validation passed for {safe_filename} (type: {detected_mime})")
            return safe_filename, detected_mime
            
        except FileValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during file validation: {e}")
            raise FileValidationError(f"File validation failed: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace problematic characters
        safe_name = filename.replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        
        # Ensure it's not too long
        if len(safe_name) > 255:
            name_part = Path(safe_name).stem[:200]
            ext_part = Path(safe_name).suffix
            safe_name = f"{name_part}{ext_part}"
        
        return safe_name

# Global validator instance
file_validator = FileValidator()
