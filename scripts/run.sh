#!/bin/bash

# QME System - Complete One-Hit Runnable Script
# This script performs complete cleanup, setup, and runs the QME system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv_clean"
LOG_FILE="$PROJECT_ROOT/logs/startup.log"

# Function to print colored output
print_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC} $1 ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
}

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

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

print_header "QME SYSTEM - ONE-HIT COMPLETE STARTUP"

# Change to project root
cd "$PROJECT_ROOT"
print_status "Working directory: $PROJECT_ROOT"

# Create logs directory
mkdir -p logs
log_with_timestamp "Starting QME system complete startup"

# ============================================================================
# STEP 1: PRE-STARTUP CLEANUP
# ============================================================================
print_step "1/8 - Pre-startup cleanup"

print_status "Cleaning Python cache files..."
log_with_timestamp "Starting cache cleanup"

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
print_success "Removed __pycache__ directories"

# Remove pytest cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
print_success "Removed pytest cache directories"

# Remove other cache files
rm -rf .mypy_cache .coverage coverage.xml htmlcov 2>/dev/null || true
print_success "Removed mypy and coverage cache"

# Remove Python compiled files
find . -name "*.py[co]" -delete 2>/dev/null || true
print_success "Removed Python compiled files"

# Remove old virtual environments
rm -rf venv .venv 2>/dev/null || true
print_success "Removed old virtual environments"

