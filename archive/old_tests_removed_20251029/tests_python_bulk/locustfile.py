#!/usr/bin/env python3
"""
T031: Production Deployment and Monitoring - Load Testing Suite
Comprehensive load testing for Whisper Transcriber using Locust
"""

import random
import time
import json
import os
import base64
from io import BytesIO
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperTranscriberUser(HttpUser):
    """
    Locust user class for load testing Whisper Transcriber
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.auth_token = None
        self.user_id = None
        self.register_and_login()
    
    def register_and_login(self):
        """Register a new user and login"""
        # Generate unique user credentials
        user_number = random.randint(1000, 9999)
        username = f"loadtest_user_{user_number}"
        email = f"loadtest_{user_number}@example.com"
        password = "LoadTest123!"
        
        # Register user
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password
        }
        
        register_response = self.client.post(
            "/api/auth/register",
            json=register_data,
            catch_response=True,
            name="register_user"
        )
        
        if register_response.status_code != 201:
            logger.error(f"Registration failed: {register_response.text}")
            register_response.failure(f"Registration failed: {register_response.status_code}")
            raise StopUser()
        
        # Login user
        login_data = {
            "username": username,
            "password": password
        }
        
        login_response = self.client.post(
            "/api/auth/login",
            json=login_data,
            catch_response=True,
            name="login_user"
        )
        
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.text}")
            login_response.failure(f"Login failed: {login_response.status_code}")
            raise StopUser()
        
        login_data = login_response.json()
        self.auth_token = login_data.get("access_token")
        self.user_id = login_data.get("user_id")
        
        if not self.auth_token:
            logger.error("No access token received")
            login_response.failure("No access token received")
            raise StopUser()
        
        # Set authorization header for future requests
        self.client.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        
        logger.info(f"User {username} registered and logged in successfully")
    
    @task(10)
    def view_dashboard(self):
        """Access user dashboard - high frequency task"""
        response = self.client.get(
            "/api/user/dashboard",
            catch_response=True,
            name="view_dashboard"
        )
        
        if response.status_code != 200:
            response.failure(f"Dashboard access failed: {response.status_code}")
    
    @task(8)
    def get_user_stats(self):
        """Get user statistics"""
        response = self.client.get(
            "/api/user/stats",
            catch_response=True,
            name="get_user_stats"
        )
        
        if response.status_code != 200:
            response.failure(f"Stats access failed: {response.status_code}")
    
    @task(6)
    def list_jobs(self):
        """List user's transcription jobs"""
        response = self.client.get(
            "/api/jobs/",
            catch_response=True,
            name="list_jobs"
        )
        
        if response.status_code != 200:
            response.failure(f"Job listing failed: {response.status_code}")
    
    @task(5)
    def get_job_status(self):
        """Get status of a specific job (if any exist)"""
        # First get list of jobs
        jobs_response = self.client.get("/api/jobs/")
        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            if jobs.get("jobs"):
                job_id = jobs["jobs"][0]["id"]
                response = self.client.get(
                    f"/api/jobs/{job_id}",
                    catch_response=True,
                    name="get_job_status"
                )
                
                if response.status_code != 200:
                    response.failure(f"Job status failed: {response.status_code}")
    
    @task(3)
    def upload_small_file(self):
        """Upload a small test audio file"""
        # Generate a small dummy audio file (WAV header + silence)
        audio_data = self.generate_dummy_audio(duration=5)
        
        files = {
            "file": ("test_audio.wav", audio_data, "audio/wav")
        }
        
        response = self.client.post(
            "/api/upload/",
            files=files,
            catch_response=True,
            name="upload_small_file"
        )
        
        if response.status_code not in [200, 201, 202]:
            response.failure(f"Upload failed: {response.status_code}")
    
    @task(2)
    def upload_medium_file(self):
        """Upload a medium test audio file"""
        audio_data = self.generate_dummy_audio(duration=30)
        
        files = {
            "file": ("test_medium_audio.wav", audio_data, "audio/wav")
        }
        
        response = self.client.post(
            "/api/upload/",
            files=files,
            catch_response=True,
            name="upload_medium_file"
        )
        
        if response.status_code not in [200, 201, 202]:
            response.failure(f"Medium upload failed: {response.status_code}")
    
    @task(1)
    def upload_large_file(self):
        """Upload a large test audio file"""
        audio_data = self.generate_dummy_audio(duration=120)
        
        files = {
            "file": ("test_large_audio.wav", audio_data, "audio/wav")
        }
        
        response = self.client.post(
            "/api/upload/",
            files=files,
            catch_response=True,
            name="upload_large_file"
        )
        
        if response.status_code not in [200, 201, 202]:
            response.failure(f"Large upload failed: {response.status_code}")
    
    @task(2)
    def test_api_endpoints(self):
        """Test various API endpoints"""
        endpoints = [
            ("/api/health", "health_check"),
            ("/api/models", "list_models"),
            ("/api/user/settings", "user_settings"),
        ]
        
        endpoint, name = random.choice(endpoints)
        response = self.client.get(
            endpoint,
            catch_response=True,
            name=name
        )
        
        if response.status_code != 200:
            response.failure(f"{name} failed: {response.status_code}")
    
    def generate_dummy_audio(self, duration=10, sample_rate=44100):
        """Generate a dummy WAV file for testing"""
        import struct
        
        # WAV file parameters
        channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        
        # Calculate data size
        num_samples = duration * sample_rate
        data_size = num_samples * block_align
        file_size = 36 + data_size
        
        # Create WAV header
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF',           # ChunkID
            file_size,         # ChunkSize
            b'WAVE',           # Format
            b'fmt ',           # Subchunk1ID
            16,                # Subchunk1Size
            1,                 # AudioFormat (PCM)
            channels,          # NumChannels
            sample_rate,       # SampleRate
            byte_rate,         # ByteRate
            block_align,       # BlockAlign
            bits_per_sample,   # BitsPerSample
            b'data',           # Subchunk2ID
            data_size          # Subchunk2Size
        )
        
        # Generate silent audio data
        audio_data = b'\x00' * data_size
        
        return wav_header + audio_data

