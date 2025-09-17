"""
Comprehensive Test Suite Runner.

This module orchestrates all UI component tests, backend endpoint tests,
and end-to-end integration tests, providing unified reporting and coverage analysis.
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import argparse

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tests.ui.test_ui_components import run_ui_component_tests
from tests.api.test_backend_endpoints import run_backend_endpoint_tests
from tests.integration.test_end_to_end_workflows import run_end_to_end_integration_tests
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ComprehensiveTestSuite:
    """Comprehensive test suite runner and reporter."""
    
    def __init__(self):
        """Initialize the comprehensive test suite."""
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        self.total_duration_ms = 0
    
    def run_all_tests(self, include_ui: bool = True, include_api: bool = True, 
                     include_integration: bool = True) -> Dict[str, Any]:
        """Run all test suites based on configuration."""
        self.start_time = time.time()
        logger.info("Starting comprehensive test suite execution...")
        
        # UI Component Tests
        if include_ui:
            logger.info("Running UI component tests...")
            try:
                ui_results = run_ui_component_tests()
                self.test_results['ui_component_tests'] = ui_results
                logger.info(f"UI tests completed: {ui_results['success_rate']:.1f}% success rate")
            except Exception as e:
                logger.error(f"UI component tests failed: {e}")
                self.test_results['ui_component_tests'] = {
                    'error': str(e),
                    'success_rate': 0,
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 1
                }
        
        # Backend Endpoint Tests
        if include_api:
            logger.info("Running backend endpoint tests...")
            try:
                api_results = run_backend_endpoint_tests()
                self.test_results['backend_endpoint_tests'] = api_results
                logger.info(f"API tests completed: {api_results['overall_summary']['overall_success_rate']:.1f}% success rate")
            except Exception as e:
                logger.error(f"Backend endpoint tests failed: {e}")
                self.test_results['backend_endpoint_tests'] = {
                    'error': str(e),
                    'overall_summary': {
                        'overall_success_rate': 0,
                        'total_tests': 0,
                        'passed_tests': 0,
                        'failed_tests': 1
                    }
                }
        
        # End-to-End Integration Tests
        if include_integration:
            logger.info("Running end-to-end integration tests...")
            try:
                integration_results = run_end_to_end_integration_tests()
                self.test_results['integration_tests'] = integration_results
                logger.info(f"Integration tests completed: {integration_results['success_rate']:.1f}% success rate")
            except Exception as e:
                logger.error(f"Integration tests failed: {e}")
                self.test_results['integration_tests'] = {
                    'error': str(e),
                    'success_rate': 0,
                    'total_integration_tests': 0,
                    'successful_tests': 0,
                    'failed_tests': 1
                }
        
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000
        
        # Generate comprehensive summary
        summary = self._generate_comprehensive_summary()
        self.test_results['comprehensive_summary'] = summary
        
        logger.info(f"Comprehensive test suite completed in {self.total_duration_ms:.0f}ms")
        logger.info(f"Overall success rate: {summary['overall_success_rate']:.1f}%")
        
        return self.test_results
    
    def _generate_comprehensive_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        summary = {
            'execution_timestamp': datetime.now().isoformat(),
            'total_duration_ms': self.total_duration_ms,
            'test_suites_run': [],
            'overall_statistics': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'overall_success_rate': 0
            },
            'suite_summaries': {},
            'coverage_analysis': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Analyze UI component tests
        if 'ui_component_tests' in self.test_results:
            ui_results = self.test_results['ui_component_tests']
            summary['test_suites_run'].append('UI Components')
            
            if 'error' not in ui_results:
                summary['overall_statistics']['total_tests'] += ui_results.get('total_tests', 0)
                summary['overall_statistics']['passed_tests'] += ui_results.get('passed_tests', 0)
                summary['overall_statistics']['failed_tests'] += ui_results.get('failed_tests', 0)
                
                summary['suite_summaries']['ui_components'] = {
                    'success_rate': ui_results.get('success_rate', 0),
                    'total_tests': ui_results.get('total_tests', 0),
                    'execution_time_ms': ui_results.get('total_execution_time_ms', 0),
                    'coverage_percentage': ui_results.get('coverage', {}).get('coverage_percentage', 0)
                }
                
                # Add coverage analysis
                coverage_data = ui_results.get('coverage', {})
                summary['coverage_analysis']['ui_components'] = {
                    'covered_components': coverage_data.get('covered_components', 0),
                    'total_components': coverage_data.get('total_components', 0),
                    'coverage_percentage': coverage_data.get('coverage_percentage', 0),
                    'uncovered_components': coverage_data.get('uncovered_components', [])
                }
        
        # Analyze backend endpoint tests
        if 'backend_endpoint_tests' in self.test_results:
            api_results = self.test_results['backend_endpoint_tests']
            summary['test_suites_run'].append('Backend Endpoints')
            
            if 'error' not in api_results:
                overall_summary = api_results.get('overall_summary', {})
                summary['overall_statistics']['total_tests'] += overall_summary.get('total_tests', 0)
                summary['overall_statistics']['passed_tests'] += overall_summary.get('passed_tests', 0)
                summary['overall_statistics']['failed_tests'] += overall_summary.get('failed_tests', 0)
                
                summary['suite_summaries']['backend_endpoints'] = {
                    'success_rate': overall_summary.get('overall_success_rate', 0),
                    'total_tests': overall_summary.get('total_tests', 0),
                    'api_success_rate': overall_summary.get('api_success_rate', 0),
                    'service_success_rate': overall_summary.get('service_success_rate', 0)
                }
                
                # Add performance metrics
                api_endpoint_results = api_results.get('api_endpoint_tests', {})
                summary['performance_metrics']['api_endpoints'] = {
                    'average_response_time_ms': api_endpoint_results.get('average_response_time_ms', 0),
                    'total_response_time_ms': api_endpoint_results.get('total_response_time_ms', 0)
                }
        
        # Analyze integration tests
        if 'integration_tests' in self.test_results:
            integration_results = self.test_results['integration_tests']
            summary['test_suites_run'].append('End-to-End Integration')
            
            if 'error' not in integration_results:
                summary['overall_statistics']['total_tests'] += integration_results.get('total_integration_tests', 0)
                summary['overall_statistics']['passed_tests'] += integration_results.get('successful_tests', 0)
                summary['overall_statistics']['failed_tests'] += integration_results.get('failed_tests', 0)
                
                summary['suite_summaries']['integration_tests'] = {
                    'success_rate': integration_results.get('success_rate', 0),
                    'total_tests': integration_results.get('total_integration_tests', 0),
                    'execution_time_ms': integration_results.get('total_execution_time_ms', 0),
                    'average_test_time_ms': integration_results.get('average_test_time_ms', 0)
                }
                
                # Analyze concurrent user performance
                for test_result in integration_results.get('test_results', []):
                    if test_result.get('test_category') == 'concurrent_users':
                        summary['performance_metrics']['concurrent_users'] = {
                            'total_users': test_result.get('total_users', 0),
                            'successful_users': test_result.get('successful_users', 0),
                            'user_success_rate': test_result.get('success_rate', 0),
                            'average_duration_ms': test_result.get('average_duration_ms', 0)
                        }
        
        # Calculate overall success rate
        total_tests = summary['overall_statistics']['total_tests']
        passed_tests = summary['overall_statistics']['passed_tests']
        summary['overall_statistics']['overall_success_rate'] = (
            (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        )
        
        # Generate recommendations
        summary['recommendations'] = self._generate_recommendations(summary)
        
        return summary
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        overall_success_rate = summary['overall_statistics']['overall_success_rate']
        
        # Overall success rate recommendations
        if overall_success_rate < 70:
            recommendations.append("CRITICAL: Overall success rate is below 70%. Immediate attention required.")
        elif overall_success_rate < 85:
            recommendations.append("WARNING: Overall success rate is below 85%. Consider investigating failing tests.")
        elif overall_success_rate >= 95:
            recommendations.append("EXCELLENT: High success rate achieved. Consider adding more edge case tests.")
        
        # UI component coverage recommendations
        ui_coverage = summary.get('coverage_analysis', {}).get('ui_components', {})
        if ui_coverage.get('coverage_percentage', 0) < 80:
            recommendations.append("Increase UI component test coverage. Target: 80%+")
            uncovered = ui_coverage.get('uncovered_components', [])
            if uncovered:
                recommendations.append(f"Add tests for uncovered components: {', '.join(uncovered[:3])}")
        
        # Performance recommendations
        api_perf = summary.get('performance_metrics', {}).get('api_endpoints', {})
        avg_response_time = api_perf.get('average_response_time_ms', 0)
        if avg_response_time > 2000:
            recommendations.append("API response times are high (>2s). Consider performance optimization.")
        
        concurrent_perf = summary.get('performance_metrics', {}).get('concurrent_users', {})
        user_success_rate = concurrent_perf.get('user_success_rate', 100)
        if user_success_rate < 90:
            recommendations.append("Concurrent user success rate is low. Check for race conditions or resource limits.")
        
        # Test suite specific recommendations
        suite_summaries = summary.get('suite_summaries', {})
        
        for suite_name, suite_data in suite_summaries.items():
            suite_success_rate = suite_data.get('success_rate', 0)
            if suite_success_rate < 80:
                recommendations.append(f"Investigate failures in {suite_name} test suite ({suite_success_rate:.1f}% success rate)")
        
        return recommendations
    
    def generate_report(self, output_format: str = 'console', output_file: str = None) -> str:
        """Generate test report in specified format."""
        if output_format == 'json':
            return self._generate_json_report(output_file)
        elif output_format == 'html':
            return self._generate_html_report(output_file)
        else:
            return self._generate_console_report()
    
    def _generate_console_report(self) -> str:
        """Generate console-friendly test report."""
        if not self.test_results:
            return "No test results available."
        
        summary = self.test_results.get('comprehensive_summary', {})
        overall_stats = summary.get('overall_statistics', {})
        
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE TEST SUITE RESULTS")
        report.append("=" * 80)
        report.append(f"Execution Time: {summary.get('total_duration_ms', 0):.0f}ms")
        report.append(f"Timestamp: {summary.get('execution_timestamp', 'Unknown')}")
        report.append("")
        
        # Overall statistics
        report.append("OVERALL STATISTICS:")
        report.append(f"  Total Tests: {overall_stats.get('total_tests', 0)}")
        report.append(f"  Passed: {overall_stats.get('passed_tests', 0)}")
        report.append(f"  Failed: {overall_stats.get('failed_tests', 0)}")
        report.append(f"  Success Rate: {overall_stats.get('overall_success_rate', 0):.1f}%")
        report.append("")
        
        # Suite summaries
        suite_summaries = summary.get('suite_summaries', {})
        if suite_summaries:
            report.append("TEST SUITE BREAKDOWN:")
            for suite_name, suite_data in suite_summaries.items():
                report.append(f"  {suite_name.replace('_', ' ').title()}:")
                report.append(f"    Success Rate: {suite_data.get('success_rate', 0):.1f}%")
                report.append(f"    Total Tests: {suite_data.get('total_tests', 0)}")
                if 'execution_time_ms' in suite_data:
                    report.append(f"    Execution Time: {suite_data['execution_time_ms']:.0f}ms")
                report.append("")
        
        # Coverage analysis
        coverage_analysis = summary.get('coverage_analysis', {})
        if coverage_analysis:
            report.append("COVERAGE ANALYSIS:")
            for component, coverage_data in coverage_analysis.items():
                report.append(f"  {component.replace('_', ' ').title()}:")
                report.append(f"    Coverage: {coverage_data.get('coverage_percentage', 0):.1f}%")
                report.append(f"    Covered: {coverage_data.get('covered_components', 0)}")
                report.append(f"    Total: {coverage_data.get('total_components', 0)}")
                uncovered = coverage_data.get('uncovered_components', [])
                if uncovered:
                    report.append(f"    Uncovered: {', '.join(uncovered[:5])}")
                report.append("")
        
        # Performance metrics
        performance_metrics = summary.get('performance_metrics', {})
        if performance_metrics:
            report.append("PERFORMANCE METRICS:")
            for metric_name, metric_data in performance_metrics.items():
                report.append(f"  {metric_name.replace('_', ' ').title()}:")
                for key, value in metric_data.items():
                    if isinstance(value, float):
                        report.append(f"    {key.replace('_', ' ').title()}: {value:.1f}")
                    else:
                        report.append(f"    {key.replace('_', ' ').title()}: {value}")
                report.append("")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            report.append("RECOMMENDATIONS:")
            for i, recommendation in enumerate(recommendations, 1):
                report.append(f"  {i}. {recommendation}")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_json_report(self, output_file: str = None) -> str:
        """Generate JSON test report."""
        json_report = json.dumps(self.test_results, indent=2, default=str)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_report)
            logger.info(f"JSON report saved to {output_file}")
        
        return json_report
    
    def _generate_html_report(self, output_file: str = None) -> str:
        """Generate HTML test report."""
        summary = self.test_results.get('comprehensive_summary', {})
        overall_stats = summary.get('overall_statistics', {})
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comprehensive Test Suite Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .success { color: green; }
                .warning { color: orange; }
                .error { color: red; }
                .metric { margin: 10px 0; }
                .suite { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .recommendation { background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Comprehensive Test Suite Results</h1>
                <p>Execution Time: {duration}ms | Timestamp: {timestamp}</p>
            </div>
            
            <div class="metric">
                <h2>Overall Statistics</h2>
                <p>Total Tests: {total_tests}</p>
                <p>Passed: <span class="success">{passed_tests}</span></p>
                <p>Failed: <span class="error">{failed_tests}</span></p>
                <p>Success Rate: <span class="{success_class}">{success_rate:.1f}%</span></p>
            </div>
            
            {suite_sections}
            
            {recommendations_section}
        </body>
        </html>
        """
        
        # Determine success rate class
        success_rate = overall_stats.get('overall_success_rate', 0)
        if success_rate >= 90:
            success_class = 'success'
        elif success_rate >= 70:
            success_class = 'warning'
        else:
            success_class = 'error'
        
        # Generate suite sections
        suite_sections = ""
        suite_summaries = summary.get('suite_summaries', {})
        for suite_name, suite_data in suite_summaries.items():
            suite_sections += f"""
            <div class="suite">
                <h3>{suite_name.replace('_', ' ').title()}</h3>
                <p>Success Rate: {suite_data.get('success_rate', 0):.1f}%</p>
                <p>Total Tests: {suite_data.get('total_tests', 0)}</p>
            </div>
            """
        
        # Generate recommendations section
        recommendations_section = ""
        recommendations = summary.get('recommendations', [])
        if recommendations:
            recommendations_section = "<h2>Recommendations</h2>"
            for recommendation in recommendations:
                recommendations_section += f'<div class="recommendation">{recommendation}</div>'
        
        html_report = html_template.format(
            duration=summary.get('total_duration_ms', 0),
            timestamp=summary.get('execution_timestamp', 'Unknown'),
            total_tests=overall_stats.get('total_tests', 0),
            passed_tests=overall_stats.get('passed_tests', 0),
            failed_tests=overall_stats.get('failed_tests', 0),
            success_rate=success_rate,
            success_class=success_class,
            suite_sections=suite_sections,
            recommendations_section=recommendations_section
        )
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(html_report)
            logger.info(f"HTML report saved to {output_file}")
        
        return html_report


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--ui', action='store_true', help='Run UI component tests')
    parser.add_argument('--api', action='store_true', help='Run backend endpoint tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--format', choices=['console', 'json', 'html'], default='console', help='Output format')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Determine which tests to run
    if not any([args.ui, args.api, args.integration]):
        args.all = True
    
    include_ui = args.all or args.ui
    include_api = args.all or args.api
    include_integration = args.all or args.integration
    
    # Run tests
    test_suite = ComprehensiveTestSuite()
    results = test_suite.run_all_tests(
        include_ui=include_ui,
        include_api=include_api,
        include_integration=include_integration
    )
    
    # Generate and display report
    report = test_suite.generate_report(args.format, args.output)
    
    if args.format == 'console':
        print(report)
    
    # Exit with appropriate code
    summary = results.get('comprehensive_summary', {})
    overall_stats = summary.get('overall_statistics', {})
    success_rate = overall_stats.get('overall_success_rate', 0)
    
    if success_rate < 70:
        sys.exit(1)  # Critical failure
    elif success_rate < 85:
        sys.exit(2)  # Warning level
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()