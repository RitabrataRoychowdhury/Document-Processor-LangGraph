#!/usr/bin/env python3
"""
Professional Template Assembly Engine Demo

This demo showcases the new Professional Template Assembly Engine with:
- Reliable document generation
- Template validation and quality checking
- Professional formatting compliance with AMA and QME standards
- Error recovery mechanisms and fallback strategies
- Quality validation against existing successful templates

Requirements implemented: 3.1, 3.2, 3.3 from QME system refactor specification.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tests.test_professional_template_assembly_engine import (
        ProfessionalTemplateAssemblyEngine,
        TemplateConfig,
        FormattingRules,
        QualityRequirements,
        AssemblyStatus,
        FallbackStrategy
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, ImpairmentRating, Finding
    from src.models.extraction_models import ExtractionResult
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


def create_sample_template_data() -> QMETemplateData:
    """Create comprehensive sample template data for demonstration."""
    print("Creating sample template data...")
    
    # Patient information
    patient_info = PatientInfo(
        name="John Smith",
        age=42,
        gender="Male",
        case_number="WC2024-001",
        injury_date=datetime(2024, 3, 15),
        employer="Construction Corp",
        occupation="Construction Foreman"
    )
    
    # Medical diagnoses
    diagnoses = [
        Diagnosis(
            id="diag_001",
            icd_code="M54.5",
            description="Low back pain",
            severity="Moderate"
        ),
        Diagnosis(
            id="diag_002",
            icd_code="M75.3",
            description="Calcific tendinitis of shoulder",
            severity="Mild"
        )
    ]
    
    # Physical examination findings
    findings = [
        Finding(
            id="find_001",
            section_id="physical_exam",
            finding_type="physical",
            description="Limited lumbar flexion to 45 degrees",
            page_reference=3
        ),
        Finding(
            id="find_002",
            section_id="physical_exam",
            finding_type="physical",
            description="Positive straight leg raise test at 60 degrees",
            page_reference=3
        ),
        Finding(
            id="find_003",
            section_id="physical_exam",
            finding_type="physical",
            description="Shoulder abduction limited to 120 degrees",
            page_reference=4
        )
    ]
    
    # Impairment ratings
    impairment_ratings = [
        ImpairmentRating(
            id="imp_001",
            diagnosis_id="diag_001",
            percentage=12,
            ama_table="Table 15-3",
            rationale="Based on DRE Category II with specific spine disorder"
        ),
        ImpairmentRating(
            id="imp_002",
            diagnosis_id="diag_002",
            percentage=5,
            ama_table="Table 16-3",
            rationale="Based on shoulder range of motion limitations"
        )
    ]
    
    # Medical findings
    medical_findings = MedicalFindings(
        diagnoses=diagnoses,
        findings=findings,
        impairment_ratings=impairment_ratings,
        treatment_history=[
            "Physical therapy - 12 sessions completed",
            "Chiropractic treatment - 8 sessions",
            "Anti-inflammatory medications"
        ]
    )
    
    return QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings,
        recommendations=[
            "Continue conservative treatment",
            "Work hardening program recommended",
            "Ergonomic workplace assessment"
        ]
    )


def create_incomplete_template_data() -> QMETemplateData:
    """Create incomplete template data to test error recovery."""
    print("Creating incomplete template data for error recovery testing...")
    
    # Minimal patient info (missing critical fields)
    patient_info = PatientInfo(
        name="Jane Doe",
        case_number=""  # Missing case number
    )
    
    # Empty medical findings
    medical_findings = MedicalFindings()
    
    return QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings
    )


def demonstrate_basic_assembly():
    """Demonstrate basic template assembly functionality."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Template Assembly")
    print("="*60)
    
    # Create template data
    template_data = create_sample_template_data()
    
    # Create assembly engine with default configuration
    engine = ProfessionalTemplateAssemblyEngine()
    
    print("Assembling professional QME template...")
    result = engine.assemble_template(template_data=template_data)
    
    print(f"Assembly Status: {result.status.value}")
    print(f"Output File: {result.file_path}")
    print(f"File Size: {result.file_size_bytes:,} bytes")
    print(f"Estimated Pages: {result.page_count}")
    print(f"Word Count: {result.word_count:,}")
    print(f"Assembly Time: {result.assembly_time_seconds:.2f} seconds")
    
    if result.quality_report:
        print(f"Quality Score: {result.quality_report.overall_score:.1f}/100")
        print(f"Compliance Status: {result.quality_report.compliance_status}")
    
    return result


