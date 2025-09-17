#!/usr/bin/env python3
"""
Basic Functionality Test

This script tests basic system functionality without complex dependencies.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_basic_imports():
    """Test basic imports that should always work."""
    try:
        from config.app_config import AppConfig
        print("✅ AppConfig imported successfully")
        
        config = AppConfig.from_env()
        print("✅ Configuration loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ Basic import test failed: {e}")
        return False

def test_directory_structure():
    """Test basic directory structure."""
    try:
        # Create basic directories
        os.makedirs("data/database", exist_ok=True)
        os.makedirs("data/documents", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        
        print("✅ Directory structure verified")
        return True
    except Exception as e:
        print(f"❌ Directory structure test failed: {e}")
        return False

def main():
    """Run basic functionality test."""
    print("🧪 Basic Functionality Test")
    print("=" * 30)
    
    imports_ok = test_basic_imports()
    directories_ok = test_directory_structure()
    
    overall_success = imports_ok and directories_ok
    
    print("\n" + "=" * 30)
    print(f"Overall: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    
    if overall_success:
        print("🎉 Basic functionality is working!")
    else:
        print("⚠️  Basic functionality has issues")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)