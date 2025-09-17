#!/usr/bin/env python3
"""
Simple Service Integration Validation Test

This script tests the core service validation functionality without external dependencies.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.infrastructure.monitoring.service_integration_validator import (
    ServiceIntegrationValidator, ServiceStatus
)
from src.infrastructure.monitoring.graceful_degradation_manager import (
    GracefulDegradationManager, DegradationLevel
)
from src.infrastructure.monitoring.ui_performance_monitor import UIPerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_service_validation():
    """Test service integration validation functionality"""
    logger.info("=== Testing Service Integration Validation ===")
    
    # Initialize validator
    validator = ServiceIntegrationValidator()
    
    # Register test services
    def healthy_service():
        time.sleep(0.01)
        return True
    
    def unhealthy_service():
        return False
    
    def slow_service():
        time.sleep(1.5)  # Will timeout
        return True
    
    validator.register_service_checker('test_healthy', healthy_service)
    validator.register_service_checker('test_unhealthy', unhealthy_service)
    validator.register_service_checker('test_slow', slow_service)
    
    # Test individual service validation
    logger.info("Testing individual service validation...")
    
    # Test healthy service
    result = validator.validate_service_availability('test_healthy')
    assert result.status == ServiceStatus.AVAILABLE
    assert result.response_time_ms > 0
    logger.info(f"✅ Healthy service test passed: {result.response_time_ms:.2f}ms")
    
    # Test unhealthy service
    result = validator.validate_service_availability('test_unhealthy')
    assert result.status == ServiceStatus.UNAVAILABLE
    assert result.error_message is not None
    logger.info(f"✅ Unhealthy service test passed: {result.error_message}")
    
    # Test timeout handling
    validator.timeout_seconds = 1  # Short timeout
    result = validator.validate_service_availability('test_slow')
    assert result.status == ServiceStatus.UNAVAILABLE
    assert 'timed out' in result.error_message.lower()
    logger.info(f"✅ Timeout handling test passed: {result.error_message}")
    
    # Test dependency checking
    logger.info("Testing dependency checking...")
    validator.register_dependency('test_component', ['test_healthy', 'test_unhealthy'])
    
    dependency_status = validator.check_dependencies('test_component')
    assert dependency_status.component_name == 'test_component'
    assert 'test_healthy' in dependency_status.available_services
    assert 'test_unhealthy' in dependency_status.missing_services
    logger.info(f"✅ Dependency checking test passed: {len(dependency_status.available_services)} available, {len(dependency_status.missing_services)} missing")
    
    # Test system health summary
    logger.info("Testing system health summary...")
    health_summary = validator.get_system_health_summary()
    assert 'overall_health' in health_summary
    assert 'available_services' in health_summary
    assert 'total_services' in health_summary
    logger.info(f"✅ System health test passed: {health_summary['health_percentage']:.1f}% healthy")
    
    return validator


def test_graceful_degradation(validator):
    """Test graceful degradation functionality"""
    logger.info("\n=== Testing Graceful Degradation ===")
    
    # Initialize degradation manager
    degradation_manager = GracefulDegradationManager(validator)
    
    # Test component degradation assessment
    logger.info("Testing component degradation assessment...")
    
    # Test with existing component
    plan = degradation_manager.assess_component_degradation('upload_interface')
    assert plan.component_name == 'upload_interface'
    assert isinstance(plan.degradation_level, DegradationLevel)
    logger.info(f"✅ Degradation assessment test passed: {plan.degradation_level.value}")
    
    # Test system degradation status
    logger.info("Testing system degradation status...")
    system_status = degradation_manager.get_system_degradation_status()
    assert 'overall_degradation' in system_status
    assert 'component_statuses' in system_status
    logger.info(f"✅ System degradation test passed: {system_status['overall_degradation']}")
    
    # Test degradation application
    logger.info("Testing degradation application...")
    degradation_result = degradation_manager.apply_degradation('upload_interface')
    assert 'component' in degradation_result
    assert 'degradation_level' in degradation_result
    logger.info(f"✅ Degradation application test passed: {degradation_result['degradation_level']}")
    
    return degradation_manager


def test_performance_monitoring():
    """Test performance monitoring functionality"""
    logger.info("\n=== Testing Performance Monitoring ===")
    
    # Initialize performance monitor
    performance_monitor = UIPerformanceMonitor(enable_memory_profiling=False)  # Disable for simplicity
    
    # Test basic performance monitoring
    logger.info("Testing basic performance monitoring...")
    
    def test_operation():
        time.sleep(0.05)
        return sum(i * i for i in range(1000))
    
    monitor_id = performance_monitor.start_performance_monitoring('test_component', 'test_operation')
    result = test_operation()
    report = performance_monitor.stop_performance_monitoring(monitor_id)
    
    assert report.component_name == 'test_component'
    assert report.operation == 'test_operation'
    assert report.duration_ms >= 50  # At least 50ms due to sleep
    logger.info(f"✅ Basic monitoring test passed: {report.duration_ms:.2f}ms")
    
    # Test page load measurement
    logger.info("Testing page load measurement...")
    
    def mock_page_load():
        time.sleep(0.02)
        return "page_loaded"
    
    page_report = performance_monitor.measure_page_load_time('test_page', mock_page_load)
    assert page_report.component_name == 'test_page'
    assert page_report.duration_ms >= 20
    logger.info(f"✅ Page load test passed: {page_report.duration_ms:.2f}ms")
    
    # Test benchmarking
    logger.info("Testing component benchmarking...")
    
    def benchmark_func():
        return sum(i for i in range(100))
    
    benchmark_result = performance_monitor.benchmark_component_performance(
        'test_component', benchmark_func, iterations=5
    )
    
    assert 'avg_execution_time_ms' in benchmark_result
    assert benchmark_result['iterations'] == 5
    logger.info(f"✅ Benchmarking test passed: {benchmark_result['avg_execution_time_ms']:.2f}ms avg")
    
    # Test load testing
    logger.info("Testing load testing...")
    
    def mock_request():
        time.sleep(0.001)
        return "response"
    
    load_result = performance_monitor.run_load_test(
        'test_load', mock_request, concurrent_users=2, duration_seconds=1
    )
    
    assert load_result.test_name == 'test_load'
    assert load_result.total_requests > 0
    logger.info(f"✅ Load testing test passed: {load_result.total_requests} requests, {load_result.requests_per_second:.2f} RPS")
    
    # Test performance report generation
    logger.info("Testing performance report generation...")
    perf_report = performance_monitor.generate_performance_report()
    assert 'timestamp' in perf_report
    assert 'components' in perf_report
    logger.info(f"✅ Report generation test passed: {len(perf_report['components'])} components")
    
    performance_monitor.cleanup()
    return performance_monitor


def test_integration_scenarios():
    """Test integration scenarios"""
    logger.info("\n=== Testing Integration Scenarios ===")
    
    validator = ServiceIntegrationValidator()
    performance_monitor = UIPerformanceMonitor(enable_memory_profiling=False)
    
    # Test service validation performance
    logger.info("Testing service validation performance...")
    
    # Register multiple services
    for i in range(5):
        validator.register_service_checker(f'service_{i}', lambda: True)
    
    monitor_id = performance_monitor.start_performance_monitoring('validation_test', 'all_services')
    all_results = validator.validate_all_services()
    validation_report = performance_monitor.stop_performance_monitoring(monitor_id)
    
    assert len(all_results) >= 5
    logger.info(f"✅ Service validation performance test passed: {len(all_results)} services in {validation_report.duration_ms:.2f}ms")
    
    # Test concurrent validation
    logger.info("Testing concurrent validation...")
    
    import concurrent.futures
    
    def concurrent_validation():
        return validator.validate_service_availability('service_0')
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(concurrent_validation) for _ in range(6)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_time = time.time()
    
    assert len(results) == 6
    assert all(r.status == ServiceStatus.AVAILABLE for r in results)
    logger.info(f"✅ Concurrent validation test passed: 6 validations in {(end_time - start_time) * 1000:.2f}ms")
    
    performance_monitor.cleanup()


def run_all_tests():
    """Run all tests"""
    logger.info("Starting Comprehensive Service Integration Validation Tests")
    logger.info("=" * 70)
    
    try:
        # Test service validation
        validator = test_service_validation()
        
        # Test graceful degradation
        degradation_manager = test_graceful_degradation(validator)
        
        # Test performance monitoring
        performance_monitor = test_performance_monitoring()
        
        # Test integration scenarios
        test_integration_scenarios()
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        logger.info("✅ Service Integration Validation: WORKING")
        logger.info("✅ Graceful Degradation: WORKING")
        logger.info("✅ Performance Monitoring: WORKING")
        logger.info("✅ Load Testing: WORKING")
        logger.info("✅ Integration Scenarios: WORKING")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)