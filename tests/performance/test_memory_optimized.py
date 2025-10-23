#!/usr/bin/env python3
"""
Memory-Optimized Performance Testing Suite

Enhanced performance testing with comprehensive memory leak prevention
and monitoring for the Whisper Transcriber application.
"""

import os
import sys
import time
import uuid
import json
import tempfile
import threading
import tracemalloc
import gc
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

import requests
import psutil
import numpy as np
import wave

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from api.utils.memory_manager import memory_manager, safe_large_operation, optimize_numpy_memory

class MemoryOptimizedPerformanceTestSuite:
    """Memory-optimized performance test suite with leak prevention."""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        """Initialize the enhanced performance test suite."""
        self.api_base = api_base
        self.test_files_dir = Path(__file__).parent / "test_files"
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Initialize memory management
        optimize_numpy_memory()
        
        # Configure requests session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MemoryOptimizedPerformanceTestSuite/1.0'
        })
        
        print(f"🚀 Memory-Optimized Performance Test Suite initialized")
        print(f"📍 API Base: {self.api_base}")
        print(f"💾 Initial memory usage: {memory_manager.get_memory_usage():.1f} MB")
    
    def generate_optimized_audio_file(self, duration_minutes: float, filename: str) -> Path:
        """Generate test audio file with chunked processing to minimize memory usage."""
        with safe_large_operation(f"generate_audio_{duration_minutes}min"):
            duration_seconds = duration_minutes * 60
            sample_rate = 44100
            num_samples = int(duration_seconds * sample_rate)
            
            print(f"🎵 Generating {duration_minutes}-minute audio file: {filename}")
            
            file_path = self.test_files_dir / filename
            
            # Process audio in 10-second chunks to minimize memory usage
            chunk_duration = 10  # seconds
            chunk_samples = sample_rate * chunk_duration
            
            with wave.open(str(file_path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                samples_written = 0
                while samples_written < num_samples:
                    # Calculate chunk size
                    remaining_samples = num_samples - samples_written
                    current_chunk_samples = min(chunk_samples, remaining_samples)
                    
                    # Generate time array for this chunk
                    t_start = samples_written / sample_rate
                    t_end = (samples_written + current_chunk_samples) / sample_rate
                    t = np.linspace(t_start, t_end, current_chunk_samples, dtype=np.float32)
                    
                    # Generate audio signal
                    audio_chunk = np.sin(2 * np.pi * 440 * t)
                    
                    # Convert to int16 and write
                    audio_int16 = (audio_chunk * 32767).astype(np.int16)
                    wav_file.writeframes(audio_int16.tobytes())
                    
                    samples_written += current_chunk_samples
                    
                    # Explicitly delete chunk data to free memory immediately
                    del t, audio_chunk, audio_int16
                    
                    # Force garbage collection every 50 seconds of audio
                    if samples_written % (sample_rate * 50) == 0:
                        gc.collect()
            
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ Generated {file_path.name} ({file_size_mb:.1f} MB)")
            
            return file_path
    
    def test_memory_leak_with_monitoring(self, iterations: int = 10) -> Dict[str, Any]:
        """Enhanced memory leak detection with comprehensive monitoring."""
        print(f"🔬 Enhanced memory leak detection over {iterations} iterations")
        
        # Start comprehensive memory tracking
        tracemalloc.start(25)  # Track 25 stack frames
        initial_snapshot = tracemalloc.take_snapshot()
        initial_memory = memory_manager.get_memory_usage()
        
        memory_snapshots = []
        operation_times = []
        gc_stats = []
        
        print(f"📊 Initial memory: {initial_memory:.1f} MB")
        
        for i in range(iterations):
            iteration_start = time.time()
            
            with memory_manager.memory_context(f"leak_test_iteration_{i+1}"):
                print(f"🧪 Iteration {i+1}/{iterations}")
                
                try:
                    # Generate small test file (30 seconds)
                    test_file = self.generate_optimized_audio_file(0.5, f"leak_test_{i}.wav")
                    
                    # Simulate file upload
                    with open(test_file, 'rb') as f:
                        try:
                            response = self.session.post(
                                f"{self.api_base}/jobs/",
                                files={"file": (test_file.name, f, "audio/wav")},
                                timeout=30
                            )
                            success = response.status_code in [200, 201, 202]
                        except Exception as e:
                            success = False
                            print(f"   ⚠️ Upload failed: {e}")
                    
                    # Clean up file immediately
                    test_file.unlink(missing_ok=True)
                    
                    # Record memory and performance metrics
                    current_memory = memory_manager.get_memory_usage()
                    iteration_time = time.time() - iteration_start
                    
                    # Get garbage collection stats
                    gc_info = gc.get_stats()
                    
                    snapshot = {
                        "iteration": i + 1,
                        "memory_mb": current_memory,
                        "growth_mb": current_memory - initial_memory,
                        "iteration_time_seconds": iteration_time,
                        "upload_success": success,
                        "gc_collections": sum(stat['collections'] for stat in gc_info)
                    }
                    
                    memory_snapshots.append(snapshot)
                    operation_times.append(iteration_time)
                    gc_stats.append(gc_info)
                    
                    print(f"   📊 Memory: {current_memory:.1f} MB ({current_memory - initial_memory:+.1f} MB)")
                    
                    # Aggressive cleanup every 3 iterations
                    if (i + 1) % 3 == 0:
                        print(f"   🧹 Forcing cleanup after iteration {i+1}")
                        memory_manager.force_cleanup()
                        gc.collect()
                
                except Exception as e:
                    print(f"   ❌ Iteration {i+1} failed: {e}")
                    current_memory = memory_manager.get_memory_usage()
                    memory_snapshots.append({
                        "iteration": i + 1,
                        "memory_mb": current_memory,
                        "growth_mb": current_memory - initial_memory,
                        "error": str(e)
                    })
        
        # Final analysis
        final_memory = memory_manager.get_memory_usage()
        total_growth = final_memory - initial_memory
        
        # Take final snapshot for detailed analysis
        final_snapshot = tracemalloc.take_snapshot()
        
        # Analyze growth pattern
        memory_values = [s["memory_mb"] for s in memory_snapshots if "memory_mb" in s]
        peak_memory = max(memory_values) if memory_values else final_memory
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else final_memory
        
        # Detect memory leak based on total growth and trend
        growth_per_iteration = total_growth / iterations
        leak_threshold = 2.0  # 2MB per iteration
        leak_detected = growth_per_iteration > leak_threshold
        
        # Calculate performance metrics
        avg_iteration_time = sum(operation_times) / len(operation_times) if operation_times else 0
        
        result = {
            "test_type": "enhanced_memory_leak_detection",
            "iterations": iterations,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "total_growth_mb": total_growth,
            "growth_per_iteration_mb": growth_per_iteration,
            "peak_memory_mb": peak_memory,
            "avg_memory_mb": avg_memory,
            "leak_detected": leak_detected,
            "leak_severity": "high" if growth_per_iteration > 5 else "medium" if growth_per_iteration > 1 else "low",
            "avg_iteration_time_seconds": avg_iteration_time,
            "memory_snapshots": memory_snapshots,
            "tracemalloc_traces": {
                "initial": len(initial_snapshot.traces),
                "final": len(final_snapshot.traces),
                "trace_growth": len(final_snapshot.traces) - len(initial_snapshot.traces)
            },
            "gc_summary": {
                "initial": gc_stats[0] if gc_stats else {},
                "final": gc_stats[-1] if gc_stats else {}
            }
        }
        
        # Print summary
        print(f"\n📊 MEMORY LEAK ANALYSIS RESULTS:")
        print(f"   💾 Total growth: {total_growth:.1f} MB")
        print(f"   📈 Growth per iteration: {growth_per_iteration:.1f} MB")
        print(f"   🎯 Leak detected: {'YES' if leak_detected else 'NO'}")
        print(f"   ⚡ Avg iteration time: {avg_iteration_time:.1f}s")
        
        if leak_detected:
            print(f"   🚨 MEMORY LEAK SEVERITY: {result['leak_severity'].upper()}")
        else:
            print(f"   ✅ Memory usage appears stable")
        
        return result
    
    def run_comprehensive_memory_tests(self) -> Dict[str, Any]:
        """Run comprehensive memory testing suite."""
        print(f"\n🏁 Starting Comprehensive Memory Testing Suite")
        print("=" * 60)
        
        results = {
            "test_start_time": time.time(),
            "initial_memory_mb": memory_manager.get_memory_usage(),
            "tests": {}
        }
        
        # Test 1: Memory leak detection
        print(f"\n🧪 TEST 1: Enhanced Memory Leak Detection")
        print("-" * 40)
        results["tests"]["memory_leak"] = self.test_memory_leak_with_monitoring(iterations=15)
        
        # Force cleanup between tests
        memory_manager.force_cleanup()
        gc.collect()
        
        # Test 2: Multiple small operations
        print(f"\n🧪 TEST 2: Multiple Small Operations")
        print("-" * 40)
        small_ops_result = self.test_multiple_small_operations(50)
        results["tests"]["small_operations"] = small_ops_result
        
        # Final memory report
        final_memory = memory_manager.get_memory_usage()
        results["final_memory_mb"] = final_memory
        results["total_suite_growth_mb"] = final_memory - results["initial_memory_mb"]
        results["memory_report"] = memory_manager.get_memory_report()
        
        print(f"\n🏆 COMPREHENSIVE MEMORY TEST SUITE COMPLETED")
        print("=" * 60)
        print(f"📊 Initial memory: {results['initial_memory_mb']:.1f} MB")
        print(f"📊 Final memory: {final_memory:.1f} MB")
        print(f"📈 Total suite growth: {results['total_suite_growth_mb']:.1f} MB")
        
        # Generate recommendations
        recommendations = self.generate_memory_recommendations(results)
        results["recommendations"] = recommendations
        
        return results
    
    def test_multiple_small_operations(self, count: int) -> Dict[str, Any]:
        """Test many small operations to detect cumulative memory issues."""
        print(f"🔄 Testing {count} small operations")
        
        initial_memory = memory_manager.get_memory_usage()
        operation_memories = []
        
        for i in range(count):
            if i % 10 == 0:
                print(f"   Operation {i}/{count}")
            
            # Small operation: generate tiny audio snippet
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    # Generate 1 second of audio
                    sample_rate = 44100
                    t = np.linspace(0, 1, sample_rate, dtype=np.float32)
                    audio = np.sin(2 * np.pi * 440 * t)
                    
                    with wave.open(tmp.name, 'w') as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(sample_rate)
                        audio_int16 = (audio * 32767).astype(np.int16)
                        wav.writeframes(audio_int16.tobytes())
                    
                    # Clean up immediately
                    os.unlink(tmp.name)
                    del t, audio, audio_int16
                
                # Record memory every 10 operations
                if i % 10 == 0:
                    current_memory = memory_manager.get_memory_usage()
                    operation_memories.append({
                        "operation": i,
                        "memory_mb": current_memory,
                        "growth_mb": current_memory - initial_memory
                    })
                
                # Force GC every 25 operations
                if i % 25 == 0:
                    gc.collect()
                    
            except Exception as e:
                print(f"   ❌ Operation {i} failed: {e}")
        
        final_memory = memory_manager.get_memory_usage()
        total_growth = final_memory - initial_memory
        
        return {
            "operation_count": count,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "total_growth_mb": total_growth,
            "growth_per_operation_mb": total_growth / count,
            "memory_snapshots": operation_memories
        }
    
    def generate_memory_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate memory optimization recommendations based on test results."""
        recommendations = []
        
        total_growth = test_results.get("total_suite_growth_mb", 0)
        leak_detected = test_results.get("tests", {}).get("memory_leak", {}).get("leak_detected", False)
        
        if total_growth > 50:
            recommendations.append("CRITICAL: Total memory growth exceeds 50MB - investigate major memory leaks")
        
        if leak_detected:
            leak_severity = test_results.get("tests", {}).get("memory_leak", {}).get("leak_severity", "unknown")
            recommendations.append(f"Memory leak detected with {leak_severity} severity - implement additional cleanup")
        
        if total_growth > 20:
            recommendations.append("Consider implementing more aggressive garbage collection")
            recommendations.append("Review NumPy array usage and ensure proper deletion")
            recommendations.append("Add explicit memory cleanup in file processing operations")
        
        small_ops = test_results.get("tests", {}).get("small_operations", {})
        if small_ops.get("growth_per_operation_mb", 0) > 0.1:
            recommendations.append("Small operations showing memory accumulation - review cleanup logic")
        
        if not recommendations:
            recommendations.append("Memory usage appears optimal - no immediate action required")
        
        return recommendations
    
    def cleanup(self):
        """Clean up test resources."""
        # Close session
        self.session.close()
        
        # Clean up test files
        if self.test_files_dir.exists():
            for file_path in self.test_files_dir.glob("*.wav"):
                try:
                    file_path.unlink()
                except:
                    pass
        
        # Force final cleanup
        memory_manager.force_cleanup()
        
        print("🧹 Test suite cleanup completed")


def main():
    """Run the memory-optimized performance test suite."""
    print("🚀 Starting Memory-Optimized Performance Testing")
    print("=" * 60)
    
    # Initialize test suite
    test_suite = MemoryOptimizedPerformanceTestSuite()
    
    try:
        # Run comprehensive tests
        results = test_suite.run_comprehensive_memory_tests()
        
        # Save results
        results_file = Path("tests/reports/memory_optimization_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {results_file}")
        
        # Print recommendations
        if "recommendations" in results:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        return results
        
    finally:
        test_suite.cleanup()


if __name__ == "__main__":
    main()