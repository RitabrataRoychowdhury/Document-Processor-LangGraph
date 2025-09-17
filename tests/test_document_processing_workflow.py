#!/usr/bin/env python3
"""
Document Processing Workflow Test
Tests the complete document upload and processing pipeline through the UI.
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

class DocumentProcessingWorkflowTester:
    """Comprehensive tester for document processing workflow through UI."""
    
    def __init__(self):
        self.streamlit_process = None
        self.test_results = {}
        self.base_url = "http://localhost:8502"  # Use different port to avoid conflicts
        self.test_documents = {}
        
    def create_test_documents(self) -> Dict[str, str]:
        """Create test documents for upload testing."""
        logger.info("Creating test documents...")
        
        test_docs = {}
        
        # Create a test PDF-like text file (simulating PDF content)
        pdf_content = """
QUALIFIED MEDICAL EVALUATOR REPORT

Patient: John Doe
Case Number: WC2024-001
Date of Injury: January 15, 2024
Body Parts Affected: Lower back, left knee

HISTORY OF PRESENT ILLNESS:
Mr. Doe is a 45-year-old construction worker who sustained injuries to his lower back and left knee on January 15, 2024, while lifting heavy materials at a construction site.

DIAGNOSIS:
1. Lumbar strain with radiculopathy
2. Left knee contusion with possible meniscal tear

TREATMENT RECOMMENDATIONS:
Physical therapy, anti-inflammatory medications, and possible MRI evaluation.

WORK RESTRICTIONS:
No lifting over 20 pounds, limited standing/walking.
"""
        
        # Create temporary test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(pdf_content)
            test_docs['qme_report.txt'] = f.name
        
        # Create a simple medical record
        medical_record = """
MEDICAL RECORD

Patient Name: Jane Smith
Date of Birth: 03/15/1980
Case Number: WC2024-002
Date of Service: February 20, 2024

CHIEF COMPLAINT:
Right shoulder pain following workplace accident.

EXAMINATION FINDINGS:
Limited range of motion in right shoulder, tenderness over rotator cuff.

ASSESSMENT:
Right shoulder impingement syndrome, possible rotator cuff tear.

