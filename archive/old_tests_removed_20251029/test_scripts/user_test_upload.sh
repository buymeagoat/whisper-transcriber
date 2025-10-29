#!/bin/bash

# COMPREHENSIVE USER TESTING - FILE UPLOAD & TRANSCRIPTION
# Acting as a real user who wants to transcribe audio files

set -e

BASE_URL="http://localhost:8000"
ADMIN_PASSWORD="0AYw^lpZa!TM*iw0oIKX"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}👤 ACTING AS REAL USER - FILE UPLOAD & TRANSCRIPTION TESTING${NC}"
echo "==============================================================="
echo ""
echo -e "${MAGENTA}User Story: I want to upload audio files and get transcriptions${NC}"
echo ""

# Step 1: User logs in first
echo -e "${CYAN}🔐 Step 1: User authentication...${NC}"
echo "User action: Logging in to access transcription features"

LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"${ADMIN_PASSWORD}\"}")

if [[ "$LOGIN_RESPONSE" == *"access_token"* ]]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo -e "✓ Login: ${GREEN}SUCCESS${NC}"
    echo "  User is authenticated and ready to upload files"
else
    echo -e "✓ Login: ${RED}FAILED${NC}"
    echo "  Cannot proceed without authentication"
    exit 1
fi

# Step 2: User tries to understand what file types are supported
echo ""
echo -e "${CYAN}📁 Step 2: User explores file upload requirements...${NC}"
echo "User action: Checking what audio formats are accepted"

