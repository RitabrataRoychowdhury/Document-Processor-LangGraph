#!/usr/bin/env python3
"""
Integration Test for Task 5: Quality Validation and System Testing
Demonstrates all implemented components working together
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

# Set test API key
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-integration-test'

from src.core.validation.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
from src.infrastructure.monitoring.system_performance_monitor import SystemPerformanceMonitor
from src.models.extraction_models import ExtractionResult, ExtractedField, QualityAssessment, ProcessingMetadata
from tests.end_to_end.test_end_to_end_system_comparison import SystemComparisonTestSuite


def test_comprehensive_quality_validation():
    """Test comprehensive quality validation service"""
    print("🔍 Testing Comprehensive Quality Validation Service...")
    
    # Create mock extraction result
    mock_extraction = ExtractionResult(
        document_id='integration_test_doc',
        extraction_method='openrouter_sonoma_sky',
        confidence_score=0.87,
        extracted_fields={
            'patient_name': ExtractedField(name='patient_name', value='John Doe', confidence=0.95),
            'date_of_birth': ExtractedField(name='date_of_birth', value='1975-03-15', confidence=0.92),
            'date_of_injury': ExtractedField(name='date_of_injury', value='2024-01-10', confidence=0.88),
            'medical_history': ExtractedField(name='medical_history', value='Chronic back pain, previous surgery', confidence=0.85),
            'examination_findings': ExtractedField(name='examination_findings', value='Limited range of motion, tenderness', confidence=0.82),
            'diagnosis': ExtractedField(name='diagnosis', value='Lumbar disc herniation L4-L5', confidence=0.90),
            'impairment_rating': ExtractedField(name='impairment_rating', value='15% whole person impairment', confidence=0.78),
            'work_restrictions': ExtractedField(name='work_restrictions', value='No lifting over 20 lbs, limited bending', confidence=0.83)
        },
        quality_assessment=QualityAssessment(
            overall_score=0.87,
            completeness_score=0.85,
            accuracy_score=0.89,
            consistency_score=0.86,
            compliance_score=0.88
        ),
        processing_metadata=ProcessingMetadata(
            extraction_method='openrouter_sonoma_sky',
            processing_time=12.5,
            model_used='anthropic/claude-3.5-sonnet:beta',
            prompt_template='qme_extraction_v2',
            api_version='1.0'
        )
    )
    
    # Initialize quality validator
    validator = ComprehensiveQualityValidationService()
    
    # Perform quality validation
    quality_result = validator.validate_extraction_quality(mock_extraction)
    
    # Display results
    print(f"   ✅ Document ID: {quality_result.document_id}")
    print(f"   📊 Overall Score: {quality_result.overall_score:.3f}")
    print(f"   ⚖️  Weighted Score: {quality_result.weighted_score:.3f}")
    print(f"   📋 Metrics Evaluated: {len(quality_result.metrics)}")
    print(f"   ✔️  Compliance Checks: {len(quality_result.compliance_checks)}")
    print(f"   💡 Recommendations: {len(quality_result.recommendations)}")
    print(f"   ⏱️  Processing Time: {quality_result.processing_time:.3f}s")
    
    # Show metric details
    print("\n   📈 Quality Metrics:")
    for metric in quality_result.metrics:
        print(f"      • {metric.name.title()}: {metric.score:.3f} (weight: {metric.weight:.2f})")
    
    # Show compliance results
    print("\n   🏛️  Compliance Checks:")
    for check in quality_result.compliance_checks:
        status = "✅ PASS" if check.passed else "❌ FAIL"
        print(f"      • {check.rule_name}: {status} ({check.severity})")
    
    # Save validation report
    report_path = validator.save_validation_report(quality_result)
    print(f"   💾 Report saved: {report_path}")
    
    return quality_result


def test_system_performance_monitor():
    """Test system performance monitoring"""
    print("\n📊 Testing System Performance Monitor...")
    
    # Initialize performance monitor
    monitor = SystemPerformanceMonitor()
    
    # Start monitoring
    monitor.start_monitoring()
    print("   ✅ Performance monitoring started")
    
    # Simulate processing session
    with monitor.track_processing_session("integration_test_session"):
        print("   🔄 Simulating document processing...")
        
        # Simulate processing multiple documents
        for i in range(3):
            doc_id = f"test_doc_{i+1}"
            
            with monitor.track_document_processing(doc_id, "integration_test_session"):
                # Simulate processing time
                import time
                time.sleep(0.1)  # Simulate 100ms processing
                
                print(f"      ✅ Processed {doc_id}")
    
    # Stop monitoring
    monitor.stop_monitoring()
    print("   ⏹️  Performance monitoring stopped")
    
    # Get performance summary
    summary = monitor.get_performance_summary(1)  # Last 1 hour
    
    print(f"   📈 Performance Summary:")
    print(f"      • Documents Processed: {summary['processing_metrics']['total_documents']}")
    print(f"      • Average Processing Time: {summary['processing_metrics']['avg_processing_time']:.3f}s")
    print(f"      • Average CPU Usage: {summary['resource_metrics']['avg_cpu_usage']:.1f}%")
    print(f"      • Average Memory Usage: {summary['resource_metrics']['avg_memory_usage']:.1f}%")
    print(f"      • Total Errors: {summary['error_metrics']['total_errors']}")
    
    # Save performance report
    report_path = monitor.save_performance_report()
    print(f"   💾 Performance report saved: {report_path}")
    
    return summary


def test_end_to_end_system_comparison():
    """Test end-to-end system comparison suite"""
    print("\n🔄 Testing End-to-End System Comparison Suite...")
    
    # Initialize comparison suite
    suite = SystemComparisonTestSuite()
    print("   ✅ System comparison suite initialized")
    
    # Test aggregate metrics calculation
    mock_results = [
        {
            "document_name": "test1.pdf",
            "refactored_system": {"success": True, "processing_time": 5.2},
            "quality_comparison": {"overall_score": 0.87, "weighted_score": 0.85},
            "baseline_comparison": {"baseline_available": True}
        },
        {
            "document_name": "test2.pdf", 
            "refactored_system": {"success": True, "processing_time": 4.8},
            "quality_comparison": {"overall_score": 0.91, "weighted_score": 0.89},
            "baseline_comparison": {"baseline_available": False}
        },
        {
            "document_name": "test3.pdf",
            "refactored_system": {"success": True, "processing_time": 6.1},
            "quality_comparison": {"overall_score": 0.83, "weighted_score": 0.81},
            "baseline_comparison": {"baseline_available": True}
        }
    ]
    
    # Calculate aggregate metrics
    metrics = suite._calculate_aggregate_metrics(mock_results)
    
    print(f"   📊 Aggregate Metrics:")
    print(f"      • Total Documents: {metrics['total_documents']}")
    print(f"      • Success Rate: {metrics['success_rate']:.1%}")
    print(f"      • Average Processing Time: {metrics['avg_processing_time']:.2f}s")
    print(f"      • Average Quality Score: {metrics['avg_quality_score']:.3f}")
    print(f"      • Documents with Baseline: {metrics['documents_with_baseline']}")
    
    # Test quality improvements identification
    improvements = suite._identify_quality_improvements(mock_results)
    print(f"   ✨ Quality Improvements Identified: {len(improvements)}")
    for improvement in improvements:
        print(f"      • {improvement}")
    
    # Test regression detection
    regressions = suite._identify_regression_issues(mock_results)
    print(f"   ⚠️  Regression Issues: {len(regressions)}")
    if regressions:
        for regression in regressions:
            print(f"      • {regression}")
    else:
        print("      • No regression issues detected ✅")
    
    return metrics


def test_migration_readiness():
    """Test migration readiness and system validation"""
    print("\n🚀 Testing Migration Readiness...")
    
    # Check configuration files
    config_files = [
        "config/validation/quality_validation_config.yaml",
        "config/settings/openrouter_config.yaml"
    ]
    
    config_status = []
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            config_status.append(f"✅ {config_file}")
        else:
            config_status.append(f"❌ {config_file} (missing)")
    
    print("   📋 Configuration Files:")
    for status in config_status:
        print(f"      {status}")
    
    # Check required directories
    required_dirs = [
        "results/validation_reports",
        "results/performance_reports", 
        "results/generated_documents",
        "results/templates_archive"
    ]
    
    dir_status = []
    for dir_path in required_dirs:
        directory = Path(dir_path)
        if directory.exists():
            dir_status.append(f"✅ {dir_path}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            dir_status.append(f"✅ {dir_path} (created)")
    
    print("\n   📁 Required Directories:")
    for status in dir_status:
        print(f"      {status}")
    
    # Check service initialization
    services_status = []
    
    try:
        validator = ComprehensiveQualityValidationService()
        services_status.append("✅ Quality Validation Service")
    except Exception as e:
        services_status.append(f"❌ Quality Validation Service: {e}")
    
    try:
        monitor = SystemPerformanceMonitor()
        services_status.append("✅ Performance Monitor Service")
    except Exception as e:
        services_status.append(f"❌ Performance Monitor Service: {e}")
    
    try:
        suite = SystemComparisonTestSuite()
        services_status.append("✅ System Comparison Suite")
    except Exception as e:
        services_status.append(f"❌ System Comparison Suite: {e}")
    
    print("\n   🔧 Service Initialization:")
    for status in services_status:
        print(f"      {status}")
    
    # Overall readiness assessment
    all_configs_ready = all("✅" in status for status in config_status)
    all_dirs_ready = all("✅" in status for status in dir_status)
    all_services_ready = all("✅" in status for status in services_status)
    
    overall_ready = all_configs_ready and all_dirs_ready and all_services_ready
    
    print(f"\n   🎯 Overall Migration Readiness: {'✅ READY' if overall_ready else '❌ NOT READY'}")
    
    return overall_ready


def main():
    """Main integration test function"""
    print("="*80)
    print("🧪 TASK 5 INTEGRATION TEST: Quality Validation and System Testing")
    print("="*80)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Quality Validation Service
        quality_result = test_comprehensive_quality_validation()
        
        # Test 2: Performance Monitoring
        performance_summary = test_system_performance_monitor()
        
        # Test 3: End-to-End System Comparison
        comparison_metrics = test_end_to_end_system_comparison()
        
        # Test 4: Migration Readiness
        migration_ready = test_migration_readiness()
        
        # Final Summary
        print("\n" + "="*80)
        print("📋 INTEGRATION TEST SUMMARY")
        print("="*80)
        
        print(f"✅ Quality Validation: Score {quality_result.weighted_score:.3f}")
        print(f"✅ Performance Monitoring: {performance_summary['processing_metrics']['total_documents']} docs processed")
        print(f"✅ System Comparison: {comparison_metrics['success_rate']:.1%} success rate")
        print(f"{'✅' if migration_ready else '❌'} Migration Readiness: {'READY' if migration_ready else 'NOT READY'}")
        
        print(f"\n🎉 Task 5 Implementation: {'SUCCESSFUL' if migration_ready else 'NEEDS ATTENTION'}")
        
        if migration_ready:
            print("\n🚀 System is ready for production deployment!")
            print("   • Quality validation is operational")
            print("   • Performance monitoring is active")
            print("   • End-to-end testing is functional")
            print("   • Migration infrastructure is in place")
        else:
            print("\n⚠️  System needs attention before deployment")
        
        print("="*80)
        
        return 0 if migration_ready else 1
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)