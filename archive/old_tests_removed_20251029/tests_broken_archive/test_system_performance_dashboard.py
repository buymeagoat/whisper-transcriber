"""
Test Suite for T032: System Performance Dashboard
Comprehensive testing for system monitoring and performance analytics
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.database import get_db
from api.auth import get_current_user
from api.models import User
from api.routes.admin_system_performance import SystemPerformanceService, perf_service


class TestSystemPerformanceService:
    """Test the SystemPerformanceService class"""
    
    @pytest.fixture
    def service(self):
        return SystemPerformanceService()
    
    @pytest.fixture
    def mock_db(self):
        db = Mock(spec=Session)
        # Mock database query results
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        db.execute.return_value = mock_result
        return db
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, service):
        """Test system metrics collection"""
        with patch('psutil.cpu_percent', return_value=45.2), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.cpu_freq') as mock_freq, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network, \
             patch('psutil.net_connections', return_value=[1, 2, 3]):
            
            # Mock CPU frequency
            mock_freq.return_value = Mock(current=3200)
            
            # Mock memory info
            mock_memory.return_value = Mock(
                used=6442450944,
                total=17179869184,
                percent=37.5
            )
            
            # Mock disk info
            mock_disk.return_value = Mock(
                used=536870912000,
                total=1099511627776
            )
            
            # Mock network info
            mock_network.return_value = Mock(
                bytes_recv=1048576,
                bytes_sent=524288
            )
            
            metrics = await service.get_system_metrics()
            
            assert 'cpu_usage' in metrics
            assert 'memory_percentage' in metrics
            assert 'disk_percentage' in metrics
            assert 'network_connections' in metrics
            assert metrics['cpu_cores'] == 8
            assert metrics['cpu_frequency'] == 3.2
            assert isinstance(metrics['timestamp'], str)
    
    @pytest.mark.asyncio
    async def test_get_application_metrics(self, service, mock_db):
        """Test application metrics collection"""
        metrics = await service.get_application_metrics(mock_db)
        
        assert 'active_jobs' in metrics
        assert 'queue_size' in metrics
        assert 'error_rate' in metrics
        assert 'avg_response_time' in metrics
        assert 'throughput' in metrics
        assert 'uptime' in metrics
        assert isinstance(metrics['timestamp'], str)
    
    @pytest.mark.asyncio
    async def test_get_service_status(self, service):
        """Test service status collection"""
        with patch('sqlite3.connect') as mock_connect, \
             patch('psutil.process_iter') as mock_processes:
            
            # Mock successful database connection
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            # Mock process list
            mock_processes.return_value = []
            
            services = await service.get_service_status()
            
            assert isinstance(services, list)
            assert len(services) >= 5  # Should have at least 5 mock services
            
            # Check service structure
            for service_info in services:
                assert 'name' in service_info
                assert 'status' in service_info
                assert 'lastCheck' in service_info
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, service, mock_db):
        """Test alert generation logic"""
        with patch.object(service, 'get_system_metrics') as mock_system_metrics, \
             patch.object(service, 'get_application_metrics') as mock_app_metrics:
            
            # Test high CPU alert
            mock_system_metrics.return_value = {
                'cpu_usage': 85.0,
                'memory_percentage': 45.0,
                'disk_percentage': 50.0
            }
            mock_app_metrics.return_value = {
                'error_rate': 2.0,
                'queue_size': 30
            }
            
            alerts = await service.get_active_alerts(mock_db)
            
            assert isinstance(alerts, list)
            # Should have CPU alert
            cpu_alerts = [a for a in alerts if 'cpu' in a['id'].lower()]
            assert len(cpu_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_get_active_alerts_critical(self, service, mock_db):
        """Test critical alert generation"""
        with patch.object(service, 'get_system_metrics') as mock_system_metrics, \
             patch.object(service, 'get_application_metrics') as mock_app_metrics:
            
            # Test critical conditions
            mock_system_metrics.return_value = {
                'cpu_usage': 95.0,
                'memory_percentage': 96.0,
                'disk_percentage': 97.0
            }
            mock_app_metrics.return_value = {
                'error_rate': 15.0,
                'queue_size': 150
            }
            
            alerts = await service.get_active_alerts(mock_db)
            
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            assert len(critical_alerts) >= 3  # CPU, memory, disk should be critical


class TestSystemPerformanceAPI:
    """Test the system performance API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.email = "admin@example.com"
        user.is_admin = True
        return user
    
    @pytest.fixture
    def mock_regular_user(self):
        user = Mock(spec=User)
        user.id = 2
        user.email = "user@example.com"
        user.is_admin = False
        return user
    
    def test_get_system_metrics_admin_required(self, client):
        """Test that admin authentication is required"""
        response = client.get("/admin/system/metrics")
        assert response.status_code == 401
    
    def test_get_system_metrics_success(self, client, mock_admin_user):
        """Test successful metrics retrieval"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('api.routes.admin_system_performance.get_db'), \
             patch.object(perf_service, 'get_system_metrics') as mock_system, \
             patch.object(perf_service, 'get_application_metrics') as mock_app:
            
            mock_system.return_value = {
                'cpu_usage': 45.2,
                'memory_percentage': 37.5,
                'timestamp': '2024-01-01T12:00:00'
            }
            mock_app.return_value = {
                'active_jobs': 3,
                'error_rate': 1.2,
                'timestamp': '2024-01-01T12:00:00'
            }
            
            response = client.get("/admin/system/metrics")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'cpu_usage' in data['data']
            assert 'active_jobs' in data['data']
    
    def test_get_historical_metrics(self, client, mock_admin_user):
        """Test historical metrics endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user):
            response = client.get("/admin/system/metrics/historical?timeRange=1h")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'labels' in data['data']
            assert 'datasets' in data['data']
            assert data['data']['timeRange'] == '1h'
    
    def test_get_historical_metrics_invalid_range(self, client, mock_admin_user):
        """Test invalid time range parameter"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user):
            response = client.get("/admin/system/metrics/historical?timeRange=invalid")
            assert response.status_code == 422  # Validation error
    
    def test_get_active_alerts(self, client, mock_admin_user):
        """Test active alerts endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('api.routes.admin_system_performance.get_db'), \
             patch.object(perf_service, 'get_active_alerts') as mock_alerts:
            
            mock_alerts.return_value = [
                {
                    'id': 'test_alert',
                    'title': 'Test Alert',
                    'severity': 'warning',
                    'timestamp': '2024-01-01T12:00:00'
                }
            ]
            
            response = client.get("/admin/system/alerts")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert len(data['data']['alerts']) == 1
            assert data['data']['count'] == 1
    
    def test_get_service_status(self, client, mock_admin_user):
        """Test service status endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch.object(perf_service, 'get_service_status') as mock_services:
            
            mock_services.return_value = [
                {
                    'name': 'Test Service',
                    'status': 'healthy',
                    'lastCheck': '2024-01-01T12:00:00'
                }
            ]
            
            response = client.get("/admin/system/services")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert len(data['data']['services']) == 1
    
    def test_get_performance_analytics(self, client, mock_admin_user):
        """Test performance analytics endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('api.routes.admin_system_performance.get_db'), \
             patch.object(perf_service, 'get_system_metrics') as mock_system, \
             patch.object(perf_service, 'get_application_metrics') as mock_app:
            
            mock_system.return_value = {'cpu_usage': 45.2}
            mock_app.return_value = {'avg_response_time': 150}
            
            response = client.get("/admin/system/analytics")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'performance_score' in data['data']
            assert 'trends' in data['data']
            assert 'recommendations' in data['data']
    
    def test_get_component_resource_usage(self, client, mock_admin_user):
        """Test component resource usage endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('psutil.process_iter') as mock_processes:
            
            # Mock process list
            mock_processes.return_value = []
            
            response = client.get("/admin/system/components")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'components' in data['data']
    
    def test_get_optimization_recommendations(self, client, mock_admin_user):
        """Test optimization recommendations endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('api.routes.admin_system_performance.get_db'), \
             patch.object(perf_service, 'get_system_metrics') as mock_system, \
             patch.object(perf_service, 'get_application_metrics') as mock_app:
            
            mock_system.return_value = {
                'cpu_usage': 85.0,
                'memory_percentage': 90.0
            }
            mock_app.return_value = {
                'queue_size': 75
            }
            
            response = client.get("/admin/system/optimization")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'recommendations' in data['data']
            assert 'system_score' in data['data']
            
            # Should have recommendations for high CPU and memory
            recommendations = data['data']['recommendations']
            assert len(recommendations) > 0
    
    def test_acknowledge_alert(self, client, mock_admin_user):
        """Test alert acknowledgment endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user):
            response = client.post("/admin/system/alerts/test_alert/acknowledge")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'acknowledged_at' in data
            assert data['acknowledged_by'] == mock_admin_user.email
    
    def test_get_system_health_summary(self, client, mock_admin_user):
        """Test system health summary endpoint"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_admin_user), \
             patch('api.routes.admin_system_performance.get_db'), \
             patch.object(perf_service, 'get_system_metrics') as mock_system, \
             patch.object(perf_service, 'get_application_metrics') as mock_app, \
             patch.object(perf_service, 'get_active_alerts') as mock_alerts, \
             patch.object(perf_service, 'get_service_status') as mock_services:
            
            mock_system.return_value = {
                'cpu_usage': 45.0,
                'memory_percentage': 35.0,
                'disk_percentage': 50.0
            }
            mock_app.return_value = {
                'error_rate': 2.0,
                'queue_size': 10
            }
            mock_alerts.return_value = []
            mock_services.return_value = [
                {'status': 'healthy'},
                {'status': 'healthy'},
                {'status': 'warning'}
            ]
            
            response = client.get("/admin/system/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'overall_health' in data['data']
            assert 'status' in data['data']
            assert data['data']['overall_health'] > 0
    
    def test_non_admin_access_denied(self, client, mock_regular_user):
        """Test that non-admin users are denied access"""
        with patch('api.routes.admin_system_performance.get_current_user', return_value=mock_regular_user):
            endpoints = [
                "/admin/system/metrics",
                "/admin/system/alerts",
                "/admin/system/services",
                "/admin/system/analytics",
                "/admin/system/components",
                "/admin/system/optimization",
                "/admin/system/health"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                # Should be forbidden due to admin_required decorator
                assert response.status_code in [401, 403]


class TestSystemPerformanceFrontend:
    """Test frontend service integration"""
    
    def test_system_performance_service_mock_data(self):
        """Test that mock data is properly structured"""
        from frontend.src.services.systemPerformanceService import systemPerformanceService
        
        mock_data = systemPerformanceService.getMockSystemMetrics()
        
        # Verify structure
        assert 'data' in mock_data
        assert 'system' in mock_data['data']
        assert 'application' in mock_data['data']
        
        # Verify system metrics
        system = mock_data['data']['system']
        assert 'cpu' in system
        assert 'memory' in system
        assert 'disk' in system
        assert 'network' in system
        
        # Verify application metrics
        app = mock_data['data']['application']
        assert 'activeJobs' in app
        assert 'queueSize' in app
        assert 'errorRate' in app
        assert 'responseTime' in app
    
    def test_formatting_utilities(self):
        """Test utility formatting functions"""
        # This would require a way to test JavaScript functions
        # In a real implementation, you might use Jest for frontend testing
        pass


class TestSystemPerformanceIntegration:
    """Integration tests for the complete system performance monitoring"""
    
    @pytest.mark.asyncio
    async def test_complete_metrics_flow(self):
        """Test complete flow from service to API response"""
        service = SystemPerformanceService()
        
        with patch('psutil.cpu_percent', return_value=45.2), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('sqlite3.connect'):
            
            mock_memory.return_value = Mock(
                used=6442450944,
                total=17179869184,
                percent=37.5
            )
            mock_disk.return_value = Mock(
                used=536870912000,
                total=1099511627776
            )
            
            # Create mock database
            mock_db = Mock(spec=Session)
            mock_result = Mock()
            mock_result.scalar.return_value = 5
            mock_db.execute.return_value = mock_result
            
            # Test system metrics
            system_metrics = await service.get_system_metrics()
            assert 'cpu_usage' in system_metrics
            
            # Test application metrics
            app_metrics = await service.get_application_metrics(mock_db)
            assert 'active_jobs' in app_metrics
            
            # Test service status
            services = await service.get_service_status()
            assert isinstance(services, list)
            
            # Test alerts
            alerts = await service.get_active_alerts(mock_db)
            assert isinstance(alerts, list)
    
    def test_error_handling(self):
        """Test error handling in service methods"""
        service = SystemPerformanceService()
        
        # Test with mocked exceptions
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                asyncio.run(service.get_system_metrics())
    
    def test_caching_behavior(self):
        """Test metrics caching functionality"""
        service = SystemPerformanceService()
        
        # Test cache timeout behavior
        assert service.cache_timeout == 30
        assert isinstance(service.metrics_cache, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])