#!/bin/bash

# Deployment script for Document Q&A System
# This script sets up the SQLite database, initializes canonical documents,
# and starts the Streamlit interface

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
DATABASE_PATH="$PROJECT_ROOT/data/database/documents.db"
LOG_DIR="$PROJECT_ROOT/logs"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python version: $PYTHON_VERSION"
}

# Function to create virtual environment
setup_virtual_environment() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "$VENV_PATH" ]; then
        print_status "Creating virtual environment at $VENV_PATH"
        $PYTHON_CMD -m venv "$VENV_PATH"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment ready"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "$PROJECT_ROOT/data"
        "$PROJECT_ROOT/data/database"
        "$PROJECT_ROOT/data/documents"
        "$LOG_DIR"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_success "Directories created"
}

# Function to validate environment configuration
validate_environment() {
    print_status "Validating environment configuration..."
    
    # Check for .env file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            print_warning ".env file not found. Copying from .env.example"
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_warning "Please edit .env file with your API keys before continuing"
        else
            print_warning ".env file not found and no .env.example available"
        fi
    fi
    
    # Check for canonical documents
    canonical_docs=(
        "AMAGuides 5th Edition.pdf"
        "QME-Study-Guide.pdf"
        "Sample3.pdf"
    )
    
    missing_docs=()
    for doc in "${canonical_docs[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$doc" ]; then
            missing_docs+=("$doc")
        fi
    done
    
    if [ ${#missing_docs[@]} -gt 0 ]; then
        print_warning "Missing canonical documents:"
        for doc in "${missing_docs[@]}"; do
            print_warning "  - $doc"
        done
        print_warning "System will start without these documents"
    else
        print_success "All canonical documents found"
    fi
}

# Function to initialize database
initialize_database() {
    print_status "Initializing SQLite database..."
    
    # Run database initialization script
    $PYTHON_CMD -c "
import sys
sys.path.append('$PROJECT_ROOT')
from src.storage.database import DatabaseManager
from src.config.app_config import AppConfig

config = AppConfig.from_env()
db_manager = DatabaseManager(config.database_path)
print('Database initialized successfully')
"
    
    print_success "Database initialized at $DATABASE_PATH"
}

# Function to run health checks
run_health_checks() {
    print_status "Running system health checks..."
    
    $PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('$PROJECT_ROOT')
from src.services.health_checker import HealthChecker
from src.config.app_config import AppConfig

async def main():
    config = AppConfig.from_env()
    health_checker = HealthChecker(config)
    
    health = health_checker.get_overall_health()
    
    print(f'Overall Health: {\"HEALTHY\" if health[\"overall_healthy\"] else \"UNHEALTHY\"}')
    print(f'Healthy Components: {health[\"healthy_components\"]}/{health[\"total_components\"]}')
    
    for component, status in health['checks'].items():
        status_text = 'PASS' if status['healthy'] else 'FAIL'
        print(f'  {component}: {status_text} - {status[\"message\"]}')
    
    return health['overall_healthy']

result = asyncio.run(main())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Health checks passed"
    else
        print_warning "Some health checks failed, but continuing with deployment"
    fi
}

# Function to initialize knowledge base
initialize_knowledge_base() {
    print_status "Initializing knowledge base with canonical documents..."
    
    $PYTHON_CMD -c "
import sys
sys.path.append('$PROJECT_ROOT')
from src.services.document_processor import process_document_simple
import os

# List of canonical documents to process
canonical_docs = [
    'AMAGuides 5th Edition.pdf',
    'QME-Study-Guide.pdf', 
    'Sample3.pdf'
]

processed = 0
failed = 0

print('Processing canonical documents...')
for doc in canonical_docs:
    if os.path.exists(doc):
        print(f'Processing: {doc}')
        try:
            result = process_document_simple(doc)
            if result:
                processed += 1
                print(f'  ✅ Successfully processed: {doc}')
            else:
                failed += 1
                print(f'  ❌ Failed to process: {doc}')
        except Exception as e:
            failed += 1
            print(f'  ❌ Error processing {doc}: {e}')
    else:
        print(f'  ⚠️  Document not found: {doc}')

print(f'\\nInitialization Summary:')
print(f'  Processed: {processed} documents')
print(f'  Failed: {failed} documents')
print(f'  Result: {\"SUCCESS\" if failed == 0 else \"PARTIAL SUCCESS\"}')
print('Knowledge base initialization completed')
"
    
    print_success "Knowledge base initialization completed"
}

# Function to start Streamlit application
start_streamlit() {
    print_status "Starting Streamlit application..."
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Start Streamlit
    print_success "Starting Streamlit on http://localhost:8501"
    print_status "Press Ctrl+C to stop the application"
    
    streamlit run src/ui/main_app.py --server.port=8501 --server.address=localhost
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup-only    Only setup environment and database, don't start app"
    echo "  --skip-kb-init  Skip knowledge base initialization"
    echo "  --help          Show this help message"
    echo ""
    echo "This script will:"
    echo "  1. Check Python version and setup virtual environment"
    echo "  2. Install dependencies"
    echo "  3. Create necessary directories"
    echo "  4. Validate environment configuration"
    echo "  5. Initialize SQLite database"
    echo "  6. Run health checks"
    echo "  7. Initialize knowledge base with canonical documents"
    echo "  8. Start Streamlit application"
}

# Main deployment function
main() {
    print_status "Starting Document Q&A System deployment..."
    
    # Parse command line arguments
    SETUP_ONLY=false
    SKIP_KB_INIT=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --skip-kb-init)
                SKIP_KB_INIT=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run deployment steps
    check_python_version
    setup_virtual_environment
    install_dependencies
    create_directories
    validate_environment
    initialize_database
    run_health_checks
    
    if [ "$SKIP_KB_INIT" = false ]; then
        initialize_knowledge_base
    else
        print_warning "Skipping knowledge base initialization"
    fi
    
    if [ "$SETUP_ONLY" = false ]; then
        start_streamlit
    else
        print_success "Setup completed. Run 'streamlit run src/ui/main_app.py' to start the application."
    fi
}

# Run main function
main "$@"