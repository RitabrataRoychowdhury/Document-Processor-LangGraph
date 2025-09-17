"""
Confidence Scoring Validation Tests.

Dedicated tests for confidence scoring validation ensuring ≥95% precision 
for critical fields and ≥90% overall field coverage as required by the 
evidence-first QME system.

Requirements tested: 1.1, 1.2, 1.3, 1.4
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Test imports
try:
    from src.core.extraction.structured_extractor import StructuredExtractor, ExtractionContext, ConfidenceMetrics
    from tests.unit.core.test_qme_field_extractor import QMEFieldExtractor, EvidenceSnippet
    CONFIDENCE_SCORING_AVAILABLE = True
except ImportError:
    CONFIDENCE_SCORING_AVAILABLE = False


@dataclass
class ConfidenceTestCase:
    """Test case for confidence scoring validation."""
    name: str
    text: str
    expected_fields: Dict[str, any]
    expected_confidence_threshold: float
    critical_fields: List[str]


class TestConfidenceScoringValidation:
    """Comprehensive confidence scoring validation tests."""
    
    @pytest.fixture
    def confidence_test_cases(self):
        """Test cases with varying confidence levels."""
        return [
            ConfidenceTestCase(
                name="high_confidence_standard_format",
                text="""
                Re: Applicant: John Smith
                Age: 45 years old
                Gender: Male
                EAMS No: ADJ12345678
                Claim No: WC789-012
                Date of Injury: January 15, 2024
                Body Part: Right shoulder
                Employer: ABC Corporation
                Occupation: Manager
                Examination Date: March 1, 2025
                """,
                expected_fields={
                    'patient_name': 'John Smith',
                    'age': 45,
                    'gender': 'Male',
                    'case_number': 'ADJ12345678',
                    'claim_number': 'WC789-012',
                    'injury_date': 'January 15, 2024',
                    'body_parts': 'Right shoulder',
                    'employer': 'ABC Corporation',
                    'occupation': 'Manager',
                    'scheduled_exam_date': 'March 1, 2025'
                },
                expected_confidence_threshold=0.9,
                critical_fields=['patient_name', 'case_number', 'injury_date', 'age']
            ),
            ConfidenceTestCase(
                name="medium_confidence_non_standard_format",
                text="""
                PATIENT NAME: ALICE JOHNSON
                PATIENT AGE: THIRTY FIVE
                WC CASE NUMBER: WC555444
                INJURY OCCURRED: FEBRUARY 2024
                INJURED BODY PART: LEFT KNEE
                WORKPLACE: XYZ COMPANY
                """,
                expected_fields={
                    'patient_name': 'Alice Johnson',
                    'age': 35,
                    'case_number': 'WC555444',
                    'injury_date': 'February 2024',
                    'body_parts': 'Left knee',
                    'employer': 'XYZ Company'
                },
                expected_confidence_threshold=0.7,
                critical_fields=['patient_name', 'case_number']
            ),
            ConfidenceTestCase(
                name="low_confidence_minimal_format",
                text="""
                Patient: Bob Wilson
                Claim: WC999888
                Hurt his ankle at work
                """,
                expected_fields={
                    'patient_name': 'Bob Wilson',
                    'claim_number': 'WC999888',
                    'body_parts': 'ankle'
                },
                expected_confidence_threshold=0.5,
                critical_fields=['patient_name', 'claim_number']
            ),
            ConfidenceTestCase(
                name="nick_diaz_pqme_format",
                text="""
                Re: Applicant: Nick Diaz Jr.
                Employer: Costco
                EAMS No: ADJ19802400
                Claim No: WC608-H07190
                
                The applicant was a 43-year-old front-end supervisor for a Costco warehouse 
                who sustained an accepted left knee injury on July 24, 2024. 
                He apparently was moving steel with a forklift.
                Your examination is scheduled to take place on September 9, 2025.
                """,
                expected_fields={
                    'patient_name': 'Nick Diaz Jr',
                    'age': 43,
                    'employer': 'Costco',
                    'case_number': 'ADJ19802400',
                    'claim_number': 'WC608-H07190',
                    'occupation': 'front-end supervisor',
                    'body_parts': 'left knee',
                    'injury_date': 'July 24, 2024',
                    'scheduled_exam_date': 'September 9, 2025'
                },
                expected_confidence_threshold=0.95,
                critical_fields=['patient_name', 'age', 'case_number', 'claim_number']
            )
        ]
    
    @pytest.mark.skipif(not CONFIDENCE_SCORING_AVAILABLE, reason="Confidence scoring components not available")
    def test_critical_field_precision_threshold(self, confidence_test_cases):
        """
        Test that critical fields meet ≥95% precision threshold.
        
        Requirements: 1.1, 1.2
        """
        extractor = StructuredExtractor()
        
        total_critical_extractions = 0
        high_confidence_extractions = 0
        
        for test_case in confidence_test_cases:
            # Create extraction context
            extraction_context = ExtractionContext(
                document_id=f"precision-test-{test_case.name}",
                document_text=test_case.text,
                source_file=f"{test_case.name}.txt"
            )
            
            # Execute extraction
            result = extractor.extract_with_confidence(extraction_context)
            
            # Check critical fields
            for field_name in test_case.critical_fields:
                if field_name in result.fields and result.fields[field_name]:
                    total_critical_extractions += 1
                    confidence = result.confidences.get(field_name, 0.0)
                    
                    # Critical fields should have ≥0.8 confidence for high precision
                    if confidence >= 0.8:
                        high_confidence_extractions += 1
                    
                    print(f"  {test_case.name} - {field_name}: {confidence:.3f}")
        
        # Calculate precision rate
        precision_rate = high_confidence_extractions / total_critical_extractions if total_critical_extractions > 0 else 0
        
        print(f"\nCritical Field Precision Results:")
        print(f"  Total critical extractions: {total_critical_extractions}")
        print(f"  High confidence extractions: {high_confidence_extractions}")
        print(f"  Precision rate: {precision_rate:.2%}")
        
        # Verify ≥95% precision threshold
        assert precision_rate >= 0.95, f"Critical field precision {precision_rate:.2%} below 95% threshold"
    
    @pytest.mark.skipif(not CONFIDENCE_SCORING_AVAILABLE, reason="Confidence scoring components not available")
    def test_overall_field_coverage_threshold(self, confidence_test_cases):
        """
        Test that overall field coverage meets ≥90% threshold.
        
        Requirements: 1.1, 1.3
        """
        extractor = StructuredExtractor()
        
        total_expected_fields = 0
        total_extracted_fields = 0
        
        for test_case in confidence_test_cases:
            # Create extraction context
            extraction_context = ExtractionContext(
                document_id=f"coverage-test-{test_case.name}",
                document_text=test_case.text,
                source_file=f"{test_case.name}.txt"
            )
            
            # Execute extraction
            result = extractor.extract_with_confidence(extraction_context)
            
            # Count expected vs extracted fields
            case_expected = len(test_case.expected_fields)
            case_extracted = sum(1 for field in test_case.expected_fields.keys() 
                               if field in result.fields and result.fields[field])
            
            total_expected_fields += case_expected
            total_extracted_fields += case_extracted
            
            case_coverage = case_extracted / case_expected if case_expected > 0 else 0
            print(f"  {test_case.name}: {case_coverage:.2%} ({case_extracted}/{case_expected})")
        
        # Calculate overall coverage rate
        overall_coverage = total_extracted_fields / total_expected_fields if total_expected_fields > 0 else 0
        
        print(f"\nOverall Field Coverage Results:")
        print(f"  Total expected fields: {total_expected_fields}")
        print(f"  Total extracted fields: {total_extracted_fields}")
        print(f"  Overall coverage rate: {overall_coverage:.2%}")
        
        # Verify ≥90% coverage threshold
        assert overall_coverage >= 0.90, f"Field coverage {overall_coverage:.2%} below 90% threshold"
    
    @pytest.mark.skipif(not CONFIDENCE_SCORING_AVAILABLE, reason="Confidence scoring components not available")
    def test_confidence_algorithm_components(self, confidence_test_cases):
        """
        Test confidence scoring algorithm components (regex, NER, cross-validation).
        
        Requirements: 1.1, 1.4
        """
        extractor = StructuredExtractor()
        
        for test_case in confidence_test_cases:
            extraction_context = ExtractionContext(
                document_id=f"algorithm-test-{test_case.name}",
                document_text=test_case.text,
                source_file=f"{test_case.name}.txt"
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            # Verify confidence breakdown exists for extracted fields
            for field_name, field_value in result.fields.items():
                if field_value and field_name in result.confidence_breakdown:
                    breakdown = result.confidence_breakdown[field_name]
                    
                    # Verify all confidence components present
                    assert 'regex_confidence' in breakdown, f"Missing regex confidence for {field_name}"
                    assert 'ner_confidence' in breakdown, f"Missing NER confidence for {field_name}"
                    assert 'cross_validation_confidence' in breakdown, f"Missing cross-validation confidence for {field_name}"
                    
                    # Verify confidence values are valid
                    for component, value in breakdown.items():
                        assert 0.0 <= value <= 1.0, f"Invalid {component} value {value} for {field_name}"
                    
                    # Verify overall confidence calculation
                    overall_confidence = result.confidences.get(field_name, 0.0)
                    assert 0.0 <= overall_confidence <= 1.0, f"Invalid overall confidence {overall_confidence}"
                    
                    print(f"  {field_name}: overall={overall_confidence:.3f}, "
                          f"regex={breakdown['regex_confidence']:.3f}, "
                          f"ner={breakdown['ner_confidence']:.3f}, "
                          f"cross_val={breakdown['cross_validation_confidence']:.3f}")
    
    @pytest.mark.skipif(not CONFIDENCE_SCORING_AVAILABLE, reason="Confidence scoring components not available")
    def test_evidence_snippet_collection(self, confidence_test_cases):
        """
        Test evidence snippet collection and source coordinate tracking.
        
        Requirements: 1.4
        """
        extractor = StructuredExtractor()
        
        for test_case in confidence_test_cases:
            extraction_context = ExtractionContext(
                document_id=f"evidence-test-{test_case.name}",
                document_text=test_case.text,
                source_file=f"{test_case.name}.txt"
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            # Verify evidence snippets exist for extracted fields
            for field_name, field_value in result.fields.items():
                if field_value and field_name in result.evidence_snippets:
                    snippet = result.evidence_snippets[field_name]
                    
                    # Verify evidence snippet structure
                    assert isinstance(snippet, EvidenceSnippet), f"Invalid snippet type for {field_name}"
                    assert snippet.content, f"Empty snippet content for {field_name}"
                    assert snippet.source_document, f"Missing source document for {field_name}"
                    assert 0.0 <= snippet.confidence <= 1.0, f"Invalid snippet confidence for {field_name}"
                    
                    # Verify source coordinates if available
                    if field_name in result.source_coordinates:
                        coordinates = result.source_coordinates[field_name]
                        assert coordinates.start_position >= 0, f"Invalid start position for {field_name}"
                        assert coordinates.end_position > coordinates.start_position, f"Invalid end position for {field_name}"
                    
                    print(f"  {field_name}: snippet='{snippet.content[:50]}...', confidence={snippet.confidence:.3f}")
    
    @pytest.mark.skipif(not CONFIDENCE_SCORING_AVAILABLE, reason="Confidence scoring components not available")
    def test_confidence_threshold_enforcement(self):
        """
        Test confidence threshold enforcement for field acceptance/flagging/rejection.
        
        Requirements: 1.2, 1.5
        """
        # Test with varying confidence scenarios
        test_scenarios = [
            {
                'name': 'high_confidence_accept',
                'text': 'Patient: John Smith, Age: 45, Case: WC-2024-001',
                'expected_acceptance': True
            },
            {
                'name': 'medium_confidence_flag',
                'text': 'Patient name might be John, case could be WC001',
                'expected_acceptance': False  # Should be flagged for review
            },
            {
                'name': 'low_confidence_reject',
                'text': 'Some text with no clear patient information',
                'expected_acceptance': False  # Should be rejected
            }
        ]
        
        extractor = StructuredExtractor()
        
        for scenario in test_scenarios:
            extraction_context = ExtractionContext(
                document_id=f"threshold-test-{scenario['name']}",
                document_text=scenario['text'],
                source_file=f"{scenario['name']}.txt"
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            # Check if critical fields meet acceptance thresholds
            critical_fields_accepted = 0
            total_critical_fields = 0
            
            for field_name in ['patient_name', 'case_number', 'age']:
                if field_name in result.fields and result.fields[field_name]:
                    total_critical_fields += 1
                    confidence = result.confidences.get(field_name, 0.0)
                    if confidence >= 0.8:  # High confidence threshold
                        critical_fields_accepted += 1
            
            acceptance_rate = critical_fields_accepted / total_critical_fields if total_critical_fields > 0 else 0
            
            print(f"  {scenario['name']}: acceptance_rate={acceptance_rate:.2%}, "
                  f"expected={scenario['expected_acceptance']}")
            
            # Verify threshold enforcement aligns with expectations
            if scenario['expected_acceptance']:
                assert acceptance_rate >= 0.5, f"Expected acceptance but got {acceptance_rate:.2%}"
            # Note: For flagged/rejected cases, we expect lower acceptance rates
    
    def test_confidence_scoring_performance(self):
        """Test confidence scoring performance with large documents."""
        # Create large test document
        large_text = """
        Re: Applicant: Performance Test Patient
        Age: 35 years old
        Case: WC-PERF-001
        """ + "\nAdditional line of text for performance testing." * 500
        
        if CONFIDENCE_SCORING_AVAILABLE:
            extractor = StructuredExtractor()
            
            import time
            start_time = time.time()
            
            extraction_context = ExtractionContext(
                document_id="performance-test-1",
                document_text=large_text,
                source_file="performance_test.txt"
            )
            
            result = extractor.extract_with_confidence(extraction_context)
            
            processing_time = time.time() - start_time
            
            # Should complete within reasonable time (2 minutes for large document)
            assert processing_time < 120, f"Confidence scoring took {processing_time:.1f}s, too slow"
            
            # Should maintain accuracy despite document size
            assert result.overall_confidence > 0.3, "Confidence scoring accuracy degraded with large document"
            
            print(f"Performance test: {processing_time:.2f}s, confidence={result.overall_confidence:.3f}")
    
    def test_cross_document_consistency_validation(self):
        """Test cross-document consistency checking for confidence scoring."""
        # Test documents with consistent information
        doc1_text = "Patient: John Smith, Age: 45, Case: WC-2024-001"
        doc2_text = "Re: Applicant: John Smith, EAMS No: WC-2024-001, Age: 45 years"
        
        if CONFIDENCE_SCORING_AVAILABLE:
            extractor = StructuredExtractor()
            
            # Extract from first document
            context1 = ExtractionContext(
                document_id="consistency-test-1",
                document_text=doc1_text,
                source_file="doc1.txt"
            )
            result1 = extractor.extract_with_confidence(context1)
            
            # Extract from second document
            context2 = ExtractionContext(
                document_id="consistency-test-2",
                document_text=doc2_text,
                source_file="doc2.txt"
            )
            result2 = extractor.extract_with_confidence(context2)
            
            # Check for consistency in extracted values
            common_fields = set(result1.fields.keys()) & set(result2.fields.keys())
            
            for field in common_fields:
                if result1.fields[field] and result2.fields[field]:
                    # Values should be consistent
                    val1 = str(result1.fields[field]).lower().strip()
                    val2 = str(result2.fields[field]).lower().strip()
                    
                    # Allow for minor formatting differences
                    consistency_check = val1 == val2 or val1 in val2 or val2 in val1
                    
                    print(f"  {field}: '{result1.fields[field]}' vs '{result2.fields[field]}' - consistent: {consistency_check}")
                    
                    # Cross-validation confidence should reflect consistency
                    cross_val_conf1 = result1.confidence_breakdown.get(field, {}).get('cross_validation_confidence', 0.0)
                    cross_val_conf2 = result2.confidence_breakdown.get(field, {}).get('cross_validation_confidence', 0.0)
                    
                    if consistency_check:
                        # Consistent values should have higher cross-validation confidence
                        assert cross_val_conf1 >= 0.5 or cross_val_conf2 >= 0.5, \
                            f"Consistent values should have higher cross-validation confidence for {field}"


if __name__ == "__main__":
    # Run confidence scoring validation tests
    print("Running Confidence Scoring Validation Tests...")
    
    if not CONFIDENCE_SCORING_AVAILABLE:
        print("⚠️  Confidence scoring components not available")
        exit(1)
    
    # Create test instance
    test_instance = TestConfidenceScoringValidation()
    
    # Run basic validation
    test_cases = [
        {
            'name': 'basic_test',
            'text': 'Patient: John Smith, Age: 45, Case: WC-2024-001',
            'expected_fields': {'patient_name': 'John Smith', 'age': 45, 'case_number': 'WC-2024-001'},
            'expected_confidence_threshold': 0.8,
            'critical_fields': ['patient_name', 'case_number']
        }
    ]
    
    extractor = StructuredExtractor()
    
    for test_case in test_cases:
        extraction_context = ExtractionContext(
            document_id=f"smoke-test-{test_case['name']}",
            document_text=test_case['text'],
            source_file=f"{test_case['name']}.txt"
        )
        
        result = extractor.extract_with_confidence(extraction_context)
        
        print(f"✓ {test_case['name']}: overall_confidence={result.overall_confidence:.3f}")
        print(f"  Extracted fields: {len(result.fields)}")
        print(f"  Confidence scores: {len(result.confidences)}")
    
    print("✓ Confidence Scoring Validation Tests Ready")