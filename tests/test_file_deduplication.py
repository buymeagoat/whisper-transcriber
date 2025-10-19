#!/usr/bin/env python3

import tempfile
import shutil
from pathlib import Path
from app.backup.files import FileBackupEngine

def test_file_deduplication():
    """Test file backup deduplication functionality."""
    print("=== Testing File Backup Deduplication ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        backup_dir = temp_path / "backups"
        
        # Create test directories
        source_dir.mkdir()
        backup_dir.mkdir()
        
        # Create test file
        test_file = source_dir / "test.txt"
        test_file.write_text("Hello, backup world!")
        
        print(f"Created test file: {test_file}")
        
        # Initialize backup engine
        engine = FileBackupEngine(
            watch_directories=[str(source_dir)],
            backup_base_dir=str(backup_dir),
            enable_realtime=False
        )
        
        print("File backup engine initialized")
        
        # First backup - should succeed
        print(f"\nFirst backup attempt:")
        result1 = engine.backup_file(test_file)
        print(f"Result: {'SUCCESS' if result1 else 'SKIPPED'}")
        if result1:
            print(f"  Backup ID: {result1['backup_id']}")
            print(f"  Type: {result1['type']}")
            print(f"  Path: {result1['backup_path']}")
        
        # Second backup of same file - should be skipped (deduplication)
        print(f"\nSecond backup attempt (same file, unchanged):")
        result2 = engine.backup_file(test_file)
        print(f"Result: {'SUCCESS' if result2 else 'SKIPPED (deduplication working)'}")
        
        # Modify file and backup again - should succeed
        print(f"\nModifying file and backing up again:")
        test_file.write_text("Hello, modified backup world!")
        result3 = engine.backup_file(test_file)
        print(f"Result: {'SUCCESS' if result3 else 'SKIPPED'}")
        if result3:
            print(f"  Backup ID: {result3['backup_id']}")
            print(f"  Type: {result3['type']}")
        
        # Create identical file in different location - should reference original
        print(f"\nCreating identical file in different location:")
        test_file2 = source_dir / "test_copy.txt"
        test_file2.write_text("Hello, backup world!")  # Same content as original
        result4 = engine.backup_file(test_file2)
        print(f"Result: {'SUCCESS' if result4 else 'SKIPPED'}")
        if result4:
            print(f"  Backup ID: {result4['backup_id']}")
            print(f"  Type: {result4['type']}")
            if result4['type'] == 'file_reference':
                print(f"  References: {result4['references_backup']}")
                print(f"  Deduplication saved: {result4['deduplication_saved']} bytes")

if __name__ == "__main__":
    test_file_deduplication()
