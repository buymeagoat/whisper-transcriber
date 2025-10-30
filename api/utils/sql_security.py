"""
SQL Security Utilities
Provides secure SQL operation helpers to prevent injection attacks.
"""

import re
from typing import List, Optional

class SQLSecurityError(Exception):
    """Raised when a potential SQL injection is detected."""
    pass

def validate_table_name(table_name: str, allowed_tables: List[str]) -> str:
    """
    Validate a table name against a whitelist of allowed tables.
    
    Args:
        table_name: The table name to validate
        allowed_tables: List of allowed table names
        
    Returns:
        The validated table name
        
    Raises:
        SQLSecurityError: If table name is not in the whitelist
    """
    if table_name not in allowed_tables:
        raise SQLSecurityError(f"Table '{table_name}' is not in the allowed list")
    return table_name

def validate_column_name(column_name: str, allowed_columns: List[str]) -> str:
    """
    Validate a column name against a whitelist of allowed columns.
    
    Args:
        column_name: The column name to validate
        allowed_columns: List of allowed column names
        
    Returns:
        The validated column name
        
    Raises:
        SQLSecurityError: If column name is not in the whitelist
    """
    if column_name not in allowed_columns:
        raise SQLSecurityError(f"Column '{column_name}' is not in the allowed list")
    return column_name

def quote_identifier(identifier: str) -> str:
    """
    Safely quote an SQL identifier (table name, column name, etc.).
    
    Args:
        identifier: The identifier to quote
        
    Returns:
        The quoted identifier
    """
    # Remove any existing quotes and validate the identifier
    clean_identifier = identifier.strip("\"`'")
    
    # Check for valid identifier characters (alphanumeric, underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', clean_identifier):
        raise SQLSecurityError(f"Invalid identifier: {identifier}")
    
    # Return quoted identifier for SQLite
    return f'"{clean_identifier}"'

def build_safe_query(base_query: str, table_name: str, allowed_tables: List[str]) -> str:
    """
    Build a safe SQL query by validating the table name.
    
    Args:
        base_query: Base query template with {table} placeholder
        table_name: Table name to insert
        allowed_tables: List of allowed table names
        
    Returns:
        The safe SQL query
        
    Raises:
        SQLSecurityError: If table name validation fails
    """
    validated_table = validate_table_name(table_name, allowed_tables)
    quoted_table = quote_identifier(validated_table)
    return base_query.format(table=quoted_table)

# Common allowed tables for the whisper-transcriber application
ALLOWED_TABLES = [
    "users", "jobs", "metadata", "config", "audit_log", 
    "query_performance_log", "user_settings"
]

# Common allowed columns for filtering/sorting operations
ALLOWED_COLUMNS = [
    "id", "username", "email", "created_at", "updated_at", "status",
    "filename", "transcript_path", "audio_path", "job_id", "user_id",
    "key", "value", "timestamp", "action", "table_name", "execution_time_ms"
]
