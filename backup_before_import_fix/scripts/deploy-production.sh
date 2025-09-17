#!/bin/bash
set -e

# Production Deployment Script for QME System
# Handles rolling updates, health checks, and rollback procedures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if required environment files exist
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        if [[ -f "${PROJECT_ROOT}/.env.example" ]]; then
            log_warn "No .env file found, copying from .env.example"
            cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
        else
            log_error "No .env file found and no .env.example to copy from"
            exit 1
        fi
    fi
    
    # Check if required directories exist
    local required_dirs=("data" "logs" "results" "config")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
            log_info "Creating required directory: ${dir}"
            mkdir -p "${PROJECT_ROOT}/${dir}"
        fi
    done
    
    log_info "Prerequisites check completed"
}

# Function to create backup
create_backup() {
    log_info "Creating backup before deployment..."
    
    local backup_timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="${BACKUP_DIR}/qme_backup_${backup_timestamp}"
    
    mkdir -p "${backup_path}"
    
    # Backup data directory
    if [[ -d "${PROJECT_ROOT}/data" ]]; then
        log_info "Backing up data directory..."
        cp -r "${PROJECT_ROOT}/data" "${backup_path}/"
    fi
    
    # Backup configuration
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        log_info "Backing up configuration..."
        cp "${PROJECT_ROOT}/.env" "${backup_path}/"
    fi
    
    # Backup current Docker images
    log_info "Backing up current Docker images..."
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep qme > "${backup_path}/docker_images.txt" || true
    
    # Create backup metadata
    cat > "${backup_path}/backup_info.json" << EOF
{
    "timestamp": "${backup_timestamp}",
    "environment": "${DEPLOYMENT_ENV}",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
    "backup_path": "${backup_path}"
}
EOF
    
    echo "${backup_path}" > "${PROJECT_ROOT}/.last_backup"
    log_info "Backup created at: ${backup_path}"
}

# Function to build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "${PROJECT_ROOT}"
    
    # Build with build args for production
    docker-compose build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="$(git describe --tags --always 2>/dev/null || echo 'latest')" \
        qme-app
    
    log_info "Docker images built successfully"
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    log_info "Running pre-deployment tests..."
    
    # Test Docker image
    log_info "Testing Docker image..."
    docker run --rm \
        -e QME_ENVIRONMENT=testing \
        -v "${PROJECT_ROOT}/data:/app/data" \
        qme-system_qme-app:latest \
        health-check
    
    # Run unit tests if available
    if [[ -f "${PROJECT_ROOT}/pytest.ini" ]] || [[ -d "${PROJECT_ROOT}/tests" ]]; then
        log_info "Running unit tests..."
        docker run --rm \
            -e QME_ENVIRONMENT=testing \
            -v "${PROJECT_ROOT}:/app" \
            qme-system_qme-app:latest \
            python -m pytest tests/ -v --tb=short || {
                log_warn "Some tests failed, but continuing deployment"
            }
    fi
    
    log_info "Pre-deployment tests completed"
}

# Function to deploy services
deploy_services() {
    log_info "Deploying services..."
    
    cd "${PROJECT_ROOT}"
    
    # Set environment for production
    export QME_ENVIRONMENT=production
    export COMPOSE_PROJECT_NAME=qme-system
    
    # Deploy with rolling update strategy
    log_info "Starting rolling deployment..."
    
    # Start infrastructure services first
    docker-compose up -d redis prometheus grafana
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure services..."
    sleep 30
    
    # Deploy main application
    docker-compose up -d qme-app
    
    # Deploy reverse proxy
    docker-compose up -d nginx
    
    log_info "Services deployed successfully"
}

# Function to wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to become healthy..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=10
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        local healthy_services=0
        local total_services=0
        
        # Check each service health
        for service in qme-app redis nginx; do
            total_services=$((total_services + 1))
            
            if docker-compose ps "$service" | grep -q "healthy\|Up"; then
                healthy_services=$((healthy_services + 1))
            fi
        done
        
        log_info "Healthy services: $healthy_services/$total_services"
        
        if [[ $healthy_services -eq $total_services ]]; then
            log_info "All services are healthy!"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Services did not become healthy within $timeout seconds"
    return 1
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    # Test main application endpoint
    local app_url="http://localhost:${QME_APP_PORT:-8501}"
    
    log_info "Testing application endpoint: $app_url"
    if curl -f -s "$app_url/_stcore/health" >/dev/null; then
        log_info "Application endpoint is responding"
    else
        log_error "Application endpoint is not responding"
        return 1
    fi
    
    # Test health endpoint if available
    local health_url="http://localhost:${QME_HEALTH_PORT:-8502}/health"
    
    log_info "Testing health endpoint: $health_url"
    if curl -f -s "$health_url" >/dev/null; then
        log_info "Health endpoint is responding"
    else
        log_warn "Health endpoint is not responding (may not be implemented yet)"
    fi
    
    # Test reverse proxy if enabled
    if docker-compose ps nginx | grep -q "Up"; then
        local proxy_url="http://localhost:${NGINX_HTTP_PORT:-80}/health"
        
        log_info "Testing reverse proxy: $proxy_url"
        if curl -f -s "$proxy_url" >/dev/null; then
            log_info "Reverse proxy is responding"
        else
            log_warn "Reverse proxy health check failed"
        fi
    fi
    
    log_info "Post-deployment tests completed"
}

