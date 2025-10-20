# Production Deployment Guide

This guide covers deploying Whisper Transcriber to a production environment with proper security, monitoring, and scalability.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 4+ cores (8+ cores recommended)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 50GB+ SSD storage
- **Network**: Static IP with domain name

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- curl, wget, openssl
- (Optional) certbot for Let's Encrypt

## 🚀 Quick Start

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Copy and configure environment
cp .env.prod.example .env.prod
nano .env.prod  # Configure your settings
```

### 2. Configure Domain and SSL

```bash
# Set your domain
export DOMAIN=yourdomain.com
export SSL_EMAIL=admin@yourdomain.com

# Setup SSL certificates
./scripts/production/setup-ssl.sh
```

### 3. Deploy Application

```bash
# Deploy to production
./scripts/production/deploy.sh deploy

# Check status
./scripts/production/deploy.sh status
```

## ⚙️ Configuration

### Environment Variables

Key settings in `.env.prod`:

```bash
# Security (REQUIRED)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
POSTGRES_PASSWORD=your-database-password
REDIS_PASSWORD=your-redis-password

# Domain
DOMAIN=yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Performance
WORKER_PROCESSES=4
MAX_UPLOAD_SIZE=500MB
```

### SSL/TLS Configuration

**Option 1: Let's Encrypt (Recommended)**
```bash
./scripts/production/setup-ssl.sh
# Choose option 1 for Let's Encrypt
```

**Option 2: Custom Certificate**
```bash
# Place your certificates in ssl/ directory:
# ssl/privkey.pem
# ssl/fullchain.pem  
# ssl/chain.pem
```

## 🏗️ Architecture

### Production Stack
- **Reverse Proxy**: Nginx with SSL termination
- **Application**: FastAPI (Python) with Gunicorn
- **Database**: PostgreSQL 15 with connection pooling
- **Cache/Queue**: Redis 7 with persistence
- **Background Tasks**: Celery workers
- **Monitoring**: Prometheus + Grafana
- **Container Runtime**: Docker with security hardening

### Network Architecture
```
Internet → Nginx (SSL) → Application → Database
                       ↓
                    Redis ← Workers
                       ↓
                   Monitoring
```

## 🔒 Security Features

### Container Security
- Non-root user execution
- Read-only filesystems
- Capability dropping
- Security contexts
- Resource limits

### Network Security
- Isolated networks
- Rate limiting
- CORS protection
- Security headers
- SSL/TLS enforcement

### Application Security
- JWT authentication
- Password hashing
- Input validation
- File type restrictions
- CSRF protection

## 📊 Monitoring

### Metrics Collection
- **Application**: Custom metrics via `/metrics` endpoint
- **Infrastructure**: Node Exporter for system metrics
- **Database**: PostgreSQL metrics
- **Cache**: Redis metrics
- **Web Server**: Nginx metrics

### Dashboards
- **Grafana**: http://yourdomain.com:3000
  - Default admin credentials in `.env.prod`
  - Pre-configured dashboards for all services

### Alerting
- Built-in health checks for all services
- Prometheus alerting rules (configurable)
- Email/Slack notifications (optional)

## 🔧 Operations

### Daily Operations

**Check System Status**
```bash
./scripts/production/deploy.sh status
```

**View Logs**
```bash
# All services
./scripts/production/deploy.sh logs

# Specific service
./scripts/production/deploy.sh logs app
./scripts/production/deploy.sh logs nginx
```

**Scale Services**
```bash
# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

### Backup and Recovery

**Automatic Backups**
- Database: Daily automated backups
- Files: Application data backups
- Retention: 7 days (configurable)

**Manual Backup**
```bash
# Create manual backup
docker-compose -f docker-compose.prod.yml exec postgres \
    pg_dumpall -U whisper > backup_$(date +%Y%m%d).sql
```

**Restore from Backup**
```bash
# Restore database
cat backup_20231201.sql | docker-compose -f docker-compose.prod.yml \
    exec -T postgres psql -U whisper
```

### Updates and Maintenance

**Deploy Updates**
```bash
# Pull latest changes
git pull origin main

# Deploy with automatic backup
./scripts/production/deploy.sh deploy
```

**Rollback Deployment**
```bash
# Rollback to previous version
./scripts/production/deploy.sh rollback
```

**Certificate Renewal**
```bash
# Renew Let's Encrypt certificates
./ssl/renew.sh

# Or set up automatic renewal
echo "0 3 * * * /path/to/whisper-transcriber/ssl/renew.sh" | crontab -
```

## 🚨 Troubleshooting

### Common Issues

**Application Not Responding**
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Restart services
docker-compose -f docker-compose.prod.yml restart app
```

**SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout

# Regenerate self-signed certificate
./scripts/production/setup-ssl.sh
```

**Database Connection Issues**
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check connection from app
docker-compose -f docker-compose.prod.yml exec app \
    python -c "from api.orm_bootstrap import engine; engine.connect()"
```

**High Memory Usage**
```bash
# Monitor resource usage
docker stats

# Adjust resource limits in docker-compose.prod.yml
# Restart with new limits
docker-compose -f docker-compose.prod.yml up -d
```

### Log Locations

- **Application**: `docker-compose logs app`
- **Nginx**: `docker-compose logs nginx`
- **Database**: `docker-compose logs postgres`
- **Redis**: `docker-compose logs redis`
- **System**: `/var/log/syslog`

## 🔧 Advanced Configuration

### Custom Domain Setup

1. **DNS Configuration**
   ```
   A     yourdomain.com      → your-server-ip
   CNAME www.yourdomain.com  → yourdomain.com
   ```

2. **Firewall Configuration**
   ```bash
   # Allow HTTP/HTTPS
   ufw allow 80
   ufw allow 443
   
   # Allow SSH (adjust port as needed)
   ufw allow 22
   ```

### Performance Tuning

**Database Optimization**
```sql
-- Recommended PostgreSQL settings for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;
SELECT pg_reload_conf();
```

**Application Tuning**
```bash
# Adjust in .env.prod
WORKER_PROCESSES=8          # 2x CPU cores
DB_POOL_SIZE=20            # Concurrent connections
CELERY_WORKER_CONCURRENCY=4 # Background task workers
```

### Horizontal Scaling

**Load Balancer Configuration**
```nginx
upstream app_servers {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}
```

**Database Read Replicas**
```yaml
# Add to docker-compose.prod.yml
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: replicator
    POSTGRES_PASSWORD: ${REPLICA_PASSWORD}
  command: |
    postgres -c wal_level=replica -c max_wal_senders=3
```

## 📞 Support

### Getting Help

1. **Documentation**: Check this guide and inline comments
2. **Logs**: Always check service logs first
3. **Health Checks**: Use built-in health endpoints
4. **Community**: GitHub Issues and Discussions

### Performance Monitoring

- **Grafana Dashboards**: Pre-configured for all metrics
- **Application Metrics**: Custom business metrics
- **Infrastructure Metrics**: System and container metrics
- **User Experience**: Response time and error rate tracking

### Security Updates

1. **Container Images**: Regular security updates
2. **Dependencies**: Automated vulnerability scanning
3. **SSL Certificates**: Automatic renewal setup
4. **Security Headers**: Comprehensive protection

---

**Production deployment is complete!** 🎉

Your Whisper Transcriber application is now running in a secure, scalable, and monitored production environment.
