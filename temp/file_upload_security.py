#!/usr/bin/env python3
"""
T026 Security Hardening: File Upload Security System
Implements comprehensive file upload security validation to prevent malicious file uploads.
"""

import os
import mimetypes
import hashlib
import magic
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
import logging
from datetime import datetime

# File type detection libraries
try:
    import filetype
except ImportError:
    filetype = None

logger = logging.getLogger("file_upload_security")

@dataclass
class FileSecurityConfig:
    """Configuration for file upload security."""
    
    # File size limits (in bytes)
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    max_audio_file_size: int = 500 * 1024 * 1024  # 500MB for audio
    max_document_size: int = 10 * 1024 * 1024  # 10MB for documents
    max_image_size: int = 5 * 1024 * 1024  # 5MB for images
    
    # Allowed file extensions
    allowed_audio_extensions: Set[str] = field(default_factory=lambda: {
        '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'
    })
    allowed_document_extensions: Set[str] = field(default_factory=lambda: {
        '.txt', '.pdf', '.doc', '.docx', '.rtf'
    })
    allowed_image_extensions: Set[str] = field(default_factory=lambda: {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
    })
    
    # Allowed MIME types
    allowed_audio_mimes: Set[str] = field(default_factory=lambda: {
        'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/flac', 
        'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/x-ms-wma'
    })
    allowed_document_mimes: Set[str] = field(default_factory=lambda: {
        'text/plain', 'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/rtf'
    })
    allowed_image_mimes: Set[str] = field(default_factory=lambda: {
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
    })
    
    # Blocked extensions (security threats)
    blocked_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl',
        '.sh', '.bash', '.ps1', '.msi', '.dll', '.so', '.dylib'
    })
    
    # Blocked MIME types
    blocked_mimes: Set[str] = field(default_factory=lambda: {
        'application/x-executable', 'application/x-msdownload',
        'application/x-dosexec', 'application/java-archive',
        'text/x-php', 'text/x-python', 'text/x-shellscript'
    })
    
    # Content validation settings
    enable_content_scanning: bool = True
    enable_virus_scanning: bool = False  # Requires ClamAV
    enable_metadata_stripping: bool = True
    
    # Path security settings
    allowed_upload_dirs: Set[str] = field(default_factory=lambda: {
        '/tmp/uploads', '/var/uploads', './uploads', './temp'
    })
    enable_path_traversal_protection: bool = True
    
    # Advanced security features
    enable_file_quarantine: bool = True
    quarantine_duration: int = 3600  # 1 hour
    enable_hash_tracking: bool = True
    max_duplicate_uploads: int = 5

