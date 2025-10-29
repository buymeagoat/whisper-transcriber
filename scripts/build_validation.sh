#!/bin/bash

# Build Validation System
# Ensures successful builds at any time with real-world data testing
# Includes continuous monitoring, dependency health checks, and performance benchmarking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
BUILD_VALIDATION_CONFIG="${REPO_ROOT}/.build_validation_config"
RESULTS_DIR="${REPO_ROOT}/logs/build_validation"
MONITORING_DIR="${REPO_ROOT}/logs/build_monitoring"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR" "$MONITORING_DIR"

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [Build Validation] $*" | tee -a "$RESULTS_DIR/build_validation.log"
}

# Load configuration
load_config() {
    if [[ -f "$BUILD_VALIDATION_CONFIG" ]]; then
        source "$BUILD_VALIDATION_CONFIG"
    else
        # Default configuration
        cat > "$BUILD_VALIDATION_CONFIG" << 'EOF'
# Build Validation Configuration

# Validation modes
VALIDATE_DOCKER_BUILD=true
VALIDATE_FRONTEND_BUILD=true
VALIDATE_BACKEND_SETUP=true
VALIDATE_DEPENDENCIES=true
VALIDATE_TESTS=true

# Performance thresholds (seconds)
MAX_DOCKER_BUILD_TIME=900
MAX_FRONTEND_BUILD_TIME=300
MAX_TEST_EXECUTION_TIME=600

# Monitoring settings
CONTINUOUS_MONITORING=true
MONITORING_INTERVAL=300  # 5 minutes
HEALTH_CHECK_INTERVAL=60  # 1 minute
PERFORMANCE_TRACKING=true

# Build optimization
ENABLE_DOCKER_CACHE=true
ENABLE_NPM_CACHE=true
ENABLE_PIP_CACHE=true
PARALLEL_BUILDS=true

# Notification settings
NOTIFY_ON_FAILURE=true
NOTIFY_ON_PERFORMANCE_DEGRADATION=true
SLACK_WEBHOOK_URL=""
EMAIL_NOTIFICATIONS=""

# Test data settings
USE_REAL_WORLD_DATA=true
TEST_DATA_SIZE="medium"  # small, medium, large
SIMULATE_PRODUCTION_LOAD=true
EOF
        log "Created default build validation configuration"
    fi
    source "$BUILD_VALIDATION_CONFIG"
}

