#!/usr/bin/env python3
"""
CRITICAL TESTING IMPLEMENTATION PLAN
====================================

Based on the comprehensive analysis, this script implements the most critical
tests needed to ensure the application will work when users try it.

Priority: TEST THE ACTUAL USER WORKFLOWS
"""

import sys
import os
import requests
import time
import subprocess
import json
from pathlib import Path

class CriticalTester:
    """Implements the most critical missing tests."""
    
    def __init__(self):
        self.results = []
        self.failures = []
    
    def log_result(self, test_name, success, details=""):
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        if not success:
            self.failures.append(result)
    
    def test_fresh_docker_build(self):
        """Test complete Docker rebuild from scratch."""
        print("\n🐳 TESTING FRESH DOCKER BUILD")
        print("=" * 50)
        
        try:
            # Stop and remove existing containers
            print("1. Stopping existing containers...")
            subprocess.run(["docker-compose", "down"], capture_output=True)
            
            # Remove existing images to force rebuild
            print("2. Removing existing images...")
            result = subprocess.run(
                ["docker", "images", "-q", "whisper-transcriber*"], 
                capture_output=True, text=True
            )
            
            if result.stdout.strip():
                subprocess.run(
                    ["docker", "rmi", "-f"] + result.stdout.strip().split('\n'),
                    capture_output=True
                )
            
            # Fresh build
            print("3. Building from scratch...")
            build_result = subprocess.run(
                ["docker-compose", "build", "--no-cache"],
                capture_output=True, text=True, timeout=300
            )
            
            if build_result.returncode == 0:
                print("✅ Fresh Docker build successful")
                self.log_result("fresh_docker_build", True, "Build completed successfully")
                return True
            else:
                print(f"❌ Build failed: {build_result.stderr}")
                self.log_result("fresh_docker_build", False, build_result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Build timed out (>5 minutes)")
            self.log_result("fresh_docker_build", False, "Build timeout")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            self.log_result("fresh_docker_build", False, str(e))
            return False
    
    def test_frontend_build_process(self):
        """Test frontend production build."""
        print("\n🎨 TESTING FRONTEND BUILD PROCESS")
        print("=" * 50)
        
        try:
            os.chdir("frontend")
            
            # Check if node_modules exists
            print("1. Checking Node.js environment...")
            if not os.path.exists("node_modules"):
                print("   Installing dependencies...")
                npm_install = subprocess.run(
                    ["npm", "install"], 
                    capture_output=True, text=True, timeout=120
                )
                if npm_install.returncode != 0:
                    print(f"❌ npm install failed: {npm_install.stderr}")
                    self.log_result("frontend_npm_install", False, npm_install.stderr)
                    return False
            
            # Test production build
            print("2. Running production build...")
            build_result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True, text=True, timeout=120
            )
            
            if build_result.returncode == 0:
                # Check if dist directory was created
                if os.path.exists("dist"):
                    dist_files = list(Path("dist").rglob("*"))
                    print(f"✅ Frontend build successful - {len(dist_files)} files generated")
                    self.log_result("frontend_build", True, f"Generated {len(dist_files)} files")
                    return True
                else:
                    print("❌ Build succeeded but no dist directory created")
                    self.log_result("frontend_build", False, "No dist directory")
                    return False
            else:
                print(f"❌ Frontend build failed: {build_result.stderr}")
                self.log_result("frontend_build", False, build_result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Frontend build timed out")
            self.log_result("frontend_build", False, "Build timeout")
            return False
        except Exception as e:
            print(f"❌ Frontend build error: {e}")
            self.log_result("frontend_build", False, str(e))
            return False
        finally:
            os.chdir("..")
    
    def test_application_startup(self):
        """Test complete application startup."""
        print("\n🚀 TESTING APPLICATION STARTUP")
        print("=" * 50)
        
        try:
            # Start services
            print("1. Starting application services...")
            startup_result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True, text=True, timeout=60
            )
            
            if startup_result.returncode != 0:
                print(f"❌ Startup failed: {startup_result.stderr}")
                self.log_result("app_startup", False, startup_result.stderr)
                return False
            
            # Wait for services to be ready
            print("2. Waiting for services to be ready...")
            max_wait = 30
            for i in range(max_wait):
                try:
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Application ready after {i+1} seconds")
                        self.log_result("app_startup", True, f"Ready in {i+1} seconds")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(1)
            
            print("❌ Application failed to become ready within 30 seconds")
            self.log_result("app_startup", False, "Ready timeout")
            return False
            
        except Exception as e:
            print(f"❌ Startup error: {e}")
            self.log_result("app_startup", False, str(e))
            return False
    
    def test_redis_connectivity(self):
        """Test Redis connectivity and job queue."""
        print("\n🔗 TESTING REDIS CONNECTIVITY")
        print("=" * 50)
        
        try:
            # Check if Redis container is running
            redis_check = subprocess.run(
                ["docker", "exec", "whisper-redis", "redis-cli", "ping"],
                capture_output=True, text=True
            )
            
            if redis_check.returncode == 0 and "PONG" in redis_check.stdout:
                print("✅ Redis server responding")
                
                # Test Celery worker connectivity
                celery_check = subprocess.run(
                    ["docker", "exec", "whisper-worker", "celery", "-A", "worker", "inspect", "ping"],
                    capture_output=True, text=True, timeout=10
                )
                
                if celery_check.returncode == 0:
                    print("✅ Celery worker responding")
                    self.log_result("redis_celery", True, "Redis and Celery working")
                    return True
                else:
                    print(f"❌ Celery worker not responding: {celery_check.stderr}")
                    self.log_result("redis_celery", False, "Celery not responding")
                    return False
            else:
                print(f"❌ Redis not responding: {redis_check.stderr}")
                self.log_result("redis_celery", False, "Redis not responding")
                return False
                
        except Exception as e:
            print(f"❌ Redis/Celery test error: {e}")
            self.log_result("redis_celery", False, str(e))
            return False
    
    def test_whisper_models(self):
        """Test Whisper model availability."""
        print("\n🤖 TESTING WHISPER MODEL AVAILABILITY")
        print("=" * 50)
        
        try:
            # Check if models directory exists and has models
            models_check = subprocess.run(
                ["docker", "exec", "whisper-app", "ls", "-la", "/app/models/"],
                capture_output=True, text=True
            )
            
            if models_check.returncode == 0:
                models = models_check.stdout
                model_files = [line for line in models.split('\n') if '.pt' in line]
                
                if model_files:
                    print(f"✅ Found {len(model_files)} Whisper model files")
                    for model in model_files:
                        print(f"   • {model.split()[-1]}")
                    
                    # Test model loading
                    model_test = subprocess.run(
                        ["docker", "exec", "whisper-app", "python", "-c", 
                         "import whisper; model = whisper.load_model('base'); print('Model loaded successfully')"],
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if model_test.returncode == 0:
                        print("✅ Whisper model loading successful")
                        self.log_result("whisper_models", True, f"{len(model_files)} models available")
                        return True
                    else:
                        print(f"❌ Model loading failed: {model_test.stderr}")
                        self.log_result("whisper_models", False, "Model loading failed")
                        return False
                else:
                    print("❌ No Whisper model files found")
                    self.log_result("whisper_models", False, "No model files")
                    return False
            else:
                print(f"❌ Cannot access models directory: {models_check.stderr}")
                self.log_result("whisper_models", False, "Cannot access models")
                return False
                
        except Exception as e:
            print(f"❌ Whisper model test error: {e}")
            self.log_result("whisper_models", False, str(e))
            return False
    
    def test_authentication_flow(self):
        """Test complete authentication workflow."""
        print("\n🔐 TESTING AUTHENTICATION FLOW")
        print("=" * 50)
        
        try:
            base_url = "http://localhost:8000"
            
            # Test user registration
            print("1. Testing user registration...")
            register_data = {
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!"
            }
            
            register_response = requests.post(
                f"{base_url}/api/register",
                json=register_data,
                timeout=10
            )
            
            if register_response.status_code in [200, 201]:
                print("✅ User registration successful")
                
                # Test user login
                print("2. Testing user login...")
                login_response = requests.post(
                    f"{base_url}/api/auth/login",
                    json=register_data,
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if "access_token" in login_data:
                        print("✅ User login successful")
                        
                        # Test authenticated endpoint
                        print("3. Testing authenticated endpoint...")
                        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
                        me_response = requests.get(
                            f"{base_url}/api/auth/me",
                            headers=headers,
                            timeout=10
                        )
                        
                        if me_response.status_code == 200:
                            print("✅ Authentication flow complete")
                            self.log_result("auth_flow", True, "Complete auth workflow")
                            return True
                        else:
                            print(f"❌ Authenticated endpoint failed: {me_response.status_code}")
                            self.log_result("auth_flow", False, "Auth endpoint failed")
                            return False
                    else:
                        print("❌ Login response missing token")
                        self.log_result("auth_flow", False, "Missing token")
                        return False
                else:
                    print(f"❌ Login failed: {login_response.status_code}")
                    self.log_result("auth_flow", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                print(f"❌ Registration failed: {register_response.status_code}")
                print(f"   Response: {register_response.text}")
                self.log_result("auth_flow", False, f"Registration failed: {register_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication flow error: {e}")
            self.log_result("auth_flow", False, str(e))
            return False
    
    def test_file_upload_capability(self):
        """Test file upload capability."""
        print("\n📁 TESTING FILE UPLOAD CAPABILITY")
        print("=" * 50)
        
        try:
            # Create a test audio file (simple WAV)
            test_file = "test_audio.wav"
            with open(test_file, "wb") as f:
                # Write a minimal WAV header (44 bytes) + some data
                f.write(b'RIFF')
                f.write((1000).to_bytes(4, 'little'))  # File size
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write((16).to_bytes(4, 'little'))    # Format chunk size
                f.write((1).to_bytes(2, 'little'))     # Audio format (PCM)
                f.write((1).to_bytes(2, 'little'))     # Number of channels
                f.write((44100).to_bytes(4, 'little')) # Sample rate
                f.write((88200).to_bytes(4, 'little')) # Byte rate
                f.write((2).to_bytes(2, 'little'))     # Block align
                f.write((16).to_bytes(2, 'little'))    # Bits per sample
                f.write(b'data')
                f.write((956).to_bytes(4, 'little'))   # Data chunk size
                f.write(b'\x00' * 956)                 # Silence data
            
            # First, register and login to get token
            register_data = {
                "username": f"uploaduser_{int(time.time())}",
                "password": "TestPassword123!"
            }
            
            requests.post("http://localhost:8000/api/register", json=register_data)
            login_response = requests.post("http://localhost:8000/api/auth/login", json=register_data)
            
            if login_response.status_code != 200:
                print("❌ Cannot authenticate for upload test")
                self.log_result("file_upload", False, "Authentication failed")
                return False
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test file upload
            print("1. Testing file upload...")
            with open(test_file, 'rb') as f:
                files = {'file': (test_file, f, 'audio/wav')}
                
                # Try multiple possible upload endpoints
                upload_endpoints = [
                    "/api/transcribe",
                    "/api/upload", 
                    "/upload",
                    "/transcribe"
                ]
                
                upload_success = False
                for endpoint in upload_endpoints:
                    try:
                        upload_response = requests.post(
                            f"http://localhost:8000{endpoint}",
                            files=files,
                            headers=headers,
                            timeout=30
                        )
                        
                        if upload_response.status_code in [200, 201, 202]:
                            print(f"✅ File upload successful to {endpoint}")
                            upload_success = True
                            break
                        elif upload_response.status_code == 404:
                            continue  # Try next endpoint
                        else:
                            print(f"   Upload to {endpoint}: {upload_response.status_code}")
                    except Exception as e:
                        print(f"   Upload to {endpoint} failed: {e}")
                        continue
                
                if upload_success:
                    self.log_result("file_upload", True, "File upload working")
                    return True
                else:
                    print("❌ No working upload endpoint found")
                    self.log_result("file_upload", False, "No upload endpoint")
                    return False
                    
        except Exception as e:
            print(f"❌ File upload test error: {e}")
            self.log_result("file_upload", False, str(e))
            return False
        finally:
            # Cleanup test file
            if os.path.exists("test_audio.wav"):
                os.remove("test_audio.wav")
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible."""
        print("\n🌐 TESTING FRONTEND ACCESSIBILITY")
        print("=" * 50)
        
        try:
            # Test frontend static files
            response = requests.get("http://localhost:8000/", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if "<!DOCTYPE html>" in content or "<html" in content:
                    print("✅ Frontend HTML page accessible")
                    
                    # Check for React-specific content
                    if "react" in content.lower() or "root" in content:
                        print("✅ React application detected")
                        self.log_result("frontend_access", True, "Frontend accessible")
                        return True
                    else:
                        print("⚠️  HTML accessible but may not be React app")
                        self.log_result("frontend_access", True, "HTML accessible, React unclear")
                        return True
                else:
                    print(f"❌ Unexpected content type: {content[:100]}...")
                    self.log_result("frontend_access", False, "Unexpected content")
                    return False
            else:
                print(f"❌ Frontend not accessible: {response.status_code}")
                self.log_result("frontend_access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Frontend accessibility error: {e}")
            self.log_result("frontend_access", False, str(e))
            return False
    
    def run_critical_tests(self):
        """Run all critical tests in order."""
        print("🧪 RUNNING CRITICAL APPLICATION TESTS")
        print("=" * 60)
        print("Testing the core functionality that users will actually use")
        
        # Test order matters - build first, then services, then functionality
        tests = [
            ("Fresh Docker Build", self.test_fresh_docker_build),
            ("Frontend Build Process", self.test_frontend_build_process), 
            ("Application Startup", self.test_application_startup),
            ("Redis/Celery Connectivity", self.test_redis_connectivity),
            ("Whisper Models", self.test_whisper_models),
            ("Authentication Flow", self.test_authentication_flow),
            ("File Upload Capability", self.test_file_upload_capability),
            ("Frontend Accessibility", self.test_frontend_accessibility)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                self.log_result(test_name.lower().replace(" ", "_"), False, f"Crashed: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 CRITICAL TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL CRITICAL TESTS PASSED!")
            print("   Application should work for user testing")
        elif passed >= total * 0.8:
            print("🟡 MOST TESTS PASSED - Application likely works with minor issues")
        elif passed >= total * 0.5:
            print("🟠 PARTIAL SUCCESS - Application may work but has significant issues")
        else:
            print("🔴 MAJOR ISSUES - Application unlikely to work for users")
        
        print(f"\nFailed tests: {len(self.failures)}")
        for failure in self.failures:
            print(f"   ❌ {failure['test']}: {failure['details']}")
        
        return passed == total

def main():
    """Run critical testing."""
    tester = CriticalTester()
    success = tester.run_critical_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)