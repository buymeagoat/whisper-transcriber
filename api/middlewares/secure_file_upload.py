"""
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
