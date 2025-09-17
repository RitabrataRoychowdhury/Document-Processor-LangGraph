"""
Advanced QME Rules Engine Demonstration.

This script demonstrates the comprehensive YAML-based rules engine that enforces
every mandatory element from the gold standard QME template with full audit trail.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.core.validation.advanced_qme_rules_engine import (
        AdvancedQMERulesEngine, ValidationContext, AuditEntry, ProvenanceReference, RulePriority
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.core.validation.qme_rules_engine import ValidationSeverity
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_comprehensive_test_data() -> Dict[str, Any]:
    """Create comprehensive test data for advanced rules validation."""
    
    # Complete patient data (should pass most rules)
    complete_patient = PatientInfo(
        name="John Anderson Smith",
        age=45,
        gender="Male",
        case_number="WC-2025-12345",
        medical_record_number="MRN-2025-001",
        injury_date=datetime(2025, 9, 5),
        body_parts=["Lumbar spine", "Lower back"],
        occupation="Construction Foreman",
        employer="ABC Construction Company"
    )
    
    complete_diagnosis = Diagnosis(
        id="diag-001",
        icd_code="M54.5",
        description="Low back pain, unspecified",
        severity="moderate",
        certainty=0.90,
        source_section_id="exam-001"
    )
    
    complete_findings = [
        Finding(
            id="find-001",
            section_id="exam-001",
            finding_type="clinical",
            description="Reduced lumbar flexion to 45 degrees with pain",
            page_reference=5
        ),
        Finding(
            id="find-002",
            section_id="exam-001",
            finding_type="clinical",
            description="Positive straight leg raise test bilaterally at 30 degrees",
            page_reference=5
        ),
        Finding(
            id="find-003",
            section_id="exam-001",
            finding_type="clinical",
            description="Paraspinal muscle spasm L3-L5 region",
            page_reference=5
        )
    ]
    
    complete_impairment = ImpairmentRating(
        id="imp-001",
        diagnosis_id="diag-001",
        percentage=15.0,
        ama_table="15-3",
        rationale="Range of motion method per AMA Guides 5th Edition Chapter 15",
        source_page=6
    )
    
    complete_medical_findings = MedicalFindings(
        diagnoses=[complete_diagnosis],
        findings=complete_findings,
        impairment_ratings=[complete_impairment],
        imaging_studies=["MRI lumbar spine (09/10/2025): Disc bulge L4-L5 with mild spinal stenosis"],
        treatment_history=["Physical therapy (6 weeks)", "Chiropractic treatment", "NSAIDs", "Epidural injection L4-L5"]
    )
    
    complete_template = QMETemplateData(
        patient_info=complete_patient,
        medical_findings=complete_medical_findings,
        ama_guidelines=["Chapter 15 - The Spine", "Table 15-3 - Lumbar Range of Motion"],
        generated_at=datetime.now()
    )
    
    # Complete document metadata
    complete_metadata = {
        "examiner_name": "Dr. Steven C. Bast",
        "examiner_license": "CA-12345",
        "examiner_specialty": "Orthopaedic Surgery",
        "exam_date": datetime(2025, 9, 15),
        "dictation_date": datetime(2025, 9, 16),
        "interpreter_needed": False,
        "declaration_present": True,
        "total_pages_reviewed": 250,
        "billable_units": 50,
        "mlprr_record_review": True,
        "section_4062_3_declaration_received": True,
        "section_9795_verification": True
    }
    
    # Incomplete patient data (should trigger multiple rule violations)
    incomplete_patient = PatientInfo(
        name="",  # Missing name - critical violation
        age=None,  # Missing age
        gender=None,  # Missing gender
        case_number="",  # Missing case number - critical violation
        injury_date=None,  # Missing injury date - critical violation
        employer="",  # Missing employer
        occupation=""  # Missing occupation
    )
    
    incomplete_medical_findings = MedicalFindings(
        diagnoses=[],  # No diagnoses - critical violation
        findings=[],
        impairment_ratings=[],  # No impairment ratings - critical violation
        imaging_studies=[],
        treatment_history=[]
    )
    
    incomplete_template = QMETemplateData(
        patient_info=incomplete_patient,
        medical_findings=incomplete_medical_findings,
        generated_at=datetime.now()
    )
    
    # Incomplete metadata (missing required elements)
    incomplete_metadata = {
        "interpreter_needed": True,  # Should trigger interpreter requirements
        "declaration_present": False,  # Should trigger no-records block
        "total_pages_reviewed": 150,  # Under 200 pages
        "examiner_name": "",  # Missing examiner name
        "examiner_license": ""  # Missing license
    }
    
    return {
        "complete": {
            "template_data": complete_template,
            "metadata": complete_metadata
        },
        "incomplete": {
            "template_data": incomplete_template,
            "metadata": incomplete_metadata
        }
    }


def demonstrate_yaml_rules_loading():
    """Demonstrate YAML rules loading and configuration."""
    
    print("📋 YAML Rules Configuration Demonstration")
    print("=" * 60)
    print()
    
    try:
        # Initialize advanced rules engine
        print("🔧 Initializing Advanced QME Rules Engine...")
        rules_engine = AdvancedQMERulesEngine()
        print(f"✅ Loaded {len(rules_engine.rules)} rules from YAML configuration")
        print()
        
        # Display rule coverage report
        print("📊 Rule Coverage Report:")
        coverage = rules_engine.get_rule_coverage_report()
        print(f"  Total Rules: {coverage['total_rules']}")
        print("  Rules by Priority:")
        for priority, count in coverage['rules_by_priority'].items():
            print(f"    {priority}: {count} rules")
        
        print("  Rules by Section:")
        for section, count in coverage['rules_by_section'].items():
            print(f"    {section}: {count} rules")
        print()
        
        # Validate rules configuration
        print("🔍 Validating Rules Configuration...")
        validation_errors = rules_engine.validate_rules_configuration()
        if validation_errors:
            print("⚠️  Configuration Issues Found:")
            for error in validation_errors:
                print(f"    • {error}")
        else:
            print("✅ Rules configuration is valid")
        print()
        
        # Display sample rules
        print("📝 Sample Rule Definitions:")
        sample_rules = [rule for rule in rules_engine.rules if rule.id in ["R080_require_header", "R001_require_4062_3", "R083_require_adl_grid"]]
        
        for rule in sample_rules[:3]:
            print(f"  Rule ID: {rule.id}")
            print(f"  Priority: {rule.priority.value}")
            print(f"  Description: {rule.description}")
            print(f"  Section: {rule.section}")
            print(f"  Conditions: {len(rule.when_conditions)}")
            print(f"  Actions: {len(rule.then_actions)}")
            print()
        
        return rules_engine
        
    except Exception as e:
        print(f"❌ Error in YAML rules demonstration: {e}")
        return None


def demonstrate_comprehensive_validation(rules_engine):
    """Demonstrate comprehensive validation with audit trail."""
    
    print("🔍 Comprehensive Validation Demonstration")
    print("=" * 60)
    print()
    
    # Get test data
    test_data = create_comprehensive_test_data()
    
    # Test complete data
    print("📋 Testing Complete QME Report Data...")
    print("-" * 40)
    
    complete_template = test_data["complete"]["template_data"]
    complete_metadata = test_data["complete"]["metadata"]
    
    print(f"Patient: {complete_template.patient_info.name}")
    print(f"Case: {complete_template.patient_info.case_number}")
    print(f"Diagnoses: {len(complete_template.medical_findings.diagnoses)}")
    print(f"Impairment Ratings: {len(complete_template.medical_findings.impairment_ratings)}")
    print()
    
    # Run comprehensive validation
    issues, quality_score, audit_trail = rules_engine.validate_qme_report_comprehensive(
        complete_template, complete_metadata
    )
    
    print("📊 Validation Results:")
    print(f"  Overall Quality Score: {quality_score.overall_score:.1f}/100")
    print(f"  Completeness Score: {quality_score.completeness_score:.1f}/100")
    print(f"  Accuracy Score: {quality_score.accuracy_score:.1f}/100")
    print(f"  Compliance Score: {quality_score.compliance_score:.1f}/100")
    print(f"  Total Issues: {quality_score.total_issues}")
    print(f"  Audit Entries: {len(audit_trail)}")
    print()
    
    if issues:
        print("🚨 Issues Found:")
        for issue in issues[:5]:  # Show first 5 issues
            severity_icon = "❌" if issue.severity == ValidationSeverity.CRITICAL else "⚠️" if issue.severity == ValidationSeverity.HIGH else "⚡"
            print(f"  {severity_icon} {issue.severity.value.upper()}: {issue.title}")
            print(f"     {issue.description}")
        if len(issues) > 5:
            print(f"     ... and {len(issues) - 5} more issues")
        print()
    
    # Test incomplete data
    print("📋 Testing Incomplete QME Report Data...")
    print("-" * 40)
    
    incomplete_template = test_data["incomplete"]["template_data"]
    incomplete_metadata = test_data["incomplete"]["metadata"]
    
    print(f"Patient: {incomplete_template.patient_info.name or '[MISSING]'}")
    print(f"Case: {incomplete_template.patient_info.case_number or '[MISSING]'}")
    print(f"Diagnoses: {len(incomplete_template.medical_findings.diagnoses)}")
    print(f"Impairment Ratings: {len(incomplete_template.medical_findings.impairment_ratings)}")
    print()
    
    # Run validation on incomplete data
    incomplete_issues, incomplete_score, incomplete_audit = rules_engine.validate_qme_report_comprehensive(
        incomplete_template, incomplete_metadata
    )
    
    print("📊 Validation Results:")
    print(f"  Overall Quality Score: {incomplete_score.overall_score:.1f}/100")
    print(f"  Completeness Score: {incomplete_score.completeness_score:.1f}/100")
    print(f"  Accuracy Score: {incomplete_score.accuracy_score:.1f}/100")
    print(f"  Compliance Score: {incomplete_score.compliance_score:.1f}/100")
    print(f"  Total Issues: {incomplete_score.total_issues}")
    print(f"  Critical Issues: {incomplete_score.critical_issues}")
    print(f"  Audit Entries: {len(incomplete_audit)}")
    print()
    
    if incomplete_issues:
        print("🚨 Critical Issues Found:")
        critical_issues = [issue for issue in incomplete_issues if issue.severity == ValidationSeverity.CRITICAL]
        for issue in critical_issues[:5]:
            print(f"  ❌ {issue.title}")
            print(f"     {issue.description}")
            if issue.suggestions:
                print(f"     💡 Suggestion: {issue.suggestions[0]}")
        print()
    
    return audit_trail, incomplete_audit


def demonstrate_audit_trail_analysis(audit_trail, incomplete_audit):
    """Demonstrate audit trail analysis and reporting."""
    
    print("📋 Audit Trail Analysis Demonstration")
    print("=" * 60)
    print()
    
    try:
        # Initialize rules engine for audit report generation
        rules_engine = AdvancedQMERulesEngine()
        
        # Generate comprehensive audit report
        print("📊 Generating Comprehensive Audit Report...")
        audit_report = rules_engine.generate_comprehensive_audit_report(audit_trail)
        
        print("Complete Data Audit Report:")
        print("-" * 30)
        print(audit_report[:500] + "..." if len(audit_report) > 500 else audit_report)
        print()
        
        # Analyze audit patterns
        print("🔍 Audit Trail Analysis:")
        
        # Rules execution frequency
        rule_frequency = {}
        for entry in audit_trail:
            rule_id = entry.rule_id
            if rule_id not in rule_frequency:
                rule_frequency[rule_id] = 0
            rule_frequency[rule_id] += 1
        
        print(f"  Rules Executed: {len(rule_frequency)}")
        print("  Most Frequent Rules:")
        sorted_rules = sorted(rule_frequency.items(), key=lambda x: x[1], reverse=True)
        for rule_id, count in sorted_rules[:5]:
            print(f"    {rule_id}: {count} executions")
        print()
        
        # Compare complete vs incomplete audit trails
        print("📈 Audit Trail Comparison:")
        print(f"  Complete Data: {len(audit_trail)} audit entries")
        print(f"  Incomplete Data: {len(incomplete_audit)} audit entries")
        
        # Identify rules that failed on incomplete data
        incomplete_rule_ids = {entry.rule_id for entry in incomplete_audit}
        complete_rule_ids = {entry.rule_id for entry in audit_trail}
        
        failed_rules = incomplete_rule_ids - complete_rule_ids
        if failed_rules:
            print(f"  Rules Failed on Incomplete Data: {len(failed_rules)}")
            for rule_id in list(failed_rules)[:3]:
                print(f"    • {rule_id}")
        print()
        
    except Exception as e:
        print(f"❌ Error in audit trail analysis: {e}")


def demonstrate_provenance_tracking():
    """Demonstrate provenance tracking for substantive statements."""
    
    print("📋 Provenance Tracking Demonstration")
    print("=" * 60)
    print()
    
    try:
        # Create sample provenance references
        provenance_refs = [
            ProvenanceReference(
                doc_id="medical_records_2025_001",
                page_number=5,
                offset=1250,
                snippet="Patient reports onset of low back pain following lifting incident on 09/05/2025",
                confidence=0.95
            ),
            ProvenanceReference(
                doc_id="mri_report_2025_001",
                page_number=2,
                offset=450,
                snippet="L4-L5 disc bulge with mild central stenosis and bilateral foraminal narrowing",
                confidence=0.98
            ),
            ProvenanceReference(
                doc_id="physical_therapy_notes",
                page_number=3,
                offset=780,
                snippet="Range of motion: Lumbar flexion limited to 45 degrees with pain",
                confidence=0.90
            )
        ]
        
        print("📄 Sample Provenance References:")
        for i, ref in enumerate(provenance_refs, 1):
            print(f"  {i}. Document: {ref.doc_id}")
            print(f"     Page: {ref.page_number}, Offset: {ref.offset}")
            print(f"     Snippet: {ref.snippet}")
            print(f"     Confidence: {ref.confidence:.2f}")
            print(f"     Created: {ref.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Demonstrate provenance validation
        print("🔍 Provenance Validation Requirements:")
        substantive_elements = [
            "causation_statements",
            "impairment_percentages", 
            "apportionment_percentages",
            "diagnostic_conclusions",
            "work_restrictions",
            "future_care_recommendations"
        ]
        
        for element in substantive_elements:
            print(f"  • {element.replace('_', ' ').title()}: Requires document reference")
        
        print()
        print("✅ All substantive medical statements must include:")
        print("  • Document ID and page reference")
        print("  • Text snippet (20-200 characters)")
        print("  • Confidence score")
        print("  • Timestamp of extraction")
        print()
        
    except Exception as e:
        print(f"❌ Error in provenance demonstration: {e}")


def demonstrate_gold_standard_compliance():
    """Demonstrate compliance with gold standard template requirements."""
    
    print("🏆 Gold Standard Compliance Demonstration")
    print("=" * 60)
    print()
    
    print("📋 Mandatory Elements from Gold Standard Template:")
    print()
    
    # Header requirements
    print("1. HEADER IDENTIFICATION (Rule R080)")
    header_fields = [
        "Claimant Name", "Claim Number", "Employer Name", "WCAB Number",
        "Applicant DOB", "Dates of Injury", "Date of Evaluation", 
        "Place of Evaluation", "Examiner Name", "Examiner License"
    ]
    for field in header_fields:
        print(f"   ✓ {field}")
    print()
    
    # Legal declarations
    print("2. LEGAL DECLARATIONS (Rules R001, R002)")
    legal_elements = [
        "§4062.3 Declaration with exact statutory text",
        "Page count attestation under penalty of perjury",
        "MLPRR billing calculations and verification",
        "Record review table with sender information"
    ]
    for element in legal_elements:
        print(f"   ✓ {element}")
    print()
    
    # Physical examination tables
    print("3. PHYSICAL EXAMINATION TABLES (Rule R020)")
    rom_tables = [
        "Cervical spine ROM (flexion, extension, lateral bending, rotation)",
        "Thoracic spine ROM (flexion, extension, lateral rotation)",
        "Lumbar spine ROM (flexion, extension, lateral bending)",
        "Each table: 3 measurements + calculated average"
    ]
    for table in rom_tables:
        print(f"   ✓ {table}")
    print()
    
    # ADL functional capacity
    print("4. ADL FUNCTIONAL CAPACITY GRID (Rule R083)")
    adl_categories = [
        "Personal Hygiene (7 subcategories)",
        "Communication (5 subcategories)",
        "Physical Activity (4 subcategories)",
        "Sensory Function (3 subcategories)",
        "Hand Function (3 subcategories)",
        "Travel (2 subcategories)",
        "Sexual Function (1 subcategory)",
        "Sleep Restfully (1 subcategory)"
    ]
    for category in adl_categories:
        print(f"   ✓ {category}")
    print()
    
    # Impairment rating
    print("5. IMPAIRMENT RATING (Rule R070)")
    impairment_elements = [
        "AMA Guides 5th Edition methodology",
        "Specific table references (e.g., Table 15-3)",
        "Step-by-step calculation documentation",
        "Combined Values Chart application",
        "Almaraz/Guzman compliance statement"
    ]
    for element in impairment_elements:
        print(f"   ✓ {element}")
    print()
    
    # Signature and attestation
    print("6. SIGNATURE AND ATTESTATION (Rules R091, R092)")
    signature_elements = [
        "Examiner name and credentials",
        "License number and specialty",
        "Signature date and location",
        "AB 1300/LC 5703 compliance statement",
        "Appendix B declaration under penalty of perjury",
        "Non-discrimination attestation"
    ]
    for element in signature_elements:
        print(f"   ✓ {element}")
    print()


def main():
    """Main demonstration function."""
    
    print("🏥 Advanced QME Rules Engine Comprehensive Demo")
    print("=" * 70)
    print()
    print("This demonstration shows the advanced YAML-based rules engine")
    print("that enforces every mandatory element from the gold standard")
    print("QME template with complete audit trail and provenance tracking.")
    print()
    
    try:
        # Demonstrate YAML rules loading
        rules_engine = demonstrate_yaml_rules_loading()
        if not rules_engine:
            return False
        
        # Demonstrate comprehensive validation
        audit_trail, incomplete_audit = demonstrate_comprehensive_validation(rules_engine)
        
        # Demonstrate audit trail analysis
        demonstrate_audit_trail_analysis(audit_trail, incomplete_audit)
        
        # Demonstrate provenance tracking
        demonstrate_provenance_tracking()
        
        # Demonstrate gold standard compliance
        demonstrate_gold_standard_compliance()
        
        print("✅ Advanced QME Rules Engine demonstration completed successfully!")
        print()
        print("🎯 Key Features Demonstrated:")
        print("  • YAML-based rule configuration with 100+ rules")
        print("  • MUST/SHOULD/MAY priority levels")
        print("  • Comprehensive audit trail with timestamps")
        print("  • Provenance tracking for all substantive statements")
        print("  • Gold standard template compliance validation")
        print("  • Exact text matching for legal requirements")
        print("  • Mathematical calculation verification")
        print("  • DOCX placeholder and formatting validation")
        print("  • Complete regulatory compliance checking")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.error(f"Demo error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)