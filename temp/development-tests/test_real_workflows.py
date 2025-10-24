#!/usr/bin/env python3
"""
Real User Workflow Testing
Tests actual end-to-end user scenarios that production users will execute
"""

import os
import sys
import time
import json
import tempfile
import requests
from pathlib import Path
from pydub import AudioSegment
import numpy as np

# Add project path
sys.path.insert(0, str(Path.cwd()))

def create_test_audio_file(duration_seconds=5, sample_rate=16000):
    """Create a synthetic audio file for testing"""
    # Generate sine wave test audio
    frequency = 440  # A4 note
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
    audio_data = np.sin(frequency * 2 * np.pi * t)
    
    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # Create AudioSegment and export
        audio = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        audio.export(f.name, format='wav')
        return f.name

class RealWorkflowTester:
    def __init__(self, base_url="http://localhost:8020"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_complete_transcription_workflow(self):
        """Test: Upload → Process → Download complete workflow"""
        print("🔄 Testing Complete Transcription Workflow...")
        
        # Step 1: Create test audio
        audio_file = create_test_audio_file(duration_seconds=3)
        try:
            print(f"  📁 Created test audio: {audio_file}")
            
            # Step 2: Upload file
            with open(audio_file, 'rb') as f:
                files = {'file': ('test.wav', f, 'audio/wav')}
                data = {'model': 'tiny'}  # Use fastest model for testing
                
                response = self.session.post(f"{self.base_url}/jobs", files=files, data=data)
                print(f"  📤 Upload response: {response.status_code}")
                
                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data.get('job_id')
                    print(f"  ✅ Job created: {job_id}")
                    
                    # Step 3: Poll job status
                    return self._poll_job_completion(job_id)
                else:
                    print(f"  ❌ Upload failed: {response.text}")
                    return False
                    
        finally:
            # Cleanup
            if os.path.exists(audio_file):
                os.unlink(audio_file)
    
    def _poll_job_completion(self, job_id, timeout=30):
        """Poll job until completion or timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.session.get(f"{self.base_url}/jobs/{job_id}")
            if response.status_code == 200:
                job_status = response.json()
                status = job_status.get('status')
                print(f"  ⏳ Job status: {status}")
                
                if status == 'completed':
                    print(f"  ✅ Transcription completed!")
                    transcript_text = job_status.get('transcript_text', '')
                    print(f"  📝 Transcript: '{transcript_text[:100]}...'")
                    
                    # Test download
                    return self._test_transcript_download(job_id)
                elif status == 'failed':
                    print(f"  ❌ Job failed: {job_status.get('error')}")
                    return False
                    
            time.sleep(1)
        
        print(f"  ⏰ Job timed out after {timeout}s")
        return False
    
    def _test_transcript_download(self, job_id):
        """Test transcript download functionality"""
        formats = ['txt', 'json', 'srt']
        for fmt in formats:
            response = self.session.get(f"{self.base_url}/jobs/{job_id}/transcript?format={fmt}")
            if response.status_code == 200:
                print(f"  📄 Downloaded {fmt} format: {len(response.content)} bytes")
            else:
                print(f"  ❌ Failed to download {fmt}: {response.status_code}")
                return False
        return True
    
    def test_multiple_concurrent_uploads(self, num_jobs=3):
        """Test concurrent file uploads to stress job queue"""
        print(f"🚀 Testing {num_jobs} Concurrent Uploads...")
        
        job_ids = []
        # Start multiple uploads
        for i in range(num_jobs):
            audio_file = create_test_audio_file(duration_seconds=2)
            try:
                with open(audio_file, 'rb') as f:
                    files = {'file': (f'test_{i}.wav', f, 'audio/wav')}
                    data = {'model': 'tiny'}
                    
                    response = self.session.post(f"{self.base_url}/jobs", files=files, data=data)
                    if response.status_code == 200:
                        job_id = response.json().get('job_id')
                        job_ids.append(job_id)
                        print(f"  📤 Started job {i+1}: {job_id}")
                    else:
                        print(f"  ❌ Upload {i+1} failed: {response.status_code}")
                        
            finally:
                os.unlink(audio_file)
        
        # Monitor all jobs
        completed = 0
        timeout = 60
        start_time = time.time()
        
        while completed < len(job_ids) and time.time() - start_time < timeout:
            for job_id in job_ids:
                response = self.session.get(f"{self.base_url}/jobs/{job_id}")
                if response.status_code == 200:
                    status = response.json().get('status')
                    if status == 'completed':
                        completed += 1
                        print(f"  ✅ Job {job_id} completed ({completed}/{len(job_ids)})")
            time.sleep(2)
        
        success_rate = completed / len(job_ids) * 100
        print(f"  📊 Concurrent test: {completed}/{len(job_ids)} completed ({success_rate:.1f}%)")
        return success_rate > 80
    
    def test_error_conditions(self):
        """Test various error conditions and edge cases"""
        print("⚠️  Testing Error Conditions...")
        
        tests = [
            self._test_invalid_file_upload,
            self._test_oversized_file,
            self._test_invalid_model_request,
            self._test_nonexistent_job_query
        ]
        
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
        
        print(f"  📊 Error testing: {passed}/{len(tests)} passed")
        return passed == len(tests)
    
    def _test_invalid_file_upload(self):
        """Test uploading non-audio file"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is not an audio file")
            f.flush()
            
            try:
                with open(f.name, 'rb') as upload_file:
                    files = {'file': ('test.txt', upload_file, 'text/plain')}
                    response = self.session.post(f"{self.base_url}/jobs", files=files)
                    
                expected_failure = response.status_code in [400, 422, 415]  # Bad request, validation error, unsupported media
                print(f"  🔍 Invalid file test: {'✅' if expected_failure else '❌'} (status: {response.status_code})")
                return expected_failure
            finally:
                os.unlink(f.name)
    
    def _test_oversized_file(self):
        """Test uploading file larger than limit"""
        # Create a 1MB dummy file (assuming limit is smaller)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'0' * (1024 * 1024))  # 1MB of zeros
            f.flush()
            
            try:
                with open(f.name, 'rb') as upload_file:
                    files = {'file': ('large.wav', upload_file, 'audio/wav')}
                    response = self.session.post(f"{self.base_url}/jobs", files=files)
                    
                expected_failure = response.status_code in [413, 400]  # Payload too large
                print(f"  📏 Oversized file test: {'✅' if expected_failure else '❌'} (status: {response.status_code})")
                return expected_failure
            finally:
                os.unlink(f.name)
    
    def _test_invalid_model_request(self):
        """Test requesting non-existent model"""
        audio_file = create_test_audio_file(duration_seconds=1)
        try:
            with open(audio_file, 'rb') as f:
                files = {'file': ('test.wav', f, 'audio/wav')}
                data = {'model': 'nonexistent-model'}
                
                response = self.session.post(f"{self.base_url}/jobs", files=files, data=data)
                expected_failure = response.status_code in [400, 422]
                print(f"  🤖 Invalid model test: {'✅' if expected_failure else '❌'} (status: {response.status_code})")
                return expected_failure
        finally:
            os.unlink(audio_file)
    
    def _test_nonexistent_job_query(self):
        """Test querying job that doesn't exist"""
        response = self.session.get(f"{self.base_url}/jobs/nonexistent-job-id")
        expected_failure = response.status_code in [404, 400]
        print(f"  🔍 Nonexistent job test: {'✅' if expected_failure else '❌'} (status: {response.status_code})")
        return expected_failure

def main():
    """Run comprehensive real workflow testing"""
    print("🧪 REAL USER WORKFLOW TESTING")
    print("=" * 50)
    
    tester = RealWorkflowTester()
    
    # Check if API is running
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running! Please start the server first.")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API! Please start the server first.")
        return False
    
    print("✅ API is running, starting tests...\n")
    
    tests = [
        ("Complete Transcription Workflow", tester.test_complete_transcription_workflow),
        ("Concurrent Upload Stress Test", tester.test_multiple_concurrent_uploads),
        ("Error Condition Handling", tester.test_error_conditions)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print(f"\n{'='*50}")
    print("📊 REAL WORKFLOW TEST RESULTS:")
    
    passed = 0
    total = len(results)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} real workflow tests passed")
    
    if passed == total:
        print("🎉 ALL REAL USER WORKFLOWS WORKING! Production ready.")
        return True
    else:
        print("⚠️  Some workflows failed. Review issues before production deployment.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)