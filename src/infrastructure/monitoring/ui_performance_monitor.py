"""
UI Performance Monitor

This module provides comprehensive performance monitoring for UI components,
including page load time measurement, memory usage tracking, and performance benchmarking.
"""

import time
import psutil
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque
import gc
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    component: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Performance report for a component or operation"""
    component_name: str
    operation: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class LoadTestResult:
    """Result of load testing"""
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    memory_peak_mb: float
    cpu_peak_percent: float
    test_duration_seconds: float
    timestamp: datetime


class UIPerformanceMonitor:
    """
    Comprehensive UI performance monitoring system
    """
    
    def __init__(self, enable_memory_profiling: bool = True):
        self.enable_memory_profiling = enable_memory_profiling
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_monitors: Dict[str, Dict] = {}
        self.baseline_metrics: Dict[str, PerformanceMetric] = {}
        self.performance_thresholds: Dict[str, Dict[str, float]] = {}
        self.monitoring_enabled = True
        
        # Initialize memory profiling if enabled
        if self.enable_memory_profiling:
            tracemalloc.start()
        
        # Set default performance thresholds
        self._initialize_performance_thresholds()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def _initialize_performance_thresholds(self):
        """Initialize default performance thresholds"""
        self.performance_thresholds.update({
            'page_load': {
                'warning_ms': 2000,
                'critical_ms': 5000
            },
            'api_call': {
                'warning_ms': 1000,
                'critical_ms': 3000
            },
            'memory_usage': {
                'warning_mb': 500,
                'critical_mb': 1000
            },
            'cpu_usage': {
                'warning_percent': 70,
                'critical_percent': 90
            },
            'response_time': {
                'warning_ms': 1500,
                'critical_ms': 3000
            }
        })
    
    def _start_background_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while self.monitoring_enabled:
                try:
                    # Collect system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory_info = psutil.virtual_memory()
                    
                    # Store system metrics
                    self._record_metric('system_cpu', cpu_percent, 'percent')
                    self._record_metric('system_memory', memory_info.percent, 'percent')
                    self._record_metric('system_memory_available', memory_info.available / (1024**2), 'MB')
                    
                    time.sleep(5)  # Monitor every 5 seconds
                except Exception as e:
                    logger.error(f"Background monitoring error: {str(e)}")
                    time.sleep(10)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def start_performance_monitoring(self, component_name: str, operation: str = "default") -> str:
        """
        Start performance monitoring for a component operation
        
        Args:
            component_name: Name of the UI component
            operation: Specific operation being monitored
            
        Returns:
            Monitor ID for stopping the monitoring
        """
        monitor_id = f"{component_name}_{operation}_{int(time.time() * 1000)}"
        
        # Get initial system state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024**2)  # MB
        initial_cpu = process.cpu_percent()
        
        # Start memory snapshot if profiling enabled
        memory_snapshot = None
        if self.enable_memory_profiling:
            memory_snapshot = tracemalloc.take_snapshot()
        
        self.active_monitors[monitor_id] = {
            'component_name': component_name,
            'operation': operation,
            'start_time': datetime.now(),
            'initial_memory_mb': initial_memory,
            'initial_cpu_percent': initial_cpu,
            'memory_snapshot': memory_snapshot,
            'metrics': []
        }
        
        logger.debug(f"Started performance monitoring: {monitor_id}")
        return monitor_id
    
    def stop_performance_monitoring(self, monitor_id: str) -> PerformanceReport:
        """
        Stop performance monitoring and generate report
        
        Args:
            monitor_id: Monitor ID returned by start_performance_monitoring
            
        Returns:
            PerformanceReport with collected metrics
        """
        if monitor_id not in self.active_monitors:
            raise ValueError(f"Monitor ID not found: {monitor_id}")
        
        monitor_data = self.active_monitors[monitor_id]
        end_time = datetime.now()
        
        # Calculate duration
        duration = (end_time - monitor_data['start_time']).total_seconds() * 1000
        
        # Get final system state
        process = psutil.Process()
        final_memory = process.memory_info().rss / (1024**2)  # MB
        final_cpu = process.cpu_percent()
        
        # Calculate memory usage
        memory_usage = final_memory - monitor_data['initial_memory_mb']
        
        # Check for memory leaks if profiling enabled
        memory_leak_info = []
        if self.enable_memory_profiling and monitor_data['memory_snapshot']:
            current_snapshot = tracemalloc.take_snapshot()
            top_stats = current_snapshot.compare_to(monitor_data['memory_snapshot'], 'lineno')
            
            # Check for significant memory increases
            for stat in top_stats[:10]:
                if stat.size_diff > 1024 * 1024:  # > 1MB increase
                    memory_leak_info.append(f"Memory increase: {stat.size_diff / (1024**2):.1f}MB in {stat.traceback}")
        
        # Create performance report
        report = PerformanceReport(
            component_name=monitor_data['component_name'],
            operation=monitor_data['operation'],
            start_time=monitor_data['start_time'],
            end_time=end_time,
            duration_ms=duration,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=final_cpu,
            metrics=monitor_data['metrics'],
            errors=[],
            warnings=memory_leak_info
        )
        
        # Check against thresholds
        self._check_performance_thresholds(report)
        
        # Store in history
        self.performance_history[monitor_data['component_name']].append(report)
        
        # Clean up
        del self.active_monitors[monitor_id]
        
        logger.debug(f"Stopped performance monitoring: {monitor_id}, Duration: {duration:.2f}ms")
        return report
    
    def measure_page_load_time(self, page_name: str, load_function: Callable) -> PerformanceReport:
        """
        Measure page load time for a Streamlit page
        
        Args:
            page_name: Name of the page being loaded
            load_function: Function that loads the page
            
        Returns:
            PerformanceReport with page load metrics
        """
        monitor_id = self.start_performance_monitoring(page_name, "page_load")
        
        try:
            # Execute page load function
            start_time = time.time()
            result = load_function()
            end_time = time.time()
            
            # Record page-specific metrics
            load_time_ms = (end_time - start_time) * 1000
            self._record_metric_for_monitor(monitor_id, 'page_load_time', load_time_ms, 'ms')
            
            return self.stop_performance_monitoring(monitor_id)
            
        except Exception as e:
            report = self.stop_performance_monitoring(monitor_id)
            report.errors.append(f"Page load error: {str(e)}")
            return report
    
    def run_load_test(self, test_name: str, test_function: Callable, 
                     concurrent_users: int = 10, duration_seconds: int = 60) -> LoadTestResult:
        """
        Run load test with concurrent users
        
        Args:
            test_name: Name of the load test
            test_function: Function to execute for each user
            concurrent_users: Number of concurrent users to simulate
            duration_seconds: Duration of the test in seconds
            
        Returns:
            LoadTestResult with load test metrics
        """
        logger.info(f"Starting load test: {test_name} with {concurrent_users} users for {duration_seconds}s")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = []
        errors = []
        
        # Monitor system resources during test
        initial_memory = psutil.virtual_memory().used / (1024**2)
        peak_memory = initial_memory
        peak_cpu = 0
        
        def run_user_session():
            """Run a single user session"""
            session_results = []
            
            while time.time() < end_time:
                try:
                    request_start = time.time()
                    test_function()
                    request_end = time.time()
                    
                    response_time = (request_end - request_start) * 1000
                    session_results.append(response_time)
                    
                    # Brief pause between requests
                    time.sleep(0.1)
                    
                except Exception as e:
                    errors.append(str(e))
                    session_results.append(-1)  # Mark as error
            
            return session_results
        
        # Run concurrent user sessions
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(run_user_session) for _ in range(concurrent_users)]
            
            # Monitor resources while test runs
            def monitor_resources():
                nonlocal peak_memory, peak_cpu
                while time.time() < end_time:
                    current_memory = psutil.virtual_memory().used / (1024**2)
                    current_cpu = psutil.cpu_percent()
                    
                    peak_memory = max(peak_memory, current_memory)
                    peak_cpu = max(peak_cpu, current_cpu)
                    
                    time.sleep(1)
            
            monitor_thread = threading.Thread(target=monitor_resources)
            monitor_thread.start()
            
            # Collect results
            for future in as_completed(futures):
                try:
                    session_results = future.result()
                    results.extend(session_results)
                except Exception as e:
                    errors.append(f"Session error: {str(e)}")
            
            monitor_thread.join()
        
        # Calculate metrics
        successful_requests = [r for r in results if r > 0]
        failed_requests = [r for r in results if r < 0]
        
        total_requests = len(results)
        successful_count = len(successful_requests)
        failed_count = len(failed_requests)
        
        if successful_requests:
            avg_response_time = sum(successful_requests) / len(successful_requests)
            min_response_time = min(successful_requests)
            max_response_time = max(successful_requests)
        else:
            avg_response_time = min_response_time = max_response_time = 0
        
        actual_duration = time.time() - start_time
        requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0
        error_rate = (failed_count / total_requests * 100) if total_requests > 0 else 0
        
        return LoadTestResult(
            test_name=test_name,
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=successful_count,
            failed_requests=failed_count,
            average_response_time_ms=avg_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            requests_per_second=requests_per_second,
            error_rate_percent=error_rate,
            memory_peak_mb=peak_memory,
            cpu_peak_percent=peak_cpu,
            test_duration_seconds=actual_duration,
            timestamp=datetime.now()
        )
    
    def detect_memory_leaks(self, component_name: str, iterations: int = 100) -> Dict[str, Any]:
        """
        Detect memory leaks in a component by running it multiple times
        
        Args:
            component_name: Name of the component to test
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with memory leak analysis
        """
        if not self.enable_memory_profiling:
            return {'error': 'Memory profiling not enabled'}
        
        logger.info(f"Starting memory leak detection for {component_name}")
        
        # Take initial snapshot
        initial_snapshot = tracemalloc.take_snapshot()
        memory_usage = []
        
        # Run multiple iterations and track memory
        for i in range(iterations):
            gc.collect()  # Force garbage collection
            
            current_memory = psutil.Process().memory_info().rss / (1024**2)
            memory_usage.append(current_memory)
            
            # Take snapshot every 10 iterations
            if i % 10 == 0:
                current_snapshot = tracemalloc.take_snapshot()
                top_stats = current_snapshot.compare_to(initial_snapshot, 'lineno')
                
                # Log significant memory increases
                for stat in top_stats[:5]:
                    if stat.size_diff > 1024 * 1024:  # > 1MB
                        logger.warning(f"Memory increase detected: {stat.size_diff / (1024**2):.1f}MB")
        
        # Analyze memory trend
        if len(memory_usage) > 10:
            # Calculate trend (simple linear regression)
            n = len(memory_usage)
            x_sum = sum(range(n))
            y_sum = sum(memory_usage)
            xy_sum = sum(i * memory_usage[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            # Memory leak detected if slope is significantly positive
            leak_detected = slope > 0.1  # More than 0.1MB per iteration
            
            return {
                'component': component_name,
                'iterations': iterations,
                'initial_memory_mb': memory_usage[0],
                'final_memory_mb': memory_usage[-1],
                'memory_increase_mb': memory_usage[-1] - memory_usage[0],
                'memory_trend_slope': slope,
                'leak_detected': leak_detected,
                'memory_usage_history': memory_usage,
                'timestamp': datetime.now()
            }
        
        return {'error': 'Insufficient data for analysis'}
    
    def benchmark_component_performance(self, component_name: str, 
                                      benchmark_function: Callable, 
                                      iterations: int = 100) -> Dict[str, Any]:
        """
        Benchmark component performance over multiple iterations
        
        Args:
            component_name: Name of the component
            benchmark_function: Function to benchmark
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Starting performance benchmark for {component_name}")
        
        execution_times = []
        memory_usage = []
        errors = []
        
        for i in range(iterations):
            try:
                # Measure execution time
                start_time = time.time()
                benchmark_function()
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # ms
                execution_times.append(execution_time)
                
                # Measure memory usage
                current_memory = psutil.Process().memory_info().rss / (1024**2)
                memory_usage.append(current_memory)
                
            except Exception as e:
                errors.append(f"Iteration {i}: {str(e)}")
        
        if execution_times:
            return {
                'component': component_name,
                'iterations': len(execution_times),
                'avg_execution_time_ms': sum(execution_times) / len(execution_times),
                'min_execution_time_ms': min(execution_times),
                'max_execution_time_ms': max(execution_times),
                'median_execution_time_ms': sorted(execution_times)[len(execution_times) // 2],
                'avg_memory_usage_mb': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'execution_times': execution_times,
                'memory_usage': memory_usage,
                'errors': errors,
                'error_rate_percent': len(errors) / iterations * 100,
                'timestamp': datetime.now()
            }
        
        return {'error': 'No successful iterations', 'errors': errors}
    
    def generate_performance_report(self, component_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            component_name: Specific component to report on, or None for all
            
        Returns:
            Dictionary with performance report
        """
        report = {
            'timestamp': datetime.now(),
            'monitoring_duration_hours': 24,  # Default to last 24 hours
            'components': {}
        }
        
        # Filter components
        components_to_report = [component_name] if component_name else self.performance_history.keys()
        
        for comp_name in components_to_report:
            if comp_name in self.performance_history:
                history = list(self.performance_history[comp_name])
                
                if history:
                    # Filter for PerformanceReport objects only
                    reports = [r for r in history if hasattr(r, 'duration_ms')]
                    
                    if reports:
                        # Calculate aggregate metrics
                        durations = [r.duration_ms for r in reports]
                        memory_usage = [r.memory_usage_mb for r in reports]
                    
                        component_report = {
                            'total_operations': len(reports),
                            'avg_duration_ms': sum(durations) / len(durations),
                            'min_duration_ms': min(durations),
                            'max_duration_ms': max(durations),
                            'avg_memory_usage_mb': sum(memory_usage) / len(memory_usage),
                            'error_count': sum(len(r.errors) for r in reports),
                            'warning_count': sum(len(r.warnings) for r in reports),
                            'recent_operations': [
                                {
                                    'operation': r.operation,
                                    'duration_ms': r.duration_ms,
                                    'memory_usage_mb': r.memory_usage_mb,
                                    'timestamp': r.start_time.isoformat(),
                                    'errors': r.errors,
                                    'warnings': r.warnings
                                }
                                for r in reports[-10:]  # Last 10 operations
                            ]
                        }
                    else:
                        component_report = {
                            'total_operations': 0,
                            'avg_duration_ms': 0,
                            'min_duration_ms': 0,
                            'max_duration_ms': 0,
                            'avg_memory_usage_mb': 0,
                            'error_count': 0,
                            'warning_count': 0,
                            'recent_operations': []
                        }
                    
                    report['components'][comp_name] = component_report
        
        return report
    
    def _record_metric(self, name: str, value: float, unit: str, component: Optional[str] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            component=component
        )
        
        # Store in appropriate history
        key = component if component else 'system'
        self.performance_history[key].append(metric)
    
    def _record_metric_for_monitor(self, monitor_id: str, name: str, value: float, unit: str):
        """Record a metric for a specific monitor"""
        if monitor_id in self.active_monitors:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                component=self.active_monitors[monitor_id]['component_name']
            )
            self.active_monitors[monitor_id]['metrics'].append(metric)
    
    def _check_performance_thresholds(self, report: PerformanceReport):
        """Check performance report against thresholds"""
        # Check duration thresholds
        if report.operation in self.performance_thresholds:
            thresholds = self.performance_thresholds[report.operation]
            
            if 'critical_ms' in thresholds and report.duration_ms > thresholds['critical_ms']:
                report.errors.append(f"Critical performance threshold exceeded: {report.duration_ms:.2f}ms > {thresholds['critical_ms']}ms")
            elif 'warning_ms' in thresholds and report.duration_ms > thresholds['warning_ms']:
                report.warnings.append(f"Performance warning: {report.duration_ms:.2f}ms > {thresholds['warning_ms']}ms")
        
        # Check memory thresholds
        memory_thresholds = self.performance_thresholds.get('memory_usage', {})
        if 'critical_mb' in memory_thresholds and report.memory_usage_mb > memory_thresholds['critical_mb']:
            report.errors.append(f"Critical memory usage: {report.memory_usage_mb:.2f}MB > {memory_thresholds['critical_mb']}MB")
        elif 'warning_mb' in memory_thresholds and report.memory_usage_mb > memory_thresholds['warning_mb']:
            report.warnings.append(f"High memory usage: {report.memory_usage_mb:.2f}MB > {memory_thresholds['warning_mb']}MB")
    
    def save_report_to_file(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save performance report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        # Ensure results directory exists
        os.makedirs("results/performance_reports", exist_ok=True)
        filepath = os.path.join("results/performance_reports", filename)
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=serialize_datetime)
        
        logger.info(f"Performance report saved to: {filepath}")
        return filepath
    
    def cleanup(self):
        """Cleanup monitoring resources"""
        self.monitoring_enabled = False
        
        if self.enable_memory_profiling:
            tracemalloc.stop()
        
        logger.info("Performance monitoring cleanup completed")


# Global instance for easy access
ui_performance_monitor = UIPerformanceMonitor()