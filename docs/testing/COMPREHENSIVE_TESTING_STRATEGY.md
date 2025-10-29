# Comprehensive Testing Strategy for Whisper Transcriber

**Date**: October 24, 2025  
**Purpose**: Systematic testing framework with automated monitoring and issue correction

## 🎯 **Testing Overview**

### **Testing Philosophy**
- **Layered Testing**: Unit → Integration → System → End-to-End
- **Real-Time Monitoring**: Continuous monitoring during all testing phases
- **Automated Correction**: Immediate issue detection and resolution
- **Progressive Complexity**: Start simple, build to complex scenarios
- **Risk-Based Priority**: Focus on critical functionality first

### **Testing Environment**
- **Current Status**: Application fully operational with JWT authentication
- **Monitoring**: Real-time monitoring script with automated corrections
- **Documentation**: All issues tracked and documented
- **Recovery**: Automated service recovery and performance optimization

## 📋 **Phase 1: Core Functionality Testing (30 minutes)**

### **1.1 System Health Verification**
```bash
# Start monitoring (run in separate terminal)
./scripts/monitor_application.sh

# Basic health checks
curl -s http://localhost:8000/health
curl -s http://localhost:8000/docs | head -5
docker compose ps
```

**Expected Results:**
- Health endpoint returns `{"status":"ok"}`
- API documentation loads successfully
- All containers show healthy status
- Monitoring shows no critical issues

**Success Criteria:**
- ✅ All endpoints respond within 500ms
- ✅ No error patterns in logs
- ✅ Resource usage <70% CPU, <80% memory

### **1.2 Authentication System Testing**
```bash
# Test admin login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "0AYw^lpZa!TM*iw0oIKX"}'

# Extract token for subsequent tests
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "0AYw^lpZa!TM*iw0oIKX"}' | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "JWT Token: $TOKEN"
```

**Expected Results:**
- Login returns JWT token successfully
- Token structure is valid JWT format
- No authentication errors in monitoring

**Success Criteria:**
- ✅ Login response time <1 second
- ✅ JWT token contains expected claims
- ✅ No failed authentication alerts

### **1.3 Database Connectivity Testing**
```bash
# Test database operations
docker compose exec app python -c "
from api.orm_bootstrap import get_db
from api.models import User
db = next(get_db())
users = db.query(User).all()
print(f'Users in database: {len(users)}')
for user in users:
    print(f'  - {user.username} ({user.role})')
"

# Test database performance
docker compose exec app python -c "
from api.orm_bootstrap import get_db
from sqlalchemy import text
import time
db = next(get_db())
start = time.time()
result = db.execute(text('SELECT COUNT(*) FROM users'))
duration = time.time() - start
print(f'Query performance: {duration:.3f}s')
"
```

**Expected Results:**
- Database contains admin user
- Query performance <100ms
- No database connection errors

**Success Criteria:**
- ✅ Database queries execute successfully
- ✅ Admin user exists with correct role
- ✅ Query performance within acceptable limits

## 📋 **Phase 2: API Endpoint Testing (45 minutes)**

### **2.1 Protected Endpoint Testing**
```bash
# Test protected endpoints with JWT token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/transcripts
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/models

# Test unauthorized access
curl -s -w "HTTP_CODE:%{http_code}" http://localhost:8000/jobs
```

**Expected Results:**
- Authorized requests succeed
- Unauthorized requests return 401
- Response times <1 second

**Success Criteria:**
- ✅ JWT authentication enforced correctly
- ✅ API responses well-formed JSON
- ✅ No authorization bypass vulnerabilities

### **2.2 File Upload Testing**
```bash
# Create test audio file
echo "This is a test audio file" > /tmp/test_audio.txt

# Test file upload endpoint
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/tmp/test_audio.txt" \
     -F "model=tiny"

# Test invalid file upload
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/etc/passwd"
```

**Expected Results:**
- Valid uploads accepted and processed
- Invalid files rejected with appropriate errors
- File size limits enforced

**Success Criteria:**
- ✅ File validation working correctly
- ✅ Upload progress tracking functional
- ✅ Security filters prevent malicious uploads

### **2.3 Whisper Model Testing**
```bash
# Test model availability
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/models

# Test model configuration
docker compose exec app python -c "
import os
models_dir = '/app/models'
if os.path.exists(models_dir):
    models = [f for f in os.listdir(models_dir) if f.endswith('.pt')]
    print(f'Available models: {models}')
else:
    print('Models directory not found')
"
```

