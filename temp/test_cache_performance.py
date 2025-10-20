"""
Test script for T025 Phase 2: API Response Caching
Tests the Redis-based caching implementation.
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List

class CachePerformanceTester:
    """Test cache performance and functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_endpoint_caching(self) -> Dict:
        """Test caching of health endpoint."""
        endpoint = f"{self.base_url}/health"
        
        # First request (cache miss)
        start_time = time.time()
        async with self.session.get(endpoint) as response:
            first_response_time = time.time() - start_time
            first_headers = dict(response.headers)
            first_content = await response.text()
        
        # Second request (should be cache hit)
        start_time = time.time()
        async with self.session.get(endpoint) as response:
            second_response_time = time.time() - start_time
            second_headers = dict(response.headers)
            second_content = await response.text()
        
        # Third request (should also be cache hit)
        start_time = time.time()
        async with self.session.get(endpoint) as response:
            third_response_time = time.time() - start_time
            third_headers = dict(response.headers)
        
        cache_hit_1 = second_headers.get('X-Cache') == 'HIT'
        cache_hit_2 = third_headers.get('X-Cache') == 'HIT'
        
        return {
            'test': 'health_endpoint_caching',
            'first_request_time': first_response_time,
            'second_request_time': second_response_time,
            'third_request_time': third_response_time,
            'cache_hit_on_second': cache_hit_1,
            'cache_hit_on_third': cache_hit_2,
            'performance_improvement': (first_response_time - second_response_time) / first_response_time * 100,
            'content_matches': first_content == second_content,
            'cache_headers': {
                'first': first_headers.get('X-Cache', 'NONE'),
                'second': second_headers.get('X-Cache', 'NONE'),
                'third': third_headers.get('X-Cache', 'NONE')
            }
        }
    
    async def test_version_endpoint_caching(self) -> Dict:
        """Test caching of version endpoint (should have longer TTL)."""
        endpoint = f"{self.base_url}/version"
        
        start_time = time.time()
        async with self.session.get(endpoint) as response:
            first_response_time = time.time() - start_time
            first_headers = dict(response.headers)
        
        # Immediate second request
        start_time = time.time()
        async with self.session.get(endpoint) as response:
            second_response_time = time.time() - start_time
            second_headers = dict(response.headers)
        
        return {
            'test': 'version_endpoint_caching',
            'first_request_time': first_response_time,
            'second_request_time': second_response_time,
            'cache_hit': second_headers.get('X-Cache') == 'HIT',
            'cache_control': second_headers.get('Cache-Control', 'NONE'),
            'performance_improvement': (first_response_time - second_response_time) / first_response_time * 100
        }
    
    async def test_cache_invalidation(self) -> Dict:
        """Test cache invalidation functionality (requires admin access)."""
        # This test would require authentication token
        # For now, just test the cache admin endpoint availability
        endpoint = f"{self.base_url}/admin/cache/health"
        
        try:
            async with self.session.get(endpoint) as response:
                if response.status == 401:
                    return {
                        'test': 'cache_invalidation',
                        'admin_endpoint_available': True,
                        'requires_auth': True,
                        'status': 'authentication_required'
                    }
                elif response.status == 200:
                    data = await response.json()
                    return {
                        'test': 'cache_invalidation',
                        'admin_endpoint_available': True,
                        'cache_service_status': data.get('status', 'unknown'),
                        'status': 'accessible'
                    }
                else:
                    return {
                        'test': 'cache_invalidation',
                        'admin_endpoint_available': False,
                        'status': f'unexpected_status_{response.status}'
                    }
        except Exception as e:
            return {
                'test': 'cache_invalidation',
                'admin_endpoint_available': False,
                'error': str(e),
                'status': 'error'
            }
    
    async def test_non_cacheable_endpoints(self) -> Dict:
        """Test that POST endpoints are not cached."""
        # Test a POST endpoint (if available)
        endpoint = f"{self.base_url}/auth/login"
        
        test_data = {"username": "test", "password": "test"}
        
        async with self.session.post(endpoint, json=test_data) as response:
            headers = dict(response.headers)
            cache_status = headers.get('X-Cache', 'NONE')
        
        return {
            'test': 'non_cacheable_endpoints',
            'post_request_cached': cache_status != 'SKIP' and cache_status != 'NONE',
            'cache_header': cache_status,
            'status': 'correct' if cache_status in ['SKIP', 'NONE'] else 'incorrect'
        }
    
    async def run_performance_benchmark(self, endpoint: str, num_requests: int = 10) -> Dict:
        """Run performance benchmark on an endpoint."""
        times = []
        cache_hits = 0
        
        for i in range(num_requests):
            start_time = time.time()
            async with self.session.get(f"{self.base_url}{endpoint}") as response:
                request_time = time.time() - start_time
                times.append(request_time)
                
                if response.headers.get('X-Cache') == 'HIT':
                    cache_hits += 1
        
        avg_time = sum(times) / len(times)
        cache_hit_ratio = cache_hits / num_requests
        
        return {
            'test': f'performance_benchmark_{endpoint.replace("/", "_")}',
            'endpoint': endpoint,
            'num_requests': num_requests,
            'average_response_time': avg_time,
            'cache_hit_ratio': cache_hit_ratio,
            'min_time': min(times),
            'max_time': max(times),
            'cache_effectiveness': cache_hit_ratio > 0.5  # 50% hit ratio threshold
        }
    
    async def run_all_tests(self) -> List[Dict]:
        """Run all cache tests."""
        print("🧪 Starting T025 Phase 2 Cache Performance Tests...")
        
        tests = [
            self.test_health_endpoint_caching(),
            self.test_version_endpoint_caching(),
            self.test_cache_invalidation(),
            self.test_non_cacheable_endpoints(),
            self.run_performance_benchmark("/health", 5),
            self.run_performance_benchmark("/version", 5)
        ]
        
        results = []
        for test in tests:
            try:
                result = await test
                results.append(result)
                print(f"✅ {result['test']}: {result.get('status', 'completed')}")
            except Exception as e:
                results.append({
                    'test': getattr(test, '__name__', 'unknown'),
                    'error': str(e),
                    'status': 'failed'
                })
                print(f"❌ Test failed: {e}")
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate a test report."""
        report = ["", "🎯 T025 Phase 2: API Response Caching Test Report", "=" * 50, ""]
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('status') not in ['failed', 'error'])
        
        report.append(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
        report.append("")
        
        for result in results:
            test_name = result.get('test', 'Unknown Test')
            status = result.get('status', 'unknown')
            
            report.append(f"🔍 {test_name}")
            
            if 'error' in result:
                report.append(f"   ❌ Error: {result['error']}")
            else:
                for key, value in result.items():
                    if key not in ['test', 'status']:
                        if isinstance(value, float):
                            report.append(f"   • {key}: {value:.4f}")
                        elif isinstance(value, dict):
                            report.append(f"   • {key}:")
                            for subkey, subvalue in value.items():
                                report.append(f"     - {subkey}: {subvalue}")
                        else:
                            report.append(f"   • {key}: {value}")
            
            report.append("")
        
        # Performance summary
        cache_performance_tests = [r for r in results if 'cache_hit_ratio' in r]
        if cache_performance_tests:
            avg_hit_ratio = sum(r['cache_hit_ratio'] for r in cache_performance_tests) / len(cache_performance_tests)
            avg_response_time = sum(r['average_response_time'] for r in cache_performance_tests) / len(cache_performance_tests)
            
            report.append("📈 Performance Summary:")
            report.append(f"   • Average Cache Hit Ratio: {avg_hit_ratio:.2%}")
            report.append(f"   • Average Response Time: {avg_response_time:.4f}s")
            report.append("")
        
        return "\n".join(report)

async def main():
    """Main test execution."""
    async with CachePerformanceTester() as tester:
        results = await tester.run_all_tests()
        report = tester.generate_report(results)
        
        print(report)
        
        # Save results to file
        with open('/tmp/cache_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to: /tmp/cache_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
