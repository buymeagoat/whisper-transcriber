#!/usr/bin/env python3
"""
Production validation test script
Tests API functionality without blocking terminals
"""
import requests
import subprocess
import time
import json
import os
import sys

def test_api_health():
    """Test API health endpoints"""
    print("🔧 Starting API server for testing...")
    
    # Start server in background
    server = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 'api.main:app', 
        '--host', '127.0.0.1', '--port', '8090'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(8)
    
    try:
        print("✅ Testing health endpoint...")
        response = requests.get('http://127.0.0.1:8090/health', timeout=5)
        print(f"Health: {response.status_code} - {response.json()}")
        
        print("✅ Testing version endpoint...")
        response = requests.get('http://127.0.0.1:8090/version', timeout=5)
        print(f"Version: {response.status_code} - {response.json()}")
        
        print("✅ Testing admin stats...")
        response = requests.get('http://127.0.0.1:8090/admin/stats', timeout=5)
        print(f"Admin stats: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    finally:
        server.terminate()
        server.wait()

def test_database():
    """Test database functionality"""
    print("🔧 Testing database...")
    try:
        from api.orm_bootstrap import get_database_info
        info = get_database_info()
        print(f"✅ Database tables: {len(info.get('tables', []))}")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_models():
    """Test model imports"""
    print("🔧 Testing model imports...")
    try:
        from api.models import Job, JobStatusEnum
        from api.extended_models.export_system import ExportTemplate, ExportJob
        print("✅ Core models import successfully")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Production Validation Tests")
    print("=" * 50)
    
    # Change to project directory
    os.chdir('/home/buymeagoat/dev/whisper-transcriber')
    
    results = []
    results.append(("Database", test_database()))
    results.append(("Models", test_models()))
    results.append(("API Health", test_api_health()))
    
    print("\n" + "=" * 50)
    print("📊 PRODUCTION TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All production tests PASSED! System ready for deployment.")
    else:
        print("⚠️  Some tests failed. Review issues before production deployment.")