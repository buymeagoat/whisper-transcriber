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
    FILE_SAVE_FAILED = 40003  # File couldn't be written to disk

    # 5xx – server
    WHISPER_RUNTIME = 50001  # Whisper process crashed
    FILE_NOT_FOUND = 50002  # Internal mismatch: missing expected output
    CLOUD_STORAGE_ERROR = 50003  # Failed S3 interaction


ERROR_MAP: dict[ErrorCode, str] = {
    ErrorCode.UNSUPPORTED_MEDIA: "Format not supported. Allowed: mp3, m4a, wav, flac.",
    ErrorCode.FILE_TOO_LARGE: "File exceeds 2 GB limit.",
    ErrorCode.JOB_NOT_FOUND: "Job no longer exists.",
    ErrorCode.TRANSCRIPT_NOT_FOUND: "Transcript not found.",
    ErrorCode.FILE_SAVE_FAILED: "Failed to save uploaded file.",
    ErrorCode.WHISPER_RUNTIME: "Transcription failed—internal Whisper error.",
    ErrorCode.FILE_NOT_FOUND: "Expected output file missing—contact support.",
    ErrorCode.CLOUD_STORAGE_ERROR: "Cloud storage operation failed.",
}

_HTTP_STATUS = {
    ErrorCode.UNSUPPORTED_MEDIA: 415,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.JOB_NOT_FOUND: 404,
    ErrorCode.TRANSCRIPT_NOT_FOUND: 404,
    ErrorCode.FILE_SAVE_FAILED: 500,
    ErrorCode.WHISPER_RUNTIME: 500,
    ErrorCode.FILE_NOT_FOUND: 500,
    ErrorCode.CLOUD_STORAGE_ERROR: 500,
}


def http_error(code: ErrorCode) -> HTTPException:
    """Return FastAPI HTTPException with structured JSON body."""
    status = _HTTP_STATUS.get(code, 500)
    message = ERROR_MAP.get(code, "Unknown error occurred.")
    return HTTPException(
        status_code=status,
        detail={"code": int(code), "message": message},
    )