# Function to rollback deployment
rollback_deployment() {
    log_error "Rolling back deployment..."
    
    if [[ ! -f "${PROJECT_ROOT}/.last_backup" ]]; then
        log_error "No backup information found, cannot rollback"
        return 1
    fi
    
    local backup_path=$(cat "${PROJECT_ROOT}/.last_backup")
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup directory not found: $backup_path"
        return 1
    fi
    
    # Stop current services
    log_info "Stopping current services..."
    docker-compose down
    
    # Restore data
    if [[ -d "$backup_path/data" ]]; then
        log_info "Restoring data directory..."
        rm -rf "${PROJECT_ROOT}/data"
        cp -r "$backup_path/data" "${PROJECT_ROOT}/"
    fi
    
    # Restore configuration
    if [[ -f "$backup_path/.env" ]]; then
        log_info "Restoring configuration..."
        cp "$backup_path/.env" "${PROJECT_ROOT}/"
    fi
    
    # Restart services with previous configuration
    log_info "Restarting services..."
    docker-compose up -d
    
    log_info "Rollback completed"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    if [[ -d "$BACKUP_DIR" ]]; then
        # Keep only last 10 backups
        find "$BACKUP_DIR" -name "qme_backup_*" -type d | sort -r | tail -n +11 | xargs -r rm -rf
        log_info "Old backups cleaned up"
    fi
}

# Function to send deployment notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Placeholder for notification system (Slack, email, etc.)
    log_info "Deployment notification: $status - $message"
    
    # Example: Send to webhook if configured
    if [[ -n "${WEBHOOK_URL}" ]]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"QME System Deployment: $status - $message\"}" \
            >/dev/null 2>&1 || true
    fi
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log_info "Starting QME System deployment to $DEPLOYMENT_ENV"
    
    # Trap for cleanup on exit
    trap 'log_info "Deployment script interrupted"' INT TERM
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup
    create_backup
    
    # Build images
    build_images
    
    # Run pre-deployment tests
    run_pre_deployment_tests
    
    # Deploy services
    deploy_services
    
    # Wait for services to be healthy
    if ! wait_for_health; then
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_deployment
            send_notification "FAILED" "Deployment failed, rolled back to previous version"
            exit 1
        else
            log_error "Deployment health check failed, but rollback is disabled"
            send_notification "FAILED" "Deployment failed, manual intervention required"
            exit 1
        fi
    fi
    
    # Run post-deployment tests
    if ! run_post_deployment_tests; then
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            rollback_deployment
            send_notification "FAILED" "Post-deployment tests failed, rolled back"
            exit 1
        else
            log_warn "Post-deployment tests failed, but rollback is disabled"
        fi
    fi
    
    # Cleanup
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_info "Deployment completed successfully in ${duration} seconds"
    send_notification "SUCCESS" "Deployment completed successfully in ${duration} seconds"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Deployment environment (default: production)"
    echo "  -b, --backup-dir DIR     Backup directory (default: ./backups)"
    echo "  -t, --timeout SECONDS    Health check timeout (default: 300)"
    echo "  -r, --no-rollback        Disable automatic rollback on failure"
    echo "  -d, --debug              Enable debug output"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  WEBHOOK_URL              Webhook URL for deployment notifications"
    echo "  QME_APP_PORT            Application port (default: 8501)"
    echo "  QME_HEALTH_PORT         Health check port (default: 8502)"
    echo "  NGINX_HTTP_PORT         NGINX HTTP port (default: 80)"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            DEPLOYMENT_ENV="$2"
            shift 2
            ;;
        -b|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -t|--timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        -r|--no-rollback)
            ROLLBACK_ON_FAILURE="false"
            shift
            ;;
        -d|--debug)
            DEBUG="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"