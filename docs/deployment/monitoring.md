# Monitoring Guide

This guide covers monitoring, observability, and health checks for Whisper Transcriber deployments.

## Health Checks

### Application Health

**Primary health endpoint:**
```bash
curl http://localhost:8000/
```

**Response (healthy):**
```json
{
  "service": "Whisper Transcriber",
  "version": "2.0.0",
  "status": "online", 
  "features": ["audio-upload", "real-time-progress", "mobile-friendly"]
}
```

### Service Health Checks

**Check all Docker services:**
```bash
# Service status
docker-compose ps

# Expected output:
# NAME               IMAGE                    STATUS
# whisper-app        whisper-transcriber_app  Up 2 hours (healthy)
# whisper-redis      redis:7-alpine           Up 2 hours (healthy)
# whisper-worker     whisper-transcriber_app  Up 2 hours
```

**Individual service checks:**

```bash
# App service health
curl -f http://localhost:8000/ || echo "App unhealthy"

# Redis health
docker exec whisper-redis redis-cli ping
# Expected: PONG

# Worker health (check recent activity)
docker logs whisper-worker --tail=10 | grep -E "(ready|started)"
```

## Monitoring Endpoints

### Built-in Monitoring

**Job status monitoring:**
```bash
# List recent jobs
curl http://localhost:8000/jobs?limit=10

# Check specific job
curl http://localhost:8000/jobs/{job_id}
```

**System information:**
```bash
# Basic system info
curl http://localhost:8000/

# Application metrics (if available)
docker exec whisper-app ps aux
docker exec whisper-app df -h
```

## Docker Health Checks

### Container Health Configuration

**In docker-compose.yml:**
```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 3s
      retries: 3

  worker:
    healthcheck:
      test: ["CMD", "celery", "-A", "app.worker", "inspect", "ping"]
      interval: 60s
      timeout: 10s
      retries: 3
```

### Health Check Scripts

**Comprehensive health check script:**
```bash
#!/bin/bash
# /usr/local/bin/health-check.sh

EXIT_CODE=0

echo "=== Whisper Transcriber Health Check ==="
echo "Timestamp: $(date)"

# Check app service
echo "Checking app service..."
if curl -sf http://localhost:8000/ > /dev/null; then
    echo "✓ App service: healthy"
else
    echo "✗ App service: unhealthy"
    EXIT_CODE=1
fi

# Check Redis
echo "Checking Redis..."
if docker exec whisper-redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis: healthy"
else
    echo "✗ Redis: unhealthy"
    EXIT_CODE=1
fi

# Check worker
echo "Checking worker..."
if docker exec whisper-worker celery -A app.worker inspect ping > /dev/null 2>&1; then
    echo "✓ Worker: healthy"
else
    echo "✗ Worker: unhealthy"
    EXIT_CODE=1
fi

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo "✓ Disk space: ${DISK_USAGE}% used"
else
    echo "✗ Disk space: ${DISK_USAGE}% used (WARNING: >90%)"
    EXIT_CODE=1
fi

# Check memory usage
echo "Checking memory usage..."
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEMORY_USAGE" -lt 90 ]; then
    echo "✓ Memory usage: ${MEMORY_USAGE}%"
else
    echo "✗ Memory usage: ${MEMORY_USAGE}% (WARNING: >90%)"
    EXIT_CODE=1
fi

echo "=== Health Check Complete ==="
exit $EXIT_CODE
```

## Log Monitoring

### Log Locations

**Docker container logs:**
```bash
# All services
docker-compose logs

# Specific services
docker logs whisper-app
docker logs whisper-worker  
docker logs whisper-redis

# Follow logs in real-time
docker-compose logs -f

# Filter by time
docker logs whisper-app --since 1h
docker logs whisper-app --until 2023-01-01T10:00:00
```

### Log Analysis

**Common log patterns to monitor:**

```bash
# Error patterns
docker logs whisper-app 2>&1 | grep -i error

# Failed transcriptions  
docker logs whisper-worker 2>&1 | grep -i "failed\|error"

# High memory usage warnings
docker logs whisper-app 2>&1 | grep -i "memory\|oom"

# Performance issues
docker logs whisper-app 2>&1 | grep -i "slow\|timeout"
```

**Log parsing script:**
```bash
#!/bin/bash
# /usr/local/bin/log-analysis.sh

echo "=== Log Analysis Report ==="
echo "Generated: $(date)"

# Count error messages in last hour
ERRORS=$(docker logs whisper-app --since 1h 2>&1 | grep -ci error)
echo "Errors in last hour: $ERRORS"

# Count successful transcriptions today
SUCCESSES=$(docker logs whisper-worker --since $(date +%Y-%m-%d) 2>&1 | grep -c "Transcription completed")
echo "Successful transcriptions today: $SUCCESSES"

# Check for any failed jobs
FAILURES=$(docker logs whisper-worker --since $(date +%Y-%m-%d) 2>&1 | grep -c "Transcription failed")
echo "Failed transcriptions today: $FAILURES"

if [ "$FAILURES" -gt 0 ]; then
    echo "Recent failures:"
    docker logs whisper-worker --since $(date +%Y-%m-%d) 2>&1 | grep "Transcription failed" | tail -5
fi
```