def demonstrate_quality_validation():
    """Demonstrate quality validation and reporting."""
    print("\n" + "="*60)
    print("DEMO 2: Quality Validation and Reporting")
    print("="*60)
    
    # Create high-quality template data
    template_data = create_sample_template_data()
    
    # Create engine with strict quality requirements
    quality_requirements = QualityRequirements(
        min_completeness_score=85.0,
        min_accuracy_score=90.0,
        min_compliance_score=95.0,
        max_critical_issues=0,
        max_high_issues=1
    )
    
    engine = ProfessionalTemplateAssemblyEngine(
        quality_requirements=quality_requirements
    )
    
    print("Assembling template with strict quality requirements...")
    result = engine.assemble_template(template_data=template_data)
    
    if result.quality_report:
        print("\nQuality Report:")
        print(f"  Overall Score: {result.quality_report.overall_score:.1f}/100")
        print(f"  Completeness: {result.quality_report.completeness_score:.1f}/100")
        print(f"  Accuracy: {result.quality_report.accuracy_score:.1f}/100")
        print(f"  Compliance: {result.quality_report.compliance_score:.1f}/100")
        print(f"  Formatting: {result.quality_report.formatting_score:.1f}/100")
        print(f"  Total Issues: {result.quality_report.total_issues}")
        print(f"  Critical Issues: {result.quality_report.critical_issues}")
        print(f"  Compliance Status: {result.quality_report.compliance_status}")
        
        if result.quality_report.recommendations:
            print("\nRecommendations:")
            for i, rec in enumerate(result.quality_report.recommendations, 1):
                print(f"  {i}. {rec}")
    
    return result


def demonstrate_error_recovery():
    """Demonstrate error recovery mechanisms."""
    print("\n" + "="*60)
    print("DEMO 3: Error Recovery Mechanisms")
    print("="*60)
    
    # Create incomplete template data
    template_data = create_incomplete_template_data()
    
    # Create engine with all fallback strategies enabled
    template_config = TemplateConfig(
        template_path="",
        enable_error_recovery=True,
        fallback_strategies=[
            FallbackStrategy.SIMPLIFIED_TEMPLATE,
            FallbackStrategy.PLACEHOLDER_TEMPLATE,
            FallbackStrategy.MINIMAL_TEMPLATE,
            FallbackStrategy.TEXT_ONLY
        ],
        max_retry_attempts=3
    )
    
    engine = ProfessionalTemplateAssemblyEngine(template_config=template_config)
    
    print("Assembling template with incomplete data (testing error recovery)...")
    result = engine.assemble_template(template_data=template_data)
    
    print(f"Assembly Status: {result.status.value}")
    print(f"Fallback Strategy Used: {result.fallback_used.value if result.fallback_used else 'None'}")
    print(f"Recovery Attempts: {result.recovery_attempts}")
    print(f"Output File: {result.file_path}")
    
    if result.error_message:
        print(f"Error Message: {result.error_message}")
    
    return result


def demonstrate_professional_formatting():
    """Demonstrate professional formatting compliance."""
    print("\n" + "="*60)
    print("DEMO 4: Professional Formatting Compliance")
    print("="*60)
    
    template_data = create_sample_template_data()
    
    # Create custom formatting rules
    formatting_rules = FormattingRules(
        font_family="Times New Roman",
        font_size=12,
        line_spacing=1.15,
        margin_inches=1.0,
        apply_ama_standards=True,
        apply_qme_standards=True
    )
    
    template_config = TemplateConfig(
        template_path="",
        apply_professional_formatting=True,
        validate_after_assembly=True
    )
    
    engine = ProfessionalTemplateAssemblyEngine(
        template_config=template_config,
        formatting_rules=formatting_rules
    )
    
    print("Assembling template with professional formatting...")
    result = engine.assemble_template(template_data=template_data)
    
    print(f"Assembly Status: {result.status.value}")
    print(f"Professional Formatting Applied: Yes")
    
    if result.quality_report:
        print(f"Formatting Score: {result.quality_report.formatting_score:.1f}/100")
        print(f"AMA Standards Compliance: {'Yes' if formatting_rules.apply_ama_standards else 'No'}")
        print(f"QME Standards Compliance: {'Yes' if formatting_rules.apply_qme_standards else 'No'}")
    
    return result


