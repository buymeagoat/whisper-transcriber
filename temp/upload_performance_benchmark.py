"""
Performance Benchmarking Script for T025 Phase 5: Chunked Upload System

Tests upload performance with various file sizes and network conditions,
measures improvements over the traditional upload system.
"""

import asyncio
import time
import tempfile
import os
import statistics
from pathlib import Path
from typing import List, Dict, Any
import aiohttp
import aiofiles
from dataclasses import dataclass, asdict
import json

from api.services.chunked_upload_service import ChunkedUploadService
from api.utils.logger import get_system_logger

logger = get_system_logger("upload_benchmark")


@dataclass
class BenchmarkResult:
    """Benchmark test result."""
    test_name: str
    file_size_mb: float
    upload_type: str  # "traditional" or "chunked"
    duration_seconds: float
    throughput_mbps: float
    memory_usage_mb: float
    success: bool
    error: str = None
    chunk_count: int = 0
    parallel_chunks: int = 0
    network_condition: str = "normal"


class UploadBenchmark:
    """Benchmark suite for upload performance testing."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results: List[BenchmarkResult] = []
        self.chunked_service = ChunkedUploadService()
        
        # Test file sizes (in MB)
        self.test_sizes = [1, 5, 10, 25, 50, 100, 250, 500]
        
        # Network conditions to simulate
        self.network_conditions = {
            "fast": {"bandwidth_mbps": 100, "latency_ms": 10, "packet_loss": 0},
            "normal": {"bandwidth_mbps": 25, "latency_ms": 50, "packet_loss": 0},
            "slow": {"bandwidth_mbps": 5, "latency_ms": 200, "packet_loss": 0.1},
            "mobile": {"bandwidth_mbps": 2, "latency_ms": 300, "packet_loss": 0.5}
        }
    
    def create_test_file(self, size_mb: float) -> Path:
        """Create a test file of specified size."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        # Generate test data (repeating pattern)
        chunk_size = 1024 * 1024  # 1MB chunks
        pattern = b'A' * chunk_size
        
        bytes_written = 0
        target_bytes = int(size_mb * 1024 * 1024)
        
        with open(temp_file.name, 'wb') as f:
            while bytes_written < target_bytes:
                remaining = target_bytes - bytes_written
                write_size = min(chunk_size, remaining)
                f.write(pattern[:write_size])
                bytes_written += write_size
        
        return Path(temp_file.name)
    
    async def benchmark_traditional_upload(
        self, 
        file_path: Path, 
        file_size_mb: float,
        network_condition: str = "normal"
    ) -> BenchmarkResult:
        """Benchmark traditional single-file upload."""
        start_time = time.time()
        memory_start = self.get_memory_usage()
        
        try:
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=file_path.name, content_type='audio/mp3')
                    data.add_field('model', 'small')
                    
                    # Simulate network conditions if needed
                    timeout = self.calculate_timeout(file_size_mb, network_condition)
                    
                    async with session.post(
                        f"{self.base_url}/jobs/",
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        result = await response.json()
                        
                        if response.status != 200:
                            raise Exception(f"Upload failed: {result}")
            
            duration = time.time() - start_time
            memory_peak = self.get_memory_usage()
            memory_used = memory_peak - memory_start
            throughput = (file_size_mb * 8) / duration  # Mbps
            
            return BenchmarkResult(
                test_name=f"traditional_{file_size_mb}MB",
                file_size_mb=file_size_mb,
                upload_type="traditional",
                duration_seconds=duration,
                throughput_mbps=throughput,
                memory_usage_mb=memory_used,
                success=True,
                network_condition=network_condition
            )
            
        except Exception as e:
            duration = time.time() - start_time
            memory_peak = self.get_memory_usage()
            memory_used = memory_peak - memory_start
            
            return BenchmarkResult(
                test_name=f"traditional_{file_size_mb}MB",
                file_size_mb=file_size_mb,
                upload_type="traditional",
                duration_seconds=duration,
                throughput_mbps=0,
                memory_usage_mb=memory_used,
                success=False,
                error=str(e),
                network_condition=network_condition
            )
    
    async def benchmark_chunked_upload(
        self, 
        file_path: Path, 
        file_size_mb: float,
        parallel_chunks: int = 4,
        network_condition: str = "normal"
    ) -> BenchmarkResult:
        """Benchmark chunked upload."""
        start_time = time.time()
        memory_start = self.get_memory_usage()
        
        try:
            # Initialize upload session
            session_result = await self.chunked_service.initialize_upload(
                user_id="benchmark_user",
                filename=file_path.name,
                file_size=file_path.stat().st_size,
                model_name="small"
            )
            
            session_id = session_result["session_id"]
            total_chunks = session_result["total_chunks"]
            chunk_size = session_result["chunk_size"]
            
            # Upload chunks in parallel
            chunk_upload_times = []
            
            async def upload_chunk_batch(chunk_numbers):
                """Upload a batch of chunks."""
                tasks = []
                for chunk_num in chunk_numbers:
                    tasks.append(self.upload_single_chunk(
                        file_path, session_id, chunk_num, chunk_size,
                        network_condition
                    ))
                
                batch_start = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                batch_duration = time.time() - batch_start
                
                # Check for errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        raise result
                
                chunk_upload_times.append(batch_duration)
                return results
            
            # Upload in batches
            for i in range(0, total_chunks, parallel_chunks):
                batch = list(range(i, min(i + parallel_chunks, total_chunks)))
                await upload_chunk_batch(batch)
            
            # Finalize upload
            finalize_start = time.time()
            finalize_result = await self.chunked_service.finalize_upload(
                session_id, "benchmark_user"
            )
            finalize_duration = time.time() - finalize_start
            
            duration = time.time() - start_time
            memory_peak = self.get_memory_usage()
            memory_used = memory_peak - memory_start
            throughput = (file_size_mb * 8) / duration  # Mbps
            
            return BenchmarkResult(
                test_name=f"chunked_{file_size_mb}MB_{parallel_chunks}parallel",
                file_size_mb=file_size_mb,
                upload_type="chunked",
                duration_seconds=duration,
                throughput_mbps=throughput,
                memory_usage_mb=memory_used,
                success=True,
                chunk_count=total_chunks,
                parallel_chunks=parallel_chunks,
                network_condition=network_condition
            )
            
        except Exception as e:
            duration = time.time() - start_time
            memory_peak = self.get_memory_usage()
            memory_used = memory_peak - memory_start
            
            return BenchmarkResult(
                test_name=f"chunked_{file_size_mb}MB_{parallel_chunks}parallel",
                file_size_mb=file_size_mb,
                upload_type="chunked",
                duration_seconds=duration,
                throughput_mbps=0,
                memory_usage_mb=memory_used,
                success=False,
                error=str(e),
                chunk_count=0,
                parallel_chunks=parallel_chunks,
                network_condition=network_condition
            )
    
    async def upload_single_chunk(
        self, 
        file_path: Path, 
        session_id: str, 
        chunk_number: int, 
        chunk_size: int,
        network_condition: str
    ):
        """Upload a single chunk."""
        start_pos = chunk_number * chunk_size
        
        async with aiofiles.open(file_path, 'rb') as f:
            await f.seek(start_pos)
            chunk_data = await f.read(chunk_size)
        
        # Simulate network delay if needed
        if network_condition != "normal":
            delay = self.calculate_network_delay(len(chunk_data), network_condition)
            await asyncio.sleep(delay)
        
        return await self.chunked_service.upload_chunk(
            session_id, chunk_number, chunk_data, "benchmark_user"
        )
    
    def calculate_timeout(self, file_size_mb: float, network_condition: str) -> float:
        """Calculate appropriate timeout based on file size and network conditions."""
        base_timeout = 30  # seconds
        size_factor = file_size_mb / 10  # Additional seconds per 10MB
        
        condition_multiplier = {
            "fast": 1.0,
            "normal": 2.0,
            "slow": 5.0,
            "mobile": 10.0
        }.get(network_condition, 2.0)
        
        return base_timeout + (size_factor * condition_multiplier)
    
    def calculate_network_delay(self, chunk_size: int, network_condition: str) -> float:
        """Calculate network delay for chunk upload simulation."""
        if network_condition == "normal":
            return 0
        
        condition = self.network_conditions.get(network_condition, self.network_conditions["normal"])
        
        # Base latency
        latency_delay = condition["latency_ms"] / 1000
        
        # Bandwidth delay
        bandwidth_bps = condition["bandwidth_mbps"] * 1024 * 1024 / 8
        transfer_delay = chunk_size / bandwidth_bps
        
        # Packet loss simulation (retry delay)
        packet_loss_delay = condition["packet_loss"] * 0.5  # Average retry delay
        
        return latency_delay + transfer_delay + packet_loss_delay
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    async def run_size_comparison(self, file_size_mb: float) -> Dict[str, Any]:
        """Compare traditional vs chunked upload for a specific file size."""
        logger.info(f"Testing {file_size_mb}MB file upload performance")
        
        # Create test file
        test_file = self.create_test_file(file_size_mb)
        
        try:
            results = {}
            
            # Test traditional upload (only for smaller files)
            if file_size_mb <= 100:  # Traditional uploads limited by memory
                traditional_result = await self.benchmark_traditional_upload(
                    test_file, file_size_mb
                )
                results["traditional"] = traditional_result
                self.results.append(traditional_result)
            
            # Test chunked upload with different parallel settings
            for parallel_chunks in [1, 2, 4, 8]:
                chunked_result = await self.benchmark_chunked_upload(
                    test_file, file_size_mb, parallel_chunks
                )
                results[f"chunked_{parallel_chunks}"] = chunked_result
                self.results.append(chunked_result)
            
            return results
            
        finally:
            # Cleanup test file
            test_file.unlink()
    
    async def run_network_condition_test(self, file_size_mb: float = 25) -> Dict[str, Any]:
        """Test upload performance under different network conditions."""
        logger.info(f"Testing network condition impact with {file_size_mb}MB file")
        
        test_file = self.create_test_file(file_size_mb)
        
        try:
            results = {}
            
            for condition_name in self.network_conditions.keys():
                logger.info(f"Testing {condition_name} network conditions")
                
                # Only test chunked uploads for network conditions
                chunked_result = await self.benchmark_chunked_upload(
                    test_file, file_size_mb, parallel_chunks=4, 
                    network_condition=condition_name
                )
                results[condition_name] = chunked_result
                self.results.append(chunked_result)
            
            return results
            
        finally:
            test_file.unlink()
    
    async def run_resume_test(self, file_size_mb: float = 50) -> Dict[str, Any]:
        """Test upload resume functionality."""
        logger.info(f"Testing upload resume with {file_size_mb}MB file")
        
        test_file = self.create_test_file(file_size_mb)
        
        try:
            # Initialize upload
            session_result = await self.chunked_service.initialize_upload(
                user_id="resume_test_user",
                filename=test_file.name,
                file_size=test_file.stat().st_size
            )
            
            session_id = session_result["session_id"]
            total_chunks = session_result["total_chunks"]
            chunk_size = session_result["chunk_size"]
            
            # Upload first half of chunks
            start_time = time.time()
            halfway_point = total_chunks // 2
            
            for chunk_num in range(halfway_point):
                chunk_data = await self.read_chunk(test_file, chunk_num, chunk_size)
                await self.chunked_service.upload_chunk(
                    session_id, chunk_num, chunk_data, "resume_test_user"
                )
            
            # Check status
            status = await self.chunked_service.get_upload_status(
                session_id, "resume_test_user"
            )
            
            # Simulate interruption (time gap)
            await asyncio.sleep(1)
            
            # Resume upload
            resume_start = time.time()
            
            for chunk_num in range(halfway_point, total_chunks):
                chunk_data = await self.read_chunk(test_file, chunk_num, chunk_size)
                await self.chunked_service.upload_chunk(
                    session_id, chunk_num, chunk_data, "resume_test_user"
                )
            
            # Finalize
            finalize_result = await self.chunked_service.finalize_upload(
                session_id, "resume_test_user"
            )
            
            total_duration = time.time() - start_time
            resume_duration = time.time() - resume_start
            
            return {
                "success": True,
                "total_duration": total_duration,
                "resume_duration": resume_duration,
                "chunks_resumed": total_chunks - halfway_point,
                "total_chunks": total_chunks
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            test_file.unlink()
    
    async def read_chunk(self, file_path: Path, chunk_number: int, chunk_size: int) -> bytes:
        """Read a specific chunk from file."""
        start_pos = chunk_number * chunk_size
        
        async with aiofiles.open(file_path, 'rb') as f:
            await f.seek(start_pos)
            return await f.read(chunk_size)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        # Group results by upload type
        traditional_results = [r for r in self.results if r.upload_type == "traditional"]
        chunked_results = [r for r in self.results if r.upload_type == "chunked"]
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "traditional_tests": len(traditional_results),
                "chunked_tests": len(chunked_results),
                "success_rate": len([r for r in self.results if r.success]) / len(self.results) * 100
            },
            "performance_comparison": {},
            "memory_usage": {},
            "scalability": {},
            "network_impact": {},
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        # Performance comparison
        if traditional_results and chunked_results:
            traditional_throughput = statistics.mean([r.throughput_mbps for r in traditional_results if r.success])
            chunked_throughput = statistics.mean([r.throughput_mbps for r in chunked_results if r.success])
            
            report["performance_comparison"] = {
                "traditional_avg_throughput_mbps": traditional_throughput,
                "chunked_avg_throughput_mbps": chunked_throughput,
                "improvement_factor": chunked_throughput / traditional_throughput if traditional_throughput > 0 else float('inf'),
                "improvement_percentage": ((chunked_throughput - traditional_throughput) / traditional_throughput * 100) if traditional_throughput > 0 else float('inf')
            }
        
        # Memory usage analysis
        traditional_memory = [r.memory_usage_mb for r in traditional_results if r.success]
        chunked_memory = [r.memory_usage_mb for r in chunked_results if r.success]
        
        if traditional_memory and chunked_memory:
            report["memory_usage"] = {
                "traditional_avg_mb": statistics.mean(traditional_memory),
                "traditional_peak_mb": max(traditional_memory),
                "chunked_avg_mb": statistics.mean(chunked_memory),
                "chunked_peak_mb": max(chunked_memory),
                "memory_reduction_percentage": ((statistics.mean(traditional_memory) - statistics.mean(chunked_memory)) / statistics.mean(traditional_memory) * 100) if traditional_memory else 0
            }
        
        # Scalability analysis
        file_sizes = sorted(list(set([r.file_size_mb for r in self.results if r.success])))
        scalability_data = []
        
        for size in file_sizes:
            size_results = [r for r in self.results if r.file_size_mb == size and r.success]
            if size_results:
                avg_throughput = statistics.mean([r.throughput_mbps for r in size_results])
                avg_memory = statistics.mean([r.memory_usage_mb for r in size_results])
                scalability_data.append({
                    "file_size_mb": size,
                    "avg_throughput_mbps": avg_throughput,
                    "avg_memory_mb": avg_memory
                })
        
        report["scalability"] = scalability_data
        
        # Network impact analysis
        network_results = {}
        for condition in self.network_conditions.keys():
            condition_results = [r for r in self.results if r.network_condition == condition and r.success]
            if condition_results:
                network_results[condition] = {
                    "avg_throughput_mbps": statistics.mean([r.throughput_mbps for r in condition_results]),
                    "avg_duration_seconds": statistics.mean([r.duration_seconds for r in condition_results])
                }
        
        report["network_impact"] = network_results
        
        return report
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        logger.info("Starting comprehensive upload performance benchmark")
        
        # Test different file sizes
        for size_mb in [1, 5, 10, 25, 50]:  # Reduced for demo
            try:
                await self.run_size_comparison(size_mb)
            except Exception as e:
                logger.error(f"Failed to test {size_mb}MB file: {e}")
        
        # Test network conditions
        try:
            await self.run_network_condition_test()
        except Exception as e:
            logger.error(f"Failed network condition test: {e}")
        
        # Test resume functionality
        try:
            resume_result = await self.run_resume_test()
            logger.info(f"Resume test result: {resume_result}")
        except Exception as e:
            logger.error(f"Failed resume test: {e}")
        
        # Generate final report
        report = self.generate_report()
        
        # Save report to file
        report_file = Path("temp/upload_benchmark_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Benchmark complete. Report saved to {report_file}")
        return report


async def main():
    """Run benchmark suite."""
    benchmark = UploadBenchmark()
    report = await benchmark.run_full_benchmark()
    
    print("\n" + "="*60)
    print("UPLOAD PERFORMANCE BENCHMARK RESULTS")
    print("="*60)
    
    summary = report.get("summary", {})
    print(f"Total tests: {summary.get('total_tests', 0)}")
    print(f"Success rate: {summary.get('success_rate', 0):.1f}%")
    
    perf = report.get("performance_comparison", {})
    if perf:
        print(f"\nPerformance Improvement:")
        print(f"  Traditional: {perf.get('traditional_avg_throughput_mbps', 0):.1f} Mbps")
        print(f"  Chunked: {perf.get('chunked_avg_throughput_mbps', 0):.1f} Mbps")
        print(f"  Improvement: {perf.get('improvement_percentage', 0):.1f}%")
    
    memory = report.get("memory_usage", {})
    if memory:
        print(f"\nMemory Usage:")
        print(f"  Traditional: {memory.get('traditional_avg_mb', 0):.1f} MB")
        print(f"  Chunked: {memory.get('chunked_avg_mb', 0):.1f} MB")
        print(f"  Reduction: {memory.get('memory_reduction_percentage', 0):.1f}%")
    
    print(f"\nDetailed report saved to temp/upload_benchmark_report.json")


if __name__ == "__main__":
    asyncio.run(main())
