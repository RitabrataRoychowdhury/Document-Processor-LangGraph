"""
Performance and Stability Tests

Comprehensive tests for UI performance monitoring, load testing,
memory leak detection, and system stability validation.
"""

import pytest
import time
import threading
import psutil
import gc
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.infrastructure.monitoring.ui_performance_monitor import (
    UIPerformanceMonitor,
    PerformanceMetric,
    PerformanceReport,
    LoadTestResult
)
from src.infrastructure.monitoring.service_integration_validator import ServiceIntegrationValidator
from src.infrastructure.monitoring.graceful_degradation_manager import GracefulDegradationManager


class TestUIPerformanceMonitor:
    """Test UI performance monitoring functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = UIPerformanceMonitor(enable_memory_profiling=True)
        self.monitor.monitoring_enabled = True
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.monitor.cleanup()
    
    def test_performance_monitoring_lifecycle(self):
        """Test complete performance monitoring lifecycle"""
        # Start monitoring
        monitor_id = self.monitor.start_performance_monitoring('test_component', 'test_operation')
        assert monitor_id in self.monitor.active_monitors
        
        # Simulate some work
        time.sleep(0.1)
        
        # Stop monitoring and get report
        report = self.monitor.stop_performance_monitoring(monitor_id)
        
        assert isinstance(report, PerformanceReport)
        assert report.component_name == 'test_component'
        assert report.operation == 'test_operation'
        assert report.duration_ms > 0
        assert report.start_time < report.end_time
        assert monitor_id not in self.monitor.active_monitors
    
    def test_page_load_time_measurement(self):
        """Test page load time measurement"""
        def mock_page_load():
            time.sleep(0.05)  # Simulate page load
            return "page_loaded"
        
        report = self.monitor.measure_page_load_time('test_page', mock_page_load)
        
        assert report.component_name == 'test_page'
        assert report.operation == 'page_load'
        assert report.duration_ms >= 50  # At least 50ms due to sleep
        assert len(report.errors) == 0
    
    def test_page_load_with_error(self):
        """Test page load measurement with error"""
        def failing_page_load():
            raise Exception("Page load failed")
        
        report = self.monitor.measure_page_load_time('failing_page', failing_page_load)
        
        assert report.component_name == 'failing_page'
        assert len(report.errors) > 0
        assert 'Page load failed' in report.errors[0]
    
    def test_load_testing(self):
        """Test load testing functionality"""
        request_count = 0
        
        def mock_request():
            nonlocal request_count
            request_count += 1
            time.sleep(0.01)  # Simulate request processing
            return f"response_{request_count}"
        
        # Run short load test
        result = self.monitor.run_load_test(
            test_name='test_load',
            test_function=mock_request,
            concurrent_users=3,
            duration_seconds=1
        )
        
        assert isinstance(result, LoadTestResult)
        assert result.test_name == 'test_load'
        assert result.concurrent_users == 3
        assert result.total_requests > 0
        assert result.successful_requests > 0
        assert result.average_response_time_ms > 0
        assert result.requests_per_second > 0
    
    def test_load_testing_with_errors(self):
        """Test load testing with some failing requests"""
        request_count = 0
        
        def failing_request():
            nonlocal request_count
            request_count += 1
            if request_count % 3 == 0:  # Every 3rd request fails
                raise Exception("Request failed")
            time.sleep(0.01)
            return "success"
        
        result = self.monitor.run_load_test(
            test_name='failing_load_test',
            test_function=failing_request,
            concurrent_users=2,
            duration_seconds=1
        )
        
        assert result.failed_requests > 0
        assert result.error_rate_percent > 0
        assert result.successful_requests > 0
    
    def test_memory_leak_detection(self):
        """Test memory leak detection"""
        # Create a function that potentially leaks memory
        leaked_objects = []
        
        def potentially_leaking_function():
            # Simulate memory allocation
            leaked_objects.append([0] * 1000)  # Allocate some memory
            if len(leaked_objects) > 50:
                leaked_objects.clear()  # Prevent actual memory issues in test
        
        # Run memory leak detection
        result = self.monitor.detect_memory_leaks('test_component', iterations=20)
        
        assert 'component' in result
        assert result['component'] == 'test_component'
        assert 'iterations' in result
        assert 'initial_memory_mb' in result
        assert 'final_memory_mb' in result
        assert 'leak_detected' in result
    
    def test_component_benchmarking(self):
        """Test component performance benchmarking"""
        def benchmark_function():
            # Simulate some computational work
            total = sum(i * i for i in range(100))
            time.sleep(0.001)  # Small delay
            return total
        
        result = self.monitor.benchmark_component_performance(
            'test_component',
            benchmark_function,
            iterations=10
        )
        
        assert result['component'] == 'test_component'
        assert result['iterations'] == 10
        assert 'avg_execution_time_ms' in result
        assert 'min_execution_time_ms' in result
        assert 'max_execution_time_ms' in result
        assert 'median_execution_time_ms' in result
        assert result['error_rate_percent'] == 0
    
    def test_benchmarking_with_errors(self):
        """Test benchmarking with some failing iterations"""
        iteration_count = 0
        
        def failing_benchmark():
            nonlocal iteration_count
            iteration_count += 1
            if iteration_count % 4 == 0:  # Every 4th iteration fails
                raise Exception("Benchmark failed")
            return "success"
        
        result = self.monitor.benchmark_component_performance(
            'failing_component',
            failing_benchmark,
            iterations=8
        )
        
        assert len(result['errors']) > 0
        assert result['error_rate_percent'] > 0
    
    def test_performance_thresholds(self):
        """Test performance threshold checking"""
        # Set custom thresholds
        self.monitor.performance_thresholds['test_operation'] = {
            'warning_ms': 50,
            'critical_ms': 100
        }
        
        # Create a slow operation that exceeds thresholds
        monitor_id = self.monitor.start_performance_monitoring('test_component', 'test_operation')
        time.sleep(0.12)  # Exceed critical threshold
        report = self.monitor.stop_performance_monitoring(monitor_id)
        
        # Should have critical error
        assert len(report.errors) > 0
        assert any('Critical performance threshold exceeded' in error for error in report.errors)
    
    def test_performance_report_generation(self):
        """Test performance report generation"""
        # Generate some performance data
        for i in range(3):
            monitor_id = self.monitor.start_performance_monitoring('test_component', f'operation_{i}')
            time.sleep(0.01)
            self.monitor.stop_performance_monitoring(monitor_id)
        
        # Generate report
        report = self.monitor.generate_performance_report('test_component')
        
        assert 'timestamp' in report
        assert 'components' in report
        assert 'test_component' in report['components']
        
        component_report = report['components']['test_component']
        assert 'total_operations' in component_report
        assert component_report['total_operations'] == 3
        assert 'avg_duration_ms' in component_report
        assert 'recent_operations' in component_report
    
    def test_metric_recording(self):
        """Test metric recording functionality"""
        # Record some metrics
        self.monitor._record_metric('test_metric', 42.5, 'units', 'test_component')
        
        # Check if metric was recorded
        assert 'test_component' in self.monitor.performance_history
        metrics = list(self.monitor.performance_history['test_component'])
        assert len(metrics) > 0
        
        latest_metric = metrics[-1]
        assert latest_metric.name == 'test_metric'
        assert latest_metric.value == 42.5
        assert latest_metric.unit == 'units'
        assert latest_metric.component == 'test_component'
    
    def test_report_file_saving(self):
        """Test saving performance report to file"""
        # Generate a simple report
        report = {
            'timestamp': datetime.now(),
            'test_data': 'test_value',
            'components': {
                'test_component': {
                    'avg_duration_ms': 100.5
                }
            }
        }
        
        # Save report
        filepath = self.monitor.save_report_to_file(report, 'test_report.json')
        
        assert filepath is not None
        assert 'test_report.json' in filepath
        
        # Verify file exists
        import os
        assert os.path.exists(filepath)
        
        # Clean up
        os.remove(filepath)


class TestPerformanceIntegration:
    """Test performance monitoring integration with other components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.performance_monitor = UIPerformanceMonitor(enable_memory_profiling=False)
        self.service_validator = ServiceIntegrationValidator()
        self.degradation_manager = GracefulDegradationManager(self.service_validator)
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.performance_monitor.cleanup()
    
    def test_service_validation_performance(self):
        """Test performance of service validation"""
        # Register multiple mock services
        for i in range(5):
            self.service_validator.register_service_checker(f'service_{i}', lambda: True)
        
        # Measure validation performance
        def validate_all_services():
            return self.service_validator.validate_all_services()
        
        report = self.performance_monitor.measure_page_load_time(
            'service_validation',
            validate_all_services
        )
        
        assert report.duration_ms > 0
        assert len(report.errors) == 0
    
    def test_degradation_manager_performance(self):
        """Test performance of degradation manager"""
        # Setup services
        self.service_validator.register_service_checker('fast_service', lambda: True)
        self.service_validator.register_service_checker('slow_service', lambda: time.sleep(0.01) or True)
        self.service_validator.register_dependency('test_component', ['fast_service', 'slow_service'])
        
        # Measure degradation assessment performance
        def assess_degradation():
            return self.degradation_manager.assess_component_degradation('test_component')
        
        benchmark_result = self.performance_monitor.benchmark_component_performance(
            'degradation_manager',
            assess_degradation,
            iterations=10
        )
        
        assert benchmark_result['avg_execution_time_ms'] > 0
        assert benchmark_result['error_rate_percent'] == 0
    
    def test_concurrent_performance_monitoring(self):
        """Test performance monitoring under concurrent load"""
        def concurrent_operation():
            monitor_id = self.performance_monitor.start_performance_monitoring('concurrent_test', 'operation')
            time.sleep(0.01)
            return self.performance_monitor.stop_performance_monitoring(monitor_id)
        
        # Run concurrent operations
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_operation) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 10
        assert all(isinstance(result, PerformanceReport) for result in results)
        assert all(result.duration_ms > 0 for result in results)
    
    def test_system_resource_monitoring(self):
        """Test system resource monitoring during operations"""
        # Start monitoring
        monitor_id = self.performance_monitor.start_performance_monitoring('resource_test', 'cpu_intensive')
        
        # Simulate CPU-intensive work
        total = 0
        for i in range(100000):
            total += i * i
        
        # Stop monitoring
        report = self.performance_monitor.stop_performance_monitoring(monitor_id)
        
        assert report.duration_ms > 0
        assert report.cpu_usage_percent >= 0  # Should have some CPU usage
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking during operations"""
        # Start monitoring
        monitor_id = self.performance_monitor.start_performance_monitoring('memory_test', 'memory_intensive')
        
        # Simulate memory allocation
        large_list = [i for i in range(10000)]
        
        # Stop monitoring
        report = self.performance_monitor.stop_performance_monitoring(monitor_id)
        
        assert report.duration_ms > 0
        # Memory usage might be positive or negative depending on GC
        assert isinstance(report.memory_usage_mb, float)
        
        # Clean up
        del large_list
        gc.collect()


class TestStabilityTesting:
    """Test system stability under various conditions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.performance_monitor = UIPerformanceMonitor(enable_memory_profiling=False)
        self.service_validator = ServiceIntegrationValidator()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.performance_monitor.cleanup()
    
    def test_long_running_operation_stability(self):
        """Test stability of long-running operations"""
        def long_running_operation():
            # Simulate long-running work
            for i in range(100):
                time.sleep(0.001)  # Small incremental work
                if i % 20 == 0:
                    gc.collect()  # Periodic cleanup
        
        # Monitor long-running operation
        report = self.performance_monitor.measure_page_load_time(
            'long_running_test',
            long_running_operation
        )
        
        assert report.duration_ms > 100  # Should take at least 100ms
        assert len(report.errors) == 0
    
    def test_repeated_operation_stability(self):
        """Test stability of repeated operations"""
        def repeated_operation():
            # Simple operation that gets repeated
            return sum(i for i in range(100))
        
        # Run many iterations to test stability
        results = []
        for i in range(50):
            try:
                monitor_id = self.performance_monitor.start_performance_monitoring('stability_test', f'iteration_{i}')
                repeated_operation()
                report = self.performance_monitor.stop_performance_monitoring(monitor_id)
                results.append(report)
            except Exception as e:
                pytest.fail(f"Operation failed on iteration {i}: {str(e)}")
        
        assert len(results) == 50
        assert all(len(report.errors) == 0 for report in results)
        
        # Check for performance degradation over time
        early_avg = sum(r.duration_ms for r in results[:10]) / 10
        late_avg = sum(r.duration_ms for r in results[-10:]) / 10
        
        # Performance shouldn't degrade significantly (allow 50% increase)
        assert late_avg < early_avg * 1.5
    
    def test_error_recovery_stability(self):
        """Test stability of error recovery mechanisms"""
        error_count = 0
        
        def sometimes_failing_operation():
            nonlocal error_count
            error_count += 1
            if error_count % 3 == 0:  # Every 3rd call fails
                raise Exception(f"Simulated error {error_count}")
            return "success"
        
        # Test error recovery over multiple iterations
        successful_operations = 0
        failed_operations = 0
        
        for i in range(20):
            try:
                monitor_id = self.performance_monitor.start_performance_monitoring('error_recovery_test', f'attempt_{i}')
                sometimes_failing_operation()
                report = self.performance_monitor.stop_performance_monitoring(monitor_id)
                successful_operations += 1
            except Exception:
                failed_operations += 1
        
        # Should have both successes and failures
        assert successful_operations > 0
        assert failed_operations > 0
        
        # System should remain stable despite errors
        assert successful_operations + failed_operations == 20
    
    def test_concurrent_user_stability(self):
        """Test system stability under concurrent user load"""
        def user_session():
            """Simulate a user session"""
            operations = ['login', 'upload', 'process', 'download']
            session_results = []
            
            for operation in operations:
                try:
                    monitor_id = self.performance_monitor.start_performance_monitoring('user_session', operation)
                    time.sleep(0.01)  # Simulate operation time
                    report = self.performance_monitor.stop_performance_monitoring(monitor_id)
                    session_results.append(report)
                except Exception as e:
                    session_results.append(f"Error: {str(e)}")
            
            return session_results
        
        # Run concurrent user sessions
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(user_session) for _ in range(10)]
            all_results = []
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    session_results = future.result()
                    all_results.extend(session_results)
                except Exception as e:
                    pytest.fail(f"User session failed: {str(e)}")
        
        # Verify all sessions completed
        successful_reports = [r for r in all_results if isinstance(r, PerformanceReport)]
        assert len(successful_reports) == 40  # 10 users * 4 operations each
        
        # Check for any performance issues
        slow_operations = [r for r in successful_reports if r.duration_ms > 100]
        assert len(slow_operations) < len(successful_reports) * 0.1  # Less than 10% should be slow
    
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios"""
        # Simulate memory pressure
        memory_hogs = []
        
        def memory_intensive_operation():
            # Allocate memory but clean it up
            temp_data = [i for i in range(10000)]
            result = sum(temp_data)
            del temp_data
            gc.collect()
            return result
        
        # Run operations while monitoring memory
        initial_memory = psutil.Process().memory_info().rss / (1024**2)
        
        for i in range(20):
            monitor_id = self.performance_monitor.start_performance_monitoring('memory_pressure_test', f'operation_{i}')
            memory_intensive_operation()
            report = self.performance_monitor.stop_performance_monitoring(monitor_id)
            
            # Check if memory usage is reasonable
            current_memory = psutil.Process().memory_info().rss / (1024**2)
            memory_increase = current_memory - initial_memory
            
            # Memory shouldn't increase dramatically (allow 100MB increase)
            assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB"
        
        # Final cleanup
        gc.collect()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])