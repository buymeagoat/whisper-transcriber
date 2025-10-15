#!/bin/bash

# Docker Security Scanner for Whisper Transcriber
# Performs comprehensive security scanning of container images and configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
DOCKERFILE="$PROJECT_ROOT/Dockerfile"
SCAN_REPORT_DIR="$PROJECT_ROOT/logs/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create scan report directory
mkdir -p "$SCAN_REPORT_DIR"

echo -e "${BLUE}=== Docker Security Scanner for Whisper Transcriber ===${NC}"
echo -e "${BLUE}Timestamp: $(date)${NC}"
echo

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to scan image with Docker Scout (if available)
scan_with_scout() {
    local image=$1
    local report_file="$SCAN_REPORT_DIR/scout_${image//\//_}_$TIMESTAMP.txt"
    
    print_status "INFO" "Scanning $image with Docker Scout..."
    
    if command_exists docker && docker scout version >/dev/null 2>&1; then
        docker scout cves "$image" --format table > "$report_file" 2>&1 || {
            print_status "WARNING" "Docker Scout scan failed for $image"
            return 1
        }
        print_status "SUCCESS" "Docker Scout scan completed for $image"
        echo "  Report saved to: $report_file"
    else
        print_status "WARNING" "Docker Scout not available, skipping vulnerability scan"
        return 1
    fi
}

# Function to scan image with Trivy (if available)
scan_with_trivy() {
    local image=$1
    local report_file="$SCAN_REPORT_DIR/trivy_${image//\//_}_$TIMESTAMP.txt"
    
    print_status "INFO" "Scanning $image with Trivy..."
    
    if command_exists trivy; then
        trivy image --format table "$image" > "$report_file" 2>&1 || {
            print_status "WARNING" "Trivy scan failed for $image"
            return 1
        }
        print_status "SUCCESS" "Trivy scan completed for $image"
        echo "  Report saved to: $report_file"
    else
        print_status "WARNING" "Trivy not available, skipping vulnerability scan"
        return 1
    fi
}

# Function to check Dockerfile security best practices
check_dockerfile_security() {
    print_status "INFO" "Checking Dockerfile security best practices..."
    local issues=0
    local report_file="$SCAN_REPORT_DIR/dockerfile_security_$TIMESTAMP.txt"
    
    {
        echo "=== Dockerfile Security Analysis ==="
        echo "File: $DOCKERFILE"
        echo "Timestamp: $(date)"
        echo
        
        # Check for non-root user
        if grep -q "USER " "$DOCKERFILE"; then
            echo "[✓] Non-root user specified"
        else
            echo "[✗] No non-root user specified"
            ((issues++))
        fi
        
        # Check for specific base image tag (not latest)
        if grep -E "^FROM.*:latest" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✗] Using 'latest' tag for base image"
            ((issues++))
        elif grep -E "^FROM.*@sha256:" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✓] Using SHA256 digest for base image"
        elif grep -E "^FROM.*:[0-9]" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✓] Using specific version tag for base image"
        else
            echo "[?] Base image tag unclear"
        fi
        
        # Check for COPY/ADD security
        if grep -E "COPY.*--chown=" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✓] Using --chown in COPY instructions"
        else
            echo "[!] Consider using --chown in COPY instructions"
        fi
        
        # Check for sensitive files
        if grep -E "(ADD|COPY).*(\\.env|\\.key|\\.pem|id_rsa)" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✗] Potentially copying sensitive files"
            ((issues++))
        else
            echo "[✓] No obvious sensitive files being copied"
        fi
        
        # Check for package manager cache cleanup
        if grep -E "apt-get.*clean|rm.*-rf.*/var/lib/apt|pip.*--no-cache" "$DOCKERFILE" >/dev/null 2>&1; then
            echo "[✓] Package manager cache cleanup detected"
        else
            echo "[!] Consider cleaning package manager caches"
        fi
        
        # Check for healthcheck
        if grep -q "HEALTHCHECK" "$DOCKERFILE"; then
            echo "[✓] Healthcheck specified"
        else
            echo "[!] No healthcheck specified"
        fi
        
        echo
        echo "Total security issues found: $issues"
        
    } > "$report_file"
    
    if [ $issues -eq 0 ]; then
        print_status "SUCCESS" "Dockerfile security check completed with no critical issues"
    elif [ $issues -le 2 ]; then
        print_status "WARNING" "Dockerfile security check completed with $issues minor issues"
    else
        print_status "ERROR" "Dockerfile security check found $issues issues that need attention"
    fi
    
    echo "  Report saved to: $report_file"
    return $issues
}

