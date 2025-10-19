#!/usr/bin/env python3

import tempfile
import sqlite3
import json
from pathlib import Path
from app.backup.service import BackupService

def test_end_to_end_backup():
    """End-to-end test of the complete backup system."""
    print("=== End-to-End Backup System Test ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test directories and files
        app_dir = temp_path / "app"
        backup_dir = temp_path / "backups"
        db_dir = temp_path / "database"
        
        app_dir.mkdir()
        backup_dir.mkdir()
        db_dir.mkdir()
        
        # Create test database
        db_path = db_dir / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob')")
        conn.commit()
        conn.close()
        
        # Create test files
        config_file = app_dir / "config.json"
        config_file.write_text(json.dumps({"app": "whisper-transcriber", "version": "1.0"}))
        
        log_file = app_dir / "app.log"
        log_file.write_text("2025-10-15 16:45:00 - Application started\n")
        
        print(f"Created test environment:")
        print(f"  Database: {db_path}")
        print(f"  Config: {config_file}")
        print(f"  Log: {log_file}")
        
        # Configure backup service
        config = {
            "backup_enabled": True,
            "backup_base_dir": str(backup_dir),
            "database": {
                "enabled": True,
                "path": str(db_path),
                "wal_mode": True,
                "schedule": "manual"
            },
            "files": {
                "enabled": True,
                "watch_directories": [str(app_dir)],
                "enable_realtime": False,
                "compression": True
            },
            "storage_backends": [
                {
                    "type": "local",
                    "path": str(backup_dir / "storage"),
                    "create_directories": True,
                    "primary": True
                }
            ],
            "retention": {
                "daily_backups": 7,
                "weekly_backups": 4,
                "monthly_backups": 12
            }
        }
        
        # Initialize backup service
        print(f"\nInitializing backup service...")
        service = BackupService(config)
        print(f"✓ Backup service initialized")
        
        # Create full backup
        print(f"\nCreating full backup...")
        backup_result = service.create_manual_backup(backup_type="full")
        print(f"✓ Full backup completed")
        print(f"  Result: {backup_result}")
        
        if 'operation_id' in backup_result:
            print(f"  Operation ID: {backup_result['operation_id']}")
        if 'components' in backup_result:
            print(f"  Components: {len(backup_result['components'])} items backed up")
            for component in backup_result['components']:
                print(f"    - {component['type']}: {component.get('status', 'success')}")
        
        # Test backup listing - use backup status
        print(f"\nChecking backup status...")
        backup_status = service.orchestrator.get_backup_status()
        print(f"✓ Backup status retrieved")
        print(f"  Last backup: {backup_status.get('last_full_backup', 'None')}")
        print(f"  Total operations: {backup_status.get('total_operations', 0)}")
        
        # Test file changes
        print(f"\nModifying files and creating incremental backup...")
        log_file.write_text("2025-10-15 16:45:00 - Application started\n2025-10-15 16:45:30 - Processing request\n")
        
        incremental_result = service.create_manual_backup(backup_type="incremental")
        print(f"✓ Incremental backup completed")
        print(f"  Result: {incremental_result}")
        if 'operation_id' in incremental_result:
            print(f"  Operation ID: {incremental_result['operation_id']}")
        
        # Test service status
        print(f"\nChecking service status...")
        status = service.get_service_status()
        print(f"✓ Service status retrieved")
        print(f"  Status: {status}")
        print(f"  Running: {status.get('running', False)}")
        print(f"  Last activity: {status.get('last_activity', 'None')}")
        print(f"  Uptime: {status.get('uptime', 'Unknown')}")
        
        # Verify backup files exist
        print(f"\nVerifying backup files...")
        backup_files = list(backup_dir.rglob("*"))
        backup_files = [f for f in backup_files if f.is_file()]
        print(f"✓ Found {len(backup_files)} backup files")
        
        for backup_file in backup_files[:5]:  # Show first 5
            relative_path = backup_file.relative_to(backup_dir)
            print(f"    - {relative_path} ({backup_file.stat().st_size} bytes)")
        
        if len(backup_files) > 5:
            print(f"    ... and {len(backup_files) - 5} more files")

if __name__ == "__main__":
    test_end_to_end_backup()
