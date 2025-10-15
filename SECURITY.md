# Security Policy

## Reporting Security Vulnerabilities

We take the security of Whisper Transcriber seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security issues by:

1. **Email**: Send details to `security@yourdomain.com`
2. **Private GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature

### What to Include

Please include as much information as possible:

- **Type of vulnerability** (e.g., XSS, SQL injection, etc.)
- **Location** of the vulnerability (file path, line number, etc.)
- **Steps to reproduce** the vulnerability
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Status updates**: Weekly until resolved
- **Resolution**: Depends on severity and complexity

## Security Considerations

### Application Security

**Input Validation:**
- All file uploads are validated for type and size
- Audio file formats are restricted to safe types
- File content is validated before processing

**Data Protection:**
- All data is processed locally (no cloud uploads)
- Uploaded files are stored temporarily and can be auto-deleted
- Database contains only metadata, not sensitive content

**Network Security:**
- HTTPS is recommended for production deployments
- No external network connections required for core functionality
- Rate limiting can be configured at the reverse proxy level

### Deployment Security

**Container Security:**
- Application runs as non-root user in containers
- Minimal base images to reduce attack surface
- No unnecessary network ports exposed

**File System Security:**
- Uploaded files stored in isolated directory
- SQLite database file has restricted permissions
- Temporary files are cleaned up automatically

**Configuration Security:**
- No default passwords or API keys
- Environment variables for sensitive configuration
- Security headers recommended in reverse proxy setup

## Known Security Considerations

### File Upload Risks

**Mitigations in place:**
- File type validation based on content, not just extension
- File size limits to prevent DoS attacks
- Uploaded files processed in isolated environment
- Automatic cleanup of old files

**Recommendations:**
- Run behind reverse proxy with additional validation
- Configure appropriate file size limits for your use case
- Monitor disk usage to prevent storage exhaustion

### Audio Processing

**Considerations:**
- Audio processing happens locally using Whisper
- No external API calls for transcription
- Temporary files created during processing are cleaned up

### Database Security

**SQLite Security:**
- Database file permissions should be restricted
- No network access to database
- Consider encryption at rest for sensitive deployments

## Security Best Practices

### Production Deployment

**Infrastructure:**
- Use HTTPS with valid SSL certificates
- Configure firewall to restrict access to necessary ports only
- Keep Docker and host OS updated with security patches
- Consider running behind a WAF (Web Application Firewall)

**Application Configuration:**
```bash
# Recommended security settings
MAX_FILE_SIZE_MB=100              # Limit upload size
ALLOWED_AUDIO_FORMATS=mp3,wav     # Restrict file types
LOG_LEVEL=WARNING                 # Reduce log verbosity
```

**Reverse Proxy Security Headers:**
```nginx
# Nginx security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Development Security

**Development Environment:**
- Use separate environment files for development
- Don't commit sensitive configuration to version control
- Regularly update dependencies for security patches

**Code Security:**
- Validate all inputs at application boundaries
- Use parameterized queries (though SQLAlchemy ORM provides this)
- Sanitize user inputs in logs and error messages

## Security Updates

### Update Policy

- **Critical vulnerabilities**: Patched within 24-48 hours
- **High severity**: Patched within 1 week
- **Medium/Low severity**: Included in next regular release

### Staying Informed

- **Watch this repository** for security updates
- **Check release notes** for security-related changes
- **Subscribe to security advisories** if available

## Security Testing

### Regular Testing

We recommend regular security testing:

**Automated Testing:**
- Dependency vulnerability scanning
- Static code analysis
- Container image scanning

**Manual Testing:**
- File upload validation testing
- Input validation testing
- Authentication bypass testing (if auth is added)

### Tools

**Recommended security tools:**
- `safety` - Python dependency vulnerability scanner
- `bandit` - Python security linter
- `npm audit` - Node.js dependency scanner
- `docker scan` - Container vulnerability scanner

## Security Features

### Current Security Features

- ✅ **Input validation** on all file uploads
- ✅ **File type restrictions** based on content
- ✅ **Size limits** to prevent DoS
- ✅ **Local processing** (no external data transfer)
- ✅ **Temporary file cleanup**
- ✅ **Non-root container execution**

### Planned Security Enhancements

- 🔄 **Content Security Policy** headers
- 🔄 **Rate limiting** at application level
- 🔄 **File quarantine** for uploaded files
- 🔄 **Audit logging** for security events

## Vulnerability Disclosure

### Public Disclosure

After a security vulnerability has been fixed:

1. **Security advisory** will be published
2. **CVE number** will be requested if applicable
3. **Credit** will be given to the reporter (unless they prefer anonymity)
4. **Timeline** of the vulnerability and fix will be documented

### Hall of Fame

We maintain a security hall of fame to recognize responsible security researchers who help improve our security:

*No vulnerabilities reported yet*

---

## Contact

For security-related questions or concerns:
- **Email**: `security@yourdomain.com`
- **GPG Key**: Available upon request

Thank you for helping keep Whisper Transcriber secure! 🔒
