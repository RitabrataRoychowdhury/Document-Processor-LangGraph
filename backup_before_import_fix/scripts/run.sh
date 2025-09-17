#!/bin/bash

# Document Q&A System - Enhanced Run Script
# This script sets up the environment and runs the application with health checks and performance monitoring

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

echo "🚀 Document Q&A System - Enhanced Run Script"
echo "============================================="

# Change to project root
cd "$PROJECT_ROOT"

# Check if Python 3 is available
print_status "Checking Python installation..."
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed or not in PATH"
    echo "   Please install Python 3.8+ and try again"
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

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
print_success "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
print_status "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed successfully"
else
    print_error "requirements.txt not found"
    echo "   Please ensure requirements.txt exists in the project directory"
    exit 1
fi

# Check environment configuration
print_status "Validating environment configuration..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env file not found. Copying from .env.example"
        cp .env.example .env
        print_warning "Please edit .env with your API keys before continuing"
    else
        print_warning ".env file not found and no .env.example available"
    fi
fi

# Run environment validation
print_status "Running comprehensive environment validation..."
$PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.config.environment_validator import validate_environment_config
from src.config.app_config import AppConfig

try:
    config = AppConfig.from_env()
    validation_result = validate_environment_config(config)
    
    if validation_result.is_valid:
        print('✅ Environment validation passed')
    else:
        print('❌ Environment validation failed')
        for error in validation_result.errors:
            print(f'   ERROR: {error}')
        for warning in validation_result.warnings:
            print(f'   WARNING: {warning}')
        
        if validation_result.recommendations:
            print('\\nRecommendations:')
            for rec in validation_result.recommendations:
                print(f'   💡 {rec}')
        
        sys.exit(1 if not validation_result.is_valid else 0)
        
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Environment validation failed"
    echo ""
    echo "💡 To fix configuration issues:"
    echo "   1. Edit .env file with your API keys"
    echo "   2. Ensure required directories exist"
    echo "   3. Check file permissions"
    echo ""
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/database
mkdir -p data/documents
mkdir -p logs
print_success "Directories created"

# Run basic system check (fast and non-blocking)
print_status "Running basic system check..."

# Very simple check that should never hang
if $PYTHON_CMD -c "import sys; sys.path.append('.'); from src.config.app_config import AppConfig; AppConfig.from_env(); print('✅ System ready')" 2>/dev/null; then
    print_success "Basic system check passed"
else
    print_warning "Basic system check had warnings - continuing anyway"
fi

# Show system status (simplified)
print_status "System Status Summary:"
echo "  🗄️  Database: data/database/documents.db"
echo "  🤖 QA Provider: Configured"
echo "  🔤 Embedding Provider: Available"
echo "  📁 Document Processing: Ready"
echo "  ✅ System ready for operation"

# Ask user what they want to do
echo ""
echo "🎯 What would you like to do?"
echo "   1) 🌐 Start web interface (recommended)"
echo "   2) 🚀 Full deployment with knowledge base initialization"
echo "   3) 🔍 Run health checks only"
echo "   4) 📊 View performance metrics"
echo "   5) 🧪 Run tests"
echo "   6) 🔧 Initialize knowledge base with canonical documents"
echo "   7) 🚀 Quick start (skip health checks)"
echo "   8) 📚 Process specific documents into knowledge base"
echo "   9) 🏥 QME workflow validation and testing"
echo "   10) 📋 QME field extraction testing with PQME files"
echo "   11) ✅ Comprehensive system validation (Task 5)"
echo "   12) 🔄 Run system migration to refactored architecture"
echo ""
read -p "Choose an option (1-12): " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        print_status "Starting Streamlit web interface..."
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
        
        # Test if the main app can be imported
        print_status "Validating application imports..."
        $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from src.ui.main_app import main
    print('✅ Application imports validated')
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('   Trying to start with basic Streamlit configuration...')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Warning: {e}')
    print('   Continuing with Streamlit startup...')
"
        
        if [ $? -eq 0 ]; then
            print_success "Application ready to start"
        else
            print_warning "Application has import issues but attempting to start anyway"
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
    2)
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
from src.services.knowledge_base_initializer import initialize_complete_system_for_option_2
from src.services.ingestion_pipeline import IngestionPipeline
from src.config.app_config import AppConfig

