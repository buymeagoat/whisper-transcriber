#!/bin/bash

# Development workflow script to avoid terminal blocking issues
# This script manages server startup and validation properly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Function to check if server is running
check_server() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start server in background if not running
start_server_if_needed() {
    if check_server; then
        log "Server already running on port 8000"
        return 0
    fi

    log "Starting FastAPI server in background..."
    
    # Activate virtual environment and start server in background
    source "$VENV_PATH/bin/activate"
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to be ready
    log "Waiting for server to start (PID: $SERVER_PID)..."
    for i in {1..30}; do
        if check_server; then
            success "Server started successfully!"
            echo $SERVER_PID > /tmp/whisper_server.pid
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    error "Server failed to start within 30 seconds"
    return 1
}

# Function to stop server
stop_server() {
    log "Stopping FastAPI server..."
    
    # Kill server by PID if available
    if [ -f /tmp/whisper_server.pid ]; then
        PID=$(cat /tmp/whisper_server.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm -f /tmp/whisper_server.pid
            success "Server stopped (PID: $PID)"
        else
            warning "Server PID $PID not found, trying alternative methods"
        fi
    fi
    
    # Fallback: kill by process name
    pkill -f "uvicorn.*api.main:app" || true
    
    # Wait for port to be free
    for i in {1..10}; do
        if ! check_server; then
            success "Server stopped successfully"
            return 0
        fi
        sleep 1
    done
    
    warning "Server may still be running on port 8000"
}

# Function to run validator
run_validator() {
    log "Running comprehensive validator..."
    source "$VENV_PATH/bin/activate"
    
    if python tools/comprehensive_validator.py; then
        success "Validation completed successfully!"
        return 0
    else
        error "Validation failed!"
        return 1
    fi
}

# Function to restart server
restart_server() {
    log "Restarting server..."
    stop_server
    sleep 2
    start_server_if_needed
}

# Main command handling
case "${1:-help}" in
    "start")
        start_server_if_needed
        ;;
    "stop")
        stop_server
        ;;
    "restart")
        restart_server
        ;;
    "status")
        if check_server; then
            success "Server is running on http://localhost:8000"
            if [ -f /tmp/whisper_server.pid ]; then
                PID=$(cat /tmp/whisper_server.pid)
                log "Server PID: $PID"
            fi
        else
            warning "Server is not running"
        fi
        ;;
    "validate")
        if ! check_server; then
            log "Server not running, starting it first..."
            start_server_if_needed
            sleep 3
        fi
        run_validator
        ;;
    "dev")
        log "Starting development workflow..."
        start_server_if_needed
        sleep 3
        run_validator
        success "Development environment ready!"
        log "Server running at: http://localhost:8000"
        log "Server logs: tail -f logs/server.log"
        log "To stop: $0 stop"
        ;;
    "help"|*)
        echo "Usage: $0 {start|stop|restart|status|validate|dev|help}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the FastAPI server in background"
        echo "  stop      - Stop the FastAPI server"
        echo "  restart   - Restart the FastAPI server"
        echo "  status    - Check server status"
        echo "  validate  - Run comprehensive validator (starts server if needed)"
        echo "  dev       - Full development setup (start server + validate)"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 dev        # Start server and run validation"
        echo "  $0 validate   # Run validator (auto-starts server)"
        echo "  $0 status     # Check if server is running"
        ;;
esac
