"""
Path configuration for the Whisper Transcriber API.
"""

from pathlib import Path
from api.settings import settings

# Directory paths
UPLOAD_DIR = settings.upload_dir
TRANSCRIPTS_DIR = settings.transcripts_dir
MODELS_DIR = settings.models_dir
CACHE_DIR = settings.cache_dir
LOGS_DIR = Path("logs")

# Create a storage object for compatibility
class StoragePaths:
    """Storage path configuration."""
    
    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.transcripts_dir = TRANSCRIPTS_DIR
        self.models_dir = MODELS_DIR
        self.cache_dir = CACHE_DIR
        self.logs_dir = LOGS_DIR
        
        # Uppercase aliases for compatibility
        self.UPLOAD_DIR = UPLOAD_DIR
        self.TRANSCRIPTS_DIR = TRANSCRIPTS_DIR
        self.MODELS_DIR = MODELS_DIR
        self.CACHE_DIR = CACHE_DIR
        self.LOGS_DIR = LOGS_DIR
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [self.upload_dir, self.transcripts_dir, self.models_dir, 
                         self.cache_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_upload_path(self, filename: str) -> Path:
        """Get the full path for an uploaded file."""
        return self.upload_dir / filename
    
    def get_transcript_dir(self, job_id: str) -> Path:
        """Get the directory path for transcripts of a specific job."""
        return self.transcripts_dir / str(job_id)

# Global storage instance
storage = StoragePaths()

# Ensure directories exist on import
storage.ensure_directories()
