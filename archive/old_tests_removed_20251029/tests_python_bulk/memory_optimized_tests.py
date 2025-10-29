"""
Memory-Optimized Performance Testing Framework
Addresses memory leak issues identified in the application testing.
"""

import tracemalloc
import gc
import psutil
import time
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import tempfile
import os
import numpy as np
import requests
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """Enhanced memory management for performance testing"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = None
        self.snapshots = []
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get current memory usage in MB"""
        mem = self.process.memory_info()
        return {
            'rss_mb': mem.rss / 1024 / 1024,
            'vms_mb': mem.vms / 1024 / 1024,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def set_baseline(self):
        """Set memory baseline for comparison"""
        gc.collect()  # Force cleanup before baseline
        time.sleep(0.1)  # Allow cleanup to complete
        self.baseline_memory = self.get_memory_info()
        logger.info(f"Memory baseline set: {self.baseline_memory['rss_mb']:.1f} MB")
    
    def get_growth_since_baseline(self) -> float:
        """Get memory growth since baseline"""
        if not self.baseline_memory:
            return 0.0
        current = self.get_memory_info()
        return current['rss_mb'] - self.baseline_memory['rss_mb']
    
    def force_cleanup(self) -> int:
        """Force garbage collection and return collected count"""
        collected = 0
        for _ in range(3):  # Multiple passes
            collected += gc.collect()
        return collected

@contextmanager
def memory_tracked_operation(memory_manager: MemoryManager, operation_name: str):
    """Context manager for tracking memory usage during operations"""
    start_mem = memory_manager.get_memory_info()
    start_time = time.time()
    
    try:
        yield
    finally:
        # Force cleanup
        collected = memory_manager.force_cleanup()
        time.sleep(0.1)  # Allow cleanup to complete
        
        end_mem = memory_manager.get_memory_info()
        end_time = time.time()
        
        growth = end_mem['rss_mb'] - start_mem['rss_mb']
        duration = end_time - start_time
        
        logger.info(f"{operation_name}: {growth:+.1f} MB in {duration:.1f}s, GC collected {collected}")

class OptimizedAudioGenerator:
    """Memory-optimized audio file generation"""
    
    @staticmethod
    def generate_optimized_audio(duration_minutes: float, filename: str, 
                               sample_rate: int = 22050) -> Path:
        """Generate audio with memory optimization"""
        
        # Use lower sample rate to reduce memory usage
        duration_seconds = duration_minutes * 60
        num_samples = int(duration_seconds * sample_rate)
        
        # Generate audio in chunks to reduce peak memory usage
        chunk_size = sample_rate * 30  # 30 seconds per chunk
        output_path = Path(f"tests/performance/test_files/{filename}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            # Write WAV header
            f.write(b'RIFF')
            f.write((36 + num_samples * 2).to_bytes(4, 'little'))
            f.write(b'WAVEfmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # PCM
            f.write((1).to_bytes(2, 'little'))  # Mono
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((num_samples * 2).to_bytes(4, 'little'))
            
            # Write audio data in chunks
            samples_written = 0
            while samples_written < num_samples:
                current_chunk_size = min(chunk_size, num_samples - samples_written)
                
                # Generate chunk
                chunk_data = np.random.uniform(-0.5, 0.5, current_chunk_size).astype(np.float32)
                chunk_bytes = (chunk_data * 32767).astype(np.int16).tobytes()
                
                f.write(chunk_bytes)
                samples_written += current_chunk_size
                
                # Clean up chunk immediately
                del chunk_data
                del chunk_bytes
                
                # Force garbage collection every 10 chunks
                if samples_written % (chunk_size * 10) == 0:
                    gc.collect()
        
        return output_path

class MemoryOptimizedPerformanceTests:
    """Memory-optimized performance testing suite"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.memory_manager = MemoryManager()
        self.audio_generator = OptimizedAudioGenerator()
        self.test_files = []
    
    def setup_memory_tracking(self):
        """Initialize memory tracking"""
        tracemalloc.start()
        self.memory_manager.set_baseline()
    
    def cleanup_test_files(self):
        """Clean up all generated test files"""
        for file_path in self.test_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
        self.test_files.clear()
    
    def test_memory_controlled_upload(self) -> Dict[str, Any]:
        """Test file upload with strict memory control"""
        
        with memory_tracked_operation(self.memory_manager, "Memory Controlled Upload"):
            # Generate small test file
            test_file = self.audio_generator.generate_optimized_audio(
                duration_minutes=1.0,  # 1 minute file
                filename="memory_test.wav"
            )
            self.test_files.append(test_file)
            
            # Test upload with memory monitoring
            try:
                with open(test_file, 'rb') as f:
                    files = {"file": (test_file.name, f, "audio/wav")}
                    response = requests.post(
                        f"{self.api_base}/jobs/",
                        files=files,
                        timeout=30
                    )
                
                return {
                    "status_code": response.status_code,
                    "file_size_mb": test_file.stat().st_size / 1024 / 1024,
                    "memory_growth_mb": self.memory_manager.get_growth_since_baseline(),
                    "success": response.status_code in [200, 201]
                }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "memory_growth_mb": self.memory_manager.get_growth_since_baseline(),
                    "success": False
                }
    
    def run_memory_leak_detection(self, iterations: int = 5) -> Dict[str, Any]:
        """Run memory leak detection with optimized cleanup"""
        
        results = []
        memory_samples = []
        
        print(f"🧠 Starting memory leak detection ({iterations} iterations)")
        
        for i in range(iterations):
            print(f"📊 Iteration {i+1}/{iterations}")
            
            # Memory before iteration
            mem_before = self.memory_manager.get_memory_info()
            
            # Run test iteration
            result = self.test_memory_controlled_upload()
            
            # Aggressive cleanup
            collected = self.memory_manager.force_cleanup()
            time.sleep(0.2)  # Allow cleanup to complete
            
            # Memory after iteration
            mem_after = self.memory_manager.get_memory_info()
            
            iteration_growth = mem_after['rss_mb'] - mem_before['rss_mb']
            
            memory_samples.append({
                'iteration': i + 1,
                'memory_before': mem_before['rss_mb'],
                'memory_after': mem_after['rss_mb'],
                'growth': iteration_growth,
                'gc_collected': collected
            })
            
            results.append(result)
            
            print(f"  Memory: {mem_before['rss_mb']:.1f} → {mem_after['rss_mb']:.1f} MB ({iteration_growth:+.1f} MB)")
            print(f"  GC collected: {collected} objects")
        
        # Cleanup all test files
        self.cleanup_test_files()
        
        # Final aggressive cleanup
        final_collected = self.memory_manager.force_cleanup()
        final_memory = self.memory_manager.get_memory_info()
        
        # Calculate statistics
        total_growth = final_memory['rss_mb'] - self.memory_manager.baseline_memory['rss_mb']
        avg_growth_per_iteration = sum(s['growth'] for s in memory_samples) / len(memory_samples)
        
        return {
            "iterations": iterations,
            "total_memory_growth_mb": total_growth,
            "avg_growth_per_iteration_mb": avg_growth_per_iteration,
            "memory_samples": memory_samples,
            "final_gc_collected": final_collected,
            "memory_leak_detected": total_growth > (iterations * 2),  # 2MB threshold per iteration
            "results": results
        }

# Main testing function
def run_memory_optimized_tests():
    """Run the memory-optimized performance tests"""
    
    print("🚀 MEMORY-OPTIMIZED PERFORMANCE TESTING")
    print("=" * 50)
    
    # Initialize test suite
    test_suite = MemoryOptimizedPerformanceTests()
    test_suite.setup_memory_tracking()
    
    # Run memory leak detection
    leak_results = test_suite.run_memory_leak_detection(iterations=5)
    
    # Report results
    print("\n📊 MEMORY LEAK DETECTION RESULTS:")
    print("=" * 50)
    print(f"Total memory growth: {leak_results['total_memory_growth_mb']:+.1f} MB")
    print(f"Average per iteration: {leak_results['avg_growth_per_iteration_mb']:+.1f} MB")
    print(f"Memory leak detected: {'❌ YES' if leak_results['memory_leak_detected'] else '✅ NO'}")
    
    return leak_results

if __name__ == "__main__":
    results = run_memory_optimized_tests()