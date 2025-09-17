#!/usr/bin/env python3
"""
Test Configuration Access from UI Components

This script tests that UI components can properly access configuration
including API keys, database settings, and other critical configuration.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_centralized_config_manager():
    """Test centralized configuration manager access."""
    print("=" * 60)
    print("TESTING CENTRALIZED CONFIGURATION MANAGER")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        print("✅ Successfully imported centralized configuration manager")
        
        # Test basic configuration access
        print("\n📋 Testing basic configuration access:")
        
        # Test API keys
        gemini_key = config_manager.get_api_key('gemini')
        openrouter_key = config_manager.get_api_key('openrouter')
        
        print(f"  • Gemini API Key: {'✅ Configured' if gemini_key else '❌ Not configured'}")
        print(f"  • OpenRouter API Key: {'✅ Configured' if openrouter_key else '❌ Not configured'}")
        
        # Test database configuration
        db_config = config_manager.get_database_config()
        print(f"  • Database Path: {db_config.get('path', 'Not set')}")
        print(f"  • Database URL: {db_config.get('url', 'Not set')}")
        
        # Test processing configuration
        proc_config = config_manager.get_processing_config()
        print(f"  • Max File Size: {proc_config.get('max_file_size_mb', 'Not set')} MB")
        print(f"  • Max Jobs: {proc_config.get('max_jobs', 'Not set')}")
        print(f"  • Timeout: {proc_config.get('timeout_seconds', 'Not set')} seconds")
        
        # Test UI configuration
        ui_config = config_manager.get_ui_config()
        print(f"  • Streamlit Port: {ui_config.get('port', 'Not set')}")
        print(f"  • Debug Mode: {ui_config.get('debug_mode', 'Not set')}")
        
        # Test validation
        print("\n🔍 Testing configuration validation:")
        validation_result = config_manager.validate_configuration()
        
        if validation_result.is_valid:
            print("  ✅ Configuration is valid")
        else:
            print("  ❌ Configuration has errors:")
            for error in validation_result.errors:
                print(f"    • {error}")
        
        if validation_result.warnings:
            print("  ⚠️ Configuration warnings:")
            for warning in validation_result.warnings:
                print(f"    • {warning}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import centralized configuration manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing centralized configuration manager: {e}")
        return False


def test_app_config_integration():
    """Test app_config integration with centralized manager."""
    print("\n" + "=" * 60)
    print("TESTING APP_CONFIG INTEGRATION")
    print("=" * 60)
    
    try:
        from src.config.app_config import app_config
        print("✅ Successfully imported app_config")
        
        # Test configuration access
        print("\n📋 Testing app_config access:")
        
        # Test API keys
        gemini_key = app_config.get_api_key_for_provider('gemini')
        openrouter_key = app_config.get_api_key_for_provider('openrouter')
        
        print(f"  • Gemini API Key: {'✅ Configured' if gemini_key else '❌ Not configured'}")
        print(f"  • OpenRouter API Key: {'✅ Configured' if openrouter_key else '❌ Not configured'}")
        
        # Test basic properties
        print(f"  • Database Path: {app_config.database_path}")
        print(f"  • Max File Size: {app_config.max_file_size_mb} MB")
        print(f"  • Allowed File Types: {app_config.allowed_file_types}")
        print(f"  • QA Provider: {app_config.qa_provider}")
        print(f"  • Embedding Provider: {app_config.embedding_provider}")
        
        # Test validation
        print("\n🔍 Testing app_config validation:")
        validation_errors = app_config.validate()
        
        if not validation_errors:
            print("  ✅ App configuration is valid")
        else:
            print("  ❌ App configuration has errors:")
            for error in validation_errors:
                print(f"    • {error}")
        
        # Test status info
        print("\n📊 Testing status info:")
        status_info = app_config.get_status_info()
        
        for key, value in status_info.items():
            if key.endswith('_configured'):
                status = "✅ Yes" if value else "❌ No"
                print(f"  • {key.replace('_', ' ').title()}: {status}")
            else:
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import app_config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing app_config: {e}")
        return False


def test_ui_component_config_access():
    """Test configuration access from UI components."""
    print("\n" + "=" * 60)
    print("TESTING UI COMPONENT CONFIGURATION ACCESS")
    print("=" * 60)
    
    success = True
    
    # Test main_app configuration access
    print("\n📱 Testing main_app configuration access:")
    try:
        # Test that app_config is accessible
        from src.config.app_config import app_config
        print(f"  ✅ app_config accessible: {type(app_config).__name__}")
        
        # Test centralized config manager access
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        print(f"  ✅ centralized config_manager accessible: {type(config_manager).__name__}")
        
    except Exception as e:
        print(f"  ❌ Error accessing configuration from main_app: {e}")
        success = False
    
    # Test qa_interface configuration access
    print("\n💬 Testing qa_interface configuration access:")
    try:
        # Test configuration access without importing the full UI
        from src.config.app_config import app_config
        api_key = app_config.get_api_key_for_provider(app_config.qa_provider)
        print(f"  ✅ API key accessible: {'Yes' if api_key else 'No'}")
        
        # Test centralized config access
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        api_config = config_manager.get_api_config(app_config.qa_provider)
        print(f"  ✅ API config accessible: {bool(api_config.get('api_key'))}")
        
    except Exception as e:
        print(f"  ❌ Error accessing configuration from qa_interface: {e}")
        success = False
    
    # Test qme_template_interface configuration access
    print("\n🏥 Testing qme_template_interface configuration access:")
    try:
        # Test configuration access without importing the full UI
        from src.config.app_config import app_config
        print(f"  ✅ Configuration accessible: {app_config.qa_provider}")
        
        # Test processing config access
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        proc_config = config_manager.get_processing_config()
        print(f"  ✅ Processing config accessible: {proc_config.get('max_file_size_mb')} MB")
        
    except Exception as e:
        print(f"  ❌ Error accessing configuration from qme_template_interface: {e}")
        success = False
    
    return success


def test_environment_variable_loading():
    """Test environment variable loading."""
    print("\n" + "=" * 60)
    print("TESTING ENVIRONMENT VARIABLE LOADING")
    print("=" * 60)
    
    success = True
    
    # Check .env file existence
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent / ".env"
    ]
    
    env_file_found = False
    for env_path in env_paths:
        if env_path.exists():
            print(f"✅ Found .env file at: {env_path}")
            env_file_found = True
            break
    
    if not env_file_found:
        print("⚠️ No .env file found in expected locations")
        # Don't fail the test for this, as env vars might be set directly
    
    # Check dotenv availability
    try:
        import dotenv
        print("✅ python-dotenv package is available")
    except ImportError:
        print("⚠️ python-dotenv package not available")
        # Don't fail the test for this
    
    # Check critical environment variables
    print("\n🔍 Checking critical environment variables:")
    
    critical_vars = [
        'GEMINI_API_KEY',
        'OPENROUTER_API_KEY',
        'DATABASE_PATH',
        'MAX_FILE_SIZE_MB',
        'STREAMLIT_PORT'
    ]
    
    missing_critical = 0
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'API_KEY' in var:
                display_value = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
            if var in ['GEMINI_API_KEY', 'OPENROUTER_API_KEY']:
                # At least one API key should be set
                missing_critical += 1
    
    # Check if at least one API key is configured
    gemini_key = os.getenv('GEMINI_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not gemini_key and not openrouter_key:
        print("  ❌ No API keys configured - at least one is required")
        success = False
    else:
        print("  ✅ At least one API key is configured")
    
    return success


def test_configuration_validation():
    """Test comprehensive configuration validation."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION VALIDATION")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.config_validator import config_validator
        print("✅ Successfully imported configuration validator")
        
        # Get validation report
        print("\n📋 Configuration Validation Report:")
        print("-" * 40)
        
        validation_report = config_validator.get_validation_report()
        print(validation_report)
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import configuration validator: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running configuration validation: {e}")
        return False


