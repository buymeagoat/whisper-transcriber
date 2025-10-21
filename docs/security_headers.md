# Enhanced Security Headers Implementation

## Overview

The Enhanced Security Headers Middleware provides comprehensive protection against common web application attacks through HTTP security headers. This implementation includes environment-specific configurations, Content Security Policy (CSP) with nonce support, and advanced security features.

## Security Headers Implemented

### Core Security Headers

| Header | Purpose | Production Value | Development Value |
|--------|---------|------------------|-------------------|
| `X-Content-Type-Options` | Prevent MIME type sniffing | `nosniff` | `nosniff` |
| `X-Frame-Options` | Prevent clickjacking | `DENY` | `DENY` |
| `X-XSS-Protection` | XSS protection | `0` (disabled - modern browsers handle better) | `0` |
| `Referrer-Policy` | Control referrer information | `strict-origin-when-cross-origin` | `strict-origin-when-cross-origin` |
| `X-Permitted-Cross-Domain-Policies` | Adobe Flash/PDF policy | `none` | `none` |
| `X-Download-Options` | IE download behavior | `noopen` | `noopen` |

### HTTPS Security Headers

| Header | Purpose | Production | Development |
|--------|---------|------------|-------------|
| `Strict-Transport-Security` | Force HTTPS | `max-age=31536000; includeSubDomains; preload` | Not set |
| `Expect-CT` | Certificate Transparency | `max-age=86400, enforce` | Not set |

### Content Security Policy (CSP)

#### Production CSP
```
default-src 'self'; 
script-src 'self' 'nonce-{random}'; 
style-src 'self' 'nonce-{random}'; 
img-src 'self' data:; 
font-src 'self'; 
connect-src 'self'; 
media-src 'self'; 
object-src 'none'; 
base-uri 'self'; 
form-action 'self'; 
frame-ancestors 'none'; 
upgrade-insecure-requests
```

#### Development CSP
```
default-src 'self'; 
script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*; 
style-src 'self' 'unsafe-inline'; 
img-src 'self' data: blob:; 
font-src 'self' data:; 
connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*; 
media-src 'self' blob:; 
object-src 'none'; 
base-uri 'self'; 
form-action 'self'; 
frame-ancestors 'none'
```

### Permissions Policy (Feature Policy)

Disables potentially dangerous browser features:
- `accelerometer`, `ambient-light-sensor`, `autoplay`
- `battery`, `camera`, `geolocation`, `gyroscope`
- `magnetometer`, `microphone`, `midi`, `payment`
- `usb`, `web-share`, and more

### Cross-Origin Policies

| Header | Value | Purpose |
|--------|-------|---------|
| `Cross-Origin-Embedder-Policy` | `require-corp` | Isolate the origin |
| `Cross-Origin-Opener-Policy` | `same-origin` | Prevent cross-origin window access |
| `Cross-Origin-Resource-Policy` | `same-origin` | Control resource loading |

### Cache Control

| Environment | Cache-Control Header |
|-------------|---------------------|
| Production | `no-cache, no-store, must-revalidate, private` |
| Development | `no-cache` |
| Static Files | `public, max-age=31536000, immutable` |

## Configuration

### Environment Variables

```bash
# Security environment (production, development, test)
ENVIRONMENT=production

# Enable/disable HSTS (overrides environment default)
SECURITY_ENABLE_HSTS=true

# CSP reporting endpoint
CSP_REPORT_URI=/api/security/csp-report

# Enable CSP reporting
ENABLE_CSP_REPORTING=false
```

### FastAPI Integration

```python
from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    create_security_headers_middleware
)

# Method 1: Using factory function
app.add_middleware(
    EnhancedSecurityHeadersMiddleware,
    environment="production",
    excluded_paths=["/docs", "/redoc", "/openapi.json"]
)

# Method 2: Using configuration factory
security_middleware = create_security_headers_middleware(
    environment="production",
    enable_hsts=True,
    excluded_paths=["/docs", "/health", "/version"]
)
```

### Custom Headers

```python
custom_headers = {
    "X-API-Version": "2.0",
    "X-Custom-Security": "enabled"
}

app.add_middleware(
    EnhancedSecurityHeadersMiddleware,
    environment="production",
    custom_headers=custom_headers
)
```

## Security Features

### Nonce-based CSP

- Dynamic nonce generation for each request
- Prevents inline script/style injection
- Supports `script-src-attr` and `style-src-attr` directives

### Environment-Specific Configuration

#### Production Environment
- Strict CSP with nonce-only inline content
- HSTS enabled with preload
- Certificate Transparency enforcement
- Strict cross-origin policies

#### Development Environment
- Permissive CSP for localhost development
- HSTS disabled
- Inline scripts/styles allowed for debugging
- WebSocket connections to localhost allowed

