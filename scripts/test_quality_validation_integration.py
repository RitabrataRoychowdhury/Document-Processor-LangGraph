#!/usr/bin/env python3
"""
Test Quality Validation Integration
Tests the quality validation system with mock data to verify implementation
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.comprehensive_quality_validation_service import (
    ComprehensiveQualityValidationService, 
    QualityValidationResult
)
from src.models.extraction_models import (
    ExtractionResult, 
    ExtractedField, 
    QualityAssessment, 
    ProcessingMetadata
)


def create_mock_extraction_result() -> ExtractionResult:
    """Create a mock extraction result for testing"""
    extracted_fields = {
        "patient_name": ExtractedField(
            name="patient_name",
            value="John Doe",
            confidence=0.95,
            source_location="page 1, line 5"
        ),
        "date_of_birth": ExtractedField(
            name="date_of_birth",
            value="01/15/1980",
            confidence=0.90,
            source_location="page 1, line 7"
        ),
        "date_of_injury": ExtractedField(
            name="date_of_injury",
            value="06/20/2023",
            confidence=0.88,
            source_location="page 1, line 10"
        ),
        "medical_history": ExtractedField(
            name="medical_history",
            value="Patient reports chronic lower back pain following workplace injury. History of previous back strain in 2020.",
            confidence=0.85,
            source_location="page 2, paragraph 1"
        ),
        "examination_findings": ExtractedField(
            name="examination_findings",
            value="Physical examination reveals limited range of motion in lumbar spine. Tenderness noted over L4-L5 region. Positive straight leg raise test on right side.",
            confidence=0.82,
            source_location="page 3, paragraph 2"
        ),
        "diagnosis": ExtractedField(
            name="diagnosis",
            value="Lumbar disc herniation with radiculopathy, L4-L5 level",
            confidence=0.90,
            source_location="page 4, line 15"
        ),
        "impairment_rating": ExtractedField(
            name="impairment_rating",
            value="12% whole person impairment based on AMA Guides 5th Edition, Table 15-3",
            confidence=0.87,
            source_location="page 5, paragraph 1"
        ),
        "work_restrictions": ExtractedField(
            name="work_restrictions",
            value="No lifting over 25 pounds, avoid prolonged sitting or standing, frequent position changes recommended",
            confidence=0.83,
            source_location="page 5, paragraph 3"
        )
    }
    
    # Create quality assessment
    quality_assessment = QualityAssessment(
        overall_score=0.85,
        completeness_score=0.90,
        accuracy_score=0.87,
        consistency_score=0.82,
        compliance_score=0.88
    )
    
    # Create processing metadata
    processing_metadata = ProcessingMetadata(
        extraction_method="mock_extraction",
        processing_time=2.5,
        model_used="mock_model",
        prompt_template="mock_template",
        api_version="mock_v1"
    )
    
    return ExtractionResult(
        document_id="test_document_001",
        extraction_method="mock_extraction",
        confidence_score=0.87,
        extracted_fields=extracted_fields,
        quality_assessment=quality_assessment,
        processing_metadata=processing_metadata
    )


def test_quality_validation_integration():
    """Test the comprehensive quality validation integration"""
    print("="*80)
    print("QUALITY VALIDATION INTEGRATION TEST")
    print("="*80)
    
    # Initialize quality validation service
    print("1. Initializing Quality Validation Service...")
    try:
        validator = ComprehensiveQualityValidationService()
        print("   ✅ Quality validation service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize quality validation service: {e}")
        return False
    
    # Create mock extraction result
    print("\n2. Creating Mock Extraction Result...")
    try:
        extraction_result = create_mock_extraction_result()
        print(f"   ✅ Mock extraction result created with {len(extraction_result.extracted_fields)} fields")
        print(f"   📊 Overall confidence: {extraction_result.confidence_score:.3f}")
    except Exception as e:
        print(f"   ❌ Failed to create mock extraction result: {e}")
        return False
    
    # Run quality validation
    print("\n3. Running Quality Validation...")
    try:
        validation_result = validator.validate_extraction_quality(extraction_result)
        print(f"   ✅ Quality validation completed successfully")
        print(f"   📈 Overall Score: {validation_result.overall_score:.3f}")
        print(f"   ⚖️  Weighted Score: {validation_result.weighted_score:.3f}")
        print(f"   ⏱️  Processing Time: {validation_result.processing_time:.3f}s")
    except Exception as e:
        print(f"   ❌ Quality validation failed: {e}")
        return False
    
    # Display detailed metrics
    print("\n4. Quality Metrics Analysis:")
    for metric in validation_result.metrics:
        status_emoji = "✅" if metric.score >= 0.75 else "⚠️" if metric.score >= 0.5 else "❌"
        print(f"   {status_emoji} {metric.name.title()}: {metric.score:.3f} (weight: {metric.weight:.2f})")
        if metric.issues:
            for issue in metric.issues[:2]:  # Show first 2 issues
                print(f"      - Issue: {issue}")
        if metric.suggestions:
            for suggestion in metric.suggestions[:1]:  # Show first suggestion
                print(f"      💡 Suggestion: {suggestion}")
    
    # Display compliance checks
    print("\n5. Compliance Analysis:")
    for check in validation_result.compliance_checks:
        status_emoji = "✅" if check.passed else "❌"
        severity_emoji = "🔴" if check.severity == "critical" else "🟡"
        print(f"   {status_emoji} {severity_emoji} {check.rule_name}: {check.message}")
        if check.reference:
            print(f"      📚 Reference: {check.reference}")
    
    # Display recommendations
    print("\n6. System Recommendations:")
    if validation_result.recommendations:
        for i, recommendation in enumerate(validation_result.recommendations, 1):
            print(f"   {i}. {recommendation}")
    else:
        print("   ✅ No recommendations - system performing well")
    
    # Save validation report
    print("\n7. Saving Validation Report...")
    try:
        report_path = validator.save_validation_report(validation_result)
        print(f"   ✅ Validation report saved to: {report_path}")
    except Exception as e:
        print(f"   ⚠️  Failed to save validation report: {e}")
    
    # Determine test success
    success_criteria = {
        "overall_score": validation_result.overall_score >= 0.7,
        "weighted_score": validation_result.weighted_score >= 0.75,
        "critical_compliance": all(check.passed for check in validation_result.compliance_checks 
                                 if check.severity == "critical"),
        "processing_time": validation_result.processing_time < 5.0
    }
    
    print("\n8. Success Criteria Assessment:")
    all_passed = True
    for criterion, passed in success_criteria.items():
        status_emoji = "✅" if passed else "❌"
        print(f"   {status_emoji} {criterion.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 QUALITY VALIDATION INTEGRATION TEST PASSED")
        print("✅ System is ready for quality validation operations")
    else:
        print("⚠️  QUALITY VALIDATION INTEGRATION TEST PARTIALLY PASSED")
        print("🔧 Some criteria need attention but core functionality works")
    print("="*80)
    
    return all_passed


def test_system_performance_validation():
    """Test system performance validation with multiple documents"""
    print("\n" + "="*80)
    print("SYSTEM PERFORMANCE VALIDATION TEST")
    print("="*80)
    
    validator = ComprehensiveQualityValidationService()
    test_results = []
    
    # Generate multiple test results
    print("1. Generating Multiple Test Results...")
    for i in range(5):
        extraction_result = create_mock_extraction_result()
        extraction_result.document_id = f"test_document_{i+1:03d}"
        
        # Vary the quality slightly for realistic testing
        extraction_result.confidence_score = 0.85 + (i * 0.02)
        
        validation_result = validator.validate_extraction_quality(extraction_result)
        test_results.append(validation_result)
        print(f"   ✅ Document {i+1}: Score {validation_result.weighted_score:.3f}")
    
    # Validate system performance
    print("\n2. Analyzing System Performance...")
    performance_assessment = validator.validate_system_performance(test_results)
    
    print(f"   📊 Total Documents: {performance_assessment['total_documents']}")
    print(f"   📈 Average Overall Score: {performance_assessment['average_overall_score']:.3f}")
    print(f"   ⚖️  Average Weighted Score: {performance_assessment['average_weighted_score']:.3f}")
    print(f"   ⏱️  Average Processing Time: {performance_assessment['average_processing_time']:.3f}s")
    print(f"   ✅ Documents Above Threshold: {performance_assessment['documents_above_threshold']}")
    print(f"   ⚠️  Documents Needing Review: {performance_assessment['documents_needing_review']}")
    print(f"   🔴 Critical Compliance Failures: {performance_assessment['critical_compliance_failures']}")
    
    # Performance criteria
    performance_success = (
        performance_assessment['average_weighted_score'] >= 0.75 and
        performance_assessment['average_processing_time'] < 3.0 and
        performance_assessment['critical_compliance_failures'] == 0
    )
    
    print("\n3. Performance Assessment:")
    if performance_success:
        print("   🎉 System performance meets all criteria")
    else:
        print("   ⚠️  System performance needs optimization")
    
    return performance_success


def main():
    """Main test execution"""
    logging.basicConfig(level=logging.INFO)
    
    print("Starting Quality Validation Integration Tests...")
    
    # Test 1: Basic quality validation integration
    test1_passed = test_quality_validation_integration()
    
    # Test 2: System performance validation
    test2_passed = test_system_performance_validation()
    
    # Overall assessment
    print("\n" + "="*80)
    print("OVERALL TEST RESULTS")
    print("="*80)
    
    tests_passed = sum([test1_passed, test2_passed])
    total_tests = 2
    
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - Quality validation system is fully functional")
        return 0
    elif tests_passed > 0:
        print("⚠️  PARTIAL SUCCESS - Core functionality works, some optimizations needed")
        return 1
    else:
        print("❌ TESTS FAILED - Quality validation system needs attention")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)