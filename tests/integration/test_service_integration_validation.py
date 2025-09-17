"""
Integration tests for Service Integration Validation

Tests service validation, dependency checking, and graceful degradation
under various failure scenarios and recovery conditions.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.infrastructure.monitoring.service_integration_validator import (
    ServiceIntegrationValidator,
    ServiceStatus,
    ValidationResult,
    DependencyStatus
)
from src.infrastructure.monitoring.graceful_degradation_manager import (
    GracefulDegradationManager,
    DegradationLevel,
    DegradationPlan
)


class TestServiceIntegrationValidator:
    """Test service integration validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ServiceIntegrationValidator()
        self.validator.service_cache.clear()  # Clear cache for clean tests
    
    def test_service_registration(self):
        """Test service checker registration"""
        def mock_checker():
            return True
        
        self.validator.register_service_checker('test_service', mock_checker)
        assert 'test_service' in self.validator.service_checkers
        
        # Test validation with registered service
        result = self.validator.validate_service_availability('test_service')
        assert result.service_name == 'test_service'
        assert result.status == ServiceStatus.AVAILABLE
    
    def test_dependency_registration(self):
        """Test component dependency registration"""
        test_dependencies = ['service1', 'service2', 'service3']
        self.validator.register_dependency('test_component', test_dependencies)
        
        assert 'test_component' in self.validator.dependency_map
        assert self.validator.dependency_map['test_component'] == test_dependencies
    
    def test_fallback_handler_registration(self):
        """Test fallback handler registration"""
        def mock_fallback():
            return {'status': 'fallback_enabled'}
        
        self.validator.register_fallback_handler('test_service', mock_fallback)
        assert 'test_service' in self.validator.fallback_handlers
    
    def test_service_validation_success(self):
        """Test successful service validation"""
        def mock_successful_service():
            return True
        
        self.validator.register_service_checker('success_service', mock_successful_service)
        result = self.validator.validate_service_availability('success_service')
        
        assert result.service_name == 'success_service'
        assert result.status == ServiceStatus.AVAILABLE
        assert result.dependencies_met is True
        assert result.error_message is None
        assert result.response_time_ms is not None
        assert result.response_time_ms > 0
    
    def test_service_validation_failure(self):
        """Test failed service validation"""
        def mock_failed_service():
            return False
        
        self.validator.register_service_checker('failed_service', mock_failed_service)
        result = self.validator.validate_service_availability('failed_service')
        
        assert result.service_name == 'failed_service'
        assert result.status == ServiceStatus.UNAVAILABLE
        assert result.dependencies_met is False
        assert result.error_message is not None
    
    def test_service_validation_timeout(self):
        """Test service validation timeout"""
        def mock_slow_service():
            time.sleep(10)  # Longer than timeout
            return True
        
        self.validator.timeout_seconds = 1  # Short timeout for test
        self.validator.register_service_checker('slow_service', mock_slow_service)
        
        result = self.validator.validate_service_availability('slow_service')
        
        assert result.service_name == 'slow_service'
        assert result.status == ServiceStatus.UNAVAILABLE
        assert 'timed out' in result.error_message.lower()
    
    def test_service_validation_exception(self):
        """Test service validation with exception"""
        def mock_exception_service():
            raise Exception("Service connection failed")
        
        self.validator.register_service_checker('exception_service', mock_exception_service)
        result = self.validator.validate_service_availability('exception_service')
        
        assert result.service_name == 'exception_service'
        assert result.status == ServiceStatus.UNAVAILABLE
        assert result.dependencies_met is False
        assert 'Service connection failed' in result.error_message
    
    def test_service_validation_caching(self):
        """Test service validation result caching"""
        call_count = 0
        
        def mock_service_with_counter():
            nonlocal call_count
            call_count += 1
            return True
        
        self.validator.register_service_checker('cached_service', mock_service_with_counter)
        self.validator.cache_ttl_seconds = 60  # Long TTL for test
        
        # First call
        result1 = self.validator.validate_service_availability('cached_service')
        assert call_count == 1
        
        # Second call should use cache
        result2 = self.validator.validate_service_availability('cached_service')
        assert call_count == 1  # Should not increment
        
        # Third call with cache disabled
        result3 = self.validator.validate_service_availability('cached_service', use_cache=False)
        assert call_count == 2  # Should increment
    
    def test_dependency_checking_all_available(self):
        """Test dependency checking when all services are available"""
        # Register mock services
        self.validator.register_service_checker('service1', lambda: True)
        self.validator.register_service_checker('service2', lambda: True)
        self.validator.register_service_checker('service3', lambda: True)
        
        # Register component dependencies
        self.validator.register_dependency('test_component', ['service1', 'service2', 'service3'])
        
        dependency_status = self.validator.check_dependencies('test_component')
        
        assert dependency_status.component_name == 'test_component'
        assert dependency_status.required_services == ['service1', 'service2', 'service3']
        assert set(dependency_status.available_services) == {'service1', 'service2', 'service3'}
        assert dependency_status.missing_services == []
        assert dependency_status.can_function is True
    
    def test_dependency_checking_partial_availability(self):
        """Test dependency checking with some services unavailable"""
        # Register mock services
        self.validator.register_service_checker('service1', lambda: True)
        self.validator.register_service_checker('service2', lambda: False)
        self.validator.register_service_checker('service3', lambda: True)
        
        # Register component dependencies
        self.validator.register_dependency('test_component', ['service1', 'service2', 'service3'])
        
        dependency_status = self.validator.check_dependencies('test_component')
        
        assert dependency_status.component_name == 'test_component'
        assert 'service2' in dependency_status.missing_services
        assert 'service1' in dependency_status.available_services
        assert 'service3' in dependency_status.available_services
    
    def test_graceful_degradation_with_fallbacks(self):
        """Test graceful degradation with available fallbacks"""
        def mock_fallback():
            return {'fallback_mode': 'enabled', 'limited_features': True}
        
        self.validator.register_fallback_handler('failed_service', mock_fallback)
        
        degradation_result = self.validator.enable_graceful_degradation(['failed_service'])
        
        assert len(degradation_result['enabled_fallbacks']) == 1
        assert degradation_result['enabled_fallbacks'][0]['service'] == 'failed_service'
        assert degradation_result['enabled_fallbacks'][0]['fallback'] == 'enabled'
    
    def test_graceful_degradation_without_fallbacks(self):
        """Test graceful degradation without available fallbacks"""
        degradation_result = self.validator.enable_graceful_degradation(['no_fallback_service'])
        
        assert 'no_fallback_service' in degradation_result['disabled_features']
        assert len(degradation_result['enabled_fallbacks']) == 0
        assert len(degradation_result['warnings']) > 0
    
    def test_system_health_summary(self):
        """Test system health summary generation"""
        # Register mock services with mixed availability
        self.validator.register_service_checker('healthy_service', lambda: True)
        self.validator.register_service_checker('unhealthy_service', lambda: False)
        
        health_summary = self.validator.get_system_health_summary()
        
        assert 'overall_health' in health_summary
        assert 'available_services' in health_summary
        assert 'total_services' in health_summary
        assert 'health_percentage' in health_summary
        assert 'service_details' in health_summary
        assert 'timestamp' in health_summary
        
        # Check that we have both healthy and unhealthy services
        service_details = health_summary['service_details']
        assert any(result.status == ServiceStatus.AVAILABLE for result in service_details.values())
        assert any(result.status == ServiceStatus.UNAVAILABLE for result in service_details.values())
    
    def test_recovery_suggestions(self):
        """Test recovery suggestions for different services"""
        suggestions = self.validator._get_recovery_suggestions('database')
        assert len(suggestions) > 0
        assert any('database' in suggestion.lower() for suggestion in suggestions)
        
        suggestions = self.validator._get_recovery_suggestions('openrouter_api')
        assert len(suggestions) > 0
        assert any('api key' in suggestion.lower() for suggestion in suggestions)
    
    def test_concurrent_service_validation(self):
        """Test concurrent service validation"""
        def mock_slow_service():
            time.sleep(0.1)  # Small delay
            return True
        
        # Register multiple services
        for i in range(5):
            self.validator.register_service_checker(f'service_{i}', mock_slow_service)
        
        start_time = time.time()
        results = self.validator.validate_all_services()
        end_time = time.time()
        
        # Should complete in reasonable time (concurrent execution)
        assert end_time - start_time < 2.0  # Should be much faster than 5 * 0.1 seconds
        assert len(results) >= 5  # At least our test services plus defaults


