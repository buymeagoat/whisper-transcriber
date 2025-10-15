# Production Deployment Guide

This guide covers deploying Whisper Transcriber in production environments with security, performance, and reliability considerations.

## Production Architecture

```
Internet
    │
    ▼
┌─────────────────┐
│   Reverse Proxy │  ← HTTPS, Rate Limiting, Caching
│   (Nginx/Caddy) │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  Load Balancer  │  ← Optional: Multiple app instances
│                 │
└─────────────────┘
    │
    ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   App Instance  │    │     Redis       │    │   Workers (N)   │
│   (FastAPI)     │◄───┤  (Task Queue)   ├───►│ (Transcription) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
    │                           │                       │
    └───────────────────────────┼───────────────────────┘
                                │
                   ┌─────────────────┐
                   │   Persistent    │
                   │    Storage      │
                   └─────────────────┘
```

## Server Requirements

### Hardware Specifications

**Minimum Production Server:**
- **CPU**: 4 cores (Intel/AMD x64)
- **RAM**: 8GB (more for larger models)
- **Storage**: 50GB SSD
- **Network**: 100Mbps connection

**Recommended Production Server:**
- **CPU**: 8+ cores with high single-thread performance
- **RAM**: 16GB+ (32GB for large-v3 model)
- **Storage**: 100GB+ NVMe SSD
- **Network**: 1Gbps connection with low latency

**Model-specific RAM requirements:**
- **tiny**: 4GB total (2GB for 2 workers)
- **small**: 8GB total (4GB for 2 workers)
- **medium**: 16GB total (10GB for 2 workers)
- **large-v3**: 32GB total (20GB for 2 workers)

### Operating System

**Supported platforms:**
- **Ubuntu 20.04/22.04 LTS** (recommended)
- **Debian 11/12**
- **CentOS/RHEL 8+**
- **Amazon Linux 2**

## Security Configuration

### Firewall Setup

**UFW (Ubuntu):**
```bash
# Enable firewall
sudo ufw enable

# Allow SSH (configure first!)
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct app access (use reverse proxy)
sudo ufw deny 8000/tcp
```

**iptables:**
```bash
# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Block everything else
iptables -A INPUT -j DROP
```

### SSL/TLS Configuration

**Using Caddy (automatic HTTPS):**

```caddyfile
# Caddyfile
yourdomain.com {
    reverse_proxy localhost:8000
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
    }
    
    # Rate limiting
    rate_limit {
        zone transcribe {
            key {remote_host}
            events 10
            window 1m
        }
    }
}
```

**Using Nginx with Let's Encrypt:**

```nginx
# /etc/nginx/sites-available/whisper-transcriber
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location /transcribe {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://localhost:8000;
        
        # Large file upload support
        client_max_body_size 500M;
        proxy_request_buffering off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Application Security

**Production environment variables:**
```bash
# .env.production
# Core settings
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///app/data/app.db
WHISPER_MODEL_DIR=/app/models

# Security settings
LOG_LEVEL=WARNING                    # Reduce log verbosity
MAX_FILE_SIZE_MB=200                # Reasonable upload limit
ALLOWED_AUDIO_FORMATS=mp3,wav,m4a   # Restrict formats

# Performance settings
CELERY_CONCURRENCY=4                # Match server cores
DEFAULT_WHISPER_MODEL=small         # Balance speed/quality

# Disable debug features
DEBUG=false
LOG_TO_STDOUT=false
```

## High Availability Setup

### Load Balancing

**Multiple app instances:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  app1:
    build: .
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./storage:/app/storage
      - ./models:/app/models
    depends_on:
      - redis

  app2:
    build: .
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./storage:/app/storage
      - ./models:/app/models
    depends_on:
      - redis

  worker:
    build: .
    restart: unless-stopped
    command: celery -A app.worker worker --loglevel=info --concurrency=4
    environment:
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./storage:/app/storage
      - ./models:/app/models
    depends_on:
      - redis
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app1
      - app2
```

**Nginx load balancer configuration:**
```nginx
upstream whisper_backend {
    least_conn;
    server app1:8000 max_fails=3 fail_timeout=30s;
    server app2:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://whisper_backend;
        # ... other proxy settings
    }
}
```

