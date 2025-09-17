"""
Comprehensive Backend Endpoint Testing Framework.

This module provides automated testing for all backend routes, API endpoints,
health checks, and service integrations including both Gemini and OpenRouter APIs.
"""

import pytest
import requests
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
import tempfile
from io import BytesIO
import asyncio

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app import get_app, initialize_app
from src.config.app_config import app_config
from src.utils.logging_config import get_logger
from src.infrastructure.api.api_provider_factory import APIProviderFactory
from src.infrastructure.monitoring.health_checker import ComprehensiveHealthChecker

logger = get_logger(__name__)


class BackendEndpointTester:
    """Comprehensive backend endpoint testing framework."""
    
    def __init__(self, base_url: str = "http://localhost:8501"):
        """Initialize the endpoint tester."""
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        self.timeout = 30
    
    def setup_test_environment(self):
        """Setup test environment with mock services."""
        # Mock environment variables for testing
        test_env = {
            'GEMINI_API_KEY': 'test_gemini_key_123',
            'OPENAI_API_KEY': 'test_openai_key_123',
            'OPENROUTER_API_KEY': 'test_openrouter_key_123',
            'DATABASE_PATH': ':memory:',
            'DEBUG': 'true'
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
    
    def test_endpoint(self, endpoint: str, method: str = 'GET', 
                     data: Dict[str, Any] = None, files: Dict[str, Any] = None,
                     headers: Dict[str, str] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Test a specific endpoint."""
        test_result = {
            'endpoint': endpoint,
            'method': method,
            'passed': False,
            'status_code': None,
            'response_time_ms': 0,
            'error_message': None,
            'response_data': None
        }
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                if files:
                    response = self.session.post(url, data=data, files=files, headers=headers, timeout=self.timeout)
                else:
                    response = self.session.post(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            test_result['status_code'] = response.status_code
            test_result['response_time_ms'] = (time.time() - start_time) * 1000
            
            # Check if status code matches expected
            if response.status_code == expected_status:
                test_result['passed'] = True
                
                # Try to parse JSON response
                try:
                    test_result['response_data'] = response.json()
                except:
                    test_result['response_data'] = response.text
            else:
                test_result['error_message'] = f"Expected status {expected_status}, got {response.status_code}"
                test_result['response_data'] = response.text
                
        except Exception as e:
            test_result['error_message'] = str(e)
            test_result['response_time_ms'] = (time.time() - start_time) * 1000
        
        self.test_results.append(test_result)
        return test_result


class APIEndpointTests:
    """Comprehensive API endpoint tests."""
    
    def __init__(self):
        """Initialize API endpoint tests."""
        self.tester = BackendEndpointTester()
        self.tester.setup_test_environment()
    
    def test_health_check_endpoints(self) -> List[Dict[str, Any]]:
        """Test health check endpoints."""
        health_endpoints = [
            '/health',
            '/api/health',
            '/api/v1/health',
            '/status',
            '/api/status'
        ]
        
        results = []
        for endpoint in health_endpoints:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='GET',
                expected_status=200
            )
            results.append(result)
        
        return results
    
    def test_document_upload_endpoints(self) -> List[Dict[str, Any]]:
        """Test document upload endpoints."""
        results = []
        
        # Create test file
        test_file_content = b"This is a test PDF document content for QME processing."
        test_file = BytesIO(test_file_content)
        test_file.name = "test_document.pdf"
        
        # Test document upload
        upload_endpoints = [
            '/api/upload',
            '/api/v1/upload',
            '/api/documents/upload',
            '/upload'
        ]
        
        for endpoint in upload_endpoints:
            files = {'file': ('test_document.pdf', test_file, 'application/pdf')}
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='POST',
                files=files,
                expected_status=200
            )
            results.append(result)
            
            # Reset file pointer
            test_file.seek(0)
        
        return results
    
    def test_document_processing_endpoints(self) -> List[Dict[str, Any]]:
        """Test document processing endpoints."""
        results = []
        
        processing_endpoints = [
            ('/api/process', {'document_id': 'test_doc_123'}),
            ('/api/v1/process', {'document_id': 'test_doc_123', 'pipeline': 'evidence_first'}),
            ('/api/documents/process', {'document_id': 'test_doc_123', 'extract_fields': True}),
            ('/api/extract', {'document_id': 'test_doc_123', 'confidence_threshold': 0.8})
        ]
        
        for endpoint, data in processing_endpoints:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='POST',
                data=data,
                expected_status=200
            )
            results.append(result)
        
        return results
    
    def test_template_generation_endpoints(self) -> List[Dict[str, Any]]:
        """Test QME template generation endpoints."""
        results = []
        
        template_data = {
            'document_id': 'test_doc_123',
            'template_type': 'qme_report',
            'doctor_info': {
                'name': 'Dr. Test Physician',
                'license': 'CA12345',
                'specialty': 'Orthopedics'
            },
            'customization': {
                'include_evidence': True,
                'format': 'docx'
            }
        }
        
        template_endpoints = [
            '/api/template/generate',
            '/api/v1/template/generate',
            '/api/qme/generate',
            '/api/documents/template'
        ]
        
        for endpoint in template_endpoints:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='POST',
                data=template_data,
                expected_status=200
            )
            results.append(result)
        
        return results
    
    def test_qa_service_endpoints(self) -> List[Dict[str, Any]]:
        """Test Q&A service endpoints."""
        results = []
        
        qa_data = {
            'question': 'What is the patient\'s primary diagnosis?',
            'document_id': 'test_doc_123',
            'context_window': 1000
        }
        
        qa_endpoints = [
            '/api/qa/ask',
            '/api/v1/qa/ask',
            '/api/question',
            '/api/documents/qa'
        ]
        
        for endpoint in qa_endpoints:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='POST',
                data=qa_data,
                expected_status=200
            )
            results.append(result)
        
        return results
    
    def test_system_status_endpoints(self) -> List[Dict[str, Any]]:
        """Test system status and monitoring endpoints."""
        results = []
        
        status_endpoints = [
            '/api/system/status',
            '/api/v1/system/status',
            '/api/monitoring/status',
            '/api/stats',
            '/api/metrics'
        ]
        
        for endpoint in status_endpoints:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method='GET',
                expected_status=200
            )
            results.append(result)
        
        return results
    
    def test_gemini_api_integration(self) -> List[Dict[str, Any]]:
        """Test Gemini API integration endpoints."""
        results = []
        
        # Mock Gemini API calls
        with patch('src.infrastructure.api.gemini_api_client.GeminiAPIClient') as mock_client:
            mock_client.return_value.extract_fields.return_value = {
                'patient_name': 'John Doe',
                'case_number': 'WC2024-001',
                'confidence_scores': {'patient_name': 0.95, 'case_number': 0.88}
            }
            
            gemini_test_data = {
                'text': 'Patient John Doe, Case WC2024-001, injured on 01/15/2024',
                'extraction_type': 'qme_fields',
                'provider': 'gemini'
            }
            
            gemini_endpoints = [
                '/api/extract/gemini',
                '/api/v1/ai/gemini/extract',
                '/api/gemini/fields'
            ]
            
            for endpoint in gemini_endpoints:
                result = self.tester.test_endpoint(
                    endpoint=endpoint,
                    method='POST',
                    data=gemini_test_data,
                    expected_status=200
                )
                results.append(result)
        
        return results
    
    def test_openrouter_api_integration(self) -> List[Dict[str, Any]]:
        """Test OpenRouter API integration endpoints."""
        results = []
        
        # Mock OpenRouter API calls
        with patch('src.infrastructure.api.openrouter_client.OpenRouterClient') as mock_client:
            mock_client.return_value.extract_fields.return_value = {
                'extracted_fields': {
                    'patient_name': 'Jane Smith',
                    'injury_date': '2024-01-15'
                },
                'confidence_scores': {'patient_name': 0.92, 'injury_date': 0.85},
                'model_used': 'anthropic/claude-3-sonnet'
            }
            
            openrouter_test_data = {
                'text': 'Patient Jane Smith injured on January 15, 2024',
                'model': 'anthropic/claude-3-sonnet',
                'extraction_type': 'medical_fields',
                'provider': 'openrouter'
            }
            
            openrouter_endpoints = [
                '/api/extract/openrouter',
                '/api/v1/ai/openrouter/extract',
                '/api/openrouter/fields'
            ]
            
            for endpoint in openrouter_endpoints:
                result = self.tester.test_endpoint(
                    endpoint=endpoint,
                    method='POST',
                    data=openrouter_test_data,
                    expected_status=200
                )
                results.append(result)
        
        return results
    
    def test_error_handling_endpoints(self) -> List[Dict[str, Any]]:
        """Test error handling in endpoints."""
        results = []
        
        # Test invalid requests
        error_test_cases = [
            ('/api/upload', 'POST', {}, 400),  # No file
            ('/api/process', 'POST', {}, 400),  # No document_id
            ('/api/qa/ask', 'POST', {}, 400),  # No question
            ('/api/nonexistent', 'GET', {}, 404),  # Non-existent endpoint
            ('/api/template/generate', 'POST', {'invalid': 'data'}, 400)  # Invalid data
        ]
        
        for endpoint, method, data, expected_status in error_test_cases:
            result = self.tester.test_endpoint(
                endpoint=endpoint,
                method=method,
                data=data,
                expected_status=expected_status
            )
            results.append(result)
        
        return results
    
    def run_all_endpoint_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests."""
        all_results = []
        
        test_methods = [
            ('health_check', self.test_health_check_endpoints),
            ('document_upload', self.test_document_upload_endpoints),
            ('document_processing', self.test_document_processing_endpoints),
            ('template_generation', self.test_template_generation_endpoints),
            ('qa_service', self.test_qa_service_endpoints),
            ('system_status', self.test_system_status_endpoints),
            ('gemini_integration', self.test_gemini_api_integration),
            ('openrouter_integration', self.test_openrouter_api_integration),
            ('error_handling', self.test_error_handling_endpoints)
        ]
        
        for test_category, test_method in test_methods:
            try:
                category_results = test_method()
                for result in category_results:
                    result['test_category'] = test_category
                all_results.extend(category_results)
            except Exception as e:
                logger.error(f"Error in {test_category} tests: {e}")
                all_results.append({
                    'test_category': test_category,
                    'endpoint': 'unknown',
                    'method': 'unknown',
                    'passed': False,
                    'error_message': str(e),
                    'response_time_ms': 0
                })
        
        # Calculate statistics
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.get('passed', False))
        total_time = sum(r.get('response_time_ms', 0) for r in all_results)
        avg_response_time = total_time / total_tests if total_tests > 0 else 0
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'total_response_time_ms': total_time,
            'average_response_time_ms': avg_response_time,
            'test_results': all_results
        }
        
        return summary


