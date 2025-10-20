#!/bin/bash
# SSL Certificate Setup Script for Production Deployment
# Supports both Let's Encrypt and self-signed certificates

set -euo pipefail

# Configuration
DOMAIN="${DOMAIN:-yourdomain.com}"
EMAIL="${SSL_EMAIL:-admin@yourdomain.com}"
SSL_DIR="./ssl"
NGINX_DIR="./nginx"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Create SSL directory
create_ssl_directory() {
    log "Creating SSL directory structure..."
    mkdir -p "${SSL_DIR}"
    chmod 700 "${SSL_DIR}"
}

# Generate self-signed certificate for development/testing
generate_self_signed() {
    log "Generating self-signed certificate for ${DOMAIN}..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${SSL_DIR}/privkey.pem" \
        -out "${SSL_DIR}/fullchain.pem" \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=${DOMAIN}"
    
    cp "${SSL_DIR}/fullchain.pem" "${SSL_DIR}/chain.pem"
    
    chmod 600 "${SSL_DIR}/privkey.pem"
    chmod 644 "${SSL_DIR}/fullchain.pem" "${SSL_DIR}/chain.pem"
    
    warn "Self-signed certificate generated. This should only be used for development!"
    warn "Browsers will show security warnings for self-signed certificates."
}

# Setup Let's Encrypt certificate
setup_letsencrypt() {
    log "Setting up Let's Encrypt certificate for ${DOMAIN}..."
    
    # Check if certbot is available
    if ! command -v certbot &> /dev/null; then
        error "certbot is not installed. Please install certbot first."
    fi
    
    # Create webroot directory for ACME challenge
    mkdir -p /var/www/certbot
    
    # Get certificate
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "${EMAIL}" \
        --agree-tos \
        --no-eff-email \
        --domains "${DOMAIN}" \
        --domains "www.${DOMAIN}"
    
    # Copy certificates to SSL directory
    cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "${SSL_DIR}/"
    cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "${SSL_DIR}/"
    cp "/etc/letsencrypt/live/${DOMAIN}/chain.pem" "${SSL_DIR}/"
    
    chmod 600 "${SSL_DIR}/privkey.pem"
    chmod 644 "${SSL_DIR}/fullchain.pem" "${SSL_DIR}/chain.pem"
    
    log "Let's Encrypt certificate installed successfully!"
}

# Verify certificate installation
verify_certificate() {
    log "Verifying certificate installation..."
    
    if [[ ! -f "${SSL_DIR}/privkey.pem" ]] || [[ ! -f "${SSL_DIR}/fullchain.pem" ]]; then
        error "Certificate files not found in ${SSL_DIR}/"
    fi
    
    # Check certificate validity
    if openssl x509 -in "${SSL_DIR}/fullchain.pem" -text -noout &> /dev/null; then
        log "Certificate files are valid"
        
        # Show certificate info
        log "Certificate information:"
        openssl x509 -in "${SSL_DIR}/fullchain.pem" -text -noout | grep -E "(Subject:|Not Before|Not After)"
    else
        error "Certificate files are invalid"
    fi
}

# Update nginx configuration with domain
update_nginx_config() {
    log "Updating nginx configuration with domain ${DOMAIN}..."
    
    # Replace domain placeholder in nginx config
    if [[ -f "${NGINX_DIR}/conf.d/default.conf" ]]; then
        sed -i "s/\${DOMAIN}/${DOMAIN}/g" "${NGINX_DIR}/conf.d/default.conf"
        log "Nginx configuration updated"
    else
        warn "Nginx configuration file not found"
    fi
}

# Setup certificate renewal (for Let's Encrypt)
setup_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > "${SSL_DIR}/renew.sh" << 'EOF'
#!/bin/bash
# Let's Encrypt Certificate Renewal Script

certbot renew --quiet --post-hook "docker-compose -f docker-compose.prod.yml restart nginx"

# Copy renewed certificates
DOMAIN=$(grep -oP 'server_name \K[^;]*' nginx/conf.d/default.conf | head -1)
if [[ -f "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ]]; then
    cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" ssl/
    cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ssl/
    cp "/etc/letsencrypt/live/${DOMAIN}/chain.pem" ssl/
    chmod 600 ssl/privkey.pem
    chmod 644 ssl/fullchain.pem ssl/chain.pem
fi
EOF
    
    chmod +x "${SSL_DIR}/renew.sh"
    
    log "Renewal script created at ${SSL_DIR}/renew.sh"
    log "Add this to crontab for automatic renewal:"
    log "0 3 * * * /path/to/whisper-transcriber/${SSL_DIR}/renew.sh"
}

# Main function
main() {
    log "Starting SSL certificate setup for Whisper Transcriber..."
    log "Domain: ${DOMAIN}"
    log "Email: ${EMAIL}"
    
    create_ssl_directory
    
    # Ask user for certificate type
    echo
    echo "Choose certificate type:"
    echo "1) Let's Encrypt (recommended for production)"
    echo "2) Self-signed (development/testing only)"
    echo
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            setup_letsencrypt
            setup_renewal
            ;;
        2)
            generate_self_signed
            ;;
        *)
            error "Invalid choice"
            ;;
    esac
    
    verify_certificate
    update_nginx_config
    
    log "SSL certificate setup completed successfully!"
    log "You can now start the production environment with:"
    log "docker-compose -f docker-compose.prod.yml up -d"
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
