#!/usr/bin/env python3
"""
Comprehensive Performance Testing Suite
Tests large file handling, memory usage, and processing limits
"""

import asyncio
import time
import psutil
import tracemalloc
import requests
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import wave
import numpy as np

class PerformanceTestSuite:
    """Comprehensive performance testing for Whisper Transcriber."""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        """Initialize the performance test suite."""
        self.api_base = api_base
        self.results = {}
        self.test_files_dir = Path("tests/performance/test_files")
        self.test_files_dir.mkdir(exist_ok=True)
        
    def generate_test_audio_file(self, duration_minutes: int, filename: str) -> Path:
        """Generate a test audio file of specified duration."""
        print(f"🎵 Generating {duration_minutes}-minute test audio file: {filename}")
        
        # Audio parameters
        sample_rate = 44100
        duration_seconds = duration_minutes * 60
        num_samples = int(sample_rate * duration_seconds)  # Convert to int for np.linspace
        
        # Generate sine wave audio data (simulates speech patterns)
        frequency = 440  # A4 note
        t = np.linspace(0, duration_seconds, num_samples, dtype=np.float32)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Add some variation to simulate speech
        variation = np.random.normal(0, 0.1, num_samples).astype(np.float32)
        audio_data += variation
        
        # Convert to 16-bit PCM
        audio_data_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        file_path = self.test_files_dir / filename
        with wave.open(str(file_path), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data_int16.tobytes())
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"✅ Generated {file_path} ({file_size_mb:.1f} MB)")
        return file_path
    
    def monitor_memory_usage(self, duration_seconds: int) -> Dict[str, Any]:
        """Monitor memory usage during a test."""
        print(f"📊 Monitoring memory usage for {duration_seconds} seconds")
        
        memory_snapshots = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_snapshots.append({
                "timestamp": time.time() - start_time,
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "cpu_percent": process.cpu_percent()
            })
            time.sleep(1)
        
        # Calculate memory statistics
        rss_values = [snap["rss_mb"] for snap in memory_snapshots]
        cpu_values = [snap["cpu_percent"] for snap in memory_snapshots]
        
        return {
            "snapshots": memory_snapshots,
            "memory_stats": {
                "peak_rss_mb": max(rss_values),
                "avg_rss_mb": sum(rss_values) / len(rss_values),
                "memory_growth_mb": rss_values[-1] - rss_values[0],
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values) if cpu_values else 0
            }
        }
    
    def test_large_file_upload(self, file_path: Path) -> Dict[str, Any]:
        """Test uploading and processing a large audio file."""
        print(f"📤 Testing large file upload: {file_path.name}")
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        start_time = time.time()
        
        try:
            # Start memory monitoring in background
            memory_monitor = threading.Thread(
                target=lambda: self.monitor_memory_usage(300),  # 5 minutes max
                daemon=True
            )
            memory_monitor.start()
            
            # Upload file
            with open(file_path, 'rb') as f:
                files = {"file": (file_path.name, f, "audio/wav")}
                response = requests.post(
                    f"{self.api_base}/jobs",
                    files=files,
                    timeout=300  # 5 minutes timeout
                )
            
            upload_time = time.time() - start_time
            
            result = {
                "file_size_mb": file_size_mb,
                "upload_time_seconds": upload_time,
                "upload_speed_mbps": file_size_mb / upload_time if upload_time > 0 else 0,
                "status_code": response.status_code,
                "success": response.status_code in [200, 201, 202],
                "response": response.text[:500] if response.text else ""
            }
            
            if result["success"]:
                print(f"✅ Large file upload successful: {file_size_mb:.1f}MB in {upload_time:.1f}s")
            else:
                print(f"❌ Large file upload failed: {response.status_code} - {response.text[:100]}")
            
            return result
            
        except Exception as e:
            print(f"❌ Large file upload error: {e}")
            return {
                "file_size_mb": file_size_mb,
                "upload_time_seconds": time.time() - start_time,
                "error": str(e),
                "success": False
            }
    
    def test_concurrent_uploads(self, num_concurrent: int, file_size_mb: int = 10) -> Dict[str, Any]:
        """Test concurrent file uploads."""
        print(f"🚀 Testing {num_concurrent} concurrent uploads ({file_size_mb}MB each)")
        
        # Generate test files for concurrent testing
        test_files = []
        for i in range(num_concurrent):
            # Create smaller files for concurrency testing (duration in minutes = size_mb / 10)
            duration_minutes = max(1, file_size_mb // 10)
            file_path = self.generate_test_audio_file(
                duration_minutes, 
                f"concurrent_test_{i}_{file_size_mb}mb.wav"
            )
            test_files.append(file_path)
        
        def upload_file(file_path: Path, thread_id: int) -> Dict[str, Any]:
            """Upload a single file (for threading)."""
            start_time = time.time()
            try:
                with open(file_path, 'rb') as f:
                    files = {"file": (file_path.name, f, "audio/wav")}
                    response = requests.post(
                        f"{self.api_base}/jobs",
                        files=files,
                        timeout=120
                    )
                
                return {
                    "thread_id": thread_id,
                    "file_name": file_path.name,
                    "duration_seconds": time.time() - start_time,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 201, 202],
                    "response_size": len(response.text) if response.text else 0
                }
            except Exception as e:
                return {
                    "thread_id": thread_id,
                    "file_name": file_path.name,
                    "duration_seconds": time.time() - start_time,
                    "error": str(e),
                    "success": False
                }
        
        # Execute concurrent uploads
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            future_to_thread = {
                executor.submit(upload_file, file_path, i): i 
                for i, file_path in enumerate(test_files)
            }
            
            for future in as_completed(future_to_thread):
                thread_id = future_to_thread[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        print(f"✅ Thread {thread_id}: Upload successful in {result['duration_seconds']:.1f}s")
                    else:
                        print(f"❌ Thread {thread_id}: Upload failed - {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Thread {thread_id}: Exception - {e}")
                    results.append({
                        "thread_id": thread_id,
                        "error": str(e),
                        "success": False
                    })
        
        total_time = time.time() - start_time
        successful_uploads = sum(1 for r in results if r["success"])
        
        # Cleanup test files
        for file_path in test_files:
            file_path.unlink(missing_ok=True)
        
        return {
            "num_concurrent": num_concurrent,
            "file_size_mb": file_size_mb,
            "total_time_seconds": total_time,
            "successful_uploads": successful_uploads,
            "success_rate": successful_uploads / num_concurrent if num_concurrent > 0 else 0,
            "avg_upload_time": sum(r["duration_seconds"] for r in results if r["success"]) / successful_uploads if successful_uploads > 0 else 0,
            "individual_results": results
        }
    
    def test_memory_leak_detection(self, iterations: int = 10) -> Dict[str, Any]:
        """Test for memory leaks during repeated operations."""
        print(f"🧠 Testing memory leak detection over {iterations} iterations")
        
        tracemalloc.start()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        memory_snapshots = [initial_memory]
        
        # Generate a test file for repeated uploads
        test_file = self.generate_test_audio_file(1, "memory_leak_test.wav")
        
        try:
            for i in range(iterations):
                print(f"📊 Memory leak test iteration {i+1}/{iterations}")
                
                # Perform upload operation
                with open(test_file, 'rb') as f:
                    files = {"file": (test_file.name, f, "audio/wav")}
                    try:
                        response = requests.post(
                            f"{self.api_base}/jobs",
                            files=files,
                            timeout=30
                        )
                    except Exception as e:
                        print(f"⚠️ Upload error in iteration {i+1}: {e}")
                
                # Take memory snapshot
                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                memory_snapshots.append(current_memory)
                
                # Small delay between iterations
                time.sleep(1)
            
            # Analyze memory growth
            final_memory = memory_snapshots[-1]
            memory_growth = final_memory - initial_memory
            avg_growth_per_iteration = memory_growth / iterations if iterations > 0 else 0
            
            # Get tracemalloc statistics
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')[:10]
            
            result = {
                "iterations": iterations,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": memory_growth,
                "avg_growth_per_iteration_mb": avg_growth_per_iteration,
                "memory_snapshots": memory_snapshots,
                "potential_leak": memory_growth > (iterations * 1),  # >1MB per iteration indicates leak
                "top_memory_allocations": [
                    {
                        "file": stat.traceback.format()[0] if stat.traceback.format() else "unknown",
                        "size_mb": stat.size / (1024 * 1024)
                    }
                    for stat in top_stats[:5]
                ]
            }
            
            if result["potential_leak"]:
                print(f"⚠️ Potential memory leak detected: {memory_growth:.1f}MB growth over {iterations} iterations")
            else:
                print(f"✅ No significant memory leak detected: {memory_growth:.1f}MB growth over {iterations} iterations")
            
            return result
            
        finally:
            tracemalloc.stop()
            test_file.unlink(missing_ok=True)
    
    def run_performance_test_suite(self) -> Dict[str, Any]:
        """Run the complete performance test suite."""
        print("🏁 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        results = {
            "test_start_time": time.time(),
            "api_base": self.api_base
        }
        
        # Test 1: Large File Handling
        print("\n🎯 TEST 1: Large File Upload Testing")
        print("-" * 40)
        
        # Generate test files of increasing sizes
        large_files_results = []
        for size_minutes in [5, 15, 30, 60, 120]:  # 5min to 2hour files
            file_path = self.generate_test_audio_file(size_minutes, f"large_test_{size_minutes}min.wav")
            result = self.test_large_file_upload(file_path)
            result["duration_minutes"] = size_minutes
            large_files_results.append(result)
            
            # Cleanup
            file_path.unlink(missing_ok=True)
            
            # Break early if uploads start failing
            if not result["success"]:
                print(f"⚠️ Stopping large file tests - {size_minutes}min file failed")
                break
        
        results["large_file_tests"] = large_files_results
        
        # Test 2: Concurrent Load Testing
        print("\n🎯 TEST 2: Concurrent Upload Testing")
        print("-" * 40)
        
        concurrent_results = []
        for num_concurrent in [5, 10, 25, 50, 100]:
            result = self.test_concurrent_uploads(num_concurrent, file_size_mb=5)
            concurrent_results.append(result)
            
            # Break if success rate drops below 50%
            if result["success_rate"] < 0.5:
                print(f"⚠️ Stopping concurrent tests - success rate dropped to {result['success_rate']:.1%}")
                break
        
        results["concurrent_tests"] = concurrent_results
        
        # Test 3: Memory Leak Detection
        print("\n🎯 TEST 3: Memory Leak Detection")
        print("-" * 40)
        
        memory_leak_result = self.test_memory_leak_detection(iterations=20)
        results["memory_leak_test"] = memory_leak_result
        
        # Calculate overall results
        results["test_end_time"] = time.time()
        results["total_test_duration"] = results["test_end_time"] - results["test_start_time"]
        
        # Performance Summary
        successful_large_files = sum(1 for r in large_files_results if r["success"])
        successful_concurrent_tests = sum(1 for r in concurrent_results if r["success_rate"] > 0.8)
        
        results["summary"] = {
            "large_file_limit_minutes": max([r["duration_minutes"] for r in large_files_results if r["success"]], default=0),
            "max_concurrent_users": max([r["num_concurrent"] for r in concurrent_results if r["success_rate"] > 0.8], default=0),
            "memory_leak_detected": memory_leak_result["potential_leak"],
            "overall_performance_score": (successful_large_files * 20 + successful_concurrent_tests * 30 + (0 if memory_leak_result["potential_leak"] else 50))
        }
        
        print("\n🏆 PERFORMANCE TEST SUITE COMPLETED")
        print("=" * 60)
        print(f"📊 Large file limit: {results['summary']['large_file_limit_minutes']} minutes")
        print(f"📊 Max concurrent users: {results['summary']['max_concurrent_users']}")
        print(f"📊 Memory leak detected: {results['summary']['memory_leak_detected']}")
        print(f"📊 Overall performance score: {results['summary']['overall_performance_score']}/100")
        
        return results

def main():
    """Run performance tests and save results."""
    print("🚀 Starting Performance Testing Suite")
    
    # Initialize test suite
    tester = PerformanceTestSuite()
    
    # Run comprehensive tests
    results = tester.run_performance_test_suite()
    
    # Save results
    results_file = Path("tests/reports/performance_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📝 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    main()