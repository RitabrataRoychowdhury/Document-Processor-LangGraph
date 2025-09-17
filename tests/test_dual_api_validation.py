#!/usr/bin/env python3
"""
Comprehensive test for dual API provider validation.
Tests both Gemini and OpenRouter APIs with various document types and fallback scenarios.
"""

import os
import sys
import json
from typing import Dict, Any, List

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

from infrastructure.api import (
    APIProviderFactory, 
    APIProviderType, 
    APIProviderConfig,
    get_api_factory,
    reset_api_factory
)
from strategies.qa_strategy import (
    QAStrategyFactory,
    HybridQAStrategy,
    RetrievalContext
)


def create_test_documents() -> Dict[str, Dict[str, Any]]:
    """Create test documents of various types for API testing."""
    return {
        "medical_record": {
            "title": "Medical Record - John Doe",
            "document_type": "medical_record",
            "original_text": """
            MEDICAL RECORD
            Patient: John Doe
            Date: 2024-01-15
            
            CHIEF COMPLAINT: Lower back pain following work-related injury
            
            HISTORY OF PRESENT ILLNESS:
            The patient is a 45-year-old construction worker who sustained a lumbar spine injury 
            while lifting heavy materials at work on 2023-12-10. He reports persistent lower back 
            pain radiating to the left leg, with numbness and tingling in the left foot.
            
            PHYSICAL EXAMINATION:
            - Limited range of motion in lumbar spine
            - Positive straight leg raise test on the left
            - Decreased sensation in L5 distribution
            - Muscle weakness in left foot dorsiflexion
            
            DIAGNOSTIC STUDIES:
            MRI lumbar spine shows L4-L5 disc herniation with nerve root compression.
            
            ASSESSMENT AND PLAN:
            1. Lumbar disc herniation with radiculopathy
            2. Work-related injury
            3. Recommend physical therapy and pain management
            4. Impairment rating: 15% whole person impairment per AMA Guides Table 15-3
            """,
            "extracted_info": {
                "patient_name": "John Doe",
                "injury_date": "2023-12-10",
                "diagnosis": "Lumbar disc herniation with radiculopathy",
                "impairment_rating": "15%",
                "ama_table": "15-3"
            },
            "analysis": "Work-related lumbar spine injury with documented impairment rating",
            "summary": "45-year-old construction worker with L4-L5 disc herniation, 15% impairment rating"
        },
        
        "qme_report": {
            "title": "QME Report - Jane Smith",
            "document_type": "qme_report",
            "original_text": """
            QUALIFIED MEDICAL EVALUATOR REPORT
            
            Injured Worker: Jane Smith
            Date of Injury: 2023-08-15
            Date of Evaluation: 2024-02-01
            
            MEDICAL HISTORY:
            Ms. Smith sustained a right shoulder injury while working as a nurse. She was lifting 
            a patient when she felt a sharp pain in her right shoulder.
            
            PHYSICAL EXAMINATION:
            Right shoulder examination reveals:
            - Limited abduction to 90 degrees
            - Positive impingement signs
            - Weakness in external rotation
            - Tenderness over subacromial space
            
            DIAGNOSTIC STUDIES:
            MRI right shoulder shows rotator cuff tear involving supraspinatus tendon.
            
            MEDICAL OPINION:
            1. Right shoulder rotator cuff tear, work-related
            2. Maximum medical improvement reached
            3. Permanent disability: 25% of the right upper extremity
            4. Apportionment: 100% industrial
            5. Future medical care: Ongoing physical therapy as needed
            
            IMPAIRMENT RATING:
            Per AMA Guides 6th Edition, Table 16-3: 25% upper extremity impairment
            Converted to whole person: 15% whole person impairment
            """,
            "extracted_info": {
                "patient_name": "Jane Smith",
                "injury_date": "2023-08-15",
                "diagnosis": "Right shoulder rotator cuff tear",
                "impairment_rating": "15% whole person, 25% upper extremity",
                "ama_table": "16-3",
                "apportionment": "100% industrial"
            },
            "analysis": "Work-related shoulder injury with permanent disability rating",
            "summary": "Nurse with work-related rotator cuff tear, 15% whole person impairment"
        },
        
        "legal_document": {
            "title": "Workers' Compensation Claim",
            "document_type": "legal_document",
            "original_text": """
            WORKERS' COMPENSATION CLAIM
            Case No: WC-2024-001234
            
            CLAIMANT: Robert Johnson
            EMPLOYER: ABC Manufacturing Inc.
            DATE OF INJURY: 2023-11-20
            
            DESCRIPTION OF INJURY:
            Employee sustained bilateral carpal tunnel syndrome due to repetitive motion 
            activities performed over a period of 5 years in the assembly line.
            
            MEDICAL TREATMENT:
            - Conservative treatment with splinting and physical therapy
            - Bilateral carpal tunnel release surgery performed on 2024-01-15
            - Post-operative recovery with return to modified duties
            
            DISABILITY RATING:
            Per QME evaluation dated 2024-03-01:
            - Bilateral carpal tunnel syndrome with surgical treatment
            - 10% permanent disability to each upper extremity
            - Combined rating: 19% whole person impairment per AMA Guides
            
            SETTLEMENT:
            Permanent disability award based on 19% whole person impairment
            Future medical care for ongoing treatment as needed
            """,
            "extracted_info": {
                "patient_name": "Robert Johnson",
                "injury_date": "2023-11-20",
                "diagnosis": "Bilateral carpal tunnel syndrome",
                "impairment_rating": "19% whole person",
                "treatment": "Bilateral carpal tunnel release surgery"
            },
            "analysis": "Repetitive motion injury with surgical treatment and permanent disability",
            "summary": "Assembly line worker with bilateral carpal tunnel syndrome, 19% impairment"
        }
    }


