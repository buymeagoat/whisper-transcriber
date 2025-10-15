"""
Backup Orchestrator - Central Backup Coordination System

Coordinates all backup operations including database backups, file backups,
scheduling, storage backends, and monitoring. Provides a unified interface
for backup and recovery operations.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Union
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .database import DatabaseBackupEngine
from .files import FileBackupEngine
from .storage import StorageBackend, LocalStorageBackend
from .compression import CompressionEngine

logger = logging.getLogger(__name__)


class BackupOrchestrator:
    """
    Central backup orchestration system.
    
    Features:
    - Coordinated database and file backups
    - Multiple storage backend support
    - Automated scheduling and retention
    - Progress monitoring and reporting
    - Disaster recovery coordination
    - Configuration management
    """
    
    def __init__(self, config: Dict):
        """
        Initialize backup orchestrator.
        
        Args:
            config: Backup configuration dictionary
        """
        self.config = config
        self.backup_base_dir = Path(config.get("backup_base_dir", "/backups"))
        self.backup_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.database_engine = None
        self.file_engine = None
        self.compression_engine = None
        self.storage_backends: List[StorageBackend] = []
        
        # State management
        self.state_file = self.backup_base_dir / "orchestrator_state.json"
        self.load_state()
        
        # Operation tracking
        self.current_operations = {}
        self.operation_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "total_backups": 0,
            "successful_backups": 0,
            "failed_backups": 0,
            "total_size_backed_up": 0,
            "last_full_backup": None,
            "last_incremental_backup": None
        }
        
        self._initialize_components()
        logger.info("Backup orchestrator initialized")
    
    def load_state(self):
        """Load orchestrator state from disk."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "initialized": False,
                "last_cleanup": None,
                "backup_history": [],
                "configuration_version": 1
            }
    
    def save_state(self):
        """Save orchestrator state to disk."""
        self.state["last_updated"] = datetime.utcnow().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def _initialize_components(self):
        """Initialize backup components based on configuration."""
        try:
            # Initialize database backup engine
            if "database" in self.config:
                db_config = self.config["database"]
                self.database_engine = DatabaseBackupEngine(
                    database_path=db_config.get("path", "app.db"),
                    backup_base_dir=str(self.backup_base_dir)
                )
                
                # Enable WAL mode for zero-downtime backups
                if db_config.get("enable_wal", True):
                    self.database_engine.enable_wal_mode()
            
            # Initialize file backup engine
            if "files" in self.config:
                file_config = self.config["files"]
                watch_dirs = file_config.get("watch_directories", [])
                self.file_engine = FileBackupEngine(
                    watch_directories=watch_dirs,
                    backup_base_dir=str(self.backup_base_dir),
                    enable_realtime=file_config.get("enable_realtime", True)
                )
            
            # Initialize compression engine
            if self.config.get("compression", {}).get("enabled", True):
                compression_config = self.config.get("compression", {})
                self.compression_engine = CompressionEngine(
                    compression_level=compression_config.get("level", 3),
                    use_zstd=compression_config.get("use_zstd", True)
                )
            
            # Initialize storage backends
            for backend_config in self.config.get("storage_backends", []):
                backend = self._create_storage_backend(backend_config)
                if backend:
                    self.storage_backends.append(backend)
            
            # Default to local storage if no backends configured
            if not self.storage_backends:
                local_backend = LocalStorageBackend(
                    base_path=str(self.backup_base_dir / "local_storage")
                )
                self.storage_backends.append(local_backend)
            
            self.state["initialized"] = True
            self.save_state()
            
        except Exception as e:
            logger.error(f"Failed to initialize backup components: {e}")
            raise
    
    def _create_storage_backend(self, backend_config: Dict) -> Optional[StorageBackend]:
        """Create a storage backend from configuration."""
        try:
            backend_type = backend_config.get("type", "local")
            
            if backend_type == "local":
                from .storage import LocalStorageBackend
                return LocalStorageBackend(
                    base_path=backend_config.get("path", str(self.backup_base_dir / "local")),
                    create_directories=backend_config.get("create_directories", True)
                )
            
            elif backend_type == "s3":
                from .storage import S3StorageBackend
                return S3StorageBackend(
                    bucket_name=backend_config["bucket_name"],
                    access_key=backend_config["access_key"],
                    secret_key=backend_config["secret_key"],
                    endpoint_url=backend_config.get("endpoint_url"),
                    region=backend_config.get("region", "us-east-1")
                )
            
            elif backend_type == "sftp":
                from .storage import SFTPStorageBackend
                return SFTPStorageBackend(
                    hostname=backend_config["hostname"],
                    username=backend_config["username"],
                    password=backend_config.get("password"),
                    private_key_path=backend_config.get("private_key_path"),
                    port=backend_config.get("port", 22),
                    remote_base_path=backend_config.get("remote_base_path", "/backups")
                )
            
            else:
                logger.error(f"Unknown storage backend type: {backend_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create storage backend: {e}")
            return None
    
    def create_full_backup(self, upload_to_storage: bool = True) -> Dict:
        """
        Create a complete system backup.
        
        Args:
            upload_to_storage: Whether to upload to configured storage backends
            
        Returns:
            Dict with backup operation results
        """
        operation_id = f"full_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self.operation_lock:
                self.current_operations[operation_id] = {
                    "type": "full_backup",
                    "started": datetime.utcnow().isoformat(),
                    "status": "in_progress",
                    "progress": 0
                }
            
            logger.info(f"Starting full backup operation: {operation_id}")
            
            backup_results = {
                "operation_id": operation_id,
                "type": "full_backup",
                "started": datetime.utcnow().isoformat(),
                "database_backup": None,
                "file_backups": [],
                "storage_uploads": [],
                "compression_stats": None,
                "total_size": 0,
                "success": False
            }
            
            # Step 1: Database backup
            if self.database_engine:
                logger.info("Creating database backup...")
                self._update_operation_progress(operation_id, 10, "Creating database backup")
                
                db_backup = self.database_engine.create_full_backup(
                    compression_engine=self.compression_engine
                )
                
                if db_backup:
                    backup_results["database_backup"] = db_backup
                    backup_results["total_size"] += db_backup.get("file_size", 0)
                    logger.info("Database backup completed successfully")
                else:
                    logger.error("Database backup failed")
                    backup_results["error"] = "Database backup failed"
                    return backup_results
            
            # Step 2: File backups
            if self.file_engine:
                logger.info("Creating file backups...")
                self._update_operation_progress(operation_id, 30, "Creating file backups")
                
                # Process any queued files first
                queued_backups = self.file_engine.process_backup_queue(
                    compression_engine=self.compression_engine
                )
                backup_results["file_backups"].extend(queued_backups)
                
                # Backup all watched directories
                for watch_dir in self.file_engine.watch_directories:
                    self._update_operation_progress(operation_id, 50, f"Backing up {watch_dir}")
                    
                    dir_backups = self.file_engine.backup_directory(
                        directory=watch_dir,
                        compression_engine=self.compression_engine
                    )
                    backup_results["file_backups"].extend(dir_backups)
                
                # Calculate total file backup size
                for file_backup in backup_results["file_backups"]:
                    if file_backup.get("type") == "file_backup":
                        backup_results["total_size"] += file_backup.get("backup_size", 0)
                
                logger.info(f"File backups completed: {len(backup_results['file_backups'])} files")
            
            # Step 3: Upload to storage backends
            if upload_to_storage and self.storage_backends:
                logger.info("Uploading backups to storage backends...")
                self._update_operation_progress(operation_id, 70, "Uploading to storage")
                
                upload_results = self._upload_backups_to_storage(backup_results)
                backup_results["storage_uploads"] = upload_results
            
            # Step 4: Update statistics and state
            self._update_operation_progress(operation_id, 90, "Finalizing backup")
            
            backup_results["completed"] = datetime.utcnow().isoformat()
            backup_results["success"] = True
            
            # Update statistics
            self.stats["total_backups"] += 1
            self.stats["successful_backups"] += 1
            self.stats["total_size_backed_up"] += backup_results["total_size"]
            self.stats["last_full_backup"] = backup_results["completed"]
            
            # Add to backup history
            self.state["backup_history"].append(backup_results)
            self.save_state()
            
            self._update_operation_progress(operation_id, 100, "Backup completed successfully")
            
            logger.info(f"Full backup completed successfully: {operation_id}")
            return backup_results
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            
            backup_results["error"] = str(e)
            backup_results["success"] = False
            
            self.stats["total_backups"] += 1
            self.stats["failed_backups"] += 1
            
            self._update_operation_progress(operation_id, 100, f"Backup failed: {e}")
            
            return backup_results
        
        finally:
            with self.operation_lock:
                if operation_id in self.current_operations:
                    self.current_operations[operation_id]["status"] = "completed"
    
    def create_incremental_backup(self, upload_to_storage: bool = True) -> Dict:
        """
        Create an incremental backup (WAL files and changed files only).
        
        Args:
            upload_to_storage: Whether to upload to configured storage backends
            
        Returns:
            Dict with backup operation results
        """
        operation_id = f"incremental_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self.operation_lock:
                self.current_operations[operation_id] = {
                    "type": "incremental_backup",
                    "started": datetime.utcnow().isoformat(),
                    "status": "in_progress",
                    "progress": 0
                }
            
            logger.info(f"Starting incremental backup operation: {operation_id}")
            
            backup_results = {
                "operation_id": operation_id,
                "type": "incremental_backup",
                "started": datetime.utcnow().isoformat(),
                "wal_backup": None,
                "file_backups": [],
                "storage_uploads": [],
                "total_size": 0,
                "success": False
            }
            
            # Step 1: WAL backup
            if self.database_engine:
                logger.info("Creating WAL backup...")
                self._update_operation_progress(operation_id, 20, "Creating WAL backup")
                
                wal_backup = self.database_engine.backup_wal_files()
                if wal_backup:
                    backup_results["wal_backup"] = wal_backup
                    # Calculate WAL backup size
                    for file_info in wal_backup.get("files", []):
                        backup_results["total_size"] += file_info.get("size", 0)
            
            # Step 2: Process file backup queue
            if self.file_engine:
                logger.info("Processing file backup queue...")
                self._update_operation_progress(operation_id, 50, "Processing file changes")
                
                queued_backups = self.file_engine.process_backup_queue(
                    compression_engine=self.compression_engine
                )
                backup_results["file_backups"] = queued_backups
                
                # Calculate file backup size
                for file_backup in backup_results["file_backups"]:
                    if file_backup.get("type") == "file_backup":
                        backup_results["total_size"] += file_backup.get("backup_size", 0)
            
            # Step 3: Upload to storage backends
            if upload_to_storage and self.storage_backends:
                logger.info("Uploading incremental backups to storage...")
                self._update_operation_progress(operation_id, 80, "Uploading to storage")
                
                upload_results = self._upload_backups_to_storage(backup_results)
                backup_results["storage_uploads"] = upload_results
            
            # Step 4: Finalize
            backup_results["completed"] = datetime.utcnow().isoformat()
            backup_results["success"] = True
            
            # Update statistics
            self.stats["total_backups"] += 1
            self.stats["successful_backups"] += 1
            self.stats["total_size_backed_up"] += backup_results["total_size"]
            self.stats["last_incremental_backup"] = backup_results["completed"]
            
            self._update_operation_progress(operation_id, 100, "Incremental backup completed")
            
            logger.info(f"Incremental backup completed: {operation_id}")
            return backup_results
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            
            backup_results["error"] = str(e)
            backup_results["success"] = False
            
            self.stats["total_backups"] += 1
            self.stats["failed_backups"] += 1
            
            return backup_results
        
        finally:
            with self.operation_lock:
                if operation_id in self.current_operations:
                    self.current_operations[operation_id]["status"] = "completed"
    
    def cleanup_expired_backups(self) -> Dict:
        """
        Clean up expired backups across all components.
        
        Returns:
            Dict with cleanup results
        """
        logger.info("Starting backup cleanup...")
        
        cleanup_results = {
            "started": datetime.utcnow().isoformat(),
            "database_cleanup": False,
            "file_cleanup": False,
            "storage_cleanup": [],
            "success": False
        }
        
        try:
            # Database backup cleanup
            if self.database_engine:
                self.database_engine.cleanup_expired_backups()
                cleanup_results["database_cleanup"] = True
            
            # File backup cleanup
            if self.file_engine:
                self.file_engine.cleanup_expired_backups()
                cleanup_results["file_cleanup"] = True
            
            # Storage backend cleanup (implementation depends on backend)
            for backend in self.storage_backends:
                try:
                    # This would require implementing cleanup in each backend
                    # For now, just mark as attempted
                    cleanup_results["storage_cleanup"].append({
                        "backend_type": backend.get_backend_info().get("backend_type"),
                        "status": "attempted"
                    })
                except Exception as e:
                    logger.error(f"Storage cleanup failed for backend: {e}")
            
            cleanup_results["completed"] = datetime.utcnow().isoformat()
            cleanup_results["success"] = True
            
            # Update state
            self.state["last_cleanup"] = cleanup_results["completed"]
            self.save_state()
            
            logger.info("Backup cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            cleanup_results["error"] = str(e)
        
        return cleanup_results
    
    def get_backup_status(self) -> Dict:
        """
        Get comprehensive backup system status.
        
        Returns:
            Dict with complete backup system status
        """
        try:
            status = {
                "orchestrator": {
                    "initialized": self.state.get("initialized", False),
                    "backup_base_dir": str(self.backup_base_dir),
                    "current_operations": len(self.current_operations),
                    "statistics": self.stats.copy()
                },
                "database": None,
                "files": None,
                "compression": None,
                "storage_backends": []
            }
            
            # Database engine status
            if self.database_engine:
                status["database"] = self.database_engine.get_backup_status()
            
            # File engine status
            if self.file_engine:
                status["files"] = self.file_engine.get_backup_status()
            
            # Compression engine status
            if self.compression_engine:
                status["compression"] = self.compression_engine.get_compression_info()
            
            # Storage backend status
            for backend in self.storage_backends:
                backend_status = backend.get_backend_info()
                status["storage_backends"].append(backend_status)
            
            # Current operations
            with self.operation_lock:
                status["current_operations"] = self.current_operations.copy()
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {"error": str(e)}
    
    def _upload_backups_to_storage(self, backup_results: Dict) -> List[Dict]:
        """Upload backup files to configured storage backends."""
        upload_results = []
        
        with ThreadPoolExecutor(max_workers=min(len(self.storage_backends), 4)) as executor:
            futures = []
            
            for backend in self.storage_backends:
                future = executor.submit(self._upload_to_backend, backend, backup_results)
                futures.append((backend, future))
            
            for backend, future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    upload_results.append(result)
                except Exception as e:
                    logger.error(f"Upload to {backend.__class__.__name__} failed: {e}")
                    upload_results.append({
                        "backend_type": backend.__class__.__name__,
                        "success": False,
                        "error": str(e)
                    })
        
        return upload_results
    
    def _upload_to_backend(self, backend: StorageBackend, backup_results: Dict) -> Dict:
        """Upload backup files to a specific storage backend."""
        try:
            upload_result = {
                "backend_type": backend.__class__.__name__,
                "files_uploaded": 0,
                "total_size": 0,
                "success": False
            }
            
            # Upload database backup
            if backup_results.get("database_backup"):
                db_backup = backup_results["database_backup"]
                if "file_path" in db_backup:
                    local_path = Path(db_backup["file_path"])
                    remote_path = f"database/{local_path.name}"
                    
                    if backend.upload_file(local_path, remote_path):
                        upload_result["files_uploaded"] += 1
                        upload_result["total_size"] += local_path.stat().st_size
            
            # Upload file backups
            for file_backup in backup_results.get("file_backups", []):
                if file_backup.get("type") == "file_backup" and "backup_path" in file_backup:
                    local_path = Path(file_backup["backup_path"])
                    remote_path = f"files/{local_path.relative_to(self.backup_base_dir)}"
                    
                    if backend.upload_file(local_path, remote_path):
                        upload_result["files_uploaded"] += 1
                        upload_result["total_size"] += local_path.stat().st_size
            
            upload_result["success"] = True
            return upload_result
            
        except Exception as e:
            logger.error(f"Upload to backend failed: {e}")
            return {
                "backend_type": backend.__class__.__name__,
                "success": False,
                "error": str(e)
            }
    
    def _update_operation_progress(self, operation_id: str, progress: int, status: str):
        """Update operation progress and status."""
        with self.operation_lock:
            if operation_id in self.current_operations:
                self.current_operations[operation_id].update({
                    "progress": progress,
                    "status": status,
                    "last_updated": datetime.utcnow().isoformat()
                })
    
    def stop(self):
        """Stop the backup orchestrator and cleanup resources."""
        logger.info("Stopping backup orchestrator...")
        
        if self.file_engine:
            self.file_engine.stop_monitoring()
        
        logger.info("Backup orchestrator stopped")
