#!/bin/bash

# Complete QME System Startup Script
# This script provides comprehensive system initialization, cleanup, and startup
# with proper error handling and recovery mechanisms.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_NAME="venv_clean"
LOG_FILE="$PROJECT_ROOT/logs/system_startup.log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
    log "$message"
}

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Error handling function
handle_error() {
    local exit_code=$?
    local line_number=$1
    print_error "Script failed at line $line_number with exit code $exit_code"
    print_info "Check the log file for details: $LOG_FILE"
    exit $exit_code
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    print_info "Checking Python version..."
    
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major=$(echo $python_version | cut -d. -f1)
    local minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        print_error "Python $python_version detected. Python 3.8 or higher is required."
        exit 1
    fi
    
    print_success "Python $python_version detected"
}

# Function to run clean environment setup
run_clean_environment_setup() {
    print_header "STEP 1: CLEAN ENVIRONMENT SETUP"
    
    local clean_script="$SCRIPT_DIR/clean_environment_setup.sh"
    
    if [ ! -f "$clean_script" ]; then
        print_error "Clean environment setup script not found: $clean_script"
        exit 1
    fi
    
    print_info "Running clean environment setup..."
    chmod +x "$clean_script"
    
    # Run the clean environment setup script
    cd "$PROJECT_ROOT"
    "$clean_script"
    
    print_success "Clean environment setup completed"
}

# Function to activate virtual environment
activate_virtual_environment() {
    print_header "STEP 2: VIRTUAL ENVIRONMENT ACTIVATION"
    
    local venv_path="$PROJECT_ROOT/$VENV_NAME"
    
    if [ ! -d "$venv_path" ]; then
        print_error "Virtual environment not found: $venv_path"
        print_info "Please run the clean environment setup first"
        exit 1
    fi
    
    print_info "Activating virtual environment: $VENV_NAME"
    source "$venv_path/bin/activate"
    
    # Verify activation
    if [ "$VIRTUAL_ENV" != "$venv_path" ]; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment activated: $VIRTUAL_ENV"
    print_info "Python executable: $(which python)"
    print_info "Pip version: $(pip --version)"
}

# Function to install additional dependencies
install_additional_dependencies() {
    print_header "STEP 3: ADDITIONAL DEPENDENCIES"
    
    print_info "Installing additional required packages..."
    
    # Core API dependencies
    pip install --quiet fastapi uvicorn python-multipart requests
    
    # Document processing
    pip install --quiet python-docx PyPDF2 pdfplumber
    
    # AI/ML packages
    pip install --quiet openai google-generativeai
    
    # Utilities
    pip install --quiet python-dotenv aiofiles asyncio
    
    # Data processing
    pip install --quiet pandas numpy
    
    print_success "Additional dependencies installed"
}

# Function to set up environment variables
setup_environment_variables() {
    print_header "STEP 4: ENVIRONMENT CONFIGURATION"
    
    # Check for .env file
    local env_file="$PROJECT_ROOT/.env"
    local env_example="$PROJECT_ROOT/.env.example"
    
    if [ ! -f "$env_file" ] && [ -f "$env_example" ]; then
        print_info "Creating .env file from .env.example"
        cp "$env_example" "$env_file"
        print_warning "Please edit .env file with your actual API keys"
    fi
    
    # Load environment variables if .env exists
    if [ -f "$env_file" ]; then
        print_info "Loading environment variables from .env"
        set -a  # automatically export all variables
        source "$env_file"
        set +a
    fi
    
    # Check for required API keys
    local keys_configured=0
    
    if [ -n "$OPENROUTER_API_KEY" ] && [ "$OPENROUTER_API_KEY" != "your_openrouter_api_key_here" ]; then
        print_success "OpenRouter API key configured"
        keys_configured=$((keys_configured + 1))
    else
        print_warning "OpenRouter API key not configured"
    fi
    
    if [ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "your_gemini_api_key_here" ]; then
        print_success "Gemini API key configured"
        keys_configured=$((keys_configured + 1))
    else
        print_warning "Gemini API key not configured"
    fi
    
    if [ $keys_configured -eq 0 ]; then
        print_warning "No API keys configured. Some features may not work."
        print_info "Edit $env_file to add your API keys"
    else
        print_success "$keys_configured API key(s) configured"
    fi
}

