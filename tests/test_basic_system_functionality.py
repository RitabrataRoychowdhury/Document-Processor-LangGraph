#!/usr/bin/env python3
"""
Basic System Functionality Test

This script tests the core functionality of the QME system without
the full startup process that might have database schema issues.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test that all critical imports work."""
    print("🔍 Testing basic imports...")
    
    try:
        # Test core imports
        from src.config.app_config import app_config
        print("✅ Configuration loaded")
        
        # Test service imports
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
        print("✅ Services imported")
        
        # Test infrastructure imports
        from src.infrastructure.api.api_provider_factory import APIProviderFactory
        from src.infrastructure.configuration.service_registry import ServiceRegistry
        print("✅ Infrastructure imported")
        
        # Test UI imports (without running Streamlit)
        from src.ui.upload_interface import UploadInterface
        print("✅ UI components imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_service_instantiation():
    """Test that services can be instantiated."""
    print("\n🔧 Testing service instantiation...")
    
    try:
        # Test API provider factory
        from src.infrastructure.api.api_provider_factory import APIProviderFactory
        factory = APIProviderFactory()
        print("✅ API Provider Factory created")
        
        # Test service registry
        from src.infrastructure.configuration.service_registry import ServiceRegistry
        registry = ServiceRegistry()
        print("✅ Service Registry created")
        
        # Test QME field service
        from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
        qme_service = ComprehensiveQMEFieldService()
        print("✅ QME Field Service created")
        
        # Test template assembler
        from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
        template_service = ProfessionalTemplateAssembler()
        print("✅ Template Assembler created")
        
        return True
        
    except Exception as e:
        print(f"❌ Service instantiation test failed: {e}")
        return False

def test_configuration():
    """Test configuration access."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from src.config.app_config import app_config
        
        # Test basic config access
        db_path = app_config.database_path
        max_size = app_config.max_file_size_mb
        file_types = app_config.allowed_file_types
        
        print(f"✅ Database path: {db_path}")
        print(f"✅ Max file size: {max_size}MB")
        print(f"✅ Allowed file types: {len(file_types)} types")
        
        # Test API key configuration (without revealing keys)
        gemini_configured = bool(app_config.gemini_api_key)
        openai_configured = bool(app_config.openai_api_key)
        
        print(f"✅ Gemini API: {'configured' if gemini_configured else 'not configured'}")
        print(f"✅ OpenAI API: {'configured' if openai_configured else 'not configured'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_database_basic():
    """Test basic database functionality."""
    print("\n🗄️ Testing basic database functionality...")
    
    try:
        from src.storage.database import DatabaseManager
        
        # Create database manager
        db_manager = DatabaseManager()
        print("✅ Database manager created")
        
        # Test connection
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ Database connection successful, found {len(tables)} tables")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_error_handling():
    """Test error handling functionality."""
    print("\n🛡️ Testing error handling...")
    
    try:
        from src.utils.error_handling import DocumentQAError, ErrorType, format_error_for_ui
        from src.infrastructure.monitoring.ui_error_handler import ui_error_handler
        
        # Test custom error creation
        test_error = DocumentQAError(
            message="Test error",
            error_type=ErrorType.SYSTEM_ERROR,
            details={"test": True}
        )
        
        # Test error formatting
        formatted = format_error_for_ui(test_error)
        print("✅ Error handling system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all basic functionality tests."""
    print("🚀 Starting Basic System Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_basic_imports),
        ("Service Instantiation", test_service_instantiation),
        ("Configuration Test", test_configuration),
        ("Database Basic Test", test_database_basic),
        ("Error Handling Test", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("📊 BASIC FUNCTIONALITY TEST SUMMARY")
    print("=" * 60)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("🎉 Basic system functionality is working correctly!")
        return True
    else:
        print(f"❌ Some tests failed ({passed}/{total})")
        print("⚠️ Basic system functionality has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)