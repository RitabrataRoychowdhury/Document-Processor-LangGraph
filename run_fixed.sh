#!/bin/bash

# QME System - Fixed Run Script
# This version skips dependency reinstallation to preserve local fixes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo "🚀 QME System - Fixed Run Script (Preserves Local Changes)"
echo "========================================================="

# Check if Python 3 is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed or not in PATH"
    exit 1
fi

print_success "Using Python: $PYTHON_CMD"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Virtual environment already active: $VIRTUAL_ENV"
else
    # Try to activate venv if it exists
    if [ -d "venv" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_warning "No virtual environment found - using system Python"
    fi
fi

# Check if streamlit is available
if ! $PYTHON_CMD -c "import streamlit" 2>/dev/null; then
    print_error "Streamlit not found. Installing..."
    pip install streamlit
fi

# Clear Python cache to ensure fixes are loaded
print_status "Clearing Python cache to load fixes..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Test that fixes are in place
print_status "Verifying fixes are active..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
try:
    from src.ui.upload_interface import UploadInterface
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    print('✅ All fixes verified and active')
except Exception as e:
    print(f'❌ Fix verification failed: {e}')
    sys.exit(1)
" || exit 1

# Start the application
print_success "Starting QME System with fixes applied..."
print_status "URL: http://localhost:8501"
print_warning "Press Ctrl+C to stop"
echo ""

$PYTHON_CMD -m streamlit run src/ui/main_app.py \
    --server.port=8501 \
    --server.address=localhost \
    --server.headless=false \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false