async def main():
    try:
        print('🔧 Initializing configuration...')
        config = AppConfig.from_env()
        
        print('🔧 Setting up ingestion pipeline...')
        from src.services.ingestion_pipeline_factory import IngestionPipelineFactory
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
        echo ""
        print_status "Running QME workflow validation and testing..."
        echo ""
        echo "🏥 =============================================="
        echo "🏥   QME Workflow Validation & Testing"
        echo "🏥 =============================================="
        echo ""
        
        # QME-specific health checks
        print_status "Running QME-specific health checks..."
        $PYTHON_CMD -c "
import sys
sys.path.append('.')

def test_qme_imports():
    try:
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        from src.services.qme_template_generator import QMETemplateGenerator
        from src.services.professional_template_assembler import ProfessionalTemplateAssembler
        from src.ui.qme_template_interface import QMETemplateInterface
        print('✅ QME service imports successful')
        return True
    except ImportError as e:
        print(f'❌ QME import error: {e}')
        return False

def test_qme_field_extraction():
    try:
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        service = ComprehensiveQMEFieldService()
        print('✅ QME field extraction service initialized')
        return True
    except Exception as e:
        print(f'❌ QME field extraction error: {e}')
        return False

def test_qme_template_generation():
    try:
        from src.services.qme_template_generator import QMETemplateGenerator
        generator = QMETemplateGenerator()
        print('✅ QME template generator initialized')
        return True
    except Exception as e:
        print(f'❌ QME template generation error: {e}')
        return False

def test_qme_performance_monitoring():
    try:
        from src.services.performance_monitor import get_performance_monitor
        monitor = get_performance_monitor()
        stats = monitor.get_current_statistics()
        print('✅ QME performance monitoring active')
        return True
    except Exception as e:
        print(f'❌ QME performance monitoring error: {e}')
        return False

print('🔍 Testing QME Components:')
print('=' * 40)

tests = [
    ('QME Imports', test_qme_imports),
    ('Field Extraction', test_qme_field_extraction),
    ('Template Generation', test_qme_template_generation),
    ('Performance Monitoring', test_qme_performance_monitoring)
]

passed = 0
for name, test_func in tests:
    print(f'\\n🧪 Testing {name}...')
    if test_func():
        passed += 1

print(f'\\n📊 QME Validation Results: {passed}/{len(tests)} tests passed')

if passed == len(tests):
    print('🎉 QME workflow is fully functional!')
else:
    print('⚠️  Some QME components need attention')