# Function to create required directories
create_required_directories() {
    print_header "STEP 5: DIRECTORY STRUCTURE"
    
    local directories=(
        "data/database"
        "data/documents"
        "data/cache"
        "data/canonical/documents"
        "data/sample_documents"
        "results/generated_documents"
        "results/templates_archive"
        "results/quality_reports"
        "results/validation_reports"
        "logs"
        "config/settings"
        "config/templates"
        "config/prompts/extraction"
        "config/prompts/generation"
        "config/prompts/validation"
    )
    
    print_info "Creating required directories..."
    
    for dir in "${directories[@]}"; do
        local full_path="$PROJECT_ROOT/$dir"
        if [ ! -d "$full_path" ]; then
            mkdir -p "$full_path"
            print_info "Created directory: $dir"
        fi
    done
    
    print_success "Directory structure verified"
}

# Function to validate system imports
validate_system_imports() {
    print_header "STEP 6: SYSTEM IMPORT VALIDATION"
    
    print_info "Validating core system imports..."
    
    # Test core imports
    python3 -c "
import sys
import os

# Set environment variables for testing
os.environ.setdefault('OPENROUTER_API_KEY', 'test-key-for-validation')
os.environ.setdefault('GEMINI_API_KEY', 'test-key-for-validation')

try:
    # Test FastAPI imports
    import fastapi
    import uvicorn
    print('✅ FastAPI components imported successfully')
    
    # Test core QME services
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    print('✅ ComprehensiveQMEFieldService imported successfully')
    
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    print('✅ OpenRouterExtractionService imported successfully')
    
    from src.core.extraction.gemini_extraction_service import GeminiExtractionService
    print('✅ GeminiExtractionService imported successfully')
    
    from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
    print('✅ ProfessionalTemplateAssembler imported successfully')
    
    # Test API module
    from src.api.extraction_testing_api import app
    print('✅ API application imported successfully')
    
    print('✅ All core imports successful')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "System import validation passed"
    else
        print_error "System import validation failed"
        exit 1
    fi
}

# Function to initialize knowledge graph (if needed)
initialize_knowledge_graph() {
    print_header "STEP 7: KNOWLEDGE GRAPH INITIALIZATION"
    
    print_info "Checking knowledge graph status..."
    
    # Check if knowledge graph needs initialization
    local db_path="$PROJECT_ROOT/data/database/documents.db"
    
    if [ ! -f "$db_path" ]; then
        print_info "Database not found. Knowledge graph initialization may be needed."
        print_warning "Knowledge graph initialization skipped - will be handled by application"
    else
        print_success "Database file exists: $db_path"
    fi
    
    # Note: Actual knowledge graph initialization will be handled by the application
    # to avoid the complex initialization issues mentioned in the error logs
    print_info "Knowledge graph will be initialized on first application startup"
}