**Expected Results:**
- Model list returns available Whisper models
- Model files exist in expected location
- No model loading errors

**Success Criteria:**
- ✅ All expected models available
- ✅ Model metadata correct
- ✅ No file system access issues

## 📋 **Phase 3: Integration Testing (60 minutes)**

### **3.1 Complete Transcription Workflow**
```bash
# Create actual audio test file (if available)
# Or test with mock audio processing

# Submit transcription job
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/transcribe" \
               -H "Authorization: Bearer $TOKEN" \
               -F "file=@/tmp/test_audio.txt" \
               -F "model=tiny" \
               -F "language=auto")

echo "Job Response: $JOB_RESPONSE"

# Extract job ID
JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', 'N/A'))")

# Monitor job progress
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs/$JOB_ID

# Check job completion
sleep 10
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs/$JOB_ID/status
```

**Expected Results:**
- Job submission successful
- Job ID returned and valid
- Job progresses through expected states
- Final result contains transcript

**Success Criteria:**
- ✅ End-to-end workflow completes
- ✅ Job status updates correctly
- ✅ Transcript quality acceptable
- ✅ No processing errors

### **3.2 WebSocket Real-Time Testing**
```bash
# Test WebSocket connection (if available)
# Note: This may need Redis configuration fix first

# Check WebSocket service status
docker compose logs app | grep -i websocket

# Test real-time updates
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/ws/test
```

**Expected Results:**
- WebSocket connections establish successfully
- Real-time updates delivered
- Connection resilience tested

**Success Criteria:**
- ✅ WebSocket authentication working
- ✅ Real-time events delivered
- ✅ Connection recovery functional

### **3.3 Background Job Processing**
```bash
# Test Celery worker functionality
docker compose logs worker | tail -20

# Submit multiple concurrent jobs
for i in {1..3}; do
    curl -X POST "http://localhost:8000/transcribe" \
         -H "Authorization: Bearer $TOKEN" \
         -F "file=@/tmp/test_audio.txt" \
         -F "model=tiny" &
done
wait

# Check job queue status
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs/queue
```

**Expected Results:**
- Multiple jobs processed concurrently
- Queue management working
- Worker scaling functional

**Success Criteria:**
- ✅ Concurrent job processing
- ✅ Queue management effective
- ✅ No resource contention issues

## 📋 **Phase 4: Performance & Load Testing (45 minutes)**

### **4.1 Response Time Testing**
```bash
# Baseline performance test
for i in {1..10}; do
    time curl -s http://localhost:8000/health > /dev/null
done

# Load testing with concurrent requests
for i in {1..5}; do
    (
        for j in {1..10}; do
            curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs
        done
    ) &
done
wait
```

**Expected Results:**
- Health endpoint <100ms consistently
- API endpoints <500ms under load
- No performance degradation

**Success Criteria:**
- ✅ Response times within SLA
- ✅ System stable under load
- ✅ No memory leaks detected

### **4.2 Resource Usage Testing**
```bash
# Monitor resource usage during load
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Memory usage baseline
docker compose exec app python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

**Expected Results:**
- CPU usage <80% during normal operations
- Memory usage stable, no leaks
- Network I/O reasonable

**Success Criteria:**
- ✅ Resource usage within limits
- ✅ No resource exhaustion
- ✅ Scaling characteristics acceptable

## 📋 **Phase 5: Security Testing (30 minutes)**

### **5.1 Authentication Security**
```bash
# Test invalid credentials
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "wrong_password"}'

# Test JWT token manipulation
INVALID_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
curl -H "Authorization: Bearer $INVALID_TOKEN" http://localhost:8000/jobs

# Test SQL injection attempts
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin'\''OR 1=1--", "password": "test"}'
```

**Expected Results:**
- Invalid credentials rejected
- Malformed tokens rejected
- SQL injection attempts blocked

**Success Criteria:**
- ✅ Authentication bypass prevented
- ✅ JWT validation robust
- ✅ Input sanitization effective

### **5.2 File Upload Security**
```bash
# Test malicious file uploads
echo "<?php system(\$_GET['cmd']); ?>" > /tmp/malicious.php
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/tmp/malicious.php"

