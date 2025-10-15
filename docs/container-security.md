# Container Security Documentation

## Overview

This document describes the comprehensive container security implementation for the Whisper Transcriber project. The security measures follow defense-in-depth principles and industry best practices for container hardening.

## Security Architecture

### Multi-Layer Security Model

1. **Base Image Security**: Secure, minimal base images with SHA256 pinning
2. **User Security**: Non-root execution with minimal privileges
3. **Capability Management**: Minimal Linux capabilities with explicit dropping
4. **Filesystem Security**: Read-only containers with secure tmpfs mounts
5. **Network Isolation**: Segmented networks with minimal exposure
6. **Resource Controls**: CPU and memory limits for DoS protection
7. **Runtime Security**: Security contexts and monitoring

## Dockerfile Security Hardening

### Base Image Security

```dockerfile
# Secure base image with SHA256 digest
FROM python:3.11-slim@sha256:...

# Non-root user creation
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

**Security Features:**
- SHA256-pinned base images prevent supply chain attacks
- Minimal slim images reduce attack surface
- Non-root user execution prevents privilege escalation
- Proper file ownership and permissions

### Build Security

- Package cache cleanup to reduce image size
- No secrets in build layers
- Minimal installed packages
- Security labels for metadata

## Docker Compose Security Contexts

### Service Hardening

Each service implements comprehensive security contexts:

```yaml
security_opt:
  - no-new-privileges:true  # Prevent privilege escalation
cap_drop:
  - ALL                     # Drop all capabilities
cap_add:
  - SETUID                  # Add only required capabilities
  - SETGID
user: "1000:1000"          # Non-root user
read_only: true            # Read-only filesystem
tmpfs:                     # Writable areas in memory
  - /tmp:noexec,nosuid,size=200m
```

### Network Isolation

**Network Architecture:**
- **Frontend Network**: Public-facing services (nginx, app)
- **Backend Network**: Internal services (redis, worker) - isolated
- **Custom Subnets**: Controlled IP ranges
- **Minimal Port Exposure**: localhost binding only

```yaml
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
  backend:
    driver: bridge
    internal: true  # No external access
    ipam:
      config:
        - subnet: 172.21.0.0/24
```

### Volume Security

**Secure Volume Configuration:**
- Named volumes instead of bind mounts
- Read-only mounts for static content
- Proper volume permissions
- Secure tmpfs for temporary data

```yaml
volumes:
  - app_models:/app/models:ro      # Read-only models
  - app_storage:/app/storage       # Application data
tmpfs:
  - /tmp:noexec,nosuid,size=200m   # Secure temporary space
```

## Security Features by Service

### Application Service (app)

**Security Measures:**
- Non-root execution (UID 1000)
- Read-only filesystem with tmpfs
- Minimal capabilities (CHOWN, SETUID, SETGID, DAC_OVERRIDE)
- Resource limits (2 CPU, 4GB RAM)
- Security headers via middleware
- Frontend + Backend network access

### Worker Service (worker)

**Security Measures:**
- Non-root execution (UID 1000)
- Read-only filesystem with larger tmpfs for ML operations
- Additional capability (SYS_NICE) for CPU scheduling
- Higher resource limits (4 CPU, 8GB RAM)
- Backend network only (no external access)

### Redis Service (redis)

**Security Measures:**
- Non-root execution (UID 999)
- Minimal capabilities (SETUID, SETGID)
- Password authentication
- Memory limits and eviction policies
- Backend network isolation
- Read-only filesystem with tmpfs

### Nginx Service (nginx)

**Security Measures:**
- Non-root execution (nginx:nginx)
- Minimal capabilities + NET_BIND_SERVICE for port binding
- Read-only configuration mounts
- SSL/TLS termination
- Frontend network only
- Production profile activation

## Security Scanning and Monitoring

### Automated Security Scanning

The `scripts/docker_security_scan.sh` script provides:

1. **Dockerfile Security Analysis**
   - Non-root user validation
   - Base image security checks
   - Sensitive file detection
   - Best practices compliance

2. **Docker Compose Security Analysis**
   - Privileged container detection
   - Security context validation
   - Network isolation verification
   - Resource limit checks

3. **Runtime Security Analysis**
   - Container user validation
   - Capability verification
   - Filesystem security checks

4. **Vulnerability Scanning**
   - Docker Scout integration
   - Trivy scanner support
   - CVE detection and reporting

### Running Security Scans

```bash
# Run comprehensive security scan
./scripts/docker_security_scan.sh

# Check scan reports
ls logs/security/security_summary_*.txt
```

## Security Testing

### Comprehensive Test Suite

The `tests/test_container_security_008.py` provides:

1. **Dockerfile Security Tests**
   - Non-root user enforcement
   - Secure base image validation
   - Sensitive file prevention

2. **Docker Compose Security Tests**
   - Security context validation
   - Capability management verification
   - Network isolation testing
   - Volume security checks

3. **Runtime Security Tests**
   - Container user validation
   - Capability verification
   - Filesystem read-only validation

### Running Security Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run container security tests
python tests/test_container_security_008.py

# Run with pytest for detailed output
pytest tests/test_container_security_008.py -v
```

## Deployment Security Guidelines

### Production Deployment

1. **Image Management**
   ```bash
   # Build with security scanning
   docker build --no-cache -t whisper-transcriber .
   
   # Scan for vulnerabilities
   ./scripts/docker_security_scan.sh
   ```

2. **Secure Environment Variables**
   ```bash
   # Use strong passwords
   export REDIS_PASSWORD=$(openssl rand -base64 32)
   
   # Set secure JWT secret
   export JWT_SECRET=$(openssl rand -base64 64)
   ```

3. **Network Security**
   - Use reverse proxy (nginx) for SSL termination
   - Implement proper firewall rules
   - Monitor network traffic

4. **Resource Monitoring**
   - Implement container resource monitoring
   - Set up log aggregation
   - Configure health checks

### Security Maintenance

1. **Regular Updates**
   - Update base images monthly
   - Scan for new vulnerabilities weekly
   - Update dependencies regularly

2. **Security Monitoring**
   - Monitor container logs for security events
   - Implement runtime threat detection
   - Regular security audits

3. **Incident Response**
   - Document security incident procedures
   - Maintain backup and recovery plans
   - Test disaster recovery regularly

## Security Compliance

### Industry Standards

The implementation follows:
- **CIS Docker Benchmark**: Container security best practices
- **NIST Cybersecurity Framework**: Risk management approach
- **OWASP Container Security**: Application security in containers

### Compliance Checklist

- ✅ Non-root container execution
- ✅ Minimal Linux capabilities
- ✅ Read-only filesystems
- ✅ Network segmentation
- ✅ Resource limits
- ✅ Security scanning
- ✅ Vulnerability management
- ✅ Security testing

## Troubleshooting

### Common Security Issues

1. **Permission Denied Errors**
   ```bash
   # Check container user
   docker exec container_name id
   
   # Verify file permissions
   docker exec container_name ls -la /app
   ```

2. **Network Connectivity Issues**
   ```bash
   # Check network configuration
   docker network ls
   docker network inspect whisper-frontend
   ```

3. **Resource Limit Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check container logs
   docker logs container_name
   ```

### Security Validation

```bash
# Validate security configuration
docker inspect container_name | jq '.[] | {
  User: .Config.User,
  ReadonlyRootfs: .HostConfig.ReadonlyRootfs,
  CapDrop: .HostConfig.CapDrop,
  SecurityOpt: .HostConfig.SecurityOpt
}'
```

## References

- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Container Security Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)
- [OWASP Container Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