# Function to run system health check
run_system_health_check() {
    print_header "STEP 8: SYSTEM HEALTH CHECK"
    
    print_info "Running basic system health check..."
    
    # Test basic system functionality
    python3 -c "
import os
import sys

# Set test environment variables
os.environ.setdefault('OPENROUTER_API_KEY', 'test-key')
os.environ.setdefault('GEMINI_API_KEY', 'test-key')

try:
    # Test service initialization
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    service = ComprehensiveQMEFieldService()
    
    print('✅ Core services can be initialized')
    print(f'✅ OpenRouter service available: {service.openrouter_service is not None}')
    print(f'✅ Gemini service available: {service.gemini_service is not None}')
    
    # Test API application
    from src.api.extraction_testing_api import app
    print('✅ API application ready')
    
    print('✅ System health check passed')
    
except Exception as e:
    print(f'❌ System health check failed: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "System health check passed"
    else
        print_error "System health check failed"
        exit 1
    fi
}

# Function to show startup menu
show_startup_menu() {
    print_header "QME SYSTEM STARTUP MENU"
    
    echo -e "${CYAN}Choose how to start the QME system:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} 🚀 Start API Server Only (Recommended)"
    echo -e "${GREEN}2)${NC} 🌐 Start Streamlit Web Interface"
    echo -e "${GREEN}3)${NC} 🔄 Start Both API Server and Web Interface"
    echo -e "${GREEN}4)${NC} 🧪 Run System Tests"
    echo -e "${GREEN}5)${NC} 📊 Run Interactive Demo"
    echo -e "${GREEN}6)${NC} 🔍 System Status Check"
    echo -e "${GREEN}7)${NC} 🛠️  Troubleshooting Mode"
    echo -e "${GREEN}8)${NC} ❌ Exit"
    echo ""
    echo -e "${YELLOW}Note: Option 1 (API Server) is recommended as it bypasses initialization issues${NC}"
    echo ""
}

# Function to start API server
start_api_server() {
    print_header "STARTING API SERVER"
    
    local api_script="$PROJECT_ROOT/scripts/start_extraction_api.py"
    
    if [ ! -f "$api_script" ]; then
        print_error "API startup script not found: $api_script"
        exit 1
    fi
    
    print_info "Starting QME Document Extraction API Server..."
    print_info "API will be available at: http://localhost:8000"
    print_info "API Documentation: http://localhost:8000/docs"
    print_info "Health Check: http://localhost:8000/health"
    print_info ""
    print_info "Press Ctrl+C to stop the server"
    
    cd "$PROJECT_ROOT"
    python "$api_script"
}

# Function to start Streamlit web interface
start_streamlit_interface() {
    print_header "STARTING STREAMLIT WEB INTERFACE"
    
    local main_app="$PROJECT_ROOT/src/ui/main_app.py"
    
    if [ ! -f "$main_app" ]; then
        print_error "Main app not found: $main_app"
        exit 1
    fi
    
    print_info "Starting Streamlit Web Interface..."
    print_info "Web Interface will be available at: http://localhost:8501"
    print_info ""
    print_warning "Note: This may encounter initialization issues. API Server is recommended."
    print_info "Press Ctrl+C to stop the interface"
    
    cd "$PROJECT_ROOT"
    streamlit run "$main_app" --server.port 8501
}

# Function to start both services
start_both_services() {
    print_header "STARTING BOTH SERVICES"
    
    print_info "Starting API Server in background..."
    
    # Start API server in background
    cd "$PROJECT_ROOT"
    python scripts/start_extraction_api.py &
    local api_pid=$!
    
    # Wait a moment for API to start
    sleep 5
    
    # Check if API is running
    if kill -0 $api_pid 2>/dev/null; then
        print_success "API Server started (PID: $api_pid)"
        print_info "API available at: http://localhost:8000"
    else
        print_error "Failed to start API Server"
        exit 1
    fi
    
    print_info "Starting Streamlit Web Interface..."
    print_info "Web Interface will be available at: http://localhost:8501"
    print_info ""
    print_info "Press Ctrl+C to stop both services"
    
    # Start Streamlit in foreground
    streamlit run src/ui/main_app.py --server.port 8501
    
    # Clean up API server when Streamlit exits
    print_info "Stopping API Server..."
    kill $api_pid 2>/dev/null || true
}

# Function to run system tests
run_system_tests() {
    print_header "RUNNING SYSTEM TESTS"
    
    local test_script="$PROJECT_ROOT/scripts/test_extraction_api.py"
    
    if [ ! -f "$test_script" ]; then
        print_error "Test script not found: $test_script"
        exit 1
    fi
    
    print_info "Running comprehensive system tests..."
    
    cd "$PROJECT_ROOT"
    python "$test_script"
}

# Function to run interactive demo
run_interactive_demo() {
    print_header "RUNNING INTERACTIVE DEMO"
    
    local demo_script="$PROJECT_ROOT/examples/api_usage_demo.py"
    
    if [ ! -f "$demo_script" ]; then
        print_error "Demo script not found: $demo_script"
        exit 1
    fi
    
    print_info "Running interactive API demo..."
    
    cd "$PROJECT_ROOT"
    python "$demo_script"
}

# Function to show system status
show_system_status() {
    print_header "SYSTEM STATUS CHECK"
    
    print_info "Checking system status..."
    
    # Check virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Virtual environment active: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment active"
    fi
    
    # Check Python version
    local python_version=$(python --version 2>&1)
    print_info "Python version: $python_version"
    
    # Check key packages
    print_info "Checking key packages..."
    python -c "
import pkg_resources
packages = ['fastapi', 'uvicorn', 'streamlit', 'requests', 'openai']
for package in packages:
    try:
        version = pkg_resources.get_distribution(package).version
        print(f'✅ {package}: {version}')
    except pkg_resources.DistributionNotFound:
        print(f'❌ {package}: Not installed')
"
    
    # Check API keys
    print_info "Checking API configuration..."
    if [ -n "$OPENROUTER_API_KEY" ] && [ "$OPENROUTER_API_KEY" != "your_openrouter_api_key_here" ]; then
        print_success "OpenRouter API key configured"
    else
        print_warning "OpenRouter API key not configured"
    fi
    
    if [ -n "$GEMINI_API_KEY" ] && [ "$GEMINI_API_KEY" != "your_gemini_api_key_here" ]; then
        print_success "Gemini API key configured"
    else
        print_warning "Gemini API key not configured"
    fi
    
    # Check directories
    print_info "Checking directory structure..."
    local key_dirs=("data" "results" "logs" "config" "src")
    for dir in "${key_dirs[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            print_success "Directory exists: $dir"
        else
            print_warning "Directory missing: $dir"
        fi
    done
    
    print_success "System status check completed"
}

# Function to run troubleshooting mode
run_troubleshooting_mode() {
    print_header "TROUBLESHOOTING MODE"
    
    echo -e "${CYAN}Troubleshooting Options:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} 🔄 Re-run clean environment setup"
    echo -e "${GREEN}2)${NC} 🧪 Test system imports"
    echo -e "${GREEN}3)${NC} 🔍 Check API server connectivity"
    echo -e "${GREEN}4)${NC} 📋 Show detailed system information"
    echo -e "${GREEN}5)${NC} 🗑️  Clean all cache and temporary files"
    echo -e "${GREEN}6)${NC} ⬅️  Return to main menu"
    echo ""
    
    read -p "Choose troubleshooting option (1-6): " choice
    
    case $choice in
        1)
            print_info "Re-running clean environment setup..."
            run_clean_environment_setup
            activate_virtual_environment
            install_additional_dependencies
            print_success "Clean environment setup completed"
            ;;
        2)
            print_info "Testing system imports..."
            validate_system_imports
            ;;
        3)
            print_info "Testing API server connectivity..."
            # Start API server in background for testing
            cd "$PROJECT_ROOT"
            python scripts/start_extraction_api.py &
            local api_pid=$!
            sleep 5
            
            # Test connectivity
            if curl -s http://localhost:8000/health > /dev/null; then
                print_success "API server is accessible"
            else
                print_error "API server is not accessible"
            fi
            
            # Stop test server
            kill $api_pid 2>/dev/null || true
            ;;
        4)
            show_system_status
            ;;
        5)
            print_info "Cleaning cache and temporary files..."
            find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
            find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
            rm -rf "$PROJECT_ROOT/.pytest_cache" 2>/dev/null || true
            print_success "Cache and temporary files cleaned"
            ;;
        6)
            return
            ;;
        *)
            print_error "Invalid option. Please choose 1-6."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Main function
