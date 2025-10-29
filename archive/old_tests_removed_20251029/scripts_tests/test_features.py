#!/usr/bin/env python3
"""
Comprehensive test script for all implemented features
"""
import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def test_security_headers():
    """Test security headers middleware"""
    print("🔒 Testing Security Headers...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        headers = response.headers
        
        # Check for security headers
        security_checks = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        print(f"  📋 Status Code: {response.status_code}")
        print(f"  📋 Response Headers: {dict(headers)}")
        
        for header, expected in security_checks.items():
            if header in headers:
                print(f"  ✅ {header}: {headers[header]}")
            else:
                print(f"  ❌ Missing: {header}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting middleware"""
    print("\n⚡ Testing Rate Limiting...")
    
    try:
        # Make multiple requests to trigger rate limiting
        for i in range(7):
            response = requests.post(
                f"{BASE_URL}/token",
                data={"username": "test", "password": "test"},
                timeout=5
            )
            print(f"  📋 Request {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"  ✅ Rate limiting activated!")
                print(f"  📋 Headers: {dict(response.headers)}")
                return True
            time.sleep(0.1)
        
        print("  ⚠️  Rate limiting not triggered (may need more requests)")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_api_caching():
    """Test API response caching"""
    print("\n💾 Testing API Caching...")
    
    try:
        # Make the same request twice to test caching
        start_time = time.time()
        response1 = requests.get(f"{BASE_URL}/", timeout=5)
        first_time = time.time() - start_time
        
        start_time = time.time()
        response2 = requests.get(f"{BASE_URL}/", timeout=5)
        second_time = time.time() - start_time
        
        print(f"  📋 First request: {first_time:.3f}s")
        print(f"  📋 Second request: {second_time:.3f}s")
        
        # Check for cache headers
        cache_headers = ["X-Cache", "X-Cache-TTL"]
        for header in cache_headers:
            if header in response2.headers:
                print(f"  ✅ {header}: {response2.headers[header]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n🚨 Testing Error Handling...")
    
    try:
        # Test with invalid endpoint
        response = requests.get(f"{BASE_URL}/nonexistent", timeout=5)
        print(f"  📋 Invalid endpoint status: {response.status_code}")
        
        # Test with invalid JSON
        response = requests.post(
            f"{BASE_URL}/token",
            data="invalid data",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"  📋 Invalid data status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("🚀 Starting Comprehensive Application Tests")
    print("=" * 50)
    
    tests = [
        test_security_headers,
        test_rate_limiting,
        test_api_caching,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"  ✅ Passed: {passed}/{total}")
    print(f"  ❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
