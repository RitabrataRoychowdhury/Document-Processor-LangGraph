#!/usr/bin/env python3
"""
Comprehensive Test Runner Script.

This script runs all UI component tests, backend endpoint tests, integration tests,
and performance tests with configurable options and detailed reporting.
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tests.test_comprehensive_suite import ComprehensiveTestSuite
from tests.performance.test_ui_performance import run_ui_performance_tests
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TestConfiguration:
    """Test configuration management."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.config = {
            'ui_tests': {
                'enabled': True,
                'timeout_seconds': 300,
                'coverage_threshold': 80
            },
            'api_tests': {
                'enabled': True,
                'timeout_seconds': 600,
                'base_url': 'http://localhost:8501',
                'retry_attempts': 3
            },
            'integration_tests': {
                'enabled': True,
                'timeout_seconds': 900,
                'concurrent_users': 5,
                'session_duration': 30
            },
            'performance_tests': {
                'enabled': False,  # Disabled by default due to resource intensity
                'load_test_users': 10,
                'load_test_duration': 60,
                'memory_leak_iterations': 100,
                'stability_test_minutes': 30
            },
            'reporting': {
                'formats': ['console', 'json'],
                'output_directory': 'test_results',
                'include_detailed_logs': True,
                'generate_html_report': False
            }
        }
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
            logger.info(f"Configuration loaded from {config_file}")
        except FileNotFoundError:
            logger.warning(f"Configuration file {config_file} not found, using defaults")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def _merge_config(self, new_config: dict):
        """Merge new configuration with existing configuration."""
        for section, values in new_config.items():
            if section in self.config:
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values
    
    def save_to_file(self, config_file: str):
        """Save current configuration to JSON file."""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Configuration saved to {config_file}")


