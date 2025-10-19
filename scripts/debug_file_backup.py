#!/usr/bin/env python3
"""Debug file backup issue"""

import tempfile
from pathlib import Path

def debug_file_backup():
    print("=== Debugging File Backup Issue ===")
    
    from app.backup.files import FileBackupEngine
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        backup_dir = Path(tmpdir) / "backups"
        source_dir.mkdir()
        
        # Create test files
        test_file1 = source_dir / "test1.txt"
        test_file1.write_text("content 1")
        print(f"Created test file: {test_file1}")
        
        # Test file backup engine
        engine = FileBackupEngine([str(source_dir)], str(backup_dir), enable_realtime=False)
        print("File backup engine initialized")
        
        # Test single file backup
        print(f"\nTesting single file backup for: {test_file1}")
        result = engine.backup_file(test_file1)
        print(f"Single file backup result: {result}")
        
        # Test backup directory
        print(f"\nTesting directory backup for: {source_dir}")
        try:
            for root, dirs, files in os.walk(source_dir):
                print(f"Walking: root={root}, dirs={dirs}, files={files}")
                for file in files:
                    file_path = Path(root) / file
                    print(f"Processing file: {file_path} (type: {type(file_path)})")
                    backup_result = engine.backup_file(file_path)
                    print(f"Backup result: {backup_result}")
        except Exception as e:
            print(f"Error in directory backup: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import os
    debug_file_backup()
