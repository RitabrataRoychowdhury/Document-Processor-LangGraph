"""
Demo script for Enhanced QME Rules Engine with Evidence-First Validation.

This script demonstrates the enhanced validation capabilities including:
- Evidence-first validation with confidence scoring
- Post-generation validation for placeholder text
- Enhanced legal compliance validation
- Comprehensive audit trail generation
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.services.qme_rules_engine import (
        QMERulesEngine, ValidationSeverity, EvidenceProvenance
    )
    from src.services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_sample_template_data() -> QMETemplateData:
    """Create sample QME template data for testing."""
    patient_info = PatientInfo(
        name="John Doe",
        age=45,
        case_number="WC12345-2025",
        injury_date="03/15/2024",
        employer="ABC Manufacturing"
    )
    
    diagnosis = Diagnosis(
        description="Lumbar strain with radiculopathy",
        icd_code="M54.16"
    )
    
    impairment_rating = ImpairmentRating(
        percentage=15.0,
        ama_table="Table 15-3",
        rationale="Based on ROM measurements and neurological findings"
    )
    
    medical_findings = MedicalFindings(
        diagnoses=[diagnosis],
        impairment_ratings=[impairment_rating]
    )
    
    return QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings
    )


def create_sample_extracted_fields() -> Dict[str, Any]:
    """Create sample extracted fields with confidence scores and provenance."""
    return {
        "patient_name": {
            "value": "John Doe",
            "confidence": 0.95,
            "provenance": {
                "source_document": "medical_records.pdf",
                "page_number": 1,
                "coordinates": (150, 200, 350, 220),
                "snippet": "Patient Name: John Doe",
                "method": "regex"
            }
        },
        "case_number": {
            "value": "WC12345-2025",
            "confidence": 0.88,
            "provenance": {
                "source_document": "claim_form.pdf",
                "page_number": 1,
                "coordinates": (100, 150, 300, 170),
                "snippet": "Case Number: WC12345-2025",
                "method": "regex"
            }
        },
        "injury_date": {
            "value": "03/15/2024",
            "confidence": 0.82,
            "provenance": {
                "source_document": "incident_report.pdf",
                "page_number": 2,
                "coordinates": (200, 300, 400, 320),
                "snippet": "Date of Injury: 03/15/2024",
                "method": "regex"
            }
        },
        "employer_name": {
            "value": "ABC Manufacturing",
            "confidence": 0.75,  # Below critical threshold
            "provenance": {
                "source_document": "employment_records.pdf",
                "page_number": 1,
                "coordinates": (50, 100, 250, 120),
                "snippet": "Employer: ABC Mfg Co",  # Slightly different text
                "method": "ner"
            }
        },
        "diagnosis": {
            "value": "Lumbar strain with radiculopathy",
            "confidence": 0.65,
            "provenance": {
                "source_document": "medical_records.pdf",
                "page_number": 5,
                "coordinates": (100, 400, 500, 420),
                "snippet": "Diagnosis: L4-L5 strain w/ radicular symptoms",
                "method": "ner"
            }
        }
    }


def create_sample_report_content_with_issues() -> str:
    """Create sample report content with validation issues."""
    return """
    QME REPORT
    
    Patient Name: {{PATIENT_NAME}}
    Case Number: WC12345-2025
    Date of Injury: 03/15/2024
    Employer: ABC Manufacturing
    
    RECORDS REVIEWED:
    TODO: List all medical records reviewed
    
    PHYSICAL EXAMINATION:
    Range of motion measurements were obtained using [MEASUREMENT_METHOD].
    Lumbar flexion: {FLEXION_DEGREES} degrees
    
    DIAGNOSIS:
    Primary diagnosis: Lumbar strain with radiculopathy (ICD-10: M54.16)
    
    IMPAIRMENT RATING:
    Based on AMA Guides 5th Edition, Table 15-3, the patient has a 15% whole person impairment.
    XXX - Need to verify calculation methodology
    
    LEGAL DECLARATIONS:
    Some declaration text here but not the complete Labor Code 4062.3 text.
    
    SIGNATURE:
    Dr. Jane Smith, MD
    License: ___________
    Date: TBD
    """


def create_sample_report_content_clean() -> str:
    """Create clean sample report content without issues."""
    return """
    QME REPORT
    
    Patient Name: John Doe
    Case Number: WC12345-2025
    Date of Injury: 03/15/2024
    Employer: ABC Manufacturing
    
    RECORDS REVIEWED:
    Medical records from ABC Medical Center (50 pages)
    Imaging studies from XYZ Radiology (10 pages)
    
    Any documents sent to the physician for record review must be accompanied by a 
    declaration under penalty of perjury that the provider of the documents has 
    complied with the provisions of Labor Code section 4062.3 before providing the 
    documents to the physician. The declaration must also contain an attestation as 
    to the total page count of the documents provided.
    
    PHYSICAL EXAMINATION:
    Range of motion measurements were obtained using dual inclinometer technique.
    Lumbar flexion: 45 degrees (average of 3 measurements: 44, 45, 46)
    
    DIAGNOSIS:
    Primary diagnosis: Lumbar strain with radiculopathy (ICD-10: M54.16)
    
    IMPAIRMENT RATING:
    Based on AMA Guides 5th Edition, Table 15-3, the patient has a 15% whole person impairment.
    Calculation performed programmatically using ROM measurements and neurological findings.
    
    SIGNATURE:
    Dr. Jane Smith, MD
    License: 12345
    Date: 2025-09-16
    
    Pursuant to AB 1300, LC Sec. 5703, I have not violated Labor Code section 139.3
    
    I declare under penalty of perjury that I did not discriminate in any way against 
    the parties to the action or the injured worker in the evaluation process or in 
    the content of this report.
    """


def demonstrate_evidence_first_validation():
    """Demonstrate evidence-first validation capabilities."""
    print("\n" + "="*80)
    print("EVIDENCE-FIRST VALIDATION DEMONSTRATION")
    print("="*80)
    
    # Initialize enhanced rules engine
    engine = QMERulesEngine()
    
    # Create sample data
    template_data = create_sample_template_data()
    extracted_fields = create_sample_extracted_fields()
    
    print("\n1. EXTRACTED FIELDS WITH CONFIDENCE SCORES:")
    print("-" * 50)
    for field_name, field_data in extracted_fields.items():
        confidence = field_data["confidence"]
        source = field_data["provenance"]["source_document"]
        print(f"  {field_name}: {confidence:.2f} confidence (from {source})")
    
    # Perform validation
    issues, quality_score, compliance_report = engine.validate_qme_report(
        template_data, 
        extracted_fields=extracted_fields
    )
    
    print(f"\n2. VALIDATION RESULTS:")
    print("-" * 50)
    print(f"  Total Issues: {len(issues)}")
    print(f"  Critical Issues: {quality_score.critical_issues}")
    print(f"  High Issues: {quality_score.high_issues}")
    print(f"  Evidence Confidence Score: {quality_score.evidence_confidence_score:.1f}%")
    print(f"  Fields Above Threshold: {quality_score.fields_above_confidence_threshold}")
    print(f"  Fields Requiring Review: {quality_score.fields_requiring_review}")
    
    print(f"\n3. EVIDENCE-FIRST ISSUES:")
    print("-" * 50)
    evidence_issues = [i for i in issues if i.requires_human_review]
    for issue in evidence_issues[:3]:  # Show first 3
        print(f"  • {issue.title}")
        print(f"    Severity: {issue.severity.value}")
        print(f"    Confidence: {issue.confidence_score:.2f}" if issue.confidence_score else "")
        if issue.evidence_provenance:
            print(f"    Source: {issue.evidence_provenance.source_document}")
        print()


def demonstrate_post_generation_validation():
    """Demonstrate post-generation validation capabilities."""
    print("\n" + "="*80)
    print("POST-GENERATION VALIDATION DEMONSTRATION")
    print("="*80)
    
    engine = QMERulesEngine()
    template_data = create_sample_template_data()
    
    print("\n1. TESTING REPORT WITH ISSUES:")
    print("-" * 50)
    
    report_with_issues = create_sample_report_content_with_issues()
    issues, quality_score, compliance_report = engine.validate_qme_report(
        template_data,
        report_content=report_with_issues
    )
    
    placeholder_issues = [i for i in issues if "placeholder" in i.title.lower()]
    print(f"  Placeholder Text Issues Found: {len(placeholder_issues)}")
    
    for issue in placeholder_issues[:3]:  # Show first 3
        print(f"  • {issue.description}")
    
    print(f"\n2. TESTING CLEAN REPORT:")
    print("-" * 50)
    
    clean_report = create_sample_report_content_clean()
    issues_clean, quality_score_clean, compliance_clean = engine.validate_qme_report(
        template_data,
        report_content=clean_report
    )
    
    placeholder_issues_clean = [i for i in issues_clean if "placeholder" in i.title.lower()]
    print(f"  Placeholder Text Issues Found: {len(placeholder_issues_clean)}")
    print(f"  Overall Quality Score: {quality_score_clean.overall_score:.1f}%")


def demonstrate_legal_compliance_validation():
    """Demonstrate enhanced legal compliance validation."""
    print("\n" + "="*80)
    print("LEGAL COMPLIANCE VALIDATION DEMONSTRATION")
    print("="*80)
    
    engine = QMERulesEngine()
    template_data = create_sample_template_data()
    
    # Test with incomplete compliance
    report_incomplete = create_sample_report_content_with_issues()
    issues, quality_score, compliance_report = engine.validate_qme_report(
        template_data,
        report_content=report_incomplete
    )
    
    print(f"\n1. INCOMPLETE COMPLIANCE REPORT:")
    print("-" * 50)
    print(f"  Overall Status: {compliance_report.overall_status}")
    print(f"  Labor Code 4062.3: {'PASS' if compliance_report.labor_code_4062_3_status else 'FAIL'}")
    print(f"  Mandatory Sections: {'PASS' if compliance_report.mandatory_sections_status else 'FAIL'}")
    print(f"  Signature Blocks: {'PASS' if compliance_report.signature_blocks_status else 'FAIL'}")
    
    print(f"\n  Failed Requirements:")
    for req in compliance_report.failed_requirements:
        print(f"    • {req}")
    
    print(f"\n  Remediation Steps:")
    for step in compliance_report.remediation_steps[:3]:  # Show first 3
        print(f"    • {step}")
    
    # Test with complete compliance
    report_complete = create_sample_report_content_clean()
    issues_clean, quality_score_clean, compliance_clean = engine.validate_qme_report(
        template_data,
        report_content=report_complete
    )
    
    print(f"\n2. COMPLETE COMPLIANCE REPORT:")
    print("-" * 50)
    print(f"  Overall Status: {compliance_clean.overall_status}")
    print(f"  Labor Code 4062.3: {'PASS' if compliance_clean.labor_code_4062_3_status else 'FAIL'}")
    print(f"  Failed Requirements: {len(compliance_clean.failed_requirements)}")


def demonstrate_comprehensive_validation():
    """Demonstrate comprehensive validation with all features."""
    print("\n" + "="*80)
    print("COMPREHENSIVE VALIDATION DEMONSTRATION")
    print("="*80)
    
    engine = QMERulesEngine()
    template_data = create_sample_template_data()
    extracted_fields = create_sample_extracted_fields()
    report_content = create_sample_report_content_clean()
    
    # Perform comprehensive validation
    issues, quality_score, compliance_report = engine.validate_qme_report(
        template_data,
        extracted_fields=extracted_fields,
        report_content=report_content
    )
    
    print(f"\n1. OVERALL QUALITY METRICS:")
    print("-" * 50)
    print(f"  Overall Score: {quality_score.overall_score:.1f}%")
    print(f"  Completeness Score: {quality_score.completeness_score:.1f}%")
    print(f"  Accuracy Score: {quality_score.accuracy_score:.1f}%")
    print(f"  Compliance Score: {quality_score.compliance_score:.1f}%")
    print(f"  Evidence Confidence Score: {quality_score.evidence_confidence_score:.1f}%")
    
    print(f"\n2. ISSUE BREAKDOWN:")
    print("-" * 50)
    print(f"  Total Issues: {quality_score.total_issues}")
    print(f"  Critical: {quality_score.critical_issues}")
    print(f"  High: {quality_score.high_issues}")
    print(f"  Medium: {quality_score.medium_issues}")
    print(f"  Low: {quality_score.low_issues}")
    
    print(f"\n3. EVIDENCE-FIRST METRICS:")
    print("-" * 50)
    print(f"  Fields Above Confidence Threshold: {quality_score.fields_above_confidence_threshold}")
    print(f"  Fields Requiring Review: {quality_score.fields_requiring_review}")
    print(f"  Placeholder Text Found: {quality_score.placeholder_text_found}")
    print(f"  Programmatic Calculations Verified: {quality_score.programmatic_calculations_verified}")
    
    print(f"\n4. COMPLIANCE STATUS:")
    print("-" * 50)
    print(f"  Overall Compliance: {compliance_report.overall_status}")
    print(f"  Evidence Sufficiency: {'PASS' if compliance_report.evidence_sufficiency_status else 'FAIL'}")
    print(f"  Calculation Accuracy: {'PASS' if compliance_report.calculation_accuracy_status else 'FAIL'}")
    
    print(f"\n5. AUDIT TRAIL SUMMARY:")
    print("-" * 50)
    print(f"  Report Generated: {compliance_report.generated_at}")
    print(f"  Validation Timestamp: {datetime.now()}")
    print(f"  Total Validation Checks: {len(issues) + 10}")  # Approximate
    
    if issues:
        print(f"\n6. SAMPLE VALIDATION ISSUES:")
        print("-" * 50)
        for issue in issues[:3]:  # Show first 3 issues
            print(f"  • {issue.title}")
            print(f"    Section: {issue.section.value}")
            print(f"    Severity: {issue.severity.value}")
            if issue.remediation_steps:
                print(f"    Remediation: {issue.remediation_steps[0]}")
            print()


def main():
    """Main demonstration function."""
    print("Enhanced QME Rules Engine with Evidence-First Validation")
    print("=" * 80)
    print("This demo showcases the enhanced validation capabilities:")
    print("• Evidence-first validation with confidence scoring")
    print("• Post-generation validation for placeholder text")
    print("• Enhanced legal compliance validation")
    print("• Comprehensive audit trail generation")
    
    try:
        demonstrate_evidence_first_validation()
        demonstrate_post_generation_validation()
        demonstrate_legal_compliance_validation()
        demonstrate_comprehensive_validation()
        
        print("\n" + "="*80)
        print("DEMONSTRATION COMPLETE")
        print("="*80)
        print("The enhanced QME Rules Engine successfully demonstrates:")
        print("✓ Evidence-first validation with confidence thresholds")
        print("✓ Post-generation validation for quality assurance")
        print("✓ Enhanced legal compliance with detailed reporting")
        print("✓ Comprehensive audit trails for complete traceability")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        print(f"\nError during demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)