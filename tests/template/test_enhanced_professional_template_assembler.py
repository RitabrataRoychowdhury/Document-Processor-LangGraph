#!/usr/bin/env python3
"""
Test script for Enhanced Professional Template Assembler with Evidence Integration.

This script tests the enhanced professional template assembler that integrates
with evidence validation results and programmatic calculations.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from tests.template.test_enhanced_professional_template_assembler import (
        ProfessionalTemplateAssembler, TemplateAssemblyConfig, EvidenceIntegrationConfig
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings, Diagnosis, ImpairmentRating
    from src.core.validation.qme_field_validator import ValidationReport, ValidationStatus, EvidenceSnippet
    from src.core.calculation.impairment_calculator import ProgrammaticCalculationResult, CalculationStep, AMATableReference, ROMMeasurement
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_mock_validation_report() -> ValidationReport:
    """Create a mock validation report with accepted fields."""
    
    # Create mock evidence snippet
    from tests.unit.core.test_qme_field_extractor import DocumentCoordinate
    
    evidence_snippet = EvidenceSnippet(
        text="John Doe, 45-year-old male",
        context="Patient information: John Doe, 45-year-old male, injured on 06/15/2023",
        coordinates=DocumentCoordinate(page_number=1, start_char=100, end_char=125, line_number=5),
        extraction_method="regex"
    )
    
    validation_report = ValidationReport(
        accepted_fields={
            'name': 'John Doe',
            'age': 45,
            'gender': 'Male',
            'case_number': 'ADJ12345678',
            'claim_number': 'WC608-H07190',
            'injury_date': datetime(2023, 6, 15),
            'employer': 'ABC Construction Company',
            'occupation': 'Construction Worker',
            'body_parts': ['Lower Back', 'Left Knee']
        },
        flagged_fields={
            'medical_record_number': 'MRN123456'
        },
        missing_fields=['date_of_birth', 'insurance_carrier'],
        overall_confidence=0.82,
        evidence_completeness=0.75,
        critical_field_coverage=0.90,
        can_generate_report=True,
        validation_status=ValidationStatus.ACCEPTED,
        recommendations=[
            "Review flagged medical record number",
            "Obtain missing date of birth and insurance carrier information"
        ]
    )
    
    return validation_report


def create_mock_calculation_results() -> ProgrammaticCalculationResult:
    """Create mock programmatic calculation results."""
    
    # Mock ROM measurements
    rom_measurements = [
        ROMMeasurement(
            joint="Lumbar Spine",
            motion_type="flexion",
            measured_degrees=45.0,
            measurement_date=datetime.now(),
            examiner="Dr. Smith",
            notes="Patient cooperative, good effort"
        ),
        ROMMeasurement(
            joint="Lumbar Spine", 
            motion_type="extension",
            measured_degrees=20.0,
            measurement_date=datetime.now(),
            examiner="Dr. Smith",
            notes="Slight limitation noted"
        )
    ]
    
    # Mock AMA table reference
    ama_table_ref = AMATableReference(
        table_id="15-3",
        chapter=15,
        title="Range of Motion Impairments - Lumbar Spine",
        page_reference=384,
        method_type="ROM",
        body_system="spine"
    )
    
    # Mock calculation steps
    calculation_steps = [
        CalculationStep(
            step_number=1,
            description="Calculate flexion impairment",
            input_values={"measured_flexion": 45.0, "normal_flexion": 60.0},
            calculation="(60 - 45) / 60 * 5",
            result=1.25,
            ama_reference=ama_table_ref,
            notes="Using AMA Guides Table 15-3"
        ),
        CalculationStep(
            step_number=2,
            description="Calculate extension impairment", 
            input_values={"measured_extension": 20.0, "normal_extension": 25.0},
            calculation="(25 - 20) / 25 * 5",
            result=1.0,
            ama_reference=ama_table_ref,
            notes="Using AMA Guides Table 15-3"
        ),
        CalculationStep(
            step_number=3,
            description="Combine impairments using Combined Values Chart",
            input_values={"flexion_impairment": 1.25, "extension_impairment": 1.0},
            calculation="Combined Values Chart lookup",
            result=2.0,
            notes="Final whole person impairment"
        )
    ]
    
    calculation_result = ProgrammaticCalculationResult(
        impairment_percentage=2.0,
        ama_table_references=[ama_table_ref],
        calculation_steps=calculation_steps,
        source_measurements=rom_measurements,
        validation_status={
            "measurements_valid": True,
            "table_references_valid": True,
            "calculation_steps_valid": True,
            "final_result_valid": True
        },
        calculation_method="AMA Guides 5th Edition ROM Method"
    )
    
    return calculation_result


def create_mock_template_data() -> QMETemplateData:
    """Create mock QME template data."""
    
    # Patient information
    patient_info = PatientInfo(
        name="John Doe",
        age=45,
        gender="Male",
        case_number="ADJ12345678",
        injury_date=datetime(2023, 6, 15),
        employer="ABC Construction Company",
        occupation="Construction Worker",
        body_parts=["Lower Back", "Left Knee"],
        medical_record_number="MRN123456"
    )
    
    # Medical findings
    diagnosis = Diagnosis(
        id="diag_001",
        description="Lumbar strain with degenerative disc disease",
        icd_code="M54.5"
    )
    
    impairment_rating = ImpairmentRating(
        id="impair_001",
        diagnosis_id="diag_001",
        percentage=2.0,
        ama_table="15-3",
        rationale="Based on ROM measurements and AMA Guides 5th Edition calculations"
    )
    
    medical_findings = MedicalFindings(
        diagnoses=[diagnosis],
        impairment_ratings=[impairment_rating],
        findings=[],  # Will be populated with Finding objects if needed
        treatment_history=["Physical therapy", "NSAIDs", "Chiropractic care"],
        imaging_studies=["MRI lumbar spine showing mild disc degeneration at L4-L5"]
    )
    
    template_data = QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings
    )
    
    return template_data


def test_evidence_integration():
    """Test evidence integration functionality."""
    print("=== Testing Evidence Integration ===")
    
    try:
        # Create mock data
        template_data = create_mock_template_data()
        validation_report = create_mock_validation_report()
        calculation_results = create_mock_calculation_results()
        
        # Configure evidence integration
        evidence_config = EvidenceIntegrationConfig(
            use_only_accepted_fields=True,
            include_confidence_scores=True,
            include_source_citations=True,
            show_evidence_snippets=False,
            require_evidence_backing=True,
            min_confidence_threshold=0.8,
            include_calculation_audit_trail=True,
            show_ama_table_references=True
        )
        
        assembly_config = TemplateAssemblyConfig(
            include_quality_indicators=True,
            include_missing_placeholders=True,
            apply_professional_formatting=True,
            validate_before_assembly=True,
            validate_after_assembly=True,
            generate_quality_report=True,
            evidence_integration=evidence_config
        )
        
        # Initialize assembler
        assembler = ProfessionalTemplateAssembler()
        
        # Doctor information
        doctor_info = {
            'name': 'Jane Smith',
            'specialty': 'Orthopedic Surgery',
            'license': 'CA12345',
            'phone': '(555) 123-4567'
        }
        
        # Assemble template with evidence integration
        print("Assembling professional template with evidence integration...")
        result = assembler.assemble_professional_template(
            template_data=template_data,
            validation_report=validation_report,
            calculation_results=calculation_results,
            doctor_info=doctor_info,
            assembly_config=assembly_config
        )
        
        print(f"✓ Template assembled successfully: {result.file_path}")
        print(f"✓ File size: {result.file_size_bytes} bytes")
        print(f"✓ Estimated pages: {result.page_count}")
        print(f"✓ Word count: {result.word_count}")
        
        # Check evidence traceability
        if result.evidence_traceability:
            print(f"✓ Evidence completeness: {result.evidence_traceability.evidence_completeness_score:.1%}")
            print(f"✓ Fields with evidence: {len(result.evidence_traceability.evidence_sources)}")
            print(f"✓ Missing evidence fields: {len(result.evidence_traceability.missing_evidence_fields)}")
            
            # Show confidence scores
            print("\nConfidence Scores:")
            for field, confidence in result.evidence_traceability.confidence_scores.items():
                print(f"  {field}: {confidence:.2f}")
        
        # Check validation results
        if result.validation_report:
            print(f"✓ Accepted fields: {len(result.validation_report.accepted_fields)}")
            print(f"✓ Flagged fields: {len(result.validation_report.flagged_fields)}")
            print(f"✓ Missing fields: {len(result.validation_report.missing_fields)}")
        
        # Check calculation results
        if result.calculation_results:
            print(f"✓ Impairment percentage: {result.calculation_results.impairment_percentage}%")
            print(f"✓ Calculation steps: {len(result.calculation_results.calculation_steps)}")
            print(f"✓ AMA table references: {len(result.calculation_results.ama_table_references)}")
        
        # Check quality report
        if result.quality_report_path:
            print(f"✓ Quality report generated: {result.quality_report_path}")
        
        print("✓ Evidence integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Evidence integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_completeness_validation():
    """Test template completeness validation."""
    print("\n=== Testing Template Completeness Validation ===")
    
    try:
        # Create template data with missing fields
        template_data = create_mock_template_data()
        template_data.patient_info.name = None  # Remove name to test validation
        
        validation_report = create_mock_validation_report()
        validation_report.accepted_fields.pop('name', None)  # Remove from accepted fields
        validation_report.missing_fields.append('name')
        validation_report.can_generate_report = False
        
        # Configure for strict validation
        evidence_config = EvidenceIntegrationConfig(
            use_only_accepted_fields=True,
            require_evidence_backing=True,
            min_confidence_threshold=0.8
        )
        
        assembly_config = TemplateAssemblyConfig(
            validate_before_assembly=True,
            validate_after_assembly=True,
            evidence_integration=evidence_config
        )
        
        assembler = ProfessionalTemplateAssembler()
        
        print("Testing template with missing critical fields...")
        result = assembler.assemble_professional_template(
            template_data=template_data,
            validation_report=validation_report,
            assembly_config=assembly_config
        )
        
        # Check that validation caught the issues
        if result.pre_assembly_validation:
            print(f"✓ Pre-assembly validation found {len(result.pre_assembly_validation.validation_issues)} issues")
        
        if result.post_assembly_validation:
            print(f"✓ Post-assembly validation found {len(result.post_assembly_validation.validation_issues)} issues")
        
        # Check evidence traceability
        if result.evidence_traceability:
            missing_count = len(result.evidence_traceability.missing_evidence_fields)
            print(f"✓ Evidence traceability identified {missing_count} missing evidence fields")
        
        print("✓ Template completeness validation test completed!")
        return True
        
    except Exception as e:
        print(f"✗ Template completeness validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculation_audit_trail():
    """Test calculation audit trail integration."""
    print("\n=== Testing Calculation Audit Trail ===")
    
    try:
        template_data = create_mock_template_data()
        validation_report = create_mock_validation_report()
        calculation_results = create_mock_calculation_results()
        
        # Configure to include detailed audit trail
        evidence_config = EvidenceIntegrationConfig(
            include_calculation_audit_trail=True,
            show_ama_table_references=True
        )
        
        assembly_config = TemplateAssemblyConfig(
            evidence_integration=evidence_config
        )
        
        assembler = ProfessionalTemplateAssembler()
        
        print("Testing calculation audit trail integration...")
        result = assembler.assemble_professional_template(
            template_data=template_data,
            validation_report=validation_report,
            calculation_results=calculation_results,
            assembly_config=assembly_config
        )
        
        # Verify calculation results are integrated
        if result.calculation_results:
            print(f"✓ Calculation method: {result.calculation_results.calculation_method}")
            print(f"✓ Calculation steps: {len(result.calculation_results.calculation_steps)}")
            print(f"✓ Source measurements: {len(result.calculation_results.source_measurements)}")
            print(f"✓ AMA table references: {len(result.calculation_results.ama_table_references)}")
            
            # Check validation status
            validation_status = result.calculation_results.validation_status
            passed_checks = sum(1 for status in validation_status.values() if status)
            total_checks = len(validation_status)
            print(f"✓ Validation checks passed: {passed_checks}/{total_checks}")
        
        print("✓ Calculation audit trail test completed!")
        return True
        
    except Exception as e:
        print(f"✗ Calculation audit trail test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests for enhanced professional template assembler."""
    print("Enhanced Professional Template Assembler Test Suite")
    print("=" * 55)
    
    tests = [
        test_evidence_integration,
        test_template_completeness_validation,
        test_calculation_audit_trail
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced Professional Template Assembler is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())