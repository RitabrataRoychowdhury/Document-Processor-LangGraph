#!/usr/bin/env python3
"""
Test script for OpenRouter API integration.
Tests the OpenRouterLLMStrategy implementation.
"""

import os
import sys
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file."""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

from strategies.qa_strategy import (
    OpenRouterLLMStrategy, 
    QAStrategyFactory, 
    RetrievalContext,
    KeywordRetrievalStrategy,
    HybridQAStrategy
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


def test_openrouter_llm_strategy():
    """Test OpenRouter LLM strategy directly."""
    print("Testing OpenRouter LLM Strategy...")
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    
    try:
        # Create OpenRouter strategy
        openrouter_strategy = OpenRouterLLMStrategy(api_key)
        print("✅ OpenRouter strategy created successfully")
        
        # Create test context
        test_context = [
            RetrievalContext(
                text="The patient has a diagnosis of lumbar spine injury with 15% impairment rating according to AMA Table 15-3.",
                source="Medical Record - Page 5",
                relevance_score=0.9,
                metadata={'page_reference': 5, 'ama_table': '15-3'}
            ),
            RetrievalContext(
                text="Physical examination revealed limited range of motion in the lumbar spine with pain on flexion and extension.",
                source="Examination Report - Page 3",
                relevance_score=0.8,
                metadata={'page_reference': 3}
            )
        ]
        
        # Test question answering
        question = "What is the patient's impairment rating and what table was used?"
        answer = openrouter_strategy.generate_answer(question, test_context)
        
        print(f"✅ Question: {question}")
        print(f"✅ Answer: {answer}")
        
        # Verify answer contains expected information
        if "15%" in answer and ("Table 15-3" in answer or "15-3" in answer):
            print("✅ Answer contains expected information")
            return True
        else:
            print("❌ Answer doesn't contain expected information")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenRouter strategy: {e}")
        return False


def test_qa_strategy_factory():
    """Test QA strategy factory with OpenRouter."""
    print("\nTesting QA Strategy Factory with OpenRouter...")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    
    try:
        # Test factory method for creating OpenRouter LLM strategy
        llm_strategy = QAStrategyFactory.create_llm_strategy('openrouter', api_key)
        print("✅ OpenRouter LLM strategy created via factory")
        
        # Test creating hybrid strategy with OpenRouter
        hybrid_strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='openrouter',
            api_key=api_key
        )
        print("✅ Hybrid strategy with OpenRouter created via factory")
        
        # Test the hybrid strategy
        test_document = {
            'original_text': 'The patient sustained a work-related injury to the lumbar spine. Medical examination shows 15% impairment rating per AMA guidelines Table 15-3.',
            'extracted_info': {'diagnosis': 'lumbar spine injury', 'impairment_rating': '15%'},
            'analysis': 'Work-related lumbar spine injury with documented impairment',
            'summary': 'Lumbar spine injury, 15% impairment rating'
        }
        
        question = "What is the impairment rating?"
        response = hybrid_strategy.answer_question(question, test_document)
        
        print(f"✅ Hybrid strategy question: {question}")
        print(f"✅ Hybrid strategy answer: {response.answer}")
        print(f"✅ Confidence: {response.confidence}")
        print(f"✅ Sources: {response.sources}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing factory: {e}")
        return False


def test_supported_types():
    """Test that factory reports correct supported types."""
    print("\nTesting supported types...")
    
    try:
        llm_types = QAStrategyFactory.get_supported_llm_types()
        retrieval_types = QAStrategyFactory.get_supported_retrieval_types()
        
        print(f"✅ Supported LLM types: {llm_types}")
        print(f"✅ Supported retrieval types: {retrieval_types}")
        
        # Verify OpenRouter is in supported types
        if 'openrouter' in llm_types:
            print("✅ OpenRouter is listed as supported LLM type")
            return True
        else:
            print("❌ OpenRouter not listed as supported LLM type")
            return False
            
    except Exception as e:
        print(f"❌ Error testing supported types: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid API keys."""
    print("\nTesting error handling...")
    
    try:
        # Test with invalid API key
        invalid_strategy = OpenRouterLLMStrategy("invalid_key")
        
        test_context = [
            RetrievalContext(
                text="Test context",
                source="Test",
                relevance_score=0.5,
                metadata={}
            )
        ]
        
        answer = invalid_strategy.generate_answer("Test question?", test_context)
        
        # Should return error message, not crash
        if "error" in answer.lower() or "sorry" in answer.lower():
            print("✅ Error handling works correctly")
            return True
        else:
            print(f"❌ Unexpected response for invalid key: {answer}")
            return False
            
    except Exception as e:
        print(f"✅ Exception handling works: {e}")
        return True


def main():
    """Run all tests."""
    print("🧪 Testing OpenRouter API Integration\n")
    
    tests = [
        test_openrouter_llm_strategy,
        test_qa_strategy_factory,
        test_supported_types,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenRouter integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)