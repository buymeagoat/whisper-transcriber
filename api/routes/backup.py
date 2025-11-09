"""
Backup Management API - Admin Endpoints for Backup Operations

This module provides a comprehensive backup system for database and file storage,
supporting both manual and scheduled backups with retention policies.
"""

import asyncio
import contextlib
import json
import os
import shutil
import threading
import zstandard
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import create_engine, text
import aiofiles
import schedule

from api.orm_bootstrap import get_db
from api.settings import settings
from api.routes.auth import get_current_admin_user
from api.utils.logger import get_system_logger
from api.paths import storage

logger = get_system_logger("backup_service")

# Create backup management router
backup_router = APIRouter(prefix="/admin/backup", tags=["backup"])

# Backup configuration
BACKUP_DIR = storage.backups_dir
DB_BACKUP_DIR = BACKUP_DIR / "database"
FILES_BACKUP_DIR = BACKUP_DIR / "files"
MANIFEST_FILE = BACKUP_DIR / "backup_manifest.json"

# Create backup directories
for directory in [BACKUP_DIR, DB_BACKUP_DIR, FILES_BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class BackupService:
    """Service for managing backups and restores."""

    def __init__(self):
        """Initialize the backup service."""
        self.manifest = self._load_manifest()
        self.scheduler = schedule.Scheduler()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_stop = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._setup_scheduled_backups()

    def _load_manifest(self) -> Dict:
        """Load or create the backup manifest."""
        if MANIFEST_FILE.exists():
            try:
                with open(MANIFEST_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading manifest: {e}")
                return {"backups": []}
        return {"backups": []}

    def _save_manifest(self):
        """Save the backup manifest."""
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def _setup_scheduled_backups(self):
        """Setup scheduled backup jobs."""
        # Daily database backup at 2 AM
        self.scheduler.every().day.at("02:00").do(
            self._run_scheduled_backup,
            "database",
        )
        # Weekly full backup on Sunday at 3 AM
        self.scheduler.every().sunday.at("03:00").do(
            self._run_scheduled_backup,
            "full",
        )

    def configure_event_loop(self, loop: Optional[asyncio.AbstractEventLoop]) -> None:
        """Persist the event loop used for scheduled tasks."""
        self._loop = loop

    def start_scheduler(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> bool:
        """Start the background scheduler thread if enabled."""
        if loop is not None:
            self.configure_event_loop(loop)
        elif self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                try:
                    self._loop = asyncio.get_event_loop()
                except RuntimeError:
                    logger.error("No event loop available for backup scheduler")
                    return False

        if self._loop is None:
            logger.warning("Backup scheduler cannot start without an event loop")
            return False

        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return True

        self._scheduler_stop.clear()
        self._scheduler_thread = threading.Thread(
            target=self._run_scheduler_loop,
            name="backup-scheduler",
            daemon=True,
        )
        self._scheduler_thread.start()
        logger.info("Backup scheduler thread started")
        return True

    def stop_scheduler(self) -> None:
        """Stop the background scheduler thread."""
        self._scheduler_stop.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)
        self._scheduler_thread = None

    def _run_scheduler_loop(self) -> None:
        """Run scheduled jobs until shutdown."""
        while not self._scheduler_stop.is_set():
            try:
                self.scheduler.run_pending()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error(f"Backup scheduler run failed: {exc}")
            self._scheduler_stop.wait(60)

    def _enqueue_scheduled_backup(self, backup_type: str) -> None:
        """Submit a scheduled backup to the application event loop."""
        if self._loop is None or self._loop.is_closed():
            logger.warning(
                "Skipping scheduled backup because event loop is unavailable"
            )
            return

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.create_backup(backup_type=backup_type),
                self._loop,
            )

            def _log_future_result(_future: asyncio.Future) -> None:
                with contextlib.suppress(Exception):
                    _future.result()

            future.add_done_callback(_log_future_result)
        except Exception as exc:
            logger.error(f"Failed to schedule backup task: {exc}")

    def _run_scheduled_backup(self, backup_type: str) -> bool:
        """Run a scheduled backup job via the configured loop."""
        logger.info(f"Scheduled backup triggered: {backup_type}")
        self._enqueue_scheduled_backup(backup_type)
        return True

    async def _compress_directory(self, source_dir: Path, output_file: Path):
        """Compress a directory using Zstandard compression."""
        cctx = zstandard.ZstdCompressor(level=3)
        with open(output_file, 'wb') as f:
            with cctx.stream_writer(f) as compressor:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(source_dir)
                        file_info = {
                            'path': str(relative_path),
                            'size': file_path.stat().st_size
                        }
                        # Write file metadata
                        compressor.write(json.dumps(file_info).encode() + b'\n')
                        # Write file content
                        async with aiofiles.open(file_path, 'rb') as src:
                            while chunk := await src.read(8192):
                                compressor.write(chunk)

    async def _decompress_directory(self, backup_file: Path, target_dir: Path):
        """Decompress a Zstandard compressed backup."""
        dctx = zstandard.ZstdDecompressor()
        target_dir.mkdir(parents=True, exist_ok=True)
        
        with open(backup_file, 'rb') as f:
            with dctx.stream_reader(f) as decompressor:
                while True:
                    try:
                        # Read file metadata
                        metadata_line = b''
                        while True:
                            char = decompressor.read(1)
                            if not char:
                                return
                            if char == b'\n':
                                break
                            metadata_line += char
                        
                        file_info = json.loads(metadata_line.decode())
                        file_path = target_dir / file_info['path']
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Read and write file content
                        remaining = file_info['size']
                        with open(file_path, 'wb') as dest:
                            while remaining > 0:
                                chunk_size = min(remaining, 8192)
                                chunk = decompressor.read(chunk_size)
                                if not chunk:
                                    break
                                dest.write(chunk)
                                remaining -= len(chunk)
                    
                    except EOFError:
                        break

    async def create_backup(
        self,
        backup_type: str = "full",
        description: Optional[str] = None
    ) -> Dict:
        """Create a new backup."""
        try:
            backup_id = str(uuid4())
            timestamp = datetime.utcnow()
            backup_info = {
                "id": backup_id,
                "type": backup_type,
                "timestamp": timestamp.isoformat(),
                "description": description,
                "status": "in_progress",
                "files": {}
            }

            # Database backup
            if backup_type in ["full", "database"]:
                db_file = DB_BACKUP_DIR / f"{backup_id}_db.sql.zst"
                await self._backup_database(db_file)
                backup_info["files"]["database"] = str(db_file)

            # Files backup (for full backups only)
            if backup_type == "full":
                # Backup uploads
                uploads_backup = FILES_BACKUP_DIR / f"{backup_id}_uploads.tar.zst"
                await self._compress_directory(storage.upload_dir, uploads_backup)
                backup_info["files"]["uploads"] = str(uploads_backup)

                # Backup transcripts
                transcripts_backup = FILES_BACKUP_DIR / f"{backup_id}_transcripts.tar.zst"
                await self._compress_directory(storage.transcripts_dir, transcripts_backup)
                backup_info["files"]["transcripts"] = str(transcripts_backup)

            backup_info["status"] = "completed"
            self.manifest["backups"].append(backup_info)
            self._save_manifest()

            # Apply retention policy
            await self.apply_retention_policy()

            return backup_info

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if "backup_info" in locals():
                backup_info["status"] = "failed"
                backup_info["error"] = str(e)
                self.manifest["backups"].append(backup_info)
                self._save_manifest()
            raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

    async def _backup_database(self, backup_file: Path):
        """Create a compressed database backup."""
        try:
            # Create a temporary SQL dump
            temp_sql = BACKUP_DIR / f"temp_{uuid4()}.sql"
            
            # Get database URL from settings
            db_url = str(settings.database_url)
            
            # Create engine for backup
            engine = create_engine(db_url)
            
            # Dump schema and data
            with engine.connect() as conn:
                with open(temp_sql, 'w') as f:
                    # Get schema
                    schema_result = conn.execute(text("""
                        SELECT sql FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """))
                    for row in schema_result:
                        f.write(f"{row[0]};\n")

                    # Get data
                    table_result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """))
                    for table_row in table_result:
                        table_name = table_row[0]
                        data_result = conn.execute(text(f"SELECT * FROM {table_name}"))
                        for data_row in data_result:
                            values = [
                                "'{}'".format(str(v).replace("'", "''")) if v is not None else "NULL"
                                for v in data_row
                            ]
                            f.write(f"INSERT INTO {table_name} VALUES ({','.join(values)});\n")

            # Compress the SQL dump
            cctx = zstandard.ZstdCompressor(level=3)
            with open(temp_sql, 'rb') as src, open(backup_file, 'wb') as dest:
                cctx.copy_stream(src, dest)

            # Cleanup
            temp_sql.unlink()

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            if "temp_sql" in locals() and temp_sql.exists():
                temp_sql.unlink()
            raise

    async def restore_backup(
        self,
        backup_id: str,
        restore_type: str = "full"
    ) -> Dict:
        """Restore from a backup."""
        try:
            # Find backup in manifest
            backup = next(
                (b for b in self.manifest["backups"] if b["id"] == backup_id),
                None
            )
            if not backup:
                raise HTTPException(status_code=404, detail="Backup not found")

            # Verify backup files exist
            for file_type, file_path in backup["files"].items():
                if not Path(file_path).exists():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Backup file missing: {file_type}"
                    )

            # Database restore
            if restore_type in ["full", "database"] and "database" in backup["files"]:
                await self._restore_database(Path(backup["files"]["database"]))

            # Files restore (full restore only)
            if restore_type == "full":
                if "uploads" in backup["files"]:
                    # Clear existing uploads
                    if storage.upload_dir.exists():
                        shutil.rmtree(storage.upload_dir)
                    storage.upload_dir.mkdir(parents=True, exist_ok=True)
                    # Restore uploads
                    await self._decompress_directory(
                        Path(backup["files"]["uploads"]),
                        storage.upload_dir
                    )

                if "transcripts" in backup["files"]:
                    # Clear existing transcripts
                    if storage.transcripts_dir.exists():
                        shutil.rmtree(storage.transcripts_dir)
                    storage.transcripts_dir.mkdir(parents=True, exist_ok=True)
                    # Restore transcripts
                    await self._decompress_directory(
                        Path(backup["files"]["transcripts"]),
                        storage.transcripts_dir
                    )

            return {
                "status": "success",
                "message": f"Restored {restore_type} backup {backup_id}",
                "timestamp": datetime.utcnow().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

    async def _restore_database(self, backup_file: Path):
        """Restore database from backup."""
        try:
            # Decompress backup
            temp_sql = BACKUP_DIR / f"temp_{uuid4()}.sql"
            dctx = zstandard.ZstdDecompressor()
            with open(backup_file, 'rb') as src, open(temp_sql, 'wb') as dest:
                dctx.copy_stream(src, dest)

            # Get database URL from settings
            db_url = str(settings.database_url)
            engine = create_engine(db_url)

            # Drop all tables
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """))
                for row in result:
                    conn.execute(text(f"DROP TABLE IF EXISTS {row[0]}"))

            # Execute restore script
            with engine.connect() as conn:
                with open(temp_sql, 'r') as f:
                    script = f.read()
                    for statement in script.split(';'):
                        if statement.strip():
                            conn.execute(text(statement))
                conn.commit()

            # Cleanup
            temp_sql.unlink()

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            if "temp_sql" in locals() and temp_sql.exists():
                temp_sql.unlink()
            raise

    async def apply_retention_policy(self):
        """Apply backup retention policy."""
        try:
            # Keep last 7 daily backups
            daily_retention = timedelta(days=7)
            # Keep last 4 weekly full backups
            weekly_retention = timedelta(days=28)

            now = datetime.utcnow()
            retained_backups = []
            deleted_backups = []

            for backup in sorted(
                self.manifest["backups"],
                key=lambda x: datetime.fromisoformat(x["timestamp"]),
                reverse=True
            ):
                backup_age = now - datetime.fromisoformat(backup["timestamp"])
                
                # Keep recent daily backups
                if backup["type"] == "database" and backup_age <= daily_retention:
                    retained_backups.append(backup)
                # Keep recent weekly backups
                elif backup["type"] == "full" and backup_age <= weekly_retention:
                    retained_backups.append(backup)
                else:
                    # Delete old backup files
                    for file_path in backup["files"].values():
                        try:
                            Path(file_path).unlink(missing_ok=True)
                        except Exception as e:
                            logger.warning(f"Failed to delete old backup file {file_path}: {e}")
                    deleted_backups.append(backup)

            # Update manifest
            self.manifest["backups"] = retained_backups
            self._save_manifest()

            return {
                "retained": len(retained_backups),
                "deleted": len(deleted_backups)
            }

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")
            raise