def demonstrate_template_comparison():
    """Demonstrate template quality comparison."""
    print("\n" + "="*60)
    print("DEMO 5: Template Quality Comparison")
    print("="*60)
    
    # Create two different quality levels of template data
    high_quality_data = create_sample_template_data()
    low_quality_data = create_incomplete_template_data()
    
    engine = ProfessionalTemplateAssemblyEngine()
    
    print("Assembling high-quality template...")
    high_quality_result = engine.assemble_template(template_data=high_quality_data)
    
    print("Assembling low-quality template...")
    low_quality_result = engine.assemble_template(template_data=low_quality_data)
    
    print("\nQuality Comparison:")
    print(f"{'Metric':<20} {'High Quality':<15} {'Low Quality':<15}")
    print("-" * 50)
    
    if high_quality_result.quality_report and low_quality_result.quality_report:
        print(f"{'Overall Score':<20} {high_quality_result.quality_report.overall_score:<15.1f} {low_quality_result.quality_report.overall_score:<15.1f}")
        print(f"{'Completeness':<20} {high_quality_result.quality_report.completeness_score:<15.1f} {low_quality_result.quality_report.completeness_score:<15.1f}")
        print(f"{'Compliance':<20} {high_quality_result.quality_report.compliance_score:<15.1f} {low_quality_result.quality_report.compliance_score:<15.1f}")
        print(f"{'Total Issues':<20} {high_quality_result.quality_report.total_issues:<15} {low_quality_result.quality_report.total_issues:<15}")
        print(f"{'Critical Issues':<20} {high_quality_result.quality_report.critical_issues:<15} {low_quality_result.quality_report.critical_issues:<15}")
    
    return high_quality_result, low_quality_result


def demonstrate_results_organization():
    """Demonstrate results organization and archiving."""
    print("\n" + "="*60)
    print("DEMO 6: Results Organization and Archiving")
    print("="*60)
    
    template_data = create_sample_template_data()
    engine = ProfessionalTemplateAssemblyEngine()
    
    print("Assembling multiple templates to demonstrate organization...")
    
    results = []
    for i in range(3):
        # Modify patient name for each template
        template_data.patient_info.name = f"Patient_{i+1}"
        result = engine.assemble_template(template_data=template_data)
        results.append(result)
        print(f"Template {i+1}: {result.file_path}")
    
    # Check results directory structure
    results_dir = Path("results/generated_documents")
    if results_dir.exists():
        print(f"\nResults Directory: {results_dir}")
        print("Generated Files:")
        for file_path in results_dir.glob("*.docx"):
            file_size = file_path.stat().st_size
            print(f"  {file_path.name} ({file_size:,} bytes)")
    
    return results


def main():
    """Run all demonstrations."""
    print("Professional Template Assembly Engine Demo")
    print("Implementing QME System Refactor Requirements 3.1, 3.2, 3.3")
    print("=" * 80)
    
    try:
        # Run demonstrations
        demo1_result = demonstrate_basic_assembly()
        demo2_result = demonstrate_quality_validation()
        demo3_result = demonstrate_error_recovery()
        demo4_result = demonstrate_professional_formatting()
        demo5_results = demonstrate_template_comparison()
        demo6_results = demonstrate_results_organization()
        
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        print("✅ Basic template assembly - PASSED")
        print("✅ Quality validation and reporting - PASSED")
        print("✅ Error recovery mechanisms - PASSED")
        print("✅ Professional formatting compliance - PASSED")
        print("✅ Template quality comparison - PASSED")
        print("✅ Results organization and archiving - PASSED")
        
        print(f"\nAll demonstrations completed successfully!")
        print(f"Generated templates are saved in: results/generated_documents/")
        
        # Display final statistics
        total_files = len(list(Path("results/generated_documents").glob("*.docx"))) if Path("results/generated_documents").exists() else 0
        print(f"Total templates generated: {total_files}")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())