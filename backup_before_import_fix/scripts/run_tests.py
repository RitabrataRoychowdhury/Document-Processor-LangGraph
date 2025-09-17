#!/usr/bin/env python3
"""
Comprehensive test runner for the QME system.

This script provides various test execution options including unit tests,
integration tests, performance tests, and coverage reporting.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import time


class TestRunner:
    """Test runner with comprehensive options and reporting."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results: Dict[str, Any] = {}
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> bool:
        """Run unit tests."""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest", "tests/unit/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov/unit",
                "--cov-report=xml:coverage-unit.xml"
            ])
        
        cmd.extend([
            "--junit-xml=test-results-unit.xml",
            "-m", "unit"
        ])
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.test_results['unit_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        if success:
            print("✅ Unit tests passed")
        else:
            print("❌ Unit tests failed")
        
        return success
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/integration/",
            "--junit-xml=test-results-integration.xml",
            "-m", "integration"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.test_results['integration_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        if success:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
        
        return success
    
    def run_end_to_end_tests(self, verbose: bool = False) -> bool:
        """Run end-to-end tests."""
        print("🎯 Running end-to-end tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/end_to_end/",
            "--junit-xml=test-results-e2e.xml",
            "-m", "e2e"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.test_results['e2e_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        if success:
            print("✅ End-to-end tests passed")
        else:
            print("❌ End-to-end tests failed")
        
        return success
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """Run performance tests."""
        print("⚡ Running performance tests...")
        
        cmd = [
            "python", "-m", "pytest", "tests/performance/",
            "--benchmark-only",
            "--benchmark-json=benchmark-results.json",
            "--junit-xml=test-results-performance.xml",
            "-m", "benchmark"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        self.test_results['performance_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode
        }
        
        if success:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
        
        return success
    
    def run_security_tests(self) -> bool:
        """Run security tests with bandit."""
        print("🔒 Running security tests...")
        
        cmd = ["python", "-m", "bandit", "-r", "src/", "-f", "json", "-o", "security-report.json"]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        # Bandit returns non-zero for security issues, but we want to capture the report
        success = result.returncode in [0, 1]  # 0 = no issues, 1 = issues found
        
        self.test_results['security_tests'] = {
            'success': success,
            'command': ' '.join(cmd),
            'return_code': result.returncode,
            'output': result.stdout,
            'errors': result.stderr
        }
        
        if result.returncode == 0:
            print("✅ No security issues found")
        elif result.returncode == 1:
            print("⚠️  Security issues found - check security-report.json")
        else:
            print("❌ Security scan failed")
            success = False
        
        return success
    
    def run_code_quality_checks(self) -> bool:
        """Run code quality checks."""
        print("📊 Running code quality checks...")
        
        checks = []
        
        # Black formatting check
        print("  Checking code formatting with Black...")
        result = subprocess.run(
            ["python", "-m", "black", "--check", "--diff", "src/", "tests/"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        checks.append(('black', result.returncode == 0, result.stdout, result.stderr))
        
        # isort import sorting check
        print("  Checking import sorting with isort...")
        result = subprocess.run(
            ["python", "-m", "isort", "--check-only", "--diff", "src/", "tests/"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        checks.append(('isort', result.returncode == 0, result.stdout, result.stderr))
        
        # Flake8 linting
        print("  Running linting with flake8...")
        result = subprocess.run(
            ["python", "-m", "flake8", "src/", "tests/"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        checks.append(('flake8', result.returncode == 0, result.stdout, result.stderr))
        
        # MyPy type checking
        print("  Running type checking with mypy...")
        result = subprocess.run(
            ["python", "-m", "mypy", "src/"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        checks.append(('mypy', result.returncode == 0, result.stdout, result.stderr))
        
        # Evaluate results
        all_passed = all(passed for _, passed, _, _ in checks)
        
        self.test_results['code_quality'] = {
            'success': all_passed,
            'checks': {
                name: {
                    'passed': passed,
                    'stdout': stdout,
                    'stderr': stderr
                }
                for name, passed, stdout, stderr in checks
            }
        }
        
        for name, passed, stdout, stderr in checks:
            if passed:
                print(f"  ✅ {name} passed")
            else:
                print(f"  ❌ {name} failed")
                if stdout:
                    print(f"    Output: {stdout[:200]}...")
                if stderr:
                    print(f"    Errors: {stderr[:200]}...")
        
        return all_passed
    
    def generate_coverage_report(self) -> bool:
        """Generate comprehensive coverage report."""
        print("📈 Generating coverage report...")
        
        # Combine coverage data if multiple test runs
        cmd = ["python", "-m", "coverage", "combine"]
        subprocess.run(cmd, cwd=self.project_root)
        
        # Generate HTML report
        cmd = ["python", "-m", "coverage", "html", "-d", "htmlcov/combined"]
        result = subprocess.run(cmd, cwd=self.project_root)
        
        # Generate XML report for CI/CD
        cmd = ["python", "-m", "coverage", "xml", "-o", "coverage-combined.xml"]
        subprocess.run(cmd, cwd=self.project_root)
        
        # Get coverage percentage
        cmd = ["python", "-m", "coverage", "report", "--format=total"]
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            coverage_percent = float(result.stdout.strip())
            print(f"📊 Overall test coverage: {coverage_percent:.1f}%")
            
            self.test_results['coverage'] = {
                'success': True,
                'percentage': coverage_percent
            }
            
            return coverage_percent >= 80.0  # Require 80% coverage
        else:
            print("❌ Failed to generate coverage report")
            self.test_results['coverage'] = {'success': False}
            return False
    
    def run_all_tests(self, 
                     include_performance: bool = False,
                     include_e2e: bool = False,
                     verbose: bool = False) -> bool:
        """Run all test suites."""
        print("🚀 Running comprehensive test suite...")
        start_time = time.time()
        
        results = []
        
        # Code quality checks first
        results.append(self.run_code_quality_checks())
        
        # Security tests
        results.append(self.run_security_tests())
        
        # Unit tests with coverage
        results.append(self.run_unit_tests(verbose=verbose, coverage=True))
        
        # Integration tests
        results.append(self.run_integration_tests(verbose=verbose))
        
        # End-to-end tests (optional)
        if include_e2e:
            results.append(self.run_end_to_end_tests(verbose=verbose))
        
        # Performance tests (optional)
        if include_performance:
            results.append(self.run_performance_tests(verbose=verbose))
        
        # Generate coverage report
        results.append(self.generate_coverage_report())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Summary
        passed_count = sum(1 for result in results if result)
        total_count = len(results)
        
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Tests passed: {passed_count}/{total_count}")
        
        if passed_count == total_count:
            print("🎉 All tests passed!")
            overall_success = True
        else:
            print("💥 Some tests failed!")
            overall_success = False
        
        # Save detailed results
        self.test_results['summary'] = {
            'overall_success': overall_success,
            'total_time': total_time,
            'passed_count': passed_count,
            'total_count': total_count,
            'timestamp': time.time()
        }
        
        self.save_test_results()
        
        return overall_success
    
    def save_test_results(self):
        """Save test results to JSON file."""
        results_file = self.project_root / "test-results-summary.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"📄 Detailed results saved to {results_file}")
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> bool:
        """Run a specific test file or directory."""
        print(f"🎯 Running specific test: {test_path}")
        
        cmd = ["python", "-m", "pytest", test_path]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print(f"✅ Test {test_path} passed")
        else:
            print(f"❌ Test {test_path} failed")
        
        return success


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="QME System Test Runner")
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "performance", "security", "quality", "all"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--include-performance",
        action="store_true",
        help="Include performance tests in 'all' run"
    )
    
    parser.add_argument(
        "--include-e2e",
        action="store_true",
        help="Include end-to-end tests in 'all' run"
    )
    
    parser.add_argument(
        "--test-path",
        help="Specific test file or directory to run"
    )
    
    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=80.0,
        help="Minimum coverage percentage required"
    )
    
    args = parser.parse_args()
    
    # Find project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # Change to project root
    os.chdir(project_root)
    
    # Create test runner
    runner = TestRunner(project_root)
    
    # Run tests based on arguments
    success = False
    
    if args.test_path:
        success = runner.run_specific_test(args.test_path, verbose=args.verbose)
    elif args.type == "unit":
        success = runner.run_unit_tests(verbose=args.verbose)
    elif args.type == "integration":
        success = runner.run_integration_tests(verbose=args.verbose)
    elif args.type == "e2e":
        success = runner.run_end_to_end_tests(verbose=args.verbose)
    elif args.type == "performance":
        success = runner.run_performance_tests(verbose=args.verbose)
    elif args.type == "security":
        success = runner.run_security_tests()
    elif args.type == "quality":
        success = runner.run_code_quality_checks()
    elif args.type == "all":
        success = runner.run_all_tests(
            include_performance=args.include_performance,
            include_e2e=args.include_e2e,
            verbose=args.verbose
        )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()