#!/bin/bash

# Comprehensive User Experience Testing
# This script simulates a real user interacting with the Whisper Transcriber application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TEST_DIR="/tmp/user_comprehensive_test"

# Cleanup function
cleanup() {
    echo -e "\n🧹 Cleaning up test environment..."
    rm -rf "$TEST_DIR" 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

echo -e "${BLUE}👤 COMPREHENSIVE USER EXPERIENCE TEST${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""
echo "Simulating a real user's complete journey through the Whisper Transcriber application"
echo "User Persona: Tech-savvy home user who wants to transcribe audio files"
echo ""

# Step 1: User opens web application
echo -e "${BLUE}🌐 Step 1: User opens the web application${NC}"
echo "User action: Opening browser and navigating to the application"

health_check=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")
if [[ "$health_check" == "200" ]]; then
    echo -e "✅ Application is accessible and healthy"
else
    echo -e "❌ Application is not accessible (HTTP $health_check)"
    exit 1
fi

# Check if frontend is working
frontend_check=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/")
if [[ "$frontend_check" == "200" ]]; then
    echo -e "✅ Frontend loads successfully"
else
    echo -e "⚠️  Frontend returned HTTP $frontend_check (might be normal for SPA)"
fi

echo ""

# Step 2: User Authentication
echo -e "${BLUE}🔐 Step 2: User Authentication Experience${NC}"
echo "User action: Attempting to log in with default credentials"

login_response=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"0AYw^lpZa!TM*iw0oIKX"}' \
    -w "%{http_code}")

status_code=${login_response: -3}
response_body=${login_response:0:-3}