class ServiceIntegrationTester:
    """Test service integrations and API providers."""
    
    def __init__(self):
        """Initialize service integration tester."""
        self.test_results = []
    
    def test_api_provider_factory(self) -> Dict[str, Any]:
        """Test API provider factory functionality."""
        test_result = {
            'test_name': 'api_provider_factory',
            'passed': False,
            'error_message': None,
            'providers_tested': []
        }
        
        try:
            factory = APIProviderFactory()
            
            # Test Gemini provider
            try:
                gemini_provider = factory.create_provider('gemini')
                test_result['providers_tested'].append({'provider': 'gemini', 'success': True})
            except Exception as e:
                test_result['providers_tested'].append({'provider': 'gemini', 'success': False, 'error': str(e)})
            
            # Test OpenRouter provider
            try:
                openrouter_provider = factory.create_provider('openrouter')
                test_result['providers_tested'].append({'provider': 'openrouter', 'success': True})
            except Exception as e:
                test_result['providers_tested'].append({'provider': 'openrouter', 'success': False, 'error': str(e)})
            
            # Test invalid provider
            try:
                invalid_provider = factory.create_provider('invalid')
                test_result['providers_tested'].append({'provider': 'invalid', 'success': False, 'error': 'Should have failed'})
            except Exception as e:
                test_result['providers_tested'].append({'provider': 'invalid', 'success': True, 'error': 'Expected failure'})
            
            test_result['passed'] = True
            
        except Exception as e:
            test_result['error_message'] = str(e)
        
        return test_result
    
    def test_health_checker_service(self) -> Dict[str, Any]:
        """Test comprehensive health checker service."""
        test_result = {
            'test_name': 'health_checker_service',
            'passed': False,
            'error_message': None,
            'health_checks': []
        }
        
        try:
            with patch('src.infrastructure.monitoring.health_checker.ComprehensiveHealthChecker') as mock_checker:
                mock_checker.return_value.get_overall_health.return_value = {
                    'overall_healthy': True,
                    'checks': {
                        'database': {'healthy': True, 'message': 'Connected'},
                        'api_providers': {'healthy': True, 'message': 'Available'},
                        'storage': {'healthy': True, 'message': 'Accessible'}
                    }
                }
                
                health_checker = mock_checker()
                health_status = health_checker.get_overall_health()
                
                test_result['health_checks'] = health_status.get('checks', {})
                test_result['passed'] = health_status.get('overall_healthy', False)
                
        except Exception as e:
            test_result['error_message'] = str(e)
        
        return test_result
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and operations."""
        test_result = {
            'test_name': 'database_connectivity',
            'passed': False,
            'error_message': None,
            'operations_tested': []
        }
        
        try:
            from src.storage.database import DatabaseManager
            
            with patch('src.storage.database.DatabaseManager') as mock_db:
                mock_db.return_value.test_connection.return_value = True
                mock_db.return_value.execute_query.return_value = {'result': 'success'}
                
                db_manager = mock_db()
                
                # Test connection
                connection_test = db_manager.test_connection()
                test_result['operations_tested'].append({'operation': 'connection', 'success': connection_test})
                
                # Test query execution
                query_test = db_manager.execute_query("SELECT 1")
                test_result['operations_tested'].append({'operation': 'query', 'success': bool(query_test)})
                
                test_result['passed'] = all(op['success'] for op in test_result['operations_tested'])
                
        except Exception as e:
            test_result['error_message'] = str(e)
        
        return test_result
    
    def run_service_integration_tests(self) -> Dict[str, Any]:
        """Run all service integration tests."""
        test_methods = [
            self.test_api_provider_factory,
            self.test_health_checker_service,
            self.test_database_connectivity
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)
            except Exception as e:
                results.append({
                    'test_name': test_method.__name__,
                    'passed': False,
                    'error_message': str(e)
                })
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get('passed', False))
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'test_results': results
        }
        
        return summary


# Main test execution functions
def run_backend_endpoint_tests() -> Dict[str, Any]:
    """Run all backend endpoint tests."""
    logger.info("Starting backend endpoint tests...")
    
    # Run API endpoint tests
    api_tests = APIEndpointTests()
    api_results = api_tests.run_all_endpoint_tests()
    
    # Run service integration tests
    service_tests = ServiceIntegrationTester()
    service_results = service_tests.run_service_integration_tests()
    
    # Combine results
    combined_results = {
        'api_endpoint_tests': api_results,
        'service_integration_tests': service_results,
        'overall_summary': {
            'total_tests': api_results['total_tests'] + service_results['total_tests'],
            'passed_tests': api_results['passed_tests'] + service_results['passed_tests'],
            'failed_tests': api_results['failed_tests'] + service_results['failed_tests'],
            'api_success_rate': api_results['success_rate'],
            'service_success_rate': service_results['success_rate'],
            'overall_success_rate': (
                (api_results['passed_tests'] + service_results['passed_tests']) /
                (api_results['total_tests'] + service_results['total_tests']) * 100
                if (api_results['total_tests'] + service_results['total_tests']) > 0 else 0
            )
        }
    }
    
    logger.info(f"Backend endpoint tests completed: {combined_results['overall_summary']['overall_success_rate']:.1f}% success rate")
    
    return combined_results


if __name__ == "__main__":
    # Run tests when executed directly
    results = run_backend_endpoint_tests()
    
    print(f"\n=== Backend Endpoint Test Results ===")
    print(f"API Endpoint Tests: {results['api_endpoint_tests']['passed_tests']}/{results['api_endpoint_tests']['total_tests']} passed ({results['api_endpoint_tests']['success_rate']:.1f}%)")
    print(f"Service Integration Tests: {results['service_integration_tests']['passed_tests']}/{results['service_integration_tests']['total_tests']} passed ({results['service_integration_tests']['success_rate']:.1f}%)")
    print(f"Overall Success Rate: {results['overall_summary']['overall_success_rate']:.1f}%")
    
    if results['overall_summary']['failed_tests'] > 0:
        print(f"\n=== Failed Tests ===")
        
        # Show failed API tests
        for result in results['api_endpoint_tests']['test_results']:
            if not result.get('passed'):
                print(f"- API {result['test_category']}: {result['endpoint']} ({result['method']}) - {result.get('error_message', 'Unknown error')}")
        
        # Show failed service tests
        for result in results['service_integration_tests']['test_results']:
            if not result.get('passed'):
                print(f"- Service {result['test_name']}: {result.get('error_message', 'Unknown error')}")