"""
Test suite for optimized database configuration functionality.
Tests the database configuration optimization implemented for I005.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from api.optimized_database_config import (
    DatabaseConfiguration,
    ConnectionPoolConfig,
    OptimizationLevel
)


class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig data structure."""
    
    def test_connection_pool_config_creation(self):
        """Test creating connection pool configuration."""
        config = ConnectionPoolConfig(
            pool_size=20,
            max_overflow=30,
            pool_timeout=60,
            pool_recycle=7200
        )
        
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200
    
    def test_connection_pool_config_defaults(self):
        """Test default values for connection pool config."""
        config = ConnectionPoolConfig()
        
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600


class TestDatabaseConfiguration:
    """Test DatabaseConfiguration class."""
    
    @pytest.fixture
    def config(self):
        """Create a DatabaseConfiguration instance for testing."""
        return DatabaseConfiguration()
    
    def test_sqlite_optimization_configuration(self, config):
        """Test SQLite optimization configuration."""
        optimizations = config.get_sqlite_optimizations(OptimizationLevel.HIGH)
        
        assert 'journal_mode' in optimizations
        assert 'cache_size' in optimizations
        assert 'busy_timeout' in optimizations
        assert 'foreign_keys' in optimizations
        assert 'synchronous' in optimizations
        assert 'temp_store' in optimizations
        
        # Check specific values for high optimization
        assert optimizations['journal_mode'] == 'WAL'
        assert optimizations['cache_size'] == -65536  # 64MB
        assert optimizations['busy_timeout'] == 30000
        assert optimizations['foreign_keys'] == 'ON'
    
    def test_sqlite_optimization_levels(self, config):
        """Test different SQLite optimization levels."""
        basic_opts = config.get_sqlite_optimizations(OptimizationLevel.BASIC)
        high_opts = config.get_sqlite_optimizations(OptimizationLevel.HIGH)
        max_opts = config.get_sqlite_optimizations(OptimizationLevel.MAXIMUM)
        
        # Basic should have fewer optimizations
        assert len(basic_opts) < len(high_opts)
        
        # Maximum should have the most aggressive settings
        assert max_opts['cache_size'] <= high_opts['cache_size']  # More negative = more cache
        assert max_opts['busy_timeout'] >= high_opts['busy_timeout']
    
    def test_postgresql_connection_config(self, config):
        """Test PostgreSQL connection configuration."""
        pg_config = config.get_postgresql_config()
        
        assert isinstance(pg_config, dict)
        assert 'pool_size' in pg_config
        assert 'max_overflow' in pg_config
        assert 'pool_timeout' in pg_config
        assert 'pool_recycle' in pg_config
        assert 'echo' in pg_config
        
        # Check reasonable defaults
        assert pg_config['pool_size'] >= 10
        assert pg_config['max_overflow'] >= 20
        assert pg_config['pool_timeout'] >= 30
    
    def test_apply_sqlite_optimizations_to_engine(self, config):
        """Test applying SQLite optimizations to an engine."""
        # Create a temporary SQLite database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create engine
            engine = create_engine(
                f"sqlite:///{db_path}",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
            
            # Apply optimizations
            config.apply_sqlite_optimizations(engine, OptimizationLevel.HIGH)
            
            # Test that pragmas are applied correctly
            with engine.connect() as conn:
                # Check some key pragmas
                result = conn.execute(text("PRAGMA journal_mode")).fetchone()
                assert result[0].upper() == 'WAL'
                
                result = conn.execute(text("PRAGMA foreign_keys")).fetchone()
                assert result[0] == 1  # ON
                
                result = conn.execute(text("PRAGMA synchronous")).fetchone()
                assert result[0] in [1, 2]  # NORMAL or FULL
        
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_create_optimized_sqlite_engine(self, config):
        """Test creating optimized SQLite engine."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            engine = config.create_optimized_sqlite_engine(
                f"sqlite:///{db_path}",
                optimization_level=OptimizationLevel.HIGH
            )
            
            assert engine is not None
            
            # Test connection and pragmas
            with engine.connect() as conn:
                # Verify optimizations are applied
                result = conn.execute(text("PRAGMA journal_mode")).fetchone()
                assert result[0].upper() == 'WAL'
                
                result = conn.execute(text("PRAGMA cache_size")).fetchone()
                assert result[0] == -65536  # 64MB cache
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_create_postgresql_engine_config(self, config):
        """Test creating PostgreSQL engine configuration."""
        db_url = "postgresql://user:password@localhost/testdb"
        
        engine_config = config.create_postgresql_engine_config(
            db_url,
            pool_config=ConnectionPoolConfig(
                pool_size=15,
                max_overflow=25,
                pool_timeout=45
            )
        )
        
        assert engine_config['url'] == db_url
        assert engine_config['pool_size'] == 15
        assert engine_config['max_overflow'] == 25
        assert engine_config['pool_timeout'] == 45
        assert 'echo' in engine_config
        assert 'future' in engine_config
    
    def test_get_migration_recommendations(self, config):
        """Test migration recommendations."""
        recommendations = config.get_migration_recommendations()
        
        assert isinstance(recommendations, dict)
        assert 'timeline' in recommendations
        assert 'benefits' in recommendations
        assert 'risks' in recommendations
        assert 'steps' in recommendations
        
        # Check that recommendations contain useful information
        assert isinstance(recommendations['timeline'], str)
        assert isinstance(recommendations['benefits'], list)
        assert len(recommendations['benefits']) > 0
        assert isinstance(recommendations['steps'], list)
        assert len(recommendations['steps']) > 0
    
    def test_validate_configuration(self, config):
        """Test configuration validation."""
        # Test valid SQLite optimization
        is_valid, message = config.validate_configuration(
            db_type="sqlite",
            optimization_level=OptimizationLevel.HIGH
        )
        assert is_valid is True
        assert message == ""
        
        # Test valid PostgreSQL configuration
        is_valid, message = config.validate_configuration(
            db_type="postgresql",
            pool_config=ConnectionPoolConfig(pool_size=10)
        )
        assert is_valid is True
        assert message == ""
    
    def test_performance_comparison(self, config):
        """Test performance comparison between configurations."""
        comparison = config.get_performance_comparison()
        
        assert isinstance(comparison, dict)
        assert 'sqlite_optimized' in comparison
        assert 'postgresql' in comparison
        
        sqlite_perf = comparison['sqlite_optimized']
        pg_perf = comparison['postgresql']
        
        # Both should have performance metrics
        assert 'concurrent_users' in sqlite_perf
        assert 'ops_per_second' in sqlite_perf
        assert 'concurrent_users' in pg_perf
        assert 'ops_per_second' in pg_perf
        
        # PostgreSQL should show better concurrency
        assert pg_perf['concurrent_users'] > sqlite_perf['concurrent_users']


class TestOptimizationLevel:
    """Test OptimizationLevel enum."""
    
    def test_optimization_level_values(self):
        """Test optimization level enum values."""
        assert OptimizationLevel.BASIC.value == "basic"
        assert OptimizationLevel.HIGH.value == "high"
        assert OptimizationLevel.MAXIMUM.value == "maximum"
    
    def test_optimization_level_ordering(self):
        """Test optimization levels can be compared."""
        levels = [OptimizationLevel.BASIC, OptimizationLevel.HIGH, OptimizationLevel.MAXIMUM]
        
        # Test that all levels are unique
        assert len(set(levels)) == 3


class TestDatabaseConfigurationIntegration:
    """Integration tests for database configuration."""
    
    def test_sqlite_optimization_workflow(self):
        """Test complete SQLite optimization workflow."""
        config = DatabaseConfiguration()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create and optimize engine
            engine = config.create_optimized_sqlite_engine(
                f"sqlite:///{db_path}",
                optimization_level=OptimizationLevel.HIGH
            )
            
            # Validate configuration
            is_valid, message = config.validate_configuration(
                db_type="sqlite",
                optimization_level=OptimizationLevel.HIGH
            )
            assert is_valid is True
            
            # Test basic operations
            with engine.connect() as conn:
                # Create a test table
                conn.execute(text("""
                    CREATE TABLE test_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                """))
                conn.commit()
                
                # Insert test data
                conn.execute(text("""
                    INSERT INTO test_table (name) VALUES ('test')
                """))
                conn.commit()
                
                # Query test data
                result = conn.execute(text("""
                    SELECT name FROM test_table WHERE id = 1
                """)).fetchone()
                assert result[0] == 'test'
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_configuration_comparison_workflow(self):
        """Test configuration comparison and recommendation workflow."""
        config = DatabaseConfiguration()
        
        # Get performance comparison
        comparison = config.get_performance_comparison()
        assert isinstance(comparison, dict)
        
        # Get migration recommendations
        recommendations = config.get_migration_recommendations()
        assert isinstance(recommendations, dict)
        
        # Validate that recommendations are actionable
        assert len(recommendations['steps']) > 0
        assert 'PostgreSQL' in str(recommendations)
    
    @pytest.mark.parametrize("optimization_level", [
        OptimizationLevel.BASIC,
        OptimizationLevel.HIGH,
        OptimizationLevel.MAXIMUM
    ])
    def test_optimization_levels_sqlite(self, optimization_level):
        """Test all optimization levels work with SQLite."""
        config = DatabaseConfiguration()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            engine = config.create_optimized_sqlite_engine(
                f"sqlite:///{db_path}",
                optimization_level=optimization_level
            )
            
            # Test that engine works
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                assert result[0] == 1
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)