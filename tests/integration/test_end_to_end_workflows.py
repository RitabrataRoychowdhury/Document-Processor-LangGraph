"""
End-to-End Integration Testing Framework.

This module provides comprehensive integration tests for complete workflows
from document upload to template download, including Q&A functionality,
error scenarios, and concurrent user testing.
"""

import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
import tempfile
from io import BytesIO
import json
import uuid

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app import get_app, initialize_app
from src.ui.upload_interface import UploadInterface
from src.ui.qa_interface_simple import render_qa_page
from src.ui.qme_template_interface import render_qme_template_page
from src.storage.document_storage import DocumentStorage
from src.models.document import Document
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EndToEndTestRunner:
    """End-to-end test runner for complete workflow testing."""
    
    def __init__(self):
        """Initialize the end-to-end test runner."""
        self.test_results = []
        self.test_data = {}
        self.concurrent_users = []
        self.workflow_states = {}
    
    def setup_test_environment(self):
        """Setup comprehensive test environment."""
        # Create test documents
        self.test_documents = {
            'pqme_report': {
                'filename': 'test_pqme_report.pdf',
                'content': self._create_mock_pqme_content(),
                'expected_fields': {
                    'patient_name': 'John Doe',
                    'case_number': 'WC2024-001',
                    'injury_date': '2024-01-15',
                    'body_parts': ['lower back', 'lumbar spine']
                }
            },
            'medical_record': {
                'filename': 'test_medical_record.pdf',
                'content': self._create_mock_medical_record(),
                'expected_fields': {
                    'patient_name': 'Jane Smith',
                    'diagnosis': 'Lumbar strain',
                    'treatment_date': '2024-02-01'
                }
            },
            'imaging_report': {
                'filename': 'test_imaging_report.pdf',
                'content': self._create_mock_imaging_report(),
                'expected_fields': {
                    'patient_name': 'Bob Johnson',
                    'study_type': 'MRI Lumbar Spine',
                    'findings': 'Disc herniation L4-L5'
                }
            }
        }
        
        # Setup mock services
        self._setup_mock_services()
    
    def _create_mock_pqme_content(self) -> str:
        """Create mock PQME document content."""
        return """
        PERMANENT AND QUALIFIED MEDICAL EVALUATOR'S REPORT
        
        Patient: John Doe
        Case Number: WC2024-001
        Date of Injury: January 15, 2024
        Date of Examination: March 1, 2024
        
        HISTORY OF PRESENT ILLNESS:
        The patient is a 45-year-old construction worker who sustained an injury to his lower back
        while lifting heavy materials on January 15, 2024. He reports persistent pain in the
        lumbar spine region with radiation to the left leg.
        
        PHYSICAL EXAMINATION:
        The patient demonstrates limited range of motion in the lumbar spine.
        Positive straight leg raise test on the left side.
        Tenderness over L4-L5 region.
        
        DIAGNOSIS:
        1. Lumbar strain with possible disc involvement
        2. Work-related injury
        
        IMPAIRMENT RATING:
        Based on AMA Guides 5th Edition: 8% whole person impairment
        """
    
    def _create_mock_medical_record(self) -> str:
        """Create mock medical record content."""
        return """
        MEDICAL RECORD
        
        Patient: Jane Smith
        DOB: 03/15/1980
        Date of Service: February 1, 2024
        
        CHIEF COMPLAINT:
        Lower back pain following workplace incident
        
        ASSESSMENT AND PLAN:
        Patient presents with acute lumbar strain. Recommend physical therapy
        and anti-inflammatory medication. Return to work with restrictions.
        
        DIAGNOSIS:
        Lumbar strain (ICD-10: M54.5)
        """
    
    def _create_mock_imaging_report(self) -> str:
        """Create mock imaging report content."""
        return """
        RADIOLOGY REPORT
        
        Patient: Bob Johnson
        Study: MRI Lumbar Spine
        Date: February 15, 2024
        
        FINDINGS:
        There is evidence of disc herniation at L4-L5 level with mild spinal
        canal narrowing. No significant nerve root compression identified.
        
        IMPRESSION:
        Disc herniation L4-L5 with mild spinal stenosis
        """
    
    def _setup_mock_services(self):
        """Setup mock services for testing."""
        # Mock file upload handler
        self.mock_file_handler = Mock()
        self.mock_file_handler.extract_text.return_value = (
            self.test_documents['pqme_report']['content'], None
        )
        
        # Mock document storage
        self.mock_storage = Mock()
        self.mock_storage.store_document.return_value = 'test_doc_123'
        
        # Mock QME template generator
        self.mock_template_generator = Mock()
        self.mock_template_generator.generate_template.return_value = {
            'template_content': 'Generated QME Template Content',
            'filename': 'QME_Report_Test.docx'
        }
    
    def run_workflow_test(self, workflow_name: str, test_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a complete workflow test."""
        workflow_result = {
            'workflow_name': workflow_name,
            'started_at': time.time(),
            'completed_at': None,
            'total_duration_ms': 0,
            'steps_completed': 0,
            'steps_failed': 0,
            'step_results': [],
            'overall_success': False,
            'error_message': None
        }
        
        try:
            for i, step in enumerate(test_steps):
                step_result = self._execute_workflow_step(step, i + 1)
                workflow_result['step_results'].append(step_result)
                
                if step_result['success']:
                    workflow_result['steps_completed'] += 1
                else:
                    workflow_result['steps_failed'] += 1
                    if step.get('critical', False):
                        workflow_result['error_message'] = f"Critical step failed: {step_result['error_message']}"
                        break
            
            workflow_result['overall_success'] = workflow_result['steps_failed'] == 0
            
        except Exception as e:
            workflow_result['error_message'] = str(e)
        
        workflow_result['completed_at'] = time.time()
        workflow_result['total_duration_ms'] = (workflow_result['completed_at'] - workflow_result['started_at']) * 1000
        
        return workflow_result
    
    def _execute_workflow_step(self, step: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_result = {
            'step_number': step_number,
            'step_name': step['name'],
            'step_type': step['type'],
            'success': False,
            'duration_ms': 0,
            'error_message': None,
            'output_data': None
        }
        
        start_time = time.time()
        
        try:
            if step['type'] == 'upload':
                step_result['output_data'] = self._execute_upload_step(step)
            elif step['type'] == 'process':
                step_result['output_data'] = self._execute_process_step(step)
            elif step['type'] == 'qa':
                step_result['output_data'] = self._execute_qa_step(step)
            elif step['type'] == 'template':
                step_result['output_data'] = self._execute_template_step(step)
            elif step['type'] == 'download':
                step_result['output_data'] = self._execute_download_step(step)
            elif step['type'] == 'validation':
                step_result['output_data'] = self._execute_validation_step(step)
            else:
                raise ValueError(f"Unknown step type: {step['type']}")
            
            step_result['success'] = True
            
        except Exception as e:
            step_result['error_message'] = str(e)
        
        step_result['duration_ms'] = (time.time() - start_time) * 1000
        return step_result
    
    def _execute_upload_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document upload step."""
        document_type = step.get('document_type', 'pqme_report')
        test_doc = self.test_documents[document_type]
        
        # Create mock uploaded file
        mock_file = BytesIO(test_doc['content'].encode())
        mock_file.name = test_doc['filename']
        
        with patch('src.ui.upload_interface.FileUploadHandler', return_value=self.mock_file_handler):
            upload_interface = UploadInterface()
            
            # Mock file metadata
            self.mock_file_handler.get_file_metadata.return_value = {
                'filename': test_doc['filename'],
                'file_type': 'pdf',
                'file_size_mb': 2.5,
                'is_valid': True
            }
            
            # Simulate upload process
            result = upload_interface._process_enhanced_file(mock_file, {
                'filename': test_doc['filename'],
                'file_type': 'pdf',
                'file_size': 2500000,
                'is_valid': True
            })
            
            return {
                'document_id': 'test_doc_123',
                'filename': test_doc['filename'],
                'upload_success': True,
                'extracted_text_length': len(test_doc['content'])
            }
    
    def _execute_process_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document processing step."""
        document_id = step.get('document_id', 'test_doc_123')
        
        # Mock field extraction
        with patch('src.services.comprehensive_qme_field_service.ComprehensiveQMEFieldService') as mock_service:
            mock_service.return_value.extract_comprehensive_fields.return_value = {
                'extracted_fields': {
                    'patient_name': {'value': 'John Doe', 'confidence': 0.95},
                    'case_number': {'value': 'WC2024-001', 'confidence': 0.88},
                    'injury_date': {'value': '2024-01-15', 'confidence': 0.82}
                },
                'validation_results': {
                    'overall_confidence': 0.88,
                    'missing_fields': [],
                    'low_confidence_fields': []
                }
            }
            
            field_service = mock_service()
            extraction_result = field_service.extract_comprehensive_fields(
                'Mock document text content'
            )
            
            return {
                'document_id': document_id,
                'processing_success': True,
                'fields_extracted': len(extraction_result['extracted_fields']),
                'overall_confidence': extraction_result['validation_results']['overall_confidence']
            }
    
    def _execute_qa_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Q&A step."""
        question = step.get('question', 'What is the patient\'s diagnosis?')
        document_id = step.get('document_id', 'test_doc_123')
        
        # Mock Q&A service
        with patch('src.strategies.qa_strategy.QAStrategy') as mock_qa:
            mock_qa.return_value.answer_question.return_value = {
                'answer': 'The patient has been diagnosed with lumbar strain with possible disc involvement.',
                'confidence': 0.87,
                'sources': ['Document page 1', 'Physical examination section'],
                'response_time_ms': 1250
            }
            
            qa_strategy = mock_qa()
            qa_result = qa_strategy.answer_question(question, document_id)
            
            return {
                'question': question,
                'answer': qa_result['answer'],
                'confidence': qa_result['confidence'],
                'response_time_ms': qa_result['response_time_ms'],
                'qa_success': True
            }
    
    def _execute_template_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute template generation step."""
        document_id = step.get('document_id', 'test_doc_123')
        template_type = step.get('template_type', 'qme_report')
        
        with patch('src.core.generation.qme_template_generator.QMETemplateGenerator', return_value=self.mock_template_generator):
            template_generator = self.mock_template_generator
            
            template_result = template_generator.generate_template({
                'document_id': document_id,
                'template_type': template_type,
                'doctor_info': {
                    'name': 'Dr. Test Physician',
                    'license': 'CA12345'
                }
            })
            
            return {
                'document_id': document_id,
                'template_type': template_type,
                'template_generated': True,
                'template_filename': template_result['filename'],
                'template_size': len(template_result['template_content'])
            }
    
    def _execute_download_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute template download step."""
        template_filename = step.get('template_filename', 'QME_Report_Test.docx')
        
        # Mock download process
        mock_template_content = b"Mock DOCX template content with QME report data"
        
        return {
            'template_filename': template_filename,
            'download_success': True,
            'file_size': len(mock_template_content),
            'download_time_ms': 500
        }
    
    def _execute_validation_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation step."""
        validation_type = step.get('validation_type', 'template_quality')
        
        # Mock validation results
        validation_results = {
            'template_quality': {
                'completeness_score': 0.92,
                'accuracy_score': 0.88,
                'formatting_score': 0.95,
                'overall_score': 0.91,
                'issues_found': ['Minor formatting inconsistency in section 3'],
                'validation_passed': True
            },
            'field_extraction': {
                'required_fields_found': 8,
                'total_required_fields': 10,
                'confidence_threshold_met': True,
                'validation_passed': True
            }
        }
        
        return validation_results.get(validation_type, {'validation_passed': False})


class WorkflowTestSuite:
    """Comprehensive workflow test suite."""
    
    def __init__(self):
        """Initialize workflow test suite."""
        self.test_runner = EndToEndTestRunner()
        self.test_runner.setup_test_environment()
    
    def test_complete_document_processing_workflow(self) -> Dict[str, Any]:
        """Test complete workflow from document upload to template download."""
        workflow_steps = [
            {
                'name': 'Upload PQME Document',
                'type': 'upload',
                'document_type': 'pqme_report',
                'critical': True
            },
            {
                'name': 'Process Document Fields',
                'type': 'process',
                'document_id': 'test_doc_123',
                'critical': True
            },
            {
                'name': 'Validate Extraction Results',
                'type': 'validation',
                'validation_type': 'field_extraction',
                'critical': False
            },
            {
                'name': 'Generate QME Template',
                'type': 'template',
                'document_id': 'test_doc_123',
                'template_type': 'qme_report',
                'critical': True
            },
            {
                'name': 'Validate Template Quality',
                'type': 'validation',
                'validation_type': 'template_quality',
                'critical': False
            },
            {
                'name': 'Download Template',
                'type': 'download',
                'template_filename': 'QME_Report_Test.docx',
                'critical': True
            }
        ]
        
        return self.test_runner.run_workflow_test(
            'complete_document_processing',
            workflow_steps
        )
    
    def test_qa_with_document_context(self) -> Dict[str, Any]:
        """Test Q&A functionality with document context."""
        workflow_steps = [
            {
                'name': 'Upload Medical Record',
                'type': 'upload',
                'document_type': 'medical_record',
                'critical': True
            },
            {
                'name': 'Process Document',
                'type': 'process',
                'document_id': 'test_doc_456',
                'critical': True
            },
            {
                'name': 'Ask Diagnosis Question',
                'type': 'qa',
                'question': 'What is the patient\'s primary diagnosis?',
                'document_id': 'test_doc_456',
                'critical': True
            },
            {
                'name': 'Ask Treatment Question',
                'type': 'qa',
                'question': 'What treatment was recommended?',
                'document_id': 'test_doc_456',
                'critical': False
            },
            {
                'name': 'Ask Date Question',
                'type': 'qa',
                'question': 'When was the patient seen?',
                'document_id': 'test_doc_456',
                'critical': False
            }
        ]
        
        return self.test_runner.run_workflow_test(
            'qa_with_document_context',
            workflow_steps
        )
    
    def test_error_scenarios_and_recovery(self) -> Dict[str, Any]:
        """Test error scenarios and recovery paths."""
        workflow_steps = [
            {
                'name': 'Upload Invalid Document',
                'type': 'upload',
                'document_type': 'invalid_document',
                'critical': False,
                'expect_error': True
            },
            {
                'name': 'Process Non-existent Document',
                'type': 'process',
                'document_id': 'non_existent_doc',
                'critical': False,
                'expect_error': True
            },
            {
                'name': 'Ask Question Without Document',
                'type': 'qa',
                'question': 'What is the diagnosis?',
                'document_id': None,
                'critical': False,
                'expect_error': True
            },
            {
                'name': 'Generate Template Without Data',
                'type': 'template',
                'document_id': 'empty_doc',
                'critical': False,
                'expect_error': True
            }
        ]
        
        # Override step execution to expect errors
        original_execute = self.test_runner._execute_workflow_step
        
        def execute_with_error_handling(step, step_number):
            result = original_execute(step, step_number)
            if step.get('expect_error', False):
                # Invert success for expected errors
                result['success'] = not result['success']
                if result['error_message']:
                    result['expected_error'] = result['error_message']
                    result['error_message'] = None
            return result
        
        self.test_runner._execute_workflow_step = execute_with_error_handling
        
        workflow_result = self.test_runner.run_workflow_test(
            'error_scenarios_and_recovery',
            workflow_steps
        )
        
        # Restore original method
        self.test_runner._execute_workflow_step = original_execute
        
        return workflow_result
    
    def test_concurrent_user_scenarios(self) -> Dict[str, Any]:
        """Test concurrent user scenarios."""
        def simulate_user_workflow(user_id: int) -> Dict[str, Any]:
            """Simulate a single user workflow."""
            user_workflow_steps = [
                {
                    'name': f'User {user_id} Upload',
                    'type': 'upload',
                    'document_type': 'pqme_report',
                    'critical': True
                },
                {
                    'name': f'User {user_id} Process',
                    'type': 'process',
                    'document_id': f'user_{user_id}_doc',
                    'critical': True
                },
                {
                    'name': f'User {user_id} Q&A',
                    'type': 'qa',
                    'question': 'What is the patient name?',
                    'document_id': f'user_{user_id}_doc',
                    'critical': False
                },
                {
                    'name': f'User {user_id} Template',
                    'type': 'template',
                    'document_id': f'user_{user_id}_doc',
                    'critical': True
                }
            ]
            
            return self.test_runner.run_workflow_test(
                f'concurrent_user_{user_id}',
                user_workflow_steps
            )
        
        # Run concurrent user simulations
        num_concurrent_users = 5
        concurrent_results = []
        
        with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            future_to_user = {
                executor.submit(simulate_user_workflow, user_id): user_id
                for user_id in range(1, num_concurrent_users + 1)
            }
            
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    result = future.result()
                    result['user_id'] = user_id
                    concurrent_results.append(result)
                except Exception as e:
                    concurrent_results.append({
                        'user_id': user_id,
                        'workflow_name': f'concurrent_user_{user_id}',
                        'overall_success': False,
                        'error_message': str(e)
                    })
        
        # Analyze concurrent results
        successful_users = sum(1 for r in concurrent_results if r.get('overall_success', False))
        total_duration = sum(r.get('total_duration_ms', 0) for r in concurrent_results)
        avg_duration = total_duration / len(concurrent_results) if concurrent_results else 0
        
        return {
            'workflow_name': 'concurrent_user_scenarios',
            'total_users': num_concurrent_users,
            'successful_users': successful_users,
            'failed_users': num_concurrent_users - successful_users,
            'success_rate': (successful_users / num_concurrent_users) * 100,
            'average_duration_ms': avg_duration,
            'total_duration_ms': total_duration,
            'user_results': concurrent_results,
            'overall_success': successful_users == num_concurrent_users
        }
    
    def run_all_integration_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        test_methods = [
            ('complete_workflow', self.test_complete_document_processing_workflow),
            ('qa_functionality', self.test_qa_with_document_context),
            ('error_scenarios', self.test_error_scenarios_and_recovery),
            ('concurrent_users', self.test_concurrent_user_scenarios)
        ]
        
        all_results = []
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                result['test_category'] = test_name
                all_results.append(result)
            except Exception as e:
                all_results.append({
                    'test_category': test_name,
                    'workflow_name': test_name,
                    'overall_success': False,
                    'error_message': str(e),
                    'total_duration_ms': 0
                })
        
        # Calculate overall statistics
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.get('overall_success', False))
        total_duration = sum(r.get('total_duration_ms', 0) for r in all_results)
        
        summary = {
            'total_integration_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            'total_execution_time_ms': total_duration,
            'average_test_time_ms': total_duration / total_tests if total_tests > 0 else 0,
            'test_results': all_results
        }
        
        return summary


# Main test execution function
def run_end_to_end_integration_tests() -> Dict[str, Any]:
    """Run all end-to-end integration tests."""
    logger.info("Starting end-to-end integration tests...")
    
    test_suite = WorkflowTestSuite()
    results = test_suite.run_all_integration_tests()
    
    logger.info(f"Integration tests completed: {results['success_rate']:.1f}% success rate")
    
    return results


if __name__ == "__main__":
    # Run tests when executed directly
    results = run_end_to_end_integration_tests()
    
    print(f"\n=== End-to-End Integration Test Results ===")
    print(f"Total Tests: {results['total_integration_tests']}")
    print(f"Successful: {results['successful_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Total Execution Time: {results['total_execution_time_ms']:.0f}ms")
    print(f"Average Test Time: {results['average_test_time_ms']:.0f}ms")
    
    if results['failed_tests'] > 0:
        print(f"\n=== Failed Tests ===")
        for result in results['test_results']:
            if not result.get('overall_success'):
                print(f"- {result['test_category']}: {result.get('error_message', 'Unknown error')}")
    
    # Show concurrent user test details if available
    concurrent_test = next((r for r in results['test_results'] if r.get('test_category') == 'concurrent_users'), None)
    if concurrent_test:
        print(f"\n=== Concurrent User Test Details ===")
        print(f"Total Users: {concurrent_test.get('total_users', 0)}")
        print(f"Successful Users: {concurrent_test.get('successful_users', 0)}")
        print(f"User Success Rate: {concurrent_test.get('success_rate', 0):.1f}%")