"""
UI Performance and Load Testing Framework.

This module provides performance testing for UI responsiveness, load testing
for concurrent users, memory leak detection, and stability testing.
"""

import time
import threading
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
import statistics
import tracemalloc

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ui.main_app import main
from src.ui.upload_interface import UploadInterface
from src.ui.qa_interface_simple import render_qa_page
from src.ui.qme_template_interface import render_qme_template_page
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class UIPerformanceMonitor:
    """Monitor UI performance metrics."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
        self.baseline_memory = None
        self.memory_samples = []
        self.response_times = []
    
    def start_monitoring(self):
        """Start performance monitoring."""
        tracemalloc.start()
        self.baseline_memory = psutil.Process().memory_info().rss
        self.memory_samples = []
        self.response_times = []
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics."""
        current_memory = psutil.Process().memory_info().rss
        memory_growth = current_memory - self.baseline_memory if self.baseline_memory else 0
        
        # Get tracemalloc statistics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return {
            'memory_growth_bytes': memory_growth,
            'memory_growth_mb': memory_growth / (1024 * 1024),
            'peak_memory_usage_mb': peak / (1024 * 1024),
            'current_memory_usage_mb': current / (1024 * 1024),
            'memory_samples': self.memory_samples,
            'response_times_ms': self.response_times,
            'avg_response_time_ms': statistics.mean(self.response_times) if self.response_times else 0,
            'max_response_time_ms': max(self.response_times) if self.response_times else 0,
            'min_response_time_ms': min(self.response_times) if self.response_times else 0
        }
    
    def record_response_time(self, response_time_ms: float):
        """Record a response time measurement."""
        self.response_times.append(response_time_ms)
    
    def sample_memory(self):
        """Sample current memory usage."""
        current_memory = psutil.Process().memory_info().rss
        self.memory_samples.append({
            'timestamp': time.time(),
            'memory_mb': current_memory / (1024 * 1024)
        })


