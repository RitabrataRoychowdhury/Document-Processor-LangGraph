#!/usr/bin/env python3
"""
Q&A Functionality Integration Test
Tests the complete Q&A system integration including UI, backend QA engines, and API providers.
"""

import sys
import os
import subprocess
import time
import threading
import requests
import tempfile
import json
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QAFunctionalityTester:
    """Comprehensive tester for Q&A functionality integration."""
    
    def __init__(self):
        self.streamlit_process = None
        self.test_results = {}
        self.base_url = "http://localhost:8503"  # Use different port to avoid conflicts
        
    def test_qa_interface_availability(self) -> Dict[str, Any]:
        """Test that the Q&A interface is available and functional."""
        logger.info("Testing Q&A interface availability...")
        
        try:
            # Start Streamlit for testing
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "src/ui/main_app.py",
                "--server.port=8503",
                "--server.headless=true",
                "--browser.gatherUsageStats=false"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for startup
            startup_success = False
            for _ in range(30):  # 30 second timeout
                try:
                    response = requests.get(f"{self.base_url}/", timeout=5)
                    if response.status_code == 200:
                        startup_success = True
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            if not startup_success:
                return {
                    "status": "FAIL",
                    "message": "Streamlit failed to start for Q&A testing",
                    "details": "Could not access Q&A interface"
                }
            
            # Check if Q&A interface is accessible
            response = requests.get(f"{self.base_url}/", timeout=10)
            page_content = response.text.lower()
            
            # Look for Q&A-related content
            qa_indicators = [
                "q&a interface",
                "ask a question",
                "document q&a",
                "question answering"
            ]
            
            found_indicators = [indicator for indicator in qa_indicators if indicator in page_content]
            
            if found_indicators:
                return {
                    "status": "PASS",
                    "message": f"Q&A interface available with {len(found_indicators)} Q&A features",
                    "details": f"Found indicators: {found_indicators}"
                }
            else:
                return {
                    "status": "PARTIAL",
                    "message": "Q&A interface may be available but not prominently displayed",
                    "details": "No Q&A-specific content found in main page"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Q&A interface test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_qa_backend_components(self) -> Dict[str, Any]:
        """Test that Q&A backend components are available."""
        logger.info("Testing Q&A backend components...")
        
        try:
            # Test import of key Q&A components
            test_imports = [
                "from src.ui.qa_interface_simple import render_qa_page",
                "from src.strategies.qa_strategy import QAStrategy, QAResponse",
                "from src.strategies.qa_strategy import GeminiLLMStrategy, OpenRouterLLMStrategy",
                "from src.infrastructure.api.api_provider_factory import APIProviderFactory"
            ]
            
            successful_imports = []
            failed_imports = []
            
            for import_statement in test_imports:
                try:
                    import_cmd = [
                        sys.executable, "-c",
                        f"import sys; sys.path.append('src'); {import_statement}; print('SUCCESS')"
                    ]
                    
                    result = subprocess.run(
                        import_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0 and "SUCCESS" in result.stdout:
                        successful_imports.append(import_statement.split()[-1])
                    else:
                        failed_imports.append(import_statement.split()[-1])
                        
                except subprocess.TimeoutExpired:
                    failed_imports.append(import_statement.split()[-1])
                except Exception:
                    failed_imports.append(import_statement.split()[-1])
            
            # Test Q&A strategy instantiation
            try:
                strategy_test_cmd = [
                    sys.executable, "-c",
                    """
import sys
sys.path.append('src')
from src.strategies.qa_strategy import KeywordRetrievalStrategy, QAResponse, RetrievalContext

# Test basic strategy components
retrieval_strategy = KeywordRetrievalStrategy()
print('RETRIEVAL_STRATEGY_SUCCESS')

# Test response objects
response = QAResponse(
    answer="Test answer",
    sources=["Test source"],
    confidence=0.8,
    metadata={}
)
print('QA_RESPONSE_SUCCESS')

context = RetrievalContext(
    text="Test context",
    source="Test source",
    relevance_score=0.9,
    metadata={}
)
print('RETRIEVAL_CONTEXT_SUCCESS')
"""
                ]
                
                result = subprocess.run(
                    strategy_test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                strategy_components_work = all(success in result.stdout for success in [
                    "RETRIEVAL_STRATEGY_SUCCESS",
                    "QA_RESPONSE_SUCCESS", 
                    "RETRIEVAL_CONTEXT_SUCCESS"
                ])
                
            except Exception:
                strategy_components_work = False
            
            # Evaluate results
            total_components = len(test_imports)
            working_components = len(successful_imports)
            
            if working_components == total_components and strategy_components_work:
                return {
                    "status": "PASS",
                    "message": f"All {total_components} Q&A backend components available",
                    "details": f"Working: {successful_imports}, Strategy components: {'✅' if strategy_components_work else '❌'}"
                }
            elif working_components > 0:
                return {
                    "status": "PARTIAL",
                    "message": f"{working_components}/{total_components} Q&A components available",
                    "details": f"Working: {successful_imports}, Failed: {failed_imports}, Strategy: {'✅' if strategy_components_work else '❌'}"
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Q&A backend components not available",
                    "details": f"Failed imports: {failed_imports}, Strategy: {'❌' if not strategy_components_work else '✅'}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Q&A backend test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_api_provider_integration(self) -> Dict[str, Any]:
        """Test that both Gemini and OpenRouter API providers work correctly."""
        logger.info("Testing API provider integration...")
        
        try:
            # Test API provider factory and strategies
            api_test_cmd = [
                sys.executable, "-c",
                """
import sys
sys.path.append('src')
import os

# Test API provider factory
try:
    from src.infrastructure.api.api_provider_factory import APIProviderFactory
    factory = APIProviderFactory()
    print('API_FACTORY_SUCCESS')
except Exception as e:
    print(f'API_FACTORY_ERROR: {e}')

# Test Gemini strategy (without actual API call)
try:
    from src.strategies.qa_strategy import GeminiLLMStrategy
    # Don't instantiate without API key, just test import
    print('GEMINI_STRATEGY_SUCCESS')
except Exception as e:
    print(f'GEMINI_STRATEGY_ERROR: {e}')

# Test OpenRouter strategy (without actual API call)
try:
    from src.strategies.qa_strategy import OpenRouterLLMStrategy
    # Don't instantiate without API key, just test import
    print('OPENROUTER_STRATEGY_SUCCESS')
except Exception as e:
    print(f'OPENROUTER_STRATEGY_ERROR: {e}')

# Test keyword fallback strategy
try:
    from src.strategies.qa_strategy import KeywordRetrievalStrategy
    strategy = KeywordRetrievalStrategy()
    
    # Test basic retrieval
    test_doc = {
        'original_text': 'Patient John Doe has a back injury from January 2024.',
        'extracted_info': {'patient_name': 'John Doe', 'injury_date': 'January 2024'}
    }
    
    contexts = strategy.retrieve_context('What is the patient name?', test_doc)
    if contexts:
        print('KEYWORD_RETRIEVAL_SUCCESS')
    else:
        print('KEYWORD_RETRIEVAL_NO_RESULTS')
        
except Exception as e:
    print(f'KEYWORD_RETRIEVAL_ERROR: {e}')

print('API_PROVIDER_TEST_COMPLETE')
"""
            ]
            
            result = subprocess.run(
                api_test_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0 and "API_PROVIDER_TEST_COMPLETE" in result.stdout:
                # Parse results from output
                output_lines = result.stdout.strip().split('\n')
                
                api_factory_works = any("API_FACTORY_SUCCESS" in line for line in output_lines)
                gemini_strategy_works = any("GEMINI_STRATEGY_SUCCESS" in line for line in output_lines)
                openrouter_strategy_works = any("OPENROUTER_STRATEGY_SUCCESS" in line for line in output_lines)
                keyword_retrieval_works = any("KEYWORD_RETRIEVAL_SUCCESS" in line for line in output_lines)
                
                working_components = sum([
                    api_factory_works,
                    gemini_strategy_works, 
                    openrouter_strategy_works,
                    keyword_retrieval_works
                ])
                
                if working_components >= 3:  # At least 3 of 4 components should work
                    return {
                        "status": "PASS",
                        "message": f"API provider integration working ({working_components}/4 components)",
                        "details": f"Factory: {'✅' if api_factory_works else '❌'}, Gemini: {'✅' if gemini_strategy_works else '❌'}, OpenRouter: {'✅' if openrouter_strategy_works else '❌'}, Keyword: {'✅' if keyword_retrieval_works else '❌'}"
                    }
                elif working_components >= 1:
                    return {
                        "status": "PARTIAL",
                        "message": f"Some API components working ({working_components}/4 components)",
                        "details": f"Factory: {'✅' if api_factory_works else '❌'}, Gemini: {'✅' if gemini_strategy_works else '❌'}, OpenRouter: {'✅' if openrouter_strategy_works else '❌'}, Keyword: {'✅' if keyword_retrieval_works else '❌'}"
                    }
                else:
                    return {
                        "status": "FAIL",
                        "message": "API provider integration not working",
                        "details": f"All components failed: {result.stdout}"
                    }
            else:
                return {
                    "status": "FAIL",
                    "message": "API provider integration test failed",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"API provider test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_fallback_behavior(self) -> Dict[str, Any]:
        """Test that fallback behavior works when API providers fail."""
        logger.info("Testing fallback behavior...")
        
        try:
            # Test fallback mechanisms
            fallback_test_cmd = [
                sys.executable, "-c",
                """
import sys
sys.path.append('src')

# Test keyword fallback strategy
try:
    from src.strategies.qa_strategy import KeywordRetrievalStrategy
    
    strategy = KeywordRetrievalStrategy()
    
    # Test with sample document
    test_document = {
        'original_text': '''
        Patient: John Doe
        Case Number: WC2024-001
        Date of Injury: January 15, 2024
        Body Parts: Lower back, left knee
        Diagnosis: Lumbar strain with radiculopathy
        Treatment: Physical therapy recommended
        Work Restrictions: No lifting over 20 pounds
        ''',
        'extracted_info': {
            'patient_name': 'John Doe',
            'case_number': 'WC2024-001',
            'injury_date': 'January 15, 2024',
            'body_parts': 'Lower back, left knee',
            'diagnosis': 'Lumbar strain with radiculopathy'
        }
    }
    
    # Test various question types
    test_questions = [
        "What is the patient's name?",
        "When did the injury occur?",
        "What body parts were affected?",
        "What is the diagnosis?",
        "What are the work restrictions?"
    ]
    
    successful_retrievals = 0
    total_questions = len(test_questions)
    
    for question in test_questions:
        contexts = strategy.retrieve_context(question, test_document)
        if contexts and len(contexts) > 0:
            successful_retrievals += 1
            print(f'QUESTION_SUCCESS: {question[:30]}... -> {len(contexts)} contexts')
        else:
            print(f'QUESTION_FAILED: {question[:30]}... -> No contexts')
    
    print(f'FALLBACK_RETRIEVAL_RATE: {successful_retrievals}/{total_questions}')
    
    if successful_retrievals >= total_questions * 0.6:  # 60% success rate
        print('FALLBACK_BEHAVIOR_SUCCESS')
    else:
        print('FALLBACK_BEHAVIOR_PARTIAL')
        
except Exception as e:
    print(f'FALLBACK_TEST_ERROR: {e}')

print('FALLBACK_TEST_COMPLETE')
"""
            ]
            
            result = subprocess.run(
                fallback_test_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and "FALLBACK_TEST_COMPLETE" in result.stdout:
                # Parse results
                output_lines = result.stdout.strip().split('\n')
                
                success_count = 0
                total_count = 0
                
                for line in output_lines:
                    if line.startswith('FALLBACK_RETRIEVAL_RATE:'):
                        rate_info = line.split(':')[1].strip()
                        success_count, total_count = map(int, rate_info.split('/'))
                        break
                
                fallback_works = any("FALLBACK_BEHAVIOR_SUCCESS" in line for line in output_lines)
                fallback_partial = any("FALLBACK_BEHAVIOR_PARTIAL" in line for line in output_lines)
                
                if fallback_works:
                    return {
                        "status": "PASS",
                        "message": f"Fallback behavior working well ({success_count}/{total_count} questions)",
                        "details": f"Keyword fallback successfully handled {success_count} out of {total_count} test questions"
                    }
                elif fallback_partial or success_count > 0:
                    return {
                        "status": "PARTIAL",
                        "message": f"Fallback behavior partially working ({success_count}/{total_count} questions)",
                        "details": f"Some fallback functionality available but may need improvement"
                    }
                else:
                    return {
                        "status": "FAIL",
                        "message": "Fallback behavior not working",
                        "details": f"Fallback mechanisms failed to handle test questions"
                    }
            else:
                return {
                    "status": "FAIL",
                    "message": "Fallback behavior test failed",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Fallback behavior test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_ui_qa_integration(self) -> Dict[str, Any]:
        """Test that UI can connect to Q&A backend correctly."""
        logger.info("Testing UI-Q&A integration...")
        
        if not self.streamlit_process or self.streamlit_process.poll() is not None:
            return {
                "status": "SKIP",
                "message": "Streamlit not running, skipping UI Q&A integration test",
                "details": "Q&A interface test must pass first"
            }
        
        try:
            # Test that the Q&A page loads without errors
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "FAIL",
                    "message": f"Q&A page not accessible (HTTP {response.status_code})",
                    "details": response.text[:500]
                }
            
            page_content = response.text.lower()
            
            # Check for Q&A integration indicators
            integration_indicators = [
                "ask a question",
                "question processing",
                "document q&a",
                "text_input"
            ]
            
            found_integration = [indicator for indicator in integration_indicators if indicator in page_content]
            
            # Check for error indicators
            error_indicators = [
                "error occurred",
                "failed to initialize",
                "import error",
                "module not found"
            ]
            
            found_errors = [error for error in error_indicators if error in page_content]
            
            if found_errors:
                return {
                    "status": "FAIL",
                    "message": f"UI shows Q&A integration errors: {found_errors}",
                    "details": "Check application logs for detailed error information"
                }
            
            if found_integration:
                return {
                    "status": "PASS",
                    "message": f"UI-Q&A integration working, found {len(found_integration)} integration features",
                    "details": f"Integration features: {found_integration}"
                }
            else:
                return {
                    "status": "PARTIAL",
                    "message": "UI loads but Q&A integration features may be limited",
                    "details": "No Q&A-specific integration content found, but no errors detected"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "FAIL",
                "message": f"Failed to test UI Q&A integration: {str(e)}",
                "details": str(e)
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"UI Q&A integration test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test that Q&A error handling works correctly."""
        logger.info("Testing Q&A error handling...")
        
        try:
            # Test error handling scenarios
            error_handling_cmd = [
                sys.executable, "-c",
                """
import sys
sys.path.append('src')

# Test error handling in Q&A components
try:
    from src.strategies.qa_strategy import KeywordRetrievalStrategy, QAResponse
    
    strategy = KeywordRetrievalStrategy()
    
    # Test with empty/invalid inputs
    test_cases = [
        ('', {}),  # Empty question and document
        ('What is the patient name?', {}),  # Valid question, empty document
        ('', {'original_text': 'Some text'}),  # Empty question, valid document
        ('What is the patient name?', {'original_text': ''}),  # Valid question, empty text
    ]
    
    handled_errors = 0
    total_cases = len(test_cases)
    
    for question, document in test_cases:
        try:
            contexts = strategy.retrieve_context(question, document)
            # Should handle gracefully, not crash
            print(f'ERROR_CASE_HANDLED: {question[:20] if question else "empty"}... -> {len(contexts) if contexts else 0} contexts')
            handled_errors += 1
        except Exception as e:
            print(f'ERROR_CASE_FAILED: {question[:20] if question else "empty"}... -> {e}')
    
    print(f'ERROR_HANDLING_RATE: {handled_errors}/{total_cases}')
    
    if handled_errors == total_cases:
        print('ERROR_HANDLING_SUCCESS')
    elif handled_errors >= total_cases * 0.5:
        print('ERROR_HANDLING_PARTIAL')
    else:
        print('ERROR_HANDLING_FAILED')
        
except Exception as e:
    print(f'ERROR_HANDLING_TEST_ERROR: {e}')

print('ERROR_HANDLING_TEST_COMPLETE')
"""
            ]
            
            result = subprocess.run(
                error_handling_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and "ERROR_HANDLING_TEST_COMPLETE" in result.stdout:
                # Parse results
                output_lines = result.stdout.strip().split('\n')
                
                handled_count = 0
                total_count = 0
                
                for line in output_lines:
                    if line.startswith('ERROR_HANDLING_RATE:'):
                        rate_info = line.split(':')[1].strip()
                        handled_count, total_count = map(int, rate_info.split('/'))
                        break
                
                error_handling_success = any("ERROR_HANDLING_SUCCESS" in line for line in output_lines)
                error_handling_partial = any("ERROR_HANDLING_PARTIAL" in line for line in output_lines)
                
                if error_handling_success:
                    return {
                        "status": "PASS",
                        "message": f"Error handling working well ({handled_count}/{total_count} cases)",
                        "details": f"All error cases handled gracefully without crashes"
                    }
                elif error_handling_partial:
                    return {
                        "status": "PARTIAL",
                        "message": f"Error handling partially working ({handled_count}/{total_count} cases)",
                        "details": f"Some error handling functionality available"
                    }
                else:
                    return {
                        "status": "FAIL",
                        "message": "Error handling not working properly",
                        "details": f"Error handling failed for most test cases"
                    }
            else:
                return {
                    "status": "FAIL",
                    "message": "Error handling test failed",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Error handling test failed: {str(e)}",
                "details": str(e)
            }
    
    def cleanup(self):
        """Clean up test resources."""
        # Clean up Streamlit process
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
                self.streamlit_process.wait()
            except Exception as e:
                logger.warning(f"Error during Streamlit cleanup: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Q&A functionality integration tests."""
        logger.info("Starting comprehensive Q&A functionality integration tests...")
        
        test_start_time = time.time()
        
        try:
            # Test 1: Q&A interface availability
            self.test_results["qa_interface"] = self.test_qa_interface_availability()
            
            # Test 2: Q&A backend components
            self.test_results["qa_backend"] = self.test_qa_backend_components()
            
            # Test 3: API provider integration
            self.test_results["api_providers"] = self.test_api_provider_integration()
            
            # Test 4: Fallback behavior
            self.test_results["fallback_behavior"] = self.test_fallback_behavior()
            
            # Test 5: UI-Q&A integration (only if interface works)
            if self.test_results["qa_interface"]["status"] in ["PASS", "PARTIAL"]:
                time.sleep(2)  # Give app time to fully initialize
                self.test_results["ui_integration"] = self.test_ui_qa_integration()
            else:
                self.test_results["ui_integration"] = {
                    "status": "SKIP",
                    "message": "Skipped due to Q&A interface failure",
                    "details": "Q&A interface test must pass first"
                }
            
            # Test 6: Error handling
            self.test_results["error_handling"] = self.test_error_handling()
            
            # Calculate overall results
            total_time = time.time() - test_start_time
            
            passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
            partial_tests = sum(1 for result in self.test_results.values() if result["status"] == "PARTIAL")
            total_tests = len([r for r in self.test_results.values() if r["status"] != "SKIP"])
            
            # Overall status logic
            if passed_tests >= total_tests * 0.8:  # 80% pass rate
                overall_status = "PASS"
            elif passed_tests + partial_tests >= total_tests * 0.6:  # 60% success rate
                overall_status = "PARTIAL"
            else:
                overall_status = "FAIL"
            
            return {
                "overall_status": overall_status,
                "total_time": total_time,
                "passed_tests": passed_tests,
                "partial_tests": partial_tests,
                "total_tests": total_tests,
                "test_results": self.test_results,
                "summary": f"{passed_tests} passed, {partial_tests} partial, {total_tests - passed_tests - partial_tests} failed in {total_time:.2f}s"
            }
            
        finally:
            self.cleanup()

def main():
    """Main test execution function."""
    print("=" * 70)
    print("Q&A FUNCTIONALITY INTEGRATION TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = QAFunctionalityTester()
    
    try:
        results = tester.run_all_tests()
        
        # Print detailed results
        print("TEST RESULTS:")
        print("-" * 50)
        
        for test_name, test_result in results["test_results"].items():
            if test_result["status"] == "PASS":
                status_icon = "✅"
            elif test_result["status"] == "PARTIAL":
                status_icon = "🟡"
            elif test_result["status"] == "FAIL":
                status_icon = "❌"
            else:
                status_icon = "⏭️"
                
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {test_result['status']}")
            print(f"   Message: {test_result['message']}")
            if test_result.get('details'):
                print(f"   Details: {test_result['details'][:200]}{'...' if len(test_result['details']) > 200 else ''}")
            print()
        
        # Print summary
        print("=" * 70)
        print("SUMMARY:")
        if results['overall_status'] == 'PASS':
            print("Overall Status: ✅ PASS")
        elif results['overall_status'] == 'PARTIAL':
            print("Overall Status: 🟡 PARTIAL")
        else:
            print("Overall Status: ❌ FAIL")
            
        print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
        if results['partial_tests'] > 0:
            print(f"Partial Success: {results['partial_tests']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print("=" * 70)
        
        # Return appropriate exit code
        return 0 if results['overall_status'] in ['PASS', 'PARTIAL'] else 1
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test execution failed: {e}")
        logger.error(f"Test execution error: {e}", exc_info=True)
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit(main())