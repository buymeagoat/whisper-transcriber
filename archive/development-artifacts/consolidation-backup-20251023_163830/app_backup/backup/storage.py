"""
Storage Backend Infrastructure - Multi-Backend Backup Storage

Provides abstracted storage backends for backups including local storage,
S3-compatible cloud storage, and SFTP/SSH remote storage.
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List, Union
import shutil
import tempfile

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for backup storage backends.
    
    Provides a common interface for different storage systems
    including local storage, cloud storage, and remote storage.
    """
    
    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to the storage backend."""
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from the storage backend."""
        pass
    
    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from the storage backend."""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in the storage backend with optional prefix filter."""
        pass
    
    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in the storage backend."""
        pass
    
    @abstractmethod
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get file information (size, modified date, etc.)."""
        pass
    
    @abstractmethod
    def get_backend_info(self) -> Dict:
        """Get storage backend information and status."""
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend.
    
    Stores backups on the local filesystem with optional directory
    structure organization and permissions management.
    """
    
    def __init__(self, base_path: str, create_directories: bool = True):
        """
        Initialize local storage backend.
        
        Args:
            base_path: Base directory for backup storage
            create_directories: Automatically create directories as needed
        """
        self.base_path = Path(base_path).resolve()
        self.create_directories = create_directories
        
        if create_directories:
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        if not self.base_path.exists():
            raise ValueError(f"Storage directory does not exist: {self.base_path}")
        
        if not self.base_path.is_dir():
            raise ValueError(f"Storage path is not a directory: {self.base_path}")
        
        logger.info(f"Local storage backend initialized: {self.base_path}")
    
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload (copy) a file to local storage."""
        try:
            local_path = Path(local_path)
            target_path = self.base_path / remote_path
            
            if self.create_directories:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(local_path, target_path)
            logger.debug(f"Uploaded file to local storage: {local_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download (copy) a file from local storage."""
        try:
            source_path = self.base_path / remote_path
            local_path = Path(local_path)
            
            if not source_path.exists():
                logger.error(f"Source file not found: {source_path}")
                return False
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, local_path)
            logger.debug(f"Downloaded file from local storage: {source_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from local storage: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from local storage."""
        try:
            target_path = self.base_path / remote_path
            
            if target_path.exists():
                target_path.unlink()
                logger.debug(f"Deleted file from local storage: {target_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {target_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in local storage with optional prefix filter."""
        try:
            files = []
            search_path = self.base_path / prefix if prefix else self.base_path
            
            if search_path.is_file():
                return [str(search_path.relative_to(self.base_path))]
            elif search_path.is_dir():
                for file_path in search_path.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(self.base_path)
                        files.append(str(relative_path))
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to list files in local storage: {e}")
            return []
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in local storage."""
        target_path = self.base_path / remote_path
        return target_path.exists() and target_path.is_file()
    
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get file information from local storage."""
        try:
            target_path = self.base_path / remote_path
            
            if not target_path.exists():
                return None
            
            stat = target_path.stat()
            return {
                "path": remote_path,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "is_file": target_path.is_file(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from local storage: {e}")
            return None
    
    def get_backend_info(self) -> Dict:
        """Get local storage backend information."""
        try:
            # Get disk usage information
            usage = shutil.disk_usage(self.base_path)
            
            # Count files and calculate total size
            file_count = 0
            total_size = 0
            
            for file_path in self.base_path.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
            
            return {
                "backend_type": "local",
                "base_path": str(self.base_path),
                "accessible": self.base_path.exists(),
                "file_count": file_count,
                "total_size": total_size,
                "disk_total": usage.total,
                "disk_used": usage.used,
                "disk_free": usage.free,
                "disk_usage_percent": (usage.used / usage.total * 100) if usage.total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get local storage backend info: {e}")
            return {"backend_type": "local", "error": str(e)}


class S3StorageBackend(StorageBackend):
    """
    S3-compatible cloud storage backend.
    
    Supports AWS S3, MinIO, Backblaze B2, and other S3-compatible services.
    Requires boto3 library for S3 API access.
    """
    
    def __init__(self, bucket_name: str, access_key: str, secret_key: str,
                 endpoint_url: Optional[str] = None, region: str = "us-east-1"):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name
            access_key: S3 access key ID
            secret_key: S3 secret access key
            endpoint_url: Custom S3 endpoint (for MinIO, etc.)
            region: AWS region
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            self.ClientError = ClientError
        except ImportError:
            raise ImportError("boto3 library required for S3 storage backend")
        
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        self.s3_client = session.client(
            's3',
            endpoint_url=endpoint_url
        )
        
        # Test connection
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 storage backend initialized: bucket={bucket_name}")
        except Exception as e:
            logger.error(f"Failed to access S3 bucket {bucket_name}: {e}")
            raise
    
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to S3 storage."""
        try:
            local_path = Path(local_path)
            
            self.s3_client.upload_file(
                str(local_path),
                self.bucket_name,
                remote_path
            )
            
            logger.debug(f"Uploaded file to S3: {local_path} -> s3://{self.bucket_name}/{remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from S3 storage."""
        try:
            local_path = Path(local_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                remote_path,
                str(local_path)
            )
            
            logger.debug(f"Downloaded file from S3: s3://{self.bucket_name}/{remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from S3 storage."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            
            logger.debug(f"Deleted file from S3: s3://{self.bucket_name}/{remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in S3 storage with optional prefix filter."""
        try:
            files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to list files in S3: {e}")
            return []
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in S3 storage."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except self.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence in S3: {e}")
            return False
    
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get file information from S3 storage."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            
            return {
                "path": remote_path,
                "size": response.get('ContentLength', 0),
                "modified_time": response.get('LastModified'),
                "etag": response.get('ETag', '').strip('"'),
                "content_type": response.get('ContentType'),
                "storage_class": response.get('StorageClass', 'STANDARD')
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from S3: {e}")
            return None
    
    def get_backend_info(self) -> Dict:
        """Get S3 storage backend information."""
        try:
            # Get bucket information
            bucket_info = self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Count objects and calculate total size
            object_count = 0
            total_size = 0
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        object_count += 1
                        total_size += obj.get('Size', 0)
            
            return {
                "backend_type": "s3",
                "bucket_name": self.bucket_name,
                "region": self.region,
                "accessible": True,
                "object_count": object_count,
                "total_size": total_size,
                "bucket_creation_date": bucket_info.get('CreationDate')
            }
            
        except Exception as e:
            logger.error(f"Failed to get S3 backend info: {e}")
            return {"backend_type": "s3", "error": str(e)}


class SFTPStorageBackend(StorageBackend):
    """
    SFTP/SSH remote storage backend.
    
    Provides secure file transfer over SSH for remote backup storage.
    Requires paramiko library for SFTP functionality.
    """
    
    def __init__(self, hostname: str, username: str, password: Optional[str] = None,
                 private_key_path: Optional[str] = None, port: int = 22,
                 remote_base_path: str = "/backups"):
        """
        Initialize SFTP storage backend.
        
        Args:
            hostname: SFTP server hostname
            username: SSH username
            password: SSH password (if not using key authentication)
            private_key_path: Path to SSH private key file
            port: SSH port (default 22)
            remote_base_path: Base directory on remote server
        """
        try:
            import paramiko
            self.paramiko = paramiko
        except ImportError:
            raise ImportError("paramiko library required for SFTP storage backend")
        
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.port = port
        self.remote_base_path = remote_base_path
        
        self.ssh_client = None
        self.sftp_client = None
        
        # Test connection
        self._connect()
        logger.info(f"SFTP storage backend initialized: {username}@{hostname}:{port}")
    
    def _connect(self):
        """Establish SSH/SFTP connection."""
        try:
            self.ssh_client = self.paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(self.paramiko.AutoAddPolicy())
            
            # Connect using password or key authentication
            if self.private_key_path:
                private_key = self.paramiko.RSAKey.from_private_key_file(self.private_key_path)
                self.ssh_client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    pkey=private_key
                )
            else:
                self.ssh_client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=self.password
                )
            
            self.sftp_client = self.ssh_client.open_sftp()
            
            # Create base directory if it doesn't exist
            try:
                self.sftp_client.stat(self.remote_base_path)
            except FileNotFoundError:
                self.sftp_client.mkdir(self.remote_base_path)
            
        except Exception as e:
            logger.error(f"Failed to connect to SFTP server: {e}")
            raise
    
    def _ensure_connected(self):
        """Ensure SFTP connection is active."""
        if not self.sftp_client:
            self._connect()
    
    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        """Upload a file to SFTP storage."""
        try:
            self._ensure_connected()
            local_path = Path(local_path)
            full_remote_path = f"{self.remote_base_path}/{remote_path}"
            
            # Create remote directories if needed
            remote_dir = "/".join(full_remote_path.split("/")[:-1])
            self._mkdir_p(remote_dir)
            
            self.sftp_client.put(str(local_path), full_remote_path)
            logger.debug(f"Uploaded file to SFTP: {local_path} -> {full_remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to SFTP: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a file from SFTP storage."""
        try:
            self._ensure_connected()
            local_path = Path(local_path)
            full_remote_path = f"{self.remote_base_path}/{remote_path}"
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.sftp_client.get(full_remote_path, str(local_path))
            logger.debug(f"Downloaded file from SFTP: {full_remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from SFTP: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from SFTP storage."""
        try:
            self._ensure_connected()
            full_remote_path = f"{self.remote_base_path}/{remote_path}"
            
            self.sftp_client.remove(full_remote_path)
            logger.debug(f"Deleted file from SFTP: {full_remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from SFTP: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """List files in SFTP storage with optional prefix filter."""
        try:
            self._ensure_connected()
            files = []
            search_path = f"{self.remote_base_path}/{prefix}" if prefix else self.remote_base_path
            
            def walk_remote_dir(path):
                try:
                    for item in self.sftp_client.listdir_attr(path):
                        item_path = f"{path}/{item.filename}"
                        if self.paramiko.sftp_attr.S_ISDIR(item.st_mode):
                            walk_remote_dir(item_path)
                        else:
                            relative_path = item_path[len(self.remote_base_path):].lstrip('/')
                            if not prefix or relative_path.startswith(prefix):
                                files.append(relative_path)
                except Exception as e:
                    logger.error(f"Error walking remote directory {path}: {e}")
            
            walk_remote_dir(search_path)
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to list files in SFTP: {e}")
            return []
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in SFTP storage."""
        try:
            self._ensure_connected()
            full_remote_path = f"{self.remote_base_path}/{remote_path}"
            
            stat = self.sftp_client.stat(full_remote_path)
            return not self.paramiko.sftp_attr.S_ISDIR(stat.st_mode)
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence in SFTP: {e}")
            return False
    
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get file information from SFTP storage."""
        try:
            self._ensure_connected()
            full_remote_path = f"{self.remote_base_path}/{remote_path}"
            
            stat = self.sftp_client.stat(full_remote_path)
            return {
                "path": remote_path,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:],
                "is_directory": self.paramiko.sftp_attr.S_ISDIR(stat.st_mode)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from SFTP: {e}")
            return None
    
    def get_backend_info(self) -> Dict:
        """Get SFTP storage backend information."""
        try:
            self._ensure_connected()
            
            # Count files and calculate total size
            file_count = 0
            total_size = 0
            
            def count_files(path):
                nonlocal file_count, total_size
                try:
                    for item in self.sftp_client.listdir_attr(path):
                        item_path = f"{path}/{item.filename}"
                        if self.paramiko.sftp_attr.S_ISDIR(item.st_mode):
                            count_files(item_path)
                        else:
                            file_count += 1
                            total_size += item.st_size
                except Exception as e:
                    logger.error(f"Error counting files in {path}: {e}")
            
            count_files(self.remote_base_path)
            
            return {
                "backend_type": "sftp",
                "hostname": self.hostname,
                "username": self.username,
                "port": self.port,
                "remote_base_path": self.remote_base_path,
                "accessible": True,
                "file_count": file_count,
                "total_size": total_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get SFTP backend info: {e}")
            return {"backend_type": "sftp", "error": str(e)}
    
    def _mkdir_p(self, remote_path: str):
        """Create remote directory recursively."""
        try:
            dirs = remote_path.split('/')
            path = ""
            for dir_name in dirs:
                if dir_name:
                    path += f"/{dir_name}"
                    try:
                        self.sftp_client.stat(path)
                    except FileNotFoundError:
                        self.sftp_client.mkdir(path)
        except Exception as e:
            logger.error(f"Failed to create remote directory {remote_path}: {e}")
    
    def __del__(self):
        """Cleanup SFTP connection."""
        if self.sftp_client:
            self.sftp_client.close()
        if self.ssh_client:
            self.ssh_client.close()
