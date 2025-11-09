"""Regression coverage for sanitizer paths and error handling."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.security.comprehensive_security import security_hardening
from api.utils.log_sanitization import sanitize_for_log


@pytest.mark.parametrize(
    "filename",
    [
        "../secrets.wav",
        "..\\windows.mp3",
        "../../etc/passwd.flac",
        "",
    ],
)
def test_validate_filename_blocks_traversal(filename: str) -> None:
    """Security input validator must reject traversal and empty filenames."""

    with pytest.raises(HTTPException) as exc:
        security_hardening.input_validator.validate_filename(filename)

    detail = exc.value.detail if isinstance(exc.value.detail, str) else str(exc.value.detail)
    assert "invalid" in detail.lower() or "cannot" in detail.lower()


@pytest.mark.parametrize(
    "payload",
    [
        "attack\r\nX-Injected: value",
        "<script>alert('x')</script>",
        "data:text/html;base64,PHNjcmlwdD4=",
    ],
)
def test_sanitize_for_log_strips_injection_vectors(payload: str) -> None:
    """Log sanitizer must neutralize CRLF, scripts, and data URIs."""

    sanitized = sanitize_for_log(payload)

    assert "\r" not in sanitized and "\n" not in sanitized
    assert "<" not in sanitized and ">" not in sanitized
    if "script" in payload.lower():
        assert "[SCRIPT_REMOVED]" in sanitized.upper()
    if payload.lower().startswith("data:"):
        assert "[DATA_URL_REMOVED]" in sanitized.upper()


def test_validate_string_input_rejects_sql_injection_vector() -> None:
    """The validator should block SQL keywords used in injection attacks."""

    malicious = "SELECT * FROM users WHERE '1'='1'"

    with pytest.raises(HTTPException):
        security_hardening.input_validator.validate_string_input(
            malicious,
            field_name="query",
        )
