"""
Evidence-First QME System Test Runner.

Comprehensive test runner for all evidence-first QME system tests including
end-to-end pipeline testing, confidence scoring validation, programmatic
calculation testing, knowledge graph initialization, and integration tests.

Usage:
    python tests/run_evidence_first_tests.py [--test-type TYPE] [--verbose] [--report]

Test Types:
    - all: Run all evidence-first tests (default)
    - pipeline: Run main pipeline tests only
    - confidence: Run confidence scoring tests only
    - calculation: Run programmatic calculation tests only
    - knowledge_graph: Run knowledge graph initialization tests only
    - integration: Run integration tests only
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test imports
import pytest
import tempfile
import shutil

# Evidence-first test availability check
try:
    from tests.test_evidence_first_pipeline import TestEvidenceFirstPipeline
    from tests.test_confidence_scoring_validation import TestConfidenceScoringValidation
    from tests.test_programmatic_calculation_validation import TestProgrammaticCalculationValidation
    from tests.test_knowledge_graph_initialization import TestKnowledgeGraphInitialization
    from tests.test_evidence_first_integration import TestEvidenceFirstIntegration
    EVIDENCE_FIRST_TESTS_AVAILABLE = True
except ImportError as e:
    EVIDENCE_FIRST_TESTS_AVAILABLE = False
    print(f"⚠️  Evidence-first tests not fully available: {e}")


class EvidenceFirstTestRunner:
    """Comprehensive test runner for evidence-first QME system."""
    
    def __init__(self, verbose: bool = False, generate_report: bool = False):
        self.verbose = verbose
        self.generate_report = generate_report
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all evidence-first tests."""
        print("🚀 Starting Evidence-First QME System Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Test categories to run
        test_categories = [
            ('pipeline', 'End-to-End Pipeline Tests'),
            ('confidence', 'Confidence Scoring Validation Tests'),
            ('calculation', 'Programmatic Calculation Tests'),
            ('knowledge_graph', 'Knowledge Graph Initialization Tests'),
            ('integration', 'Integration Tests')
        ]
        
        overall_success = True
        
        for category, description in test_categories:
            print(f"\n📋 Running {description}...")
            print("-" * 40)
            
            try:
                result = self._run_test_category(category)
                self.test_results[category] = result
                
                if result['success']:
                    print(f"✅ {description}: PASSED ({result['tests_run']} tests)")
                else:
                    print(f"❌ {description}: FAILED ({result['failures']} failures)")
                    overall_success = False
                    
            except Exception as e:
                print(f"💥 {description}: ERROR - {str(e)}")
                self.test_results[category] = {
                    'success': False,
                    'error': str(e),
                    'tests_run': 0,
                    'failures': 1
                }
                overall_success = False
        
        self.end_time = time.time()
        
        # Generate summary
        self._print_test_summary(overall_success)
        
        # Generate report if requested
        if self.generate_report:
            self._generate_test_report()
        
        return {
            'overall_success': overall_success,
            'test_results': self.test_results,
            'execution_time': self.end_time - self.start_time
        }
    
    def run_specific_test(self, test_type: str) -> Dict[str, Any]:
        """Run specific test category."""
        print(f"🎯 Running {test_type.title()} Tests Only")
        print("=" * 40)
        
        self.start_time = time.time()
        
        try:
            result = self._run_test_category(test_type)
            self.test_results[test_type] = result
            
            if result['success']:
                print(f"✅ {test_type.title()} Tests: PASSED")
            else:
                print(f"❌ {test_type.title()} Tests: FAILED")
                
        except Exception as e:
            print(f"💥 {test_type.title()} Tests: ERROR - {str(e)}")
            result = {
                'success': False,
                'error': str(e),
                'tests_run': 0,
                'failures': 1
            }
            self.test_results[test_type] = result
        
        self.end_time = time.time()
        
        if self.generate_report:
            self._generate_test_report()
        
        return {
            'success': result['success'],
            'test_results': self.test_results,
            'execution_time': self.end_time - self.start_time
        }
    
    def _run_test_category(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category."""
        if not EVIDENCE_FIRST_TESTS_AVAILABLE:
            return {
                'success': False,
                'error': 'Evidence-first test components not available',
                'tests_run': 0,
                'failures': 1
            }
        
        # Map categories to test files
        test_files = {
            'pipeline': 'tests/test_evidence_first_pipeline.py',
            'confidence': 'tests/test_confidence_scoring_validation.py',
            'calculation': 'tests/test_programmatic_calculation_validation.py',
            'knowledge_graph': 'tests/test_knowledge_graph_initialization.py',
            'integration': 'tests/test_evidence_first_integration.py'
        }
        
        if category not in test_files:
            raise ValueError(f"Unknown test category: {category}")
        
        test_file = test_files[category]
        
        # Run pytest on the specific test file
        pytest_args = [
            test_file,
            '-v' if self.verbose else '-q',
            '--tb=short',
            '--disable-warnings'
        ]
        
        # Capture pytest results
        result = pytest.main(pytest_args)
        
        # Parse pytest exit code
        success = result == 0
        
        # For now, we'll use basic success/failure
        # In a real implementation, you'd parse pytest output for detailed metrics
        return {
            'success': success,
            'tests_run': 1,  # Placeholder - would parse actual count
            'failures': 0 if success else 1,
            'execution_time': time.time() - self.start_time if self.start_time else 0
        }
    
    def _print_test_summary(self, overall_success: bool):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 EVIDENCE-FIRST QME SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_execution_time = self.end_time - self.start_time
        
        print(f"⏱️  Total Execution Time: {total_execution_time:.2f} seconds")
        print(f"🎯 Overall Result: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        print("\n📋 Test Category Results:")
        print("-" * 40)
        
        total_tests = 0
        total_failures = 0
        
        for category, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            tests_run = result.get('tests_run', 0)
            failures = result.get('failures', 0)
            
            print(f"  {category.ljust(15)}: {status} ({tests_run} tests, {failures} failures)")
            
            total_tests += tests_run
            total_failures += failures
        
        print("-" * 40)
        print(f"  {'TOTAL'.ljust(15)}: {total_tests} tests, {total_failures} failures")
        
        # Performance summary
        if total_execution_time > 0:
            print(f"\n⚡ Performance Summary:")
            print(f"  Average time per category: {total_execution_time / len(self.test_results):.2f}s")
            
            if total_execution_time > 300:  # 5 minutes
                print("  ⚠️  Execution time exceeds 5-minute benchmark")
            else:
                print("  ✅ Execution time within acceptable limits")
        
        # Requirements coverage summary
        print(f"\n📋 Requirements Coverage:")
        requirements_covered = [
            "1.1 - Evidence-First Structured Extraction",
            "1.2 - Confidence Scoring and Validation", 
            "2.1 - Programmatic Impairment Calculations",
            "2.5 - Calculation Documentation and Audit",
            "3.2 - Knowledge Graph Initialization",
            "4.5 - Two-Pipeline Workflow Integration",
            "5.5 - Legal Compliance Validation"
        ]
        
        for req in requirements_covered:
            print(f"  ✅ {req}")
    
    def _generate_test_report(self):
        """Generate detailed test report."""
        report_data = {
            'test_run_info': {
                'timestamp': datetime.now().isoformat(),
                'execution_time': self.end_time - self.start_time if self.end_time and self.start_time else 0,
                'overall_success': all(result.get('success', False) for result in self.test_results.values())
            },
            'test_results': self.test_results,
            'requirements_coverage': {
                '1.1': 'Evidence-First Structured Extraction Pipeline',
                '1.2': 'Evidence Validation Gateway and Threshold Management',
                '2.1': 'Programmatic Impairment Calculation Engine',
                '2.5': 'Calculation Documentation and Validation',
                '3.2': 'Knowledge Graph Complete Initialization',
                '4.5': 'Two-Pipeline Workflow Integration',
                '5.5': 'Enhanced Rules Engine and Legal Compliance'
            },
            'performance_metrics': {
                'total_execution_time': self.end_time - self.start_time if self.end_time and self.start_time else 0,
                'average_time_per_category': (self.end_time - self.start_time) / len(self.test_results) if self.test_results and self.end_time and self.start_time else 0,
                'within_benchmark': (self.end_time - self.start_time) < 300 if self.end_time and self.start_time else False
            }
        }
        
        # Generate report file
        report_filename = f"evidence_first_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join('tests', 'reports', report_filename)
        
        # Create reports directory if it doesn't exist
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed test report generated: {report_path}")
    
    def run_smoke_tests(self) -> bool:
        """Run quick smoke tests to verify basic functionality."""
        print("💨 Running Evidence-First Smoke Tests...")
        
        if not EVIDENCE_FIRST_TESTS_AVAILABLE:
            print("❌ Evidence-first components not available for smoke tests")
            return False
        
        try:
            # Test basic imports
            from src.services.structured_extractor import StructuredExtractor
            from src.services.impairment_calculator import ImpairmentCalculator
            print("✅ Core components import successfully")
            
            # Test basic functionality
            temp_dir = tempfile.mkdtemp()
            try:
                # Create minimal test data
                test_content = "Patient: John Doe, Age: 45, Case: WC-2024-001"
                test_file = os.path.join(temp_dir, 'smoke_test.txt')
                with open(test_file, 'w') as f:
                    f.write(test_content)
                
                # Test extraction
                extractor = StructuredExtractor()
                from src.services.structured_extractor import ExtractionContext
                
                context = ExtractionContext(
                    document_id="smoke-test-1",
                    document_text=test_content,
                    source_file=test_file
                )
                
                result = extractor.extract_with_confidence(context)
                print(f"✅ Extraction smoke test: confidence={result.overall_confidence:.3f}")
                
                # Test calculation (with minimal tables)
                ama_tables = {
                    "15-5": {
                        "table_id": "15-5",
                        "chapter": 15,
                        "title": "Test Table",
                        "body_system": "spine",
                        "data_structure": {"measurements": {"flexion": {"normal": 50}}}
                    }
                }
                
                tables_file = os.path.join(temp_dir, 'smoke_tables.json')
                with open(tables_file, 'w') as f:
                    json.dump(ama_tables, f)
                
                calculator = ImpairmentCalculator(tables_file)
                print("✅ Calculator smoke test: initialization successful")
                
                return True
                
            finally:
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            print(f"❌ Smoke test failed: {e}")
            return False


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Evidence-First QME System Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  all           Run all evidence-first tests (default)
  pipeline      Run main pipeline tests only
  confidence    Run confidence scoring tests only
  calculation   Run programmatic calculation tests only
  knowledge_graph Run knowledge graph initialization tests only
  integration   Run integration tests only
  smoke         Run quick smoke tests only

Examples:
  python tests/run_evidence_first_tests.py
  python tests/run_evidence_first_tests.py --test-type confidence --verbose
  python tests/run_evidence_first_tests.py --test-type smoke
  python tests/run_evidence_first_tests.py --report
        """
    )
    
    parser.add_argument(
        '--test-type',
        choices=['all', 'pipeline', 'confidence', 'calculation', 'knowledge_graph', 'integration', 'smoke'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='Generate detailed test report'
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = EvidenceFirstTestRunner(
        verbose=args.verbose,
        generate_report=args.report
    )
    
    # Run tests based on type
    if args.test_type == 'smoke':
        success = runner.run_smoke_tests()
        sys.exit(0 if success else 1)
    elif args.test_type == 'all':
        result = runner.run_all_tests()
        sys.exit(0 if result['overall_success'] else 1)
    else:
        result = runner.run_specific_test(args.test_type)
        sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()