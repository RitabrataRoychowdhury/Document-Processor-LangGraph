#!/usr/bin/env python3
"""
Basic test for OpenRouter API integration without requiring valid API keys.
Tests the implementation structure and error handling.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategies.qa_strategy import (
    OpenRouterLLMStrategy, 
    QAStrategyFactory, 
    RetrievalContext
)


def test_openrouter_initialization():
    """Test OpenRouter strategy initialization."""
    print("Testing OpenRouter initialization...")
    
    try:
        # Test with dummy API key
        strategy = OpenRouterLLMStrategy("test_key")
        print("✅ OpenRouter strategy initialized successfully")
        
        # Check attributes
        assert strategy.api_key == "test_key"
        assert strategy.model == "anthropic/claude-3.5-sonnet"
        assert strategy.api_url == "https://openrouter.ai/api/v1/chat/completions"
        print("✅ All attributes set correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing OpenRouter strategy: {e}")
        return False


def test_factory_integration():
    """Test factory integration with OpenRouter."""
    print("\nTesting factory integration...")
    
    try:
        # Test factory method
        strategy = QAStrategyFactory.create_llm_strategy('openrouter', 'test_key')
        print("✅ Factory created OpenRouter strategy")
        
        # Test with custom model
        strategy_custom = QAStrategyFactory.create_llm_strategy('openrouter', 'test_key', 'anthropic/claude-3-opus')
        assert strategy_custom.model == 'anthropic/claude-3-opus'
        print("✅ Factory supports custom models")
        
        # Test hybrid strategy creation
        hybrid = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='openrouter',
            api_key='test_key'
        )
        print("✅ Factory created hybrid strategy with OpenRouter")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing factory: {e}")
        return False


def test_supported_types():
    """Test supported types include OpenRouter."""
    print("\nTesting supported types...")
    
    try:
        llm_types = QAStrategyFactory.get_supported_llm_types()
        
        assert 'openrouter' in llm_types
        assert 'gemini' in llm_types
        assert 'openai' in llm_types
        
        print(f"✅ Supported LLM types: {llm_types}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing supported types: {e}")
        return False


def test_api_headers():
    """Test that OpenRouter uses correct headers."""
    print("\nTesting API headers...")
    
    try:
        strategy = OpenRouterLLMStrategy("test_key")
        
        # Test the _call_openrouter_api method structure (without actually calling)
        messages = [{"role": "user", "content": "test"}]
        
        # We can't test the actual API call without a valid key,
        # but we can verify the method exists and has the right structure
        assert hasattr(strategy, '_call_openrouter_api')
        print("✅ OpenRouter API method exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API headers: {e}")
        return False


def test_error_handling_structure():
    """Test error handling structure."""
    print("\nTesting error handling structure...")
    
    try:
        strategy = OpenRouterLLMStrategy("invalid_key")
        
        # Create test context
        context = [
            RetrievalContext(
                text="Test context",
                source="Test",
                relevance_score=0.5,
                metadata={}
            )
        ]
        
        # This should handle the error gracefully
        answer = strategy.generate_answer("Test question?", context)
        
        # Should return an error message, not crash
        assert isinstance(answer, str)
        assert len(answer) > 0
        print("✅ Error handling returns proper response")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in error handling test: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing OpenRouter Basic Integration\n")
    
    tests = [
        test_openrouter_initialization,
        test_factory_integration,
        test_supported_types,
        test_api_headers,
        test_error_handling_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! OpenRouter integration structure is correct.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)