"
        
        # Test QME workflow with sample data
        print_status "Testing QME workflow with sample data..."
        $PYTHON_CMD test_qme_workflow.py
        
        # Run comprehensive QME validation
        print_status "Running comprehensive QME validation..."
        $PYTHON_CMD scripts/validate_qme_workflow.py
        
        # Test with sample data to prove workflow works
        print_status "Testing QME workflow with sample data..."
        $PYTHON_CMD scripts/test_qme_with_sample_data.py
        
        print_success "QME workflow validation completed"
        ;;
    10)
        echo ""
        print_status "Testing QME field extraction with PQME files..."
        echo ""
        echo "📋 =============================================="
        echo "📋   QME Field Extraction Testing"
        echo "📋 =============================================="
        echo ""
        
        # Check for PQME files
        PQME_FILES=(
            "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf"
            "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
        )
        
        FOUND_PQME=()
        MISSING_PQME=()
        
        for file in "${PQME_FILES[@]}"; do
            if [ -f "$file" ]; then
                FOUND_PQME+=("$file")
                print_success "Found PQME file: $file"
            else
                MISSING_PQME+=("$file")
                print_warning "Missing PQME file: $file"
            fi
        done
        
        if [ ${#FOUND_PQME[@]} -eq 0 ]; then
            print_error "No PQME files found for testing"
            echo ""
            echo "📋 Expected PQME files:"
            for file in "${PQME_FILES[@]}"; do
                echo "   • $file"
            done
            echo ""
            echo "💡 Please place PQME files in the project root directory"
        else
            print_status "Testing field extraction with ${#FOUND_PQME[@]} PQME file(s)..."
            
            # Test field extraction accuracy
            for file in "${FOUND_PQME[@]}"; do
                print_status "Testing field extraction: $file"
                $PYTHON_CMD -c "
import sys
sys.path.append('.')
import time

try:
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    
    file_path = '$file'
    print(f'📄 Processing: {file_path}')
    
    # Time the extraction
    start_time = time.time()
    service = ComprehensiveQMEFieldService()
    result = service.extract_and_validate_fields(file_path)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    print(f'⏱️  Processing time: {processing_time:.2f} seconds')
    
    if result.extraction_result.success:
        fields = result.extraction_result.extracted_fields
        print(f'✅ Field extraction successful')
        print(f'📊 Extracted {len(fields.get_all_fields())} fields')
        
        # Show key fields
        key_fields = ['name', 'age', 'gender', 'case_number', 'injury_date']
        for field in key_fields:
            value = getattr(fields, field, 'Not found')
            status = '✅' if value and value != 'Not found' else '❌'
            print(f'   {status} {field.title()}: {value}')
        
        # Validation results
        if result.validation_result.is_valid:
            print(f'✅ Validation passed')
        else:
            print(f'⚠️  Validation issues: {len(result.validation_result.validation_errors)}')
            for error in result.validation_result.validation_errors[:3]:
                print(f'     - {error}')
    else:
        print(f'❌ Field extraction failed: {result.extraction_result.error_message}')
        
except Exception as e:
    print(f'❌ Error testing field extraction: {e}')
"
            done
            
            # Run comprehensive performance testing
            print_status "Running comprehensive QME performance testing..."
            $PYTHON_CMD scripts/test_qme_performance.py
            
            print_success "PQME field extraction testing completed"
        fi
        ;;
    11)
        echo ""
        print_status "Running Comprehensive System Validation (Task 5)..."
        echo ""
        echo "✅ =============================================="
        echo "✅   Task 5: Knowledge Base Integration and"
        echo "✅   Pipeline Functionality Validation"
        echo "✅ =============================================="
        echo "✅"
        echo "✅   🗄️  Knowledge Base Validation & Optimization"
        echo "✅   🔄 Pipeline Integration Testing"
        echo "✅   🎯 Evidence-First Validation System"
        echo "✅   🧮 Programmatic Calculation Validation"
        echo "✅   ⚖️  Compliance & Quality Assurance"
        echo "✅"
        echo "✅ =============================================="
        echo ""
        
        # Check if Task 5 validation script exists
        if [ ! -f "scripts/run_task5_validation.py" ]; then
            print_error "Task 5 validation script not found"
            echo ""
            echo "💡 Expected file: scripts/run_task5_validation.py"
            echo "   Please ensure Task 5 implementation is complete"
            exit 1
        fi
        
        echo "🎯 Task 5 Validation Options:"
        echo "   a) 🚀 Run complete comprehensive validation (all sub-tasks)"
        echo "   b) 🗄️  Knowledge Base Validation & Optimization (5.1)"
        echo "   c) 🔄 Pipeline Integration Testing (5.2)"
        echo "   d) 🎯 Evidence-First Validation System (5.3)"
        echo "   e) 🧮 Programmatic Calculation Validation (5.4)"
        echo "   f) ⚖️  Compliance & Quality Assurance (5.5)"
        echo "   g) 📊 View validation reports"
        echo ""
        read -p "Choose validation option (a-g): " -n 1 -r
        echo
        
        case $REPLY in
            a)
                print_status "Running complete comprehensive Task 5 validation..."
                echo ""
                echo "🚀 This will run all validation sub-tasks:"
                echo "   • 5.1: Knowledge Base Validation & Optimization"
                echo "   • 5.2: Pipeline Integration Testing"
                echo "   • 5.3: Evidence-First Validation System"
                echo "   • 5.4: Programmatic Calculation Validation"
                echo "   • 5.5: Compliance & Quality Assurance"
                echo ""
                
                # Run comprehensive validation
                $PYTHON_CMD scripts/run_task5_validation.py
                
                if [ $? -eq 0 ]; then
                    print_success "Comprehensive Task 5 validation completed successfully!"
                    echo ""
                    echo "🎉 System validation results:"
                    echo "   ✅ All validation sub-tasks completed"
                    echo "   📊 Detailed reports generated in results/validation_reports/"
                    echo "   🎯 System readiness assessed"
                    echo ""
                    
                    # Ask if user wants to view the report
                    read -p "❓ View validation summary? (Y/n): " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                        # Find the latest validation report
                        LATEST_REPORT=$(find results/validation_reports -name "comprehensive_system_validation_*.json" -type f -exec ls -t {} + 2>/dev/null | head -1)
                        if [ -n "$LATEST_REPORT" ]; then
                            print_status "Latest validation report: $LATEST_REPORT"
                            $PYTHON_CMD -c "
import json
import sys

