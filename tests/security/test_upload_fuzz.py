"""Property-based fuzz tests for upload security boundaries."""

from __future__ import annotations

import io
import shutil
from pathlib import Path

import pytest
from fastapi import UploadFile
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from api.models import Job
from api.orm_bootstrap import SessionLocal

try:  # Consolidated service exposes SUPPORTED_FORMATS in some revisions
    from api.services.consolidated_upload_service import SUPPORTED_FORMATS
except ImportError:  # pragma: no cover - compatibility guard
    SUPPORTED_FORMATS = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp3": ".mp3",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/x-m4a": ".m4a",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
    }

from api.services.consolidated_upload_service import ConsolidatedUploadService
from api.settings import settings as app_settings


def _dangerous_filename_strategy() -> st.SearchStrategy[str]:
    """Generate filenames with characters that often break sanitizers."""

    base_alphabet = st.characters(
        blacklist_categories=("Cs",),
        min_codepoint=1,
        max_codepoint=0xD7FF,
    )
    path_fragment = st.text(base_alphabet, min_size=1, max_size=12)
    traversal = st.sampled_from(["..", "../", "..\\", "//", "\\\\"])
    decorated = st.one_of(
        path_fragment,
        st.builds(lambda frag: f"../{frag}", path_fragment),
        st.builds(lambda frag: f"..\\{frag}", path_fragment),
        st.builds(lambda frag: f"{frag}/..", path_fragment),
        st.builds(lambda frag, delim: f"{frag}{delim}{frag}", path_fragment, traversal),
    )
    extension = st.sampled_from(list(SUPPORTED_FORMATS.values()))
    return st.builds(lambda core, ext: f"{core.strip() or 'payload'}{ext}", decorated, extension)


def _payload_strategy() -> st.SearchStrategy[bytes]:
    """Generate binary payloads with wide byte coverage."""

    return st.binary(min_size=1, max_size=4096)


@pytest.mark.usefixtures("fakeredis_server")
@given(
    filename=_dangerous_filename_strategy(),
    payload=_payload_strategy(),
    mime=st.sampled_from(sorted(SUPPORTED_FORMATS.keys())),
)
@settings(
    deadline=None,
    max_examples=20,
    suppress_health_check=(
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
    ),
)
def test_direct_upload_never_escapes_upload_root(
    event_loop,
    stub_job_queue,
    filename: str,
    payload: bytes,
    mime: str,
) -> None:
    """Ensure fuzzed filenames can't escape the configured upload directory."""

    stub_job_queue.submitted.clear()
    service = ConsolidatedUploadService()

    async def _run_upload() -> dict[str, str]:
        upload = UploadFile(
            filename=filename,
            file=io.BytesIO(payload),
            headers={"content-type": mime},
        )

        try:
            with SessionLocal() as db:
                result = await service.handle_direct_upload(
                    upload,
                    user_id="fuzz-user",
                    db=db,
                    model_name="small",
                    language="en",
                )
        finally:
            await upload.close()

        return result

    result = event_loop.run_until_complete(_run_upload())
    assert result["status"] == "queued"
    assert stub_job_queue.submitted, "The fuzz run should enqueue a transcription job"

    saved_path = Path(stub_job_queue.submitted[-1]["kwargs"]["file_path"]).resolve()
    upload_root = Path(app_settings.upload_dir).resolve()

    # The saved file must live directly beneath the configured upload directory.
    assert saved_path.parent == upload_root
    assert ".." not in saved_path.parts

    # Clean up the stored job and the fuzzed artifact.
    job_id = result["job_id"]
    with SessionLocal() as cleanup_db:
        job = cleanup_db.get(Job, job_id)
        if job:
            cleanup_db.delete(job)
            cleanup_db.commit()

    if saved_path.exists():
        saved_path.unlink()

    stub_job_queue.submitted.clear()
    service.chunked_service.chunk_processor.cleanup()


@pytest.mark.usefixtures("fakeredis_server")
@given(
    filename=_dangerous_filename_strategy(),
    payload=_payload_strategy(),
    chunk_number=st.integers(min_value=0, max_value=4),
)
@settings(
    deadline=None,
    max_examples=12,
    suppress_health_check=(
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
    ),
)
def test_chunked_upload_stores_chunks_in_session_directory(
    event_loop,
    filename: str,
    payload: bytes,
    chunk_number: int,
) -> None:
    """Ensure chunk assembly never writes outside the session sandbox."""

    service = ConsolidatedUploadService().chunked_service
    file_size = service.chunk_size * max(chunk_number + 1, 1)

    session_dir: Path | None = None
    try:
        async def _initialize_and_upload() -> tuple[str, dict[str, str]]:
            init = await service.initialize_upload(
                user_id="chunk-user",
                filename=filename,
                file_size=file_size,
                file_hash=None,
                model_name="small",
                language="en",
            )

            session_id = init["session_id"]
            upload_result = await service.upload_chunk(
                session_id=session_id,
                chunk_number=chunk_number,
                chunk_data=payload,
                user_id="chunk-user",
            )

            return session_id, upload_result

        session_id, upload_result = event_loop.run_until_complete(
            _initialize_and_upload()
        )
        assert upload_result["status"] in {"uploaded", "already_uploaded"}

        session_dir = (
            Path(app_settings.upload_dir)
            .resolve()
            .joinpath("sessions", session_id)
        )
        chunk_path = session_dir / "chunks" / f"chunk_{chunk_number:06d}.tmp"

        assert chunk_path.exists()
        assert session_dir.is_dir()
        assert Path(app_settings.upload_dir).resolve() in chunk_path.resolve().parents
    finally:
        if session_dir is not None:
            shutil.rmtree(session_dir, ignore_errors=True)
        service.chunk_processor.cleanup()