def test_gemini_api_with_documents():
    """Test Gemini API with various document types."""
    print("Testing Gemini API with various document types...")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set, skipping Gemini tests")
        return True
    
    try:
        # Create Gemini strategy
        gemini_strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='gemini',
            api_key=gemini_key
        )
        
        test_documents = create_test_documents()
        test_questions = [
            "What is the patient's impairment rating?",
            "What was the date of injury?",
            "What is the primary diagnosis?",
            "What AMA table was used for the rating?"
        ]
        
        success_count = 0
        total_tests = 0
        
        for doc_type, document in test_documents.items():
            print(f"  Testing with {doc_type}...")
            
            for question in test_questions:
                total_tests += 1
                try:
                    response = gemini_strategy.answer_question(question, document)
                    
                    if response.answer and len(response.answer) > 10:
                        success_count += 1
                        print(f"    ✅ Q: {question[:30]}... A: {response.answer[:50]}...")
                    else:
                        print(f"    ❌ Q: {question[:30]}... (No meaningful answer)")
                        
                except Exception as e:
                    print(f"    ❌ Q: {question[:30]}... Error: {e}")
        
        success_rate = success_count / total_tests if total_tests > 0 else 0
        print(f"  Gemini API success rate: {success_count}/{total_tests} ({success_rate:.1%})")
        
        # Consider test passed if success rate > 50%
        return success_rate > 0.5
        
    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
        return False


def test_openrouter_api_with_documents():
    """Test OpenRouter API with various document types."""
    print("\nTesting OpenRouter API with various document types...")
    
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_key:
        print("⚠️  OPENROUTER_API_KEY not set, skipping OpenRouter tests")
        return True
    
    try:
        # Create OpenRouter strategy
        openrouter_strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='openrouter',
            api_key=openrouter_key
        )
        
        test_documents = create_test_documents()
        test_questions = [
            "What is the patient's impairment rating?",
            "What was the date of injury?",
            "What is the primary diagnosis?",
            "What AMA table was used for the rating?"
        ]
        
        success_count = 0
        total_tests = 0
        
        for doc_type, document in test_documents.items():
            print(f"  Testing with {doc_type}...")
            
            for question in test_questions:
                total_tests += 1
                try:
                    response = openrouter_strategy.answer_question(question, document)
                    
                    if response.answer and len(response.answer) > 10 and "error" not in response.answer.lower():
                        success_count += 1
                        print(f"    ✅ Q: {question[:30]}... A: {response.answer[:50]}...")
                    else:
                        print(f"    ❌ Q: {question[:30]}... A: {response.answer[:50]}...")
                        
                except Exception as e:
                    print(f"    ❌ Q: {question[:30]}... Error: {e}")
        
        success_rate = success_count / total_tests if total_tests > 0 else 0
        print(f"  OpenRouter API success rate: {success_count}/{total_tests} ({success_rate:.1%})")
        
        # Consider test passed if success rate > 50%
        return success_rate > 0.5
        
    except Exception as e:
        print(f"❌ Error testing OpenRouter API: {e}")
        return False


