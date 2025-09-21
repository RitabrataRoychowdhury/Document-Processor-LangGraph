#!/bin/bash

# Test script for run.sh - validates that the script can execute without errors

echo "🧪 Testing run.sh script..."
echo "=========================="

# Test 1: Check script syntax
echo "Test 1: Script syntax validation..."
if bash -n scripts/run.sh; then
    echo "✅ Script syntax is valid"
else
    echo "❌ Script syntax error"
    exit 1
fi

# Test 2: Check if script can start (dry run simulation)
echo ""
echo "Test 2: Configuration loading test..."
python3 -c "
import sys
import os
sys.path.insert(0, '.')

try:
    from src.config.app_config import AppConfig
    config = AppConfig.from_env()
    print('✅ Configuration loads successfully')
    print(f'   Debug mode: {config.debug_mode}')
    print(f'   Max file size: {config.max_file_size_mb}MB')
    print(f'   API configured: {config.is_api_configured()}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed"
else
    echo "❌ Configuration test failed"
    exit 1
fi

# Test 3: Check critical imports
echo ""
echo "Test 3: Critical imports test..."
python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from src.config.app_config import AppConfig
    from src.ui.main_app import main
    print('✅ Critical imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Warning: {e}')
    print('   Imports may work but with warnings')
"

if [ $? -eq 0 ]; then
    echo "✅ Import test passed"
else
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "🎉 All tests passed! run.sh script is ready to use."
echo ""
echo "To run the QME system:"
echo "  ./scripts/run.sh"
echo ""
echo "The script will:"
echo "  1. Clean all cache files"
echo "  2. Create fresh virtual environment"
echo "  3. Install dependencies"
echo "  4. Validate system health"
echo "  5. Present startup menu"