### Database High Availability

**For larger deployments, consider PostgreSQL:**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: whisper
      POSTGRES_USER: whisper
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  postgres_backup:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - ./backups:/backups
    command: |
      sh -c "
      while true; do
        pg_dump -h postgres -U whisper whisper > /backups/backup_$(date +%Y%m%d_%H%M%S).sql
        find /backups -name '*.sql' -mtime +7 -delete
        sleep 86400
      done"
    depends_on:
      - postgres
```

## Monitoring and Observability

### Application Monitoring

**Health check endpoint:**
```bash
# Add to cron for automated monitoring
*/5 * * * * curl -f http://localhost:8000/ || echo "Service down" | mail -s "Alert" admin@yourdomain.com
```

**System monitoring with systemd:**
```ini
# /etc/systemd/system/whisper-monitor.service
[Unit]
Description=Whisper Transcriber Monitor
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/whisper-health-check.sh

# /etc/systemd/system/whisper-monitor.timer
[Unit]
Description=Run Whisper Monitor every 5 minutes

[Timer]
OnCalendar=*:0/5

[Install]
WantedBy=timers.target
```

### Log Management

**Centralized logging with rsyslog:**
```bash
# Ship Docker logs to syslog
docker run -d --log-driver=syslog --log-opt syslog-address=udp://logserver:514 ...
```

**Log rotation:**
```bash
# /etc/logrotate.d/whisper-transcriber
/var/log/whisper/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        docker kill -s USR1 whisper-app
    endscript
}
```

## Backup Strategy

### Automated Backups

**Daily backup script:**
```bash
#!/bin/bash
# /usr/local/bin/whisper-backup.sh

BACKUP_DIR="/backup/whisper"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec whisper-app sqlite3 /app/data/app.db ".backup /tmp/backup.db"
docker cp whisper-app:/tmp/backup.db "$BACKUP_DIR/database_$DATE.db"

# Backup uploads (if needed)
tar czf "$BACKUP_DIR/storage_$DATE.tar.gz" storage/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Automated backup with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/whisper-backup.sh >> /var/log/whisper-backup.log 2>&1
```

### Disaster Recovery

**Recovery procedures:**
1. **Restore database**: Copy backup database file
2. **Restore uploads**: Extract storage backup
3. **Restart services**: `docker-compose up -d`
4. **Verify functionality**: Test upload and transcription

## Performance Optimization

### System Tuning

**Kernel parameters:**
```bash
# /etc/sysctl.d/99-whisper.conf
# Increase file descriptor limits
fs.file-max = 100000

# Network tuning
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048

# Apply changes
sysctl -p /etc/sysctl.d/99-whisper.conf
```

**Docker optimization:**
```bash
# Increase Docker logging limits
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' > /etc/docker/daemon.json
systemctl restart docker
```

### Application Tuning

**Worker optimization:**
```bash
# Match worker count to CPU cores
CELERY_CONCURRENCY=8

# Optimize for CPU-bound tasks
CELERY_WORKER_PREFETCH_MULTIPLIER=1

# Increase task timeout for large files
CELERY_TASK_TIME_LIMIT=7200  # 2 hours
```

## Maintenance

### Regular Maintenance Tasks

**Weekly tasks:**
```bash
#!/bin/bash
# /usr/local/bin/whisper-maintenance.sh

# Clean up completed transcription files older than 30 days
find storage/transcripts -name "*.txt" -mtime +30 -delete

# Clean up uploaded files older than 7 days
find storage/uploads -name "*" -mtime +7 -delete

# Clean up Docker system
docker system prune -f

# Update Docker images
docker-compose pull && docker-compose up -d
```

### Monitoring Alerts

**Set up alerts for:**
- **Service downtime** (health check failures)
- **High CPU usage** (> 80% for 10 minutes)
- **Low disk space** (< 10% free)
- **High memory usage** (> 90% for 5 minutes)
- **Failed transcriptions** (error rate > 10%)

### Updates and Patches

**Update procedure:**
1. **Test in staging** environment first
2. **Schedule maintenance** window
3. **Backup current state**
4. **Deploy updates** with zero-downtime if possible
5. **Verify functionality** post-deployment
6. **Monitor for issues** for 24 hours
