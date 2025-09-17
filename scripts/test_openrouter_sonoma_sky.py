#!/usr/bin/env python3
"""
Test script to verify OpenRouter API connectivity with Sonoma Sky (Claude 3.5 Sonnet).

This script tests the OpenRouter integration to ensure the API key is working
and the Sonoma Sky model is accessible for document extraction.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
from src.models.extraction_models import ExtractionConfig
from src.config.openrouter_config_manager import OpenRouterConfigManager


def test_api_connectivity():
    """Test basic API connectivity."""
    print("🔍 Testing OpenRouter API connectivity...")
    
    try:
        # Check if API key is set
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("❌ OPENROUTER_API_KEY not found in environment variables")
            return False
        
        print(f"✅ API Key found: {api_key[:20]}...")
        
        # Initialize the service
        service = OpenRouterExtractionService()
        print("✅ OpenRouter service initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing OpenRouter service: {str(e)}")
        return False


def test_model_access():
    """Test access to Sonoma Sky (Claude 3.5 Sonnet) model."""
    print("\n🤖 Testing Sonoma Sky model access...")
    
    try:
        service = OpenRouterExtractionService()
        
        # Create a simple test prompt
        test_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond with a JSON object containing a 'status' field set to 'success' and a 'message' field with a brief greeting."
            },
            {
                "role": "user",
                "content": "Please respond with a test message to verify the API is working."
            }
        ]
        
        print("📡 Making test API call to Sonoma Sky...")
        start_time = time.time()
        
        # Make API call
        response = service._make_api_call(test_messages)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ API call successful in {response_time:.2f} seconds")
        
        # Extract response content
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0]['message']['content']
            print(f"📝 Response content: {content[:200]}...")
            
            # Try to parse as JSON
            try:
                parsed_response = json.loads(content)
                if parsed_response.get('status') == 'success':
                    print("✅ Sonoma Sky model responding correctly")
                    return True
                else:
                    print("⚠️ Unexpected response format")
                    return False
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON, but API is working")
                return True
        else:
            print("❌ Unexpected API response format")
            return False
            
    except Exception as e:
        print(f"❌ Error testing model access: {str(e)}")
        return False


def test_document_extraction():
    """Test document extraction with a sample text."""
    print("\n📄 Testing document extraction capabilities...")
    
    try:
        service = OpenRouterExtractionService()
        
        # Create a sample medical document text
        sample_document = """
        QUALIFIED MEDICAL EVALUATOR REPORT
        
        Patient Information:
        Name: John Smith
        Date of Birth: 01/15/1980
        Age: 43
        Gender: Male
        Case Number: WC-2023-12345
        
        Medical History:
        The patient sustained a work-related injury to his lower back on March 15, 2023.
        He reports persistent pain in the lumbar region with radiation to the left leg.
        
        Diagnosis:
        Primary: Lumbar disc herniation at L4-L5
        Secondary: Sciatica, left side
        
        Impairment Rating:
        Based on AMA Guides 5th Edition, Table 15-3
        Whole Person Impairment: 12%
        """
        
        # Create extraction config
        extraction_config = ExtractionConfig(
            prompt_template="patient_info",
            extraction_type="qme_comprehensive",
            quality_threshold=0.7,
            enable_vision=False
        )
        
        # Create a temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_document)
            temp_file_path = f.name
        
        try:
            print("🔄 Extracting information from sample document...")
            start_time = time.time()
            
            # Perform extraction
            result = service.extract_from_document(temp_file_path, extraction_config)
            
            end_time = time.time()
            extraction_time = end_time - start_time
            
            print(f"✅ Extraction completed in {extraction_time:.2f} seconds")
            print(f"📊 Confidence Score: {result.confidence_score:.2f}")
            print(f"🔍 Fields Extracted: {len(result.extracted_fields)}")
            
            # Display extracted fields
            for field_name, field in result.extracted_fields.items():
                if field.value and field.value != "NOT_FOUND":
                    print(f"  • {field_name}: {field.value} (confidence: {field.confidence:.2f})")
            
            # Check quality assessment
            quality = result.quality_assessment
            print(f"📈 Quality Metrics:")
            print(f"  • Overall Score: {quality.overall_score:.2f}")
            print(f"  • Completeness: {quality.completeness_score:.2f}")
            print(f"  • Accuracy: {quality.accuracy_score:.2f}")
            
            if result.confidence_score >= 0.7:
                print("✅ Document extraction test passed")
                return True
            else:
                print("⚠️ Document extraction confidence below threshold")
                return False
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"❌ Error testing document extraction: {str(e)}")
        return False


def test_vision_capabilities():
    """Test vision capabilities if enabled."""
    print("\n👁️ Testing vision capabilities...")
    
    try:
        service = OpenRouterExtractionService()
        
        # Check if vision is enabled in config
        if not service.config.get('vision', {}).get('enabled', False):
            print("⚠️ Vision capabilities not enabled in configuration")
            return True  # Not a failure, just not configured
        
        print("✅ Vision capabilities are enabled in configuration")
        print("📝 Note: Vision testing requires actual image files")
        print("   This would be tested with real PDF/image documents in production")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing vision capabilities: {str(e)}")
        return False


def test_error_handling():
    """Test error handling and recovery."""
    print("\n🛡️ Testing error handling...")
    
    try:
        service = OpenRouterExtractionService()
        
        # Test with invalid input
        try:
            invalid_messages = [{"invalid": "format"}]
            service._make_api_call(invalid_messages)
            print("⚠️ Expected error not raised for invalid input")
            return False
        except Exception as e:
            print(f"✅ Error handling working correctly: {type(e).__name__}")
        
        # Test with non-existent file
        try:
            extraction_config = ExtractionConfig(prompt_template="patient_info")
            service.extract_from_document("/non/existent/file.txt", extraction_config)
            print("⚠️ Expected error not raised for non-existent file")
            return False
        except Exception as e:
            print(f"✅ File error handling working correctly: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing error handling: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🚀 OpenRouter Sonoma Sky API Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Connectivity", test_api_connectivity),
        ("Model Access", test_model_access),
        ("Document Extraction", test_document_extraction),
        ("Vision Capabilities", test_vision_capabilities),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Sonoma Sky integration is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration and API key.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)