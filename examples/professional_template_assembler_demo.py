"""
Professional Template Assembler Demo.

This script demonstrates the Professional Template Assembly System with
gold standard compliance, comprehensive validation, and quality assurance.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from src.services.professional_template_assembler_simple import (
        ProfessionalTemplateAssembler,
        TemplateAssemblyConfig
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_comprehensive_sample_data():
    """Create comprehensive sample data for demonstration."""
    print("📋 Creating comprehensive sample patient data...")
    
    # Patient information
    patient_info = PatientInfo(
        name="Robert Johnson",
        age=52,
        gender="Male",
        case_number="WC2024-DEMO-001",
        medical_record_number="MRN-789456",
        injury_date=datetime(2024, 1, 15),
        employer="Industrial Manufacturing Corp",
        occupation="Machine Operator",
        body_parts=["Lower Back", "Right Shoulder"]
    )
    
    # Primary diagnosis
    primary_diagnosis = Diagnosis(
        id="diag_001",
        icd_code="M54.5",
        description="Low back pain",
        severity="moderate",
        certainty=0.9,
        source_section_id="medical_records_001"
    )
    
    # Secondary diagnosis
    secondary_diagnosis = Diagnosis(
        id="diag_002", 
        icd_code="M75.3",
        description="Calcific tendinitis of shoulder",
        severity="mild",
        certainty=0.8,
        source_section_id="medical_records_002"
    )
    
    # Clinical findings
    findings = [
        Finding(
            id="find_001",
            section_id="physical_exam_001",
            finding_type="examination",
            description="Decreased lumbar flexion to 45 degrees (normal 90 degrees)"
        ),
        Finding(
            id="find_002",
            section_id="physical_exam_002", 
            finding_type="examination",
            description="Right shoulder abduction limited to 120 degrees (normal 180 degrees)"
        ),
        Finding(
            id="find_003",
            section_id="physical_exam_003",
            finding_type="neurological",
            description="Positive straight leg raise test at 60 degrees bilaterally"
        ),
        Finding(
            id="find_004",
            section_id="physical_exam_004",
            finding_type="palpation",
            description="Tenderness over L4-L5 spinous processes and right subacromial space"
        )
    ]
    
    # Impairment ratings
    impairment_ratings = [
        ImpairmentRating(
            id="rating_001",
            diagnosis_id="diag_001",
            percentage=12,
            ama_table="15-3",
            rationale="Based on DRE Category II findings with specific articular disorder per AMA Guides 5th Edition Table 15-3",
            body_part="Lumbar Spine",
            measurement_method="DRE Method"
        ),
        ImpairmentRating(
            id="rating_002", 
            diagnosis_id="diag_002",
            percentage=5,
            ama_table="16-3",
            rationale="Based on shoulder ROM limitations per AMA Guides 5th Edition Table 16-3",
            body_part="Right Shoulder",
            measurement_method="ROM Method"
        )
    ]
    
    # Imaging studies
    imaging_studies = [
        "MRI Lumbar Spine (01/20/2024): Mild disc degeneration L4-L5 with small central disc protrusion",
        "X-ray Right Shoulder (01/18/2024): Calcific deposits in supraspinatus tendon",
        "CT Lumbar Spine (02/15/2024): No evidence of fracture, mild facet arthropathy L4-L5"
    ]
    
    # Treatment history
    treatment_history = [
        "Physical therapy - 12 sessions completed",
        "NSAIDs (Ibuprofen 600mg TID) - ongoing",
        "Corticosteroid injection right shoulder - 02/10/2024",
        "Chiropractic treatment - 8 sessions",
        "Work hardening program - 4 weeks completed"
    ]
    
    # Medical findings
    medical_findings = MedicalFindings(
        diagnoses=[primary_diagnosis, secondary_diagnosis],
        findings=findings,
        impairment_ratings=impairment_ratings,
        imaging_studies=imaging_studies,
        treatment_history=treatment_history
    )
    
    # Template data
    template_data = QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings,
        missing_sections=["Social History", "Family History"],
        recommendations=[
            "Complete detailed social history including smoking and alcohol use",
            "Obtain family history of musculoskeletal disorders",
            "Consider MRI right shoulder if conservative treatment fails"
        ],
        ama_guidelines=[
            "AMA Guides 5th Edition Chapter 15 - Spine",
            "AMA Guides 5th Edition Chapter 16 - Upper Extremities"
        ]
    )
    
    print(f"✅ Created sample data for patient: {patient_info.name}")
    print(f"   - {len(medical_findings.diagnoses)} diagnoses")
    print(f"   - {len(medical_findings.findings)} clinical findings")
    print(f"   - {len(medical_findings.impairment_ratings)} impairment ratings")
    print(f"   - {len(medical_findings.imaging_studies)} imaging studies")
    
    return template_data


def create_doctor_information():
    """Create sample doctor information."""
    return {
        'name': 'Michael Thompson',
        'license': 'CA-MD-12345',
        'specialty': 'Orthopaedic Surgery',
        'clinic': 'Advanced Orthopaedic Associates',
        'address': '123 Medical Center Drive\nSuite 200\nSan Francisco, CA 94102',
        'phone': '(415) 555-0123',
        'email': 'mthompson@advancedortho.com'
    }


def demonstrate_basic_assembly():
    """Demonstrate basic template assembly."""
    print("\n" + "="*60)
    print("🏥 BASIC TEMPLATE ASSEMBLY DEMONSTRATION")
    print("="*60)
    
    # Create assembler
    assembler = ProfessionalTemplateAssembler()
    
    # Create sample data
    template_data = create_comprehensive_sample_data()
    doctor_info = create_doctor_information()
    
    # Basic configuration
    config = TemplateAssemblyConfig(
        include_quality_indicators=False,
        include_missing_placeholders=True,
        apply_professional_formatting=True,
        validate_before_assembly=True,
        validate_after_assembly=True,
        generate_quality_report=True
    )
    
    print(f"\n📋 Assembly Configuration:")
    print(f"   - Quality Indicators: {config.include_quality_indicators}")
    print(f"   - Missing Placeholders: {config.include_missing_placeholders}")
    print(f"   - Professional Formatting: {config.apply_professional_formatting}")
    print(f"   - Pre-Assembly Validation: {config.validate_before_assembly}")
    print(f"   - Post-Assembly Validation: {config.validate_after_assembly}")
    print(f"   - Quality Report: {config.generate_quality_report}")
    
    # Assemble template
    output_path = "demo_qme_report_basic.docx"
    
    print(f"\n🚀 Assembling professional template...")
    print(f"   Output: {output_path}")
    
    try:
        result = assembler.assemble_professional_template(
            template_data=template_data,
            output_path=output_path,
            doctor_info=doctor_info,
            assembly_config=config
        )
        
        print(f"\n✅ Template assembly completed successfully!")
        print(f"   File: {result.file_path}")
        print(f"   Size: {result.file_size_bytes / 1024:.1f} KB")
        print(f"   Pages: {result.page_count}")
        print(f"   Words: {result.word_count}")
        
        # Display validation results
        print(f"\n🔍 Validation Results:")
        
        pre_val = result.pre_assembly_validation
        print(f"   Pre-Assembly:")
        print(f"     - Valid: {pre_val.is_valid}")
        print(f"     - Quality Score: {pre_val.quality_score.overall_score:.1f}/100")
        print(f"     - Issues: {len(pre_val.validation_issues)}")
        print(f"     - Status: {pre_val.compliance_status}")
        
        post_val = result.post_assembly_validation
        print(f"   Post-Assembly:")
        print(f"     - Valid: {post_val.is_valid}")
        print(f"     - Quality Score: {post_val.quality_score.overall_score:.1f}/100")
        print(f"     - Placeholders: {post_val.placeholder_count}")
        print(f"     - Status: {post_val.compliance_status}")
        
        if result.quality_report_path:
            print(f"   Quality Report: {result.quality_report_path}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during template assembly: {str(e)}")
        logger.error(f"Template assembly error: {e}")
        return None


def demonstrate_draft_mode_assembly():
    """Demonstrate template assembly with quality indicators (draft mode)."""
    print("\n" + "="*60)
    print("📝 DRAFT MODE ASSEMBLY DEMONSTRATION")
    print("="*60)
    
    # Create assembler
    assembler = ProfessionalTemplateAssembler()
    
    # Create sample data with some missing information
    template_data = create_comprehensive_sample_data()
    
    # Simulate missing information for draft mode
    template_data.patient_info.age = None
    template_data.medical_findings.diagnoses = template_data.medical_findings.diagnoses[:1]  # Only one diagnosis
    template_data.missing_sections.extend(["Past Medical History", "Occupational History"])
    
    doctor_info = create_doctor_information()
    
    # Draft mode configuration
    config = TemplateAssemblyConfig(
        include_quality_indicators=True,  # Show quality indicators
        include_missing_placeholders=True,
        apply_professional_formatting=True,
        validate_before_assembly=True,
        validate_after_assembly=True,
        generate_quality_report=True,
        template_version="1.0-DRAFT"
    )
    
    print(f"\n📋 Draft Mode Features:")
    print(f"   - Quality indicators section included")
    print(f"   - Missing information highlighted")
    print(f"   - Comprehensive validation enabled")
    print(f"   - Template version: {config.template_version}")
    
    # Assemble draft template
    output_path = "demo_qme_report_draft.docx"
    
    print(f"\n🚀 Assembling draft template...")
    
    try:
        result = assembler.assemble_professional_template(
            template_data=template_data,
            output_path=output_path,
            doctor_info=doctor_info,
            assembly_config=config
        )
        
        print(f"\n✅ Draft template assembly completed!")
        print(f"   File: {result.file_path}")
        
        # Show validation issues
        all_issues = (result.pre_assembly_validation.validation_issues + 
                     result.post_assembly_validation.validation_issues)
        
        if all_issues:
            print(f"\n⚠️  Validation Issues Found ({len(all_issues)} total):")
            
            # Group by severity
            from src.core.validation.qme_rules_engine import ValidationSeverity
            
            critical = [i for i in all_issues if i.severity == ValidationSeverity.CRITICAL]
            high = [i for i in all_issues if i.severity == ValidationSeverity.HIGH]
            medium = [i for i in all_issues if i.severity == ValidationSeverity.MEDIUM]
            
            if critical:
                print(f"   🚨 Critical ({len(critical)}):")
                for issue in critical[:3]:  # Show top 3
                    print(f"      - {issue.title}")
            
            if high:
                print(f"   ⚠️  High ({len(high)}):")
                for issue in high[:3]:  # Show top 3
                    print(f"      - {issue.title}")
            
            if medium:
                print(f"   📝 Medium ({len(medium)}):")
                for issue in medium[:2]:  # Show top 2
                    print(f"      - {issue.title}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during draft assembly: {str(e)}")
        return None


def demonstrate_download_package():
    """Demonstrate creating a complete download package."""
    print("\n" + "="*60)
    print("📦 DOWNLOAD PACKAGE DEMONSTRATION")
    print("="*60)
    
    # First create a template
    assembler = ProfessionalTemplateAssembler()
    template_data = create_comprehensive_sample_data()
    doctor_info = create_doctor_information()
    
    config = TemplateAssemblyConfig(
        generate_quality_report=True,
        template_version="1.0-FINAL"
    )
    
    print(f"🚀 Creating template for package...")
    
    try:
        result = assembler.assemble_professional_template(
            template_data=template_data,
            output_path="demo_package_template.docx",
            doctor_info=doctor_info,
            assembly_config=config
        )
        
        print(f"✅ Template created successfully")
        
        # Create download package
        print(f"\n📦 Creating download package...")
        
        package_dir = assembler.generate_download_package(
            result=result,
            include_quality_report=True,
            include_validation_summary=True
        )
        
        print(f"✅ Download package created: {package_dir}")
        
        # List package contents
        package_files = os.listdir(package_dir)
        print(f"\n📋 Package Contents ({len(package_files)} files):")
        for file in sorted(package_files):
            file_path = os.path.join(package_dir, file)
            size = os.path.getsize(file_path)
            print(f"   - {file} ({size:,} bytes)")
        
        return package_dir
        
    except Exception as e:
        print(f"❌ Error creating download package: {str(e)}")
        return None


def demonstrate_validation_analysis():
    """Demonstrate detailed validation analysis."""
    print("\n" + "="*60)
    print("🔍 VALIDATION ANALYSIS DEMONSTRATION")
    print("="*60)
    
    # Create template with various issues for analysis
    assembler = ProfessionalTemplateAssembler()
    
    # Create problematic data
    template_data = create_comprehensive_sample_data()
    
    # Introduce issues
    template_data.patient_info.name = ""  # Missing name
    template_data.patient_info.case_number = ""  # Missing case number
    template_data.medical_findings.impairment_ratings = []  # No impairment ratings
    
    config = TemplateAssemblyConfig(
        validate_before_assembly=True,
        validate_after_assembly=True,
        generate_quality_report=True
    )
    
    print(f"🔍 Running validation analysis on problematic data...")
    
    try:
        result = assembler.assemble_professional_template(
            template_data=template_data,
            output_path="demo_validation_analysis.docx",
            assembly_config=config
        )
        
        print(f"\n📊 Validation Analysis Results:")
        
        # Pre-assembly analysis
        pre_val = result.pre_assembly_validation
        print(f"\n📋 Pre-Assembly Analysis:")
        print(f"   Overall Score: {pre_val.quality_score.overall_score:.1f}/100")
        print(f"   Completeness: {pre_val.quality_score.completeness_score:.1f}/100")
        print(f"   Accuracy: {pre_val.quality_score.accuracy_score:.1f}/100")
        print(f"   Compliance: {pre_val.quality_score.compliance_score:.1f}/100")
        
        print(f"\n   Issue Breakdown:")
        print(f"   - Critical: {pre_val.quality_score.critical_issues}")
        print(f"   - High: {pre_val.quality_score.high_issues}")
        print(f"   - Medium: {pre_val.quality_score.medium_issues}")
        print(f"   - Low: {pre_val.quality_score.low_issues}")
        
        # Show specific issues
        if pre_val.validation_issues:
            print(f"\n   Top Issues:")
            for i, issue in enumerate(pre_val.validation_issues[:5], 1):
                print(f"   {i}. [{issue.severity.value.upper()}] {issue.title}")
                print(f"      {issue.description}")
                if issue.suggestions:
                    print(f"      Suggestion: {issue.suggestions[0]}")
        
        # Post-assembly analysis
        post_val = result.post_assembly_validation
        print(f"\n📄 Post-Assembly Analysis:")
        print(f"   Document Quality: {post_val.quality_score.overall_score:.1f}/100")
        print(f"   Placeholders Remaining: {post_val.placeholder_count}")
        print(f"   Compliance Status: {post_val.compliance_status.upper()}")
        
        # Overall assessment
        overall_score = (pre_val.quality_score.overall_score + post_val.quality_score.overall_score) / 2
        
        print(f"\n🎯 Overall Assessment:")
        print(f"   Combined Score: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            assessment = "EXCELLENT - Ready for submission"
        elif overall_score >= 80:
            assessment = "GOOD - Minor improvements recommended"
        elif overall_score >= 70:
            assessment = "ACCEPTABLE - Review recommended"
        else:
            assessment = "NEEDS IMPROVEMENT - Significant issues to address"
        
        print(f"   Assessment: {assessment}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during validation analysis: {str(e)}")
        return None


def main():
    """Main demonstration function."""
    print("🏥 PROFESSIONAL QME TEMPLATE ASSEMBLER DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases the Professional Template Assembly System with")
    print("gold standard compliance, comprehensive validation, and quality assurance.")
    print("=" * 80)
    
    # Run demonstrations
    demos = [
        ("Basic Assembly", demonstrate_basic_assembly),
        ("Draft Mode Assembly", demonstrate_draft_mode_assembly),
        ("Download Package", demonstrate_download_package),
        ("Validation Analysis", demonstrate_validation_analysis)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        print(f"\n🎯 Running {demo_name} demonstration...")
        try:
            result = demo_func()
            results[demo_name] = result
            print(f"✅ {demo_name} completed successfully")
        except Exception as e:
            print(f"❌ {demo_name} failed: {str(e)}")
            results[demo_name] = None
    
    # Summary
    print("\n" + "="*60)
    print("📊 DEMONSTRATION SUMMARY")
    print("="*60)
    
    successful = sum(1 for result in results.values() if result is not None)
    total = len(results)
    
    print(f"Demonstrations completed: {successful}/{total}")
    
    for demo_name, result in results.items():
        status = "✅ SUCCESS" if result is not None else "❌ FAILED"
        print(f"   {demo_name}: {status}")
    
    # List generated files
    generated_files = [
        "demo_qme_report_basic.docx",
        "demo_qme_report_draft.docx", 
        "demo_package_template.docx",
        "demo_validation_analysis.docx"
    ]
    
    existing_files = [f for f in generated_files if os.path.exists(f)]
    
    if existing_files:
        print(f"\n📁 Generated Files ({len(existing_files)}):")
        for file in existing_files:
            size = os.path.getsize(file)
            print(f"   - {file} ({size:,} bytes)")
    
    print(f"\n🎉 Professional Template Assembler demonstration completed!")
    print(f"   Check the generated files to see the results.")


if __name__ == "__main__":
    main()