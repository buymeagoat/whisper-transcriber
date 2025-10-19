"""
Database locking utilities for the Whisper Transcriber API.
"""

import threading
from contextlib import contextmanager
from api.utils.logger import get_system_logger

logger = get_system_logger("db_lock")

class DatabaseLock:
    """Simple database lock for preventing concurrent operations."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._locked_by = None
    
    @contextmanager
    def acquire(self, operation: str = "unknown"):
        """Acquire the database lock."""
        thread_id = threading.current_thread().ident
        
        logger.debug(f"Thread {thread_id} requesting lock for: {operation}")
        
        acquired = self._lock.acquire(timeout=30)  # 30 second timeout
        
        if not acquired:
            logger.error(f"Thread {thread_id} failed to acquire lock for: {operation}")
            raise TimeoutError(f"Failed to acquire database lock for: {operation}")
        
        try:
            self._locked_by = (thread_id, operation)
            logger.debug(f"Thread {thread_id} acquired lock for: {operation}")
            yield
        finally:
            self._locked_by = None
            self._lock.release()
            logger.debug(f"Thread {thread_id} released lock for: {operation}")

# Global database lock instance
db_lock = DatabaseLock()