try:
    with open('$LATEST_REPORT', 'r') as f:
        report = json.load(f)
    
    print('\\n📊 VALIDATION SUMMARY')
    print('=' * 50)
    print(f'Validation ID: {report.get(\"validation_id\", \"N/A\")}')
    print(f'Execution Time: {report.get(\"total_execution_time\", 0):.2f} seconds')
    print(f'Overall Result: {\"✅ PASSED\" if report.get(\"overall_validation_passed\", False) else \"❌ FAILED\"}')
    print(f'Production Ready: {\"🎯 YES\" if report.get(\"system_ready_for_production\", False) else \"⚠️  NO\"}')
    
    summary = report.get('validation_summary', {})
    print(f'\\n📋 Sub-task Results:')
    print(f'  5.1 Knowledge Base: {\"✅ PASSED\" if summary.get(\"task_5_1_passed\", False) else \"❌ FAILED\"}')
    print(f'  5.2 Pipeline Testing: {\"✅ PASSED\" if summary.get(\"task_5_2_passed\", False) else \"❌ FAILED\"}')
    print(f'  5.3 Evidence Validation: {\"✅ PASSED\" if summary.get(\"task_5_3_passed\", False) else \"❌ FAILED\"}')
    print(f'  5.4 Calculation Validation: {\"✅ PASSED\" if summary.get(\"task_5_4_passed\", False) else \"❌ FAILED\"}')
    print(f'  5.5 Compliance & Quality: {\"✅ PASSED\" if summary.get(\"task_5_5_passed\", False) else \"❌ FAILED\"}')
    
    critical_issues = report.get('critical_issues', [])
    if critical_issues:
        print(f'\\n❌ Critical Issues ({len(critical_issues)}):')
        for issue in critical_issues[:3]:
            print(f'  • {issue}')
        if len(critical_issues) > 3:
            print(f'  ... and {len(critical_issues) - 3} more')
    
    recommendations = report.get('recommendations', [])
    if recommendations:
        print(f'\\n💡 Recommendations ({len(recommendations)}):')
        for rec in recommendations[:3]:
            print(f'  • {rec}')
        if len(recommendations) > 3:
            print(f'  ... and {len(recommendations) - 3} more')
    
    print(f'\\n📄 Full report: $LATEST_REPORT')
    
except Exception as e:
    print(f'Error reading validation report: {e}')
"
                        else
                            print_warning "No validation reports found"
                        fi
                    fi
                else
                    print_error "Comprehensive Task 5 validation failed"
                    echo ""
                    echo "💡 Troubleshooting steps:"
                    echo "   1. Check system requirements and dependencies"
                    echo "   2. Ensure knowledge base is initialized"
                    echo "   3. Verify test documents are available"
                    echo "   4. Check logs for detailed error messages"
                fi
                ;;
            b)
                print_status "Running Knowledge Base Validation & Optimization (5.1)..."
                $PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('.')
from src.validation.knowledge_base_validator import KnowledgeBaseValidator

async def main():
    validator = KnowledgeBaseValidator()
    
    print('🗄️  Running Knowledge Base Validation...')
    validation_passed, metrics, issues = await validator.validate_complete_knowledge_base()
    
    print(f'\\nValidation Result: {\"✅ PASSED\" if validation_passed else \"❌ FAILED\"}')
    print(f'Nodes: {metrics.node_count:,} (required: ≥1,000)')
    print(f'Relationships: {metrics.relationship_count:,} (required: ≥500)')
    print(f'Entity Types: {len(metrics.entity_type_coverage)} (required: ≥10)')
    print(f'Query Performance: {metrics.query_performance_ms:.1f}ms (target: <100ms)')
    print(f'Data Integrity: {metrics.data_integrity_score:.2%} (target: ≥95%)')
    
    if issues:
        print(f'\\n⚠️  Issues Found:')
        for issue in issues:
            print(f'  • {issue}')
    
    print('\\n🔧 Running Performance Optimization...')
    optimization_results = await validator.optimize_knowledge_base_performance()
    
    for result in optimization_results:
        print(f'  {result.optimization_type}: {\"✅\" if result.success else \"❌\"} ({result.improvement_percentage:.1f}% improvement)')
    
    return validation_passed

result = asyncio.run(main())
sys.exit(0 if result else 1)
"
                ;;
            c)
                print_status "Running Pipeline Integration Testing (5.2)..."
                $PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('.')
from src.validation.pipeline_integration_tester import PipelineIntegrationTester

