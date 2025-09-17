#!/usr/bin/env python3
"""
Test script for QME Template Interface functionality.
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_qme_interface_import():
    """Test that QME interface can be imported successfully."""
    try:
        from src.ui.qme_template_interface import QMETemplateInterface, render_qme_template_page
        print("✅ QME Template Interface imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import QME Template Interface: {e}")
        return False

def test_qa_interface_enhancements():
    """Test that QA interface enhancements can be imported."""
    try:
        from src.ui.qa_interface import QAInterface, render_qa_page
        print("✅ Enhanced QA Interface imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import enhanced QA Interface: {e}")
        return False

def test_qme_template_generator():
    """Test QME template generator functionality."""
    try:
        from src.core.generation.qme_template_generator import QMETemplateGenerator
        generator = QMETemplateGenerator()
        print("✅ QME Template Generator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize QME Template Generator: {e}")
        return False

def test_document_processing():
    """Test document processing functionality."""
    try:
        from src.infrastructure.storage.file_handler import FileUploadHandler
        handler = FileUploadHandler()
        print("✅ File Upload Handler initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize File Upload Handler: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing QME Template Interface Implementation")
    print("=" * 50)
    
    tests = [
        test_qme_interface_import,
        test_qa_interface_enhancements,
        test_qme_template_generator,
        test_document_processing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! QME Template Interface is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())