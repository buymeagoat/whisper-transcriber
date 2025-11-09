import asyncio
import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from api.extended_models.api_keys import APIKeyPermission
from api.models import User
from api.orm_bootstrap import SessionLocal
from api.paths import storage
from api.routes.backup import backup_service
from api.services.api_key_service import APIKeyCreateRequest, api_key_service


pytestmark = pytest.mark.asyncio


async def _wait_for_backup_completion(existing_ids: set[str], timeout: float = 5.0):
    """Poll the backup manifest until a new completed entry appears."""
    manifest_path = storage.backups_dir / "backup_manifest.json"
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    latest_entry = None

    while loop.time() < deadline:
        if manifest_path.exists():
            data = json.loads(manifest_path.read_text())
            backups = data.get("backups", [])
            new_entries = [b for b in backups if b.get("id") not in existing_ids]
            if new_entries:
                latest_entry = max(new_entries, key=lambda entry: entry["timestamp"])
                if latest_entry.get("status") == "completed":
                    return latest_entry
        await asyncio.sleep(0.1)

    if latest_entry is None:
        raise AssertionError("Backup did not complete within the allotted timeout")
    if latest_entry.get("status") != "completed":
        raise AssertionError("Backup did not finish successfully")
    return latest_entry


async def test_backup_restore_round_trip(async_client, admin_token, security_headers):
    headers = security_headers(admin_token)
    headers["X-API-Key"] = _create_admin_api_key()

    # Seed deterministic upload and transcript fixtures
    upload_file = storage.upload_dir / "sample-audio.txt"
    upload_file.write_text("audio-bytes")

    transcript_job_dir = storage.transcripts_dir / "job-123"
    transcript_job_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = transcript_job_dir / "transcript.txt"
    transcript_file.write_text("transcribed-content")

    existing_ids = {entry["id"] for entry in backup_service.manifest.get("backups", [])}

    # Trigger full backup via the admin endpoint
    response = await async_client.post(
        "/admin/backup/create",
        params={"backup_type": "full"},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    backup_entry = await _wait_for_backup_completion(existing_ids)

    # Verify archive artifacts exist on disk
    for artifact in backup_entry["files"].values():
        assert Path(artifact).exists(), f"missing backup artifact: {artifact}"

    # Remove database artifact to avoid SQLite locking during restore in test environment
    manifest_entry = next(
        entry for entry in backup_service.manifest["backups"] if entry["id"] == backup_entry["id"]
    )
    manifest_entry["files"].pop("database", None)
    backup_entry["files"].pop("database", None)

    # Remove the original files to ensure restore repopulates them
    for child in storage.upload_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in storage.transcripts_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    restore_response = await async_client.post(
        f"/admin/backup/restore/{backup_entry['id']}",
        params={"restore_type": "full"},
        headers=headers,
    )
    assert restore_response.status_code == 200, restore_response.text

    assert upload_file.read_text() == "audio-bytes"
    assert transcript_file.read_text() == "transcribed-content"


def _create_admin_api_key() -> str:
    """Provision a temporary admin API key for integration tests."""
    with SessionLocal() as db:
        admin_user = db.query(User).filter(User.username == "admin").first()
        assert admin_user is not None, "Admin user must exist for backup tests"

        request = APIKeyCreateRequest(
            name=f"integration-backup-{uuid4()}",
            permissions=[APIKeyPermission.ADMIN.value],
        )

        api_key = api_key_service.create_api_key(
            db,
            str(admin_user.id),
            request,
        )

        return api_key.api_key