# Test oversized file upload
dd if=/dev/zero of=/tmp/large_file.dat bs=1M count=200
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/tmp/large_file.dat"
```

**Expected Results:**
- Malicious files rejected
- File size limits enforced
- Content type validation working

**Success Criteria:**
- ✅ File type restrictions enforced
- ✅ File size limits effective
- ✅ Malicious content detection working

## 📋 **Phase 6: Error Handling & Recovery (30 minutes)**

### **6.1 Service Failure Testing**
```bash
# Test database disconnection recovery
docker compose stop redis
sleep 5
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/jobs
docker compose start redis

# Test service restart recovery
docker compose restart app
sleep 10
curl -s http://localhost:8000/health
```

**Expected Results:**
- Graceful degradation during outages
- Automatic recovery after restart
- Error messages informative

**Success Criteria:**
- ✅ Service resilience demonstrated
- ✅ Recovery procedures effective
- ✅ Error handling comprehensive

### **6.2 Data Corruption Testing**
```bash
# Test with invalid input data
curl -X POST "http://localhost:8000/transcribe" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"invalid": "json structure"}'

# Test with corrupted file
echo -e "\x00\x01\x02\x03\x04\x05" > /tmp/corrupted.dat
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/tmp/corrupted.dat"
```

**Expected Results:**
- Invalid input handled gracefully
- Corrupted files detected and rejected
- System remains stable

**Success Criteria:**
- ✅ Input validation comprehensive
- ✅ Error recovery functional
- ✅ System stability maintained

## 🎯 **Testing Execution Guide**

### **Pre-Testing Setup**
1. **Start Monitoring**:
   ```bash
   # Terminal 1: Start real-time monitoring
   ./scripts/monitor_application.sh
   
   # Terminal 2: Run tests
   # Follow phases sequentially
   ```

2. **Verify Baseline**:
   - All containers healthy
   - Authentication working
   - Basic endpoints responding

### **Testing Execution**
1. **Sequential Execution**: Run phases in order 1→6
2. **Monitor Continuously**: Watch monitoring terminal for issues
3. **Document Issues**: Record any problems detected
4. **Auto-Correction**: Let monitoring script fix issues automatically
5. **Manual Investigation**: Investigate persistent issues

### **Post-Testing Analysis**
1. **Review Monitoring Logs**: Check `/tmp/whisper_monitoring.log`
2. **Performance Analysis**: Analyze response times and resource usage
3. **Issue Documentation**: Document all issues found
4. **Optimization Planning**: Plan performance improvements
5. **Security Review**: Review security test results

## 📊 **Success Metrics**

### **Functional Testing**
- ✅ **Authentication**: 100% of auth tests pass
- ✅ **API Endpoints**: All endpoints respond correctly
- ✅ **File Processing**: Upload and transcription workflow complete
- ✅ **Database Operations**: All database tests successful

### **Performance Testing**
- ✅ **Response Times**: 95% of requests <500ms
- ✅ **Resource Usage**: CPU <70%, Memory <80%
- ✅ **Concurrency**: Handle 10+ concurrent requests
- ✅ **Stability**: No crashes during testing

### **Security Testing**
- ✅ **Authentication**: No bypass vulnerabilities
- ✅ **Authorization**: Role-based access enforced
- ✅ **Input Validation**: Malicious input blocked
- ✅ **File Security**: Malicious uploads prevented

### **Reliability Testing**
- ✅ **Error Handling**: Graceful error responses
- ✅ **Recovery**: Automatic service recovery
- ✅ **Data Integrity**: No data corruption
- ✅ **Monitoring**: Real-time issue detection

## 🚀 **Getting Started**

### **Quick Start Commands**
```bash
# 1. Start monitoring (Terminal 1)
cd /home/buymeagoat/dev/whisper-transcriber
./scripts/monitor_application.sh

# 2. Run Phase 1 tests (Terminal 2)
curl -s http://localhost:8000/health
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "0AYw^lpZa!TM*iw0oIKX"}' | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Continue with systematic testing...
```

### **Monitoring Commands**
```bash
# Check monitoring status
tail -f /tmp/whisper_monitoring.log

# Run single monitoring cycle
./scripts/monitor_application.sh --single

# Custom monitoring intervals
./scripts/monitor_application.sh -i 5 -t 1.0
```

---

**Ready to begin comprehensive testing with real-time monitoring and automated issue correction!**