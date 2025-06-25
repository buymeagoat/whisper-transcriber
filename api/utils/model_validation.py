from api.paths import MODEL_DIR
from api.utils.logger import get_system_logger


system_log = get_system_logger()


def validate_models_dir():
    """Ensure MODEL_DIR contains all required Whisper model files."""
    if not MODEL_DIR.exists():
        system_log.critical(
            "Missing models directory. Populate models/ before running."
        )
        raise RuntimeError(
            "Whisper models directory missing. Ensure models/ contains the required files."
        )

    required_models = [
        "base.pt",
        "large-v3.pt",
        "medium.pt",
        "small.pt",
        "tiny.pt",
    ]

    missing = [m for m in required_models if not (MODEL_DIR / m).is_file()]

    if missing:
        system_log.critical(
            "Missing model files in %s: %s",
            MODEL_DIR,
            ", ".join(missing),
        )
        raise RuntimeError(
            f"Required model files missing: {', '.join(missing)}. Add them to models/."
        )
