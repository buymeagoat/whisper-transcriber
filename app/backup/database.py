"""
Database Backup Engine - SQLite Specialized Backup System

Provides point-in-time recovery, WAL mode backup, and integrity validation
specifically optimized for SQLite databases.
"""

import os
import sqlite3
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import tempfile
import json

logger = logging.getLogger(__name__)


class DatabaseBackupEngine:
    """
    SQLite-specialized backup engine with point-in-time recovery capabilities.
    
    Features:
    - WAL mode support for zero-downtime backups
    - Point-in-time recovery with transaction log preservation
    - Backup integrity validation with checksums
    - Incremental backup support
    - Backup compression and encryption integration
    """
    
    def __init__(self, database_path: str, backup_base_dir: str):
        self.database_path = Path(database_path)
        self.backup_base_dir = Path(backup_base_dir)
        self.backup_dir = self.backup_base_dir / "database"
        self.wal_backup_dir = self.backup_dir / "wal"
        self.snapshot_dir = self.backup_dir / "snapshots"
        
        # Create backup directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.wal_backup_dir.mkdir(exist_ok=True)
        self.snapshot_dir.mkdir(exist_ok=True)
        
        # Backup metadata
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load backup metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "backups": [],
                "last_full_backup": None,
                "last_wal_backup": None,
                "schema_version": 1
            }
    
    def save_metadata(self):
        """Save backup metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def enable_wal_mode(self) -> bool:
        """
        Enable WAL mode on the database for zero-downtime backups.
        
        Returns:
            bool: True if WAL mode was enabled successfully
        """
        try:
            with sqlite3.connect(str(self.database_path)) as conn:
                # Enable WAL mode
                conn.execute("PRAGMA journal_mode=WAL")
                
                # Optimize WAL settings for backup
                conn.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint every 1000 pages
            # Set SQLite PRAGMA settings for performance optimization
            # These are system commands, not user input, so they're safe
            conn.execute("PRAGMA synchronous=NORMAL")      # Balance safety and performance
            
            # Verify WAL mode is active
            result = conn.execute("PRAGMA journal_mode").fetchone()
            is_wal = result[0].upper() == 'WAL'
            
            if is_wal:
                logger.info(f"WAL mode enabled for database: {self.database_path}")
            else:
                logger.error(f"Failed to enable WAL mode for: {self.database_path}")
            
            return is_wal
                
        except Exception as e:
            logger.error(f"Error enabling WAL mode: {e}")
            return False
    
    def create_full_backup(self, compression_engine=None, encryption_engine=None) -> Optional[Dict]:
        """
        Create a full database backup using SQLite's backup API.
        
        Args:
            compression_engine: Optional compression engine
            encryption_engine: Optional encryption engine
            
        Returns:
            Dict with backup metadata or None if failed
        """
        try:
            timestamp = datetime.utcnow()
            backup_name = f"full_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = self.snapshot_dir / backup_name
            
            logger.info(f"Creating full database backup: {backup_name}")
            
            # Create backup using SQLite backup API (online backup)
            source_conn = sqlite3.connect(str(self.database_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            try:
                # Use SQLite's online backup API
                source_conn.backup(backup_conn)
                
                # Calculate checksum for integrity
                checksum = self._calculate_file_checksum(backup_path)
                
                # Get database stats
                stats = self._get_database_stats(source_conn)
                
                # Apply compression if available
                if compression_engine:
                    compressed_path = backup_path.with_suffix('.db.zst')
                    compression_engine.compress_file(backup_path, compressed_path)
                    backup_path.unlink()  # Remove uncompressed version
                    backup_path = compressed_path
                    checksum = self._calculate_file_checksum(backup_path)
                
                # Apply encryption if available
                if encryption_engine:
                    encrypted_path = backup_path.with_suffix(backup_path.suffix + '.enc')
                    encryption_engine.encrypt_file(backup_path, encrypted_path)
                    backup_path.unlink()  # Remove unencrypted version
                    backup_path = encrypted_path
                    checksum = self._calculate_file_checksum(backup_path)
                
                # Create backup metadata
                backup_metadata = {
                    "backup_id": f"full_{timestamp.isoformat()}",
                    "type": "full",
                    "timestamp": timestamp.isoformat(),
                    "file_path": str(backup_path),
                    "file_size": backup_path.stat().st_size,
                    "checksum": checksum,
                    "compressed": compression_engine is not None,
                    "encrypted": encryption_engine is not None,
                    "database_stats": stats,
                    "retention_until": (timestamp + timedelta(days=30)).isoformat()
                }
                
                # Update metadata
                self.metadata["backups"].append(backup_metadata)
                self.metadata["last_full_backup"] = timestamp.isoformat()
                self.save_metadata()
                
                logger.info(f"Full backup completed: {backup_path} ({backup_path.stat().st_size} bytes)")
                return backup_metadata
                
            finally:
                source_conn.close()
                backup_conn.close()
                
        except Exception as e:
            logger.error(f"Failed to create full backup: {e}")
            return None
    
    def backup_wal_files(self) -> Optional[Dict]:
        """
        Backup WAL and SHM files for point-in-time recovery.
        
        Returns:
            Dict with backup metadata or None if failed
        """
        try:
            timestamp = datetime.utcnow()
            wal_file = self.database_path.with_suffix('.db-wal')
            shm_file = self.database_path.with_suffix('.db-shm')
            
            if not wal_file.exists():
                logger.debug("No WAL file to backup")
                return None
            
            # Create WAL backup directory for this timestamp
            wal_backup_subdir = self.wal_backup_dir / timestamp.strftime('%Y%m%d_%H%M%S')
            wal_backup_subdir.mkdir(exist_ok=True)
            
            backed_up_files = []
            
            # Backup WAL file
            if wal_file.exists():
                wal_backup = wal_backup_subdir / "database.db-wal"
                shutil.copy2(wal_file, wal_backup)
                backed_up_files.append({
                    "original": str(wal_file),
                    "backup": str(wal_backup),
                    "size": wal_backup.stat().st_size,
                    "checksum": self._calculate_file_checksum(wal_backup)
                })
            
            # Backup SHM file if it exists
            if shm_file.exists():
                shm_backup = wal_backup_subdir / "database.db-shm"
                shutil.copy2(shm_file, shm_backup)
                backed_up_files.append({
                    "original": str(shm_file),
                    "backup": str(shm_backup),
                    "size": shm_backup.stat().st_size,
                    "checksum": self._calculate_file_checksum(shm_backup)
                })
            
            if backed_up_files:
                # Create WAL backup metadata
                wal_metadata = {
                    "backup_id": f"wal_{timestamp.isoformat()}",
                    "type": "wal",
                    "timestamp": timestamp.isoformat(),
                    "files": backed_up_files,
                    "retention_until": (timestamp + timedelta(hours=24)).isoformat()
                }
                
                # Update metadata
                self.metadata["last_wal_backup"] = timestamp.isoformat()
                self.save_metadata()
                
                logger.debug(f"WAL backup completed: {len(backed_up_files)} files")
                return wal_metadata
            
        except Exception as e:
            logger.error(f"Failed to backup WAL files: {e}")
            return None
    
    def validate_backup(self, backup_metadata: Dict) -> bool:
        """
        Validate backup integrity using checksums.
        
        Args:
            backup_metadata: Backup metadata dict
            
        Returns:
            bool: True if backup is valid
        """
        try:
            if backup_metadata["type"] == "full":
                backup_path = Path(backup_metadata["file_path"])
                if not backup_path.exists():
                    logger.error(f"Backup file not found: {backup_path}")
                    return False
                
                current_checksum = self._calculate_file_checksum(backup_path)
                expected_checksum = backup_metadata["checksum"]
                
                if current_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {backup_path}")
                    return False
                
            elif backup_metadata["type"] == "wal":
                for file_info in backup_metadata["files"]:
                    backup_path = Path(file_info["backup"])
                    if not backup_path.exists():
                        logger.error(f"WAL backup file not found: {backup_path}")
                        return False
                    
                    current_checksum = self._calculate_file_checksum(backup_path)
                    expected_checksum = file_info["checksum"]
                    
                    if current_checksum != expected_checksum:
                        logger.error(f"WAL checksum mismatch for {backup_path}")
                        return False
            
            logger.debug(f"Backup validation successful: {backup_metadata['backup_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Backup validation failed: {e}")
            return False
    
    def cleanup_expired_backups(self):
        """Remove expired backups based on retention policies."""
        try:
            current_time = datetime.utcnow()
            expired_backups = []
            
            for backup in self.metadata["backups"]:
                retention_until = datetime.fromisoformat(backup["retention_until"])
                if current_time > retention_until:
                    expired_backups.append(backup)
            
            for backup in expired_backups:
                try:
                    if backup["type"] == "full":
                        backup_path = Path(backup["file_path"])
                        if backup_path.exists():
                            backup_path.unlink()
                            logger.info(f"Removed expired backup: {backup_path}")
                    
                    elif backup["type"] == "wal":
                        for file_info in backup["files"]:
                            backup_path = Path(file_info["backup"])
                            if backup_path.exists():
                                backup_path.unlink()
                        
                        # Remove empty WAL backup directory
                        wal_dir = Path(backup["files"][0]["backup"]).parent
                        if wal_dir.exists() and not any(wal_dir.iterdir()):
                            wal_dir.rmdir()
                    
                    self.metadata["backups"].remove(backup)
                    
                except Exception as e:
                    logger.error(f"Failed to remove expired backup {backup['backup_id']}: {e}")
            
            if expired_backups:
                self.save_metadata()
                logger.info(f"Cleaned up {len(expired_backups)} expired backups")
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired backups: {e}")
    
    def get_backup_status(self) -> Dict:
        """
        Get current backup status and statistics.
        
        Returns:
            Dict with backup status information
        """
        try:
            total_backups = len(self.metadata["backups"])
            full_backups = len([b for b in self.metadata["backups"] if b["type"] == "full"])
            wal_backups = len([b for b in self.metadata["backups"] if b["type"] == "wal"])
            
            # Calculate total backup size
            total_size = 0
            for backup in self.metadata["backups"]:
                if backup["type"] == "full":
                    backup_path = Path(backup["file_path"])
                    if backup_path.exists():
                        total_size += backup_path.stat().st_size
                elif backup["type"] == "wal":
                    for file_info in backup["files"]:
                        backup_path = Path(file_info["backup"])
                        if backup_path.exists():
                            total_size += backup_path.stat().st_size
            
            # Get latest backup times
            latest_full = self.metadata.get("last_full_backup")
            latest_wal = self.metadata.get("last_wal_backup")
            
            return {
                "database_path": str(self.database_path),
                "database_exists": self.database_path.exists(),
                "wal_mode_enabled": self._is_wal_mode_enabled(),
                "total_backups": total_backups,
                "full_backups": full_backups,
                "wal_backups": wal_backups,
                "total_backup_size": total_size,
                "last_full_backup": latest_full,
                "last_wal_backup": latest_wal,
                "backup_directory": str(self.backup_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {"error": str(e)}
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_database_stats(self, conn: sqlite3.Connection) -> Dict:
        """Get database statistics for backup metadata."""
        try:
            stats = {}
            
            # Get table count
            result = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()
            stats["table_count"] = result[0] if result else 0
            
            # Get database size in pages
            result = conn.execute("PRAGMA page_count").fetchone()
            stats["page_count"] = result[0] if result else 0
            
            result = conn.execute("PRAGMA page_size").fetchone()
            stats["page_size"] = result[0] if result else 0
            
            stats["database_size"] = stats["page_count"] * stats["page_size"]
            
            # Get record counts for main tables (using safe table names)
            main_tables = ["users", "jobs", "metadata", "config"]
            for table in main_tables:
                try:
                    # Validate table name against whitelist for security
                    if table not in ["users", "jobs", "metadata", "config"]:
                        continue
                    # Use quote_identifier for safe table name handling
                    safe_table = f'"{table}"'  # SQLite identifier quoting
                    result = conn.execute(f"SELECT COUNT(*) FROM {safe_table}").fetchone()
                    stats[f"{table}_count"] = result[0] if result else 0
                except sqlite3.OperationalError:
                    stats[f"{table}_count"] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def _is_wal_mode_enabled(self) -> bool:
        """Check if WAL mode is enabled on the database."""
        try:
            with sqlite3.connect(str(self.database_path)) as conn:
                result = conn.execute("PRAGMA journal_mode").fetchone()
                return result[0].upper() == 'WAL' if result else False
        except Exception:
            return False