#### Test Environment
- Minimal security headers
- Permissive CSP for testing frameworks
- No HSTS or strict policies

### Path-Based Exclusions

Certain endpoints can be excluded from security headers:
- `/docs` - Swagger documentation
- `/redoc` - ReDoc documentation  
- `/openapi.json` - OpenAPI specification
- `/health` - Health check endpoint
- `/version` - Version information

### Request-Specific Headers

Different headers applied based on request type:
- **API endpoints** (`/api/*`): Include `X-API-Version`
- **Static files** (`/static/*`): Modified cache control for performance
- **Health/monitoring**: Minimal caching for real-time data

## Monitoring and Statistics

The middleware tracks usage statistics:

```python
middleware = EnhancedSecurityHeadersMiddleware(app)

# Get statistics
stats = middleware.get_statistics()
# Returns:
# {
#     "headers_applied_count": 1234,
#     "excluded_requests_count": 56,
#     "total_requests": 1290
# }
```

## CSP Reporting

### Enabling CSP Reporting

```python
app.add_middleware(
    EnhancedSecurityHeadersMiddleware,
    environment="production",
    enable_csp_reporting=True,
    csp_report_uri="/api/security/csp-violations"
)
```

### CSP Violation Handler

```python
@app.post("/api/security/csp-violations")
async def handle_csp_violation(request: Request):
    """Handle CSP violation reports"""
    violation_data = await request.json()
    
    # Log violation
    logger.warning(f"CSP Violation: {violation_data}")
    
    # Store in database/monitoring system
    # ...
    
    return {"status": "received"}
```

## Testing

### Unit Tests

```bash
pytest tests/test_enhanced_security_headers.py -v
```

### Manual Testing

```bash
# Test production headers
curl -I http://localhost:8000/

# Test development headers  
ENVIRONMENT=development curl -I http://localhost:8000/

# Test excluded paths
curl -I http://localhost:8000/health
```

### Security Scanner Integration

The middleware is compatible with security scanning tools:
- **Mozilla Observatory**: Tests HTTP security headers
- **Security Headers**: Online header scanner
- **OWASP ZAP**: Web application security scanner

## Best Practices

### 1. Environment Configuration
- Always use `production` environment for live deployments
- Test CSP policies in development before production
- Monitor CSP violation reports

### 2. HSTS Deployment
- Enable HSTS only over HTTPS
- Start with shorter `max-age` values
- Submit to HSTS preload list for maximum security

### 3. CSP Implementation
- Start with permissive policies and gradually restrict
- Use nonces for inline scripts/styles
- Regularly review and update CSP directives

### 4. Monitoring
- Set up CSP violation reporting
- Monitor security header compliance
- Track middleware statistics

### 5. Performance Considerations
- Headers add minimal overhead (~1-2KB per response)
- Nonce generation is lightweight
- Consider caching static header values

## Troubleshooting

### Common Issues

1. **CSP Blocking Resources**
   - Check browser console for CSP violations
   - Add necessary sources to CSP directives
   - Use CSP reporting to identify issues

2. **HSTS Errors in Development**
   - Ensure HSTS is disabled for development
   - Clear browser HSTS cache if needed
   - Use different domains/ports for dev/prod

3. **Middleware Not Applied**
   - Check middleware order in FastAPI
   - Verify environment configuration
   - Check excluded paths configuration

### Debug Mode

Enable debug logging to trace middleware behavior:

```python
import logging
logging.getLogger("api.middlewares.enhanced_security_headers").setLevel(logging.DEBUG)
```

## Security Impact

### Protection Against:
- **XSS Attacks**: CSP and X-XSS-Protection
- **Clickjacking**: X-Frame-Options
- **MIME Sniffing**: X-Content-Type-Options
- **Information Leakage**: Referrer-Policy, Server header
- **Protocol Downgrade**: HSTS
- **Feature Abuse**: Permissions Policy
- **Cross-Origin Attacks**: CORP, COEP, COOP

### Risk Reduction:
- **High Risk**: XSS, Clickjacking, Protocol downgrade
- **Medium Risk**: Information disclosure, MIME confusion
- **Low Risk**: Feature abuse, cross-origin leakage

## Compliance

This implementation helps meet security standards:
- **OWASP Top 10**: Addresses injection, broken authentication, XSS
- **PCI DSS**: Network security, secure coding practices
- **NIST Cybersecurity Framework**: Protect function
- **ISO 27001**: Information security controls

## Version History

- **v1.0**: Initial implementation with basic headers
- **v2.0**: Enhanced CSP with nonce support
- **v3.0**: Environment-specific configuration
- **v4.0**: Permissions Policy and cross-origin headers
- **v5.0**: Statistics and monitoring capabilities

## References

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Content Security Policy Level 3](https://www.w3.org/TR/CSP3/)
- [HTTP Security Headers Reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security)