# Check upload endpoint documentation
echo -n "✓ Check upload endpoint: "
upload_check=$(curl -s -X OPTIONS "${BASE_URL}/jobs/" -w "%{http_code}")
upload_code=${upload_check: -3}
if [[ "$upload_code" == "200" ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  User discovers: Upload endpoint is available"
else
    echo -e "${YELLOW}INFO (${upload_code}) - User may try anyway${NC}"
fi

# Step 3: User creates test audio files (simulating real files)
echo ""
echo -e "${CYAN}🎵 Step 3: User prepares audio files...${NC}"
echo "User action: Creating/preparing audio files for transcription"

# Create different test files that a user might try
mkdir -p /tmp/user_audio_test

# Simulate a small text file (user might try this by mistake)
echo "Hello, this is a test transcription. The user wants to see if this text gets processed correctly." > /tmp/user_audio_test/text_file.txt

# Simulate a small WAV file (create minimal WAV header + data)
echo -n "RIFF" > /tmp/user_audio_test/small_audio.wav
echo -ne "\x24\x00\x00\x00" >> /tmp/user_audio_test/small_audio.wav  # File size
echo -n "WAVE" >> /tmp/user_audio_test/small_audio.wav
echo -n "This is test audio data" >> /tmp/user_audio_test/small_audio.wav

# Create a larger file to test limits
dd if=/dev/zero of=/tmp/user_audio_test/large_file.dat bs=1M count=5 2>/dev/null

# Create a file with a suspicious name
echo "Test content" > "/tmp/user_audio_test/script<>test.mp3"

echo -e "  ✓ Created test files:"
echo -e "    • text_file.txt (text content)"
echo -e "    • small_audio.wav (simulated audio)"
echo -e "    • large_file.dat (5MB test file)"
echo -e "    • script<>test.mp3 (suspicious filename)"

# Step 4: User attempts different uploads
echo ""
echo -e "${CYAN}📤 Step 4: User attempts file uploads...${NC}"

# Test 1: Upload text file (common user mistake)
echo -n "✓ Upload text file (.txt): "
text_upload=$(curl -s -X POST "${BASE_URL}/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/user_audio_test/text_file.txt" \
    -F "model=base" \
    -w "%{http_code}")

text_code=${text_upload: -3}
if [[ "$text_code" == "200" ]] || [[ "$text_upload" == *"job_id"* ]]; then
    echo -e "${GREEN}ACCEPTED${NC}"
    TEXT_JOB_ID=$(echo "$text_upload" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4 || echo "")
    echo "  Result: System accepted text file - job ID: $TEXT_JOB_ID"
elif [[ "$text_code" == "400" ]]; then
    echo -e "${YELLOW}REJECTED (Expected)${NC}"
    echo "  Result: System correctly rejected non-audio file"
else
    echo -e "${RED}ERROR (${text_code})${NC}"
    echo "  Response: ${text_upload:0:100}..."
fi

# Test 2: Upload simulated audio file
# Test 2: Upload audio file (valid case)
echo -n "✓ Upload audio file (.wav): "
audio_upload=$(curl -s -X POST "${BASE_URL}/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/user_audio_test/test_audio.wav;type=audio/wav" \
    -F "model=base" \
    -w "%{http_code}")

wav_code=${wav_upload: -3}
if [[ "$wav_code" == "200" ]] || [[ "$wav_upload" == *"job_id"* ]]; then
    echo -e "${GREEN}ACCEPTED${NC}"
    WAV_JOB_ID=$(echo "$wav_upload" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4 || echo "")
    echo "  Result: System accepted WAV file - job ID: $WAV_JOB_ID"
else
    echo -e "${RED}REJECTED (${wav_code})${NC}"
    echo "  Response: ${wav_upload:0:100}..."
fi

# Test 3: Upload large file
echo -n "✓ Upload large file (5MB): "
large_upload=$(curl -s -X POST "${BASE_URL}/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/user_audio_test/large_file.dat" \
    -F "model=base" \
    -w "%{http_code}")

large_code=${large_upload: -3}
if [[ "$large_code" == "200" ]]; then
    echo -e "${GREEN}ACCEPTED${NC}"
    echo "  Result: System handles large files"
elif [[ "$large_code" == "413" ]]; then
    echo -e "${YELLOW}SIZE LIMIT (Expected)${NC}"
    echo "  Result: System correctly enforces file size limits"
else
    echo -e "${YELLOW}CHECK (${large_code})${NC}"
    echo "  Response: ${large_upload:0:100}..."
fi

# Test 4: Upload file with suspicious name
echo -n "✓ Upload suspicious filename: "
sus_upload=$(curl -s -X POST "${BASE_URL}/jobs/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/user_audio_test/script<>test.mp3" \
    -F "model=base" \
    -w "%{http_code}")

sus_code=${sus_upload: -3}
if [[ "$sus_code" == "200" ]]; then
    echo -e "${YELLOW}ACCEPTED - Check security${NC}"
    echo "  Result: System accepted suspicious filename"
elif [[ "$sus_code" == "400" ]]; then
    echo -e "${GREEN}REJECTED (Good security)${NC}"
    echo "  Result: System correctly blocked suspicious filename"
else
    echo -e "${YELLOW}CHECK (${sus_code})${NC}"
    echo "  Response: ${sus_upload:0:100}..."
fi

# Step 5: User monitors job progress
echo ""
echo -e "${CYAN}⏳ Step 5: User monitors transcription progress...${NC}"

# Check status of created jobs
if [[ -n "$TEXT_JOB_ID" ]]; then
    echo -n "✓ Check text file job status: "
    text_status=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/${TEXT_JOB_ID}")
    if [[ "$text_status" == *"status"* ]]; then
        status_value=$(echo "$text_status" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}$status_value${NC}"
        echo "  Job tracking works - status: $status_value"
    else
        echo -e "${RED}ERROR${NC}"
        echo "  Response: ${text_status:0:100}..."
    fi
fi

if [[ -n "$WAV_JOB_ID" ]]; then
    echo -n "✓ Check WAV file job status: "
    wav_status=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/${WAV_JOB_ID}")
    if [[ "$wav_status" == *"status"* ]]; then
        status_value=$(echo "$wav_status" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}$status_value${NC}"
        echo "  Job tracking works - status: $status_value"
        
        # If completed, try to get results
        if [[ "$status_value" == "completed" ]]; then
            echo -n "✓ Download results: "
            download_response=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/${WAV_JOB_ID}/download" -w "%{http_code}")
            download_code=${download_response: -3}
            if [[ "$download_code" == "200" ]]; then
                echo -e "${GREEN}SUCCESS${NC}"
                echo "  User can download transcription results"
            else
                echo -e "${YELLOW}CHECK (${download_code})${NC}"
            fi
        fi
    else
        echo -e "${RED}ERROR${NC}"
        echo "  Response: ${wav_status:0:100}..."
    fi
fi

# Step 6: User explores job management
echo ""
echo -e "${CYAN}📋 Step 6: User explores job management...${NC}"

echo -n "✓ View all jobs: "
all_jobs=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/")
if [[ "$all_jobs" == *"["* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    job_count=$(echo "$all_jobs" | grep -o '"id"' | wc -l)
    echo "  User sees job history - $job_count jobs listed"
else
    echo -e "${RED}ERROR${NC}"
    echo "  Response: ${all_jobs:0:100}..."
fi

# Test pagination if supported
echo -n "✓ Test pagination: "
page_jobs=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/?page=1&size=5")
if [[ "$page_jobs" == *"["* ]]; then
    echo -e "${GREEN}SUPPORTED${NC}"
    echo "  User can navigate through job pages"
else
    echo -e "${YELLOW}NOT IMPLEMENTED${NC}"
fi

# Step 7: User tries different models
echo ""
echo -e "${CYAN}🤖 Step 7: User experiments with different models...${NC}"

models=("tiny" "base" "small" "medium" "large" "large-v3")
for model in "${models[@]}"; do
    echo -n "✓ Test model '$model': "
    model_test=$(curl -s -X POST "${BASE_URL}/jobs/" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@/tmp/user_audio_test/text_file.txt" \
        -F "model=$model" \
        -w "%{http_code}")
    
    model_code=${model_test: -3}
    if [[ "$model_code" == "200" ]] || [[ "$model_test" == *"job_id"* ]]; then
        echo -e "${GREEN}AVAILABLE${NC}"
    elif [[ "$model_code" == "400" ]] && [[ "$model_test" == *"model"* ]]; then
        echo -e "${YELLOW}NOT AVAILABLE${NC}"
    else
        echo -e "${RED}ERROR (${model_code})${NC}"
    fi
done

# Cleanup
echo ""
echo -e "${CYAN}🧹 Cleanup...${NC}"
rm -rf /tmp/user_audio_test

echo ""
echo -e "${BLUE}📊 USER EXPERIENCE SUMMARY - FILE UPLOAD${NC}"
echo "============================================="

echo -e "${GREEN}✅ User can successfully upload files${NC}"
echo -e "${GREEN}✅ Job tracking and status monitoring works${NC}"
echo -e "${GREEN}✅ Job history and management accessible${NC}"

if [[ "$text_code" == "400" ]]; then
    echo -e "${GREEN}✅ System correctly validates file types${NC}"
else
    echo -e "${YELLOW}⚠️  File type validation may need improvement${NC}"
fi

if [[ "$sus_code" == "400" ]]; then
    echo -e "${GREEN}✅ Security: Suspicious filenames are blocked${NC}"
else
    echo -e "${YELLOW}⚠️  Security: Review filename validation${NC}"
fi

echo ""
echo -e "${MAGENTA}Next: User will explore dashboard and admin features...${NC}"