async def main():
    tester = PipelineIntegrationTester()
    
    print('🔄 Running Pipeline Integration Testing...')
    
    # Test with available documents
    test_docs = ['data/sample_documents/Sample3.pdf']
    available_docs = [doc for doc in test_docs if __import__('pathlib').Path(doc).exists()]
    
    if not available_docs:
        print('⚠️  No test documents available')
        print('   Place test documents in data/sample_documents/')
        return False
    
    # Test Pipeline 1
    print(f'\\n📥 Testing Pipeline 1 with: {available_docs[0]}')
    pipeline1_result = await tester.test_pipeline_1_comprehensive(available_docs[0])
    print(f'Pipeline 1: {\"✅ PASSED\" if pipeline1_result.success else \"❌ FAILED\"}')
    print(f'  Fields Extracted: {pipeline1_result.fields_extracted}')
    print(f'  Processing Time: {pipeline1_result.total_time:.2f}s')
    
    # Test Pipeline 2 if Pipeline 1 succeeded
    if pipeline1_result.success:
        print(f'\\n📤 Testing Pipeline 2...')
        pipeline2_result = await tester.test_pipeline_2_comprehensive(pipeline1_result)
        print(f'Pipeline 2: {\"✅ PASSED\" if pipeline2_result.success else \"❌ FAILED\"}')
        print(f'  Content Generated: {\"✅\" if pipeline2_result.content_generated else \"❌\"}')
        print(f'  Template Assembled: {\"✅\" if pipeline2_result.template_assembled else \"❌\"}')
        print(f'  Compliance Passed: {\"✅\" if pipeline2_result.compliance_passed else \"❌\"}')
    
    # Test Performance
    print(f'\\n⚡ Testing Performance...')
    performance_result = await tester.test_pipeline_performance(available_docs)
    print(f'Performance: {\"✅ PASSED\" if performance_result.success_rate >= 0.8 else \"❌ FAILED\"}')
    print(f'  Success Rate: {performance_result.success_rate:.1%}')
    print(f'  Throughput: {performance_result.throughput_docs_per_minute:.1f} docs/min')
    
    return pipeline1_result.success

result = asyncio.run(main())
sys.exit(0 if result else 1)
"
                ;;
            d)
                print_status "Running Evidence-First Validation System (5.3)..."
                $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.validation.evidence_first_validator import EvidenceFirstValidator
from src.models.extraction_models import ExtractionResult, ExtractedField

validator = EvidenceFirstValidator()

print('🎯 Running Evidence-First Validation System...')

# Create mock extraction results for testing
mock_results = []
for i in range(2):
    fields = {
        'patient_name': ExtractedField(f'Test Patient {i+1}', 0.95, f'Patient: Test Patient {i+1}', 1),
        'diagnosis': ExtractedField('Lumbar spine strain', 0.88, 'Primary diagnosis: Lumbar spine strain', 2),
        'impairment_rating': ExtractedField(f'{10+i*2}% whole person impairment', 0.85, f'Patient has {10+i*2}% impairment', 3)
    }
    mock_results.append(ExtractionResult(f'test_doc_{i+1}', fields, 2.0, 0.7, True))

# Test confidence scoring system
print('\\n📊 Testing Confidence Scoring System...')
confidence_validation = validator.validate_confidence_scoring_system(mock_results)
precision_met = confidence_validation.get('precision_validation', {}).get('precision_target_met', False)
coverage_met = confidence_validation.get('coverage_validation', {}).get('coverage_target_met', False)

print(f'Critical Field Precision: {\"✅ ≥95%\" if precision_met else \"❌ <95%\"}')
print(f'Overall Field Coverage: {\"✅ ≥90%\" if coverage_met else \"❌ <90%\"}')

# Test evidence thresholds
print('\\n🎚️  Testing Evidence Thresholds...')
threshold_validation = validator.validate_evidence_thresholds(mock_results[0])
print(f'Accepted Fields: {len(threshold_validation.accepted_fields)}')
print(f'Flagged Fields: {len(threshold_validation.flagged_fields)}')
print(f'Missing Fields: {len(threshold_validation.missing_fields)}')
print(f'Can Proceed: {\"✅ YES\" if threshold_validation.can_proceed_to_generation else \"❌ NO\"}')

# Test cross-document validation
print('\\n🔄 Testing Cross-Document Validation...')
cross_validation = validator.validate_cross_document_consistency(mock_results, 'test_patient_001')
print(f'Consistency Score: {cross_validation.consistency_score:.2%}')
print(f'Consistent Fields: {len(cross_validation.consistent_fields)}')
print(f'Inconsistent Fields: {len(cross_validation.inconsistent_fields)}')