class TestResultsManager:
    """Manage test results and reporting."""
    
    def __init__(self, output_directory: str = 'test_results'):
        """Initialize results manager."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def save_results(self, results: dict, test_type: str = 'comprehensive'):
        """Save test results to files."""
        # Save JSON results
        json_file = self.output_directory / f"{test_type}_results_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {json_file}")
        
        # Save summary report
        summary_file = self.output_directory / f"{test_type}_summary_{self.timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(self._generate_summary_report(results))
        logger.info(f"Summary saved to {summary_file}")
        
        return json_file, summary_file
    
    def _generate_summary_report(self, results: dict) -> str:
        """Generate a summary report from test results."""
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("TEST EXECUTION SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append(f"Timestamp: {datetime.now().isoformat()}")
        summary_lines.append("")
        
        # Extract key metrics
        if 'comprehensive_summary' in results:
            comp_summary = results['comprehensive_summary']
            overall_stats = comp_summary.get('overall_statistics', {})
            
            summary_lines.append("OVERALL RESULTS:")
            summary_lines.append(f"  Total Tests: {overall_stats.get('total_tests', 0)}")
            summary_lines.append(f"  Passed: {overall_stats.get('passed_tests', 0)}")
            summary_lines.append(f"  Failed: {overall_stats.get('failed_tests', 0)}")
            summary_lines.append(f"  Success Rate: {overall_stats.get('overall_success_rate', 0):.1f}%")
            summary_lines.append(f"  Duration: {comp_summary.get('total_duration_ms', 0):.0f}ms")
            summary_lines.append("")
            
            # Suite breakdown
            suite_summaries = comp_summary.get('suite_summaries', {})
            if suite_summaries:
                summary_lines.append("SUITE BREAKDOWN:")
                for suite_name, suite_data in suite_summaries.items():
                    summary_lines.append(f"  {suite_name.replace('_', ' ').title()}:")
                    summary_lines.append(f"    Success Rate: {suite_data.get('success_rate', 0):.1f}%")
                    summary_lines.append(f"    Tests: {suite_data.get('total_tests', 0)}")
                summary_lines.append("")
            
            # Recommendations
            recommendations = comp_summary.get('recommendations', [])
            if recommendations:
                summary_lines.append("RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations[:10], 1):
                    summary_lines.append(f"  {i}. {rec}")
                summary_lines.append("")
        
        # Performance results if available
        if 'performance_results' in results:
            perf_results = results['performance_results']
            summary_lines.append("PERFORMANCE RESULTS:")
            summary_lines.append(f"  Overall Score: {perf_results.get('overall_performance_score', 0):.1f}/100")
            
            if perf_results.get('load_test'):
                load_metrics = perf_results['load_test'].get('aggregate_metrics', {})
                summary_lines.append(f"  Load Test Success Rate: {load_metrics.get('success_rate', 0):.1f}%")
            
            if perf_results.get('memory_leak_test'):
                memory_test = perf_results['memory_leak_test']
                summary_lines.append(f"  Memory Leak Detected: {'Yes' if memory_test.get('leak_detected') else 'No'}")
            
            summary_lines.append("")
        
        summary_lines.append("=" * 80)
        
        return "\n".join(summary_lines)


def create_default_config_file():
    """Create a default configuration file."""
    config = TestConfiguration()
    config_file = 'test_config.json'
    config.save_to_file(config_file)
    print(f"Default configuration file created: {config_file}")
    print("Edit this file to customize test settings.")


def run_tests_with_config(config_file: str = None, **kwargs):
    """Run tests with configuration file and command line overrides."""
    # Load configuration
    config = TestConfiguration()
    if config_file and os.path.exists(config_file):
        config.load_from_file(config_file)
    
    # Apply command line overrides
    for key, value in kwargs.items():
        if value is not None:
            if '.' in key:
                section, setting = key.split('.', 1)
                if section in config.config:
                    config.config[section][setting] = value
            else:
                # Top-level setting
                for section in config.config.values():
                    if isinstance(section, dict) and key in section:
                        section[key] = value
    
    # Initialize results manager
    results_manager = TestResultsManager(config.config['reporting']['output_directory'])
    
    # Run comprehensive test suite
    test_suite = ComprehensiveTestSuite()
    
    logger.info("Starting comprehensive test execution...")
    
    comprehensive_results = test_suite.run_all_tests(
        include_ui=config.config['ui_tests']['enabled'],
        include_api=config.config['api_tests']['enabled'],
        include_integration=config.config['integration_tests']['enabled']
    )
    
    # Run performance tests if enabled
    performance_results = None
    if config.config['performance_tests']['enabled']:
        logger.info("Running performance tests...")
        try:
            performance_results = run_ui_performance_tests()
            comprehensive_results['performance_results'] = performance_results
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            comprehensive_results['performance_results'] = {'error': str(e)}
    
    # Save results
    json_file, summary_file = results_manager.save_results(comprehensive_results)
    
    # Generate reports
    report_formats = config.config['reporting']['formats']
    
    if 'console' in report_formats:
        console_report = test_suite.generate_report('console')
        print(console_report)
    
    if 'html' in report_formats or config.config['reporting']['generate_html_report']:
        html_file = results_manager.output_directory / f"test_report_{results_manager.timestamp}.html"
        test_suite.generate_report('html', str(html_file))
        logger.info(f"HTML report generated: {html_file}")
    
    # Return results for programmatic use
    return comprehensive_results, json_file, summary_file


def main():
    """Main function for command line execution."""
    parser = argparse.ArgumentParser(
        description='Run comprehensive test suite for QME system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comprehensive_tests.py --all
  python run_comprehensive_tests.py --ui --api --config test_config.json
  python run_comprehensive_tests.py --performance --output-dir results
  python run_comprehensive_tests.py --create-config
        """
    )
    
    # Test selection
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--ui', action='store_true', help='Run UI component tests')
    parser.add_argument('--api', action='store_true', help='Run backend endpoint tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    
    # Configuration
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--create-config', action='store_true', help='Create default configuration file')
    
    # Output options
    parser.add_argument('--output-dir', default='test_results', help='Output directory for results')
    parser.add_argument('--format', choices=['console', 'json', 'html'], action='append', help='Output formats')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML report')
    
    # Performance test options
    parser.add_argument('--load-users', type=int, help='Number of concurrent users for load testing')
    parser.add_argument('--load-duration', type=int, help='Load test duration in seconds')
    
    # Verbosity
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    
    args = parser.parse_args()
    
    # Handle create-config
    if args.create_config:
        create_default_config_file()
        return
    
    # Configure logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        import logging
        logging.getLogger().setLevel(logging.WARNING)
    
    # Determine which tests to run
    if not any([args.ui, args.api, args.integration, args.performance]):
        args.all = True
    
    # Prepare kwargs for configuration overrides
    kwargs = {}
    
    if args.all or args.ui:
        kwargs['ui_tests.enabled'] = True
    if args.all or args.api:
        kwargs['api_tests.enabled'] = True
    if args.all or args.integration:
        kwargs['integration_tests.enabled'] = True
    if args.performance:
        kwargs['performance_tests.enabled'] = True
    
    if args.output_dir:
        kwargs['reporting.output_directory'] = args.output_dir
    
    if args.format:
        kwargs['reporting.formats'] = args.format
    
    if args.html_report:
        kwargs['reporting.generate_html_report'] = True
    
    if args.load_users:
        kwargs['performance_tests.load_test_users'] = args.load_users
    
    if args.load_duration:
        kwargs['performance_tests.load_test_duration'] = args.load_duration
    
    try:
        # Run tests
        results, json_file, summary_file = run_tests_with_config(args.config, **kwargs)
        
        # Determine exit code based on results
        if 'comprehensive_summary' in results:
            success_rate = results['comprehensive_summary']['overall_statistics']['overall_success_rate']
            if success_rate < 70:
                print(f"\nCRITICAL: Test success rate is {success_rate:.1f}% (below 70%)")
                sys.exit(1)
            elif success_rate < 85:
                print(f"\nWARNING: Test success rate is {success_rate:.1f}% (below 85%)")
                sys.exit(2)
            else:
                print(f"\nSUCCESS: Test success rate is {success_rate:.1f}%")
                sys.exit(0)
        else:
            print("\nERROR: Could not determine test results")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()