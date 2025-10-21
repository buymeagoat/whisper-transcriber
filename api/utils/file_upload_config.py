"""
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
