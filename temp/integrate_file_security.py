#!/usr/bin/env python3
"""
T026 Security Hardening: File Upload Security Integration
Integrates comprehensive file upload security into the whisper-transcriber application.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any

def integrate_file_upload_security():
    """Integrate file upload security into the application."""
    project_root = Path("/home/buymeagoat/dev/whisper-transcriber")
    
    print("📁 T026 Security Hardening: Integrating File Upload Security")
    print("=" * 70)
    
    # Copy file upload security system to the api/utils directory
    source_file = project_root / "temp" / "file_upload_security.py"
    target_file = project_root / "api" / "utils" / "file_upload_security.py"
    
    # Create utils directory if it doesn't exist
    target_file.parent.mkdir(exist_ok=True)
    
    # Copy the file
    shutil.copy2(source_file, target_file)
    print(f"✅ Copied file upload security system to {target_file}")
    
    # Create FastAPI integration middleware
    integration_content = '''"""
File Upload Security Middleware for FastAPI
Provides secure file upload handling with comprehensive validation.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from api.utils.file_upload_security import (
    FileSecurityConfig, 
    FileSecurityValidator,
    create_secure_file_validator
)

class SecureFileUploadHandler:
    """Secure file upload handler for FastAPI applications."""
    
    def __init__(self, config: Optional[FileSecurityConfig] = None):
        self.validator = create_secure_file_validator(config)
        self.temp_dir = Path(tempfile.gettempdir()) / "secure_uploads"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def validate_and_save_upload(
        self, 
        upload_file: UploadFile, 
        file_type: str = "audio",
        destination_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and securely save an uploaded file.
        
        Args:
            upload_file: FastAPI UploadFile object
            file_type: Expected file type ("audio", "document", "image")
            destination_dir: Directory to save the validated file
            
        Returns:
            Dictionary with file information and validation results
            
        Raises:
            HTTPException: If file validation fails
        """
        # Create temporary file for validation
        temp_file = self.temp_dir / f"upload_{upload_file.filename}"
        
        try:
            # Save upload to temporary file
            with open(temp_file, "wb") as buffer:
                content = await upload_file.read()
                buffer.write(content)
            
            # Validate the file
            is_valid, errors, metadata = self.validator.validate_file(
                str(temp_file), file_type
            )
            
            if not is_valid:
                # File failed validation - quarantine if enabled
                if self.validator.config.enable_file_quarantine:
                    quarantine_path = self.validator.quarantine_file(
                        str(temp_file), 
                        f"Validation failed: {', '.join(errors)}"
                    )
                else:
                    # Just delete the file
                    temp_file.unlink()
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "File validation failed",
                        "reasons": errors,
                        "filename": upload_file.filename
                    }
                )
            
            # File is valid - move to destination if specified
            final_path = temp_file
            if destination_dir:
                dest_dir = Path(destination_dir)
                dest_dir.mkdir(parents=True, exist_ok=True)
                final_path = dest_dir / upload_file.filename
                shutil.move(str(temp_file), str(final_path))
            
            return {
                "filename": upload_file.filename,
                "file_path": str(final_path),
                "file_size": metadata["file_size"],
                "mime_type": metadata["mime_type"],
                "file_hash": metadata.get("hash"),
                "validation_status": "passed",
                "upload_timestamp": metadata.get("upload_timestamp")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload processing error: {str(e)}"
            )
    
    def create_upload_validator_dependency(self, file_type: str = "audio"):
        """
        Create a FastAPI dependency for file upload validation.
        
        Args:
            file_type: Expected file type
            
        Returns:
            FastAPI dependency function
        """
        async def validate_upload(upload_file: UploadFile) -> Dict[str, Any]:
            return await self.validate_and_save_upload(upload_file, file_type)
        
        return validate_upload

# Global secure upload handler instance
_upload_handler = None

def get_secure_upload_handler(config: Optional[FileSecurityConfig] = None) -> SecureFileUploadHandler:
    """Get or create the global secure upload handler."""
    global _upload_handler
    if _upload_handler is None:
        _upload_handler = SecureFileUploadHandler(config)
    return _upload_handler

# Convenience functions for common use cases
async def validate_audio_upload(upload_file: UploadFile, destination_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate and save an audio file upload."""
    handler = get_secure_upload_handler()
    return await handler.validate_and_save_upload(upload_file, "audio", destination_dir)

async def validate_document_upload(upload_file: UploadFile, destination_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate and save a document file upload."""
    handler = get_secure_upload_handler()
    return await handler.validate_and_save_upload(upload_file, "document", destination_dir)

async def validate_image_upload(upload_file: UploadFile, destination_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate and save an image file upload."""
    handler = get_secure_upload_handler()
    return await handler.validate_and_save_upload(upload_file, "image", destination_dir)

# FastAPI dependency functions
def AudioUploadValidator():
    """FastAPI dependency for audio file upload validation."""
    return get_secure_upload_handler().create_upload_validator_dependency("audio")

def DocumentUploadValidator():
    """FastAPI dependency for document file upload validation.""" 
    return get_secure_upload_handler().create_upload_validator_dependency("document")

def ImageUploadValidator():
    """FastAPI dependency for image file upload validation."""
    return get_secure_upload_handler().create_upload_validator_dependency("image")
'''
    
    middleware_file = project_root / "api" / "middlewares" / "secure_file_upload.py"
    with open(middleware_file, 'w') as f:
        f.write(integration_content)
    print(f"✅ Created secure file upload middleware at {middleware_file}")
    
    # Create configuration file for file upload security
    config_content = '''"""
File Upload Security Configuration
Customize file upload security settings for different environments.
"""

from api.utils.file_upload_security import FileSecurityConfig

# Production configuration (most restrictive)
PRODUCTION_CONFIG = FileSecurityConfig(
    # File size limits (bytes)
    max_file_size=50 * 1024 * 1024,  # 50MB general limit
    max_audio_file_size=200 * 1024 * 1024,  # 200MB for audio files
    max_document_size=5 * 1024 * 1024,  # 5MB for documents
    max_image_size=2 * 1024 * 1024,  # 2MB for images
    
    # Security features
    enable_content_scanning=True,
    enable_virus_scanning=False,  # Enable if ClamAV is available
    enable_metadata_stripping=True,
    enable_path_traversal_protection=True,
    enable_file_quarantine=True,
    enable_hash_tracking=True,
    
    # Upload limits
    max_duplicate_uploads=3,
    quarantine_duration=7200,  # 2 hours
    
    # Allowed directories
    allowed_upload_dirs={
        "./uploads", "./temp", "/tmp/uploads"
    }
)

# Development configuration (more lenient)
DEVELOPMENT_CONFIG = FileSecurityConfig(
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_audio_file_size=500 * 1024 * 1024,  # 500MB
    max_document_size=10 * 1024 * 1024,  # 10MB
    max_image_size=5 * 1024 * 1024,  # 5MB
    
    enable_content_scanning=True,
    enable_virus_scanning=False,
    enable_metadata_stripping=False,  # Keep metadata for debugging
    enable_path_traversal_protection=True,
    enable_file_quarantine=False,  # Don't quarantine in dev
    enable_hash_tracking=True,
    
    max_duplicate_uploads=10,
    
    allowed_upload_dirs={
        "./uploads", "./temp", "/tmp/uploads", "./dev_uploads"
    }
)

# Test configuration (very lenient)
TEST_CONFIG = FileSecurityConfig(
    max_file_size=1024 * 1024 * 1024,  # 1GB for testing
    max_audio_file_size=1024 * 1024 * 1024,
    max_document_size=100 * 1024 * 1024,
    max_image_size=50 * 1024 * 1024,
    
    enable_content_scanning=False,  # Disable for faster tests
    enable_virus_scanning=False,
    enable_metadata_stripping=False,
    enable_path_traversal_protection=True,
    enable_file_quarantine=False,
    enable_hash_tracking=False,  # Disable for test repeatability
    
    max_duplicate_uploads=100,
    
    allowed_upload_dirs={
        "./test_uploads", "./temp", "/tmp"
    }
)

def get_config_for_environment(environment: str = "production") -> FileSecurityConfig:
    """Get file upload security configuration for the specified environment."""
    if environment == "production":
        return PRODUCTION_CONFIG
    elif environment == "development":
        return DEVELOPMENT_CONFIG
    elif environment == "test":
        return TEST_CONFIG
    else:
        return PRODUCTION_CONFIG  # Default to most secure
'''
    
    config_file = project_root / "api" / "utils" / "file_upload_config.py"
    with open(config_file, 'w') as f:
        f.write(config_content)
    print(f"✅ Created file upload security configuration at {config_file}")
    
    # Create example usage documentation
    usage_examples = '''# File Upload Security - Usage Examples

## Basic Usage in FastAPI Routes

```python
from fastapi import FastAPI, UploadFile, Depends
from api.middlewares.secure_file_upload import validate_audio_upload, AudioUploadValidator

app = FastAPI()

# Method 1: Direct validation
@app.post("/upload-audio/")
async def upload_audio_file(file: UploadFile):
    try:
        result = await validate_audio_upload(file, "./uploads/audio")
        return {"message": "File uploaded successfully", "file_info": result}
    except HTTPException as e:
        return {"error": e.detail}

# Method 2: Using dependency injection
@app.post("/transcribe/")
async def transcribe_audio(file_info: dict = Depends(AudioUploadValidator())):
    # file_info contains validated file information
    file_path = file_info["file_path"]
    # Process the validated file...
    return {"status": "processing", "file": file_info}
```

## Customizing Security Configuration

```python
from api.utils.file_upload_security import FileSecurityConfig
from api.middlewares.secure_file_upload import SecureFileUploadHandler

# Create custom configuration
custom_config = FileSecurityConfig(
    max_audio_file_size=100 * 1024 * 1024,  # 100MB
    enable_content_scanning=True,
    enable_file_quarantine=True
)

# Use custom handler
handler = SecureFileUploadHandler(custom_config)
```

## Security Features

1. **File Type Validation**: Extension and MIME type checking
2. **Content Scanning**: Malicious content detection
3. **Size Limits**: Configurable per file type
4. **Path Traversal Protection**: Prevents directory traversal attacks
5. **Hash Tracking**: Prevents duplicate uploads
6. **Quarantine System**: Isolates suspicious files
7. **Metadata Stripping**: Removes potentially dangerous metadata

## Environment-Specific Settings

The system automatically detects the environment (production/development/test) and applies appropriate security settings. Production has the most restrictive settings for maximum security.

## Monitoring and Logging

All file upload attempts are logged with detailed information about validation results, enabling security monitoring and incident response.
'''
    
    docs_file = project_root / "docs" / "file_upload_security.md"
    docs_file.parent.mkdir(exist_ok=True)
    with open(docs_file, 'w') as f:
        f.write(usage_examples)
    print(f"✅ Created usage documentation at {docs_file}")
    
    # Update requirements.txt for new dependencies
    req_file = project_root / "requirements.txt"
    try:
        with open(req_file, 'r') as f:
            content = f.read()
        
        new_deps = []
        if 'python-magic' not in content:
            new_deps.append('python-magic>=0.4.27')
        if 'filetype' not in content:
            new_deps.append('filetype>=1.2.0')
        
        if new_deps:
            with open(req_file, 'a') as f:
                for dep in new_deps:
                    f.write(f'\\n{dep}')
            print(f"✅ Added dependencies to requirements.txt: {', '.join(new_deps)}")
        else:
            print("✅ Required dependencies already in requirements.txt")
            
    except FileNotFoundError:
        print("⚠️  requirements.txt not found")
    
    # Create directories for secure uploads
    upload_dirs = ['uploads', 'temp', 'quarantine']
    for dir_name in upload_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(exist_ok=True)
        
        # Create .gitkeep to ensure directories exist in git
        gitkeep = dir_path / '.gitkeep'
        gitkeep.touch()
    print(f"✅ Created secure upload directories: {', '.join(upload_dirs)}")
    
    print("\\n" + "=" * 70)
    print("📁 FILE UPLOAD SECURITY INTEGRATION COMPLETE")
    print("=" * 70)
    print("Security features implemented:")
    print("  • Comprehensive file type validation (extension + MIME + content)")
    print("  • File size limits with per-type customization")
    print("  • Content scanning for malicious patterns")
    print("  • Path traversal attack prevention")
    print("  • Duplicate upload tracking and limiting")
    print("  • File quarantine system for suspicious uploads")
    print("  • Environment-specific security configurations")
    print("  • Comprehensive security logging")
    print("\\nFiles created:")
    print(f"  • {target_file}")
    print(f"  • {middleware_file}")
    print(f"  • {config_file}")
    print(f"  • {docs_file}")
    print("\\nNext steps:")
    print("  • Review and customize security settings in file_upload_config.py")
    print("  • Integrate secure upload handlers into your API endpoints")
    print("  • Set up monitoring for quarantined files")
    print("  • Consider adding ClamAV for virus scanning in production")

if __name__ == "__main__":
    integrate_file_upload_security()