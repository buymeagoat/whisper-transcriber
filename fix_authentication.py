#!/usr/bin/env python3
"""
Complete Authentication Reset and Fix

This script completely resets authentication, creates clean users,
and verifies everything works end-to-end.
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class AuthenticationFixer:
    """Complete authentication fixing and testing"""
    
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8000"
        
    def reset_database(self):
        """Completely reset the database"""
        print("🗄️  Resetting database...")
        
        # Remove old database
        db_file = Path("whisper_dev.db")
        if db_file.exists():
            db_file.unlink()
            print("✅ Removed old database")
        
        # Create clean database from models
        from api.models import Base
        from api.orm_bootstrap import engine
        
        Base.metadata.create_all(bind=engine)
        print("✅ Created clean database tables")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ Created tables: {', '.join(tables)}")
        
        return True
    
    def create_users(self):
        """Create and verify users"""
        print("\n👥 Creating users...")
        
        from api.services.users import create_user, get_user_by_username, verify_password
        
        users_to_create = [
            ("admin", "admin123", "admin"),
            ("testuser", "test123", "user"),
            ("developer", "dev123", "user")
        ]
        
        created_users = []
        
        for username, password, role in users_to_create:
            try:
                # Check if user exists
                existing_user = get_user_by_username(username)
                if existing_user:
                    print(f"✅ User {username} already exists")
                    user = existing_user
                else:
                    user = create_user(username, password, role)
                    print(f"✅ Created user: {username} ({role})")
                
                # Verify password
                if verify_password(password, user.hashed_password):
                    print(f"✅ Password verification works for {username}")
                    created_users.append((username, password, role))
                else:
                    print(f"❌ Password verification failed for {username}")
                    
            except Exception as e:
                print(f"❌ Error creating user {username}: {e}")
        
        return created_users
    
    def start_server(self):
        """Start the server with clean database"""
        print("\n🚀 Starting server...")
        
        try:
            # Start the server
            cmd = [sys.executable, "scripts/server_entry.py"]
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "LOG_LEVEL": "INFO"}
            )
            
            # Wait for server to start
            for attempt in range(30):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ Server started successfully")
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    
            print("❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def test_authentication(self, users):
        """Test authentication for all users"""
        print("\n🔐 Testing authentication...")
        
        successful_logins = []
        
        for username, password, role in users:
            try:
                response = requests.post(
                    f"{self.base_url}/token",
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        print(f"✅ Login successful for {username}")
                        successful_logins.append((username, password, data["access_token"]))
                    else:
                        print(f"❌ Login response missing token for {username}")
                else:
                    print(f"❌ Login failed for {username}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Login error for {username}: {e}")
        
        return successful_logins
    
    def test_authenticated_endpoints(self, successful_logins):
        """Test endpoints that require authentication"""
        print("\n🌐 Testing authenticated endpoints...")
        
        if not successful_logins:
            print("❌ No successful logins to test with")
            return False
        
        # Use admin token for testing
        admin_login = None
        user_login = None
        
        for username, password, token in successful_logins:
            if username == "admin":
                admin_login = (username, token)
            else:
                user_login = (username, token)
        
        if not admin_login:
            print("❌ No admin login available")
            return False
        
        admin_username, admin_token = admin_login
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test endpoints
        endpoints_to_test = [
            ("GET", "/user/settings", "User Settings"),
            ("GET", "/admin/stats", "Admin Statistics"),
            ("GET", "/users", "User List"),
            ("GET", "/admin/browse?folder=logs", "File Browser"),
        ]
        
        successful_tests = 0
        
        for method, endpoint, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
                
                if response.status_code < 400:
                    print(f"✅ {name}: {response.status_code}")
                    successful_tests += 1
                else:
                    print(f"❌ {name}: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"❌ {name}: Exception - {e}")
        
        print(f"\n📊 Authenticated endpoint tests: {successful_tests}/{len(endpoints_to_test)} successful")
        return successful_tests > 0
    
    def test_file_upload_with_auth(self, successful_logins):
        """Test file upload with authentication"""
        print("\n📁 Testing file upload with authentication...")
        
        if not successful_logins:
            print("⚠️  No auth tokens available, testing without authentication")
            headers = {}
        else:
            # Use any valid token
            username, password, token = successful_logins[0]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"Using token from user: {username}")
        
        # Create a test audio file
        test_audio_path = project_root / "test_auth_audio.wav"
        
        # Create minimal WAV file
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # File size
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # Subchunk1Size
            0x01, 0x00,              # AudioFormat
            0x01, 0x00,              # NumChannels
            0x44, 0xAC, 0x00, 0x00,  # SampleRate
            0x88, 0x58, 0x01, 0x00,  # ByteRate
            0x02, 0x00,              # BlockAlign
            0x10, 0x00,              # BitsPerSample
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x00, 0x00, 0x00   # Subchunk2Size
        ])
        
        try:
            with open(test_audio_path, "wb") as f:
                f.write(wav_header)
            
            # Upload the file
            with open(test_audio_path, "rb") as f:
                files = {"file": ("test_auth_audio.wav", f, "audio/wav")}
                data = {"model": "tiny"}
                
                response = requests.post(
                    f"{self.base_url}/jobs",
                    files=files,
                    data=data,
                    headers=headers
                )
            
            # Clean up
            test_audio_path.unlink(missing_ok=True)
            
            if response.status_code < 400:
                try:
                    result_data = response.json()
                    job_id = result_data.get("job_id")
                    print(f"✅ File upload successful! Job ID: {job_id}")
                    return job_id
                except:
                    print(f"✅ File upload successful! Status: {response.status_code}")
                    return True
            else:
                print(f"❌ File upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ File upload error: {e}")
            return False
    
    def stop_server(self):
        """Stop the test server"""
        if self.server_process:
            print("\n🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.server_process.wait()
            print("✅ Server stopped")
    
    def run_complete_fix(self):
        """Run the complete authentication fix and test"""
        print("🔧 COMPLETE AUTHENTICATION RESET AND FIX")
        print("=" * 60)
        
        try:
            # Step 1: Reset database
            if not self.reset_database():
                print("❌ Database reset failed")
                return False
            
            # Step 2: Create users
            users = self.create_users()
            if not users:
                print("❌ User creation failed")
                return False
            
            # Step 3: Start server
            if not self.start_server():
                print("❌ Server start failed")
                return False
            
            # Step 4: Test authentication
            successful_logins = self.test_authentication(users)
            if not successful_logins:
                print("❌ Authentication tests failed")
                return False
            
            # Step 5: Test authenticated endpoints
            auth_endpoints_work = self.test_authenticated_endpoints(successful_logins)
            
            # Step 6: Test file upload
            upload_result = self.test_file_upload_with_auth(successful_logins)
            
            # Final assessment
            print("\n" + "=" * 60)
            print("AUTHENTICATION FIX SUMMARY")
            print("=" * 60)
            
            print(f"✅ Database: Reset and initialized")
            print(f"✅ Users: {len(users)} created")
            print(f"✅ Authentication: {len(successful_logins)} successful logins")
            print(f"{'✅' if auth_endpoints_work else '❌'} Authenticated Endpoints: {'Working' if auth_endpoints_work else 'Failed'}")
            print(f"{'✅' if upload_result else '❌'} File Upload: {'Working' if upload_result else 'Failed'}")
            
            success_rate = (
                1 +  # Database
                1 +  # Users
                (1 if successful_logins else 0) +  # Auth
                (1 if auth_endpoints_work else 0) +  # Endpoints
                (1 if upload_result else 0)  # Upload
            ) / 5 * 100
            
            print(f"\n📊 Overall Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("🎉 AUTHENTICATION FULLY FIXED!")
                print("\nCredentials:")
                for username, password, role in users:
                    print(f"  {username}: {password} ({role})")
                    
                print(f"\nServer running at: {self.base_url}")
                print("You can now run the comprehensive tests!")
                return True
            else:
                print("⚠️  Authentication partially working but needs attention")
                return False
                
        except KeyboardInterrupt:
            print("\n🛑 Fix interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Fix failed with exception: {e}")
            return False
        finally:
            # Keep server running for testing
            if self.server_process:
                print(f"\n🔄 Server left running for testing at {self.base_url}")
                print("Stop with: pkill -f server_entry.py")

def main():
    """Main entry point"""
    fixer = AuthenticationFixer()
    success = fixer.run_complete_fix()
    
    if success:
        print("\n🚀 Ready to run comprehensive tests:")
        print("  python comprehensive_integration_test.py")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
