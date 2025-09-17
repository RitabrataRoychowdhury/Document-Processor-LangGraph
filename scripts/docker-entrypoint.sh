#!/bin/bash
set -e

# Production-ready Docker entrypoint script for QME System
# Handles initialization, health checks, and graceful startup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    if [[ "${QME_LOG_LEVEL}" == "DEBUG" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Function to wait for dependencies
wait_for_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if database directory is writable
    if [[ ! -w "data/database" ]]; then
        log_error "Database directory is not writable"
        exit 1
    fi
    
    # Check if logs directory is writable
    if [[ ! -w "logs" ]]; then
        log_error "Logs directory is not writable"
        exit 1
    fi
    
    # Validate environment variables
    if [[ -z "${QME_ENVIRONMENT}" ]]; then
        log_warn "QME_ENVIRONMENT not set, defaulting to production"
        export QME_ENVIRONMENT=production
    fi
    
    log_info "Dependencies check completed"
}

# Function to initialize the system
initialize_system() {
    log_info "Initializing QME System..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "Created .env file from template"
        else
            log_warn "No .env.example found, creating minimal .env"
            cat > .env << EOF
QME_ENVIRONMENT=${QME_ENVIRONMENT}
QME_LOG_LEVEL=${QME_LOG_LEVEL:-INFO}
QME_ENABLE_MONITORING=${QME_ENABLE_MONITORING:-true}
QME_ENABLE_HEALTH_CHECKS=${QME_ENABLE_HEALTH_CHECKS:-true}
EOF
        fi
    fi
    
    # Initialize database if needed
    if [[ ! -f "data/database/documents.db" ]]; then
        log_info "Initializing database..."
        python -c "
from src.storage.database import DatabaseManager
from src.config.app_config import AppConfig
config = AppConfig()
db_manager = DatabaseManager(config.database_path)
db_manager.initialize_database()
print('Database initialized successfully')
" || {
            log_error "Failed to initialize database"
            exit 1
        }
    fi
    
    # Initialize knowledge base if needed
    if [[ "${QME_ENABLE_KNOWLEDGE_BASE_INIT:-true}" == "true" ]]; then
        log_info "Checking knowledge base initialization..."
        python -c "
from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer
from src.config.app_config import AppConfig
config = AppConfig()
initializer = KnowledgeBaseInitializer(config)
if initializer.needs_initialization():
    print('Initializing knowledge base...')
    initializer.initialize_knowledge_base()
    print('Knowledge base initialized successfully')
else:
    print('Knowledge base already initialized')
" || {
            log_warn "Knowledge base initialization failed, continuing without it"
        }
    fi
    
    log_info "System initialization completed"
}

# Function to run health checks
run_health_checks() {
    log_info "Running startup health checks..."
    
    python -c "
import sys
from src.infrastructure.monitoring.health_checker import get_health_checker
from src.config.app_config import AppConfig

try:
    config = AppConfig()
    health_checker = get_health_checker(config)
    
    # Wait for system to be healthy
    if health_checker.wait_for_healthy_state(timeout_seconds=60):
        print('System health checks passed')
        sys.exit(0)
    else:
        print('System health checks failed')
        sys.exit(1)
        
except Exception as e:
    print(f'Health check error: {e}')
    sys.exit(1)
" || {
        log_error "Health checks failed"
        exit 1
    }
    
    log_info "Health checks completed successfully"
}

# Function to start monitoring services
start_monitoring() {
    if [[ "${QME_ENABLE_MONITORING}" == "true" ]]; then
        log_info "Starting monitoring services..."
        
        # Start performance monitoring in background
        python -c "
from src.infrastructure.monitoring.performance_monitor import initialize_performance_monitor
from src.infrastructure.monitoring.comprehensive_logging_service import initialize_logging_service

# Initialize monitoring services
perf_config = {
    'max_processing_time': 30.0,
    'monitoring_interval_seconds': 60,
    'enable_alerts': True
}
initialize_performance_monitor(perf_config)

log_config = {
    'log_level': '${QME_LOG_LEVEL:-INFO}',
    'enable_audit_logging': True,
    'retention_days': 30
}
initialize_logging_service(log_config)

print('Monitoring services initialized')
" &
        
        log_info "Monitoring services started"
    fi
}

# Function to handle graceful shutdown
graceful_shutdown() {
    log_info "Received shutdown signal, shutting down gracefully..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    # Run cleanup
    python -c "
from src.infrastructure.monitoring.performance_monitor import get_performance_monitor
from src.infrastructure.monitoring.comprehensive_logging_service import get_logging_service

try:
    # Shutdown monitoring services
    perf_monitor = get_performance_monitor()
    perf_monitor.shutdown()
    
    logging_service = get_logging_service()
    logging_service.shutdown()
    
    print('Cleanup completed')
except Exception as e:
    print(f'Cleanup error: {e}')
" || log_warn "Cleanup failed"
    
    log_info "Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap graceful_shutdown SIGTERM SIGINT

# Main execution
main() {
    local mode="${1:-production}"
    
    log_info "Starting QME System in ${mode} mode"
    log_info "Environment: ${QME_ENVIRONMENT}"
    log_info "Log Level: ${QME_LOG_LEVEL}"
    
    # Pre-startup checks
    wait_for_dependencies
    initialize_system
    
    if [[ "${QME_ENABLE_HEALTH_CHECKS}" == "true" ]]; then
        run_health_checks
    fi
    
    start_monitoring
    
    # Start the application based on mode
    case "${mode}" in
        "production")
            log_info "Starting production server..."
            exec streamlit run src/ui/main_app.py \
                --server.port=8501 \
                --server.address=0.0.0.0 \
                --server.headless=true \
                --browser.gatherUsageStats=false \
                --server.enableCORS=false \
                --server.enableXsrfProtection=true
            ;;
        "development")
            log_info "Starting development server..."
            exec streamlit run src/ui/main_app.py \
                --server.port=8501 \
                --server.address=0.0.0.0 \
                --server.runOnSave=true
            ;;
        "worker")
            log_info "Starting background worker..."
            exec python -m src.worker.background_processor
            ;;
        "migrate")
            log_info "Running database migrations..."
            python -c "
from src.infrastructure.storage.database_manager import DatabaseManager
from src.config.app_config import AppConfig
config = AppConfig()
db_manager = DatabaseManager(config.database_path)
db_manager.run_migrations()
print('Migrations completed')
"
            ;;
        "health-check")
            log_info "Running health check..."
            run_health_checks
            log_info "Health check completed"
            ;;
        "shell")
            log_info "Starting interactive shell..."
            exec /bin/bash
            ;;
        *)
            log_error "Unknown mode: ${mode}"
            log_info "Available modes: production, development, worker, migrate, health-check, shell"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"