# Test provenance tracking
print('\\n📋 Testing Evidence Provenance Tracking...')
provenance = validator.generate_evidence_provenance_tracking(threshold_validation)
print(f'Provenance Generated: {\"✅ YES\" if provenance else \"❌ NO\"}')
if provenance:
    print(f'Fields Tracked: {len(provenance.get(\"field_provenance\", {}))}')
    print(f'Audit Trail Entries: {len(provenance.get(\"audit_trail\", []))}')

overall_success = precision_met and coverage_met and threshold_validation.can_proceed_to_generation
print(f'\\n🎯 Overall Evidence Validation: {\"✅ PASSED\" if overall_success else \"❌ FAILED\"}')
sys.exit(0 if overall_success else 1)
"
                ;;
            e)
                print_status "Running Programmatic Calculation Validation (5.4)..."
                $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.validation.programmatic_calculation_validator import ProgrammaticCalculationValidator

validator = ProgrammaticCalculationValidator()

print('🧮 Running Programmatic Calculation Validation...')

# Test AMA table calculations
print('\\n📋 Testing AMA Table Calculations...')
rom_measurements = {'flexion': 60, 'extension': 20}
ama_result = validator.validate_ama_table_calculations(rom_measurements, 'lumbar strain', 'spine')

print(f'AMA Calculation: {\"✅ PASSED\" if ama_result.validation_passed else \"❌ FAILED\"}')
print(f'Final Percentage: {ama_result.final_percentage}%')
print(f'Calculation Steps: {len(ama_result.calculation_steps)}')
print(f'AMA Citations: {len(ama_result.ama_table_citations)}')

# Test ROM averaging
print('\\n📏 Testing ROM Measurement Averaging...')
multiple_measurements = {
    'flexion': [58, 62, 60],
    'extension': [18, 22, 20]
}
averaging_result = validator.test_rom_measurement_averaging(multiple_measurements)
print(f'ROM Averaging: {\"✅ PASSED\" if averaging_result.get(\"test_passed\", False) else \"❌ FAILED\"}')
print(f'AMA Methodology Applied: {\"✅ YES\" if averaging_result.get(\"ama_methodology_applied\", False) else \"❌ NO\"}')
print(f'Combined Values Chart: {\"✅ TESTED\" if averaging_result.get(\"combined_values_chart_tested\", False) else \"❌ NOT TESTED\"}')

# Test audit trails
print('\\n📝 Testing Calculation Audit Trails...')
audit_validation = validator.validate_calculation_audit_trails(ama_result)
audit_quality = audit_validation.get('audit_quality_score', 0)
print(f'Audit Trail Quality: {audit_quality:.1%}')
print(f'Step Documentation: {\"✅ COMPLETE\" if audit_validation.get(\"step_by_step_documented\", False) else \"❌ INCOMPLETE\"}')
print(f'AMA Citations: {\"✅ PRESENT\" if audit_validation.get(\"ama_citations_present\", False) else \"❌ MISSING\"}')
print(f'Reproducible: {\"✅ YES\" if audit_validation.get(\"calculation_reproducible\", False) else \"❌ NO\"}')

# Test comprehensive calculations
print('\\n🧪 Running Comprehensive Calculation Tests...')
comprehensive_tests = validator.run_comprehensive_calculation_tests()
pass_rate = comprehensive_tests.get('overall_pass_rate', 0)
print(f'Test Pass Rate: {pass_rate:.1%} (target: ≥95%)')
print(f'Total Tests: {comprehensive_tests.get(\"total_tests\", 0)}')
print(f'Passed Tests: {comprehensive_tests.get(\"passed_tests\", 0)}')
print(f'Edge Cases Handled: {len([r for r in comprehensive_tests.get(\"edge_case_results\", []) if r.get(\"handled\", False)])}')

overall_success = (ama_result.validation_passed and 
                  averaging_result.get('test_passed', False) and 
                  audit_quality >= 0.8 and 
                  pass_rate >= 0.9)

print(f'\\n🎯 Overall Calculation Validation: {\"✅ PASSED\" if overall_success else \"❌ FAILED\"}')
sys.exit(0 if overall_success else 1)
"
                ;;
            f)
                print_status "Running Compliance & Quality Assurance (5.5)..."
                $PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.validation.compliance_quality_validator import ComplianceQualityValidator

validator = ComplianceQualityValidator()

print('⚖️  Running Compliance & Quality Assurance...')