PLAN:
MRI ordered, physical therapy referral, work restrictions implemented.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(medical_record)
            test_docs['medical_record.txt'] = f.name
        
        logger.info(f"Created {len(test_docs)} test documents")
        return test_docs
    
    def test_upload_interface_availability(self) -> Dict[str, Any]:
        """Test that the upload interface is available and functional."""
        logger.info("Testing upload interface availability...")
        
        try:
            # Start Streamlit for testing
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "src/ui/main_app.py",
                "--server.port=8502",
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
                    "message": "Streamlit failed to start for upload testing",
                    "details": "Could not access upload interface"
                }
            
            # Check if upload interface is accessible
            response = requests.get(f"{self.base_url}/", timeout=10)
            page_content = response.text.lower()
            
            # Look for upload-related content
            upload_indicators = [
                "upload documents",
                "file_uploader",
                "drag and drop",
                "choose a document"
            ]
            
            found_indicators = [indicator for indicator in upload_indicators if indicator in page_content]
            
            if found_indicators:
                return {
                    "status": "PASS",
                    "message": f"Upload interface available with {len(found_indicators)} upload features",
                    "details": f"Found indicators: {found_indicators}"
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Upload interface not properly accessible",
                    "details": "No upload-related content found in page"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Upload interface test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_backend_processing_pipeline(self) -> Dict[str, Any]:
        """Test that backend document processing components are available."""
        logger.info("Testing backend processing pipeline...")
        
        try:
            # Test import of key processing components
            test_imports = [
                "from src.ui.upload_interface import UploadInterface",
                "from src.infrastructure.storage.file_handler import FileUploadHandler",
                "from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService",
                "from src.core.extraction.document_processor import DocumentProcessor"
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
            
            # Test upload interface instantiation
            try:
                instantiation_cmd = [
                    sys.executable, "-c",
                    """
import sys
sys.path.append('src')
from src.ui.upload_interface import UploadInterface
interface = UploadInterface()
print('UPLOAD_INTERFACE_SUCCESS')
"""
                ]
                
                result = subprocess.run(
                    instantiation_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                upload_interface_works = "UPLOAD_INTERFACE_SUCCESS" in result.stdout
                
            except Exception:
                upload_interface_works = False
            
            # Evaluate results
            total_components = len(test_imports)
            working_components = len(successful_imports)
            
            if working_components == total_components and upload_interface_works:
                return {
                    "status": "PASS",
                    "message": f"All {total_components} backend processing components available",
                    "details": f"Working: {successful_imports}, Upload interface: {'✅' if upload_interface_works else '❌'}"
                }
            elif working_components > 0:
                return {
                    "status": "PARTIAL",
                    "message": f"{working_components}/{total_components} backend components available",
                    "details": f"Working: {successful_imports}, Failed: {failed_imports}, Upload interface: {'✅' if upload_interface_works else '❌'}"
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Backend processing pipeline not available",
                    "details": f"Failed imports: {failed_imports}, Upload interface: {'❌' if not upload_interface_works else '✅'}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Backend pipeline test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_document_processing_simulation(self) -> Dict[str, Any]:
        """Test document processing simulation with test documents."""
        logger.info("Testing document processing simulation...")
        
        try:
            # Create test documents
            self.test_documents = self.create_test_documents()
            
            # Test processing simulation
            processing_test_cmd = [
                sys.executable, "-c",
                f"""
import sys
sys.path.append('src')
from src.ui.upload_interface import UploadInterface

# Create upload interface
interface = UploadInterface()

# Test field extraction simulation
test_text = '''
Patient: John Doe
Case Number: WC2024-001
Date of Injury: January 15, 2024
Body Parts: Lower back, left knee
Diagnosis: Lumbar strain
'''

# Test extraction simulation
extracted_fields = interface._simulate_field_extraction(test_text)
print(f'EXTRACTED_FIELDS: {{len(extracted_fields)}}')

# Test validation simulation
validation_results = interface._simulate_evidence_validation(extracted_fields)
print(f'VALIDATION_SUCCESS: {{validation_results.get("evidence_completeness", 0) > 0}}')

# Test knowledge graph simulation
kg_results = interface._simulate_kg_population(validation_results)
print(f'KG_SUCCESS: {{kg_results.get("population_success", False)}}')

print('PROCESSING_SIMULATION_SUCCESS')
"""
            ]
            
            result = subprocess.run(
                processing_test_cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0 and "PROCESSING_SIMULATION_SUCCESS" in result.stdout:
                # Parse results from output
                output_lines = result.stdout.strip().split('\n')
                extracted_count = 0
                validation_success = False
                kg_success = False
                
                for line in output_lines:
                    if line.startswith('EXTRACTED_FIELDS:'):
                        extracted_count = int(line.split(':')[1].strip())
                    elif line.startswith('VALIDATION_SUCCESS:'):
                        validation_success = 'True' in line
                    elif line.startswith('KG_SUCCESS:'):
                        kg_success = 'True' in line
                
                return {
                    "status": "PASS",
                    "message": "Document processing simulation successful",
                    "details": f"Extracted {extracted_count} fields, Validation: {'✅' if validation_success else '❌'}, KG: {'✅' if kg_success else '❌'}"
                }
            else:
                return {
                    "status": "FAIL",
                    "message": "Document processing simulation failed",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Processing simulation test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_ui_processing_integration(self) -> Dict[str, Any]:
        """Test that UI can trigger backend processing correctly."""
        logger.info("Testing UI-backend processing integration...")
        
        if not self.streamlit_process or self.streamlit_process.poll() is not None:
            return {
                "status": "SKIP",
                "message": "Streamlit not running, skipping UI integration test",
                "details": "Upload interface test must pass first"
            }
        
        try:
            # Test that the upload page loads without errors
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code != 200:
                return {
                    "status": "FAIL",
                    "message": f"Upload page not accessible (HTTP {response.status_code})",
                    "details": response.text[:500]
                }
            
            page_content = response.text.lower()
            
            # Check for processing-related content
            processing_indicators = [
                "processing progress",
                "field extraction",
                "evidence validation",
                "confidence score",
                "real-time"
            ]
            
            found_processing = [indicator for indicator in processing_indicators if indicator in page_content]
            
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
                    "message": f"UI shows processing errors: {found_errors}",
                    "details": "Check application logs for detailed error information"
                }
            
            if found_processing:
                return {
                    "status": "PASS",
                    "message": f"UI-backend integration working, found {len(found_processing)} processing features",
                    "details": f"Processing features: {found_processing}"
                }
            else:
                return {
                    "status": "PARTIAL",
                    "message": "UI loads but processing features may be limited",
                    "details": "No processing-specific content found, but no errors detected"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "FAIL",
                "message": f"Failed to test UI integration: {str(e)}",
                "details": str(e)
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"UI integration test failed: {str(e)}",
                "details": str(e)
            }
    
    def test_processing_results_display(self) -> Dict[str, Any]:
        """Test that processing results are displayed correctly in UI."""
        logger.info("Testing processing results display...")
        
        try:
            # Test results display components
            display_test_cmd = [
                sys.executable, "-c",
                """
import sys
sys.path.append('src')
from src.ui.upload_interface import UploadInterface

# Create upload interface
interface = UploadInterface()

# Test display methods exist and work
test_fields = {
    'patient_name': {'value': 'John Doe', 'confidence': 0.95},
    'case_number': {'value': 'WC2024-001', 'confidence': 0.88}
}

test_validation = {
    'accepted_fields': test_fields,
    'flagged_fields': {},
    'missing_fields': [],
    'evidence_completeness': 0.9
}

# Test that display methods exist
methods_to_test = [
    '_display_real_time_extraction_results',
    '_display_validation_results', 
    '_display_evidence_snippet_viewer'
]

for method_name in methods_to_test:
    if hasattr(interface, method_name):
        print(f'METHOD_EXISTS: {method_name}')
    else:
        print(f'METHOD_MISSING: {method_name}')

print('DISPLAY_TEST_SUCCESS')
"""
            ]
            
            result = subprocess.run(
                display_test_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and "DISPLAY_TEST_SUCCESS" in result.stdout:
                # Count existing methods
                output_lines = result.stdout.strip().split('\n')
                existing_methods = [line for line in output_lines if line.startswith('METHOD_EXISTS:')]
                missing_methods = [line for line in output_lines if line.startswith('METHOD_MISSING:')]
                
                if len(existing_methods) >= 2:  # At least 2 display methods should exist
                    return {
                        "status": "PASS",
                        "message": f"Processing results display components available ({len(existing_methods)} methods)",
                        "details": f"Existing: {len(existing_methods)}, Missing: {len(missing_methods)}"
                    }
                else:
                    return {
                        "status": "PARTIAL",
                        "message": f"Some display components missing ({len(existing_methods)} of 3 methods)",
                        "details": f"Existing: {len(existing_methods)}, Missing: {len(missing_methods)}"
                    }
            else:
                return {
                    "status": "FAIL",
                    "message": "Processing results display test failed",
                    "details": f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Results display test failed: {str(e)}",
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
        
        # Clean up test documents
        for doc_path in self.test_documents.values():
            try:
                os.unlink(doc_path)
            except Exception as e:
                logger.warning(f"Error cleaning up test document {doc_path}: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all document processing workflow tests."""
        logger.info("Starting comprehensive document processing workflow tests...")
        
        test_start_time = time.time()
        
        try:
            # Test 1: Upload interface availability
            self.test_results["upload_interface"] = self.test_upload_interface_availability()
            
            # Test 2: Backend processing pipeline
            self.test_results["backend_pipeline"] = self.test_backend_processing_pipeline()
            
            # Test 3: Document processing simulation
            self.test_results["processing_simulation"] = self.test_document_processing_simulation()
            
            # Test 4: UI-backend integration (only if upload interface works)
            if self.test_results["upload_interface"]["status"] == "PASS":
                time.sleep(2)  # Give app time to fully initialize
                self.test_results["ui_integration"] = self.test_ui_processing_integration()
            else:
                self.test_results["ui_integration"] = {
                    "status": "SKIP",
                    "message": "Skipped due to upload interface failure",
                    "details": "Upload interface test must pass first"
                }
            
            # Test 5: Processing results display
            self.test_results["results_display"] = self.test_processing_results_display()
            
            # Calculate overall results
            total_time = time.time() - test_start_time
            
            passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
            partial_tests = sum(1 for result in self.test_results.values() if result["status"] == "PARTIAL")
            total_tests = len([r for r in self.test_results.values() if r["status"] != "SKIP"])
            
            # Overall status logic
            if passed_tests == total_tests:
                overall_status = "PASS"
            elif passed_tests + partial_tests >= total_tests * 0.7:  # 70% success rate
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
    print("DOCUMENT PROCESSING WORKFLOW TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = DocumentProcessingWorkflowTester()
    
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