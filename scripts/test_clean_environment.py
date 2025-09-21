#!/usr/bin/env python3
"""
Test script to validate the clean environment and multi-layer fallback system.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test that the environment is properly set up."""
    print("🧪 Testing Clean Environment Setup")
    print("=================================")
    
    # Test Python version
    python_version = sys.version
    print(f"✅ Python version: {python_version}")
    
    # Test virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path and 'venv_clean' in venv_path:
        print(f"✅ Clean virtual environment active: {venv_path}")
    else:
        print(f"⚠️  Virtual environment: {venv_path}")
    
    return True

def test_basic_imports():
    """Test basic package imports."""
    print("\n🔧 Testing Basic Package Imports")
    print("================================")
    
    packages = [
        'streamlit',
        'fastapi',
        'requests',
        'openai',
        'docx',  # python-docx imports as 'docx'
        'PyPDF2',
        'numpy',
        'pandas'
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            return False
    
    return True

def test_qme_system_imports():
    """Test QME system specific imports."""
    print("\n🏥 Testing QME System Imports")
    print("=============================")
    
    # Set test environment variables
    os.environ['OPENROUTER_API_KEY'] = 'test-key-for-import-validation'
    os.environ['GEMINI_API_KEY'] = 'test-key-for-import-validation'
    
    try:
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        print("✅ ComprehensiveQMEFieldService imported successfully")
    except ImportError as e:
        print(f"❌ ComprehensiveQMEFieldService import failed: {e}")
        return False
    
    try:
        from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
        print("✅ OpenRouterExtractionService imported successfully")
    except ImportError as e:
        print(f"❌ OpenRouterExtractionService import failed: {e}")
        return False
    
    try:
        from src.core.extraction.gemini_extraction_service import GeminiExtractionService
        print("✅ GeminiExtractionService imported successfully")
    except ImportError as e:
        print(f"❌ GeminiExtractionService import failed: {e}")
        return False
    
    try:
        from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
        print("✅ ProfessionalTemplateAssembler imported successfully")
    except ImportError as e:
        print(f"❌ ProfessionalTemplateAssembler import failed: {e}")
        return False
    
    return True

def test_service_initialization():
    """Test service initialization and multi-layer fallback system."""
    print("\n🔧 Testing Service Initialization")
    print("=================================")
    
    # Set test environment variables
    os.environ['OPENROUTER_API_KEY'] = 'test-key-for-service-init'
    os.environ['GEMINI_API_KEY'] = 'test-key-for-service-init'
    
    try:
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        
        # Initialize the service
        service = ComprehensiveQMEFieldService()
        
        # Check service availability
        has_openrouter = service.openrouter_service is not None
        has_gemini = service.gemini_service is not None
        has_rule_based = service.field_extraction_service is not None
        
        print(f"✅ ComprehensiveQMEFieldService initialized")
        print(f"✅ OpenRouter service available: {has_openrouter}")
        print(f"✅ Gemini service available: {has_gemini}")
        print(f"✅ Rule-based service available: {has_rule_based}")
        
        # Test fallback system
        if has_openrouter and has_gemini and has_rule_based:
            print("✅ Multi-layer fallback system ready: OpenRouter → Gemini → Rule-based")
            return True
        elif has_gemini and has_rule_based:
            print("✅ Fallback system ready: Gemini → Rule-based")
            return True
        elif has_rule_based:
            print("✅ Basic fallback system ready: Rule-based only")
            return True
        else:
            print("❌ No extraction services available")
            return False
            
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

def test_ui_imports():
    """Test UI component imports."""
    print("\n🖥️  Testing UI Component Imports")
    print("===============================")
    
    ui_components = [
        'src.ui.main_app',
        'src.ui.upload_interface',
        'src.ui.qa_interface_simple',
        'src.ui.qme_template_interface',
        'src.ui.document_manager'
    ]
    
    for component in ui_components:
        try:
            __import__(component)
            print(f"✅ {component} imported successfully")
        except ImportError as e:
            print(f"❌ {component} import failed: {e}")
            return False
    
    return True

def test_configuration_loading():
    """Test configuration loading."""
    print("\n⚙️  Testing Configuration Loading")
    print("===============================")
    
    try:
        from src.config.app_config import AppConfig
        config = AppConfig.from_env()
        print("✅ AppConfig loaded successfully")
        
        # Test API configuration
        if hasattr(config, 'openrouter_api_key') or hasattr(config, 'gemini_api_key'):
            print("✅ API configuration accessible")
        else:
            print("⚠️  API configuration may not be fully loaded")
        
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Clean Environment Validation")
    print("===============================")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Basic Imports", test_basic_imports),
        ("QME System Imports", test_qme_system_imports),
        ("Service Initialization", test_service_initialization),
        ("UI Component Imports", test_ui_imports),
        ("Configuration Loading", test_configuration_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print(f"\n🎉 Clean Environment Validation Complete!")
    print("=========================================")
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✨ All tests passed! Clean environment is ready for QME system operation.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())