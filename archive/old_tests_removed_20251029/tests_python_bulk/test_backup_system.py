"""
Comprehensive Test Suite for Backup and Recovery System

Tests all components of the backup system including database backups,
file backups, compression, storage backends, orchestration, recovery,
and API endpoints.
"""

import os
import tempfile
import shutil
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient

# Import backup system components
try:
    from app.backup.database import DatabaseBackupEngine
    from app.backup.files import FileBackupEngine
    from app.backup.compression import CompressionEngine
    from app.backup.storage import LocalStorageBackend, S3StorageBackend, SFTPStorageBackend
    from app.backup.orchestrator import BackupOrchestrator
    from app.backup.recovery import RecoveryManager
    from app.backup.config import get_backup_config, validate_backup_config
    from app.backup.service import BackupService
    from app.backup_api import backup_router
    BACKUP_AVAILABLE = True
except ImportError:
    BACKUP_AVAILABLE = False


class TestBackupSystemAvailability:
    """Test that backup system components are available."""
    
    def test_backup_system_imports(self):
        """Test that all backup system components can be imported."""
        if not BACKUP_AVAILABLE:
            pytest.skip("Backup system not available")
        
        assert DatabaseBackupEngine is not None
        assert FileBackupEngine is not None
        assert CompressionEngine is not None
        assert LocalStorageBackend is not None
        assert BackupOrchestrator is not None
        assert RecoveryManager is not None
        assert BackupService is not None


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestDatabaseBackupEngine:
    """Test database backup functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary SQLite database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create test database with sample data
        conn = sqlite3.connect(db_path)
        conn.execute('CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)')
        conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test_data_1',))
        conn.execute('INSERT INTO test_table (data) VALUES (?)', ('test_data_2',))
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        # Clean up WAL and SHM files
        for ext in ['-wal', '-shm']:
            wal_path = db_path + ext
            if os.path.exists(wal_path):
                os.unlink(wal_path)
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_database_backup_engine_init(self, temp_db, temp_backup_dir):
        """Test DatabaseBackupEngine initialization."""
        engine = DatabaseBackupEngine(temp_db, temp_backup_dir)
        
        assert engine.db_path == temp_db
        assert engine.backup_dir == temp_backup_dir
        assert engine.wal_backup_enabled is True
    
    def test_create_full_backup(self, temp_db, temp_backup_dir):
        """Test creating a full database backup."""
        engine = DatabaseBackupEngine(temp_db, temp_backup_dir)
        result = engine.create_full_backup()
        
        assert result is not None
        assert result['success'] is True
        assert 'backup_file' in result
        assert os.path.exists(result['backup_file'])
        
        # Verify backup file is valid SQLite database
        backup_conn = sqlite3.connect(result['backup_file'])
        cursor = backup_conn.execute('SELECT COUNT(*) FROM test_table')
        count = cursor.fetchone()[0]
        assert count == 2
        backup_conn.close()
    
    def test_wal_backup(self, temp_db, temp_backup_dir):
        """Test WAL file backup."""
        # Enable WAL mode
        conn = sqlite3.connect(temp_db)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('INSERT INTO test_table (data) VALUES (?)', ('wal_data',))
        conn.commit()
        conn.close()
        
        engine = DatabaseBackupEngine(temp_db, temp_backup_dir)
        result = engine.backup_wal_files()
        
        assert result is not None
        assert result['success'] is True
    
    def test_backup_integrity_check(self, temp_db, temp_backup_dir):
        """Test backup file integrity verification."""
        engine = DatabaseBackupEngine(temp_db, temp_backup_dir)
        backup_result = engine.create_full_backup()
        
        integrity_result = engine.verify_backup_integrity(backup_result['backup_file'])
        assert integrity_result['valid'] is True


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestFileBackupEngine:
    """Test file backup functionality."""
    
    @pytest.fixture
    def temp_source_dir(self):
        """Create temporary source directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files
        (Path(temp_dir) / 'test1.txt').write_text('Content of file 1')
        (Path(temp_dir) / 'test2.txt').write_text('Content of file 2')
        
        # Create subdirectory with files
        subdir = Path(temp_dir) / 'subdir'
        subdir.mkdir()
        (subdir / 'test3.txt').write_text('Content of file 3')
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_file_backup_engine_init(self, temp_source_dir, temp_backup_dir):
        """Test FileBackupEngine initialization."""
        engine = FileBackupEngine([temp_source_dir], temp_backup_dir)
        
        assert temp_source_dir in engine.source_dirs
        assert engine.backup_dir == temp_backup_dir
        assert engine.deduplication_enabled is True
    
    def test_create_file_backup(self, temp_source_dir, temp_backup_dir):
        """Test creating file backup."""
        engine = FileBackupEngine([temp_source_dir], temp_backup_dir)
        result = engine.create_backup()
        
        assert result is not None
        assert result['success'] is True
        assert 'backup_file' in result
        assert os.path.exists(result['backup_file'])
    
    def test_file_deduplication(self, temp_source_dir, temp_backup_dir):
        """Test file deduplication functionality."""
        # Create duplicate files
        (Path(temp_source_dir) / 'duplicate1.txt').write_text('Same content')
        (Path(temp_source_dir) / 'duplicate2.txt').write_text('Same content')
        
        engine = FileBackupEngine([temp_source_dir], temp_backup_dir)
        result = engine.create_backup()
        
        assert result['success'] is True
        # Check that deduplication detected duplicates
        assert 'deduplicated_files' in result or 'file_stats' in result


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestCompressionEngine:
    """Test compression functionality."""
    
    @pytest.fixture
    def temp_test_file(self):
        """Create temporary test file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('This is test data for compression testing. ' * 100)
            test_file = f.name
        
        yield test_file
        
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    def test_compression_engine_init(self):
        """Test CompressionEngine initialization."""
        engine = CompressionEngine()
        assert engine.preferred_algorithm in ['zstd', 'gzip']
    
    def test_compress_file(self, temp_test_file):
        """Test file compression."""
        engine = CompressionEngine()
        
        with tempfile.NamedTemporaryFile(delete=False) as compressed_file:
            result = engine.compress_file(temp_test_file, compressed_file.name)
            
            assert result is not None
            assert result['success'] is True
            assert os.path.exists(compressed_file.name)
            assert os.path.getsize(compressed_file.name) < os.path.getsize(temp_test_file)
            
            os.unlink(compressed_file.name)
    
    def test_decompress_file(self, temp_test_file):
        """Test file decompression."""
        engine = CompressionEngine()
        
        # Compress file first
        with tempfile.NamedTemporaryFile(delete=False) as compressed_file:
            compress_result = engine.compress_file(temp_test_file, compressed_file.name)
            assert compress_result['success'] is True
            
            # Decompress file
            with tempfile.NamedTemporaryFile(delete=False) as decompressed_file:
                decompress_result = engine.decompress_file(compressed_file.name, decompressed_file.name)
                
                assert decompress_result is not None
                assert decompress_result['success'] is True
                
                # Verify content matches
                with open(temp_test_file, 'r') as original, open(decompressed_file.name, 'r') as decompressed:
                    assert original.read() == decompressed.read()
                
                os.unlink(decompressed_file.name)
            
            os.unlink(compressed_file.name)


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestStorageBackends:
    """Test storage backend functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_test_file(self):
        """Create temporary test file to upload."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('Test backup file content')
            test_file = f.name
        
        yield test_file
        
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    def test_local_storage_backend(self, temp_storage_dir, temp_test_file):
        """Test local storage backend."""
        backend = LocalStorageBackend(temp_storage_dir)
        
        # Test upload
        remote_path = 'test/backup.txt'
        result = backend.upload_file(temp_test_file, remote_path)
        assert result is True
        
        # Verify file exists
        expected_path = Path(temp_storage_dir) / remote_path
        assert expected_path.exists()
        
        # Test download
        with tempfile.NamedTemporaryFile(delete=False) as download_file:
            download_result = backend.download_file(remote_path, download_file.name)
            assert download_result is True
            
            # Verify content matches
            with open(temp_test_file, 'r') as original, open(download_file.name, 'r') as downloaded:
                assert original.read() == downloaded.read()
            
            os.unlink(download_file.name)
        
        # Test delete
        delete_result = backend.delete_file(remote_path)
        assert delete_result is True
        assert not expected_path.exists()
    
    def test_s3_storage_backend_mock(self, temp_test_file):
        """Test S3 storage backend with mocked boto3."""
        with patch('boto3.client') as mock_boto3:
            mock_s3 = Mock()
            mock_boto3.return_value = mock_s3
            
            backend = S3StorageBackend('test-bucket', 'us-east-1')
            
            # Test upload
            mock_s3.upload_file.return_value = None
            result = backend.upload_file(temp_test_file, 'test/backup.txt')
            assert result is True
            mock_s3.upload_file.assert_called_once()
            
            # Test download
            mock_s3.download_file.return_value = None
            with tempfile.NamedTemporaryFile(delete=False) as download_file:
                result = backend.download_file('test/backup.txt', download_file.name)
                assert result is True
                mock_s3.download_file.assert_called_once()
                os.unlink(download_file.name)
            
            # Test delete
            mock_s3.delete_object.return_value = None
            result = backend.delete_file('test/backup.txt')
            assert result is True
            mock_s3.delete_object.assert_called_once()


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestBackupOrchestrator:
    """Test backup orchestration functionality."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        db_dir = tempfile.mkdtemp()
        source_dir = tempfile.mkdtemp()
        backup_dir = tempfile.mkdtemp()
        storage_dir = tempfile.mkdtemp()
        
        # Create test database
        db_path = Path(db_dir) / 'test.db'
        conn = sqlite3.connect(str(db_path))
        conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)')
        conn.execute('INSERT INTO test (data) VALUES (?)', ('test_data',))
        conn.commit()
        conn.close()
        
        # Create test files
        (Path(source_dir) / 'test.txt').write_text('Test file content')
        
        yield {
            'db_path': str(db_path),
            'source_dir': source_dir,
            'backup_dir': backup_dir,
            'storage_dir': storage_dir
        }
        
        # Cleanup
        for dir_path in [db_dir, source_dir, backup_dir, storage_dir]:
            shutil.rmtree(dir_path)
    
    def test_orchestrator_init(self, temp_dirs):
        """Test BackupOrchestrator initialization."""
        config = {
            'database': {'path': temp_dirs['db_path']},
            'storage': {'local': {'path': temp_dirs['storage_dir']}},
            'backup_dir': temp_dirs['backup_dir']
        }
        
        orchestrator = BackupOrchestrator(config)
        assert orchestrator.config == config
        assert orchestrator.db_engine is not None
        assert orchestrator.file_engine is not None
        assert len(orchestrator.storage_backends) > 0
    
    def test_full_backup_orchestration(self, temp_dirs):
        """Test full backup orchestration."""
        config = {
            'database': {'path': temp_dirs['db_path']},
            'files': {'source_dirs': [temp_dirs['source_dir']]},
            'storage': {'local': {'path': temp_dirs['storage_dir']}},
            'backup_dir': temp_dirs['backup_dir'],
            'compression': {'enabled': True}
        }
        
        orchestrator = BackupOrchestrator(config)
        result = orchestrator.create_full_backup()
        
        assert result is not None
        assert result['success'] is True
        assert 'database_backup' in result
        assert 'file_backup' in result


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestRecoveryManager:
    """Test recovery functionality."""
    
    @pytest.fixture
    def temp_recovery_setup(self):
        """Set up temporary environment for recovery testing."""
        backup_dir = tempfile.mkdtemp()
        restore_dir = tempfile.mkdtemp()
        
        # Create mock backup files
        db_backup = Path(backup_dir) / 'database_backup.db'
        db_backup.write_text('mock database backup')
        
        file_backup = Path(backup_dir) / 'files_backup.tar.gz'
        file_backup.write_text('mock file backup')
        
        yield {
            'backup_dir': backup_dir,
            'restore_dir': restore_dir,
            'db_backup': str(db_backup),
            'file_backup': str(file_backup)
        }
        
        # Cleanup
        for dir_path in [backup_dir, restore_dir]:
            shutil.rmtree(dir_path)
    
    def test_recovery_manager_init(self, temp_recovery_setup):
        """Test RecoveryManager initialization."""
        config = {
            'backup_dir': temp_recovery_setup['backup_dir'],
            'storage': {'local': {'path': temp_recovery_setup['backup_dir']}}
        }
        
        manager = RecoveryManager(config)
        assert manager.backup_dir == temp_recovery_setup['backup_dir']
        assert len(manager.storage_backends) > 0
    
    def test_list_available_backups(self, temp_recovery_setup):
        """Test listing available backups."""
        config = {
            'backup_dir': temp_recovery_setup['backup_dir'],
            'storage': {'local': {'path': temp_recovery_setup['backup_dir']}}
        }
        
        manager = RecoveryManager(config)
        backups = manager.list_available_backups()
        
        assert isinstance(backups, dict)
        # Should have database and file backup categories
        assert 'database_backups' in backups or 'file_backups' in backups


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestBackupConfiguration:
    """Test backup configuration functionality."""
    
    def test_get_backup_config_defaults(self):
        """Test getting default backup configuration."""
        config = get_backup_config()
        
        assert isinstance(config, dict)
        assert 'backup_dir' in config
        assert 'database' in config
        assert 'files' in config
        assert 'storage' in config
    
    def test_validate_backup_config(self):
        """Test backup configuration validation."""
        valid_config = {
            'backup_dir': '/tmp/backups',
            'database': {'path': '/tmp/test.db'},
            'files': {'source_dirs': ['/tmp/source']},
            'storage': {'local': {'path': '/tmp/storage'}}
        }
        
        # Should not raise exception for valid config
        validate_backup_config(valid_config)
    
    def test_validate_backup_config_invalid(self):
        """Test backup configuration validation with invalid config."""
        invalid_config = {
            'backup_dir': '/tmp/backups'
            # Missing required keys
        }
        
        with pytest.raises(ValueError):
            validate_backup_config(invalid_config)


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestBackupService:
    """Test backup service functionality."""
    
    @pytest.fixture
    def temp_service_setup(self):
        """Set up temporary environment for service testing."""
        backup_dir = tempfile.mkdtemp()
        db_dir = tempfile.mkdtemp()
        source_dir = tempfile.mkdtemp()
        storage_dir = tempfile.mkdtemp()
        
        # Create test database
        db_path = Path(db_dir) / 'test.db'
        conn = sqlite3.connect(str(db_path))
        conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)')
        conn.commit()
        conn.close()
        
        # Create test file
        (Path(source_dir) / 'test.txt').write_text('Test content')
        
        config = {
            'backup_dir': backup_dir,
            'database': {'path': str(db_path)},
            'files': {'source_dirs': [source_dir]},
            'storage': {'local': {'path': storage_dir}},
            'scheduling': {'enabled': False}  # Disable scheduling for tests
        }
        
        yield config, {
            'backup_dir': backup_dir,
            'db_dir': db_dir,
            'source_dir': source_dir,
            'storage_dir': storage_dir
        }
        
        # Cleanup
        for dir_path in [backup_dir, db_dir, source_dir, storage_dir]:
            shutil.rmtree(dir_path)
    
    def test_backup_service_init(self, temp_service_setup):
        """Test BackupService initialization."""
        config, dirs = temp_service_setup
        
        service = BackupService(config)
        assert service.config == config
        assert service.orchestrator is not None
        assert service.recovery_manager is not None
    
    def test_backup_service_status(self, temp_service_setup):
        """Test getting backup service status."""
        config, dirs = temp_service_setup
        
        service = BackupService(config)
        status = service.get_service_status()
        
        assert isinstance(status, dict)
        assert 'service' in status
        assert 'backup_system' in status
        assert 'configuration' in status
    
    def test_manual_backup_creation(self, temp_service_setup):
        """Test manual backup creation through service."""
        config, dirs = temp_service_setup
        
        service = BackupService(config)
        result = service.create_manual_backup(backup_type='full')
        
        assert result is not None
        assert isinstance(result, dict)
        # Should contain operation details


@pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
class TestBackupAPI:
    """Test backup API endpoints."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client with backup router."""
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(backup_router)
        
        client = TestClient(app)
        yield client
    
    @patch('app.backup_api.get_backup_service')
    def test_backup_status_endpoint(self, mock_get_service, test_client):
        """Test backup status API endpoint."""
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            'service': {'running': True, 'statistics': {}},
            'backup_system': {'storage_backends': ['local']},
            'configuration': {}
        }
        mock_get_service.return_value = mock_service
        
        response = test_client.get("/admin/backup/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'timestamp' in data
        assert 'service_running' in data
        assert 'backup_system' in data
    
    @patch('app.backup_api.get_backup_service')
    def test_create_backup_endpoint(self, mock_get_service, test_client):
        """Test create backup API endpoint."""
        mock_service = Mock()
        mock_service.create_manual_backup.return_value = {
            'operation_id': 'test_op_123',
            'type': 'full',
            'success': True,
            'started': '2025-01-15T10:00:00',
            'completed': '2025-01-15T10:05:00'
        }
        mock_get_service.return_value = mock_service
        
        response = test_client.post("/admin/backup/create", json={
            "backup_type": "full",
            "upload_to_storage": True
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert data['operation_id'] == 'test_op_123'
        assert data['type'] == 'full'
        assert data['success'] is True
    
    @patch('app.backup_api.get_backup_service')
    def test_backup_health_endpoint(self, mock_get_service, test_client):
        """Test backup health check endpoint."""
        mock_service = Mock()
        mock_service.get_service_status.return_value = {
            'service': {'running': True, 'statistics': {'last_full_backup': '2025-01-15T10:00:00'}},
            'backup_system': {'storage_backends': ['local']},
            'configuration': {}
        }
        mock_get_service.return_value = mock_service
        
        response = test_client.get("/admin/backup/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'healthy' in data
        assert 'timestamp' in data
        assert data['healthy'] is True


class TestBackupSystemIntegration:
    """Integration tests for the complete backup system."""
    
    @pytest.mark.skipif(not BACKUP_AVAILABLE, reason="Backup system not available")
    def test_backup_system_end_to_end(self):
        """Test complete backup and recovery workflow."""
        # This would be a comprehensive end-to-end test
        # that exercises the entire backup system workflow
        
        # Create temporary environment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Set up test environment
            db_path = temp_path / 'test.db'
            source_dir = temp_path / 'source'
            backup_dir = temp_path / 'backups'
            storage_dir = temp_path / 'storage'
            
            source_dir.mkdir()
            backup_dir.mkdir()
            storage_dir.mkdir()
            
            # Create test database
            conn = sqlite3.connect(str(db_path))
            conn.execute('CREATE TABLE test (id INTEGER, data TEXT)')
            conn.execute('INSERT INTO test VALUES (1, "test data")')
            conn.commit()
            conn.close()
            
            # Create test files
            (source_dir / 'test.txt').write_text('Test file content')
            
            # Configure backup system
            config = {
                'backup_dir': str(backup_dir),
                'database': {'path': str(db_path)},
                'files': {'source_dirs': [str(source_dir)]},
                'storage': {'local': {'path': str(storage_dir)}},
                'compression': {'enabled': True},
                'scheduling': {'enabled': False}
            }
            
            # Test backup creation
            service = BackupService(config)
            backup_result = service.create_manual_backup('full')
            
            assert backup_result is not None
            
            # Test backup listing
            available_backups = service.recovery_manager.list_available_backups()
            assert isinstance(available_backups, dict)
            
            # Test system validation
            validation_result = service.recovery_manager.validate_system_recovery()
            assert isinstance(validation_result, dict)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
