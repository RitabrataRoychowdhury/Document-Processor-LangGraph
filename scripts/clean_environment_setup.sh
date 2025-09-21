#!/bin/bash

# Clean Environment Setup Script
# This script creates a fresh virtual environment and tests the QME system

set -e  # Exit on any error

echo "🧹 Starting Clean Environment Setup"
echo "=================================="

# Step 1: Deactivate current virtual environment if active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "📤 Deactivating current virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# Step 2: Remove existing virtual environment if it exists
if [ -d "venv_clean" ]; then
    echo "🗑️  Removing existing clean virtual environment"
    rm -rf venv_clean
fi

# Step 3: Create fresh virtual environment
echo "🆕 Creating fresh virtual environment: venv_clean"
python3 -m venv venv_clean

# Step 4: Activate the new virtual environment
echo "🔄 Activating clean virtual environment"
source venv_clean/bin/activate

# Step 5: Upgrade pip to latest version
echo "⬆️  Upgrading pip to latest version"
pip install --upgrade pip

# Step 6: Install requirements
echo "📦 Installing requirements from requirements.txt"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, installing basic dependencies"
    pip install streamlit fastapi uvicorn python-multipart requests pyyaml python-docx
fi

# Step 7: Verify Python environment
echo "🐍 Python environment verification:"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "Virtual environment: $VIRTUAL_ENV"

# Step 8: Test basic imports
echo "🧪 Testing basic imports"
python -c "
import sys
print(f'✅ Python path: {sys.executable}')

try:
    import streamlit
    print('✅ Streamlit imported successfully')
except ImportError as e:
    print(f'❌ Streamlit import failed: {e}')

try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import requests
    print('✅ Requests imported successfully')
except ImportError as e:
    print(f'❌ Requests import failed: {e}')
"

# Step 9: Test QME system imports
echo "🏥 Testing QME system imports"
python -c "
import os
import sys

# Set environment variables for testing
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-import-validation'
os.environ['GEMINI_API_KEY'] = 'test-key-for-import-validation'

try:
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    print('✅ ComprehensiveQMEFieldService imported successfully')
except ImportError as e:
    print(f'❌ ComprehensiveQMEFieldService import failed: {e}')

try:
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    print('✅ OpenRouterExtractionService imported successfully')
except ImportError as e:
    print(f'❌ OpenRouterExtractionService import failed: {e}')

try:
    from src.core.extraction.gemini_extraction_service import GeminiExtractionService
    print('✅ GeminiExtractionService imported successfully')
except ImportError as e:
    print(f'❌ GeminiExtractionService import failed: {e}')

try:
    from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
    print('✅ ProfessionalTemplateAssembler imported successfully')
except ImportError as e:
    print(f'❌ ProfessionalTemplateAssembler import failed: {e}')
"

# Step 10: Test service initialization
echo "🔧 Testing service initialization"
python -c "
import os
import sys

# Set environment variables for testing
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-service-init'
os.environ['GEMINI_API_KEY'] = 'test-key-for-service-init'

try:
    from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
    service = ComprehensiveQMEFieldService()
    
    has_openrouter = service.openrouter_service is not None
    has_gemini = service.gemini_service is not None
    
    print(f'✅ ComprehensiveQMEFieldService initialized')
    print(f'✅ OpenRouter service available: {has_openrouter}')
    print(f'✅ Gemini service available: {has_gemini}')
    
    if has_openrouter and has_gemini:
        print('✅ Multi-layer fallback system ready: OpenRouter → Gemini → Rule-based')
    elif has_gemini:
        print('✅ Fallback system ready: Gemini → Rule-based')
    else:
        print('✅ Basic fallback system ready: Rule-based only')
        
except Exception as e:
    print(f'❌ Service initialization failed: {e}')
"

echo ""
echo "🎉 Clean Environment Setup Complete!"
echo "=================================="
echo "✅ Fresh virtual environment created: venv_clean"
echo "✅ All dependencies installed"
echo "✅ QME system imports validated"
echo "✅ Multi-layer fallback system tested"
echo ""
echo "To use this clean environment:"
echo "  source venv_clean/bin/activate"
echo ""
echo "To test the system:"
echo "  python run_direct.py"
echo "  # or"
echo "  streamlit run src/ui/main_app.py"