class FileSecurityValidator:
    """Comprehensive file upload security validator."""
    
    def __init__(self, config: FileSecurityConfig):
        self.config = config
        self.quarantine_dir = Path("./quarantine")
        self.quarantine_dir.mkdir(exist_ok=True)
        self.uploaded_hashes: Dict[str, List[datetime]] = {}
        
        # Initialize magic for MIME type detection
        try:
            self.magic_mime = magic.Magic(mime=True)
        except:
            logger.warning("python-magic not available, using fallback MIME detection")
            self.magic_mime = None
    
    def validate_file(self, file_path: str, file_type: str = "audio") -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive file validation.
        
        Args:
            file_path: Path to the file to validate
            file_type: Expected file type ("audio", "document", "image")
            
        Returns:
            Tuple of (is_valid, errors, metadata)
        """
        errors = []
        metadata = {}
        
        try:
            file_path_obj = Path(file_path)
            
            # Basic file existence check
            if not file_path_obj.exists():
                errors.append("File does not exist")
                return False, errors, metadata
            
            # File size validation
            file_size = file_path_obj.stat().st_size
            metadata['file_size'] = file_size
            
            if not self._validate_file_size(file_size, file_type):
                max_size = self._get_max_size_for_type(file_type)
                errors.append(f"File size {file_size} exceeds maximum {max_size} bytes")
            
            # Extension validation
            file_extension = file_path_obj.suffix.lower()
            metadata['extension'] = file_extension
            
            if not self._validate_extension(file_extension, file_type):
                errors.append(f"File extension '{file_extension}' not allowed for {file_type} files")
            
            # MIME type validation
            detected_mime = self._detect_mime_type(file_path_obj)
            metadata['mime_type'] = detected_mime
            
            if not self._validate_mime_type(detected_mime, file_type):
                errors.append(f"MIME type '{detected_mime}' not allowed for {file_type} files")
            
            # Content validation
            if self.config.enable_content_scanning:
                content_errors = self._scan_file_content(file_path_obj)
                errors.extend(content_errors)
            
            # Path traversal protection
            if self.config.enable_path_traversal_protection:
                if not self._validate_file_path(file_path_obj):
                    errors.append("File path contains unsafe characters")
            
            # Hash tracking for duplicate detection
            if self.config.enable_hash_tracking:
                file_hash = self._calculate_file_hash(file_path_obj)
                metadata['hash'] = file_hash
                
                if not self._validate_hash_limits(file_hash):
                    errors.append("Too many uploads of this file")
            
            # Advanced security checks
            security_errors = self._perform_security_checks(file_path_obj)
            errors.extend(security_errors)
            
            # Log validation attempt
            self._log_validation_attempt(file_path_obj, errors, metadata)
            
            return len(errors) == 0, errors, metadata
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors, metadata
    
    def _validate_file_size(self, size: int, file_type: str) -> bool:
        """Validate file size against limits."""
        if file_type == "audio":
            return size <= self.config.max_audio_file_size
        elif file_type == "document":
            return size <= self.config.max_document_size
        elif file_type == "image":
            return size <= self.config.max_image_size
        else:
            return size <= self.config.max_file_size
    
    def _get_max_size_for_type(self, file_type: str) -> int:
        """Get maximum file size for file type."""
        if file_type == "audio":
            return self.config.max_audio_file_size
        elif file_type == "document":
            return self.config.max_document_size
        elif file_type == "image":
            return self.config.max_image_size
        else:
            return self.config.max_file_size
    
    def _validate_extension(self, extension: str, file_type: str) -> bool:
        """Validate file extension."""
        # Check blocked extensions first
        if extension in self.config.blocked_extensions:
            return False
        
        # Check allowed extensions for file type
        if file_type == "audio":
            return extension in self.config.allowed_audio_extensions
        elif file_type == "document":
            return extension in self.config.allowed_document_extensions
        elif file_type == "image":
            return extension in self.config.allowed_image_extensions
        
        return False
    
    def _detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type using multiple methods."""
        # Try python-magic first (most reliable)
        if self.magic_mime:
            try:
                return self.magic_mime.from_file(str(file_path))
            except:
                pass
        
        # Try filetype library
        if filetype:
            try:
                kind = filetype.guess(str(file_path))
                if kind:
                    return kind.mime
            except:
                pass
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"
    
    def _validate_mime_type(self, mime_type: str, file_type: str) -> bool:
        """Validate MIME type."""
        # Check blocked MIME types first
        if mime_type in self.config.blocked_mimes:
            return False
        
        # Check allowed MIME types for file type
        if file_type == "audio":
            return mime_type in self.config.allowed_audio_mimes
        elif file_type == "document":
            return mime_type in self.config.allowed_document_mimes
        elif file_type == "image":
            return mime_type in self.config.allowed_image_mimes
        
        return False
    
    def _scan_file_content(self, file_path: Path) -> List[str]:
        """Scan file content for security threats."""
        errors = []
        
        try:
            # Read file header for signature validation
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # First 1KB
            
            # Check for embedded executables or scripts
            dangerous_signatures = [
                b'MZ',  # Windows executable
                b'\\x7fELF',  # Linux executable
                b'\\xca\\xfe\\xba\\xbe',  # Java class file
                b'\\xfe\\xed\\xfa',  # Mach-O executable
                b'<?php',  # PHP script
                b'#!/bin/',  # Shell script
                b'<script',  # JavaScript
            ]
            
            for signature in dangerous_signatures:
                if signature in header:
                    errors.append(f"Dangerous file signature detected: {signature}")
            
            # Check for suspicious strings in text content
            if self._is_text_file(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(8192)  # First 8KB of text
                
                suspicious_patterns = [
                    'eval(', 'exec(', 'system(', 'shell_exec(',
                    'javascript:', 'vbscript:', 'onload=', 'onerror=',
                    'document.cookie', 'document.write',
                    'SELECT * FROM', 'DROP TABLE', 'UNION SELECT'
                ]
                
                for pattern in suspicious_patterns:
                    if pattern.lower() in content.lower():
                        errors.append(f"Suspicious content pattern: {pattern}")
            
        except Exception as e:
            logger.warning(f"Content scanning error: {e}")
        
        return errors
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file appears to be text-based."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
            
            # Simple heuristic: if more than 30% are printable ASCII, consider it text
            printable_chars = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in [9, 10, 13])
            return (printable_chars / len(chunk)) > 0.3 if chunk else False
        except:
            return False
    
    def _validate_file_path(self, file_path: Path) -> bool:
        """Validate file path for security."""
        path_str = str(file_path)
        
        # Check for path traversal attempts
        dangerous_patterns = ['../', '..\\\\', '~/', '/etc/', '/usr/', '/var/', '/root/']
        for pattern in dangerous_patterns:
            if pattern in path_str:
                return False
        
        # Ensure path is within allowed directories
        if self.config.allowed_upload_dirs:
            resolved_path = file_path.resolve()
            for allowed_dir in self.config.allowed_upload_dirs:
                allowed_path = Path(allowed_dir).resolve()
                try:
                    resolved_path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            return False
        
        return True
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _validate_hash_limits(self, file_hash: str) -> bool:
        """Validate against duplicate upload limits."""
        current_time = datetime.now()
        
        # Clean old entries
        cutoff_time = current_time.timestamp() - 3600  # 1 hour ago
        if file_hash in self.uploaded_hashes:
            self.uploaded_hashes[file_hash] = [
                dt for dt in self.uploaded_hashes[file_hash] 
                if dt.timestamp() > cutoff_time
            ]
        
        # Check current count
        if file_hash not in self.uploaded_hashes:
            self.uploaded_hashes[file_hash] = []
        
        current_count = len(self.uploaded_hashes[file_hash])
        if current_count >= self.config.max_duplicate_uploads:
            return False
        
        # Add current upload
        self.uploaded_hashes[file_hash].append(current_time)
        return True
    
    def _perform_security_checks(self, file_path: Path) -> List[str]:
        """Perform additional security checks."""
        errors = []
        
        try:
            # Check file permissions
            stat = file_path.stat()
            if stat.st_mode & 0o111:  # Check if executable
                errors.append("File has executable permissions")
            
            # Check for symlinks
            if file_path.is_symlink():
                errors.append("Symbolic links not allowed")
            
            # Check for hidden files (security concern)
            if file_path.name.startswith('.') and file_path.name not in ['.', '..']:
                errors.append("Hidden files not allowed")
            
        except Exception as e:
            logger.warning(f"Security check error: {e}")
        
        return errors
    
    def _log_validation_attempt(self, file_path: Path, errors: List[str], metadata: Dict[str, Any]):
        """Log file validation attempt."""
        status = "REJECTED" if errors else "ACCEPTED"
        logger.info(
            f"File validation {status}: {file_path.name} "
            f"(size: {metadata.get('file_size', 0)}, "
            f"mime: {metadata.get('mime_type', 'unknown')}) "
            f"Errors: {', '.join(errors) if errors else 'None'}"
        )
    
    def quarantine_file(self, file_path: str, reason: str) -> str:
        """Move file to quarantine for security review."""
        try:
            source_path = Path(file_path)
            quarantine_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source_path.name}"
            quarantine_path = self.quarantine_dir / quarantine_name
            
            shutil.move(str(source_path), str(quarantine_path))
            
            # Create metadata file
            metadata_path = quarantine_path.with_suffix('.metadata')
            with open(metadata_path, 'w') as f:
                f.write(f"Original path: {source_path}\\n")
                f.write(f"Quarantine reason: {reason}\\n")
                f.write(f"Quarantine time: {datetime.now().isoformat()}\\n")
            
            logger.warning(f"File quarantined: {quarantine_path} (reason: {reason})")
            return str(quarantine_path)
            
        except Exception as e:
            logger.error(f"Failed to quarantine file: {e}")
            raise

def create_secure_file_validator(config: Optional[FileSecurityConfig] = None) -> FileSecurityValidator:
    """Factory function to create a secure file validator."""
    if config is None:
        config = FileSecurityConfig()
    
    return FileSecurityValidator(config)

# Utility functions for integration
def validate_uploaded_file(file_path: str, file_type: str = "audio", 
                          config: Optional[FileSecurityConfig] = None) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Quick function to validate an uploaded file.
    
    Args:
        file_path: Path to the uploaded file
        file_type: Type of file expected ("audio", "document", "image")
        config: Optional custom configuration
    
    Returns:
        Tuple of (is_valid, errors, metadata)
    """
    validator = create_secure_file_validator(config)
    return validator.validate_file(file_path, file_type)

def secure_file_upload_middleware():
    """Create middleware for secure file uploads."""
    # This would be integrated with FastAPI file upload handlers
    pass

# Export main components
__all__ = [
    "FileSecurityConfig",
    "FileSecurityValidator", 
    "create_secure_file_validator",
    "validate_uploaded_file"
]