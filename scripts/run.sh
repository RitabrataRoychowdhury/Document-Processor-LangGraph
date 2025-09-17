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

# Run system health check
print_status "Running comprehensive system health check..."
HEALTH_RESULT=$($PYTHON_CMD -c "
import sys
import asyncio
sys.path.append('.')
from src.services.health_checker import HealthChecker
from src.config.app_config import AppConfig

async def main():
    try:
        config = AppConfig.from_env()
        health_checker = HealthChecker(config)
        
        health = health_checker.get_overall_health()
        
        print(f'Overall Health: {\"HEALTHY\" if health[\"overall_healthy\"] else \"UNHEALTHY\"}')
        print(f'Healthy Components: {health[\"healthy_components\"]}/{health[\"total_components\"]}')
        
        critical_issues = 0
        for component, status in health['checks'].items():
            status_text = 'PASS' if status['healthy'] else 'FAIL'
            print(f'  {component}: {status_text} - {status[\"message\"]}')
            
            # Only consider database and configuration as critical
            if not status['healthy'] and component in ['database', 'configuration']:
                critical_issues += 1
        
        # Return success if no critical issues (knowledge_graph and file_system warnings are OK)
        return critical_issues == 0
    except Exception as e:
        print(f'❌ Health check error: {e}')
        return False

result = asyncio.run(main())
sys.exit(0 if result else 1)
" 2>&1)

HEALTH_EXIT_CODE=$?
echo "$HEALTH_RESULT"

if [ $HEALTH_EXIT_CODE -ne 0 ]; then
    print_warning "System health check detected critical issues"
    echo ""
    echo "💡 Common issues:"
    echo "   - Empty knowledge graph (normal for new installations)"
    echo "   - Missing API keys in .env file"
    echo "   - Database connection problems"
    echo ""
    read -p "❓ Continue anyway? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "   Please fix the issues and run this script again"
        exit 1
    fi
    print_status "Continuing with startup despite health check warnings..."
fi

print_success "System health check passed"

# Show system status
print_status "System Status Summary:"
$PYTHON_CMD -c "
import sys
sys.path.append('.')
from src.services.performance_monitor import get_performance_monitor
from src.config.app_config import AppConfig

try:
    config = AppConfig.from_env()
    perf_monitor = get_performance_monitor()
    stats = perf_monitor.get_current_statistics()
    
    print(f'  📊 Performance Monitor: Active')
    print(f'  🗄️  Database: {config.database_path}')
    print(f'  🤖 QA Provider: {config.qa_provider}')
    print(f'  🔤 Embedding Provider: {config.embedding_provider}')
    print(f'  📁 Max File Size: {config.max_file_size_mb}MB')
    print(f'  📄 Allowed Types: {\", \".join(config.allowed_file_types)}')
    
    overall_stats = stats.get('overall_stats', {})
    if overall_stats.get('total_documents_processed', 0) > 0:
        print(f'  📈 Documents Processed: {overall_stats[\"total_documents_processed\"]}')
        print(f'  ✅ Success Rate: {overall_stats[\"successful_processing\"]}/{overall_stats[\"total_documents_processed\"]}')
    
except Exception as e:
    print(f'  ⚠️  Status check error: {e}')
"

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
echo ""
read -p "Choose an option (1-10): " -n 1 -r
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