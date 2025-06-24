# api/errors.py
#
# Centralized error-code enum + helper for consistent JSON error bodies.
# Import `http_error` in your routes and raise it instead of raw HTTPException:
#
#     raise http_error(ErrorCode.JOB_NOT_FOUND)
#
# Every client will then receive:
#     { "code": 40401, "message": "Job no longer exists." }

from enum import IntEnum
from fastapi import HTTPException


class ErrorCode(IntEnum):
    def __str__(self):
        return f"{self.name} ({self.value})"

    # 4xx – client
    UNSUPPORTED_MEDIA = 40001  # Unsupported file format
    FILE_TOO_LARGE = 40002  # > 2 GB limit
    JOB_NOT_FOUND = 40401  # /jobs/{id} missing
    TRANSCRIPT_NOT_FOUND = 40402  # Transcript missing on disk
    AUDIO_NOT_FOUND = 40403  # Original audio missing
    FILE_SAVE_FAILED = 40003  # File couldn't be written to disk
    DUPLICATE_JOB = 40901  # Same audio already queued
    JOB_BUSY = 40301  # Job is running; action blocked

    # 5xx – server
    WHISPER_RUNTIME = 50001  # Whisper process crashed
    FILE_NOT_FOUND = 50002  # Internal mismatch: missing expected output


ERROR_MAP: dict[ErrorCode, str] = {
    ErrorCode.UNSUPPORTED_MEDIA: "Format not supported. Allowed: mp3, m4a, wav, flac.",
    ErrorCode.FILE_TOO_LARGE: "File exceeds 2 GB limit.",
    ErrorCode.JOB_NOT_FOUND: "Job no longer exists.",
    ErrorCode.TRANSCRIPT_NOT_FOUND: "Transcript not found.",
    ErrorCode.AUDIO_NOT_FOUND: "Original audio not found.",
    ErrorCode.FILE_SAVE_FAILED: "Failed to save uploaded file.",
    ErrorCode.DUPLICATE_JOB: "Audio already queued or completed.",
    ErrorCode.JOB_BUSY: "Job is currently running—try later.",
    ErrorCode.WHISPER_RUNTIME: "Transcription failed—internal Whisper error.",
    ErrorCode.FILE_NOT_FOUND: "Expected output file missing—contact support.",
}

_HTTP_STATUS = {
    ErrorCode.UNSUPPORTED_MEDIA: 415,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.JOB_NOT_FOUND: 404,
    ErrorCode.TRANSCRIPT_NOT_FOUND: 404,
    ErrorCode.AUDIO_NOT_FOUND: 404,
    ErrorCode.FILE_SAVE_FAILED: 500,
    ErrorCode.DUPLICATE_JOB: 409,
    ErrorCode.JOB_BUSY: 403,
    ErrorCode.WHISPER_RUNTIME: 500,
    ErrorCode.FILE_NOT_FOUND: 500,
}


def http_error(code: ErrorCode) -> HTTPException:
    """Return FastAPI HTTPException with structured JSON body."""
    status = _HTTP_STATUS.get(code, 500)
    message = ERROR_MAP.get(code, "Unknown error occurred.")
    return HTTPException(
        status_code=status,
        detail={"code": int(code), "message": message},
    )
