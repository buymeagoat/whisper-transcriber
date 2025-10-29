"""
Test suite for database performance monitoring functionality.
Tests the database performance monitoring system implemented for I005.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from api.database_performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    DatabaseAlert,
    AlertLevel
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics data structure."""
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics."""
        timestamp = datetime.utcnow()
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            query_time=0.5,
            connection_count=10,
            error_count=1,
            operation_type="SELECT"
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.query_time == 0.5
        assert metrics.connection_count == 10
        assert metrics.error_count == 1
        assert metrics.operation_type == "SELECT"
    
    def test_performance_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        timestamp = datetime.utcnow()
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            query_time=0.3,
            connection_count=5,
            error_count=0,
            operation_type="INSERT"
        )
        
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert metrics_dict['query_time'] == 0.3
        assert metrics_dict['connection_count'] == 5
        assert metrics_dict['error_count'] == 0
        assert metrics_dict['operation_type'] == "INSERT"


class TestDatabaseAlert:
    """Test DatabaseAlert functionality."""
    
    def test_alert_creation(self):
        """Test creating database alert."""
        alert = DatabaseAlert(
            level=AlertLevel.WARNING,
            message="High query time detected",
            metric_value=2.5,
            threshold=2.0
        )
        
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "High query time detected"
        assert alert.metric_value == 2.5
        assert alert.threshold == 2.0
        assert isinstance(alert.timestamp, datetime)


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create a PerformanceMonitor instance for testing."""
        return PerformanceMonitor()
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initializes with correct defaults."""
        assert monitor.query_time_threshold == 1.0
        assert monitor.error_rate_threshold == 0.1
        assert monitor.connection_count_threshold == 50
        assert monitor.monitoring_active is False
        assert len(monitor.metrics_history) == 0
        assert len(monitor.alerts) == 0
    
    def test_configure_thresholds(self, monitor):
        """Test configuring performance thresholds."""
        monitor.configure_thresholds(
            query_time=2.0,
            error_rate=0.05,
            connection_count=100
        )
        
        assert monitor.query_time_threshold == 2.0
        assert monitor.error_rate_threshold == 0.05
        assert monitor.connection_count_threshold == 100
    
    def test_add_metric(self, monitor):
        """Test adding performance metric."""
        monitor.add_metric(
            query_time=0.5,
            connection_count=10,
            error_count=0,
            operation_type="SELECT"
        )
        
        assert len(monitor.metrics_history) == 1
        metric = monitor.metrics_history[0]
        assert metric.query_time == 0.5
        assert metric.connection_count == 10
        assert metric.error_count == 0
        assert metric.operation_type == "SELECT"
    
    def test_alert_on_high_query_time(self, monitor):
        """Test alert generation for high query time."""
        monitor.query_time_threshold = 1.0
        
        monitor.add_metric(
            query_time=2.5,
            connection_count=5,
            error_count=0,
            operation_type="SELECT"
        )
        
        assert len(monitor.alerts) == 1
        alert = monitor.alerts[0]
        assert alert.level == AlertLevel.WARNING
        assert "query time" in alert.message.lower()
        assert alert.metric_value == 2.5
    
    def test_alert_on_high_connection_count(self, monitor):
        """Test alert generation for high connection count."""
        monitor.connection_count_threshold = 10
        
        monitor.add_metric(
            query_time=0.1,
            connection_count=15,
            error_count=0,
            operation_type="INSERT"
        )
        
        assert len(monitor.alerts) == 1
        alert = monitor.alerts[0]
        assert alert.level == AlertLevel.WARNING
        assert "connection count" in alert.message.lower()
    
    def test_get_current_metrics(self, monitor):
        """Test getting current performance metrics."""
        # Add some metrics
        monitor.add_metric(0.1, 5, 0, "SELECT")
        monitor.add_metric(0.2, 7, 1, "INSERT")
        monitor.add_metric(0.3, 6, 0, "UPDATE")
        
        current = monitor.get_current_metrics()
        
        assert current['total_operations'] == 3
        assert current['average_query_time'] == 0.2
        assert current['total_errors'] == 1
        assert current['average_connections'] == 6.0
    
    def test_get_alerts(self, monitor):
        """Test getting alerts."""
        # Generate some alerts
        monitor.query_time_threshold = 0.1
        monitor.add_metric(0.5, 5, 0, "SELECT")
        monitor.add_metric(0.6, 6, 0, "INSERT")
        
        alerts = monitor.get_alerts()
        assert len(alerts) == 2
        
        # Test filtering by level
        warning_alerts = monitor.get_alerts(level=AlertLevel.WARNING)
        assert len(warning_alerts) == 2
        
        critical_alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_alerts) == 0
    
    def test_clear_old_metrics(self, monitor):
        """Test clearing old metrics."""
        # Add metrics with different timestamps
        now = datetime.utcnow()
        old_time = now - timedelta(hours=25)  # Older than 24 hours
        
        # Mock the metric timestamps
        monitor.add_metric(0.1, 5, 0, "SELECT")
        monitor.metrics_history[0].timestamp = old_time
        
        monitor.add_metric(0.2, 6, 0, "INSERT")  # Recent metric
        
        assert len(monitor.metrics_history) == 2
        
        monitor.clear_old_metrics()
        
        # Should only have the recent metric
        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0].query_time == 0.2
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """Test starting monitoring with background task."""
        with patch.object(monitor, '_monitoring_loop') as mock_loop:
            mock_loop.return_value = AsyncMock()
            
            await monitor.start_monitoring()
            assert monitor.monitoring_active is True
            mock_loop.assert_called_once()
    
    def test_stop_monitoring(self, monitor):
        """Test stopping monitoring."""
        monitor.monitoring_active = True
        monitor.stop_monitoring()
        assert monitor.monitoring_active is False
    
    def test_calculate_error_rate(self, monitor):
        """Test error rate calculation."""
        # Add metrics with some errors
        monitor.add_metric(0.1, 5, 1, "SELECT")  # 1 error
        monitor.add_metric(0.1, 5, 0, "INSERT")  # 0 errors
        monitor.add_metric(0.1, 5, 2, "UPDATE")  # 2 errors
        
        error_rate = monitor._calculate_error_rate()
        assert error_rate == 1.0  # 3 errors out of 3 operations = 100%
    
    def test_metrics_history_limit(self, monitor):
        """Test that metrics history respects maximum size."""
        monitor.max_metrics_history = 5
        
        # Add more metrics than the limit
        for i in range(10):
            monitor.add_metric(0.1, 5, 0, "SELECT")
        
        # Should only keep the most recent metrics
        assert len(monitor.metrics_history) == 5


class TestPerformanceMonitorIntegration:
    """Integration tests for performance monitoring."""
    
    @pytest.mark.asyncio
    async def test_monitoring_workflow(self):
        """Test complete monitoring workflow."""
        monitor = PerformanceMonitor()
        monitor.configure_thresholds(
            query_time=0.5,
            error_rate=0.2,
            connection_count=10
        )
        
        # Simulate normal operations
        monitor.add_metric(0.1, 3, 0, "SELECT")
        monitor.add_metric(0.2, 4, 0, "INSERT")
        
        # No alerts should be generated
        assert len(monitor.get_alerts()) == 0
        
        # Simulate problematic operations
        monitor.add_metric(1.0, 15, 1, "SELECT")  # High query time and connections
        
        # Should generate alerts
        alerts = monitor.get_alerts()
        assert len(alerts) >= 1
        
        # Check current metrics
        current = monitor.get_current_metrics()
        assert current['total_operations'] == 3
        assert current['total_errors'] == 1
    
    def test_threshold_configuration_validation(self):
        """Test validation of threshold configuration."""
        monitor = PerformanceMonitor()
        
        # Test valid configuration
        monitor.configure_thresholds(
            query_time=1.0,
            error_rate=0.1,
            connection_count=50
        )
        
        assert monitor.query_time_threshold == 1.0
        assert monitor.error_rate_threshold == 0.1
        assert monitor.connection_count_threshold == 50
        
        # Test with None values (should keep existing)
        original_query_time = monitor.query_time_threshold
        monitor.configure_thresholds(query_time=None)
        assert monitor.query_time_threshold == original_query_time