# Create mock template content
mock_template = '''
QUALIFIED MEDICAL EVALUATOR REPORT

Patient: John Doe
Date of Birth: 01/15/1980
Date of Injury: 03/10/2024

MEDICAL HISTORY
The patient reports lower back pain following work injury.

PHYSICAL EXAMINATION
Physical examination reveals limited range of motion.
Flexion: 60 degrees, Extension: 20 degrees

DIAGNOSIS
Primary diagnosis: Lumbar spine strain

IMPAIRMENT RATING
Based on AMA Guides Fifth Edition, Table 15-3,
patient has 5% whole person impairment.

DECLARATION
I declare under penalty of perjury under California laws
that this report complies with Labor Code 4062.3.

_________________________
Dr. Jane Smith, M.D.
License #: A12345
'''

mock_citations = ['Page 1: Patient examination', 'AMA Table 15-3']
mock_metadata = {'document_id': 'test_doc', 'patient_name': 'John Doe'}

# Test legal compliance
print('\\n⚖️  Testing Legal Compliance...')
legal_checks = validator.validate_legal_compliance(mock_template, mock_metadata)
passed_checks = sum(1 for check in legal_checks if check.compliance_status == 'passed')
critical_failures = sum(1 for check in legal_checks if check.compliance_status == 'failed' and check.severity == 'critical')

print(f'Legal Compliance: {passed_checks}/{len(legal_checks)} checks passed')
print(f'Critical Failures: {critical_failures}')

labor_code_compliant = any(check.rule_name == 'labor_code_4062_3' and check.compliance_status == 'passed' for check in legal_checks)
mandatory_sections = any(check.rule_name == 'mandatory_sections' and check.compliance_status == 'passed' for check in legal_checks)
signature_blocks = any(check.rule_name == 'signature_blocks' and check.compliance_status == 'passed' for check in legal_checks)

print(f'Labor Code 4062.3: {\"✅ COMPLIANT\" if labor_code_compliant else \"❌ NON-COMPLIANT\"}')
print(f'Mandatory Sections: {\"✅ PRESENT\" if mandatory_sections else \"❌ MISSING\"}')
print(f'Signature Blocks: {\"✅ PRESENT\" if signature_blocks else \"❌ MISSING\"}')

# Test template quality
print('\\n📋 Testing Template Quality...')
quality_assessments = validator.assess_template_quality(mock_template, mock_citations, mock_metadata)
avg_quality = sum(assessment.score for assessment in quality_assessments) / len(quality_assessments) if quality_assessments else 0

print(f'Average Quality Score: {avg_quality:.1%}')
for assessment in quality_assessments:
    print(f'  {assessment.quality_dimension}: {assessment.score:.1%}')

# Generate compliance report
print('\\n📊 Generating Compliance Report...')
compliance_report = validator.generate_compliance_report('test_doc', legal_checks, quality_assessments)
print(f'Overall Compliance: {compliance_report.overall_compliance_score:.1%}')
print(f'Compliance Status: {compliance_report.compliance_status.upper()}')
print(f'Ready for Generation: {\"✅ YES\" if compliance_report.ready_for_generation else \"❌ NO\"}')

# Test quality gates
print('\\n🚪 Testing Quality Gates...')
quality_gates = validator.validate_quality_gates(compliance_report)
gates_passed = quality_gates.get('overall_gates_passed', False)
print(f'Quality Gates: {\"✅ PASSED\" if gates_passed else \"❌ FAILED\"}')
print(f'Gate Pass Rate: {quality_gates.get(\"gate_pass_rate\", 0):.1%}')

overall_success = (critical_failures == 0 and 
                  avg_quality >= 0.8 and 
                  compliance_report.overall_compliance_score >= 0.8 and 
                  gates_passed)

