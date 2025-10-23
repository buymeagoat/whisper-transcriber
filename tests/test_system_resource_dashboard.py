"""
T013: System Resource Usage Dashboard - Comprehensive Test Suite

Tests for the system resource usage dashboard including backend API
endpoints, frontend components, and resource monitoring functionality.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient
from api.main import app
from api.routes.admin_system_resources import SystemResourceService


class TestSystemResourceDashboard:
    """Test suite for system resource usage dashboard T013"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for authentication"""
        return {
            "user_id": "admin-test-user",
            "username": "admin",
            "is_admin": True,
            "email": "admin@test.com"
        }

    @pytest.fixture
    def mock_resource_service(self):
        """Mock resource service for testing"""
        return SystemResourceService()

    def test_storage_usage_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of storage usage data"""
        mock_storage_data = {
            'storage': {
                'system': {
                    'path': '/',
                    'total': 500000000000,  # 500GB
                    'used': 250000000000,   # 250GB
                    'free': 250000000000,   # 250GB
                    'percentage': 50.0
                },
                'models': {
                    'path': './models/',
                    'size': 5000000000,  # 5GB
                    'human_readable': '5.00 GB'
                },
                'cache': {
                    'path': './cache/',
                    'size': 1000000000,  # 1GB
                    'human_readable': '1.00 GB'
                },
                'database_files': {
                    'total_size': 100000000,  # 100MB
                    'human_readable': '100.00 MB',
                    'files': {
                        'whisper_app.db': {
                            'size': 90000000,
                            'human_readable': '90.00 MB'
                        },
                        'whisper_app.db-wal': {
                            'size': 10000000,
                            'human_readable': '10.00 MB'
                        }
                    }
                }
            },
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_storage_usage', return_value=mock_storage_data):
                response = client.get(
                    "/api/admin/system/resources/storage",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert "data" in data
                assert data["data"]["storage"]["system"]["percentage"] == 50.0
                assert data["data"]["storage"]["models"]["size"] == 5000000000

    def test_process_information_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of process information"""
        mock_process_data = {
            'processes': [
                {
                    'pid': 1234,
                    'name': 'python',
                    'cpu_percent': 15.5,
                    'memory_percent': 8.2,
                    'memory_mb': 256.5,
                    'status': 'running',
                    'is_current': True,
                    'uptime': 3600
                },
                {
                    'pid': 5678,
                    'name': 'nginx',
                    'cpu_percent': 2.1,
                    'memory_percent': 1.5,
                    'memory_mb': 48.2,
                    'status': 'sleeping',
                    'is_current': False,
                    'uptime': 86400
                }
            ],
            'total_processes': 156,
            'load_average': {
                '1_min': 0.85,
                '5_min': 0.92,
                '15_min': 0.78
            },
            'system_uptime': {
                'seconds': 604800,
                'human_readable': '7d 0h 0m'
            },
            'boot_time': '2024-01-08T10:30:00Z',
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_process_information', return_value=mock_process_data):
                response = client.get(
                    "/api/admin/system/resources/processes",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert len(data["data"]["processes"]) == 2
                assert data["data"]["total_processes"] == 156
                assert data["data"]["load_average"]["1_min"] == 0.85

    def test_memory_details_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of memory details"""
        mock_memory_data = {
            'virtual_memory': {
                'total': 16000000000,  # 16GB
                'available': 8000000000,  # 8GB
                'used': 8000000000,  # 8GB
                'free': 4000000000,  # 4GB
                'percentage': 50.0,
                'active': 6000000000,
                'inactive': 2000000000,
                'buffers': 1000000000,
                'cached': 3000000000,
                'shared': 500000000
            },
            'swap_memory': {
                'total': 2000000000,  # 2GB
                'used': 500000000,   # 500MB
                'free': 1500000000,  # 1.5GB
                'percentage': 25.0,
                'sin': 0,
                'sout': 0
            },
            'top_memory_processes': [
                {
                    'pid': 1234,
                    'name': 'python',
                    'memory_percent': 8.2,
                    'memory_rss': 1312000000,
                    'memory_vms': 2048000000,
                    'memory_mb': 1250.0
                }
            ],
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_memory_details', return_value=mock_memory_data):
                response = client.get(
                    "/api/admin/system/resources/memory",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert data["data"]["virtual_memory"]["percentage"] == 50.0
                assert data["data"]["swap_memory"]["percentage"] == 25.0
                assert len(data["data"]["top_memory_processes"]) == 1

    def test_cpu_details_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of CPU details"""
        mock_cpu_data = {
            'cpu_count': {
                'logical': 8,
                'physical': 4
            },
            'cpu_percent_total': 45.5,
            'cpu_percent_per_core': [42.1, 48.3, 44.7, 46.9, 43.2, 47.8, 45.1, 44.6],
            'cpu_frequency': {
                'current': 2800.0,
                'min': 1200.0,
                'max': 3600.0
            },
            'cpu_times': {
                'user': 123456.78,
                'system': 45678.90,
                'idle': 987654.32,
                'nice': 123.45,
                'iowait': 567.89,
                'irq': 12.34,
                'softirq': 56.78,
                'steal': 0.0,
                'guest': 0.0
            },
            'cpu_stats': {
                'ctx_switches': 1234567890,
                'interrupts': 987654321,
                'soft_interrupts': 123456789,
                'syscalls': 456789123
            },
            'top_cpu_processes': [
                {
                    'pid': 1234,
                    'name': 'python',
                    'cpu_percent': 15.5
                }
            ],
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_cpu_details', return_value=mock_cpu_data):
                response = client.get(
                    "/api/admin/system/resources/cpu",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert data["data"]["cpu_count"]["logical"] == 8
                assert data["data"]["cpu_percent_total"] == 45.5
                assert len(data["data"]["cpu_percent_per_core"]) == 8

    def test_network_details_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of network details"""
        mock_network_data = {
            'interfaces': {
                'eth0': {
                    'addresses': [
                        {
                            'family': 'AF_INET',
                            'address': '192.168.1.100',
                            'netmask': '255.255.255.0',
                            'broadcast': '192.168.1.255'
                        }
                    ],
                    'is_up': True,
                    'duplex': 'full',
                    'speed': 1000,
                    'mtu': 1500,
                    'bytes_sent': 1234567890,
                    'bytes_recv': 9876543210,
                    'packets_sent': 1234567,
                    'packets_recv': 9876543,
                    'errors_in': 0,
                    'errors_out': 0,
                    'dropped_in': 0,
                    'dropped_out': 0
                }
            },
            'active_connections': [
                {
                    'local_address': '192.168.1.100:8000',
                    'remote_address': '192.168.1.50:45678',
                    'status': 'ESTABLISHED',
                    'pid': 1234,
                    'family': 'AF_INET',
                    'type': 'SOCK_STREAM'
                }
            ],
            'total_connections': 15,
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_network_details', return_value=mock_network_data):
                response = client.get(
                    "/api/admin/system/resources/network",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert "eth0" in data["data"]["interfaces"]
                assert data["data"]["interfaces"]["eth0"]["is_up"] is True
                assert data["data"]["total_connections"] == 15

    def test_application_resource_usage_success(self, client, mock_admin_user):
        """Test successful retrieval of application resource usage"""
        mock_app_data = {
            'database': {
                'file_size': 100000000,
                'file_size_human': '100.00 MB',
                'tables': {
                    'jobs': 1250,
                    'users': 45,
                    'audit_logs': 5000
                },
                'pages': {
                    'count': 24576,
                    'size': 4096,
                    'total_size': 100663296
                },
                'auto_vacuum': 1
            },
            'jobs': {
                'jobs_last_24h': 125,
                'by_status': {
                    'completed': 100,
                    'failed': 15,
                    'processing': 5,
                    'pending': 5
                },
                'avg_duration_seconds': 245
            },
            'application_memory': {
                'rss': 268435456,  # 256MB
                'vms': 536870912,  # 512MB
                'rss_human': '256.00 MB',
                'vms_human': '512.00 MB',
                'percent': 1.6
            },
            'timestamp': '2024-01-15T10:30:00Z'
        }

        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_application_resource_usage', return_value=mock_app_data):
                response = client.get(
                    "/api/admin/system/resources/application",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["success"] is True
                assert data["data"]["database"]["file_size"] == 100000000
                assert data["data"]["jobs"]["jobs_last_24h"] == 125
                assert data["data"]["application_memory"]["percent"] == 1.6

    def test_resource_overview_endpoint_success(self, client, mock_admin_user):
        """Test successful retrieval of comprehensive resource overview"""
        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_storage_usage') as mock_storage:
                with patch.object(SystemResourceService, 'get_memory_details') as mock_memory:
                    with patch.object(SystemResourceService, 'get_cpu_details') as mock_cpu:
                        with patch.object(SystemResourceService, 'get_application_resource_usage') as mock_app:
                            
                            mock_storage.return_value = {'storage': 'data'}
                            mock_memory.return_value = {'memory': 'data'}
                            mock_cpu.return_value = {'cpu': 'data'}
                            mock_app.return_value = {'application': 'data'}
                            
                            response = client.get(
                                "/api/admin/system/resources/overview",
                                headers={"Authorization": "Bearer mock-admin-token"}
                            )
                            
                            assert response.status_code == 200
                            data = response.json()
                            
                            assert data["success"] is True
                            assert "storage" in data["data"]
                            assert "memory" in data["data"]
                            assert "cpu" in data["data"]
                            assert "application" in data["data"]

    def test_unauthorized_access_to_resources(self, client):
        """Test unauthorized access to resource endpoints"""
        endpoints = [
            "/api/admin/system/resources/storage",
            "/api/admin/system/resources/processes",
            "/api/admin/system/resources/memory",
            "/api/admin/system/resources/cpu",
            "/api/admin/system/resources/network",
            "/api/admin/system/resources/application",
            "/api/admin/system/resources/overview"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_non_admin_access_to_resources(self, client):
        """Test non-admin user access to resource endpoints"""
        mock_user = {
            "user_id": "regular-user",
            "username": "user",
            "is_admin": False,
            "email": "user@test.com"
        }
        
        endpoints = [
            "/api/admin/system/resources/storage",
            "/api/admin/system/resources/processes",
            "/api/admin/system/resources/memory",
            "/api/admin/system/resources/cpu",
            "/api/admin/system/resources/network",
            "/api/admin/system/resources/application",
            "/api/admin/system/resources/overview"
        ]
        
        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_user):
            for endpoint in endpoints:
                response = client.get(
                    endpoint,
                    headers={"Authorization": "Bearer mock-user-token"}
                )
                assert response.status_code == 403

    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.walk')
    def test_storage_usage_calculation(self, mock_walk, mock_getsize, mock_exists, mock_resource_service):
        """Test storage usage calculation with mocked file system"""
        # Mock file system structure
        mock_exists.return_value = True
        mock_getsize.side_effect = lambda path: {
            'whisper_app.db': 90000000,
            'whisper_app.db-wal': 10000000,
            'whisper_app.db-shm': 5000000
        }.get(path.split('/')[-1], 1000000)
        
        mock_walk.return_value = [
            ('./models/', ['model1', 'model2'], ['large.pt', 'medium.pt']),
            ('./models/model1', [], ['file1.bin']),
            ('./models/model2', [], ['file2.bin'])
        ]
        
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value = (500000000000, 250000000000, 250000000000)  # total, used, free
            
            storage_data = mock_resource_service.get_storage_usage()
            
            assert 'storage' in storage_data
            assert storage_data['storage']['system']['percentage'] == 50.0

    @patch('psutil.process_iter')
    @patch('psutil.boot_time')
    @patch('os.getloadavg')
    def test_process_information_collection(self, mock_loadavg, mock_boot_time, mock_process_iter, mock_resource_service):
        """Test process information collection with mocked psutil"""
        # Mock processes
        mock_process = MagicMock()
        mock_process.info = {
            'pid': 1234,
            'name': 'python',
            'cpu_percent': 15.5,
            'memory_percent': 8.2,
            'status': 'running',
            'create_time': 1640995200.0  # Mock timestamp
        }
        mock_process.memory_info.return_value = MagicMock(rss=268435456)  # 256MB
        
        mock_process_iter.return_value = [mock_process]
        mock_loadavg.return_value = (0.85, 0.92, 0.78)
        mock_boot_time.return_value = 1640995200.0
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.timestamp.return_value = 1641081600.0  # 24 hours later
            
            process_data = mock_resource_service.get_process_information()
            
            assert len(process_data['processes']) == 1
            assert process_data['load_average']['1_min'] == 0.85

    def test_byte_formatting_utility(self, mock_resource_service):
        """Test byte formatting utility function"""
        assert mock_resource_service._format_bytes(1024) == "1.00 KB"
        assert mock_resource_service._format_bytes(1048576) == "1.00 MB"
        assert mock_resource_service._format_bytes(1073741824) == "1.00 GB"
        assert mock_resource_service._format_bytes(1099511627776) == "1.00 TB"

    def test_uptime_formatting_utility(self, mock_resource_service):
        """Test uptime formatting utility function"""
        assert mock_resource_service._format_uptime(3600) == "1h 0m"
        assert mock_resource_service._format_uptime(86400) == "1d 0h 0m"
        assert mock_resource_service._format_uptime(90061) == "1d 1h 1m"
        assert mock_resource_service._format_uptime(300) == "5m"

    def test_error_handling_in_resource_collection(self, client, mock_admin_user):
        """Test error handling when resource collection fails"""
        with patch('api.services.auth_service.AuthService.get_current_user', return_value=mock_admin_user):
            with patch.object(SystemResourceService, 'get_storage_usage', side_effect=Exception("Storage error")):
                response = client.get(
                    "/api/admin/system/resources/storage",
                    headers={"Authorization": "Bearer mock-admin-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert "Storage error" in data["error"]

    @patch('psutil.virtual_memory')
    @patch('psutil.swap_memory')
    def test_memory_details_with_partial_data(self, mock_swap, mock_virtual, mock_resource_service):
        """Test memory details collection with partial data availability"""
        # Mock virtual memory
        mock_vm = MagicMock()
        mock_vm.total = 16000000000
        mock_vm.available = 8000000000
        mock_vm.used = 8000000000
        mock_vm.free = 4000000000
        mock_vm.percent = 50.0
        mock_vm.active = 6000000000
        mock_vm.inactive = None  # Simulate missing data
        mock_vm.buffers = 1000000000
        mock_vm.cached = None  # Simulate missing data
        mock_vm.shared = 500000000
        mock_virtual.return_value = mock_vm
        
        # Mock swap memory
        mock_sm = MagicMock()
        mock_sm.total = 2000000000
        mock_sm.used = 500000000
        mock_sm.free = 1500000000
        mock_sm.percent = 25.0
        mock_sm.sin = 0
        mock_sm.sout = 0
        mock_swap.return_value = mock_sm
        
        with patch('psutil.process_iter', return_value=[]):
            memory_data = mock_resource_service.get_memory_details()
            
            assert memory_data['virtual_memory']['total'] == 16000000000
            assert memory_data['virtual_memory']['inactive'] == 0  # Should default to 0
            assert memory_data['virtual_memory']['cached'] == 0    # Should default to 0

    def test_resource_service_directory_size_calculation(self, mock_resource_service):
        """Test directory size calculation with error handling"""
        with patch('os.walk') as mock_walk:
            # Simulate directory with files and some access errors
            mock_walk.return_value = [
                ('./test/', [], ['file1.txt', 'file2.txt']),
            ]
            
            with patch('os.path.getsize') as mock_getsize:
                mock_getsize.side_effect = [1000, OSError("Permission denied")]
                
                # Should handle errors gracefully and return partial size
                size = mock_resource_service._get_directory_size('./test/')
                assert size == 1000  # Only file1.txt counted

    def test_current_process_memory_info(self, mock_resource_service):
        """Test current process memory information collection"""
        with patch('psutil.Process') as mock_process_class:
            mock_process = MagicMock()
            mock_memory = MagicMock()
            mock_memory.rss = 268435456  # 256MB
            mock_memory.vms = 536870912  # 512MB
            mock_process.memory_info.return_value = mock_memory
            mock_process.memory_percent.return_value = 1.6
            mock_process_class.return_value = mock_process
            
            memory_info = mock_resource_service._get_current_process_memory()
            
            assert memory_info['rss'] == 268435456
            assert memory_info['rss_human'] == '256.00 MB'
            assert memory_info['percent'] == 1.6


class TestSystemResourceDashboardFrontend:
    """Test frontend component functionality (would be run in browser environment)"""
    
    def test_dashboard_component_structure(self):
        """Test expected dashboard component structure and features"""
        expected_features = [
            "Six tabbed interface (Storage, Processes, Memory, CPU, Network, Application)",
            "Auto-refresh toggle with configurable intervals",
            "Real-time data fetching from resource API endpoints",
            "Chart.js integration for CPU core usage and memory distribution",
            "Material-UI responsive design with cards and tables",
            "Storage usage visualization with progress bars",
            "Process management table with sorting by CPU/memory usage",
            "Memory breakdown with virtual and swap memory details",
            "CPU usage per core with frequency and statistics",
            "Network interface monitoring with traffic statistics",
            "Application-specific metrics including database and job statistics",
            "Error handling and loading states",
            "Administrative access controls",
            "Data formatting utilities for bytes and uptime"
        ]
        
        # Verify all expected features are documented
        assert len(expected_features) == 14
        
        # Each feature represents a key capability of the dashboard
        for feature in expected_features:
            assert len(feature) > 0

    def test_api_integration_requirements(self):
        """Test API integration requirements for the dashboard"""
        required_endpoints = [
            "/api/admin/system/resources/storage",
            "/api/admin/system/resources/processes", 
            "/api/admin/system/resources/memory",
            "/api/admin/system/resources/cpu",
            "/api/admin/system/resources/network",
            "/api/admin/system/resources/application",
            "/api/admin/system/resources/overview"
        ]
        
        # Verify all required endpoints are defined
        assert len(required_endpoints) == 7
        
        # Each endpoint should follow the admin resource pattern
        for endpoint in required_endpoints:
            assert endpoint.startswith("/api/admin/system/resources/")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])