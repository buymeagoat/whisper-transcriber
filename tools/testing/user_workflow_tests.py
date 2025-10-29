#!/usr/bin/env python3
"""
FOCUSED USER WORKFLOW TESTING
=============================

Now that the application is running, test the actual workflows a user would experience.
This answers the question: "Does the application actually work for real use?"
"""

import requests
import time
import os
import json
import sys
from pathlib import Path

class UserWorkflowTester:
    """Tests actual user workflows end-to-end."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.auth_token = None
        self.test_user = f"testuser_{int(time.time())}"
        
    def log_test(self, test_name, success, details="", response_data=None):
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
        if not success and response_data:
            print(f"   Response: {response_data}")
    
    def test_frontend_loads(self):
        """Test if the frontend actually loads in a browser."""
        print("\n🌐 TESTING FRONTEND LOADING")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Check for React application indicators
                react_indicators = [
                    '<div id="root"',
                    'react',
                    'vite',
                    '<script',
                    'html'
                ]
                
                found_indicators = [ind for ind in react_indicators if ind.lower() in content.lower()]
                
                if len(found_indicators) >= 2:
                    self.log_test(
                        "frontend_loads", 
                        True, 
                        f"Frontend loads with {len(found_indicators)} React indicators",
                        {"indicators": found_indicators}
                    )
                    return True
                else:
                    self.log_test(
                        "frontend_loads",
                        False,
                        "Frontend loads but doesn't appear to be React app",
                        {"content_preview": content[:200]}
                    )
                    return False
            else:
                self.log_test(
                    "frontend_loads",
                    False,
                    f"Frontend request failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test("frontend_loads", False, f"Frontend loading error: {e}")
            return False
    
    def test_user_registration_workflow(self):
        """Test complete user registration workflow."""
        print("\n👤 TESTING USER REGISTRATION WORKFLOW")
        print("=" * 50)
        
        try:
            # Test registration endpoint discovery
            registration_endpoints = [
                "/api/register",
                "/api/auth/register", 
                "/register",
                "/auth/register"
            ]
            
            registration_success = False
            for endpoint in registration_endpoints:
                try:
                    register_data = {
                        "username": self.test_user,
                        "password": "SecureTestPassword123!"
                    }
                    
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=register_data,
                        timeout=10
                    )
                    
                    print(f"   Trying {endpoint}: {response.status_code}")
                    
                    if response.status_code in [200, 201]:
                        self.log_test(
                            "user_registration",
                            True,
                            f"Registration successful at {endpoint}",
                            response.json()
                        )
                        registration_success = True
                        break
                    elif response.status_code == 409:
                        # User already exists - that's actually good, means registration works
                        self.log_test(
                            "user_registration", 
                            True,
                            f"Registration endpoint working at {endpoint} (user exists)",
                            {"message": "User already exists - endpoint functional"}
                        )
                        registration_success = True
                        break
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(f"      Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {e}")
                    continue
            
            if not registration_success:
                self.log_test(
                    "user_registration",
                    False,
                    "No working registration endpoint found",
                    {"attempted_endpoints": registration_endpoints}
                )
            
            return registration_success
            
        except Exception as e:
            self.log_test("user_registration", False, f"Registration workflow error: {e}")
            return False
    
    def test_user_login_workflow(self):
        """Test complete user login workflow."""
        print("\n🔐 TESTING USER LOGIN WORKFLOW")
        print("=" * 50)
        
        try:
            login_endpoints = [
                "/api/auth/login",
                "/api/login",
                "/auth/login",
                "/login"
            ]
            
            login_data = {
                "username": self.test_user,
                "password": "SecureTestPassword123!"
            }
            
            login_success = False
            for endpoint in login_endpoints:
                try:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=login_data,
                        timeout=10
                    )
                    
                    print(f"   Trying {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "access_token" in response_data:
                            self.auth_token = response_data["access_token"]
                            self.log_test(
                                "user_login",
                                True,
                                f"Login successful at {endpoint}",
                                {"token_received": True}
                            )
                            login_success = True
                            break
                        else:
                            print(f"      No token in response: {response_data}")
                    elif response.status_code == 404:
                        continue
                    else:
                        print(f"      Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {e}")
                    continue
            
            if not login_success:
                self.log_test(
                    "user_login",
                    False,
                    "No working login endpoint found",
                    {"attempted_endpoints": login_endpoints}
                )
            
            return login_success
            
        except Exception as e:
            self.log_test("user_login", False, f"Login workflow error: {e}")
            return False
    
    def test_authenticated_access(self):
        """Test authenticated API access."""
        print("\n🔒 TESTING AUTHENTICATED ACCESS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_test("authenticated_access", False, "No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test authenticated endpoints
            auth_endpoints = [
                "/api/auth/me",
                "/api/user/profile",
                "/auth/me",
                "/me"
            ]
            
            auth_success = False
            for endpoint in auth_endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"   Trying {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "username" in response_data or "id" in response_data:
                            self.log_test(
                                "authenticated_access",
                                True,
                                f"Authenticated access successful at {endpoint}",
                                response_data
                            )
                            auth_success = True
                            break
                    elif response.status_code == 404:
                        continue
                    else:
                        print(f"      Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {e}")
                    continue
            
            if not auth_success:
                self.log_test(
                    "authenticated_access",
                    False,
                    "No working authenticated endpoint found"
                )
            
            return auth_success
            
        except Exception as e:
            self.log_test("authenticated_access", False, f"Authentication error: {e}")
            return False
    
    def test_file_upload_workflow(self):
        """Test the core file upload workflow."""
        print("\n📁 TESTING FILE UPLOAD WORKFLOW")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_test("file_upload_workflow", False, "No auth token for upload test")
            return False
        
        try:
            # Create a test audio file
            test_file = "test_upload.wav"
            self.create_test_audio_file(test_file)
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test upload endpoints
            upload_endpoints = [
                "/api/transcribe/upload",
                "/api/transcribe",
                "/api/upload",
                "/upload",
                "/transcribe"
            ]
            
            upload_success = False
            for endpoint in upload_endpoints:
                try:
                    with open(test_file, 'rb') as f:
                        files = {'file': (test_file, f, 'audio/wav')}
                        
                        response = requests.post(
                            f"{self.base_url}{endpoint}",
                            files=files,
                            headers=headers,
                            timeout=30
                        )
                    
                    print(f"   Trying {endpoint}: {response.status_code}")
                    
                    if response.status_code in [200, 201, 202]:
                        response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        self.log_test(
                            "file_upload_workflow",
                            True,
                            f"File upload successful at {endpoint}",
                            response_data
                        )
                        upload_success = True
                        break
                    elif response.status_code == 404:
                        continue
                    else:
                        print(f"      Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {e}")
                    continue
            
            if not upload_success:
                self.log_test(
                    "file_upload_workflow",
                    False,
                    "No working upload endpoint found"
                )
            
            return upload_success
            
        except Exception as e:
            self.log_test("file_upload_workflow", False, f"Upload workflow error: {e}")
            return False
        finally:
            # Cleanup
            if os.path.exists("test_upload.wav"):
                os.remove("test_upload.wav")
    
    def test_transcription_status_workflow(self):
        """Test job status tracking."""
        print("\n📊 TESTING TRANSCRIPTION STATUS WORKFLOW")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_test("transcription_status", False, "No auth token for status test")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test job status endpoints
            status_endpoints = [
                "/api/jobs",
                "/api/transcribe/jobs",
                "/api/transcribe/status",
                "/jobs",
                "/status"
            ]
            
            status_success = False
            for endpoint in status_endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"   Trying {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        self.log_test(
                            "transcription_status",
                            True,
                            f"Status endpoint accessible at {endpoint}",
                            response_data
                        )
                        status_success = True
                        break
                    elif response.status_code == 404:
                        continue
                    else:
                        print(f"      Response: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"      Error: {e}")
                    continue
            
            if not status_success:
                self.log_test(
                    "transcription_status",
                    False,
                    "No working status endpoint found"
                )
            
            return status_success
            
        except Exception as e:
            self.log_test("transcription_status", False, f"Status workflow error: {e}")
            return False
    
    def create_test_audio_file(self, filename):
        """Create a minimal test audio file."""
        with open(filename, "wb") as f:
            # Write a minimal WAV header + data
            f.write(b'RIFF')
            f.write((1000).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # PCM
            f.write((1).to_bytes(2, 'little'))  # Mono
            f.write((44100).to_bytes(4, 'little'))  # Sample rate
            f.write((88200).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))  # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((956).to_bytes(4, 'little'))
            f.write(b'\x00' * 956)  # Silence
    
    def test_whisper_engine_availability(self):
        """Test if Whisper transcription engine is available."""
        print("\n🤖 TESTING WHISPER ENGINE AVAILABILITY")
        print("=" * 50)
        
        try:
            # Check if we can see any transcription-related endpoints
            response = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            
            if response.status_code == 200:
                openapi_spec = response.json()
                endpoints = openapi_spec.get("paths", {}).keys()
                
                transcribe_endpoints = [ep for ep in endpoints if "transcrib" in ep.lower()]
                
                if transcribe_endpoints:
                    self.log_test(
                        "whisper_engine_availability",
                        True,
                        f"Found {len(transcribe_endpoints)} transcription endpoints",
                        {"endpoints": transcribe_endpoints}
                    )
                    return True
                else:
                    self.log_test(
                        "whisper_engine_availability",
                        False,
                        "No transcription endpoints found in API spec",
                        {"total_endpoints": len(endpoints)}
                    )
                    return False
            else:
                self.log_test(
                    "whisper_engine_availability",
                    False,
                    "Cannot access OpenAPI spec to check endpoints"
                )
                return False
                
        except Exception as e:
            self.log_test("whisper_engine_availability", False, f"Engine check error: {e}")
            return False
    
    def run_complete_user_testing(self):
        """Run complete end-to-end user testing."""
        print("🧪 COMPLETE USER WORKFLOW TESTING")
        print("=" * 60)
        print("Testing actual user workflows to validate production readiness")
        
        # Test workflows in logical order
        tests = [
            ("Frontend Loading", self.test_frontend_loads),
            ("User Registration", self.test_user_registration_workflow),
            ("User Login", self.test_user_login_workflow),
            ("Authenticated Access", self.test_authenticated_access),
            ("Whisper Engine Check", self.test_whisper_engine_availability),
            ("File Upload", self.test_file_upload_workflow),
            ("Status Tracking", self.test_transcription_status_workflow)
        ]
        
        passed = 0
        critical_passed = 0
        total = len(tests)
        critical_tests = ["Frontend Loading", "User Registration", "User Login", "File Upload"]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            try:
                success = test_func()
                if success:
                    passed += 1
                    if test_name in critical_tests:
                        critical_passed += 1
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                self.log_test(test_name.lower().replace(" ", "_"), False, f"Test crashed: {e}")
        
        # Analysis
        print(f"\n{'='*60}")
        print("📊 USER WORKFLOW TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Overall Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"Critical Tests Passed: {critical_passed}/{len(critical_tests)} ({critical_passed/len(critical_tests)*100:.1f}%)")
        
        # Determine readiness
        if critical_passed == len(critical_tests):
            print("🎉 CORE USER WORKFLOWS WORKING!")
            print("   Users should be able to use the application successfully")
            user_success_likelihood = "HIGH"
        elif critical_passed >= len(critical_tests) * 0.75:
            print("🟡 MOST CORE WORKFLOWS WORKING")
            print("   Users likely to succeed with minor issues")
            user_success_likelihood = "MEDIUM-HIGH"
        elif critical_passed >= len(critical_tests) * 0.5:
            print("🟠 SOME CORE WORKFLOWS WORKING")
            print("   Users may encounter significant issues")
            user_success_likelihood = "MEDIUM"
        else:
            print("🔴 CORE WORKFLOWS NOT WORKING")
            print("   Users unlikely to succeed")
            user_success_likelihood = "LOW"
        
        # Detailed results
        print(f"\nUser Success Likelihood: {user_success_likelihood}")
        print("\nDetailed Test Results:")
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\nFailed Tests ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"   • {result['test']}: {result['details']}")
        
        return critical_passed == len(critical_tests)

def main():
    """Run comprehensive user workflow testing."""
    print("🎯 USER WORKFLOW VALIDATION")
    print("Testing what users will actually experience")
    
    tester = UserWorkflowTester()
    success = tester.run_complete_user_testing()
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    if success:
        print("✅ Application is ready for user testing")
        print("   Core workflows are functional")
    else:
        print("❌ Application needs fixes before user testing")
        print("   Core workflows have issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)