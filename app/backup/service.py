"""
Backup Service - Main Entry Point for Backup System

Provides a high-level interface for backup operations, integrating all
backup components with scheduling, monitoring, and administration features.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import schedule
import signal
import sys

from .config import get_backup_config, validate_backup_config
from .orchestrator import BackupOrchestrator
from .recovery import RecoveryManager

logger = logging.getLogger(__name__)


class BackupService:
    """
    Main backup service providing high-level backup operations.
    
    Features:
    - Automated scheduled backups
    - Manual backup triggering
    - Recovery operations
    - Health monitoring
    - Administrative interface
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize backup service.
        
        Args:
            config: Optional backup configuration (uses default if None)
        """
        # Load and validate configuration
        self.config = config or get_backup_config()
        is_valid, errors = validate_backup_config(self.config)
        
        if not is_valid:
            raise ValueError(f"Invalid backup configuration: {', '.join(errors)}")
        
        # Initialize components
        self.orchestrator = BackupOrchestrator(self.config)
        self.recovery_manager = RecoveryManager(
            backup_base_dir=self.config["backup_base_dir"],
            target_system_dir=str(self.config.get("target_system_dir", "/"))
        )
        
        # Service state
        self.is_running = False
        self.scheduler_thread = None
        self.shutdown_event = threading.Event()
        
        # Statistics
        self.service_stats = {
            "started": None,
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "last_full_backup": None,
            "last_incremental_backup": None,
            "last_cleanup": None
        }
        
        # Setup scheduling
        self._setup_scheduling()
        
        logger.info("Backup service initialized")
    
    def start(self):
        """Start the backup service with scheduling."""
        if self.is_running:
            logger.warning("Backup service is already running")
            return
        
        logger.info("Starting backup service...")
        
        self.is_running = True
        self.service_stats["started"] = datetime.utcnow().isoformat()
        
        # Start scheduler thread
        if self.config.get("scheduling", {}).get("enabled", True):
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Backup scheduler started")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Backup service started successfully")
    
    def stop(self):
        """Stop the backup service gracefully."""
        if not self.is_running:
            logger.warning("Backup service is not running")
            return
        
        logger.info("Stopping backup service...")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Stop scheduler thread
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        # Stop orchestrator
        self.orchestrator.stop()
        
        logger.info("Backup service stopped")
    
    def create_manual_backup(self, backup_type: str = "full", 
                           upload_to_storage: bool = True) -> Dict:
        """
        Create a manual backup.
        
        Args:
            backup_type: Type of backup ("full" or "incremental")
            upload_to_storage: Whether to upload to storage backends
            
        Returns:
            Dict with backup operation results
        """
        try:
            logger.info(f"Starting manual {backup_type} backup...")
            
            self.service_stats["total_operations"] += 1
            
            if backup_type == "full":
                result = self.orchestrator.create_full_backup(upload_to_storage)
                if result.get("success", False):
                    self.service_stats["last_full_backup"] = result.get("completed")
            elif backup_type == "incremental":
                result = self.orchestrator.create_incremental_backup(upload_to_storage)
                if result.get("success", False):
                    self.service_stats["last_incremental_backup"] = result.get("completed")
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")
            
            if result.get("success", False):
                self.service_stats["successful_operations"] += 1
                logger.info(f"Manual {backup_type} backup completed successfully")
            else:
                self.service_stats["failed_operations"] += 1
                logger.error(f"Manual {backup_type} backup failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Manual backup failed: {e}")
            self.service_stats["failed_operations"] += 1
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_recovery(self, recovery_type: str = "full", **kwargs) -> Dict:
        """
        Perform recovery operation.
        
        Args:
            recovery_type: Type of recovery ("database", "files", or "full")
            **kwargs: Additional recovery parameters
            
        Returns:
            Dict with recovery operation results
        """
        try:
            logger.info(f"Starting {recovery_type} recovery...")
            
            if recovery_type == "database":
                result = self.recovery_manager.restore_database(**kwargs)
            elif recovery_type == "files":
                result = self.recovery_manager.restore_files(**kwargs)
            elif recovery_type == "full":
                result = self.recovery_manager.perform_full_system_recovery(**kwargs)
            else:
                raise ValueError(f"Unknown recovery type: {recovery_type}")
            
            if result.get("success", False):
                logger.info(f"{recovery_type} recovery completed successfully")
            else:
                logger.error(f"{recovery_type} recovery failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Recovery operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def cleanup_backups(self) -> Dict:
        """
        Perform backup cleanup operation.
        
        Returns:
            Dict with cleanup results
        """
        try:
            logger.info("Starting backup cleanup...")
            
            self.service_stats["total_operations"] += 1
            
            result = self.orchestrator.cleanup_expired_backups()
            
            if result.get("success", False):
                self.service_stats["successful_operations"] += 1
                self.service_stats["last_cleanup"] = result.get("completed")
                logger.info("Backup cleanup completed successfully")
            else:
                self.service_stats["failed_operations"] += 1
                logger.error("Backup cleanup failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            self.service_stats["failed_operations"] += 1
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_service_status(self) -> Dict:
        """
        Get comprehensive backup service status.
        
        Returns:
            Dict with complete service status
        """
        try:
            status = {
                "service": {
                    "running": self.is_running,
                    "started": self.service_stats.get("started"),
                    "uptime_seconds": None,
                    "statistics": self.service_stats.copy()
                },
                "backup_system": self.orchestrator.get_backup_status(),
                "available_backups": self.recovery_manager.list_available_backups(),
                "configuration": {
                    "scheduling_enabled": self.config.get("scheduling", {}).get("enabled", False),
                    "realtime_monitoring": self.config.get("files", {}).get("enable_realtime", False),
                    "compression_enabled": self.config.get("compression", {}).get("enabled", False),
                    "encryption_enabled": self.config.get("encryption", {}).get("enabled", False),
                    "storage_backends": len(self.config.get("storage_backends", []))
                }
            }
            
            # Calculate uptime
            if self.service_stats.get("started"):
                started_time = datetime.fromisoformat(self.service_stats["started"])
                uptime = datetime.utcnow() - started_time
                status["service"]["uptime_seconds"] = int(uptime.total_seconds())
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {"error": str(e)}
    
    def test_backup_system(self) -> Dict:
        """
        Test backup and recovery system functionality.
        
        Returns:
            Dict with test results
        """
        try:
            logger.info("Starting backup system test...")
            
            test_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "backup_test": None,
                "recovery_test": None,
                "storage_test": None,
                "overall_success": False
            }
            
            # Test backup creation
            logger.info("Testing backup creation...")
            backup_test = self.create_manual_backup("incremental", upload_to_storage=False)
            test_result["backup_test"] = {
                "success": backup_test.get("success", False),
                "operation_id": backup_test.get("operation_id"),
                "error": backup_test.get("error")
            }
            
            # Test recovery procedures
            logger.info("Testing recovery procedures...")
            recovery_test = self.recovery_manager.test_recovery_procedures()
            test_result["recovery_test"] = recovery_test
            
            # Test storage backends
            logger.info("Testing storage backends...")
            storage_test_results = []
            for backend in self.orchestrator.storage_backends:
                try:
                    backend_info = backend.get_backend_info()
                    storage_test_results.append({
                        "backend_type": backend_info.get("backend_type"),
                        "accessible": backend_info.get("accessible", False),
                        "error": backend_info.get("error")
                    })
                except Exception as e:
                    storage_test_results.append({
                        "backend_type": "unknown",
                        "accessible": False,
                        "error": str(e)
                    })
            
            test_result["storage_test"] = storage_test_results
            
            # Overall success
            test_result["overall_success"] = all([
                test_result["backup_test"].get("success", False),
                test_result["recovery_test"].get("success", False),
                all(st.get("accessible", False) for st in storage_test_results)
            ])
            
            logger.info(f"Backup system test completed: {'SUCCESS' if test_result['overall_success'] else 'FAILED'}")
            return test_result
            
        except Exception as e:
            logger.error(f"Backup system test failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_success": False
            }
    
    def _setup_scheduling(self):
        """Setup backup scheduling based on configuration."""
        scheduling_config = self.config.get("scheduling", {})
        
        if not scheduling_config.get("enabled", True):
            logger.info("Backup scheduling disabled")
            return
        
        # Schedule full backups
        full_backup_cron = scheduling_config.get("full_backup_cron", "0 2 * * *")
        schedule.every().day.at("02:00").do(self._scheduled_full_backup)
        
        # Schedule incremental backups
        incremental_backup_cron = scheduling_config.get("incremental_backup_cron", "*/15 * * * *")
        schedule.every(15).minutes.do(self._scheduled_incremental_backup)
        
        # Schedule cleanup
        cleanup_cron = scheduling_config.get("cleanup_cron", "0 3 * * 0")
        schedule.every().sunday.at("03:00").do(self._scheduled_cleanup)
        
        logger.info("Backup scheduling configured")
    
    def _run_scheduler(self):
        """Run the backup scheduler in a separate thread."""
        logger.info("Backup scheduler thread started")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
        
        logger.info("Backup scheduler thread stopped")
    
    def _scheduled_full_backup(self):
        """Perform scheduled full backup."""
        logger.info("Executing scheduled full backup...")
        result = self.create_manual_backup("full", upload_to_storage=True)
        
        if result.get("success", False):
            logger.info("Scheduled full backup completed successfully")
        else:
            logger.error(f"Scheduled full backup failed: {result.get('error')}")
    
    def _scheduled_incremental_backup(self):
        """Perform scheduled incremental backup."""
        logger.debug("Executing scheduled incremental backup...")
        result = self.create_manual_backup("incremental", upload_to_storage=True)
        
        if result.get("success", False):
            logger.debug("Scheduled incremental backup completed successfully")
        else:
            logger.warning(f"Scheduled incremental backup failed: {result.get('error')}")
    
    def _scheduled_cleanup(self):
        """Perform scheduled backup cleanup."""
        logger.info("Executing scheduled backup cleanup...")
        result = self.cleanup_backups()
        
        if result.get("success", False):
            logger.info("Scheduled backup cleanup completed successfully")
        else:
            logger.error(f"Scheduled backup cleanup failed: {result.get('error')}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        # Removed sys.exit(0) to prevent FastAPI server crashes
        # Let the main process handle the shutdown gracefully


# Global backup service instance
_backup_service: Optional[BackupService] = None


def get_backup_service(config: Optional[Dict] = None) -> BackupService:
    """
    Get or create the global backup service instance.
    
    Args:
        config: Optional backup configuration
        
    Returns:
        BackupService instance
    """
    global _backup_service
    
    if _backup_service is None:
        _backup_service = BackupService(config)
    
    return _backup_service


def start_backup_service(config: Optional[Dict] = None):
    """
    Start the backup service.
    
    Args:
        config: Optional backup configuration
    """
    service = get_backup_service(config)
    service.start()


def stop_backup_service():
    """Stop the backup service."""
    global _backup_service
    
    if _backup_service:
        _backup_service.stop()


if __name__ == "__main__":
    # Command line interface for backup service
    import argparse
    
    parser = argparse.ArgumentParser(description="Whisper Transcriber Backup Service")
    parser.add_argument("--action", choices=["start", "backup", "restore", "test", "status"], 
                       default="start", help="Action to perform")
    parser.add_argument("--backup-type", choices=["full", "incremental"], 
                       default="full", help="Type of backup to create")
    parser.add_argument("--recovery-type", choices=["database", "files", "full"], 
                       default="full", help="Type of recovery to perform")
    parser.add_argument("--config", help="Path to custom configuration file")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        if args.action == "start":
            # Start backup service and keep running
            start_backup_service()
            logger.info("Backup service is running. Press Ctrl+C to stop.")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down...")
                stop_backup_service()
        
        elif args.action == "backup":
            # Create manual backup
            service = get_backup_service()
            result = service.create_manual_backup(args.backup_type)
            print(f"Backup result: {result}")
        
        elif args.action == "restore":
            # Perform recovery
            service = get_backup_service()
            result = service.create_recovery(args.recovery_type)
            print(f"Recovery result: {result}")
        
        elif args.action == "test":
            # Test backup system
            service = get_backup_service()
            result = service.test_backup_system()
            print(f"Test result: {result}")
        
        elif args.action == "status":
            # Get service status
            service = get_backup_service()
            status = service.get_service_status()
            print(f"Service status: {status}")
    
    except Exception as e:
        logger.error(f"Backup service error: {e}")
        sys.exit(1)
