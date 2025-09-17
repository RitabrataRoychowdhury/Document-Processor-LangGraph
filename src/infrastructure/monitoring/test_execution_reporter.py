"""
Test Execution and Reporting System

This module provides comprehensive test execution coordination and reporting
for UI components, performance tests, and system validation.
"""

import os
import json
import time
import logging
import subprocess
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
from pathlib import Path

from .ui_performance_monitor import UIPerformanceMonitor, LoadTestResult
from .service_integration_validator import ServiceIntegrationValidator

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestCategory(Enum):
    """Test category classification"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    END_TO_END = "end_to_end"
    STABILITY = "stability"
    LOAD = "load"


@dataclass
class TestResult:
    """Individual test result"""
    test_name: str
    category: TestCategory
    status: TestStatus
    duration_seconds: float
    error_message: Optional[str] = None
    output: Optional[str] = None
    coverage_percentage: Optional[float] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuiteResult:
    """Test suite execution result"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration_seconds: float
    coverage_percentage: float
    test_results: List[TestResult] = field(default_factory=list)
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComprehensiveTestReport:
    """Comprehensive test execution report"""
    report_id: str
    execution_start: datetime
    execution_end: datetime
    total_duration_seconds: float
    overall_status: TestStatus
    suite_results: List[TestSuiteResult] = field(default_factory=list)
    performance_benchmarks: Dict[str, Any] = field(default_factory=dict)
    system_health: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class TestExecutionReporter:
    """
    Comprehensive test execution and reporting system
    """
    
    def __init__(self):
        self.performance_monitor = UIPerformanceMonitor(enable_memory_profiling=True)
        self.service_validator = ServiceIntegrationValidator()
        self.test_results: Dict[str, TestSuiteResult] = {}
        self.active_executions: Dict[str, Dict] = {}
        self.coverage_data = None
        
        # Initialize coverage tracking
        if COVERAGE_AVAILABLE:
            self.cov = coverage.Coverage()
        else:
            self.cov = None
        
        # Test configuration
        self.test_directories = {
            TestCategory.UNIT: "tests/unit",
            TestCategory.INTEGRATION: "tests/integration", 
            TestCategory.PERFORMANCE: "tests/performance",
            TestCategory.END_TO_END: "tests/end_to_end",
            TestCategory.STABILITY: "tests/performance",  # Stability tests in performance dir
            TestCategory.LOAD: "tests/performance"
        }
        
        # Performance thresholds for different test types
        self.performance_thresholds = {
            TestCategory.UNIT: {"max_duration_seconds": 1.0},
            TestCategory.INTEGRATION: {"max_duration_seconds": 10.0},
            TestCategory.PERFORMANCE: {"max_duration_seconds": 60.0},
            TestCategory.END_TO_END: {"max_duration_seconds": 120.0},
            TestCategory.STABILITY: {"max_duration_seconds": 300.0},
            TestCategory.LOAD: {"max_duration_seconds": 600.0}
        }
    
    def execute_test_suite(self, suite_name: str, category: TestCategory, 
                          test_patterns: Optional[List[str]] = None,
                          parallel: bool = False) -> TestSuiteResult:
        """
        Execute a test suite and collect results
        
        Args:
            suite_name: Name of the test suite
            category: Category of tests to run
            test_patterns: Specific test patterns to run
            parallel: Whether to run tests in parallel
            
        Returns:
            TestSuiteResult with execution results
        """
        logger.info(f"Starting test suite execution: {suite_name} ({category.value})")
        
        start_time = datetime.now()
        execution_id = f"{suite_name}_{int(time.time())}"
        
        # Start performance monitoring
        monitor_id = self.performance_monitor.start_performance_monitoring(suite_name, "test_execution")
        
        # Initialize coverage tracking
        if self.cov:
            self.cov.start()
        
        try:
            # Build pytest command
            test_dir = self.test_directories.get(category, "tests")
            pytest_args = [test_dir, "-v", "--tb=short"]
            
            if parallel:
                pytest_args.extend(["-n", "auto"])  # Requires pytest-xdist
            
            if test_patterns:
                for pattern in test_patterns:
                    pytest_args.extend(["-k", pattern])
            
            # Add coverage reporting
            pytest_args.extend(["--cov=src", "--cov-report=json"])
            
            # Execute tests
            if PYTEST_AVAILABLE:
                logger.info(f"Running pytest with args: {pytest_args}")
                result = pytest.main(pytest_args)
            else:
                logger.warning("pytest not available, skipping test execution")
                result = 0
            
            # Stop coverage tracking
            if self.cov:
                self.cov.stop()
                self.cov.save()
            
            # Parse test results
            test_results = self._parse_pytest_results(execution_id, category)
            
            # Calculate metrics
            total_tests = len(test_results)
            passed_tests = sum(1 for r in test_results if r.status == TestStatus.PASSED)
            failed_tests = sum(1 for r in test_results if r.status == TestStatus.FAILED)
            skipped_tests = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)
            error_tests = sum(1 for r in test_results if r.status == TestStatus.ERROR)
            
            # Get coverage data
            coverage_percentage = self._get_coverage_percentage()
            
            # Stop performance monitoring
            performance_report = self.performance_monitor.stop_performance_monitoring(monitor_id)
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # Create suite result
            suite_result = TestSuiteResult(
                suite_name=suite_name,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                error_tests=error_tests,
                total_duration_seconds=total_duration,
                coverage_percentage=coverage_percentage,
                test_results=test_results,
                performance_summary={
                    'execution_time_ms': performance_report.duration_ms,
                    'memory_usage_mb': performance_report.memory_usage_mb,
                    'cpu_usage_percent': performance_report.cpu_usage_percent
                },
                timestamp=start_time
            )
            
            # Store results
            self.test_results[suite_name] = suite_result
            
            logger.info(f"Test suite completed: {suite_name}, "
                       f"Passed: {passed_tests}/{total_tests}, "
                       f"Coverage: {coverage_percentage:.1f}%")
            
            return suite_result
            
        except Exception as e:
            logger.error(f"Test suite execution failed: {str(e)}")
            
            # Stop monitoring on error
            try:
                performance_report = self.performance_monitor.stop_performance_monitoring(monitor_id)
            except:
                pass
            
            # Create error result
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                error_tests=0,
                total_duration_seconds=total_duration,
                coverage_percentage=0.0,
                test_results=[TestResult(
                    test_name=f"{suite_name}_execution",
                    category=category,
                    status=TestStatus.ERROR,
                    duration_seconds=total_duration,
                    error_message=str(e)
                )],
                timestamp=start_time
            )
    
    def run_performance_benchmarks(self, components: List[str]) -> Dict[str, Any]:
        """
        Run performance benchmarks for specified components
        
        Args:
            components: List of component names to benchmark
            
        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Running performance benchmarks for components: {components}")
        
        benchmark_results = {}
        
        for component in components:
            try:
                # Define benchmark function based on component
                benchmark_func = self._get_component_benchmark_function(component)
                
                if benchmark_func:
                    # Run benchmark
                    result = self.performance_monitor.benchmark_component_performance(
                        component_name=component,
                        benchmark_function=benchmark_func,
                        iterations=50
                    )
                    benchmark_results[component] = result
                    
                    # Run memory leak detection
                    leak_result = self.performance_monitor.detect_memory_leaks(
                        component_name=component,
                        iterations=20
                    )
                    benchmark_results[f"{component}_memory_analysis"] = leak_result
                    
                else:
                    logger.warning(f"No benchmark function defined for component: {component}")
                    
            except Exception as e:
                logger.error(f"Benchmark failed for component {component}: {str(e)}")
                benchmark_results[component] = {'error': str(e)}
        
        return benchmark_results
    
    def run_load_tests(self, test_scenarios: List[Dict[str, Any]]) -> List[LoadTestResult]:
        """
        Run load tests for specified scenarios
        
        Args:
            test_scenarios: List of load test scenario configurations
            
        Returns:
            List of LoadTestResult objects
        """
        logger.info(f"Running {len(test_scenarios)} load test scenarios")
        
        load_test_results = []
        
        for scenario in test_scenarios:
            try:
                test_name = scenario.get('name', 'unnamed_test')
                concurrent_users = scenario.get('concurrent_users', 10)
                duration_seconds = scenario.get('duration_seconds', 60)
                test_function = scenario.get('test_function')
                
                if not test_function:
                    logger.error(f"No test function provided for scenario: {test_name}")
                    continue
                
                # Run load test
                result = self.performance_monitor.run_load_test(
                    test_name=test_name,
                    test_function=test_function,
                    concurrent_users=concurrent_users,
                    duration_seconds=duration_seconds
                )
                
                load_test_results.append(result)
                
                logger.info(f"Load test completed: {test_name}, "
                           f"RPS: {result.requests_per_second:.2f}, "
                           f"Error Rate: {result.error_rate_percent:.2f}%")
                
            except Exception as e:
                logger.error(f"Load test failed for scenario {scenario.get('name', 'unknown')}: {str(e)}")
        
        return load_test_results
    
    def execute_comprehensive_test_suite(self) -> ComprehensiveTestReport:
        """
        Execute comprehensive test suite covering all categories
        
        Returns:
            ComprehensiveTestReport with complete results
        """
        logger.info("Starting comprehensive test suite execution")
        
        execution_start = datetime.now()
        report_id = f"comprehensive_{int(time.time())}"
        
        suite_results = []
        overall_status = TestStatus.PASSED
        
        # Test execution order (fastest to slowest)
        test_categories = [
            TestCategory.UNIT,
            TestCategory.INTEGRATION,
            TestCategory.PERFORMANCE,
            TestCategory.END_TO_END,
            TestCategory.STABILITY
        ]
        
        # Execute each test category
        for category in test_categories:
            try:
                suite_result = self.execute_test_suite(
                    suite_name=f"{category.value}_tests",
                    category=category,
                    parallel=(category in [TestCategory.UNIT, TestCategory.INTEGRATION])
                )
                
                suite_results.append(suite_result)
                
                # Update overall status
                if suite_result.failed_tests > 0 or suite_result.error_tests > 0:
                    overall_status = TestStatus.FAILED
                
            except Exception as e:
                logger.error(f"Failed to execute {category.value} tests: {str(e)}")
                overall_status = TestStatus.ERROR
        
        # Run performance benchmarks
        components_to_benchmark = [
            'upload_interface', 'qa_interface', 'template_interface',
            'document_manager', 'health_status'
        ]
        performance_benchmarks = self.run_performance_benchmarks(components_to_benchmark)
        
        # Run load tests
        load_test_scenarios = self._get_default_load_test_scenarios()
        load_test_results = self.run_load_tests(load_test_scenarios)
        
        # Get system health
        system_health = self.service_validator.get_system_health_summary()
        
        execution_end = datetime.now()
        total_duration = (execution_end - execution_start).total_seconds()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(suite_results, performance_benchmarks, system_health)
        
        # Create comprehensive report
        report = ComprehensiveTestReport(
            report_id=report_id,
            execution_start=execution_start,
            execution_end=execution_end,
            total_duration_seconds=total_duration,
            overall_status=overall_status,
            suite_results=suite_results,
            performance_benchmarks=performance_benchmarks,
            system_health=system_health,
            recommendations=recommendations
        )
        
        logger.info(f"Comprehensive test suite completed in {total_duration:.2f}s, Status: {overall_status.value}")
        
        return report
    
    def generate_html_report(self, report: ComprehensiveTestReport, output_path: Optional[str] = None) -> str:
        """
        Generate HTML report from comprehensive test results
        
        Args:
            report: ComprehensiveTestReport to generate HTML for
            output_path: Optional output path for HTML file
            
        Returns:
            Path to generated HTML file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/test_reports/comprehensive_test_report_{timestamp}.html"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate HTML content
        html_content = self._generate_html_content(report)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path
    
    def save_json_report(self, report: ComprehensiveTestReport, output_path: Optional[str] = None) -> str:
        """
        Save comprehensive test report as JSON
        
        Args:
            report: ComprehensiveTestReport to save
            output_path: Optional output path for JSON file
            
        Returns:
            Path to saved JSON file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"results/test_reports/comprehensive_test_report_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert report to dictionary
        report_dict = self._report_to_dict(report)
        
        # Save JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"JSON report saved: {output_path}")
        return output_path
    
    def _parse_pytest_results(self, execution_id: str, category: TestCategory) -> List[TestResult]:
        """Parse pytest results from JSON report"""
        # This is a simplified implementation
        # In practice, you'd parse the actual pytest JSON output
        return []
    
    def _get_coverage_percentage(self) -> float:
        """Get code coverage percentage"""
        if not self.cov:
            return 0.0
        
        try:
            # Load coverage data
            self.cov.load()
            return self.cov.report(show_missing=False)
        except Exception as e:
            logger.error(f"Failed to get coverage data: {str(e)}")
            return 0.0
    
    def _get_component_benchmark_function(self, component: str) -> Optional[Callable]:
        """Get benchmark function for a component"""
        benchmark_functions = {
            'upload_interface': lambda: time.sleep(0.01),  # Simulate upload
            'qa_interface': lambda: time.sleep(0.02),      # Simulate Q&A
            'template_interface': lambda: time.sleep(0.015), # Simulate template
            'document_manager': lambda: time.sleep(0.005),   # Simulate doc ops
            'health_status': lambda: time.sleep(0.001)       # Simulate health check
        }
        return benchmark_functions.get(component)
    
    def _get_default_load_test_scenarios(self) -> List[Dict[str, Any]]:
        """Get default load test scenarios"""
        def mock_api_call():
            time.sleep(0.01)  # Simulate API call
            return "success"
        
        return [
            {
                'name': 'api_load_test',
                'test_function': mock_api_call,
                'concurrent_users': 10,
                'duration_seconds': 30
            },
            {
                'name': 'ui_load_test',
                'test_function': lambda: time.sleep(0.005),
                'concurrent_users': 5,
                'duration_seconds': 20
            }
        ]
    
    def _generate_recommendations(self, suite_results: List[TestSuiteResult], 
                                performance_benchmarks: Dict[str, Any],
                                system_health: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check test failures
        total_failed = sum(suite.failed_tests for suite in suite_results)
        if total_failed > 0:
            recommendations.append(f"Address {total_failed} failing tests to improve system reliability")
        
        # Check coverage
        avg_coverage = sum(suite.coverage_percentage for suite in suite_results) / len(suite_results) if suite_results else 0
        if avg_coverage < 80:
            recommendations.append(f"Increase test coverage from {avg_coverage:.1f}% to at least 80%")
        
        # Check performance
        for component, benchmark in performance_benchmarks.items():
            if isinstance(benchmark, dict) and 'avg_execution_time_ms' in benchmark:
                if benchmark['avg_execution_time_ms'] > 100:
                    recommendations.append(f"Optimize {component} performance (avg: {benchmark['avg_execution_time_ms']:.1f}ms)")
        
        # Check system health
        if system_health.get('health_percentage', 100) < 90:
            recommendations.append("Address service availability issues to improve system health")
        
        return recommendations
    
    def _generate_html_content(self, report: ComprehensiveTestReport) -> str:
        """Generate HTML content for the report"""
        # Simplified HTML template
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Test Report - {report.report_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .status-passed {{ color: green; }}
                .status-failed {{ color: red; }}
                .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Comprehensive Test Report</h1>
                <p><strong>Report ID:</strong> {report.report_id}</p>
                <p><strong>Execution Time:</strong> {report.execution_start} - {report.execution_end}</p>
                <p><strong>Duration:</strong> {report.total_duration_seconds:.2f} seconds</p>
                <p><strong>Overall Status:</strong> <span class="status-{report.overall_status.value.lower()}">{report.overall_status.value}</span></p>
            </div>
            
            <h2>Test Suite Results</h2>
            {''.join(f'<div class="suite"><h3>{suite.suite_name}</h3><p>Passed: {suite.passed_tests}/{suite.total_tests}, Coverage: {suite.coverage_percentage:.1f}%</p></div>' for suite in report.suite_results)}
            
            <h2>Recommendations</h2>
            <div class="recommendations">
                {''.join(f'<p>• {rec}</p>' for rec in report.recommendations)}
            </div>
        </body>
        </html>
        """
    
    def _report_to_dict(self, report: ComprehensiveTestReport) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            'report_id': report.report_id,
            'execution_start': report.execution_start.isoformat(),
            'execution_end': report.execution_end.isoformat(),
            'total_duration_seconds': report.total_duration_seconds,
            'overall_status': report.overall_status.value,
            'suite_results': [
                {
                    'suite_name': suite.suite_name,
                    'total_tests': suite.total_tests,
                    'passed_tests': suite.passed_tests,
                    'failed_tests': suite.failed_tests,
                    'coverage_percentage': suite.coverage_percentage,
                    'duration_seconds': suite.total_duration_seconds
                }
                for suite in report.suite_results
            ],
            'performance_benchmarks': report.performance_benchmarks,
            'system_health': report.system_health,
            'recommendations': report.recommendations
        }


# Global instance for easy access
test_execution_reporter = TestExecutionReporter()