# Function to check docker-compose security
check_compose_security() {
    print_status "INFO" "Checking docker-compose.yml security configuration..."
    local issues=0
    local report_file="$SCAN_REPORT_DIR/compose_security_$TIMESTAMP.txt"
    
    {
        echo "=== Docker Compose Security Analysis ==="
        echo "File: $COMPOSE_FILE"
        echo "Timestamp: $(date)"
        echo
        
        # Check for privileged containers
        if grep -q "privileged.*true" "$COMPOSE_FILE"; then
            echo "[✗] Privileged containers detected"
            ((issues++))
        else
            echo "[✓] No privileged containers"
        fi
        
        # Check for security contexts
        if grep -q "security_opt:" "$COMPOSE_FILE"; then
            echo "[✓] Security options configured"
        else
            echo "[✗] No security options configured"
            ((issues++))
        fi
        
        # Check for capability drops
        if grep -q "cap_drop:" "$COMPOSE_FILE"; then
            echo "[✓] Capability dropping configured"
        else
            echo "[✗] No capability dropping configured"
            ((issues++))
        fi
        
        # Check for read-only filesystems
        if grep -q "read_only.*true" "$COMPOSE_FILE"; then
            echo "[✓] Read-only filesystems configured"
        else
            echo "[!] No read-only filesystems configured"
        fi
        
        # Check for non-root users
        if grep -q "user:" "$COMPOSE_FILE"; then
            echo "[✓] Non-root users configured"
        else
            echo "[✗] No non-root users configured"
            ((issues++))
        fi
        
        # Check for resource limits
        if grep -q "resources:" "$COMPOSE_FILE"; then
            echo "[✓] Resource limits configured"
        else
            echo "[!] No resource limits configured"
        fi
        
        # Check for network configuration
        if grep -q "networks:" "$COMPOSE_FILE"; then
            echo "[✓] Custom networks configured"
        else
            echo "[!] No custom networks configured"
        fi
        
        # Check for volume security
        if grep -E "volumes:.*:ro" "$COMPOSE_FILE" >/dev/null 2>&1; then
            echo "[✓] Read-only volumes detected"
        else
            echo "[!] Consider using read-only volumes where appropriate"
        fi
        
        # Check for secrets in environment
        if grep -E "(PASSWORD|SECRET|KEY|TOKEN).*=" "$COMPOSE_FILE" >/dev/null 2>&1; then
            echo "[!] Hardcoded secrets detected in environment variables"
        else
            echo "[✓] No hardcoded secrets in environment variables"
        fi
        
        echo
        echo "Total security issues found: $issues"
        
    } > "$report_file"
    
    if [ $issues -eq 0 ]; then
        print_status "SUCCESS" "Docker Compose security check completed with no critical issues"
    elif [ $issues -le 2 ]; then
        print_status "WARNING" "Docker Compose security check completed with $issues minor issues"
    else
        print_status "ERROR" "Docker Compose security check found $issues issues that need attention"
    fi
    
    echo "  Report saved to: $report_file"
    return $issues
}

