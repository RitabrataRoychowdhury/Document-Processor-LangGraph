#!/usr/bin/env python3
"""
Test Streamlit Application Startup

This script tests that the Streamlit application can start successfully
with the centralized configuration management system.
"""

import sys
import os
import subprocess
import time
import signal
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_streamlit_import():
    """Test that the main Streamlit app can be imported without errors."""
    print("=" * 60)
    print("TESTING STREAMLIT APPLICATION IMPORT")
    print("=" * 60)
    
    try:
        # Test importing the main app module
        print("📱 Testing main_app import...")
        
        # Import key components that main_app uses
        from src.config.app_config import app_config
        print("  ✅ app_config imported successfully")
        
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        print("  ✅ centralized config_manager imported successfully")
        
        # Test that configuration is accessible
        api_configured = app_config.is_api_configured()
        print(f"  ✅ API configuration accessible: {'Yes' if api_configured else 'No'}")
        
        # Test validation
        validation_result = config_manager.validate_configuration()
        print(f"  ✅ Configuration validation: {'Valid' if validation_result.is_valid else 'Invalid'}")
        
        # Test that we can access UI configuration
        ui_config = config_manager.get_ui_config()
        print(f"  ✅ UI configuration accessible: Port {ui_config.get('port', 'Unknown')}")
        
        print("\n✅ All imports successful - Streamlit app should start correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_for_streamlit():
    """Test configuration specifically for Streamlit requirements."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION FOR STREAMLIT REQUIREMENTS")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        from src.config.app_config import app_config
        
        # Test required configurations for Streamlit
        print("📋 Checking Streamlit requirements:")
        
        # Check port configuration
        port = config_manager.get('streamlit_port', 8501)
        print(f"  • Streamlit Port: {port}")
        
        # Check file upload configuration
        max_file_size = config_manager.get('max_file_size_mb', 10)
        allowed_types = config_manager.get('allowed_file_types', [])
        print(f"  • Max File Size: {max_file_size} MB")
        print(f"  • Allowed File Types: {allowed_types}")
        
        # Check API configuration
        gemini_configured = config_manager.is_api_configured('gemini')
        openrouter_configured = config_manager.is_api_configured('openrouter')
        print(f"  • Gemini API: {'✅ Configured' if gemini_configured else '❌ Not configured'}")
        print(f"  • OpenRouter API: {'✅ Configured' if openrouter_configured else '❌ Not configured'}")
        
        # Check database configuration
        db_config = config_manager.get_database_config()
        db_path = Path(db_config.get('path', ''))
        print(f"  • Database Path: {db_path}")
        print(f"  • Database Directory Exists: {'✅ Yes' if db_path.parent.exists() else '❌ No'}")
        
        # Create database directory if it doesn't exist
        if not db_path.parent.exists():
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"  • Created database directory: {db_path.parent}")
            except Exception as e:
                print(f"  • Failed to create database directory: {e}")
                return False
        
        # Check that at least one API is configured
        if not (gemini_configured or openrouter_configured):
            print("  ❌ No API providers configured - Streamlit app will have limited functionality")
            return False
        
        print("\n✅ All Streamlit requirements satisfied")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration check error: {e}")
        return False


def test_streamlit_dry_run():
    """Test Streamlit app startup in dry-run mode."""
    print("\n" + "=" * 60)
    print("TESTING STREAMLIT DRY RUN")
    print("=" * 60)
    
    try:
        # Test that we can run streamlit --help without errors
        print("📱 Testing Streamlit availability...")
        
        result = subprocess.run(
            ['streamlit', '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ Streamlit is available and working")
        else:
            print("  ❌ Streamlit is not available or not working")
            print(f"  Error: {result.stderr}")
            return False
        
        # Test that our main app file exists and is readable
        main_app_path = Path("src/ui/main_app.py")
        if main_app_path.exists():
            print(f"  ✅ Main app file exists: {main_app_path}")
        else:
            print(f"  ❌ Main app file not found: {main_app_path}")
            return False
        
        # Test syntax check on main app
        print("📋 Testing main app syntax...")
        
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(main_app_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✅ Main app syntax is valid")
        else:
            print("  ❌ Main app has syntax errors")
            print(f"  Error: {result.stderr}")
            return False
        
        print("\n✅ Streamlit dry run successful")
        return True
        
    except subprocess.TimeoutExpired:
        print("  ❌ Streamlit test timed out")
        return False
    except FileNotFoundError:
        print("  ❌ Streamlit not found - please install streamlit")
        return False
    except Exception as e:
        print(f"  ❌ Streamlit dry run error: {e}")
        return False


def test_environment_setup():
    """Test that the environment is properly set up for Streamlit."""
    print("\n" + "=" * 60)
    print("TESTING ENVIRONMENT SETUP")
    print("=" * 60)
    
    try:
        # Check Python version
        python_version = sys.version_info
        print(f"📋 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("  ⚠️ Python 3.8+ recommended for Streamlit")
        else:
            print("  ✅ Python version is compatible")
        
        # Check required packages
        required_packages = [
            'streamlit',
            'dotenv',
            'pathlib',
            'dataclasses'
        ]
        
        print("\n📦 Checking required packages:")
        
        for package in required_packages:
            try:
                if package == 'dotenv':
                    import dotenv
                elif package == 'pathlib':
                    import pathlib
                elif package == 'dataclasses':
                    import dataclasses
                elif package == 'streamlit':
                    import streamlit
                
                print(f"  ✅ {package}: Available")
                
            except ImportError:
                print(f"  ❌ {package}: Not available")
                if package == 'streamlit':
                    print("    Install with: pip install streamlit")
                elif package == 'dotenv':
                    print("    Install with: pip install python-dotenv")
                return False
        
        # Check working directory
        cwd = Path.cwd()
        print(f"\n📁 Working Directory: {cwd}")
        
        # Check that src directory exists
        src_dir = cwd / "src"
        if src_dir.exists():
            print(f"  ✅ Source directory exists: {src_dir}")
        else:
            print(f"  ❌ Source directory not found: {src_dir}")
            return False
        
        # Check that .env file exists
        env_file = cwd / ".env"
        if env_file.exists():
            print(f"  ✅ Environment file exists: {env_file}")
        else:
            print(f"  ⚠️ Environment file not found: {env_file}")
            print("    This may limit functionality")
        
        print("\n✅ Environment setup is ready for Streamlit")
        return True
        
    except Exception as e:
        print(f"\n❌ Environment setup error: {e}")
        return False


def main():
    """Run all Streamlit startup tests."""
    print("🧪 STREAMLIT APPLICATION STARTUP TESTS")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Streamlit Import", test_streamlit_import()))
    test_results.append(("Configuration for Streamlit", test_configuration_for_streamlit()))
    test_results.append(("Streamlit Dry Run", test_streamlit_dry_run()))
    test_results.append(("Environment Setup", test_environment_setup()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Streamlit application is ready to start!")
        print("\n💡 You can now run: streamlit run src/ui/main_app.py")
        return True
    else:
        print("⚠️ Some startup tests failed. Please address the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)