main() {
    # Change to project root
    cd "$PROJECT_ROOT"
    
    print_header "QME SYSTEM COMPLETE STARTUP"
    print_info "Project root: $PROJECT_ROOT"
    print_info "Log file: $LOG_FILE"
    print_info "Starting comprehensive system initialization..."
    
    # Check Python version first
    check_python_version
    
    # Run initialization steps
    run_clean_environment_setup
    activate_virtual_environment
    install_additional_dependencies
    setup_environment_variables
    create_required_directories
    validate_system_imports
    initialize_knowledge_graph
    run_system_health_check
    
    print_success "System initialization completed successfully!"
    print_info ""
    
    # Show menu and handle user choice
    while true; do
        show_startup_menu
        read -p "Choose an option (1-8): " choice
        
        case $choice in
            1)
                start_api_server
                break
                ;;
            2)
                start_streamlit_interface
                break
                ;;
            3)
                start_both_services
                break
                ;;
            4)
                run_system_tests
                echo ""
                read -p "Press Enter to return to menu..."
                ;;
            5)
                run_interactive_demo
                echo ""
                read -p "Press Enter to return to menu..."
                ;;
            6)
                show_system_status
                echo ""
                read -p "Press Enter to return to menu..."
                ;;
            7)
                run_troubleshooting_mode
                ;;
            8)
                print_info "Exiting QME System Startup"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-8."
                ;;
        esac
    done
}

# Handle script interruption
cleanup() {
    print_info "Script interrupted. Cleaning up..."
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup INT TERM

# Run main function
main "$@"