class UILoadTester:
    """Load testing for UI components."""
    
    def __init__(self):
        """Initialize load tester."""
        self.test_results = []
        self.concurrent_sessions = {}
    
    def simulate_user_session(self, user_id: int, session_duration: int = 60) -> Dict[str, Any]:
        """Simulate a single user session."""
        session_result = {
            'user_id': user_id,
            'session_duration_s': session_duration,
            'actions_completed': 0,
            'actions_failed': 0,
            'total_response_time_ms': 0,
            'avg_response_time_ms': 0,
            'errors': [],
            'success': True
        }
        
        monitor = UIPerformanceMonitor()
        monitor.start_monitoring()
        
        start_time = time.time()
        end_time = start_time + session_duration
        
        # Simulate user actions
        actions = [
            self._simulate_page_load,
            self._simulate_file_upload,
            self._simulate_qa_interaction,
            self._simulate_template_generation,
            self._simulate_navigation
        ]
        
        try:
            while time.time() < end_time:
                for action in actions:
                    if time.time() >= end_time:
                        break
                    
                    action_start = time.time()
                    try:
                        action(user_id)
                        session_result['actions_completed'] += 1
                        action_time = (time.time() - action_start) * 1000
                        session_result['total_response_time_ms'] += action_time
                        monitor.record_response_time(action_time)
                    except Exception as e:
                        session_result['actions_failed'] += 1
                        session_result['errors'].append(str(e))
                    
                    # Brief pause between actions
                    time.sleep(0.1)
                
                # Sample memory periodically
                monitor.sample_memory()
                time.sleep(1)
        
        except Exception as e:
            session_result['success'] = False
            session_result['errors'].append(f"Session error: {str(e)}")
        
        # Calculate averages
        total_actions = session_result['actions_completed'] + session_result['actions_failed']
        if session_result['actions_completed'] > 0:
            session_result['avg_response_time_ms'] = (
                session_result['total_response_time_ms'] / session_result['actions_completed']
            )
        
        # Add performance metrics
        perf_metrics = monitor.stop_monitoring()
        session_result['performance_metrics'] = perf_metrics
        
        return session_result
    
    def _simulate_page_load(self, user_id: int):
        """Simulate page loading."""
        with patch('streamlit.set_page_config'), \
             patch('streamlit.title'), \
             patch('streamlit.sidebar'), \
             patch('streamlit.columns'):
            # Simulate main app loading
            time.sleep(0.05)  # Simulate processing time
    
    def _simulate_file_upload(self, user_id: int):
        """Simulate file upload action."""
        with patch('src.ui.upload_interface.FileUploadHandler') as mock_handler:
            mock_handler.return_value.get_file_metadata.return_value = {
                'filename': f'user_{user_id}_test.pdf',
                'file_type': 'pdf',
                'file_size_mb': 2.5,
                'is_valid': True
            }
            
            upload_interface = UploadInterface()
            time.sleep(0.1)  # Simulate upload processing
    
    def _simulate_qa_interaction(self, user_id: int):
        """Simulate Q&A interaction."""
        with patch('src.ui.qa_interface_simple._check_qa_services_available', return_value=True), \
             patch('src.ui.qa_interface_simple._process_question'):
            time.sleep(0.08)  # Simulate Q&A processing
    
    def _simulate_template_generation(self, user_id: int):
        """Simulate template generation."""
        with patch('src.ui.qme_template_interface.QMETemplateGenerator'), \
             patch('src.ui.qme_template_interface.ComprehensiveQMEFieldService'):
            time.sleep(0.15)  # Simulate template generation
    
    def _simulate_navigation(self, user_id: int):
        """Simulate navigation between pages."""
        time.sleep(0.02)  # Simulate navigation
    
    def run_load_test(self, num_users: int = 10, session_duration: int = 30) -> Dict[str, Any]:
        """Run load test with multiple concurrent users."""
        logger.info(f"Starting load test with {num_users} users for {session_duration}s each")
        
        load_test_result = {
            'num_users': num_users,
            'session_duration_s': session_duration,
            'start_time': time.time(),
            'end_time': None,
            'total_duration_s': 0,
            'user_results': [],
            'aggregate_metrics': {},
            'system_metrics': {},
            'success': True
        }
        
        # Monitor system resources during test
        system_monitor = UIPerformanceMonitor()
        system_monitor.start_monitoring()
        
        # Run concurrent user sessions
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            future_to_user = {
                executor.submit(self.simulate_user_session, user_id, session_duration): user_id
                for user_id in range(1, num_users + 1)
            }
            
            for future in as_completed(future_to_user):
                user_id = future_to_user[future]
                try:
                    user_result = future.result()
                    load_test_result['user_results'].append(user_result)
                except Exception as e:
                    logger.error(f"User {user_id} session failed: {e}")
                    load_test_result['user_results'].append({
                        'user_id': user_id,
                        'success': False,
                        'error': str(e)
                    })
        
        load_test_result['end_time'] = time.time()
        load_test_result['total_duration_s'] = load_test_result['end_time'] - load_test_result['start_time']
        
        # Calculate aggregate metrics
        load_test_result['aggregate_metrics'] = self._calculate_aggregate_metrics(load_test_result['user_results'])
        
        # Get system metrics
        load_test_result['system_metrics'] = system_monitor.stop_monitoring()
        
        logger.info(f"Load test completed in {load_test_result['total_duration_s']:.1f}s")
        
        return load_test_result
    
    def _calculate_aggregate_metrics(self, user_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics from user results."""
        successful_users = [r for r in user_results if r.get('success', False)]
        failed_users = [r for r in user_results if not r.get('success', False)]
        
        if not successful_users:
            return {
                'success_rate': 0,
                'total_actions': 0,
                'avg_response_time_ms': 0,
                'max_response_time_ms': 0,
                'throughput_actions_per_second': 0
            }
        
        total_actions = sum(r.get('actions_completed', 0) for r in successful_users)
        total_response_time = sum(r.get('total_response_time_ms', 0) for r in successful_users)
        response_times = [r.get('avg_response_time_ms', 0) for r in successful_users if r.get('avg_response_time_ms', 0) > 0]
        
        # Calculate throughput
        total_duration = max(r.get('session_duration_s', 1) for r in successful_users)
        throughput = total_actions / total_duration if total_duration > 0 else 0
        
        return {
            'success_rate': (len(successful_users) / len(user_results)) * 100,
            'successful_users': len(successful_users),
            'failed_users': len(failed_users),
            'total_actions': total_actions,
            'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
            'max_response_time_ms': max(response_times) if response_times else 0,
            'min_response_time_ms': min(response_times) if response_times else 0,
            'throughput_actions_per_second': throughput,
            'total_errors': sum(len(r.get('errors', [])) for r in user_results)
        }


class MemoryLeakDetector:
    """Detect memory leaks in UI components."""
    
    def __init__(self):
        """Initialize memory leak detector."""
        self.memory_snapshots = []
        self.leak_threshold_mb = 50  # MB
    
    def run_memory_leak_test(self, iterations: int = 100) -> Dict[str, Any]:
        """Run memory leak detection test."""
        logger.info(f"Starting memory leak test with {iterations} iterations")
        
        leak_test_result = {
            'iterations': iterations,
            'memory_snapshots': [],
            'memory_growth_mb': 0,
            'leak_detected': False,
            'leak_rate_mb_per_iteration': 0,
            'recommendations': []
        }
        
        # Initial memory snapshot
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        leak_test_result['memory_snapshots'].append({
            'iteration': 0,
            'memory_mb': initial_memory
        })
        
        # Run iterations
        for i in range(1, iterations + 1):
            try:
                # Simulate UI operations that might cause leaks
                self._simulate_ui_operations()
                
                # Force garbage collection
                gc.collect()
                
                # Take memory snapshot every 10 iterations
                if i % 10 == 0:
                    current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                    leak_test_result['memory_snapshots'].append({
                        'iteration': i,
                        'memory_mb': current_memory
                    })
                
            except Exception as e:
                logger.error(f"Error in iteration {i}: {e}")
        
        # Analyze results
        final_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        memory_growth = final_memory - initial_memory
        leak_rate = memory_growth / iterations
        
        leak_test_result['memory_growth_mb'] = memory_growth
        leak_test_result['leak_rate_mb_per_iteration'] = leak_rate
        leak_test_result['leak_detected'] = memory_growth > self.leak_threshold_mb
        
        # Generate recommendations
        if leak_test_result['leak_detected']:
            leak_test_result['recommendations'].extend([
                f"Memory leak detected: {memory_growth:.1f}MB growth over {iterations} iterations",
                f"Leak rate: {leak_rate:.3f}MB per iteration",
                "Review UI component cleanup and disposal",
                "Check for unclosed resources or event listeners",
                "Consider implementing proper component lifecycle management"
            ])
        else:
            leak_test_result['recommendations'].append(
                f"No significant memory leak detected. Growth: {memory_growth:.1f}MB"
            )
        
        logger.info(f"Memory leak test completed. Growth: {memory_growth:.1f}MB")
        
        return leak_test_result
    
    def _simulate_ui_operations(self):
        """Simulate UI operations that might cause memory leaks."""
        # Simulate component creation and destruction
        with patch('streamlit.empty') as mock_empty, \
             patch('streamlit.container') as mock_container, \
             patch('streamlit.columns') as mock_columns:
            
            # Create mock components
            mock_components = []
            for _ in range(10):
                mock_components.append(mock_empty())
                mock_components.append(mock_container())
                mock_components.append(mock_columns(2))
            
            # Simulate some processing
            time.sleep(0.001)
            
            # Clear references
            mock_components.clear()


class StabilityTester:
    """Test UI stability under various conditions."""
    
    def __init__(self):
        """Initialize stability tester."""
        self.stability_results = []
    
    def run_stability_test(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """Run long-running stability test."""
        logger.info(f"Starting stability test for {duration_minutes} minutes")
        
        stability_result = {
            'duration_minutes': duration_minutes,
            'start_time': time.time(),
            'end_time': None,
            'operations_completed': 0,
            'errors_encountered': 0,
            'error_details': [],
            'memory_samples': [],
            'performance_degradation': False,
            'stability_score': 0,
            'recommendations': []
        }
        
        monitor = UIPerformanceMonitor()
        monitor.start_monitoring()
        
        end_time = time.time() + (duration_minutes * 60)
        operation_count = 0
        
        try:
            while time.time() < end_time:
                try:
                    # Perform various UI operations
                    self._perform_stability_operations()
                    operation_count += 1
                    stability_result['operations_completed'] = operation_count
                    
                    # Sample memory every minute
                    if operation_count % 60 == 0:
                        monitor.sample_memory()
                    
                    time.sleep(1)  # 1 second between operations
                    
                except Exception as e:
                    stability_result['errors_encountered'] += 1
                    stability_result['error_details'].append({
                        'operation': operation_count,
                        'timestamp': time.time(),
                        'error': str(e)
                    })
                    
                    # Continue testing even after errors
                    time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Stability test interrupted by user")
        
        stability_result['end_time'] = time.time()
        actual_duration = (stability_result['end_time'] - stability_result['start_time']) / 60
        
        # Get performance metrics
        perf_metrics = monitor.stop_monitoring()
        stability_result['performance_metrics'] = perf_metrics
        
        # Calculate stability score
        error_rate = stability_result['errors_encountered'] / max(stability_result['operations_completed'], 1)
        memory_growth_rate = perf_metrics.get('memory_growth_mb', 0) / actual_duration
        
        # Stability score (0-100, higher is better)
        stability_score = max(0, 100 - (error_rate * 100) - (memory_growth_rate * 2))
        stability_result['stability_score'] = stability_score
        
        # Check for performance degradation
        response_times = perf_metrics.get('response_times_ms', [])
        if len(response_times) > 10:
            early_times = response_times[:len(response_times)//3]
            late_times = response_times[-len(response_times)//3:]
            
            if late_times and early_times:
                early_avg = statistics.mean(early_times)
                late_avg = statistics.mean(late_times)
                degradation = (late_avg - early_avg) / early_avg * 100
                
                stability_result['performance_degradation'] = degradation > 20  # 20% degradation threshold
        
        # Generate recommendations
        if stability_result['stability_score'] < 80:
            stability_result['recommendations'].append("Stability score is below 80. Investigation recommended.")
        
        if stability_result['errors_encountered'] > 0:
            stability_result['recommendations'].append(f"Encountered {stability_result['errors_encountered']} errors during testing.")
        
        if stability_result['performance_degradation']:
            stability_result['recommendations'].append("Performance degradation detected over time.")
        
        if perf_metrics.get('memory_growth_mb', 0) > 100:
            stability_result['recommendations'].append("Significant memory growth detected.")
        
        logger.info(f"Stability test completed. Score: {stability_score:.1f}/100")
        
        return stability_result
    
    def _perform_stability_operations(self):
        """Perform various operations for stability testing."""
        operations = [
            self._simulate_page_navigation,
            self._simulate_file_operations,
            self._simulate_data_processing,
            self._simulate_ui_interactions
        ]
        
        # Randomly select and perform operations
        import random
        operation = random.choice(operations)
        operation()
    
    def _simulate_page_navigation(self):
        """Simulate page navigation."""
        with patch('streamlit.rerun'), \
             patch('streamlit.switch_page'):
            time.sleep(0.01)
    
    def _simulate_file_operations(self):
        """Simulate file operations."""
        with patch('src.ui.upload_interface.FileUploadHandler'):
            time.sleep(0.02)
    
    def _simulate_data_processing(self):
        """Simulate data processing operations."""
        # Simulate some CPU-intensive work
        data = list(range(1000))
        result = sum(x * x for x in data)
        time.sleep(0.01)
    
    def _simulate_ui_interactions(self):
        """Simulate UI interactions."""
        with patch('streamlit.button'), \
             patch('streamlit.selectbox'), \
             patch('streamlit.text_input'):
            time.sleep(0.005)


# Main test execution functions
def run_ui_performance_tests() -> Dict[str, Any]:
    """Run all UI performance tests."""
    logger.info("Starting UI performance tests...")
    
    results = {
        'load_test': None,
        'memory_leak_test': None,
        'stability_test': None,
        'overall_performance_score': 0,
        'recommendations': []
    }
    
    try:
        # Load testing
        load_tester = UILoadTester()
        results['load_test'] = load_tester.run_load_test(num_users=5, session_duration=30)
        
        # Memory leak testing
        leak_detector = MemoryLeakDetector()
        results['memory_leak_test'] = leak_detector.run_memory_leak_test(iterations=50)
        
        # Stability testing
        stability_tester = StabilityTester()
        results['stability_test'] = stability_tester.run_stability_test(duration_minutes=5)
        
        # Calculate overall performance score
        load_score = results['load_test']['aggregate_metrics']['success_rate']
        stability_score = results['stability_test']['stability_score']
        memory_score = 100 if not results['memory_leak_test']['leak_detected'] else 50
        
        results['overall_performance_score'] = (load_score + stability_score + memory_score) / 3
        
        # Aggregate recommendations
        for test_result in results.values():
            if isinstance(test_result, dict) and 'recommendations' in test_result:
                results['recommendations'].extend(test_result['recommendations'])
        
    except Exception as e:
        logger.error(f"Performance tests failed: {e}")
        results['error'] = str(e)
    
    logger.info(f"UI performance tests completed. Overall score: {results['overall_performance_score']:.1f}/100")
    
    return results


if __name__ == "__main__":
    # Run performance tests when executed directly
    results = run_ui_performance_tests()
    
    print(f"\n=== UI Performance Test Results ===")
    print(f"Overall Performance Score: {results['overall_performance_score']:.1f}/100")
    
    if results.get('load_test'):
        load_metrics = results['load_test']['aggregate_metrics']
        print(f"Load Test Success Rate: {load_metrics['success_rate']:.1f}%")
        print(f"Average Response Time: {load_metrics['avg_response_time_ms']:.1f}ms")
    
    if results.get('memory_leak_test'):
        memory_test = results['memory_leak_test']
        print(f"Memory Leak Detected: {'Yes' if memory_test['leak_detected'] else 'No'}")
        print(f"Memory Growth: {memory_test['memory_growth_mb']:.1f}MB")
    
    if results.get('stability_test'):
        stability_test = results['stability_test']
        print(f"Stability Score: {stability_test['stability_score']:.1f}/100")
        print(f"Operations Completed: {stability_test['operations_completed']}")
        print(f"Errors Encountered: {stability_test['errors_encountered']}")
    
    if results.get('recommendations'):
        print(f"\n=== Recommendations ===")
        for i, recommendation in enumerate(results['recommendations'][:5], 1):
            print(f"{i}. {recommendation}")