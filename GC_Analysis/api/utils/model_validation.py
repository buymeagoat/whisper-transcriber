from api.paths import MODEL_DIR
from api.utils.logger import get_system_logger


system_log = get_system_logger()


def validate_models_dir():
    """Ensure MODEL_DIR contains all required Whisper model files."""
    if not MODEL_DIR.exists():
        system_log.critical("Missing models directory: %s", MODEL_DIR.resolve())
        raise RuntimeError(
            f"Whisper models directory {MODEL_DIR.resolve()} is missing."
            " Populate it with the required files before running."
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
            MODEL_DIR.resolve(),
            ", ".join(missing),
        )
        raise RuntimeError(
            f"Required model files missing from {MODEL_DIR.resolve()}: "
            f"{', '.join(missing)}."
        )


def available_models() -> set[str]:
    """Return model names discovered in ``MODEL_DIR``.

    Model files are expected to have a ``.pt`` extension. The returned names
    exclude the extension. Missing ``MODEL_DIR`` simply results in an empty
    set.
    """
    if not MODEL_DIR.exists():
        return set()
    return {p.stem for p in MODEL_DIR.glob("*.pt") if p.is_file()}
