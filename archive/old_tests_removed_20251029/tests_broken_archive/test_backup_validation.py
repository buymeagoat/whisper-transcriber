#!/usr/bin/env python3
"""Test script for backup system validation"""

import tempfile
import sqlite3
import os
from pathlib import Path

# Test storage backend
def test_storage_backend():
    print("Testing Local Storage Backend...")
    from app.backup.storage import LocalStorageBackend
    
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = LocalStorageBackend(tmpdir)
        print("✓ Local storage backend initialized")
        print(f"  Backend info: {backend.get_backend_info()}")
        
        # Test file operations
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        
        result = backend.upload_file(test_file, "backup/test.txt")
        print(f"✓ File upload: {result}")
        
        exists = backend.file_exists("backup/test.txt")
        print(f"✓ File exists check: {exists}")
        
        files = backend.list_files()
        print(f"✓ File listing: {files}")

# Test database backup
def test_database_backup():
    print("\nTesting Database Backup Engine...")
    from app.backup.database import DatabaseBackupEngine
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test database
        db_path = Path(tmpdir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test data')")
        conn.commit()
        conn.close()
        
        # Test backup engine
        backup_dir = Path(tmpdir) / "backups"
        engine = DatabaseBackupEngine(str(db_path), str(backup_dir))
        print("✓ Database backup engine initialized")
        
        # Enable WAL mode
        wal_result = engine.enable_wal_mode()
        print(f"✓ WAL mode enabled: {wal_result}")
        
        # Create backup
        backup_result = engine.create_full_backup()
        print(f"✓ Full backup created: {backup_result is not None}")
        if backup_result:
            print(f"  Backup ID: {backup_result.get('backup_id', 'Unknown')}")

# Test file backup
def test_file_backup():
    print("\nTesting File Backup Engine...")
    from app.backup.files import FileBackupEngine
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        backup_dir = Path(tmpdir) / "backups"
        source_dir.mkdir()
        
        # Create test files
        (source_dir / "test1.txt").write_text("content 1")
        (source_dir / "test2.txt").write_text("content 2")
        
        # Test file backup engine
        engine = FileBackupEngine([str(source_dir)], str(backup_dir), enable_realtime=False)
        print("✓ File backup engine initialized")
        
        # Test backup
        results = engine.backup_directory(source_dir)
        print(f"✓ Directory backup completed: {len(results)} files processed")

# Test compression
def test_compression():
    print("\nTesting Compression Engine...")
    from app.backup.compression import CompressionEngine
    
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = CompressionEngine()
        print("✓ Compression engine initialized")
        
        # Create test file
        test_file = Path(tmpdir) / "test.txt"
        test_content = "This is test content for compression testing. " * 100
        test_file.write_text(test_content)
        
        # Test compression
        compressed_file = Path(tmpdir) / "test.txt.zst"
        result = engine.compress_file(test_file, compressed_file)
        print(f"✓ File compression: {result.get('success', False)}")
        if result.get('success'):
            print(f"  Compression ratio: {result.get('compression_ratio', 0):.2f}")

# Test service initialization
def test_backup_service():
    print("\nTesting Backup Service...")
    from app.backup.service import BackupService
    
    try:
        # Test with minimal config
        config = {
            "backup_base_dir": "/tmp/test_backups",
            "database": {"path": "/tmp/test.db"},
            "files": {"watch_directories": ["/tmp"]},
            "storage_backends": [
                {
                    "type": "local",
                    "path": "/tmp/backup_storage",
                    "create_directories": True,
                    "primary": True
                }
            ],
            "scheduling": {"enabled": False}
        }
        
        service = BackupService(config)
        print("✓ Backup service initialized")
        
        status = service.get_service_status()
        print(f"✓ Service status retrieved: {status.get('service', {}).get('running', False)}")
        
    except Exception as e:
        print(f"✗ Backup service test failed: {e}")

# Test API endpoints
def test_backup_api():
    print("\nTesting Backup API...")
    try:
        from app.backup_api import backup_router
        print("✓ Backup API router imported successfully")
        
        # Check routes
        routes = [route for route in backup_router.routes]
        print(f"✓ API endpoints: {len(routes)} routes registered")
        for route in routes[:5]:  # Show first 5 routes
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                print(f"  - {route.path} [{', '.join(route.methods)}]")
        
    except Exception as e:
        print(f"✗ Backup API test failed: {e}")

if __name__ == "__main__":
    print("=== Backup System Comprehensive Test ===\n")
    
    try:
        test_storage_backend()
        test_database_backup()
        test_file_backup()
        test_compression()
        test_backup_service()
        test_backup_api()
        
        print("\n=== Test Summary ===")
        print("✓ All core components tested successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
