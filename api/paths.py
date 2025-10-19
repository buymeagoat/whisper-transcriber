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
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [self.upload_dir, self.transcripts_dir, self.models_dir, 
                         self.cache_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

# Global storage instance
storage = StoragePaths()

# Ensure directories exist on import
storage.ensure_directories()