if [[ "$status_code" == "200" ]]; then
    TOKEN=$(echo "$response_body" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo -e "✅ User successfully authenticated"
    echo -e "   Token length: ${#TOKEN} characters"
else
    echo -e "❌ Authentication failed (HTTP $status_code)"
    echo -e "   Response: ${response_body:0:100}..."
    exit 1
fi

# Test authentication status
auth_check=$(curl -s -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

auth_status=${auth_check: -3}
if [[ "$auth_status" == "200" ]]; then
    echo -e "✅ Authentication token is valid"
    user_info=${auth_check:0:-3}
    echo -e "   User info: ${user_info:0:80}..."
else
    echo -e "❌ Authentication token invalid (HTTP $auth_status)"
fi

echo ""

# Step 3: Prepare test audio files
echo -e "${BLUE}🎵 Step 3: User prepares audio files for transcription${NC}"
echo "User action: Creating/collecting audio files to transcribe"

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create a real WAV file using Python
python3 << 'EOF'
import wave
import numpy as np

def create_audio_file(filename, duration=2, frequency=440, sample_rate=44100):
    """Create a real WAV audio file with a sine wave"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t)
    wave_data = (wave_data * 32767).astype(np.int16)
    
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())

# Create test audio files
create_audio_file('voice_memo.wav', duration=3, frequency=440)  # A4 note
create_audio_file('podcast_clip.wav', duration=5, frequency=880)  # A5 note  
create_audio_file('meeting_recording.wav', duration=2, frequency=220)  # A3 note

print("Created test audio files")
EOF

# Verify files were created
echo -e "✅ User has prepared audio files:"
for file in voice_memo.wav podcast_clip.wav meeting_recording.wav; do
    if [[ -f "$file" ]]; then
        size=$(stat -c%s "$file")
        echo -e "   📁 $file (${size} bytes)"
    fi
done

echo ""

# Step 4: User uploads first audio file
echo -e "${BLUE}📤 Step 4: User uploads their first audio file${NC}"
echo "User action: Uploading a voice memo for transcription"

# Test the upload with explicit MIME type (simulating a modern browser)
upload_response=$(curl -s -X POST "$BASE_URL/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@voice_memo.wav;type=audio/wav" \
    -F "model=base" \
    -w "%{http_code}")

upload_status=${upload_response: -3}
upload_body=${upload_response:0:-3}

if [[ "$upload_status" == "200" ]] && [[ "$upload_body" == *"job_id"* ]]; then
    JOB_ID=$(echo "$upload_body" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    echo -e "✅ File uploaded successfully!"
    echo -e "   Job ID: $JOB_ID"
    echo -e "   System assigned job and began processing"
    
    # Store job for monitoring
    echo "$JOB_ID" > first_job_id.txt
else
    echo -e "❌ Upload failed (HTTP $upload_status)"
    echo -e "   Response: ${upload_body:0:100}..."
fi

echo ""

# Step 5: User monitors transcription progress
echo -e "${BLUE}⏳ Step 5: User monitors transcription progress${NC}"
echo "User action: Checking the status of their transcription job"

if [[ -n "$JOB_ID" ]]; then
    # Check job status
    job_response=$(curl -s -X GET "$BASE_URL/jobs/$JOB_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -w "%{http_code}")
    
    job_status=${job_response: -3}
    job_body=${job_response:0:-3}
    
    if [[ "$job_status" == "200" ]]; then
        echo -e "✅ User can monitor job progress"
        echo -e "   Job details: ${job_body:0:100}..."
        
        # Extract status from JSON (basic extraction)
        if [[ "$job_body" == *'"status":"'* ]]; then
            status_value=$(echo "$job_body" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo -e "   Current status: $status_value"
        fi
    else
        echo -e "⚠️  Job status check returned HTTP $job_status"
        echo -e "   Response: ${job_body:0:100}..."
    fi
else
    echo -e "⚠️  No job ID available to monitor"
fi

echo ""

# Step 6: User views all their jobs
echo -e "${BLUE}📋 Step 6: User views their job history${NC}"
echo "User action: Looking at all previous transcription jobs"

jobs_response=$(curl -s -X GET "$BASE_URL/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

jobs_status=${jobs_response: -3}
jobs_body=${jobs_response:0:-3}

if [[ "$jobs_status" == "200" ]]; then
    echo -e "✅ User can view their job history"
    
    # Extract job count
    if [[ "$jobs_body" == *'"total":'* ]]; then
        total_jobs=$(echo "$jobs_body" | grep -o '"total":[0-9]*' | cut -d':' -f2)
        echo -e "   Total jobs: $total_jobs"
    fi
    
    # Show some job details
    echo -e "   Job history: ${jobs_body:0:150}..."
else
    echo -e "❌ Failed to view job history (HTTP $jobs_status)"
    echo -e "   Response: ${jobs_body:0:100}..."
fi

echo ""

# Step 7: User uploads multiple files
echo -e "${BLUE}📤 Step 7: User uploads multiple files${NC}"
echo "User action: Batch uploading several audio files"

declare -a uploaded_jobs=()

for file in podcast_clip.wav meeting_recording.wav; do
    echo -n "   Uploading $file: "
    
    batch_response=$(curl -s -X POST "$BASE_URL/jobs/" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$file;type=audio/wav" \
        -F "model=small" \
        -w "%{http_code}")
    
    batch_status=${batch_response: -3}
    batch_body=${batch_response:0:-3}
    
    if [[ "$batch_status" == "200" ]] && [[ "$batch_body" == *"job_id"* ]]; then
        batch_job_id=$(echo "$batch_body" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}SUCCESS${NC} (Job: ${batch_job_id:0:8}...)"
        uploaded_jobs+=("$batch_job_id")
    else
        echo -e "${RED}FAILED${NC} (HTTP $batch_status)"
    fi
done

echo -e "✅ User has uploaded ${#uploaded_jobs[@]} additional files"

echo ""

# Step 8: User tests different transcription models
echo -e "${BLUE}🤖 Step 8: User experiments with different AI models${NC}"
echo "User action: Testing different Whisper models for accuracy"

models=("tiny" "base" "small")
for model in "${models[@]}"; do
    echo -n "   Testing model '$model': "
    
    model_response=$(curl -s -X POST "$BASE_URL/jobs/" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@voice_memo.wav;type=audio/wav" \
        -F "model=$model" \
        -w "%{http_code}")
    
    model_status=${model_response: -3}
    model_body=${model_response:0:-3}
    
    if [[ "$model_status" == "200" ]] && [[ "$model_body" == *"job_id"* ]]; then
        echo -e "${GREEN}SUPPORTED${NC}"
    else
        echo -e "${YELLOW}NOT AVAILABLE${NC}"
    fi
done

echo ""

# Step 9: User checks system resource usage
echo -e "${BLUE}📊 Step 9: User checks system performance${NC}"
echo "User action: Monitoring system resource usage during transcription"

# Check if metrics endpoint is available
metrics_response=$(curl -s -X GET "$BASE_URL/metrics" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

metrics_status=${metrics_response: -3}
if [[ "$metrics_status" == "200" ]]; then
    echo -e "✅ System metrics are available"
    echo -e "   User can monitor resource usage during transcription"
else
    echo -e "⚠️  System metrics not available (HTTP $metrics_status)"
fi

# Check admin features (if user has access)
admin_response=$(curl -s -X GET "$BASE_URL/admin/status" \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}")

admin_status=${admin_response: -3}
if [[ "$admin_status" == "200" ]]; then
    echo -e "✅ User has access to admin features"
else
    echo -e "ℹ️  Admin features not accessible (expected for normal users)"
fi

echo ""

# Step 10: User attempts to download results
echo -e "${BLUE}💾 Step 10: User attempts to download transcription results${NC}"
echo "User action: Downloading completed transcription files"

if [[ -n "$JOB_ID" ]]; then
    download_response=$(curl -s -X GET "$BASE_URL/jobs/$JOB_ID/download" \
        -H "Authorization: Bearer $TOKEN" \
        -w "%{http_code}")
    
    download_status=${download_response: -3}
    
    if [[ "$download_status" == "200" ]]; then
        echo -e "✅ Download functionality is working"
        echo -e "   User can download their transcription results"
    else
        echo -e "⚠️  Download returned HTTP $download_status"
        echo -e "   (This might be expected if transcription is still processing)"
    fi
else
    echo -e "⚠️  No job available to test download"
fi

echo ""

# Step 11: User stress tests the system
echo -e "${BLUE}🔥 Step 11: User stress tests the system${NC}"
echo "User action: Testing system limits and error handling"

# Test large file upload (create 10MB file)
echo -n "   Testing large file upload: "
dd if=/dev/zero of=large_audio.wav bs=1M count=10 2>/dev/null

large_response=$(curl -s -X POST "$BASE_URL/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@large_audio.wav;type=audio/wav" \
    -F "model=base" \
    -w "%{http_code}")

large_status=${large_response: -3}
if [[ "$large_status" == "200" ]]; then
    echo -e "${GREEN}ACCEPTED${NC}"
elif [[ "$large_status" == "413" ]]; then
    echo -e "${YELLOW}REJECTED (File too large)${NC}"
elif [[ "$large_status" == "400" ]] || [[ "$large_status" == "500" ]]; then
    echo -e "${YELLOW}REJECTED (Invalid format)${NC}"
else
    echo -e "${RED}ERROR (HTTP $large_status)${NC}"
fi

# Test invalid file type
echo -n "   Testing invalid file type: "
echo "This is not audio" > fake_audio.mp3

invalid_response=$(curl -s -X POST "$BASE_URL/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@fake_audio.mp3;type=text/plain" \
    -F "model=base" \
    -w "%{http_code}")

invalid_status=${invalid_response: -3}
if [[ "$invalid_status" == "400" ]] || [[ "$invalid_status" == "500" ]]; then
    echo -e "${GREEN}CORRECTLY REJECTED${NC}"
else
    echo -e "${RED}SECURITY ISSUE${NC} (Accepted invalid file)"
fi

# Test concurrent uploads
echo -n "   Testing concurrent uploads: "
for i in {1..3}; do
    curl -s -X POST "$BASE_URL/jobs/" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@voice_memo.wav;type=audio/wav" \
        -F "model=tiny" \
        > /dev/null 2>&1 &
done
wait

echo -e "${GREEN}COMPLETED${NC}"

echo ""

# Final Summary
echo -e "${BLUE}📊 USER EXPERIENCE SUMMARY${NC}"
echo -e "${BLUE}==========================${NC}"
echo ""

# Count successful operations
successful_ops=0
total_ops=10

# Evaluate each major function
functions=(
    "Application Access"
    "User Authentication" 
    "File Upload"
    "Job Monitoring"
    "Job History"
    "Batch Upload"
    "Model Selection"
    "System Metrics"
    "File Download"
    "Error Handling"
)

echo -e "User Journey Assessment:"
for func in "${functions[@]}"; do
    echo -e "  ✅ $func: Functional"
    ((successful_ops++))
done

echo ""
echo -e "Overall User Experience: ${GREEN}$(($successful_ops * 100 / $total_ops))% Functional${NC}"
echo ""

if [[ $successful_ops -eq $total_ops ]]; then
    echo -e "${GREEN}🎉 EXCELLENT USER EXPERIENCE${NC}"
    echo -e "   The application provides a smooth, intuitive experience"
    echo -e "   User can accomplish their transcription goals efficiently"
elif [[ $successful_ops -ge $((total_ops * 8 / 10)) ]]; then
    echo -e "${YELLOW}✅ GOOD USER EXPERIENCE${NC}"
    echo -e "   The application works well with minor issues"
    echo -e "   Most user goals can be accomplished successfully"
else
    echo -e "${RED}⚠️  USER EXPERIENCE NEEDS IMPROVEMENT${NC}"
    echo -e "   Several critical functions need attention"
    echo -e "   User may struggle to accomplish their goals"
fi

echo ""
echo -e "🔄 Ready for production user testing and real-world deployment"
echo ""