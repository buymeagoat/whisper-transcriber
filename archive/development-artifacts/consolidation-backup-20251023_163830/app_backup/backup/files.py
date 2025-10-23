"""
File Backup Engine - Real-time File System Backup

Provides real-time file monitoring and backup with deduplication,
incremental backups, and comprehensive file integrity validation.
"""

import os
import shutil
import hashlib
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Set
import threading
import time

logger = logging.getLogger(__name__)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog library not available, real-time monitoring disabled")


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events for real-time backup."""
    
    def __init__(self, backup_engine):
        self.backup_engine = backup_engine
        self.logger = logging.getLogger(f"{__name__}.FileChangeHandler")
    
    def on_created(self, event):
        if not event.is_directory:
            self.logger.debug(f"File created: {event.src_path}")
            self.backup_engine.queue_file_for_backup(Path(event.src_path))
    
    def on_modified(self, event):
        if not event.is_directory:
            self.logger.debug(f"File modified: {event.src_path}")
            self.backup_engine.queue_file_for_backup(Path(event.src_path))
    
    def on_moved(self, event):
        if not event.is_directory:
            self.logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")
            self.backup_engine.queue_file_for_backup(Path(event.dest_path))


class FileBackupEngine:
    """
    Real-time file backup engine with deduplication and monitoring.
    
    Features:
    - Real-time file change monitoring
    - Content-based deduplication
    - Incremental backup support
    - File integrity validation
    - Configurable backup filters
    - Backup queue management
    """
    
    def __init__(self, watch_directories: List[str], backup_base_dir: str, 
                 enable_realtime: bool = True):
        """
        Initialize file backup engine.
        
        Args:
            watch_directories: List of directories to monitor
            backup_base_dir: Base directory for backups
            enable_realtime: Enable real-time file monitoring
        """
        self.watch_directories = [Path(d) for d in watch_directories]
        self.backup_base_dir = Path(backup_base_dir)
        self.backup_dir = self.backup_base_dir / "files"
        self.enable_realtime = enable_realtime and WATCHDOG_AVAILABLE
        
        # Create backup directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "uploads").mkdir(exist_ok=True)
        (self.backup_dir / "transcripts").mkdir(exist_ok=True)
        (self.backup_dir / "config").mkdir(exist_ok=True)
        (self.backup_dir / "logs").mkdir(exist_ok=True)
        
        # File tracking and deduplication
        self.file_index_file = self.backup_dir / "file_index.json"
        self.content_hash_index_file = self.backup_dir / "content_hash_index.json"
        self.load_indexes()
        
        # Backup queue for real-time processing
        self.backup_queue: Set[Path] = set()
        self.queue_lock = threading.Lock()
        
        # File monitoring
        self.observer = None
        self.event_handler = None
        
        # Backup filters
        self.ignored_extensions = {'.tmp', '.temp', '.lock', '.pyc', '.pyo', '~'}
        self.ignored_patterns = {'__pycache__', '.pytest_cache', '.git', 'node_modules'}
        
        if self.enable_realtime:
            self.start_monitoring()
    
    def load_indexes(self):
        """Load file indexes from disk."""
        # File index: maps file paths to backup metadata
        if self.file_index_file.exists():
            with open(self.file_index_file, 'r') as f:
                self.file_index = json.load(f)
        else:
            self.file_index = {}
        
        # Content hash index: maps content hashes to backup locations
        if self.content_hash_index_file.exists():
            with open(self.content_hash_index_file, 'r') as f:
                self.content_hash_index = json.load(f)
        else:
            self.content_hash_index = {}
    
    def save_indexes(self):
        """Save file indexes to disk."""
        with open(self.file_index_file, 'w') as f:
            json.dump(self.file_index, f, indent=2, default=str)
        
        with open(self.content_hash_index_file, 'w') as f:
            json.dump(self.content_hash_index, f, indent=2)
    
    def start_monitoring(self):
        """Start real-time file monitoring."""
        if not self.enable_realtime:
            logger.warning("Real-time monitoring not available")
            return
        
        try:
            self.event_handler = FileChangeHandler(self)
            self.observer = Observer()
            
            for watch_dir in self.watch_directories:
                if watch_dir.exists():
                    self.observer.schedule(self.event_handler, str(watch_dir), recursive=True)
                    logger.info(f"Started monitoring directory: {watch_dir}")
                else:
                    logger.warning(f"Watch directory does not exist: {watch_dir}")
            
            self.observer.start()
            logger.info("File monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
            self.enable_realtime = False
    
    def stop_monitoring(self):
        """Stop real-time file monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("File monitoring stopped")
    
    def queue_file_for_backup(self, file_path: Path):
        """Add a file to the backup queue."""
        if self.should_backup_file(file_path):
            with self.queue_lock:
                self.backup_queue.add(file_path)
    
    def should_backup_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be backed up.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file should be backed up
        """
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check ignored extensions
        if file_path.suffix.lower() in self.ignored_extensions:
            return False
        
        # Check ignored patterns
        for pattern in self.ignored_patterns:
            if pattern in str(file_path):
                return False
        
        # Check if file is in a watched directory
        for watch_dir in self.watch_directories:
            try:
                file_path.relative_to(watch_dir)
                return True
            except ValueError:
                continue
        
        return False
    
    def backup_file(self, file_path: Path, compression_engine=None) -> Optional[Dict]:
        """
        Backup a single file with deduplication.
        
        Args:
            file_path: Path to the file to backup
            compression_engine: Optional compression engine
            
        Returns:
            Dict with backup metadata or None if skipped
        """
        try:
            if not self.should_backup_file(file_path):
                return None
            
            timestamp = datetime.utcnow()
            file_path = file_path.resolve()
            
            # Calculate file hash for deduplication
            content_hash = self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # Check if file has changed since last backup
            file_key = str(file_path)
            if file_key in self.file_index:
                last_backup = self.file_index[file_key]
                if (last_backup.get("content_hash") == content_hash and 
                    datetime.fromisoformat(last_backup.get("file_mtime", "1970-01-01")) >= file_mtime):
                    logger.debug(f"File unchanged, skipping backup: {file_path}")
                    return None
            
            # Check for content deduplication
            if content_hash in self.content_hash_index:
                existing_backup = self.content_hash_index[content_hash]
                logger.debug(f"Content already backed up, creating reference: {file_path}")
                
                # Create a reference instead of copying the file
                backup_metadata = {
                    "backup_id": f"file_{timestamp.isoformat()}",
                    "type": "file_reference",
                    "timestamp": timestamp.isoformat(),
                    "original_path": str(file_path),
                    "content_hash": content_hash,
                    "file_size": file_size,
                    "file_mtime": file_mtime.isoformat(),
                    "references_backup": existing_backup["backup_path"],
                    "deduplication_saved": file_size
                }
            else:
                # Create new backup
                relative_path = self._get_relative_backup_path(file_path)
                backup_subdir = self.backup_dir / relative_path.parent
                backup_subdir.mkdir(parents=True, exist_ok=True)
                
                backup_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{relative_path.name}"
                backup_path = backup_subdir / backup_filename
                
                # Copy file to backup location
                shutil.copy2(file_path, backup_path)
                
                # Apply compression if available
                if compression_engine:
                    compressed_path = backup_path.with_suffix(backup_path.suffix + compression_engine.extension)
                    compression_stats = compression_engine.compress_file(backup_path, compressed_path)
                    backup_path.unlink()  # Remove uncompressed version
                    backup_path = compressed_path
                
                backup_metadata = {
                    "backup_id": f"file_{timestamp.isoformat()}",
                    "type": "file_backup",
                    "timestamp": timestamp.isoformat(),
                    "original_path": str(file_path),
                    "backup_path": str(backup_path),
                    "content_hash": content_hash,
                    "file_size": file_size,
                    "file_mtime": file_mtime.isoformat(),
                    "backup_size": backup_path.stat().st_size,
                    "compressed": compression_engine is not None,
                    "retention_until": (timestamp + timedelta(days=30)).isoformat()
                }
                
                if compression_engine:
                    backup_metadata["compression_stats"] = compression_stats
                
                # Update content hash index
                self.content_hash_index[content_hash] = {
                    "backup_path": str(backup_path),
                    "first_seen": timestamp.isoformat(),
                    "reference_count": 1
                }
            
            # Update file index
            self.file_index[file_key] = backup_metadata
            self.save_indexes()
            
            logger.info(f"File backup completed: {file_path} -> {backup_metadata.get('backup_path', 'reference')}")
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Failed to backup file {file_path}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def process_backup_queue(self, compression_engine=None) -> List[Dict]:
        """
        Process all files in the backup queue.
        
        Args:
            compression_engine: Optional compression engine
            
        Returns:
            List of backup metadata for processed files
        """
        backups_completed = []
        
        with self.queue_lock:
            files_to_process = list(self.backup_queue)
            self.backup_queue.clear()
        
        logger.info(f"Processing backup queue: {len(files_to_process)} files")
        
        for file_path in files_to_process:
            backup_result = self.backup_file(file_path, compression_engine)
            if backup_result:
                backups_completed.append(backup_result)
        
        return backups_completed
    
    def backup_directory(self, directory: Path, compression_engine=None) -> List[Dict]:
        """
        Backup all files in a directory recursively.
        
        Args:
            directory: Directory to backup
            compression_engine: Optional compression engine
            
        Returns:
            List of backup metadata for all files
        """
        backups_completed = []
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return backups_completed
        
        logger.info(f"Starting directory backup: {directory}")
        
        for root, dirs, files in os.walk(directory):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_patterns]
            
            for file in files:
                file_path = Path(root) / file
                backup_result = self.backup_file(file_path, compression_engine)
                if backup_result:
                    backups_completed.append(backup_result)
        
        logger.info(f"Directory backup completed: {len(backups_completed)} files backed up")
        return backups_completed
    
    def cleanup_expired_backups(self):
        """Remove expired file backups based on retention policies."""
        try:
            current_time = datetime.utcnow()
            expired_files = []
            
            for file_path, backup_info in self.file_index.items():
                if "retention_until" in backup_info:
                    retention_until = datetime.fromisoformat(backup_info["retention_until"])
                    if current_time > retention_until:
                        expired_files.append((file_path, backup_info))
            
            for file_path, backup_info in expired_files:
                try:
                    if backup_info["type"] == "file_backup":
                        backup_path = Path(backup_info["backup_path"])
                        if backup_path.exists():
                            backup_path.unlink()
                            logger.info(f"Removed expired file backup: {backup_path}")
                        
                        # Update content hash index
                        content_hash = backup_info["content_hash"]
                        if content_hash in self.content_hash_index:
                            hash_info = self.content_hash_index[content_hash]
                            hash_info["reference_count"] = hash_info.get("reference_count", 1) - 1
                            if hash_info["reference_count"] <= 0:
                                del self.content_hash_index[content_hash]
                    
                    del self.file_index[file_path]
                    
                except Exception as e:
                    logger.error(f"Failed to remove expired backup for {file_path}: {e}")
            
            if expired_files:
                self.save_indexes()
                logger.info(f"Cleaned up {len(expired_files)} expired file backups")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired file backups: {e}")
    
    def get_backup_status(self) -> Dict:
        """
        Get file backup status and statistics.
        
        Returns:
            Dict with backup status information
        """
        try:
            total_files = len(self.file_index)
            total_unique_content = len(self.content_hash_index)
            
            # Calculate statistics
            total_original_size = 0
            total_backup_size = 0
            deduplication_saved = 0
            
            for backup_info in self.file_index.values():
                total_original_size += backup_info.get("file_size", 0)
                if backup_info["type"] == "file_backup":
                    total_backup_size += backup_info.get("backup_size", 0)
                elif backup_info["type"] == "file_reference":
                    deduplication_saved += backup_info.get("deduplication_saved", 0)
            
            # Queue status
            with self.queue_lock:
                queue_size = len(self.backup_queue)
            
            return {
                "monitored_directories": [str(d) for d in self.watch_directories],
                "realtime_monitoring_enabled": self.enable_realtime,
                "total_files_tracked": total_files,
                "unique_content_items": total_unique_content,
                "backup_queue_size": queue_size,
                "total_original_size": total_original_size,
                "total_backup_size": total_backup_size,
                "deduplication_saved": deduplication_saved,
                "storage_efficiency": (1 - total_backup_size / total_original_size) if total_original_size > 0 else 0,
                "backup_directory": str(self.backup_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file backup status: {e}")
            return {"error": str(e)}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_relative_backup_path(self, file_path: Path) -> Path:
        """Get relative backup path for a file."""
        file_path = file_path.resolve()
        
        # Determine which watch directory this file belongs to
        for watch_dir in self.watch_directories:
            try:
                relative_path = file_path.relative_to(watch_dir.resolve())
                return Path(watch_dir.name) / relative_path
            except ValueError:
                continue
        
        # Fallback: use the file's parent directory name
        return Path("other") / file_path.name
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'observer') and self.observer:
            self.stop_monitoring()
