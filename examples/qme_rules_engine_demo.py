"""
QME Rules Engine Demonstration.

This script demonstrates the QME Rules Engine functionality using sample patient documents
and shows how it validates against the gold standard template requirements.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.core.validation.qme_rules_engine import (
        QMERulesEngine, ValidationIssue, QualityScore, ValidationSeverity, SectionType
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.core.generation.enhanced_qme_generator import EnhancedQMETemplateGenerator, EnhancedQMEResult
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.config.qme_gold_standard_config import qme_config
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_sample_patient_data() -> Dict[str, QMETemplateData]:
    """Create sample patient data based on the injured worker documents."""
    
    # Sample Patient 1: Based on Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf
    patient_1_info = PatientInfo(
        name="John Anderson",
        age=45,
        gender="Male",
        case_number="CL-09.09.2025-AA",
        medical_record_number="MRN-2025-001",
        injury_date=datetime(2025, 9, 5),
        body_parts=["Lower back", "Lumbar spine"],
        occupation="Construction Worker",
        employer="ABC Construction Company"
    )
    
    patient_1_diagnosis = Diagnosis(
        id="diag-001",
        icd_code="M54.5",
        description="Low back pain, unspecified",
        severity="moderate",
        certainty=0.85,
        source_section_id="exam-001"
    )
    
    patient_1_findings = [
        Finding(
            id="find-001",
            section_id="exam-001",
            finding_type="clinical",
            description="Reduced range of motion in lumbar spine with flexion limited to 45 degrees",
            page_reference=3
        ),
        Finding(
            id="find-002", 
            section_id="exam-001",
            finding_type="clinical",
            description="Positive straight leg raise test at 30 degrees bilaterally",
            page_reference=3
        ),
        Finding(
            id="find-003",
            section_id="exam-001", 
            finding_type="clinical",
            description="Muscle spasm in paraspinal muscles L3-L5 region",
            page_reference=3
        )
    ]
    
    patient_1_impairment = ImpairmentRating(
        id="imp-001",
        diagnosis_id="diag-001",
        percentage=15.0,
        ama_table="15-3",
        rationale="Range of motion method per AMA Guides 5th Edition",
        source_page=5
    )
    
    patient_1_medical_findings = MedicalFindings(
        diagnoses=[patient_1_diagnosis],
        findings=patient_1_findings,
        impairment_ratings=[patient_1_impairment],
        imaging_studies=["MRI lumbar spine showing disc bulge at L4-L5"],
        treatment_history=["Physical therapy", "Chiropractic treatment", "NSAIDs"]
    )
    
    patient_1_template = QMETemplateData(
        patient_info=patient_1_info,
        medical_findings=patient_1_medical_findings,
        ama_guidelines=["Chapter 15 - The Spine", "Table 15-3 - Lumbar Range of Motion"],
        generated_at=datetime.now()
    )
    
    # Sample Patient 2: Based on Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf
    patient_2_info = PatientInfo(
        name="David Adams", 
        age=38,
        gender="Male",
        case_number="CL-09.09.2025-DA",
        medical_record_number="MRN-2025-002",
        injury_date=datetime(2025, 9, 8),
        body_parts=["Right shoulder", "Rotator cuff"],
        occupation="Warehouse Worker",
        employer="XYZ Logistics"
    )
    
    patient_2_diagnosis = Diagnosis(
        id="diag-002",
        icd_code="M75.3",
        description="Calcific tendinitis of shoulder",
        severity="moderate",
        certainty=0.90,
        source_section_id="exam-002"
    )
    
    patient_2_findings = [
        Finding(
            id="find-004",
            section_id="exam-002",
            finding_type="clinical", 
            description="Limited shoulder abduction to 90 degrees",
            page_reference=4
        ),
        Finding(
            id="find-005",
            section_id="exam-002",
            finding_type="clinical",
            description="Positive impingement signs with Hawkins and Neer tests",
            page_reference=4
        )
    ]
    
    # Incomplete data to demonstrate validation issues
    patient_2_medical_findings = MedicalFindings(
        diagnoses=[patient_2_diagnosis],
        findings=patient_2_findings,
        impairment_ratings=[],  # Missing impairment rating
        imaging_studies=["X-ray right shoulder showing calcific deposits"],
        treatment_history=["Cortisone injection", "Physical therapy"]
    )
    
    patient_2_template = QMETemplateData(
        patient_info=patient_2_info,
        medical_findings=patient_2_medical_findings,
        ama_guidelines=["Chapter 16 - The Upper Extremities"],
        generated_at=datetime.now()
    )
    
    return {
        "patient_1_complete": patient_1_template,
        "patient_2_incomplete": patient_2_template
    }


def demonstrate_rules_engine_validation():
    """Demonstrate the QME Rules Engine validation capabilities."""
    
    print("🏥 QME Rules Engine Demonstration")
    print("=" * 60)
    print()
    
    # Initialize rules engine
    print("📋 Initializing QME Rules Engine...")
    rules_engine = QMERulesEngine()
    print("✅ Rules Engine initialized successfully")
    print()
    
    # Create sample patient data
    print("👥 Creating sample patient data...")
    sample_patients = create_sample_patient_data()
    print(f"✅ Created {len(sample_patients)} sample patient records")
    print()
    
    # Validate each patient
    for patient_name, template_data in sample_patients.items():
        print(f"🔍 Validating {patient_name.replace('_', ' ').title()}...")
        print("-" * 40)
        
        # Perform validation
        issues, quality_score = rules_engine.validate_qme_report(template_data)
        
        # Display patient information
        print(f"Patient: {template_data.patient_info.name}")
        print(f"Case: {template_data.patient_info.case_number}")
        print(f"Injury Date: {template_data.patient_info.injury_date.strftime('%m/%d/%Y') if template_data.patient_info.injury_date else 'Not specified'}")
        print()
        
        # Display quality scores
        print("📊 Quality Assessment:")
        print(f"  Overall Score: {quality_score.overall_score:.1f}/100")
        print(f"  Completeness: {quality_score.completeness_score:.1f}/100")
        print(f"  Accuracy: {quality_score.accuracy_score:.1f}/100") 
        print(f"  Compliance: {quality_score.compliance_score:.1f}/100")
        print()
        
        # Display issue summary
        print(f"🚨 Issues Found: {quality_score.total_issues} total")
        if quality_score.critical_issues > 0:
            print(f"  ❌ Critical: {quality_score.critical_issues}")
        if quality_score.high_issues > 0:
            print(f"  ⚠️  High: {quality_score.high_issues}")
        if quality_score.medium_issues > 0:
            print(f"  ⚡ Medium: {quality_score.medium_issues}")
        if quality_score.low_issues > 0:
            print(f"  ℹ️  Low: {quality_score.low_issues}")
        print()
        
        # Display top issues
        if issues:
            print("🔍 Top Issues:")
            critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
            high_issues = [issue for issue in issues if issue.severity == ValidationSeverity.HIGH]
            
            # Show critical issues first
            for issue in critical_issues[:3]:
                print(f"  ❌ CRITICAL: {issue.title}")
                print(f"     {issue.description}")
                if issue.suggestions:
                    print(f"     💡 Suggestion: {issue.suggestions[0]}")
                print()
            
            # Show high priority issues
            for issue in high_issues[:2]:
                print(f"  ⚠️  HIGH: {issue.title}")
                print(f"     {issue.description}")
                if issue.suggestions:
                    print(f"     💡 Suggestion: {issue.suggestions[0]}")
                print()
        
        # Display improvement suggestions
        suggestions = rules_engine.get_improvement_suggestions(issues)
        if suggestions:
            print("💡 Improvement Recommendations:")
            for section, section_suggestions in list(suggestions.items())[:3]:
                print(f"  📋 {section.value.replace('_', ' ').title()}:")
                for suggestion in section_suggestions[:2]:
                    print(f"     • {suggestion}")
                print()
        
        print("=" * 60)
        print()


def demonstrate_enhanced_generator():
    """Demonstrate the Enhanced QME Generator with rules engine integration."""
    
    print("🚀 Enhanced QME Generator Demonstration")
    print("=" * 60)
    print()
    
    try:
        # Initialize enhanced generator
        print("🔧 Initializing Enhanced QME Generator...")
        enhanced_generator = EnhancedQMETemplateGenerator()
        print("✅ Enhanced Generator initialized successfully")
        print()
        
        # Create sample data for demonstration
        sample_patients = create_sample_patient_data()
        complete_patient = sample_patients["patient_1_complete"]
        
        print("📝 Demonstrating template generation process...")
        print(f"Patient: {complete_patient.patient_info.name}")
        print(f"Case: {complete_patient.patient_info.case_number}")
        print()
        
        # Simulate enhanced generation (without actual file creation)
        print("🔍 Performing quality validation...")
        rules_engine = QMERulesEngine()
        issues, quality_score = rules_engine.validate_qme_report(complete_patient)
        
        print("📊 Quality Assessment Results:")
        print(f"  Overall Quality: {quality_score.overall_score:.1f}/100")
        print(f"  Issues Found: {len(issues)}")
        print()
        
        # Generate quality summary
        from src.core.generation.enhanced_qme_generator import EnhancedQMEResult
        
        mock_result = EnhancedQMEResult(
            file_path="sample_qme_report.docx",
            template_data=complete_patient,
            validation_issues=issues,
            quality_score=quality_score,
            quality_report=rules_engine.generate_quality_report(issues, quality_score),
            improvement_suggestions=rules_engine.get_improvement_suggestions(issues)
        )
        
        quality_summary = enhanced_generator.generate_quality_summary_report(mock_result)
        
        print("📋 Quality Summary Report:")
        print("-" * 40)
        print(quality_summary)
        print()
        
    except Exception as e:
        print(f"❌ Error in enhanced generator demonstration: {e}")
        logger.error(f"Enhanced generator demo error: {e}")


def demonstrate_gold_standard_compliance():
    """Demonstrate compliance checking against gold standard requirements."""
    
    print("🏆 Gold Standard Compliance Demonstration")
    print("=" * 60)
    print()
    
    print("📋 Gold Standard Requirements:")
    print(f"  Required Sections: {len(qme_config.REQUIRED_SECTIONS)}")
    print("  Key Sections:")
    for section in qme_config.REQUIRED_SECTIONS[:8]:
        print(f"    • {section.replace('_', ' ').title()}")
    print("    • ... and more")
    print()
    
    print("👤 Patient Identification Requirements:")
    required_fields = qme_config.PATIENT_ID_REQUIREMENTS["required_fields"]
    print(f"  Required Fields: {len(required_fields)}")
    for field in required_fields[:6]:
        print(f"    • {field.replace('_', ' ').title()}")
    print("    • ... and more")
    print()
    
    print("🏥 Physical Examination Requirements:")
    exam_reqs = qme_config.EXAMINATION_REQUIREMENTS
    print("  Musculoskeletal Assessment:")
    for measurement in exam_reqs["musculoskeletal"]["required_measurements"][:4]:
        print(f"    • {measurement.replace('_', ' ').title()}")
    print()
    
    print("📊 Impairment Rating Requirements:")
    imp_reqs = qme_config.IMPAIRMENT_REQUIREMENTS
    print("  Required Elements:")
    for element in imp_reqs["methodology"]["required_elements"]:
        print(f"    • {element.replace('_', ' ').title()}")
    print()
    
    print("📝 Formatting Standards:")
    format_reqs = qme_config.FORMATTING_REQUIREMENTS
    typography = format_reqs["typography"]
    print(f"  Font: {typography['font_family']}")
    print(f"  Size: {typography['font_size']} pt")
    print(f"  Line Spacing: {typography['line_spacing']}")
    print()


def main():
    """Main demonstration function."""
    
    print("🏥 QME Rules Engine & Enhanced Generator Demo")
    print("=" * 70)
    print()
    print("This demonstration shows how the QME Rules Engine validates")
    print("QME reports against the gold standard template and provides")
    print("quality assessment and improvement recommendations.")
    print()
    
    try:
        # Demonstrate rules engine validation
        demonstrate_rules_engine_validation()
        
        # Demonstrate enhanced generator
        demonstrate_enhanced_generator()
        
        # Demonstrate gold standard compliance
        demonstrate_gold_standard_compliance()
        
        print("✅ Demonstration completed successfully!")
        print()
        print("🎯 Key Features Demonstrated:")
        print("  • Comprehensive quality validation")
        print("  • AMA Guidelines compliance checking")
        print("  • Legal requirement validation")
        print("  • Gold standard template compliance")
        print("  • Automated improvement suggestions")
        print("  • Professional report generation")
        print()
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.error(f"Demo error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)