class AdminUser(HttpUser):
    """
    Admin user for testing admin endpoints
    """
    
    wait_time = between(5, 15)  # Longer wait time for admin tasks
    weight = 1  # Lower weight (fewer admin users)
    
    def on_start(self):
        """Login as admin user"""
        self.login_admin()
    
    def login_admin(self):
        """Login with admin credentials"""
        admin_data = {
            "username": os.getenv("ADMIN_USERNAME", "admin"),
            "password": os.getenv("ADMIN_PASSWORD", "admin123")
        }
        
        response = self.client.post(
            "/api/auth/login",
            json=admin_data,
            catch_response=True,
            name="admin_login"
        )
        
        if response.status_code != 200:
            logger.error(f"Admin login failed: {response.text}")
            response.failure(f"Admin login failed: {response.status_code}")
            raise StopUser()
        
        login_data = response.json()
        auth_token = login_data.get("access_token")
        
        if not auth_token:
            response.failure("No access token received")
            raise StopUser()
        
        self.client.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
    
    @task(5)
    def admin_dashboard(self):
        """Access admin dashboard"""
        response = self.client.get(
            "/api/admin/dashboard",
            catch_response=True,
            name="admin_dashboard"
        )
        
        if response.status_code != 200:
            response.failure(f"Admin dashboard failed: {response.status_code}")
    
    @task(3)
    def admin_stats(self):
        """Get admin statistics"""
        response = self.client.get(
            "/api/admin/stats",
            catch_response=True,
            name="admin_stats"
        )
        
        if response.status_code != 200:
            response.failure(f"Admin stats failed: {response.status_code}")
    
    @task(3)
    def admin_users(self):
        """List all users"""
        response = self.client.get(
            "/api/admin/users",
            catch_response=True,
            name="admin_users"
        )
        
        if response.status_code != 200:
            response.failure(f"Admin users listing failed: {response.status_code}")
    
    @task(2)
    def admin_jobs(self):
        """List all jobs"""
        response = self.client.get(
            "/api/admin/jobs",
            catch_response=True,
            name="admin_jobs"
        )
        
        if response.status_code != 200:
            response.failure(f"Admin jobs listing failed: {response.status_code}")
    
    @task(1)
    def system_health(self):
        """Check system health"""
        response = self.client.get(
            "/api/admin/health",
            catch_response=True,
            name="system_health"
        )
        
        if response.status_code != 200:
            response.failure(f"System health check failed: {response.status_code}")

