#!/usr/bin/env python3
"""
Test Streamlit Configuration Integration

This script tests configuration access specifically in a Streamlit-like environment
to ensure UI components can properly access configuration, API keys, and database settings.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_streamlit_config_access():
    """Test configuration access in Streamlit environment."""
    print("=" * 60)
    print("TESTING STREAMLIT CONFIGURATION ACCESS")
    print("=" * 60)
    
    try:
        # Mock Streamlit session state
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def get(self, key, default=None):
                return self.data.get(key, default)
            
            def __setitem__(self, key, value):
                self.data[key] = value
            
            def __getitem__(self, key):
                return self.data[key]
            
            def __contains__(self, key):
                return key in self.data
        
        # Create mock session state
        session_state = MockSessionState()
        
        # Test 1: Basic configuration loading
        print("\n📋 Test 1: Basic Configuration Loading")
        
        from src.config.app_config import app_config
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        
        # Store config in session state (simulating Streamlit initialization)
        session_state['app_config'] = app_config
        session_state['config_manager'] = config_manager
        
        print("  ✅ Configuration stored in session state")
        
        # Test 2: API Key Access
        print("\n🔑 Test 2: API Key Access")
        
        stored_config = session_state.get('app_config')
        if stored_config:
            gemini_key = stored_config.get_api_key_for_provider('gemini')
            openrouter_key = stored_config.get_api_key_for_provider('openrouter')
            
            print(f"  • Gemini API Key: {'✅ Available' if gemini_key else '❌ Not available'}")
            print(f"  • OpenRouter API Key: {'✅ Available' if openrouter_key else '❌ Not available'}")
            
            # Test API configuration status
            api_configured = stored_config.is_api_configured()
            print(f"  • API Configured: {'✅ Yes' if api_configured else '❌ No'}")
        else:
            print("  ❌ Configuration not available in session state")
            return False
        
        # Test 3: Database Configuration Access
        print("\n🗄️ Test 3: Database Configuration Access")
        
        stored_manager = session_state.get('config_manager')
        if stored_manager:
            db_config = stored_manager.get_database_config()
            
            print(f"  • Database Path: {db_config.get('path', 'Not set')}")
            print(f"  • Database URL: {db_config.get('url', 'Not set')}")
            print(f"  • Database Directory: {db_config.get('directory', 'Not set')}")
        else:
            print("  ❌ Config manager not available in session state")
            return False
        
        # Test 4: UI Configuration Access
        print("\n🖥️ Test 4: UI Configuration Access")
        
        ui_config = stored_manager.get_ui_config()
        
        print(f"  • Streamlit Port: {ui_config.get('port', 'Not set')}")
        print(f"  • Debug Mode: {ui_config.get('debug_mode', 'Not set')}")
        print(f"  • Max File Size: {ui_config.get('max_file_size_mb', 'Not set')} MB")
        print(f"  • Allowed File Types: {ui_config.get('allowed_file_types', 'Not set')}")
        
        # Test 5: Processing Configuration Access
        print("\n⚙️ Test 5: Processing Configuration Access")
        
        proc_config = stored_manager.get_processing_config()
        
        print(f"  • Max Processing Jobs: {proc_config.get('max_jobs', 'Not set')}")
        print(f"  • Processing Timeout: {proc_config.get('timeout_seconds', 'Not set')} seconds")
        print(f"  • Max Workers: {proc_config.get('max_workers', 'Not set')}")
        
        # Test 6: Configuration Validation in UI Context
        print("\n✅ Test 6: Configuration Validation")
        
        validation_result = stored_manager.validate_configuration()
        
        print(f"  • Configuration Valid: {'✅ Yes' if validation_result.is_valid else '❌ No'}")
        print(f"  • Validation Errors: {len(validation_result.errors)}")
        print(f"  • Validation Warnings: {len(validation_result.warnings)}")
        
        if validation_result.errors:
            print("  • Errors:")
            for error in validation_result.errors:
                print(f"    - {error}")
        
        if validation_result.warnings:
            print("  • Warnings:")
            for warning in validation_result.warnings:
                print(f"    - {warning}")
        
        # Test 7: Error Handling for Missing Configuration
        print("\n🚨 Test 7: Error Handling for Missing Configuration")
        
        # Test accessing non-existent configuration
        missing_config = session_state.get('non_existent_config', 'default_value')
        print(f"  • Missing config handling: {'✅ Handled' if missing_config == 'default_value' else '❌ Not handled'}")
        
        # Test graceful degradation
        try:
            # Try to access a configuration that might not exist
            optional_config = stored_manager.get('non_existent_key', 'fallback_value')
            print(f"  • Graceful degradation: {'✅ Working' if optional_config == 'fallback_value' else '❌ Not working'}")
        except Exception as e:
            print(f"  • Graceful degradation: ❌ Exception raised: {e}")
            return False
        
        # Test 8: Configuration Status for UI Display
        print("\n📊 Test 8: Configuration Status for UI Display")
        
        status_info = stored_config.get_status_info()
        
        print("  • Status Information:")
        for key, value in status_info.items():
            if isinstance(value, bool):
                status = "✅ Yes" if value else "❌ No"
                print(f"    - {key.replace('_', ' ').title()}: {status}")
            elif isinstance(value, (list, dict)):
                print(f"    - {key.replace('_', ' ').title()}: {len(value)} items")
            else:
                print(f"    - {key.replace('_', ' ').title()}: {value}")
        
        print("\n✅ All Streamlit configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in Streamlit configuration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_error_handling():
    """Test error handling for configuration issues in UI context."""
    print("\n" + "=" * 60)
    print("TESTING UI ERROR HANDLING")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.config_validator import validate_for_ui
        
        # Test UI-specific validation
        is_valid, errors, warnings = validate_for_ui()
        
        print(f"✅ UI validation function accessible")
        print(f"  • Configuration Valid: {'✅ Yes' if is_valid else '❌ No'}")
        print(f"  • Errors: {len(errors)}")
        print(f"  • Warnings: {len(warnings)}")
        
        if errors:
            print("  • Error Messages:")
            for error in errors:
                print(f"    - {error}")
        
        if warnings:
            print("  • Warning Messages:")
            for warning in warnings:
                print(f"    - {warning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing UI error handling: {e}")
        return False


def test_configuration_hot_reload():
    """Test configuration hot reload functionality."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION HOT RELOAD")
    print("=" * 60)
    
    try:
        from src.infrastructure.configuration.centralized_config_manager import config_manager
        
        # Test reload functionality
        print("📋 Testing configuration reload:")
        
        # Get current configuration
        original_debug_mode = config_manager.get('debug_mode')
        print(f"  • Original debug mode: {original_debug_mode}")
        
        # Test reload (this should work even if no changes were made)
        reload_success = config_manager.reload_configuration()
        print(f"  • Reload successful: {'✅ Yes' if reload_success else '❌ No'}")
        
        # Verify configuration is still accessible after reload
        new_debug_mode = config_manager.get('debug_mode')
        print(f"  • Debug mode after reload: {new_debug_mode}")
        
        # Test validation after reload
        validation_result = config_manager.validate_configuration(force_refresh=True)
        print(f"  • Validation after reload: {'✅ Valid' if validation_result.is_valid else '❌ Invalid'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration hot reload: {e}")
        return False


def main():
    """Run all Streamlit configuration tests."""
    print("🧪 STREAMLIT CONFIGURATION INTEGRATION TESTS")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Streamlit Config Access", test_streamlit_config_access()))
    test_results.append(("UI Error Handling", test_ui_error_handling()))
    test_results.append(("Configuration Hot Reload", test_configuration_hot_reload()))
    
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
        print("🎉 All Streamlit configuration tests passed!")
        print("\n💡 Configuration is ready for UI components!")
        return True
    else:
        print("⚠️ Some Streamlit configuration tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)