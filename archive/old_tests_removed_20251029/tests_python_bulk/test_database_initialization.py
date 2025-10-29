"""
Integration tests for database initialization and table creation.
"""

import pytest
from sqlalchemy import text, inspect
from api.orm_bootstrap import validate_or_initialize_database, engine, SessionLocal
from api.models import PerformanceMetric, QueryPerformanceLog, AuditLog


class TestDatabaseInitialization:
    """Test database initialization and table creation."""

    def test_validate_or_initialize_database_success(self):
        """Test that database validation/initialization succeeds."""
        result = validate_or_initialize_database()
        assert result is True

    def test_performance_metrics_table_exists(self):
        """Test that the performance_metrics table exists after initialization."""
        # Ensure database is initialized
        validate_or_initialize_database()
        
        # Check that the table exists using SQLAlchemy inspector
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        assert "performance_metrics" in table_names, "performance_metrics table should exist"

    def test_all_critical_tables_exist(self):
        """Test that all critical tables exist after initialization."""
        # Ensure database is initialized
        validate_or_initialize_database()
        
        # Check that all important tables exist
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            "users",
            "jobs", 
            "transcript_metadata",
            "config_entries",
            "user_settings",
            "audit_logs",
            "performance_metrics",
            "query_performance_logs"
        ]
        
        for table in expected_tables:
            assert table in table_names, f"Table {table} should exist"

    def test_performance_metrics_table_structure(self):
        """Test that the performance_metrics table has the correct structure."""
        # Ensure database is initialized
        validate_or_initialize_database()
        
        # Check table columns
        inspector = inspect(engine)
        columns = inspector.get_columns("performance_metrics")
        column_names = [col['name'] for col in columns]
        
        expected_columns = ['id', 'timestamp', 'metric_type', 'metric_name', 'value', 'unit', 'tags']
        
        for col in expected_columns:
            assert col in column_names, f"Column {col} should exist in performance_metrics table"

    def test_can_create_performance_metric_record(self):
        """Test that we can create and save a PerformanceMetric record."""
        from datetime import datetime
        
        # Ensure database is initialized
        validate_or_initialize_database()
        
        # Try to create and save a performance metric
        with SessionLocal() as db:
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                metric_type="test",
                metric_name="test_metric",
                value=42.0,
                unit="ms",
                tags='{"test": true}'
            )
            
            db.add(metric)
            db.commit()
            db.refresh(metric)
            
            # Verify it was saved
            assert metric.id is not None
            assert metric.value == 42.0
            assert metric.metric_name == "test_metric"

    def test_database_connection_after_initialization(self):
        """Test that database connection works after initialization."""
        # Ensure database is initialized
        validate_or_initialize_database()
        
        # Test basic database connectivity
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1

    def test_models_import_before_create_all(self):
        """Test that all models are properly imported and registered."""
        # This test verifies our fix - that api.models is imported before create_all
        from api.orm_bootstrap import Base
        
        # Check that our models are registered in Base.metadata
        table_names = list(Base.metadata.tables.keys())
        
        expected_tables = [
            "users",
            "jobs", 
            "transcript_metadata",
            "config_entries", 
            "user_settings",
            "audit_logs",
            "performance_metrics",
            "query_performance_logs"
        ]
        
        for table in expected_tables:
            assert table in table_names, f"Model for {table} should be registered in Base.metadata"