class TestGracefulDegradationManager:
    """Test graceful degradation manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ServiceIntegrationValidator()
        self.degradation_manager = GracefulDegradationManager(self.validator)
    
    def test_degradation_plan_initialization(self):
        """Test degradation plan initialization"""
        assert len(self.degradation_manager.degradation_plans) > 0
        assert 'upload_interface' in self.degradation_manager.degradation_plans
        assert 'qa_interface' in self.degradation_manager.degradation_plans
    
    def test_component_degradation_assessment_full_functionality(self):
        """Test degradation assessment with full functionality"""
        # Mock all services as available
        self.validator.register_service_checker('service1', lambda: True)
        self.validator.register_service_checker('service2', lambda: True)
        self.validator.register_dependency('test_component', ['service1', 'service2'])
        
        plan = self.degradation_manager.assess_component_degradation('test_component')
        
        assert plan.component_name == 'test_component'
        assert plan.degradation_level == DegradationLevel.FULL_FUNCTIONALITY
        assert len(plan.disabled_features) == 0
    
    def test_component_degradation_assessment_partial_functionality(self):
        """Test degradation assessment with partial functionality"""
        # Mock mixed service availability
        self.validator.register_service_checker('available_service', lambda: True)
        self.validator.register_service_checker('unavailable_service', lambda: False)
        self.validator.register_dependency('test_component', ['available_service', 'unavailable_service'])
        
        plan = self.degradation_manager.assess_component_degradation('test_component')
        
        assert plan.component_name == 'test_component'
        assert plan.degradation_level in [DegradationLevel.PARTIAL_FUNCTIONALITY, DegradationLevel.NO_FUNCTIONALITY]
        assert 'unavailable_service' in plan.disabled_features
    
    def test_component_degradation_assessment_no_functionality(self):
        """Test degradation assessment with no functionality"""
        # Mock all critical services as unavailable
        self.validator.register_service_checker('critical_service', lambda: False)
        self.validator.register_dependency('test_component', ['critical_service'])
        
        # Override critical services for this component
        original_method = self.degradation_manager.service_validator._get_critical_services
        self.degradation_manager.service_validator._get_critical_services = lambda comp: ['critical_service']
        
        plan = self.degradation_manager.assess_component_degradation('test_component')
        
        assert plan.component_name == 'test_component'
        assert plan.degradation_level == DegradationLevel.NO_FUNCTIONALITY
        
        # Restore original method
        self.degradation_manager.service_validator._get_critical_services = original_method
    
    def test_apply_degradation_full_functionality(self):
        """Test applying degradation with full functionality"""
        # Mock all services as available
        self.validator.register_service_checker('service1', lambda: True)
        self.validator.register_dependency('test_component', ['service1'])
        
        result = self.degradation_manager.apply_degradation('test_component')
        
        assert result['component'] == 'test_component'
        assert result['degradation_level'] == 'full'
        assert len(result['disabled_features']) == 0
        assert result['fallback_rendered'] is False
    
    def test_apply_degradation_with_fallback(self):
        """Test applying degradation with fallback rendering"""
        # Mock service as unavailable
        self.validator.register_service_checker('critical_service', lambda: False)
        self.validator.register_dependency('test_component', ['critical_service'])
        
        # Override critical services and add fallback
        self.degradation_manager.service_validator._get_critical_services = lambda comp: ['critical_service']
        self.degradation_manager.fallback_components['test_component'] = Mock()
        
        result = self.degradation_manager.apply_degradation('test_component')
        
        assert result['component'] == 'test_component'
        assert result['degradation_level'] == 'none'
        assert result['fallback_rendered'] is True
    
    def test_system_degradation_status(self):
        """Test system-wide degradation status"""
        # Setup mixed service availability
        self.validator.register_service_checker('good_service', lambda: True)
        self.validator.register_service_checker('bad_service', lambda: False)
        
        # Register dependencies for existing components
        self.validator.register_dependency('upload_interface', ['good_service'])
        self.validator.register_dependency('qa_interface', ['bad_service'])
        
        status = self.degradation_manager.get_system_degradation_status()
        
        assert 'overall_degradation' in status
        assert 'component_statuses' in status
        assert 'total_components' in status
        assert 'fully_functional' in status
        assert 'degraded_components' in status
        
        # Should have some degraded components
        assert status['degraded_components'] > 0


class TestServiceIntegrationScenarios:
    """Test various service integration failure and recovery scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ServiceIntegrationValidator()
        self.degradation_manager = GracefulDegradationManager(self.validator)
    
    def test_database_failure_scenario(self):
        """Test handling of database service failure"""
        # Mock database as unavailable
        self.validator.register_service_checker('database', lambda: False)
        
        # Test components that depend on database
        for component in ['document_manager', 'template_interface']:
            if 'database' in self.validator.dependency_map.get(component, []):
                dependency_status = self.validator.check_dependencies(component)
                assert 'database' in dependency_status.missing_services
                
                degradation_result = self.degradation_manager.apply_degradation(component)
                assert degradation_result['degradation_level'] != 'full'
    
    def test_api_service_failure_scenario(self):
        """Test handling of API service failures"""
        # Mock API services as unavailable
        self.validator.register_service_checker('openrouter_api', lambda: False)
        self.validator.register_service_checker('gemini_api', lambda: False)
        
        # Test Q&A interface which depends on API services
        dependency_status = self.validator.check_dependencies('qa_interface')
        
        # Should detect missing API services
        api_services = [s for s in dependency_status.missing_services if 'api' in s]
        assert len(api_services) > 0
        
        degradation_result = self.degradation_manager.apply_degradation('qa_interface')
        assert degradation_result['degradation_level'] != 'full'
    
    def test_file_storage_failure_scenario(self):
        """Test handling of file storage failure"""
        # Mock file storage as unavailable
        self.validator.register_service_checker('file_storage', lambda: False)
        
        # Test upload interface which depends on file storage
        dependency_status = self.validator.check_dependencies('upload_interface')
        
        if 'file_storage' in dependency_status.missing_services:
            degradation_result = self.degradation_manager.apply_degradation('upload_interface')
            assert degradation_result['degradation_level'] != 'full'
    
    def test_service_recovery_scenario(self):
        """Test service recovery after failure"""
        call_count = 0
        
        def mock_recovering_service():
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Fail first 2 calls, then succeed
        
        self.validator.register_service_checker('recovering_service', mock_recovering_service)
        self.validator.cache_ttl_seconds = 0  # Disable caching for this test
        
        # First calls should fail
        result1 = self.validator.validate_service_availability('recovering_service')
        assert result1.status == ServiceStatus.UNAVAILABLE
        
        result2 = self.validator.validate_service_availability('recovering_service')
        assert result2.status == ServiceStatus.UNAVAILABLE
        
        # Third call should succeed
        result3 = self.validator.validate_service_availability('recovering_service')
        assert result3.status == ServiceStatus.AVAILABLE
    
    def test_cascading_failure_scenario(self):
        """Test handling of cascading service failures"""
        # Mock multiple related services as failing
        self.validator.register_service_checker('primary_service', lambda: False)
        self.validator.register_service_checker('dependent_service', lambda: False)
        self.validator.register_service_checker('secondary_service', lambda: False)
        
        # Register a component that depends on all these services
        self.validator.register_dependency('complex_component', 
                                         ['primary_service', 'dependent_service', 'secondary_service'])
        
        dependency_status = self.validator.check_dependencies('complex_component')
        
        # Should detect all missing services
        assert len(dependency_status.missing_services) == 3
        assert not dependency_status.can_function
        
        # Apply graceful degradation
        degradation_result = self.validator.enable_graceful_degradation(dependency_status.missing_services)
        
        # Should have multiple disabled features
        assert len(degradation_result['disabled_features']) == 3
        assert len(degradation_result['recovery_suggestions']) > 0
    
    @patch('streamlit.warning')
    @patch('streamlit.error')
    def test_ui_integration_with_degradation(self, mock_error, mock_warning):
        """Test UI integration with degradation manager"""
        # Mock service as unavailable
        self.validator.register_service_checker('ui_service', lambda: False)
        self.validator.register_dependency('test_ui_component', ['ui_service'])
        
        # Apply degradation (this would normally show UI elements)
        degradation_result = self.degradation_manager.apply_degradation('test_ui_component')
        
        # Verify degradation was applied
        assert degradation_result['degradation_level'] != 'full'
        assert len(degradation_result['recovery_actions']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])