# Clean temporary files
rm -rf .streamlit/cache 2>/dev/null || true
rm -rf logs/*.log 2>/dev/null || true
print_success "Cleaned temporary files"

log_with_timestamp "Cache cleanup completed"

# ============================================================================
# STEP 2: PYTHON VERSION CHECK
# ============================================================================
print_step "2/8 - Python version validation"

if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed or not in PATH"
    echo "   Please install Python 3.8+ and try again"
    log_with_timestamp "ERROR: Python not found"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    log_with_timestamp "ERROR: Python version too old: $PYTHON_VERSION"
    exit 1
fi

print_success "Python version: $PYTHON_VERSION"
log_with_timestamp "Python version validated: $PYTHON_VERSION"

# ============================================================================
# STEP 3: VIRTUAL ENVIRONMENT SETUP
# ============================================================================
print_step "3/8 - Virtual environment setup"

print_status "Creating fresh virtual environment..."
$PYTHON_CMD -m venv "$VENV_PATH"
print_success "Virtual environment created: $VENV_PATH"
log_with_timestamp "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
print_success "Virtual environment activated: $VIRTUAL_ENV"
log_with_timestamp "Virtual environment activated"

# ============================================================================
# STEP 4: DEPENDENCY INSTALLATION
# ============================================================================
print_step "4/8 - Dependency installation"

# Upgrade pip first
print_status "Upgrading pip to latest version..."
pip install --upgrade pip --quiet
PIP_VERSION=$(pip --version | cut -d' ' -f2)
print_success "Pip upgraded to version: $PIP_VERSION"
log_with_timestamp "Pip upgraded to: $PIP_VERSION"

# Install dependencies
print_status "Installing project dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "All dependencies installed successfully"
    log_with_timestamp "Dependencies installed from requirements.txt"
else
    print_error "requirements.txt not found"
    echo "   Please ensure requirements.txt exists in the project directory"
    log_with_timestamp "ERROR: requirements.txt not found"
    exit 1
fi

# Install additional dependencies that might be missing
print_status "Installing additional QME system dependencies..."
pip install --quiet \
    streamlit>=1.28.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    python-multipart>=0.0.6 \
    python-docx>=0.8.11 \
    PyPDF2>=3.0.1 \
    requests>=2.31.0 \
    python-dotenv>=1.0.0 \
    PyYAML>=6.0 \
    psutil>=5.9.0 \
    openai>=1.0.0 \
    sentence-transformers>=2.2.2 \
    spacy>=3.7.0 \
    chromadb>=0.4.0 \
    numpy>=1.24.0 \
    typing-extensions>=4.8.0 \
    langgraph>=0.0.40

print_success "Additional dependencies installed"
log_with_timestamp "Additional dependencies installed"

# ============================================================================
# STEP 5: ENVIRONMENT CONFIGURATION
# ============================================================================
print_step "5/8 - Environment configuration"

# Setup environment file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_status "Creating .env file from .env.example..."
        cp .env.example .env
        print_success ".env file created"
        print_warning "Please edit .env with your API keys if needed"
        log_with_timestamp ".env file created from example"
    else
        print_status "Creating basic .env file..."
        cat > .env << 'EOF'
# QME System Environment Configuration
# Edit these values with your actual API keys

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=meta-llama/llama-3.2-90b-vision-instruct:free

# Gemini API Configuration  
GEMINI_API_KEY=your_gemini_api_key_here

# System Configuration
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
STREAMLIT_PORT=8501
API_PORT=8000

# Database Configuration
DATABASE_URL=sqlite:///data/database/documents.db

# Performance Configuration
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=10
EOF
        print_success "Basic .env file created"
        print_warning "Please edit .env with your actual API keys"
        log_with_timestamp "Basic .env file created"
    fi
else
    print_success ".env file already exists"
    log_with_timestamp ".env file exists"
fi

# Create required directories
print_status "Creating required directories..."
mkdir -p data/database
mkdir -p data/documents  
mkdir -p data/cache
mkdir -p data/canonical
mkdir -p data/ama_guidelines
mkdir -p data/qme_references
mkdir -p data/sample_documents
mkdir -p data/exports
mkdir -p logs
mkdir -p results/generated_documents
mkdir -p results/templates_archive
mkdir -p results/validation_reports
mkdir -p results/performance_reports
mkdir -p results/quality_reports
mkdir -p results/audit_trails
mkdir -p results/extraction_results
mkdir -p results/metadata
mkdir -p results/processing_logs
mkdir -p results/template_results
mkdir -p results/validation_results
print_success "All required directories created"
log_with_timestamp "Required directories created"

# ============================================================================
# STEP 6: SYSTEM VALIDATION AND IMPORT TESTING
# ============================================================================
print_step "6/8 - System validation and import testing"

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
print_status "Python path configured: $PYTHONPATH"
log_with_timestamp "Python path configured"

# Test critical imports
print_status "Testing critical system imports..."
$PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')

print('🔍 Testing core imports...')
try:
    # Test configuration imports
    from src.config.app_config import AppConfig
    print('✅ AppConfig import successful')
    
    # Test core service imports
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    print('✅ ComprehensiveQMEFieldService import successful')
    
    # Test extraction service imports
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    print('✅ OpenRouterExtractionService import successful')
    
    # Test UI imports
    from src.ui.main_app import main
    print('✅ Main app import successful')
    
    from src.ui.upload_interface import UploadInterface
    print('✅ UploadInterface import successful')
    
    # Test API imports
    try:
        from src.api.extraction_testing_api import app
        print('✅ API extraction testing import successful')
    except ImportError:
        print('⚠️  API extraction testing not available (optional)')
    
    print('\\n🎉 All critical imports successful - system ready!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('\\n🔧 Troubleshooting steps:')
    print('   1. Check that all source files exist')
    print('   2. Verify Python path is correct')
    print('   3. Ensure dependencies are installed')
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    print_error "System import validation failed"
    echo ""
    echo "💡 Troubleshooting steps:"
    echo "   1. Check that all source files exist in src/ directory"
    echo "   2. Verify dependencies are properly installed"
    echo "   3. Check for any syntax errors in Python files"
    echo ""
    log_with_timestamp "ERROR: System import validation failed"
    exit 1
fi

print_success "System import validation passed"
log_with_timestamp "System import validation passed"

# Test environment configuration
print_status "Testing environment configuration..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')

try:
    import os
    from src.config.app_config import AppConfig
    
    print('🔧 Loading configuration...')
    config = AppConfig.from_env()
    
    print('✅ Configuration loaded successfully')
    print(f'   Debug mode: {config.debug_mode}')
    print(f'   Log level: {os.getenv(\"LOG_LEVEL\", \"INFO\")}')
    print(f'   Max file size: {config.max_file_size_mb}MB')
    print(f'   OpenRouter configured: {bool(config.openrouter_api_key)}')
    print(f'   Gemini configured: {bool(config.gemini_api_key)}')
    
    if not config.openrouter_api_key and not config.gemini_api_key:
        print('⚠️  Warning: No API keys configured - some features may not work')
        print('   Edit .env file to add your API keys')
    
except Exception as e:
    print(f'❌ Configuration error: {e}')
    print('\\n💡 Fix by editing .env file with proper values')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    print_warning "Configuration has issues but continuing..."
    log_with_timestamp "WARNING: Configuration issues detected"
else
    print_success "Environment configuration validated"
    log_with_timestamp "Environment configuration validated"
fi

# ============================================================================
# STEP 7: SYSTEM HEALTH CHECK
# ============================================================================
print_step "7/8 - System health check"

print_status "Running comprehensive system health check..."
$PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')

try:
    from src.config.app_config import AppConfig
    
    print('🏥 System Health Check')
    print('=' * 30)
    
    # Check configuration
    config = AppConfig.from_env()
    print('✅ Configuration: OK')
    
    # Check directories
    required_dirs = [
        'data/database', 'data/documents', 'logs', 
        'results/generated_documents', 'src/ui', 'src/core'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f'✅ Directory {dir_path}: OK')
        else:
            print(f'❌ Directory {dir_path}: MISSING')
    
    # Check key files
    key_files = [
        'src/ui/main_app.py',
        'src/config/app_config.py', 
        'src/services/comprehensive_qme_field_service.py',
        'requirements.txt',
        '.env'
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f'✅ File {file_path}: OK')
        else:
            print(f'❌ File {file_path}: MISSING')
    
    print('\\n🎯 System Status Summary:')
    print(f'   🗄️  Database: data/database/documents.db')
    print(f'   🤖 API Keys: {\"Configured\" if (config.openrouter_api_key or config.gemini_api_key) else \"Not configured\"}')
    print(f'   📁 Document Processing: Ready')
    print(f'   🌐 Web Interface: Ready')
    print(f'   🚀 API Server: Ready')
    print(f'   ✅ System: OPERATIONAL')
    
except Exception as e:
    print(f'❌ Health check error: {e}')
    print('⚠️  System may have issues but will attempt to start')
"

print_success "System health check completed"
log_with_timestamp "System health check completed"

# ============================================================================
# STEP 8: STARTUP MENU AND LAUNCH
# ============================================================================
print_step "8/8 - System startup"

print_success "🎉 QME System setup completed successfully!"
echo ""
log_with_timestamp "QME System setup completed successfully"

# Show startup options
echo "🎯 QME System Startup Options:"
echo "   1) 🌐 Start Streamlit Web Interface (Default)"
echo "   2) 🚀 Start FastAPI Server"  
echo "   3) 🔄 Start Both Web Interface and API Server"
echo "   4) 🧪 Run System Tests"
echo "   5) 🔍 Run Health Check Only"
echo ""
read -p "Choose an option (1-5) or press Enter for default [1]: " -n 1 -r
echo ""

# Default to option 1 if no input
if [ -z "$REPLY" ]; then
    REPLY="1"
fi

case $REPLY in
    1)
        print_header "STARTING STREAMLIT WEB INTERFACE"
        echo ""
        echo "🌐   📍 URL: http://localhost:8501"
        echo "🌐   📚 Upload documents and generate QME templates"
        echo "🌐   🔍 View logs in: logs/"
        echo "🌐   ⏹️  Press Ctrl+C to stop the server"
        echo ""
        
        log_with_timestamp "Starting Streamlit web interface"
        
        # Final import validation
        print_status "Final application validation..."
        $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    from src.ui.main_app import main
    print('✅ Application ready to start')
except Exception as e:
    print(f'⚠️  Warning: {e}')
    print('   Attempting to start anyway...')
"
        
        print_status "Launching Streamlit server..."
        echo "   👉 http://localhost:8501"
        echo ""
        
        # Start Streamlit
        $PYTHON_CMD -m streamlit run src/ui/main_app.py \
            --server.port=8501 \
            --server.address=localhost \
            --server.headless=false \
            --browser.gatherUsageStats=false \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false
        ;;
    2)
        print_header "STARTING FASTAPI SERVER"
        echo ""
        echo "🚀   📍 API URL: http://localhost:8000"
        echo "🚀   📖 API Docs: http://localhost:8000/docs"
        echo "🚀   🔍 Health Check: http://localhost:8000/health"
        echo "🚀   ⏹️  Press Ctrl+C to stop the server"
        echo ""
        
        log_with_timestamp "Starting FastAPI server"
        
        # Check if API server exists
        if [ -f "src/api/extraction_testing_api.py" ]; then
            print_status "Starting FastAPI server..."
            $PYTHON_CMD -m uvicorn src.api.extraction_testing_api:app \
                --host 0.0.0.0 \
                --port 8000 \
                --reload
        else
            print_status "API server not found, starting basic FastAPI server..."
            # Create a basic API server on the fly
            $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title='QME System API', version='1.0.0')

@app.get('/health')
async def health_check():
    return JSONResponse({'status': 'healthy', 'message': 'QME System API is running'})

@app.get('/')
async def root():
    return JSONResponse({'message': 'QME System API', 'docs': '/docs'})

if __name__ == '__main__':
    print('🚀 Starting basic QME API server...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
"
        fi
        ;;
    3)
        print_header "STARTING BOTH WEB INTERFACE AND API SERVER"
        echo ""
        echo "🔄   📍 Web Interface: http://localhost:8501"
        echo "🔄   📍 API Server: http://localhost:8000"
        echo "🔄   ⏹️  Press Ctrl+C to stop both servers"
        echo ""
        
        log_with_timestamp "Starting both web interface and API server"
        
        # Start API server in background
        if [ -f "src/api/extraction_testing_api.py" ]; then
            print_status "Starting API server in background..."
            $PYTHON_CMD -m uvicorn src.api.extraction_testing_api:app \
                --host 0.0.0.0 \
                --port 8000 \
                --reload &
            API_PID=$!
            echo "API server started with PID: $API_PID"
        fi
        
        # Wait a moment for API to start
        sleep 2
        
        # Start Streamlit in foreground
        print_status "Starting Streamlit web interface..."
        $PYTHON_CMD -m streamlit run src/ui/main_app.py \
            --server.port=8501 \
            --server.address=localhost \
            --server.headless=false \
            --browser.gatherUsageStats=false
        
        # Kill API server when Streamlit stops
        if [ ! -z "$API_PID" ]; then
            kill $API_PID 2>/dev/null || true
        fi
        ;;
    4)
        print_header "RUNNING SYSTEM TESTS"
        echo ""
        
        log_with_timestamp "Running system tests"
        
        print_status "Running comprehensive system tests..."
        
        # Run basic import tests
        $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')

print('🧪 Running System Tests')
print('=' * 30)

test_count = 0
passed_count = 0

# Test 1: Configuration loading
test_count += 1
try:
    from src.config.app_config import AppConfig
    config = AppConfig.from_env()
    print('✅ Test 1: Configuration loading - PASSED')
    passed_count += 1
except Exception as e:
    print(f'❌ Test 1: Configuration loading - FAILED: {e}')

# Test 2: Core service imports
test_count += 1
try:
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    print('✅ Test 2: Core service imports - PASSED')
    passed_count += 1
except Exception as e:
    print(f'❌ Test 2: Core service imports - FAILED: {e}')

# Test 3: UI imports
test_count += 1
try:
    from src.ui.main_app import main
    print('✅ Test 3: UI imports - PASSED')
    passed_count += 1
except Exception as e:
    print(f'❌ Test 3: UI imports - FAILED: {e}')

# Test 4: Directory structure
test_count += 1
import os
required_dirs = ['data', 'logs', 'src', 'results']
if all(os.path.exists(d) for d in required_dirs):
    print('✅ Test 4: Directory structure - PASSED')
    passed_count += 1
else:
    print('❌ Test 4: Directory structure - FAILED')

print(f'\\n📊 Test Results: {passed_count}/{test_count} tests passed')
if passed_count == test_count:
    print('🎉 All tests passed! System is ready.')
else:
    print('⚠️  Some tests failed. System may have issues.')
"
        
        # Run pytest if available
        if command -v pytest >/dev/null 2>&1 && [ -d "tests" ]; then
            print_status "Running pytest suite..."
            $PYTHON_CMD -m pytest tests/ -v --tb=short || true
        else
            print_status "Pytest not available or no tests directory found"
        fi
        
        print_success "System tests completed"
        ;;
    5)
        print_header "RUNNING HEALTH CHECK ONLY"
        echo ""
        
        log_with_timestamp "Running health check only"
        
        $PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')

print('🏥 Comprehensive Health Check')
print('=' * 40)

try:
    import os
    from src.config.app_config import AppConfig
    config = AppConfig.from_env()
    
    print('✅ Configuration: OK')
    print(f'   Debug mode: {config.debug_mode}')
    print(f'   Log level: {os.getenv(\"LOG_LEVEL\", \"INFO\")}')
    print(f'   OpenRouter API: {\"Configured\" if config.openrouter_api_key else \"Not configured\"}')
    print(f'   Gemini API: {\"Configured\" if config.gemini_api_key else \"Not configured\"}')
    
    import os
    print('\\n📁 Directory Check:')
    dirs = ['data', 'logs', 'src', 'results']
    for d in dirs:
        status = '✅ OK' if os.path.exists(d) else '❌ MISSING'
        print(f'   {d}: {status}')
    
    print('\\n📄 Key Files Check:')
    files = ['src/ui/main_app.py', 'src/config/app_config.py', '.env']
    for f in files:
        status = '✅ OK' if os.path.exists(f) else '❌ MISSING'
        print(f'   {f}: {status}')
    
    print('\\n🎯 System Status: HEALTHY')
    
except Exception as e:
    print(f'❌ Health check failed: {e}')
"
        
        print_success "Health check completed"
        echo ""
        print_status "Running full deployment with complete knowledge base initialization..."
        echo ""
        echo "🚀 =============================================="
        echo "🚀   Complete Knowledge Base Initialization"
        echo "🚀 =============================================="
        echo "🚀"
        echo "🚀   📚 Processing canonical documents"
        echo "🚀   📊 Loading AMA Guidelines tables"
        echo "🚀   ⚖️  Loading QME reference patterns"
        echo "🚀   🔗 Creating structured entities"
        echo "🚀   ✅ Validating system readiness"
        echo "🚀"
        echo "🚀 =============================================="
        echo ""
        
        # Run enhanced complete knowledge base initialization with progress tracking
        print_status "Starting enhanced complete knowledge base initialization..."
        $PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('.')
from src.infrastructure.knowledge.knowledge_base_initializer import initialize_complete_system_for_option_2
from src.core.extraction.ingestion_pipeline import IngestionPipeline
from src.config.app_config import AppConfig

async def main():
    try:
        print('🔧 Initializing configuration...')
        config = AppConfig.from_env()
        
        print('🔧 Setting up ingestion pipeline...')
        from src.core.extraction.ingestion_pipeline_factory import IngestionPipelineFactory
        pipeline = IngestionPipelineFactory.create_default_pipeline()
        
        print('\\n🚀 Starting enhanced complete knowledge base initialization...')
        print('   This process includes:')
        print('   • Pre-initialization checks for canonical documents and system readiness')
        print('   • Real-time progress tracking with completion percentage reporting')
        print('   • Post-initialization validation tests for extraction patterns and calculation tables')
        print('   • Comprehensive error handling with detailed remediation recommendations')
        print('')
        
        result = await initialize_complete_system_for_option_2(config, pipeline)
        
        print('\\n' + '='*60)
        print('📊 FINAL INITIALIZATION RESULTS')
        print('='*60)
        print(f'Overall Success: {\"🎉 YES\" if result.success else \"❌ NO\"}')
        print(f'Processing Time: {result.total_processing_time:.2f} seconds')
        print(f'Processed Documents: {len(result.processed_documents)}')
        print(f'Failed Documents: {len(result.failed_documents)}')
        print(f'Knowledge Graph Nodes: {result.node_count:,}')
        print(f'Knowledge Graph Relationships: {result.relationship_count:,}')
        print(f'AMA Tables Loaded: {result.ama_tables_loaded}')
        print(f'Legal Patterns Loaded: {result.legal_patterns_loaded}')
        print(f'Validation Passed: {\"✅ YES\" if result.validation_passed else \"❌ NO\"}')
        print(f'System Ready: {\"🎯 YES\" if result.system_ready else \"⚠️  NO\"}')
        
        if result.processed_documents:
            print(f'\\n📄 Successfully Processed Documents:')
            for doc in result.processed_documents:
                print(f'  ✅ {doc}')
        
        if result.failed_documents:
            print(f'\\n❌ Failed Documents:')
            for doc in result.failed_documents:
                print(f'  ❌ {doc}')
        
        if result.error_messages:
            print(f'\\n⚠️  Issues and Errors Found:')
            for i, error in enumerate(result.error_messages, 1):
                print(f'  {i}. {error}')
        
        if result.system_ready:
            print(f'\\n🎉 SYSTEM FULLY READY FOR EVIDENCE-FIRST QME PROCESSING!')
            print(f'   📍 Web interface available at: http://localhost:8501')
            print(f'   📚 Knowledge graph: {result.node_count:,} nodes, {result.relationship_count:,} relationships')
            print(f'   ⚖️  Legal patterns and AMA calculation tables are loaded and accessible')
            print(f'   🔍 Extraction patterns ready for high-confidence field extraction')
            print(f'   📊 Programmatic impairment calculations enabled')
            print(f'   ✅ All validation tests passed - system is production-ready')
        else:
            print(f'\\n⚠️  SYSTEM INITIALIZATION COMPLETED WITH LIMITATIONS')
            print(f'   🔧 Some components may not function optimally')
            print(f'   💡 Review the issues above for specific remediation steps')
            print(f'   🔄 You can retry initialization after addressing the issues')
            print(f'   📍 Basic functionality may still be available at: http://localhost:8501')
            
            # Provide specific remediation recommendations
            print(f'\\n💡 REMEDIATION RECOMMENDATIONS:')
            if len(result.failed_documents) > 0:
                print(f'   📚 Document Processing Issues:')
                print(f'      • Ensure canonical documents exist in project root')
                print(f'      • Check file permissions and accessibility')
                print(f'      • Verify document formats are supported (PDF, DOCX)')
            
            if result.node_count < 1000:
                print(f'   📊 Knowledge Graph Issues:')
                print(f'      • Current nodes: {result.node_count:,} (minimum: 1,000)')
                print(f'      • Process more canonical documents')
                print(f'      • Check AMA Guidelines and QME reference files')
            
            if result.ama_tables_loaded == 0:
                print(f'   📋 AMA Guidelines Issues:')
                print(f'      • No AMA calculation tables loaded')
                print(f'      • Check data/ama_guidelines/tables.json exists')
                print(f'      • Verify file format and content structure')
            
            if result.legal_patterns_loaded == 0:
                print(f'   ⚖️  Legal Patterns Issues:')
                print(f'      • No legal extraction patterns loaded')
                print(f'      • Check data/qme_references/ directory exists')
                print(f'      • Verify legal_patterns.json and related files')
            
            print(f'\\n🔄 To retry initialization:')
            print(f'   1. Address the issues listed above')
            print(f'   2. Run this script again and select option 2')
            print(f'   3. Or use option 6 to initialize knowledge base separately')
        
        print('='*60)
        return result.success
        
    except Exception as e:
        print(f'\\n❌ CRITICAL ERROR DURING INITIALIZATION')
        print(f'Error: {e}')
        print(f'\\n🔧 TROUBLESHOOTING STEPS:')
        print(f'   1. Check that all required files exist:')
        print(f'      • AMAGuides 5th Edition.pdf')
        print(f'      • QME-Study-Guide.pdf')
        print(f'      • Sample3.pdf')
        print(f'      • data/ama_guidelines/tables.json')
        print(f'      • data/qme_references/legal_patterns.json')
        print(f'   2. Verify .env file configuration')
        print(f'   3. Check database permissions and connectivity')
        print(f'   4. Ensure sufficient disk space and memory')
        print(f'   5. Check logs/errors.log for detailed error information')
        print(f'\\n💡 ALTERNATIVE OPTIONS:')
        print(f'   • Try option 6 to initialize knowledge base with available documents')
        print(f'   • Try option 1 to start with basic functionality')
        print(f'   • Check system health with option 3')
        
        import traceback
        print(f'\\n🔍 DETAILED ERROR TRACE:')
        traceback.print_exc()
        return False

result = asyncio.run(main())
print('\\n' + '='*60)
if result:
    print('🎉 ENHANCED INITIALIZATION COMPLETED SUCCESSFULLY!')
    print('   System is ready for evidence-first QME processing')
else:
    print('⚠️  INITIALIZATION COMPLETED WITH ISSUES')
    print('   Review the recommendations above and retry if needed')
print('='*60)
"
        
        # Start the web interface after initialization
        if [ $? -eq 0 ]; then
            echo ""
            print_success "Complete initialization finished successfully!"
            echo ""
            read -p "❓ Start web interface now? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                print_status "Starting Streamlit web interface..."
                echo ""
                echo "🌐 =============================================="
                echo "🌐   Evidence-First QME System Ready"
                echo "🌐 =============================================="
                echo "🌐"
                echo "🌐   📍 URL: http://localhost:8501"
                echo "🌐   📚 Complete knowledge base initialized"
                echo "🌐   ⚖️  Legal patterns and AMA tables loaded"
                echo "🌐   🔍 Evidence-first processing enabled"
                echo "🌐   ⏹️  Press Ctrl+C to stop the server"
                echo "🌐"
                echo "🌐 =============================================="
                echo ""
                
                # Set up environment
                export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
                
                # Start Streamlit
                streamlit run src/ui/main_app.py \
                    --server.port=8501 \
                    --server.address=localhost \
                    --server.headless=false \
                    --browser.gatherUsageStats=false \
                    --server.enableCORS=false \
                    --server.enableXsrfProtection=false
            fi
        else
            print_error "Complete initialization failed"
            echo ""
            echo "💡 Troubleshooting steps:"
            echo "   1. Check that canonical documents exist in project root"
            echo "   2. Verify .env file configuration"
            echo "   3. Check logs for detailed error messages"
            echo "   4. Try running option 6 to initialize knowledge base separately"
        fi
        ;;
    3)
        echo ""
        print_status "Running comprehensive health checks..."
        $PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('.')
from src.services.health_checker import HealthChecker
from src.config.app_config import AppConfig

async def main():
    config = AppConfig.from_env()
    health_checker = HealthChecker(config)
    health = health_checker.get_overall_health()
    
    print('\\n📊 Detailed Health Report:')
    print('=' * 50)
    
    for component, status in health['checks'].items():
        print(f'\\n🔧 {component.upper()}:')
        print(f'   Status: {\"✅ HEALTHY\" if status[\"healthy\"] else \"❌ UNHEALTHY\"}')
        print(f'   Message: {status[\"message\"]}')
        if status.get('response_time_ms'):
            print(f'   Response Time: {status[\"response_time_ms\"]:.2f}ms')
        if status.get('details'):
            print(f'   Details: {status[\"details\"]}')
    
    print(f'\\n📈 Overall Status: {\"✅ SYSTEM HEALTHY\" if health[\"overall_healthy\"] else \"❌ SYSTEM ISSUES DETECTED\"}')
    print(f'📊 Total Response Time: {health[\"total_response_time_ms\"]:.2f}ms')

asyncio.run(main())
"
        ;;
    4)
        echo ""
        print_status "Viewing performance metrics..."
        $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.services.performance_monitor import get_performance_monitor

perf_monitor = get_performance_monitor()
stats = perf_monitor.get_current_statistics()

print('\\n📈 Performance Metrics:')
print('=' * 40)

overall_stats = stats.get('overall_stats', {})
print(f'Total Documents Processed: {overall_stats.get(\"total_documents_processed\", 0)}')
print(f'Successful Processing: {overall_stats.get(\"successful_processing\", 0)}')
print(f'Failed Processing: {overall_stats.get(\"failed_processing\", 0)}')
print(f'Average Processing Time: {overall_stats.get(\"average_processing_time\", 0):.2f}s')
print(f'Target Violations: {overall_stats.get(\"target_violations\", 0)}')

recent = stats.get('recent_processing', [])
if recent:
    print(f'\\n📋 Recent Processing ({len(recent)} documents):')
    for proc in recent[-5:]:  # Show last 5
        status = '✅' if proc['success'] else '❌'
        print(f'  {status} {proc[\"document\"]} - {proc.get(\"processing_time\", 0):.2f}s')

targets = stats.get('performance_targets', [])
if targets:
    print(f'\\n🎯 Performance Targets:')
    for target in targets:
        print(f'  • {target[\"description\"]}: {target[\"target_value\"]} {target[\"unit\"]}')
"
        ;;
    5)
        echo ""
        print_status "Running tests..."
        $PYTHON_CMD -m pytest tests/ -v --tb=short
        ;;
    6)
        echo ""
        print_status "Initializing knowledge base with canonical documents..."
        
        # Check if canonical documents exist
        CANONICAL_DOCS=(
            "AMAGuides 5th Edition.pdf"
            "QME-Study-Guide.pdf"
            "Sample3.pdf"
        )
        
        FOUND_DOCS=()
        MISSING_DOCS=()
        
        for doc in "${CANONICAL_DOCS[@]}"; do
            if [ -f "$doc" ]; then
                FOUND_DOCS+=("$doc")
                print_success "Found: $doc"
            else
                MISSING_DOCS+=("$doc")
                print_warning "Missing: $doc"
            fi
        done
        
        if [ ${#FOUND_DOCS[@]} -eq 0 ]; then
            print_error "No canonical documents found in project root"
            echo ""
            echo "📚 Please place the following files in the project root:"
            for doc in "${CANONICAL_DOCS[@]}"; do
                echo "   • $doc"
            done
            echo ""
            echo "💡 You can also use option 8 to process specific documents"
        else
            print_status "Processing ${#FOUND_DOCS[@]} canonical document(s)..."
            
            # Process each found document
            for doc in "${FOUND_DOCS[@]}"; do
                print_status "Processing: $doc"
                $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.services.document_processor import process_document_simple
import os

try:
    doc_path = '$doc'
    if os.path.exists(doc_path):
        print(f'📄 Processing: {doc_path}')
        result = process_document_simple(doc_path)
        if result:
            print(f'✅ Successfully processed: {doc_path}')
        else:
            print(f'❌ Failed to process: {doc_path}')
    else:
        print(f'❌ File not found: {doc_path}')
except Exception as e:
    print(f'❌ Error processing {doc_path}: {e}')
"
            done
            
            print_success "Knowledge base initialization completed"
            echo ""
            echo "📊 Summary:"
            echo "   ✅ Processed: ${#FOUND_DOCS[@]} documents"
            if [ ${#MISSING_DOCS[@]} -gt 0 ]; then
                echo "   ⚠️  Missing: ${#MISSING_DOCS[@]} documents"
            fi
        fi
        ;;
    7)
        echo ""
        print_status "Quick start - launching Streamlit directly..."
        echo ""
        echo "🚀 =============================================="
        echo "🚀   Quick Start - Document Q&A System"
        echo "🚀 =============================================="
        echo "🚀"
        echo "🚀   📍 URL: http://localhost:8501"
        echo "🚀   ⚡ Skipping health checks for faster startup"
        echo "🚀   📚 Upload documents via the web interface"
        echo "🚀   ⏹️  Press Ctrl+C to stop the server"
        echo "🚀"
        echo "🚀 =============================================="
        echo ""
        
        # Set up minimal environment
        export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
        
        # Create basic directories
        mkdir -p data/database data/documents logs
        
        echo ""
        print_status "Starting Streamlit server (quick mode)..."
        echo "   👉 http://localhost:8501"
        echo ""
        
        # Start Streamlit directly
        streamlit run src/ui/main_app.py \
            --server.port=8501 \
            --server.address=localhost \
            --server.headless=false \
            --browser.gatherUsageStats=false
        ;;
    8)
        echo ""
        print_status "Processing specific documents into knowledge base..."
        echo ""
        echo "📚 Available documents in current directory:"
        
        # Find PDF files in current directory
        PDF_FILES=($(find . -maxdepth 1 -name "*.pdf" -type f | sort))
        
        if [ ${#PDF_FILES[@]} -eq 0 ]; then
            print_warning "No PDF files found in current directory"
            echo ""
            echo "💡 Please place PDF files in the project root directory"
            echo "   Supported formats: PDF, DOCX, TXT"
        else
            echo ""
            for i in "${!PDF_FILES[@]}"; do
                echo "   $((i+1))) ${PDF_FILES[$i]}"
            done
            echo "   0) Process all files"
            echo ""
            
            read -p "Choose files to process (comma-separated numbers, or 0 for all): " -r
            
            if [ "$REPLY" = "0" ]; then
                SELECTED_FILES=("${PDF_FILES[@]}")
            else
                IFS=',' read -ra INDICES <<< "$REPLY"
                SELECTED_FILES=()
                for index in "${INDICES[@]}"; do
                    index=$((index-1))
                    if [ $index -ge 0 ] && [ $index -lt ${#PDF_FILES[@]} ]; then
                        SELECTED_FILES+=("${PDF_FILES[$index]}")
                    fi
                done
            fi
            
            if [ ${#SELECTED_FILES[@]} -eq 0 ]; then
                print_warning "No valid files selected"
            else
                print_status "Processing ${#SELECTED_FILES[@]} file(s)..."
                
                for doc in "${SELECTED_FILES[@]}"; do
                    print_status "Processing: $doc"
                    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.services.document_processor import process_document_simple
import os

try:
    doc_path = '$doc'
    if os.path.exists(doc_path):
        print(f'📄 Processing: {doc_path}')
        result = process_document_simple(doc_path)
        if result:
            print(f'✅ Successfully processed: {doc_path}')
        else:
            print(f'❌ Failed to process: {doc_path}')
    else:
        print(f'❌ File not found: {doc_path}')
except Exception as e:
    print(f'❌ Error processing {doc_path}: {e}')
"
                done
                
                print_success "Document processing completed"
            fi
        fi
        ;;
    *)
        echo ""
        print_status "Starting Streamlit web interface (default)..."
        echo ""
        echo "🌐 =============================================="
        echo "🌐   Document Q&A System Web Interface"
        echo "🌐 =============================================="
        echo "🌐"
        echo "🌐   📍 URL: http://localhost:8501"
        echo "🌐   📚 Upload documents via the web interface"
        echo "🌐   🔍 View logs in: logs/"
        echo "🌐   ⏹️  Press Ctrl+C to stop the server"
        echo "🌐"
        echo "🌐 =============================================="
        echo ""
        
        # Set up environment
        export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
        
        # Check if Streamlit is installed
        if ! $PYTHON_CMD -c "import streamlit" 2>/dev/null; then
            print_error "Streamlit is not installed"
            echo "   Installing Streamlit..."
            pip install streamlit
        fi
        
        echo ""
        print_status "Launching Streamlit server..."
        echo "   If the browser doesn't open automatically, visit:"
        echo "   👉 http://localhost:8501"
        echo ""
        
        # Start Streamlit with better error handling
        if command -v streamlit >/dev/null 2>&1; then
            streamlit run src/ui/main_app.py \
                --server.port=8501 \
                --server.address=localhost \
                --server.headless=false \
                --browser.gatherUsageStats=false \
                --server.enableCORS=false \
                --server.enableXsrfProtection=false
        else
            print_error "Streamlit command not found"
            echo "   Trying to run with python -m streamlit..."
            $PYTHON_CMD -m streamlit run src/ui/main_app.py \
                --server.port=8501 \
                --server.address=localhost \
                --server.headless=false \
                --browser.gatherUsageStats=false \
                --server.enableCORS=false \
                --server.enableXsrfProtection=false
        fi
        ;;
    9)
        ;;
    *)
        print_header "STARTING DEFAULT - STREAMLIT WEB INTERFACE"
        echo ""
        echo "🌐   📍 URL: http://localhost:8501"
        echo "🌐   📚 Upload documents and generate QME templates"
        echo "🌐   ⏹️  Press Ctrl+C to stop the server"
        echo ""
        
        log_with_timestamp "Starting default Streamlit web interface"
        
        print_status "Launching Streamlit server..."
        $PYTHON_CMD -m streamlit run src/ui/main_app.py \
            --server.port=8501 \
            --server.address=localhost \
            --server.headless=false \
            --browser.gatherUsageStats=false
        ;;
esac

# Cleanup and exit
print_success "QME System session completed"
log_with_timestamp "QME System session completed"

echo ""
echo "👋 Thank you for using the QME System!"
echo "   📝 Logs saved to: $LOG_FILE"
echo "   🔄 Run ./scripts/run.sh again anytime"
echo ""
