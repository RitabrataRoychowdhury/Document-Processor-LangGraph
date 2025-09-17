#!/usr/bin/env python3
"""
Validation Script for Refactored QME System

This script validates the refactored QME system against real documents
and provides comprehensive quality metrics and performance assessments.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.services.quality_validation_service import QualityValidationService
from src.services.performance_monitoring_service import PerformanceMonitoringService, PerformanceMonitor
from tests.test_end_to_end_quality_validation import EndToEndQualityTestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main validation function"""
    print("="*80)
    print("QME REFACTORED SYSTEM VALIDATION")
    print("="*80)
    
    try:
        # Initialize services
        print("Initializing validation services...")
        quality_validator = QualityValidationService()
        performance_monitor = PerformanceMonitoringService()
        
        # Run comprehensive quality tests
        print("\nRunning comprehensive quality validation tests...")
        test_suite = EndToEndQualityTestSuite()
        
        with PerformanceMonitor(performance_monitor, 'validation_system', 'comprehensive_tests'):
            results = test_suite.run_comprehensive_quality_tests()
        
        # Display results
        print("\n" + "="*80)
        print("VALIDATION RESULTS")
        print("="*80)
        
        summary = results['test_summary']
        print(f"Total Tests Run: {summary['total_tests_run']}")
        print(f"Successful Tests: {summary['successful_tests']}")
        print(f"Failed Tests: {summary['failed_tests']}")
        print(f"Overall Quality Improvement: {summary['overall_quality_improvement']}")
        
        # Template comparison results
        template_results = results.get('template_comparison_results', {})
        if template_results:
            print(f"\nTemplate Comparison:")
            print(f"  Templates Tested: {template_results.get('total_templates_tested', 0)}")
            print(f"  Successful Comparisons: {template_results.get('successful_comparisons', 0)}")
            print(f"  Quality Improvements: {len(template_results.get('quality_improvements', []))}")
            print(f"  Quality Regressions: {len(template_results.get('quality_regressions', []))}")
        
        # Real document validation results
        validation_results = results.get('real_document_validation_results', {})
        if validation_results:
            print(f"\nReal Document Validation:")
            print(f"  Documents Tested: {validation_results.get('total_documents_tested', 0)}")
            print(f"  Successful Validations: {validation_results.get('successful_validations', 0)}")
            
            # Show quality assessments
            assessments = validation_results.get('quality_assessments', [])
            if assessments:
                print(f"  Quality Scores:")
                for assessment_data in assessments:
                    doc_name = Path(assessment_data['document']).stem
                    assessment = assessment_data['assessment']
                    print(f"    {doc_name}: {assessment.metrics.overall_score:.3f}")
        
        # Performance metrics
        performance_results = results.get('performance_metrics', {})
        if performance_results:
            print(f"\nPerformance Metrics:")
            validation_perf = performance_results.get('validation_performance', {})
            if validation_perf:
                print(f"  Validation Time: {validation_perf.get('validation_time_seconds', 0):.2f}s")
                print(f"  Issues Detected: {validation_perf.get('issues_detected', 0)}")
                print(f"  Quality Score: {validation_perf.get('overall_quality_score', 0):.3f}")
            
            scalability = performance_results.get('scalability_metrics', {})
            if scalability:
                print(f"  Scalability (10 docs): {scalability.get('time_for_10_documents', 0):.2f}s")
                print(f"  Avg Time per Doc: {scalability.get('average_time_per_document', 0):.2f}s")
        
        # System health report
        print(f"\nGenerating system health report...")
        health_report = performance_monitor.generate_health_report()
        print(f"Overall System Health: {health_report.overall_health_score:.3f}")
        
        if health_report.component_health:
            print("Component Health:")
            for component, health in health_report.component_health.items():
                print(f"  {component}: {health:.3f}")
        
        if health_report.active_alerts:
            print(f"\nActive Alerts: {len(health_report.active_alerts)}")
            for alert in health_report.active_alerts[:5]:  # Show first 5 alerts
                print(f"  {alert.level.value.upper()}: {alert.message}")
        
        # Recommendations
        print(f"\nRecommendations:")
        for i, rec in enumerate(results.get('recommendations', []), 1):
            print(f"  {i}. {rec}")
        
        # Overall assessment
        print(f"\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)
        
        if summary['failed_tests'] == 0:
            print("✅ All tests passed successfully")
        else:
            print(f"⚠️  {summary['failed_tests']} tests failed")
        
        if summary.get('overall_quality_improvement', False):
            print("✅ Quality improvement detected")
        else:
            print("ℹ️  No significant quality improvement detected")
        
        if health_report.overall_health_score >= 0.8:
            print("✅ System health is good")
        elif health_report.overall_health_score >= 0.6:
            print("⚠️  System health needs attention")
        else:
            print("❌ System health is poor")
        
        # Save detailed results
        results_file = Path("results/validation_reports") / f"system_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': results,
            'health_report': {
                'overall_health_score': health_report.overall_health_score,
                'component_health': health_report.component_health,
                'active_alerts_count': len(health_report.active_alerts),
                'recommendations': health_report.recommendations
            },
            'validation_summary': {
                'all_tests_passed': summary['failed_tests'] == 0,
                'quality_improvement': summary.get('overall_quality_improvement', False),
                'system_health_good': health_report.overall_health_score >= 0.8,
                'validation_successful': (
                    summary['failed_tests'] == 0 and 
                    health_report.overall_health_score >= 0.6
                )
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)
        
        print(f"\nDetailed validation report saved to: {results_file}")
        
        # Final status
        if validation_report['validation_summary']['validation_successful']:
            print("\n🎉 VALIDATION SUCCESSFUL - Refactored system is ready for use!")
            return 0
        else:
            print("\n⚠️  VALIDATION ISSUES DETECTED - Review recommendations before use")
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1
    
    finally:
        # Stop performance monitoring
        try:
            performance_monitor.stop_monitoring()
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())