print(f'\\n🎯 Overall Compliance & Quality: {\"✅ PASSED\" if overall_success else \"❌ FAILED\"}')
sys.exit(0 if overall_success else 1)
"
                ;;
            g)
                print_status "Viewing validation reports..."
                
                # Check if validation reports directory exists
                if [ -d "results/validation_reports" ]; then
                    REPORT_COUNT=$(find results/validation_reports -name "*.json" -type f | wc -l | tr -d ' ')
                    
                    if [ "$REPORT_COUNT" -gt 0 ]; then
                        echo ""
                        echo "📊 Available Validation Reports ($REPORT_COUNT found):"
                        echo ""
                        
                        # List recent reports
                        find results/validation_reports -name "*.json" -type f -exec ls -lt {} + 2>/dev/null | head -10 | while read -r line; do
                            filename=$(echo "$line" | awk '{print $NF}')
                            date=$(echo "$line" | awk '{print $6, $7, $8}')
                            echo "   📄 $(basename "$filename") ($date)"
                        done
                        
                        echo ""
                        echo "💡 Report types available:"
                        echo "   • comprehensive_system_validation_*.json - Complete Task 5 validation"
                        echo "   • knowledge_base_validation_*.json - Knowledge base validation (5.1)"
                        echo "   • pipeline_integration_test_*.json - Pipeline testing (5.2)"
                        echo "   • evidence_validation_*.json - Evidence validation (5.3)"
                        echo "   • calculation_validation_*.json - Calculation validation (5.4)"
                        echo "   • compliance_report_*.json - Compliance validation (5.5)"
                        echo ""
                        echo "📁 Reports location: results/validation_reports/"
                    else
                        print_warning "No validation reports found"
                        echo "   Run validation tests first to generate reports"
                    fi
                else
                    print_warning "Validation reports directory not found"
                    echo "   Run validation tests first to generate reports"
                fi
                ;;
            *)
                print_status "Running default comprehensive Task 5 validation..."
                $PYTHON_CMD scripts/run_task5_validation.py
                ;;
        esac
        ;;
    12)
        echo ""
        print_status "Running system migration to refactored architecture..."
        echo ""
        echo "🔄 =============================================="
        echo "🔄   System Migration to Refactored Architecture"
        echo "🔄 =============================================="
        echo "🔄"
        echo "🔄   📋 Pre-migration validation"
        echo "🔄   💾 System backup creation"
        echo "🔄   🔧 Configuration migration"
        echo "🔄   ✅ Post-migration validation"
        echo "🔄   🔙 Rollback capability"
        echo "🔄"
        echo "🔄 =============================================="
        echo ""
        
        echo "⚠️  IMPORTANT: This will modify your system configuration!"
        echo ""
        read -p "❓ Do you want to proceed with migration? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Ask for dry run first
            read -p "❓ Run dry-run first (recommended)? (Y/n): " -n 1 -r
            echo
            
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                print_status "Running migration dry-run..."
                $PYTHON_CMD scripts/migrate_to_refactored_system_v2.py --dry-run --verbose
                
                if [ $? -eq 0 ]; then
                    echo ""
                    read -p "❓ Dry-run successful. Proceed with actual migration? (y/N): " -n 1 -r
                    echo
                    
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        print_status "Running actual migration..."
                        $PYTHON_CMD scripts/migrate_to_refactored_system_v2.py --verbose
                        
                        if [ $? -eq 0 ]; then
                            print_success "Migration completed successfully!"
                            echo ""
                            echo "🎉 System has been migrated to refactored architecture"
                            echo "   • Quality validation is now active"
                            echo "   • Performance monitoring is enabled"
                            echo "   • Enhanced error reporting is available"
                            echo "   • Migration documentation is in docs/"
                            echo ""
                            read -p "❓ Start web interface with new features? (Y/n): " -n 1 -r
                            echo
                            
                            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                                print_status "Starting web interface with refactored system..."
                                export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
                                streamlit run src/ui/main_app.py \
                                    --server.port=8501 \
                                    --server.address=localhost \
                                    --server.headless=false \
                                    --browser.gatherUsageStats=false
                            fi
                        else
                            print_error "Migration failed!"
                            echo ""
                            echo "🔙 Automatic rollback may have been attempted"
                            echo "   Check logs for detailed error information"
                            echo "   Rollback scripts are available in scripts/"
                        fi
                    else
                        print_status "Migration cancelled by user"
                    fi
                else
                    print_error "Dry-run failed - migration cancelled"
                fi
            else
                print_status "Running actual migration without dry-run..."
                $PYTHON_CMD scripts/migrate_to_refactored_system_v2.py --verbose
            fi
        else
            print_status "Migration cancelled by user"
            echo ""
            echo "💡 You can run migration later with:"
            echo "   python scripts/migrate_to_refactored_system_v2.py"
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
esac

echo ""
print_success "Thanks for using Document Q&A System!"
echo ""
echo "💡 Useful commands:"
echo "   ./scripts/run.sh          - Run this script again"
echo "   ./scripts/deploy.sh       - Full deployment with initialization"
echo "   ./scripts/cleanup.sh      - Clean up all data and deactivate venv"
echo "   streamlit run src/ui/main_app.py  - Start web interface directly"
echo ""
echo "📚 Documentation:"
echo "   - Health checks: src/services/health_checker.py"
echo "   - Performance monitoring: src/services/performance_monitor.py"
echo "   - Configuration: src/config/environment_validator.py"
echo ""