# Function to check running containers security
check_running_containers() {
    print_status "INFO" "Checking running container security..."
    local report_file="$SCAN_REPORT_DIR/runtime_security_$TIMESTAMP.txt"
    
    {
        echo "=== Runtime Container Security Analysis ==="
        echo "Timestamp: $(date)"
        echo
        
        # Check if containers are running
        if ! docker ps --filter "name=whisper" --format "table {{.Names}}\t{{.Status}}" | grep -q whisper; then
            echo "No Whisper containers currently running"
            return 0
        fi
        
        echo "Running Whisper containers:"
        docker ps --filter "name=whisper" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo
        
        # Check container processes
        for container in $(docker ps --filter "name=whisper" --format "{{.Names}}"); do
            echo "=== Container: $container ==="
            
            # Check user
            user=$(docker exec "$container" id 2>/dev/null || echo "Unable to check user")
            echo "User: $user"
            
            # Check capabilities
            echo "Capabilities:"
            docker exec "$container" cat /proc/1/status | grep Cap 2>/dev/null || echo "Unable to check capabilities"
            
            # Check mounted filesystems
            echo "Mounted filesystems:"
            docker exec "$container" mount | grep -E "(ro,|rw,)" 2>/dev/null || echo "Unable to check mounts"
            
            echo
        done
        
    } > "$report_file"
    
    print_status "SUCCESS" "Runtime security check completed"
    echo "  Report saved to: $report_file"
}

# Function to generate summary report
generate_summary() {
    local summary_file="$SCAN_REPORT_DIR/security_summary_$TIMESTAMP.txt"
    
    print_status "INFO" "Generating security summary report..."
    
    {
        echo "=== Docker Security Scan Summary ==="
        echo "Project: Whisper Transcriber"
        echo "Timestamp: $(date)"
        echo "Scan ID: $TIMESTAMP"
        echo
        
        echo "=== Files Scanned ==="
        echo "- Dockerfile: $DOCKERFILE"
        echo "- Docker Compose: $COMPOSE_FILE"
        echo
        
        echo "=== Reports Generated ==="
        ls -la "$SCAN_REPORT_DIR"/*"$TIMESTAMP"* 2>/dev/null || echo "No reports found"
        echo
        
        echo "=== Recommendations ==="
        echo "1. Review all security reports for critical vulnerabilities"
        echo "2. Update base images regularly"
        echo "3. Monitor for new CVEs affecting used images"
        echo "4. Implement runtime security monitoring"
        echo "5. Regular security scans in CI/CD pipeline"
        echo
        
        echo "=== Next Steps ==="
        echo "1. Address any critical or high severity vulnerabilities"
        echo "2. Update docker-compose.yml with additional security contexts if needed"
        echo "3. Consider implementing container runtime security monitoring"
        echo "4. Schedule regular security scans"
        
    } > "$summary_file"
    
    print_status "SUCCESS" "Security summary generated"
    echo "  Summary saved to: $summary_file"
}

# Main execution
main() {
    local total_issues=0
    
    # Ensure we're in the right directory
    if [ ! -f "$DOCKERFILE" ] || [ ! -f "$COMPOSE_FILE" ]; then
        print_status "ERROR" "Dockerfile or docker-compose.yml not found in project root"
        exit 1
    fi
    
    print_status "INFO" "Starting Docker security scan..."
    echo
    
    # 1. Check Dockerfile security
    check_dockerfile_security
    total_issues=$((total_issues + $?))
    echo
    
    # 2. Check docker-compose security
    check_compose_security
    total_issues=$((total_issues + $?))
    echo
    
    # 3. Check running containers (if any)
    check_running_containers
    echo
    
    # 4. Scan images if they exist locally
    for image in "whisper-transcriber-app" "redis:7-alpine" "nginx:1.25-alpine"; do
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
            echo "Image $image found locally, scanning..."
            scan_with_trivy "$image" || true
            scan_with_scout "$image" || true
            echo
        fi
    done
    
    # 5. Generate summary
    generate_summary
    
    echo
    print_status "INFO" "Docker security scan completed"
    echo -e "${BLUE}Total configuration issues found: $total_issues${NC}"
    
    if [ $total_issues -eq 0 ]; then
        print_status "SUCCESS" "All security checks passed!"
        return 0
    elif [ $total_issues -le 3 ]; then
        print_status "WARNING" "Minor security issues found - review recommended"
        return 0
    else
        print_status "ERROR" "Multiple security issues found - immediate attention required"
        return 1
    fi
}

# Run main function
main "$@"
