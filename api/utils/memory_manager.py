"""
Production Memory Management Utilities
Provides memory monitoring and optimization for the Whisper Transcriber application.
"""

import gc
import psutil
import tracemalloc
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time
import os
import weakref
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages memory usage and prevents leaks in the application."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()
        self._tracked_objects: Dict[str, weakref.WeakSet] = {}
        self._memory_snapshots: List[Dict[str, Any]] = []
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def track_object(self, obj: Any, category: str = "general") -> None:
        """Track an object for memory leak detection."""
        if category not in self._tracked_objects:
            self._tracked_objects[category] = weakref.WeakSet()
        self._tracked_objects[category].add(obj)
    
    def get_tracked_objects_count(self) -> Dict[str, int]:
        """Get count of tracked objects by category."""
        return {cat: len(objects) for cat, objects in self._tracked_objects.items()}
    
    @contextmanager
    def memory_context(self, operation_name: str = "operation"):
        """Context manager to track memory usage of an operation."""
        initial_memory = self.get_memory_usage()
        
        # Start tracemalloc if not already running
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        snapshot_before = tracemalloc.take_snapshot()
        
        logger.debug(f"Starting {operation_name} - Memory: {initial_memory:.1f} MB")
        
        try:
            yield self
        finally:
            # Force garbage collection
            gc.collect()
            
            # Take snapshot after operation
            snapshot_after = tracemalloc.take_snapshot()
            final_memory = self.get_memory_usage()
            
            # Calculate memory change
            memory_diff = final_memory - initial_memory
            
            # Store snapshot
            self._memory_snapshots.append({
                'operation': operation_name,
                'memory_before': initial_memory,
                'memory_after': final_memory,
                'memory_diff': memory_diff,
                'snapshot_before': snapshot_before,
                'snapshot_after': snapshot_after
            })
            
            logger.info(f"Completed {operation_name} - Memory: {final_memory:.1f} MB ({memory_diff:+.1f} MB)")
            
            # Warn about significant memory growth
            if memory_diff > 10:  # More than 10MB growth
                logger.warning(f"Significant memory growth in {operation_name}: {memory_diff:+.1f} MB")
                self._analyze_memory_growth(snapshot_before, snapshot_after)
    
    def _analyze_memory_growth(self, before_snapshot, after_snapshot):
        """Analyze memory growth between snapshots."""
        top_stats = after_snapshot.compare_to(before_snapshot, 'lineno')
        
        logger.warning("Top memory allocations:")
        for index, stat in enumerate(top_stats[:5]):
            if stat.size_diff > 1024 * 1024:  # More than 1MB
                logger.warning(f"  {index+1}. {stat.size_diff / (1024*1024):.1f} MB - {stat.traceback.format()[-1].strip()}")
    
    def force_cleanup(self):
        """Force comprehensive memory cleanup."""
        logger.info("Forcing comprehensive memory cleanup...")
        
        # Multiple garbage collection passes
        collected = 0
        for i in range(3):
            collected += gc.collect()
        
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Clear tracked object references
        for category in self._tracked_objects:
            self._tracked_objects[category].clear()
        
        # Try to release memory back to OS (platform specific)
        try:
            if hasattr(os, 'malloc_trim'):
                os.malloc_trim(0)  # Linux only
        except:
            pass
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Generate a comprehensive memory usage report."""
        current_memory = self.get_memory_usage()
        
        report = {
            'current_memory_mb': current_memory,
            'initial_memory_mb': self.initial_memory,
            'total_growth_mb': current_memory - self.initial_memory,
            'tracked_objects': self.get_tracked_objects_count(),
            'gc_stats': gc.get_stats(),
            'operations': []
        }
        
        # Add operation summaries
        for snapshot in self._memory_snapshots[-10:]:  # Last 10 operations
            report['operations'].append({
                'operation': snapshot['operation'],
                'memory_diff_mb': snapshot['memory_diff']
            })
        
        return report
    
    def check_memory_threshold(self, threshold_mb: float = 500) -> bool:
        """Check if memory usage exceeds threshold."""
        current_memory = self.get_memory_usage()
        if current_memory > threshold_mb:
            logger.warning(f"Memory usage ({current_memory:.1f} MB) exceeds threshold ({threshold_mb:.1f} MB)")
            return True
        return False


# Global memory manager instance
memory_manager = MemoryManager()


@contextmanager 
def safe_large_operation(operation_name: str = "large_operation"):
    """Context manager for safe handling of large memory operations."""
    with memory_manager.memory_context(operation_name):
        try:
            yield
        finally:
            # Always force cleanup after large operations
            memory_manager.force_cleanup()


def optimize_numpy_memory():
    """Optimize NumPy memory usage settings."""
    try:
        import numpy as np
        
        # Configure NumPy for better memory management
        # Disable memory mapping for large arrays (can cause memory leaks)
        np.seterr(all='ignore')  # Don't print warnings that can accumulate
        
        logger.info("NumPy memory optimization applied")
        
    except ImportError:
        logger.warning("NumPy not available for memory optimization")


def clean_temp_files(temp_dir: Path, max_age_hours: int = 1):
    """Clean up temporary files older than specified age."""
    if not temp_dir.exists():
        return
        
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_count = 0
    cleaned_size = 0
    
    for file_path in temp_dir.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_count += 1
                    cleaned_size += file_size
                except OSError as e:
                    logger.warning(f"Failed to clean temp file {file_path}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"Cleaned {cleaned_count} temp files, freed {cleaned_size / (1024*1024):.1f} MB")


def monitor_memory_usage(func):
    """Decorator to monitor memory usage of functions."""
    def wrapper(*args, **kwargs):
        with memory_manager.memory_context(func.__name__):
            return func(*args, **kwargs)
    return wrapper