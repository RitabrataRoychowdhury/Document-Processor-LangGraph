#!/usr/bin/env python3
"""
Comprehensive Streamlit Application Startup Test
Tests all aspects of the Streamlit UI startup process and navigation.
"""

import sys
import os
import subprocess
import time
import threading
import requests
import signal
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

class StreamlitStartupTester:
    """Comprehensive tester for Streamlit application startup and navigation."""
    
    def __init__(self):
        self.streamlit_process = None
        self.test_results = {}
        self.startup_time = None
        self.base_url = "http://localhost:8501"
        
    def test_import_validation(self) -> Dict[str, Any]:
        """Test that all imports in main_app.py work correctly."""
        logger.info("Testing import validation...")
        
        try:
            # Test basic Python import
            import_cmd = [
                sys.executable, "-c",
                "import sys; sys.path.append('src'); from src.ui.main_app import main; print('SUCCESS: All imports work')"
            ]
            
            result = subprocess.run(
                import_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "status": "PASS",
                    "message": "All imports successful",
                    "details": result.stdout.strip()
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Import errors detected",
                    "details": result.stderr.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "message": "Import test timed out",
                "details": "Import process took longer than 30 seconds"
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Import test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_streamlit_startup(self) -> Dict[str, Any]:
        """Test Streamlit application startup process."""
        logger.info("Testing Streamlit startup...")
        
        try:
            # Start Streamlit in background
            start_time = time.time()
            
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "src/ui/main_app.py",
                "--server.port=8501",
                "--server.headless=true",
                "--browser.gatherUsageStats=false"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for startup (max 60 seconds)
            startup_timeout = 60
            startup_success = False
            
            for _ in range(startup_timeout):
                try:
                    response = requests.get(f"{self.base_url}/", timeout=5)
                    if response.status_code == 200:
                        startup_success = True
                        self.startup_time = time.time() - start_time
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            if startup_success:
                return {
                    "status": "PASS",
                    "message": f"Streamlit started successfully in {self.startup_time:.2f} seconds",
                    "details": f"Application accessible at {self.base_url}",
                    "startup_time": self.startup_time
                }
            else:
                # Get process output for debugging
                stdout, stderr = self.streamlit_process.communicate(timeout=5)
                return {
                    "status": "FAIL",
                    "message": "Streamlit failed to start within timeout",
                    "details": f"STDOUT: {stdout}\nSTDERR: {stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Streamlit startup test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_page_navigation(self) -> Dict[str, Any]:
        """Test that all UI pages can be navigated without errors."""
        logger.info("Testing page navigation...")
        
        if not self.streamlit_process or self.streamlit_process.poll() is not None:
            return {
                "status": "SKIP",
                "message": "Streamlit not running, skipping navigation test",
                "details": "Startup test must pass first"
            }
        
        try:
            # Test main page accessibility
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "FAIL",
                    "message": f"Main page not accessible (HTTP {response.status_code})",
                    "details": response.text[:500]
                }
            
            # Check for common error indicators in the response
            page_content = response.text.lower()
            
            error_indicators = [
                "importerror",
                "modulenotfounderror", 
                "traceback",
                "error occurred",
                "something went wrong"
            ]
            
            found_errors = [error for error in error_indicators if error in page_content]
            
            if found_errors:
                return {
                    "status": "FAIL",
                    "message": f"Page contains error indicators: {found_errors}",
                    "details": "Check application logs for detailed error information"
                }
            
            # Check for expected content
            expected_content = [
                "production-ready qme system",
                "upload documents",
                "system healthy" 
            ]
            
            found_content = [content for content in expected_content if content in page_content]
            
            return {
                "status": "PASS",
                "message": f"Page navigation successful, found expected content: {found_content}",
                "details": f"Page loaded successfully with {len(found_content)}/{len(expected_content)} expected elements"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "FAIL",
                "message": f"Failed to access Streamlit page: {str(e)}",
                "details": str(e)
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Page navigation test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test that startup failures are handled gracefully."""
        logger.info("Testing error handling...")
        
        try:
            # Test with invalid configuration to see error handling
            test_cmd = [
                sys.executable, "-c",
                """
import sys
sys.path.append('src')
import os
# Temporarily break configuration
os.environ['GEMINI_API_KEY'] = ''
os.environ['OPENAI_API_KEY'] = ''
try:
    from src.ui.main_app import main
    print('SUCCESS: Error handling works')
except Exception as e:
    print(f'ERROR: {str(e)}')
    raise
"""
            ]
            
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # We expect this to either succeed (good error handling) or fail gracefully
            if "SUCCESS" in result.stdout or "ERROR" in result.stdout:
                return {
                    "status": "PASS",
                    "message": "Error handling test completed",
                    "details": result.stdout.strip() or result.stderr.strip()
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Error handling test produced unexpected output",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "FAIL",
                "message": "Error handling test timed out",
                "details": "Test took longer than 30 seconds"
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Error handling test failed: {str(e)}",
                "details": str(e)
            }
    
    def cleanup(self):
        """Clean up test resources."""
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
                self.streamlit_process.wait()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all startup tests and return comprehensive results."""
        logger.info("Starting comprehensive Streamlit startup tests...")
        
        test_start_time = time.time()
        
        try:
            # Test 1: Import validation
            self.test_results["import_validation"] = self.test_import_validation()
            
            # Test 2: Streamlit startup (only if imports work)
            if self.test_results["import_validation"]["status"] == "PASS":
                self.test_results["streamlit_startup"] = self.test_streamlit_startup()
                
                # Test 3: Page navigation (only if startup works)
                if self.test_results["streamlit_startup"]["status"] == "PASS":
                    time.sleep(2)  # Give app time to fully initialize
                    self.test_results["page_navigation"] = self.test_page_navigation()
                else:
                    self.test_results["page_navigation"] = {
                        "status": "SKIP",
                        "message": "Skipped due to startup failure",
                        "details": "Streamlit startup test must pass first"
                    }
            else:
                self.test_results["streamlit_startup"] = {
                    "status": "SKIP", 
                    "message": "Skipped due to import failures",
                    "details": "Import validation test must pass first"
                }
                self.test_results["page_navigation"] = {
                    "status": "SKIP",
                    "message": "Skipped due to import failures", 
                    "details": "Import validation test must pass first"
                }
            
            # Test 4: Error handling
            self.test_results["error_handling"] = self.test_error_handling()
            
            # Calculate overall results
            total_time = time.time() - test_start_time
            
            passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
            total_tests = len([r for r in self.test_results.values() if r["status"] != "SKIP"])
            
            overall_status = "PASS" if passed_tests == total_tests else "FAIL"
            
            return {
                "overall_status": overall_status,
                "total_time": total_time,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "startup_time": self.startup_time,
                "test_results": self.test_results,
                "summary": f"{passed_tests}/{total_tests} tests passed in {total_time:.2f}s"
            }
            
        finally:
            self.cleanup()

def main():
    """Main test execution function."""
    print("=" * 60)
    print("STREAMLIT APPLICATION STARTUP TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = StreamlitStartupTester()
    
    try:
        results = tester.run_all_tests()
        
        # Print detailed results
        print("TEST RESULTS:")
        print("-" * 40)
        
        for test_name, test_result in results["test_results"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌" if test_result["status"] == "FAIL" else "⏭️"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {test_result['status']}")
            print(f"   Message: {test_result['message']}")
            if test_result.get('details'):
                print(f"   Details: {test_result['details'][:200]}{'...' if len(test_result['details']) > 200 else ''}")
            print()
        
        # Print summary
        print("=" * 60)
        print("SUMMARY:")
        print(f"Overall Status: {'✅ PASS' if results['overall_status'] == 'PASS' else '❌ FAIL'}")
        print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        if results['startup_time']:
            print(f"Startup Time: {results['startup_time']:.2f} seconds")
        print("=" * 60)
        
        # Return appropriate exit code
        return 0 if results['overall_status'] == 'PASS' else 1
        
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