# Initialize backup service
backup_service = BackupService()

@backup_router.get("/status")
async def backup_status(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get backup service status."""
    try:
        manifest = backup_service.manifest
        last_backup = None
        if manifest["backups"]:
            last_backup = max(
                manifest["backups"],
                key=lambda x: datetime.fromisoformat(x["timestamp"])
            )

        return {
            "status": "active",
            "total_backups": len(manifest["backups"]),
            "last_backup": last_backup,
            "backup_dir": str(BACKUP_DIR),
            "storage_usage": {
                "database": sum(p.stat().st_size for p in DB_BACKUP_DIR.glob("*")),
                "files": sum(p.stat().st_size for p in FILES_BACKUP_DIR.glob("*"))
            }
        }
    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@backup_router.post("/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    backup_type: str = Query("full", regex="^(full|database)$"),
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """Initiate a new backup."""
    try:
        # Start backup in background
        task = asyncio.create_task(
            backup_service.create_backup(
                backup_type=backup_type,
                description=description
            )
        )
        background_tasks.add_task(lambda: task)

        return {
            "status": "initiated",
            "backup_type": backup_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initiating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@backup_router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    restore_type: str = Query("full", regex="^(full|database)$"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Restore from a backup."""
    try:
        return await backup_service.restore_backup(
            backup_id=backup_id,
            restore_type=restore_type
        )
    except Exception as e:
        logger.error(f"Error initiating restore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@backup_router.get("/list")
async def list_backups(
    current_user: dict = Depends(get_current_admin_user)
):
    """List available backups."""
    try:
        return {
            "backups": backup_service.manifest["backups"]
        }
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@backup_router.delete("/cleanup")
async def cleanup_old_backups(
    current_user: dict = Depends(get_current_admin_user)
):
    """Clean up old backups according to retention policy."""
    try:
        result = await backup_service.apply_retention_policy()
        return {
            "status": "success",
            "cleaned": result
        }
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@backup_router.get("/health")
async def backup_health():
    """Backup service health check."""
    try:
        # Check backup directories
        for directory in [BACKUP_DIR, DB_BACKUP_DIR, FILES_BACKUP_DIR]:
            if not directory.exists() or not os.access(directory, os.W_OK):
                raise HTTPException(
                    status_code=503,
                    detail=f"Backup directory {directory} not accessible"
                )

        # Check manifest
        if not MANIFEST_FILE.exists():
            backup_service._save_manifest()

        # Check disk space
        disk_usage = shutil.disk_usage(BACKUP_DIR)
        free_space_gb = disk_usage.free / (1024**3)
        
        if free_space_gb < 1:  # Less than 1GB free
            return {
                "status": "warning",
                "message": f"Low disk space: {free_space_gb:.2f}GB free"
            }

        return {
            "status": "healthy",
            "disk_space_free_gb": round(free_space_gb, 2),
            "manifest_exists": MANIFEST_FILE.exists(),
            "backup_dirs_ready": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Backup service health check failed: {str(e)}"
        )


def initialize_backup_service() -> bool:
    """Initialize the backup subsystem."""
    try:
        backup_service.configure_event_loop(None)
        logger.info("Backup service initialized")
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Failed to initialize backup service: {exc}")
        return False


def start_backup_service_if_configured(
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> bool:
    """Start the backup scheduler when enabled via configuration."""
    try:
        scheduler_enabled = getattr(settings, "backup_scheduler_enabled", True)
        if not scheduler_enabled:
            logger.info("Backup scheduler disabled via configuration")
            return False

        started = backup_service.start_scheduler(loop=loop)
        if started:
            logger.info("Backup scheduler started")
        return started
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Failed to start backup scheduler: {exc}")
        return False


def shutdown_backup_service() -> None:
    """Stop the backup scheduler."""
    try:
        backup_service.stop_scheduler()
        logger.info("Backup scheduler stopped")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"Error during backup scheduler shutdown: {exc}")


__all__ = [
    "backup_router",
    "initialize_backup_service",
    "start_backup_service_if_configured",
    "shutdown_backup_service",
]
