"""Bootstrap helpers for preparing Whisper checkpoints."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, List
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from api.paths import storage

LOGGER = logging.getLogger("whisper.worker.bootstrap")

DEFAULT_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "small")
DEFAULT_MODEL_URLS = {
    "tiny": "https://huggingface.co/openai/whisper-tiny/resolve/main/tiny.pt?download=1",
    "base": "https://huggingface.co/openai/whisper-base/resolve/main/base.pt?download=1",
    "small": "https://huggingface.co/openai/whisper-small/resolve/main/small.pt?download=1",
    "medium": "https://huggingface.co/openai/whisper-medium/resolve/main/medium.pt?download=1",
    "large-v2": "https://huggingface.co/openai/whisper-large-v2/resolve/main/large-v2.pt?download=1",
}


class WhisperModelBootstrapError(RuntimeError):
    """Raised when Whisper checkpoints cannot be prepared for the worker."""


def _log_available(paths: Iterable[Path]) -> None:
    for path in paths:
        LOGGER.info("Whisper checkpoint available: %s", path)


def _copy_checkpoint(source: Path, destination_dir: Path) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    if source.resolve() == destination.resolve():
        return destination
    shutil.copy2(source, destination)
    return destination


def _copy_from_directory(source_dir: Path, destination_dir: Path) -> List[Path]:
    copied: List[Path] = []
    for candidate in source_dir.glob("*.pt"):
        copied.append(_copy_checkpoint(candidate, destination_dir))
    return copied


def _download_checkpoint(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    if parsed.scheme in {"", "file"}:
        source_path = Path(parsed.path)
        if not source_path.exists():
            raise WhisperModelBootstrapError(f"Whisper checkpoint not found at {source_path}")
        return _copy_checkpoint(source_path, destination.parent)

    tmp_path = destination.with_suffix(destination.suffix + ".download")
    try:
        with urlopen(url) as response, open(tmp_path, "wb") as outfile:  # type: ignore[arg-type]
            shutil.copyfileobj(response, outfile)
    except URLError as exc:  # pragma: no cover - network dependent
        raise WhisperModelBootstrapError(f"Failed to download Whisper checkpoint from {url}: {exc}") from exc
    os.replace(tmp_path, destination)
    return destination


def bootstrap_model_assets(*, force_download: bool = False) -> List[Path]:
    """Ensure Whisper checkpoints exist in ``storage.models_dir``.

    The bootstrap routine supports three sourcing strategies, attempted in
    order:

    1. Copy a specific checkpoint defined via ``WHISPER_MODEL_PATH`` or
       ``WHISPER_MODELS_DIR``.
    2. Download a checkpoint from ``WHISPER_MODEL_DOWNLOAD_URL``.
    3. Download a known OpenAI Whisper release that matches
       ``WHISPER_MODEL_NAME``.

    If ``force_download`` is set the routine ignores any pre-existing assets
    and re-runs the download/copy steps.  Otherwise, an existing ``*.pt`` file
    short-circuits the bootstrap logic.
    """

    models_dir = storage.models_dir
    models_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(models_dir.glob("*.pt"))
    if existing and not force_download:
        _log_available(existing)
        return existing

    model_file_env = os.getenv("WHISPER_MODEL_PATH")
    if model_file_env:
        candidate = Path(model_file_env).expanduser()
        if candidate.is_file():
            existing.append(_copy_checkpoint(candidate, models_dir))
        elif candidate.is_dir():
            existing.extend(_copy_from_directory(candidate, models_dir))
        else:
            raise WhisperModelBootstrapError(
                f"WHISPER_MODEL_PATH refers to missing location: {candidate}"
            )

    model_dir_env = os.getenv("WHISPER_MODELS_DIR")
    if model_dir_env:
        directory = Path(model_dir_env).expanduser()
        if directory.is_dir():
            existing.extend(_copy_from_directory(directory, models_dir))
        else:
            raise WhisperModelBootstrapError(
                f"WHISPER_MODELS_DIR refers to missing directory: {directory}"
            )

    download_url = os.getenv("WHISPER_MODEL_DOWNLOAD_URL")
    model_name = os.getenv("WHISPER_MODEL_NAME", DEFAULT_MODEL_NAME)
    destination = models_dir / f"{model_name}.pt"

    if force_download and download_url:
        existing.clear()

    if download_url:
        existing.append(_download_checkpoint(download_url, destination))
    elif not existing:
        fallback_url = DEFAULT_MODEL_URLS.get(model_name)
        if fallback_url is None:
            raise WhisperModelBootstrapError(
                "No Whisper checkpoints found and no download URL configured; "
                "set WHISPER_MODEL_DOWNLOAD_URL or provide a model file."
            )
        LOGGER.info(
            "Downloading Whisper checkpoint for model '%s' from %s", model_name, fallback_url
        )
        existing.append(_download_checkpoint(fallback_url, destination))

    final_paths = sorted(models_dir.glob("*.pt"))
    if not final_paths:
        raise WhisperModelBootstrapError(
            f"Whisper model bootstrap failed: no '.pt' checkpoints present in {models_dir.resolve()}"
        )

    _log_available(final_paths)
    return final_paths


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint used by deployment scripts."""

    argv = list(argv or [])
    force = "--force" in argv
    try:
        paths = bootstrap_model_assets(force_download=force)
    except WhisperModelBootstrapError as exc:
        LOGGER.error("%s", exc)
        return 1

    print("Whisper checkpoints ready:")
    for path in paths:
        print(f" - {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution path
    sys.exit(main(sys.argv[1:]))