class StressTestUser(HttpUser):
    """
    High-intensity stress testing user
    """
    
    wait_time = between(0.1, 1)  # Very short wait time
    weight = 1  # Lower weight for stress testing
    
    def on_start(self):
        """Quick setup for stress testing"""
        self.auth_token = None
        self.quick_login()
    
    def quick_login(self):
        """Quick login for stress testing"""
        user_number = random.randint(10000, 99999)
        username = f"stress_user_{user_number}"
        password = "StressTest123!"
        
        # Try to login directly (user might already exist)
        login_data = {"username": username, "password": password}
        response = self.client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            auth_token = response.json().get("access_token")
            if auth_token:
                self.client.headers.update({"Authorization": f"Bearer {auth_token}"})
                return
        
        # If login fails, register and login
        register_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "confirm_password": password
        }
        
        self.client.post("/api/auth/register", json=register_data)
        response = self.client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            auth_token = response.json().get("access_token")
            if auth_token:
                self.client.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    @task(10)
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/api/health", name="rapid_health")
    
    @task(8)
    def rapid_dashboard_access(self):
        """Rapid dashboard access"""
        self.client.get("/api/user/dashboard", name="rapid_dashboard")
    
    @task(5)
    def rapid_api_calls(self):
        """Rapid API calls"""
        endpoints = ["/api/models", "/api/user/stats", "/api/jobs/"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name="rapid_api")

# Event handlers for custom statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info("Load test starting...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info("Load test completed.")
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"RPS: {stats.total.current_rps:.2f}")

# Custom task sets for different test scenarios
class LoadTestTaskSet:
    """Task set configurations for different load test scenarios"""
    
    @staticmethod
    def light_load():
        """Configuration for light load testing"""
        return {
            "users": 10,
            "spawn_rate": 2,
            "run_time": "5m"
        }
    
    @staticmethod
    def medium_load():
        """Configuration for medium load testing"""
        return {
            "users": 50,
            "spawn_rate": 5,
            "run_time": "10m"
        }
    
    @staticmethod
    def heavy_load():
        """Configuration for heavy load testing"""
        return {
            "users": 100,
            "spawn_rate": 10,
            "run_time": "15m"
        }
    
    @staticmethod
    def stress_test():
        """Configuration for stress testing"""
        return {
            "users": 200,
            "spawn_rate": 20,
            "run_time": "20m"
        }

if __name__ == "__main__":
    # This allows running the script directly for testing
    import subprocess
    import sys
    
    # Default configuration
    config = LoadTestTaskSet.medium_load()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "light":
            config = LoadTestTaskSet.light_load()
        elif test_type == "heavy":
            config = LoadTestTaskSet.heavy_load()
        elif test_type == "stress":
            config = LoadTestTaskSet.stress_test()
    
    # Run locust with the configuration
    cmd = [
        "locust",
        "--users", str(config["users"]),
        "--spawn-rate", str(config["spawn_rate"]),
        "--run-time", config["run_time"],
        "--host", "http://localhost:8000"
    ]
    
    logger.info(f"Running load test with config: {config}")
    subprocess.run(cmd)