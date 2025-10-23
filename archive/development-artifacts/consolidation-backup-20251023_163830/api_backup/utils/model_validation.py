"""
Model validation utilities for the Whisper Transcriber API.
"""

from pathlib import Path
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("model_validation")

def validate_models_dir():
    """Validate that the models directory exists and contains expected models."""
    models_dir = settings.models_dir
    
    if not models_dir.exists():
        logger.warning(f"Models directory does not exist: {models_dir}")
        models_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created models directory: {models_dir}")
    
    # Check for expected model files
    expected_models = ["tiny.pt", "small.pt", "medium.pt", "large-v3.pt"]
    found_models = []
    
    for model_file in expected_models:
        model_path = models_dir / model_file
        if model_path.exists():
            found_models.append(model_file)
    
    if found_models:
        logger.info(f"Found Whisper models: {', '.join(found_models)}")
    else:
        logger.warning("No pre-downloaded Whisper models found. Models will be downloaded on first use.")
    
    return {
        "models_dir": str(models_dir),
        "found_models": found_models,
        "expected_models": expected_models
    }