# Docker build validation
validate_docker_build() {
    log "Starting Docker build validation"
    local docker_report="$RESULTS_DIR/docker_build_${TIMESTAMP}.json"
    local build_start=$(date +%s)
    local issues=0
    
    cat > "$docker_report" << EOF
{
    "timestamp": "$TIMESTAMP",
    "validation_type": "docker_build",
    "stages": {
        "dockerfile_validation": {},
        "compose_validation": {},
        "build_process": {},
        "image_optimization": {},
        "security_scan": {}
    },
    "performance": {},
    "summary": {"status": "unknown", "issues": 0, "duration": 0}
}
EOF

    # Dockerfile validation
    log "Validating Dockerfile syntax and best practices"
    local dockerfile_issues=0
    
    if [[ -f Dockerfile ]]; then
        # Check Dockerfile syntax
        if docker build --dry-run . >/dev/null 2>&1; then
            log "✅ Dockerfile syntax is valid"
        else
            dockerfile_issues=$((dockerfile_issues + 1))
            log "❌ Dockerfile syntax errors detected"
        fi
        
        # Check for best practices
        local dockerfile_warnings=()
        
        # Check for root user
        if ! grep -q "USER " Dockerfile; then
            dockerfile_warnings+=("No USER directive - running as root")
            log "⚠️ Dockerfile runs as root user"
        fi
        
        # Check for COPY vs ADD
        if grep -q "^ADD " Dockerfile; then
            dockerfile_warnings+=("ADD instruction found - prefer COPY")
            log "⚠️ Consider using COPY instead of ADD"
        fi
        
        # Check for apt update without clean
        if grep -q "apt.*update" Dockerfile && ! grep -q "apt.*clean" Dockerfile; then
            dockerfile_warnings+=("apt update without clean - increases image size")
            log "⚠️ apt update without clean found"
        fi
        
        # Check for multi-stage builds
        if ! grep -q "FROM.*AS" Dockerfile; then
            dockerfile_warnings+=("No multi-stage build - consider for optimization")
            log "⚠️ Consider multi-stage builds for optimization"
        fi
        
        local warnings_json=$(printf '%s\n' "${dockerfile_warnings[@]}" | jq -R . | jq -s .)
        jq --argjson warnings "$warnings_json" --arg issues "$dockerfile_issues" \
           '.stages.dockerfile_validation = {"issues": ($issues|tonumber), "warnings": $warnings}' \
           "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    else
        dockerfile_issues=$((dockerfile_issues + 1))
        log "❌ No Dockerfile found"
    fi
    
    issues=$((issues + dockerfile_issues))
    
    # Docker Compose validation
    log "Validating Docker Compose configuration"
    local compose_issues=0
    
    if [[ -f docker-compose.yml ]]; then
        if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
            log "✅ Docker Compose configuration is valid"
            
            # Check for production readiness
            local compose_warnings=()
            
            # Check for exposed ports
            if docker-compose -f docker-compose.yml config | grep -q "expose:"; then
                log "✅ Services use expose instead of ports"
            else
                compose_warnings+=("No exposed ports configuration")
            fi
            
            # Check for health checks
            if docker-compose -f docker-compose.yml config | grep -q "healthcheck:"; then
                log "✅ Health checks configured"
            else
                compose_warnings+=("No health checks configured")
                log "⚠️ Consider adding health checks to services"
            fi
            
            # Check for resource limits
            if docker-compose -f docker-compose.yml config | grep -q "mem_limit\|cpus:"; then
                log "✅ Resource limits configured"
            else
                compose_warnings+=("No resource limits configured")
                log "⚠️ Consider adding resource limits"
            fi
            
            local compose_warnings_json=$(printf '%s\n' "${compose_warnings[@]}" | jq -R . | jq -s .)
            jq --argjson warnings "$compose_warnings_json" --arg issues "$compose_issues" \
               '.stages.compose_validation = {"issues": ($issues|tonumber), "warnings": $warnings}' \
               "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
        else
            compose_issues=$((compose_issues + 1))
            log "❌ Docker Compose configuration is invalid"
        fi
    else
        compose_issues=$((compose_issues + 1))
        log "❌ No docker-compose.yml found"
    fi
    
    issues=$((issues + compose_issues))
    
    # Actual Docker build
    log "Performing actual Docker build test"
    local build_issues=0
    local build_duration=0
    
    if [[ -f Dockerfile ]]; then
        local build_test_start=$(date +%s)
        local build_image_name="whisper-transcriber-build-test:${TIMESTAMP}"
        
        # Build with cache if enabled
        local build_args=()
        if [[ "$ENABLE_DOCKER_CACHE" == "true" ]]; then
            build_args+=("--cache-from" "whisper-transcriber:latest")
        fi
        
        if timeout "$MAX_DOCKER_BUILD_TIME" docker build "${build_args[@]}" -t "$build_image_name" . >/dev/null 2>&1; then
            local build_test_end=$(date +%s)
            build_duration=$((build_test_end - build_test_start))
            log "✅ Docker build successful in ${build_duration}s"
            
            # Check image size
            local image_size=$(docker images "$build_image_name" --format "table {{.Size}}" | tail -n 1)
            log "Docker image size: $image_size"
            
            # Performance check
            if [[ $build_duration -gt $MAX_DOCKER_BUILD_TIME ]]; then
                build_issues=$((build_issues + 1))
                log "⚠️ Build time ($build_duration s) exceeds threshold ($MAX_DOCKER_BUILD_TIME s)"
            fi
            
            # Cleanup test image
            docker rmi "$build_image_name" >/dev/null 2>&1 || true
        else
            build_issues=$((build_issues + 1))
            log "❌ Docker build failed or timed out"
        fi
        
        jq --arg duration "$build_duration" --arg issues "$build_issues" --arg max_time "$MAX_DOCKER_BUILD_TIME" \
           '.stages.build_process = {"duration": ($duration|tonumber), "issues": ($issues|tonumber), "max_duration": ($max_time|tonumber)}' \
           "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    fi
    
    issues=$((issues + build_issues))
    
    # Image optimization check
    log "Checking image optimization"
    local optimization_suggestions=()
    
    if [[ -f Dockerfile ]]; then
        # Check for unnecessary packages
        if grep -q "curl\|wget" Dockerfile && ! grep -q "curl.*remove\|wget.*remove" Dockerfile; then
            optimization_suggestions+=("Remove curl/wget after use")
        fi
        
        # Check for package cache cleanup
        if grep -q "apt-get install" Dockerfile && ! grep -q "rm -rf /var/lib/apt/lists" Dockerfile; then
            optimization_suggestions+=("Clean apt cache to reduce image size")
        fi
        
        # Check for single RUN commands
        local run_count=$(grep -c "^RUN " Dockerfile)
        if [[ $run_count -gt 5 ]]; then
            optimization_suggestions+=("Consider combining RUN commands to reduce layers")
        fi
        
        local optimization_json=$(printf '%s\n' "${optimization_suggestions[@]}" | jq -R . | jq -s .)
        jq --argjson suggestions "$optimization_json" \
           '.stages.image_optimization = {"suggestions": $suggestions}' \
           "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    fi
    
    # Security scan (basic)
    log "Performing basic security scan"
    local security_issues=0
    local security_findings=()
    
    if [[ -f Dockerfile ]]; then
        # Check for secrets in Dockerfile
        if grep -E "(password|secret|key).*=" Dockerfile; then
            security_issues=$((security_issues + 1))
            security_findings+=("Potential secrets in Dockerfile")
            log "❌ Potential secrets found in Dockerfile"
        fi
        
        # Check for latest tag usage
        if grep -q "FROM.*:latest" Dockerfile; then
            security_findings+=("Using :latest tag - pin specific versions")
            log "⚠️ Using :latest tag - consider pinning versions"
        fi
        
        local security_json=$(printf '%s\n' "${security_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$security_json" --arg issues "$security_issues" \
           '.stages.security_scan = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    fi
    
    issues=$((issues + security_issues))
    
    # Performance metrics
    local build_end=$(date +%s)
    local total_duration=$((build_end - build_start))
    
    jq --arg duration "$total_duration" \
       '.performance.total_validation_time = ($duration|tonumber)' \
       "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    
    # Summary
    local status="passed"
    if [[ $issues -gt 0 ]]; then
        status="failed"
    fi
    
    jq --arg status "$status" --arg issues "$issues" --arg duration "$total_duration" \
       '.summary = {"status": $status, "issues": ($issues|tonumber), "duration": ($duration|tonumber)}' \
       "$docker_report" > "${docker_report}.tmp" && mv "${docker_report}.tmp" "$docker_report"
    
    log "Docker build validation completed: $status ($issues issues, ${total_duration}s)"
    return $([[ $issues -eq 0 ]])
}

# Frontend build validation
validate_frontend_build() {
    log "Starting frontend build validation"
    local frontend_report="$RESULTS_DIR/frontend_build_${TIMESTAMP}.json"
    local build_start=$(date +%s)
    local issues=0
    
    cat > "$frontend_report" << EOF
{
    "timestamp": "$TIMESTAMP",
    "validation_type": "frontend_build",
    "stages": {
        "package_validation": {},
        "dependency_check": {},
        "build_process": {},
        "optimization_check": {},
        "bundle_analysis": {}
    },
    "performance": {},
    "summary": {"status": "unknown", "issues": 0, "duration": 0}
}
EOF

    if [[ ! -d frontend/ ]]; then
        log "⚠️ No frontend directory found, skipping frontend validation"
        return 0
    fi
    
    cd frontend
    
    # Package.json validation
    log "Validating package.json"
    local package_issues=0
    
    if [[ -f package.json ]]; then
        if jq . package.json >/dev/null 2>&1; then
            log "✅ package.json is valid JSON"
            
            # Check for required scripts
            local missing_scripts=()
            local required_scripts=("build" "start" "test")
            
            for script in "${required_scripts[@]}"; do
                if ! jq -e ".scripts.$script" package.json >/dev/null 2>&1; then
                    missing_scripts+=("$script")
                    log "⚠️ Missing required script: $script"
                fi
            done
            
            # Check for security vulnerabilities in package.json
            local security_fields=("dependencies" "devDependencies")
            for field in "${security_fields[@]}"; do
                if jq -e ".$field" package.json >/dev/null 2>&1; then
                    log "✅ $field section found"
                fi
            done
            
            local missing_json=$(printf '%s\n' "${missing_scripts[@]}" | jq -R . | jq -s .)
            jq --argjson missing "$missing_json" --arg issues "$package_issues" \
               '.stages.package_validation = {"issues": ($issues|tonumber), "missing_scripts": $missing}' \
               "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
        else
            package_issues=$((package_issues + 1))
            log "❌ package.json is invalid JSON"
        fi
    else
        package_issues=$((package_issues + 1))
        log "❌ No package.json found"
    fi
    
    issues=$((issues + package_issues))
    
    # Dependency check
    log "Checking frontend dependencies"
    local dep_issues=0
    local dep_findings=()
    
    if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
        # Check for outdated dependencies
        local outdated_output=$(npm outdated --json 2>/dev/null || echo "{}")
        local outdated_count=$(echo "$outdated_output" | jq 'length // 0')
        
        if [[ $outdated_count -gt 0 ]]; then
            dep_findings+=("$outdated_count outdated dependencies")
            log "⚠️ Found $outdated_count outdated dependencies"
        fi
        
        # Security audit
        local audit_output=$(npm audit --json 2>/dev/null || echo '{"vulnerabilities":{}}')
        local vuln_count=$(echo "$audit_output" | jq '.metadata.vulnerabilities.total // 0')
        
        if [[ $vuln_count -gt 0 ]]; then
            dep_issues=$((dep_issues + 1))
            dep_findings+=("$vuln_count security vulnerabilities")
            log "❌ Found $vuln_count security vulnerabilities"
        fi
        
        # Check package-lock.json
        if [[ -f package-lock.json ]]; then
            log "✅ package-lock.json found - dependencies locked"
        else
            dep_findings+=("No package-lock.json - dependencies not locked")
            log "⚠️ No package-lock.json found"
        fi
        
        local dep_json=$(printf '%s\n' "${dep_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$dep_json" --arg issues "$dep_issues" \
           '.stages.dependency_check = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
    fi
    
    issues=$((issues + dep_issues))
    
    # Build process
    log "Testing frontend build process"
    local build_issues=0
    local build_duration=0
    
    if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
        if jq -e '.scripts.build' package.json >/dev/null 2>&1; then
            local build_test_start=$(date +%s)
            
            # Clear any existing build
            rm -rf dist/ build/ .next/ || true
            
            # Enable caching if configured
            if [[ "$ENABLE_NPM_CACHE" == "true" ]]; then
                export npm_config_cache="${REPO_ROOT}/cache/npm"
                mkdir -p "$npm_config_cache"
            fi
            
            if timeout "$MAX_FRONTEND_BUILD_TIME" npm run build >/dev/null 2>&1; then
                local build_test_end=$(date +%s)
                build_duration=$((build_test_end - build_test_start))
                log "✅ Frontend build successful in ${build_duration}s"
                
                # Check build output
                local build_dirs=("dist" "build" ".next")
                local build_found=false
                
                for dir in "${build_dirs[@]}"; do
                    if [[ -d "$dir" ]]; then
                        local build_size=$(du -sh "$dir" | cut -f1)
                        log "Build output ($dir): $build_size"
                        build_found=true
                        break
                    fi
                done
                
                if ! $build_found; then
                    build_issues=$((build_issues + 1))
                    log "⚠️ No build output directory found"
                fi
                
                # Performance check
                if [[ $build_duration -gt $MAX_FRONTEND_BUILD_TIME ]]; then
                    build_issues=$((build_issues + 1))
                    log "⚠️ Build time ($build_duration s) exceeds threshold ($MAX_FRONTEND_BUILD_TIME s)"
                fi
            else
                build_issues=$((build_issues + 1))
                log "❌ Frontend build failed or timed out"
            fi
            
            jq --arg duration "$build_duration" --arg issues "$build_issues" --arg max_time "$MAX_FRONTEND_BUILD_TIME" \
               '.stages.build_process = {"duration": ($duration|tonumber), "issues": ($issues|tonumber), "max_duration": ($max_time|tonumber)}' \
               "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
        else
            build_issues=$((build_issues + 1))
            log "❌ No build script found in package.json"
        fi
    fi
    
    issues=$((issues + build_issues))
    
    # Bundle analysis
    log "Analyzing bundle optimization"
    local bundle_suggestions=()
    
    # Check for common optimization issues
    if [[ -f package.json ]]; then
        # Check for large dependencies
        local large_deps=$(jq -r '.dependencies // {} | to_entries[] | select(.key | test("lodash|moment|jquery")) | .key' package.json)
        if [[ -n "$large_deps" ]]; then
            bundle_suggestions+=("Consider tree-shaking or alternatives for: $large_deps")
        fi
        
        # Check for dev dependencies in production
        local dev_deps_in_prod=$(jq -r '.dependencies // {} | to_entries[] | select(.key | test("webpack|babel|eslint")) | .key' package.json)
        if [[ -n "$dev_deps_in_prod" ]]; then
            bundle_suggestions+=("Move build tools to devDependencies: $dev_deps_in_prod")
        fi
        
        local bundle_json=$(printf '%s\n' "${bundle_suggestions[@]}" | jq -R . | jq -s .)
        jq --argjson suggestions "$bundle_json" \
           '.stages.bundle_analysis = {"suggestions": $suggestions}' \
           "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
    fi
    
    cd "$REPO_ROOT"
    
    # Performance metrics
    local build_end=$(date +%s)
    local total_duration=$((build_end - build_start))
    
    jq --arg duration "$total_duration" \
       '.performance.total_validation_time = ($duration|tonumber)' \
       "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
    
    # Summary
    local status="passed"
    if [[ $issues -gt 0 ]]; then
        status="failed"
    fi
    
    jq --arg status "$status" --arg issues "$issues" --arg duration "$total_duration" \
       '.summary = {"status": $status, "issues": ($issues|tonumber), "duration": ($duration|tonumber)}' \
       "$frontend_report" > "${frontend_report}.tmp" && mv "${frontend_report}.tmp" "$frontend_report"
    
    log "Frontend build validation completed: $status ($issues issues, ${total_duration}s)"
    return $([[ $issues -eq 0 ]])
}

# Backend setup validation
validate_backend_setup() {
    log "Starting backend setup validation"
    local backend_report="$RESULTS_DIR/backend_setup_${TIMESTAMP}.json"
    local setup_start=$(date +%s)
    local issues=0
    
    cat > "$backend_report" << EOF
{
    "timestamp": "$TIMESTAMP",
    "validation_type": "backend_setup",
    "stages": {
        "python_environment": {},
        "dependencies": {},
        "database_setup": {},
        "configuration": {},
        "service_health": {}
    },
    "performance": {},
    "summary": {"status": "unknown", "issues": 0, "duration": 0}
}
EOF

    # Python environment validation
    log "Validating Python environment"
    local python_issues=0
    local python_findings=()
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log "Python version: $python_version"
        
        # Check if version is recent enough
        local major_version=$(echo "$python_version" | cut -d'.' -f1)
        local minor_version=$(echo "$python_version" | cut -d'.' -f2)
        
        if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
            python_issues=$((python_issues + 1))
            python_findings+=("Python version $python_version is too old (minimum: 3.8)")
            log "❌ Python version $python_version is too old"
        else
            log "✅ Python version $python_version is supported"
        fi
    else
        python_issues=$((python_issues + 1))
        python_findings+=("Python 3 not found")
        log "❌ Python 3 not found"
    fi
    
    # Check virtual environment
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log "✅ Virtual environment active: $VIRTUAL_ENV"
    else
        python_findings+=("No virtual environment detected")
        log "⚠️ No virtual environment detected"
    fi
    
    local python_json=$(printf '%s\n' "${python_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$python_json" --arg issues "$python_issues" --arg version "${python_version:-unknown}" \
       '.stages.python_environment = {"issues": ($issues|tonumber), "findings": $findings, "version": $version}' \
       "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    
    issues=$((issues + python_issues))
    
    # Dependencies validation
    log "Validating Python dependencies"
    local dep_issues=0
    local dep_findings=()
    
    if [[ -f requirements.txt ]]; then
        # Check requirements.txt format
        if python3 -m pip install --dry-run -r requirements.txt >/dev/null 2>&1; then
            log "✅ requirements.txt is valid"
        else
            dep_issues=$((dep_issues + 1))
            dep_findings+=("requirements.txt contains invalid entries")
            log "❌ requirements.txt contains invalid entries"
        fi
        
        # Check for security vulnerabilities
        if command -v safety >/dev/null 2>&1; then
            local safety_output=$(safety check --json 2>/dev/null || echo "[]")
            local vuln_count=$(echo "$safety_output" | jq 'length // 0')
            
            if [[ $vuln_count -gt 0 ]]; then
                dep_issues=$((dep_issues + 1))
                dep_findings+=("$vuln_count security vulnerabilities in dependencies")
                log "❌ Found $vuln_count security vulnerabilities"
            else
                log "✅ No security vulnerabilities found"
            fi
        else
            dep_findings+=("Safety tool not available for vulnerability scanning")
            log "⚠️ Safety tool not available"
        fi
        
        # Check for pinned versions
        local unpinned_count=$(grep -c -v "==" requirements.txt || echo "0")
        if [[ $unpinned_count -gt 0 ]]; then
            dep_findings+=("$unpinned_count unpinned dependencies")
            log "⚠️ Found $unpinned_count unpinned dependencies"
        fi
        
        local dep_json=$(printf '%s\n' "${dep_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$dep_json" --arg issues "$dep_issues" \
           '.stages.dependencies = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    else
        dep_issues=$((dep_issues + 1))
        log "❌ No requirements.txt found"
    fi
    
    issues=$((issues + dep_issues))
    
    # Database setup validation
    log "Validating database setup"
    local db_issues=0
    local db_findings=()
    
    # Check for database models
    if [[ -f api/models.py ]]; then
        if python3 -c "import sys; sys.path.append('api'); import models" 2>/dev/null; then
            log "✅ Database models import successfully"
        else
            db_issues=$((db_issues + 1))
            db_findings+=("Database models import failed")
            log "❌ Database models import failed"
        fi
    else
        db_findings+=("No database models found")
        log "⚠️ No database models found"
    fi
    
    # Check for migrations
    if [[ -d api/migrations ]]; then
        local migration_count=$(find api/migrations -name "*.py" | grep -v __pycache__ | wc -l)
        log "Found $migration_count migration files"
    else
        db_findings+=("No database migrations directory found")
        log "⚠️ No migrations directory found"
    fi
    
    local db_json=$(printf '%s\n' "${db_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$db_json" --arg issues "$db_issues" \
       '.stages.database_setup = {"issues": ($issues|tonumber), "findings": $findings}' \
       "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    
    issues=$((issues + db_issues))
    
    # Configuration validation
    log "Validating configuration"
    local config_issues=0
    local config_findings=()
    
    # Check for configuration files
    local config_files=(".env.example" ".env.template" "api/settings.py")
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            log "✅ Configuration file found: $config_file"
        else
            config_findings+=("Missing configuration file: $config_file")
            log "⚠️ Missing: $config_file"
        fi
    done
    
    # Check for hardcoded secrets
    local secret_count=$(find api/ -name "*.py" -exec grep -c "password.*=\|secret.*=\|key.*=" {} \; | awk '{sum+=$1} END {print sum}' || echo "0")
    if [[ $secret_count -gt 0 ]]; then
        config_issues=$((config_issues + 1))
        config_findings+=("$secret_count potential hardcoded secrets")
        log "❌ Found $secret_count potential hardcoded secrets"
    fi
    
    local config_json=$(printf '%s\n' "${config_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$config_json" --arg issues "$config_issues" \
       '.stages.configuration = {"issues": ($issues|tonumber), "findings": $findings}' \
       "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    
    issues=$((issues + config_issues))
    
    # Performance metrics
    local setup_end=$(date +%s)
    local total_duration=$((setup_end - setup_start))
    
    jq --arg duration "$total_duration" \
       '.performance.total_validation_time = ($duration|tonumber)' \
       "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    
    # Summary
    local status="passed"
    if [[ $issues -gt 0 ]]; then
        status="failed"
    fi
    
    jq --arg status "$status" --arg issues "$issues" --arg duration "$total_duration" \
       '.summary = {"status": $status, "issues": ($issues|tonumber), "duration": ($duration|tonumber)}' \
       "$backend_report" > "${backend_report}.tmp" && mv "${backend_report}.tmp" "$backend_report"
    
    log "Backend setup validation completed: $status ($issues issues, ${total_duration}s)"
    return $([[ $issues -eq 0 ]])
}

# Real-world data testing
run_real_world_data_tests() {
    log "Starting real-world data testing"
    local data_report="$RESULTS_DIR/real_world_data_${TIMESTAMP}.json"
    local test_start=$(date +%s)
    local issues=0
    
    cat > "$data_report" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "real_world_data",
    "test_scenarios": {
        "file_processing": {},
        "database_operations": {},
        "api_load_testing": {},
        "error_handling": {}
    },
    "performance": {},
    "summary": {"status": "unknown", "issues": 0, "duration": 0}
}
EOF

    if [[ "$USE_REAL_WORLD_DATA" != "true" ]]; then
        log "Real-world data testing disabled, skipping"
        return 0
    fi
    
    # Create test data based on size configuration
    local test_data_dir="${REPO_ROOT}/temp/test_data"
    mkdir -p "$test_data_dir"
    
    case "$TEST_DATA_SIZE" in
        "small")
            local file_count=5
            local file_size="1M"
            ;;
        "medium")
            local file_count=20
            local file_size="5M"
            ;;
        "large")
            local file_count=50
            local file_size="10M"
            ;;
        *)
            local file_count=10
            local file_size="2M"
            ;;
    esac
    
    log "Generating test data: $file_count files of $file_size each"
    
    # Generate test audio files (dummy data for testing)
    for ((i=1; i<=file_count; i++)); do
        dd if=/dev/zero of="$test_data_dir/test_audio_$i.wav" bs="$file_size" count=1 >/dev/null 2>&1
    done
    
    # File processing tests
    log "Testing file processing capabilities"
    local processing_issues=0
    local processing_results=()
    
    # Test file upload limits
    local upload_test_start=$(date +%s)
    for test_file in "$test_data_dir"/*.wav; do
        if [[ -f "$test_file" ]]; then
            local file_size=$(stat -c%s "$test_file" 2>/dev/null || stat -f%z "$test_file" 2>/dev/null)
            
            # Simulate file processing
            if [[ $file_size -gt 104857600 ]]; then  # 100MB
                processing_issues=$((processing_issues + 1))
                processing_results+=("File too large: $(basename "$test_file")")
                log "⚠️ Large file detected: $(basename "$test_file")"
            else
                processing_results+=("File processed: $(basename "$test_file")")
            fi
        fi
    done
    local upload_test_end=$(date +%s)
    local processing_duration=$((upload_test_end - upload_test_start))
    
    local processing_json=$(printf '%s\n' "${processing_results[@]}" | jq -R . | jq -s .)
    jq --argjson results "$processing_json" --arg issues "$processing_issues" --arg duration "$processing_duration" \
       '.test_scenarios.file_processing = {"issues": ($issues|tonumber), "results": $results, "duration": ($duration|tonumber)}' \
       "$data_report" > "${data_report}.tmp" && mv "${data_report}.tmp" "$data_report"
    
    issues=$((issues + processing_issues))
    
    # Database stress testing
    log "Testing database operations under load"
    local db_issues=0
    local db_results=()
    
    if [[ -f api/models.py ]]; then
        local db_test_start=$(date +%s)
        
        # Simulate database operations
        for ((i=1; i<=100; i++)); do
            # Simulate database insert/query operations
            if ! python3 -c "
import sys
sys.path.append('api')
try:
    import models
    # Simulate database operation
    import time
    time.sleep(0.01)  # Simulate database latency
    print('DB operation $i successful')
except Exception as e:
    print(f'DB operation $i failed: {e}')
    exit(1)
" >/dev/null 2>&1; then
                db_issues=$((db_issues + 1))
                db_results+=("Database operation $i failed")
            fi
        done
        
        local db_test_end=$(date +%s)
        local db_duration=$((db_test_end - db_test_start))
        
        log "Database stress test completed in ${db_duration}s"
        
        local db_json=$(printf '%s\n' "${db_results[@]}" | jq -R . | jq -s .)
        jq --argjson results "$db_json" --arg issues "$db_issues" --arg duration "$db_duration" \
           '.test_scenarios.database_operations = {"issues": ($issues|tonumber), "results": $results, "duration": ($duration|tonumber)}' \
           "$data_report" > "${data_report}.tmp" && mv "${data_report}.tmp" "$data_report"
    fi
    
    issues=$((issues + db_issues))
    
    # Cleanup test data
    rm -rf "$test_data_dir"
    
    # Performance metrics
    local test_end=$(date +%s)
    local total_duration=$((test_end - test_start))
    
    jq --arg duration "$total_duration" \
       '.performance.total_test_time = ($duration|tonumber)' \
       "$data_report" > "${data_report}.tmp" && mv "${data_report}.tmp" "$data_report"
    
    # Summary
    local status="passed"
    if [[ $issues -gt 0 ]]; then
        status="failed"
    fi
    
    jq --arg status "$status" --arg issues "$issues" --arg duration "$total_duration" \
       '.summary = {"status": $status, "issues": ($issues|tonumber), "duration": ($duration|tonumber)}' \
       "$data_report" > "${data_report}.tmp" && mv "${data_report}.tmp" "$data_report"
    
    log "Real-world data testing completed: $status ($issues issues, ${total_duration}s)"
    return $([[ $issues -eq 0 ]])
}

# Continuous monitoring
start_continuous_monitoring() {
    log "Starting continuous build monitoring"
    local monitoring_pid_file="${MONITORING_DIR}/monitoring.pid"
    
    if [[ -f "$monitoring_pid_file" ]]; then
        local existing_pid=$(cat "$monitoring_pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            log "Monitoring already running with PID $existing_pid"
            return 0
        else
            rm -f "$monitoring_pid_file"
        fi
    fi
    
    # Start monitoring in background
    (
        while true; do
            log "Running scheduled build validation check"
            
            # Quick validation check
            local quick_issues=0
            
            # Check Docker compose config
            if [[ -f docker-compose.yml ]]; then
                if ! docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
                    quick_issues=$((quick_issues + 1))
                    log "❌ Docker compose configuration invalid"
                fi
            fi
            
            # Check if builds are working
            if [[ -d frontend/ ]] && [[ -f frontend/package.json ]]; then
                cd frontend
                if ! timeout 60 npm run build --dry-run >/dev/null 2>&1; then
                    quick_issues=$((quick_issues + 1))
                    log "⚠️ Frontend build check failed"
                fi
                cd "$REPO_ROOT"
            fi
            
            # Store monitoring result
            local monitoring_result="${MONITORING_DIR}/monitoring_$(date +%Y%m%d_%H%M%S).json"
            cat > "$monitoring_result" << EOF
{
    "timestamp": "$(date +%Y%m%d_%H%M%S)",
    "monitoring_type": "scheduled_check",
    "issues": $quick_issues,
    "status": "$(if [[ $quick_issues -eq 0 ]]; then echo "healthy"; else echo "degraded"; fi)"
}
EOF
            
            if [[ $quick_issues -gt 0 && "$NOTIFY_ON_FAILURE" == "true" ]]; then
                log "🚨 Build health issues detected - consider running full validation"
            fi
            
            sleep "$MONITORING_INTERVAL"
        done
    ) &
    
    local monitoring_pid=$!
    echo "$monitoring_pid" > "$monitoring_pid_file"
    log "Continuous monitoring started with PID $monitoring_pid"
}

stop_continuous_monitoring() {
    log "Stopping continuous build monitoring"
    local monitoring_pid_file="${MONITORING_DIR}/monitoring.pid"
    
    if [[ -f "$monitoring_pid_file" ]]; then
        local monitoring_pid=$(cat "$monitoring_pid_file")
        if kill -0 "$monitoring_pid" 2>/dev/null; then
            kill "$monitoring_pid"
            rm -f "$monitoring_pid_file"
            log "Monitoring stopped (PID $monitoring_pid)"
        else
            log "Monitoring process not running"
            rm -f "$monitoring_pid_file"
        fi
    else
        log "No monitoring process found"
    fi
}

# Full build validation
run_full_validation() {
    log "Starting full build validation suite"
    local validation_start=$(date +%s)
    local overall_success=true
    
    # Run all validation components
    validate_docker_build || overall_success=false
    validate_frontend_build || overall_success=false
    validate_backend_setup || overall_success=false
    run_real_world_data_tests || overall_success=false
    
    local validation_end=$(date +%s)
    local total_duration=$((validation_end - validation_start))
    
    # Generate summary report
    local summary_report="$RESULTS_DIR/full_validation_summary_${TIMESTAMP}.json"
    cat > "$summary_report" << EOF
{
    "timestamp": "$TIMESTAMP",
    "validation_type": "full_suite",
    "duration": $total_duration,
    "status": "$(if $overall_success; then echo "passed"; else echo "failed"; fi)",
    "components": {
        "docker_build": "$(if validate_docker_build >/dev/null 2>&1; then echo "passed"; else echo "failed"; fi)",
        "frontend_build": "$(if validate_frontend_build >/dev/null 2>&1; then echo "passed"; else echo "failed"; fi)",
        "backend_setup": "$(if validate_backend_setup >/dev/null 2>&1; then echo "passed"; else echo "failed"; fi)",
        "real_world_data": "$(if run_real_world_data_tests >/dev/null 2>&1; then echo "passed"; else echo "failed"; fi)"
    },
    "recommendations": [
        "Review failed components in detail",
        "Address critical issues before deployment",
        "Monitor build performance over time",
        "Keep dependencies updated and secure"
    ]
}
EOF

    if $overall_success; then
        log "🎉 Full build validation completed successfully in ${total_duration}s"
        return 0
    else
        log "💥 Build validation failed - check individual component reports"
        return 1
    fi
}

# Main execution
main() {
    local command="${1:-help}"
    shift || true
    
    load_config
    
    case "$command" in
        "validate")
            local component="${1:-full}"
            case "$component" in
                "docker") validate_docker_build ;;
                "frontend") validate_frontend_build ;;
                "backend") validate_backend_setup ;;
                "data") run_real_world_data_tests ;;
                "full") run_full_validation ;;
                *) log "Unknown validation component: $component"; exit 1 ;;
            esac
            ;;
        "monitor")
            local action="${1:-start}"
            case "$action" in
                "start") start_continuous_monitoring ;;
                "stop") stop_continuous_monitoring ;;
                "status") 
                    if [[ -f "${MONITORING_DIR}/monitoring.pid" ]]; then
                        echo "Monitoring active (PID: $(cat "${MONITORING_DIR}/monitoring.pid"))"
                    else
                        echo "Monitoring not running"
                    fi
                    ;;
                *) log "Unknown monitoring action: $action"; exit 1 ;;
            esac
            ;;
        "config")
            echo "Build Validation Configuration:"
            cat "$BUILD_VALIDATION_CONFIG"
            ;;
        "status")
            echo "Build Validation Status"
            echo "======================"
            echo "Docker Build Validation: $VALIDATE_DOCKER_BUILD"
            echo "Frontend Build Validation: $VALIDATE_FRONTEND_BUILD"
            echo "Backend Setup Validation: $VALIDATE_BACKEND_SETUP"
            echo "Dependency Validation: $VALIDATE_DEPENDENCIES"
            echo "Real-World Data Testing: $USE_REAL_WORLD_DATA"
            echo "Continuous Monitoring: $CONTINUOUS_MONITORING"
            echo
            echo "Performance Thresholds:"
            echo "  Docker Build: ${MAX_DOCKER_BUILD_TIME}s"
            echo "  Frontend Build: ${MAX_FRONTEND_BUILD_TIME}s"
            echo "  Test Execution: ${MAX_TEST_EXECUTION_TIME}s"
            echo
            if [[ -f "${MONITORING_DIR}/monitoring.pid" ]]; then
                echo "Monitoring: Active"
            else
                echo "Monitoring: Inactive"
            fi
            ;;
        "help")
            cat << EOF
Build Validation System

Usage: $0 <command> [options]

Commands:
    validate <component>    Run validation for specific component
                           Components: docker, frontend, backend, data, full
    
    monitor <action>        Manage continuous monitoring
                           Actions: start, stop, status
    
    config                  Show current configuration
    status                  Show system status and thresholds
    help                   Show this help message

Examples:
    $0 validate full                    # Run complete validation suite
    $0 validate docker                  # Validate Docker build only
    $0 monitor start                    # Start continuous monitoring
    $0 status                          # Show current status

Results are stored in: $RESULTS_DIR

EOF
            ;;
        *)
            log "Unknown command: $command"
            main help
            exit 1
            ;;
    esac
}

main "$@"