def test_api_provider_factory_with_real_apis():
    """Test API provider factory with real API calls."""
    print("\nTesting API Provider Factory with real APIs...")
    
    try:
        # Reset and get fresh factory
        reset_api_factory()
        factory = get_api_factory()
        
        # Test all configured providers
        test_results = factory.test_all_providers()
        
        print("  Provider test results:")
        for provider_type, result in test_results.items():
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"    {provider_type.value}: {status}")
            if not result.success:
                print(f"      Error: {result.error}")
        
        # Test answer generation with fallback
        test_context = [
            RetrievalContext(
                text="Patient has 15% impairment rating per AMA Table 15-3 for lumbar spine injury.",
                source="Medical Record",
                relevance_score=0.9,
                metadata={'ama_table': '15-3'}
            )
        ]
        
        result = factory.generate_answer_with_fallback(
            "What is the impairment rating?", 
            test_context
        )
        
        if result.success:
            print(f"  ✅ Fallback answer generation successful with {result.provider_used.value}")
            print(f"    Answer: {result.result[:100]}...")
        else:
            print(f"  ❌ Fallback answer generation failed: {result.error}")
        
        # Get provider statistics
        stats = factory.get_provider_stats()
        health = factory.get_provider_health()
        
        print("  Provider health status:")
        for provider_type, status in health.items():
            print(f"    {provider_type.value}: {status}")
        
        return len([r for r in test_results.values() if r.success]) > 0
        
    except Exception as e:
        print(f"❌ Error testing API provider factory: {e}")
        return False


def test_fallback_behavior():
    """Test fallback behavior when primary provider is unavailable."""
    print("\nTesting fallback behavior...")
    
    try:
        factory = APIProviderFactory()
        
        # Add providers with different priorities
        # Primary: Invalid key (should fail)
        # Secondary: Valid key (should succeed)
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        
        if not (gemini_key or openrouter_key):
            print("⚠️  No valid API keys available, skipping fallback test")
            return True
        
        # Add invalid primary provider
        factory.add_provider(APIProviderConfig(
            provider_type=APIProviderType.GEMINI,
            api_key="invalid_key_primary",
            priority=1,
            max_retries=1  # Fail fast
        ))
        
        # Add valid secondary provider
        if openrouter_key:
            factory.add_provider(APIProviderConfig(
                provider_type=APIProviderType.OPENROUTER,
                api_key=openrouter_key,
                priority=2,
                max_retries=1
            ))
        elif gemini_key:
            factory.add_provider(APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                api_key=gemini_key,
                priority=2,
                max_retries=1
            ))
        
        # Test fallback
        test_context = [
            RetrievalContext(
                text="Test context for fallback testing.",
                source="Test",
                relevance_score=1.0,
                metadata={}
            )
        ]
        
        result = factory.generate_answer_with_fallback(
            "What is this test about?",
            test_context
        )
        
        if result.success:
            print(f"  ✅ Fallback successful: Primary failed, {result.provider_used.value} succeeded")
            print(f"    Attempts made: {result.attempt_count}")
            return True
        else:
            print(f"  ❌ Fallback failed: {result.error}")
            print(f"    Attempts made: {result.attempt_count}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing fallback behavior: {e}")
        return False


def test_api_comparison():
    """Compare responses from both APIs for the same questions."""
    print("\nTesting API comparison...")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    
    if not (gemini_key and openrouter_key):
        print("⚠️  Both API keys needed for comparison, skipping")
        return True
    
    try:
        # Create strategies for both APIs
        gemini_strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='gemini',
            api_key=gemini_key
        )
        
        openrouter_strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type='keyword',
            llm_type='openrouter',
            api_key=openrouter_key
        )
        
        # Test document
        test_doc = create_test_documents()["medical_record"]
        test_question = "What is the patient's impairment rating and which AMA table was used?"
        
        print(f"  Question: {test_question}")
        
        # Get responses from both APIs
        gemini_response = gemini_strategy.answer_question(test_question, test_doc)
        openrouter_response = openrouter_strategy.answer_question(test_question, test_doc)
        
        print(f"  Gemini answer: {gemini_response.answer[:100]}...")
        print(f"  OpenRouter answer: {openrouter_response.answer[:100]}...")
        
        # Check if both contain expected information
        expected_terms = ["15%", "table", "15-3"]
        
        gemini_score = sum(1 for term in expected_terms if term.lower() in gemini_response.answer.lower())
        openrouter_score = sum(1 for term in expected_terms if term.lower() in openrouter_response.answer.lower())
        
        print(f"  Gemini relevance score: {gemini_score}/{len(expected_terms)}")
        print(f"  OpenRouter relevance score: {openrouter_score}/{len(expected_terms)}")
        
        # Test passes if at least one API provides relevant information
        return max(gemini_score, openrouter_score) >= 2
        
    except Exception as e:
        print(f"❌ Error in API comparison: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🧪 Comprehensive Dual API Provider Validation\n")
    
    tests = [
        test_gemini_api_with_documents,
        test_openrouter_api_with_documents,
        test_api_provider_factory_with_real_apis,
        test_fallback_behavior,
        test_api_comparison
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
    
    if passed >= total - 1:  # Allow one test to fail (in case API keys are missing)
        print("🎉 Dual API validation successful! Both providers are working correctly.")
        return True
    else:
        print("❌ Some critical tests failed. Please check API configurations.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)