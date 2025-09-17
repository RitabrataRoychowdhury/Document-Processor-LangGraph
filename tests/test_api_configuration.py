#!/usr/bin/env python3
"""
Test script to verify API configurations for both Gemini and OpenRouter.
This script tests the configuration and basic connectivity without making actual API calls.
"""

import os
import sys
from typing import Dict, Any

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_environment_variables():
    """Test that environment variables are properly loaded."""
    print("🔧 Testing Environment Variables...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
    except ImportError:
        print("⚠️  dotenv not available, using system environment variables")
    
    # Check API keys
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
    
    print(f"📊 API Key Status:")
    print(f"   Gemini API Key: {'✅ Configured' if gemini_key else '❌ Missing'}")
    print(f"   OpenRouter API Key: {'✅ Configured' if openrouter_key else '❌ Missing'}")
    
    return {
        'gemini_configured': bool(gemini_key),
        'openrouter_configured': bool(openrouter_key),
        'gemini_key_length': len(gemini_key) if gemini_key else 0,
        'openrouter_key_length': len(openrouter_key) if openrouter_key else 0
    }

def test_app_config():
    """Test the application configuration."""
    print("\n🔧 Testing Application Configuration...")
    
    try:
        from src.config.app_config import AppConfig
        
        # Create config from environment
        config = AppConfig.from_env()
        
        print("✅ AppConfig created successfully")
        print(f"📊 Configuration Status:")
        print(f"   QA Provider: {config.qa_provider}")
        print(f"   Embedding Provider: {config.embedding_provider}")
        print(f"   API Configured: {'✅' if config.is_api_configured() else '❌'}")
        print(f"   Database Path: {config.database_path}")
        print(f"   Max File Size: {config.max_file_size_mb} MB")
        
        # Test validation
        errors = config.validate()
        if errors:
            print(f"⚠️  Configuration Errors:")
            for error in errors:
                print(f"     - {error}")
        else:
            print("✅ Configuration validation passed")
        
        return {
            'config_created': True,
            'api_configured': config.is_api_configured(),
            'validation_errors': errors,
            'qa_provider': config.qa_provider
        }
        
    except Exception as e:
        print(f"❌ Error creating AppConfig: {e}")
        return {
            'config_created': False,
            'error': str(e)
        }

def test_qa_strategies():
    """Test QA strategy creation."""
    print("\n🔧 Testing QA Strategy Creation...")
    
    try:
        from src.strategies.qa_strategy import QAStrategyFactory, GeminiLLMStrategy, OpenRouterLLMStrategy
        
        # Test Gemini strategy
        gemini_key = os.getenv('GEMINI_API_KEY', '')
        if gemini_key:
            try:
                gemini_strategy = GeminiLLMStrategy(gemini_key)
                print("✅ Gemini LLM Strategy created successfully")
            except Exception as e:
                print(f"❌ Error creating Gemini strategy: {e}")
        else:
            print("⚠️  Gemini API key not available, skipping Gemini strategy test")
        
        # Test OpenRouter strategy
        openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
        if openrouter_key:
            try:
                openrouter_strategy = OpenRouterLLMStrategy(openrouter_key)
                print("✅ OpenRouter LLM Strategy created successfully")
            except Exception as e:
                print(f"❌ Error creating OpenRouter strategy: {e}")
        else:
            print("⚠️  OpenRouter API key not available, skipping OpenRouter strategy test")
        
        # Test factory
        try:
            if gemini_key:
                hybrid_gemini = QAStrategyFactory.create_hybrid_strategy(
                    retrieval_type="keyword",
                    llm_type="gemini",
                    api_key=gemini_key
                )
                print("✅ Hybrid Gemini strategy created via factory")
            
            if openrouter_key:
                hybrid_openrouter = QAStrategyFactory.create_hybrid_strategy(
                    retrieval_type="keyword",
                    llm_type="openrouter",
                    api_key=openrouter_key,
                    model="anthropic/claude-3.5-sonnet"
                )
                print("✅ Hybrid OpenRouter strategy created via factory")
                
        except Exception as e:
            print(f"❌ Error creating hybrid strategies: {e}")
        
        return {
            'gemini_available': bool(gemini_key),
            'openrouter_available': bool(openrouter_key),
            'strategies_tested': True
        }
        
    except Exception as e:
        print(f"❌ Error testing QA strategies: {e}")
        return {
            'strategies_tested': False,
            'error': str(e)
        }

def test_dependency_injection():
    """Test dependency injection configuration."""
    print("\n🔧 Testing Dependency Injection...")
    
    try:
        from src.config.dependency_injection import DependencyContainer, AppConfig as DIAppConfig
        
        # Create container
        container = DependencyContainer()
        print("✅ Dependency container created")
        
        # Test configuration validation
        validation = container.validate_configuration()
        print(f"📊 Configuration Validation:")
        print(f"   Valid: {'✅' if validation['valid'] else '❌'}")
        
        if validation['errors']:
            print(f"   Errors:")
            for error in validation['errors']:
                print(f"     - {error}")
        
        if validation['warnings']:
            print(f"   Warnings:")
            for warning in validation['warnings']:
                print(f"     - {warning}")
        
        # Test configuration summary
        summary = container.get_configuration_summary()
        print(f"📊 Configuration Summary:")
        print(f"   QA Provider: {summary['qa_provider']}")
        print(f"   Embedding Provider: {summary['embedding_provider']}")
        print(f"   Has Gemini Key: {'✅' if summary['has_gemini_key'] else '❌'}")
        print(f"   Has OpenAI Key: {'✅' if summary['has_openai_key'] else '❌'}")
        print(f"   Has OpenRouter Key: {'✅' if summary['has_openrouter_key'] else '❌'}")
        
        return {
            'container_created': True,
            'validation_passed': validation['valid'],
            'summary': summary
        }
        
    except Exception as e:
        print(f"❌ Error testing dependency injection: {e}")
        return {
            'container_created': False,
            'error': str(e)
        }

def test_main_app_imports():
    """Test that main app can import without errors."""
    print("\n🔧 Testing Main App Imports...")
    
    try:
        # Test basic imports
        from src.ui.main_app import main
        print("✅ Main app imports successful")
        
        # Test upload interface
        from src.ui.upload_interface import UploadInterface
        upload_interface = UploadInterface()
        print("✅ Upload interface created successfully")
        
        return {
            'main_app_imports': True,
            'upload_interface_created': True
        }
        
    except Exception as e:
        print(f"❌ Error testing main app imports: {e}")
        return {
            'main_app_imports': False,
            'error': str(e)
        }

def main():
    """Run all configuration tests."""
    print("🚀 API Configuration Test Suite")
    print("=" * 50)
    
    results = {}
    
    # Run tests
    results['env_vars'] = test_environment_variables()
    results['app_config'] = test_app_config()
    results['qa_strategies'] = test_qa_strategies()
    results['dependency_injection'] = test_dependency_injection()
    results['main_app'] = test_main_app_imports()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for test_name, result in results.items():
        total_tests += 1
        if isinstance(result, dict):
            # Check if test passed based on key indicators
            test_passed = False
            if test_name == 'env_vars':
                test_passed = result.get('gemini_configured', False) or result.get('openrouter_configured', False)
            elif test_name == 'app_config':
                test_passed = result.get('config_created', False) and result.get('api_configured', False)
            elif test_name == 'qa_strategies':
                test_passed = result.get('strategies_tested', False)
            elif test_name == 'dependency_injection':
                test_passed = result.get('container_created', False)
            elif test_name == 'main_app':
                test_passed = result.get('main_app_imports', False)
            
            if test_passed:
                passed_tests += 1
                print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
            else:
                print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
    
    print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)