## Performance Monitoring

### Resource Usage

**Real-time resource monitoring:**
```bash
# Docker container stats
docker stats

# System resources
htop

# Disk I/O
iotop

# Network usage
iftop
```

**Resource monitoring script:**
```bash
#!/bin/bash
# /usr/local/bin/resource-monitor.sh

echo "=== Resource Monitor ==="
echo "Timestamp: $(date)"

# CPU usage
echo "CPU Usage:"
docker exec whisper-app cat /proc/loadavg

# Memory usage by container
echo "Memory Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Disk usage
echo "Disk Usage:"
df -h | grep -E "(Filesystem|/dev/)"

# Active transcription jobs
echo "Active Jobs:"
ACTIVE_JOBS=$(curl -s http://localhost:8000/jobs | jq '.jobs[] | select(.status == "processing") | .id' | wc -l)
echo "Processing: $ACTIVE_JOBS jobs"

echo "========================"
```

### Queue Monitoring

**Celery queue status:**
```bash
# Check queue length
docker exec whisper-worker celery -A app.worker inspect active

# Worker statistics
docker exec whisper-worker celery -A app.worker inspect stats

# Reserved tasks
docker exec whisper-worker celery -A app.worker inspect reserved
```

## Alerting

### Email Alerts

**Simple email alerting:**
```bash
#!/bin/bash
# /usr/local/bin/alert-check.sh

# Configuration
ALERT_EMAIL="admin@yourdomain.com"
SERVICE_URL="http://localhost:8000"

# Check service
if ! curl -sf "$SERVICE_URL" > /dev/null; then
    echo "ALERT: Whisper Transcriber service is down" | \
        mail -s "Service Alert: Whisper Transcriber Down" "$ALERT_EMAIL"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ALERT: Disk space is ${DISK_USAGE}% full" | \
        mail -s "Disk Space Alert: ${DISK_USAGE}% full" "$ALERT_EMAIL"
fi
```

### Webhook Alerts

**Slack webhook integration:**
```bash
#!/bin/bash
# /usr/local/bin/slack-alert.sh

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

send_slack_alert() {
    local message="$1"
    local color="$2"
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"text\": \"$message\",
                \"footer\": \"Whisper Transcriber Monitor\",
                \"ts\": $(date +%s)
            }]
        }" \
        "$SLACK_WEBHOOK"
}

# Example usage
if ! curl -sf http://localhost:8000/ > /dev/null; then
    send_slack_alert "🚨 Whisper Transcriber service is down!" "danger"
fi
```

## Automated Monitoring

### Systemd Service for Monitoring

**Monitor service definition:**
```ini
# /etc/systemd/system/whisper-monitor.service
[Unit]
Description=Whisper Transcriber Health Monitor
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/health-check.sh
User=whisper
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Timer for regular checks:**
```ini
# /etc/systemd/system/whisper-monitor.timer
[Unit]
Description=Run Whisper health check every 5 minutes
Requires=whisper-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable automated monitoring:**
```bash
sudo systemctl enable whisper-monitor.timer
sudo systemctl start whisper-monitor.timer

# Check timer status
sudo systemctl status whisper-monitor.timer
```

### Cron-based Monitoring

**Crontab entries:**
```bash
# Edit crontab
crontab -e

# Add monitoring tasks
# Health check every 5 minutes
*/5 * * * * /usr/local/bin/health-check.sh >> /var/log/whisper-health.log 2>&1

# Resource monitoring every 15 minutes  
*/15 * * * * /usr/local/bin/resource-monitor.sh >> /var/log/whisper-resources.log 2>&1

# Daily log analysis
0 8 * * * /usr/local/bin/log-analysis.sh | mail -s "Daily Whisper Report" admin@yourdomain.com
```

## Troubleshooting Monitoring Issues

### Common Problems

**Health check failures:**
```bash
# Check if service is running
docker-compose ps

# Check service logs
docker logs whisper-app --tail=50

# Test manually
curl -v http://localhost:8000/
```

**False positive alerts:**
```bash
# Increase health check timeout
# In docker-compose.yml:
healthcheck:
  timeout: 30s  # Increase from 10s
  retries: 5    # Increase from 3
```

**Missing metrics:**
```bash
# Verify monitoring scripts have correct permissions
chmod +x /usr/local/bin/health-check.sh
chmod +x /usr/local/bin/resource-monitor.sh

# Check script dependencies
which curl jq docker
```

### Monitoring Best Practices

1. **Set appropriate thresholds** - Not too sensitive, not too late
2. **Monitor trends** - Look for gradual degradation
3. **Test alerts** - Verify alert mechanisms work
4. **Document procedures** - Clear escalation paths
5. **Regular review** - Adjust monitoring based on experience