def test_streamlit_environment():
    """Test configuration access in Streamlit environment simulation."""
    print("\n" + "=" * 60)
    print("TESTING STREAMLIT ENVIRONMENT SIMULATION")
    print("=" * 60)
    
    try:
        # Simulate Streamlit session state
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def get(self, key, default=None):
                return self.data.get(key, default)
            
            def __setitem__(self, key, value):
                self.data[key] = value
            
            def __getitem__(self, key):
                return self.data[key]
        
        # Mock streamlit
        class MockStreamlit:
            def __init__(self):
                self.session_state = MockSessionState()
        
        # Test configuration access in mock Streamlit environment
        mock_st = MockStreamlit()
        
        # Test app_config access
        from src.config.app_config import app_config
        
        # Simulate storing config in session state
        mock_st.session_state['app_config'] = app_config
        
        # Test retrieval
        retrieved_config = mock_st.session_state.get('app_config')
        
        if retrieved_config:
            print("✅ Configuration successfully stored and retrieved from session state")
            print(f"  • QA Provider: {retrieved_config.qa_provider}")
            print(f"  • API Configured: {retrieved_config.is_api_configured()}")
            print(f"  • Max File Size: {retrieved_config.max_file_size_mb} MB")
        else:
            print("❌ Failed to store/retrieve configuration from session state")
        
        # Test centralized config manager access
        try:
            from src.infrastructure.configuration.centralized_config_manager import config_manager
            
            # Test validation in mock environment
            validation_result = config_manager.validate_configuration()
            print(f"✅ Validation accessible: {'Valid' if validation_result.is_valid else 'Invalid'}")
            
        except ImportError:
            print("⚠️ Centralized config manager not available in mock environment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Streamlit environment: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("🧪 QME SYSTEM CONFIGURATION ACCESS TESTS")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Centralized Config Manager", test_centralized_config_manager()))
    test_results.append(("App Config Integration", test_app_config_integration()))
    test_results.append(("UI Component Config Access", test_ui_component_config_access()))
    test_results.append(("Environment Variable Loading", test_environment_variable_loading()))
    test_results.append(("Configuration Validation", test_configuration_validation()))
    test_results.append(("Streamlit Environment", test_streamlit_environment()))
    
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
        print("🎉 All configuration tests passed!")
        return True
    else:
        print("⚠️ Some configuration tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)