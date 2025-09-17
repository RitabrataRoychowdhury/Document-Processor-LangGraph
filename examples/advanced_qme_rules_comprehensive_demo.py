#!/usr/bin/env python3
"""
Comprehensive demonstration of the Advanced QME Rules Engine with Legal Compliance.

This script demonstrates the enhanced YAML-configured rules engine with:
- Comprehensive legal compliance validation
- MUST/SHOULD/MAY priority levels
- Audit trail with provenance tracking
- Enhanced quality scoring
- Legal requirement enforcement
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.core.validation.advanced_qme_rules_engine import AdvancedQMERulesEngine, ProvenanceReference
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Finding, Diagnosis
    from src.utils.logging_config import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)


def create_sample_qme_data() -> QMETemplateData:
    """Create comprehensive sample QME data for demonstration."""
    
    # Patient information
    patient_info = PatientInfo(
        name="Maria Rodriguez",
        age=42,
        gender="Female",
        case_number="WC2024-001234",
        employer="Construction Company ABC",
        injury_date=datetime(2023, 6, 15),
        occupation="Construction Worker"
    )
    
    # Medical findings
    findings = [
        Finding(
            id="finding_1",
            section_id="physical_exam",
            finding_type="physical",
            description="Cervical spine tenderness with limited range of motion",
            page_reference=12
        ),
        Finding(
            id="finding_2", 
            section_id="imaging",
            finding_type="imaging",
            description="MRI shows disc herniation at C5-C6 level",
            page_reference=18
        ),
        Finding(
            id="finding_3",
            section_id="neurological",
            finding_type="neurological", 
            description="Positive Spurling's test bilaterally",
            page_reference=14
        )
    ]
    
    medical_findings = MedicalFindings(findings=findings)
    
    return QMETemplateData(
        patient_info=patient_info,
        medical_findings=medical_findings
    )


def create_comprehensive_metadata() -> Dict[str, Any]:
    """Create comprehensive document metadata for validation."""
    return {
        # Examiner information
        "examiner_name": "Dr. Sarah Johnson, MD",
        "examiner_license": "A12345",
        "examiner_specialty": "Orthopedic Surgery",
        
        # Legal compliance
        "declaration_present": True,
        "section_4062_3_compliant": True,
        "section_9795_verified": True,
        
        # MLPRR billing
        "total_pages_reviewed": 285,
        "billing_amount": 255.00,  # (285 - 200) * 3.00 = 255.00
        "page_count_attestation": 285,
        
        # Interpreter requirements
        "interpreter_needed": False,
        "interpreter_used": False,
        
        # Apportionment
        "industrial_percentage": 75.0,
        "nonindustrial_percentage": 25.0,
        "apportionment_required": True,
        
        # Causation
        "causation_found": True,
        "causation_type": "specific_injury",
        "medical_probability": "reasonable",
        
        # Validation state for simulation
        "completed_sections": [
            "header", "legal_declarations", "records_review", "identifying_data",
            "history_of_injury", "occupational_history", "activities_daily_living",
            "physical_examination", "diagnostic_impression", "causation_analysis",
            "impairment_rating", "apportionment", "work_restrictions", 
            "future_medical_care", "signature_block"
        ],
        "calculations_correct": True,
        "legal_requirements_met": True,
        "adl_grid_present": True,
        "adl_columns": ["Without Difficulty", "With Some Difficulty", "With Moderate Difficulty", "Unable To Do"],
        "adl_categories": ["Personal Hygiene", "Communication", "Physical Activity", "Sensory Function", 
                          "Hand Function", "Travel", "Sexual Function", "Sleep Restfully"],
        "ama_citations": ["Chapter 15", "Table 15-3", "Combined Values Chart"],
        "documented_methodologies": ["table_method", "rom_method", "combined_values_chart"]
    }


def create_problematic_metadata() -> Dict[str, Any]:
    """Create metadata with legal compliance issues for demonstration."""
    return {
        # Missing examiner information
        "examiner_name": None,
        "examiner_license": None,
        
        # Legal compliance issues
        "declaration_present": False,
        "section_4062_3_compliant": False,
        
        # MLPRR billing errors
        "total_pages_reviewed": 250,
        "billing_amount": 100.00,  # Incorrect: should be 150.00
        "page_count_attestation": None,
        
        # Interpreter issues
        "interpreter_needed": True,
        "interpreter_used": True,
        # Missing interpreter documentation
        
        # Apportionment errors
        "industrial_percentage": 60.0,
        "nonindustrial_percentage": 50.0,  # Error: sums to 110%
        
        # Missing causation
        "causation_found": False,
        "causation_type": None,
        
        # Incomplete validation state
        "completed_sections": ["header", "identifying_data"],  # Missing most sections
        "calculations_correct": False,
        "legal_requirements_met": False,
        "adl_grid_present": False
    }


def demonstrate_comprehensive_validation():
    """Demonstrate comprehensive QME validation with legal compliance."""
    
    print("=" * 80)
    print("ADVANCED QME RULES ENGINE - COMPREHENSIVE LEGAL COMPLIANCE DEMO")
    print("=" * 80)
    
    # Initialize the rules engine
    print("\n1. Initializing Advanced QME Rules Engine...")
    rules_engine = AdvancedQMERulesEngine()
    
    print(f"   ✓ Loaded {len(rules_engine.rules)} validation rules")
    
    # Get rule coverage report
    coverage = rules_engine.get_rule_coverage_report()
    print(f"   ✓ MUST rules: {coverage['rules_by_priority']['MUST']}")
    print(f"   ✓ SHOULD rules: {coverage['rules_by_priority']['SHOULD']}")
    print(f"   ✓ MAY rules: {coverage['rules_by_priority']['MAY']}")
    print(f"   ✓ Legal compliance rules: {coverage['legal_compliance_rules']}")
    
    # Validate rules configuration
    config_errors = rules_engine.validate_rules_configuration()
    if config_errors:
        print(f"   ⚠ Configuration issues: {len(config_errors)}")
        for error in config_errors[:3]:  # Show first 3 errors
            print(f"     - {error}")
    else:
        print("   ✓ Rules configuration is valid")
    
    # Create sample data
    print("\n2. Creating sample QME report data...")
    qme_data = create_sample_qme_data()
    print(f"   ✓ Patient: {qme_data.patient_info.name}")
    print(f"   ✓ Case: {qme_data.patient_info.case_number}")
    print(f"   ✓ Findings: {len(qme_data.medical_findings.findings)}")
    
    # Test with compliant metadata
    print("\n3. Testing with COMPLIANT metadata...")
    compliant_metadata = create_comprehensive_metadata()
    
    issues, quality_score, audit_trail = rules_engine.validate_qme_report_comprehensive(
        qme_data, compliant_metadata
    )
    
    print(f"   ✓ Validation issues found: {len(issues)}")
    print(f"   ✓ Overall quality score: {quality_score.overall_score:.1f}%")
    print(f"   ✓ Compliance score: {quality_score.compliance_score:.1f}%")
    print(f"   ✓ Audit trail entries: {len(audit_trail)}")
    
    # Show critical issues (if any)
    critical_issues = [issue for issue in issues if issue.severity.name == "CRITICAL"]
    if critical_issues:
        print(f"   ⚠ Critical issues: {len(critical_issues)}")
        for issue in critical_issues[:3]:
            print(f"     - {issue.title}")
    else:
        print("   ✓ No critical issues found")
    
    # Test with problematic metadata
    print("\n4. Testing with PROBLEMATIC metadata...")
    problematic_metadata = create_problematic_metadata()
    
    issues_prob, quality_score_prob, audit_trail_prob = rules_engine.validate_qme_report_comprehensive(
        qme_data, problematic_metadata
    )
    
    print(f"   ⚠ Validation issues found: {len(issues_prob)}")
    print(f"   ⚠ Overall quality score: {quality_score_prob.overall_score:.1f}%")
    print(f"   ⚠ Compliance score: {quality_score_prob.compliance_score:.1f}%")
    
    # Show critical legal compliance issues
    critical_issues_prob = [issue for issue in issues_prob if issue.severity.name == "CRITICAL"]
    print(f"   ⚠ Critical legal issues: {len(critical_issues_prob)}")
    for issue in critical_issues_prob[:5]:
        print(f"     - {issue.title}: {issue.description}")
    
    # Demonstrate audit trail
    print("\n5. Generating comprehensive audit report...")
    audit_report = rules_engine.generate_comprehensive_audit_report(audit_trail_prob)
    
    # Show key sections of audit report
    audit_lines = audit_report.split('\n')
    print("   Audit Report Summary:")
    for line in audit_lines[:15]:  # Show first 15 lines
        if line.strip():
            print(f"   {line}")
    
    # Demonstrate provenance tracking
    print("\n6. Demonstrating provenance tracking...")
    if audit_trail_prob:
        sample_entry = audit_trail_prob[0]
        rules_engine.add_provenance_to_audit(
            sample_entry,
            doc_id="PQME_2024_001234",
            page=12,
            offset=450,
            snippet="Patient reports neck pain radiating to bilateral upper extremities with numbness and tingling"
        )
        
        if sample_entry.provenance:
            print(f"   ✓ Added provenance to audit entry {sample_entry.rule_id}")
            print(f"     - Document: {sample_entry.provenance['doc_id']}")
            print(f"     - Page: {sample_entry.provenance['page']}")
            print(f"     - Snippet: {sample_entry.provenance['snippet'][:60]}...")
    
    # Export configuration
    print("\n7. Exporting rules configuration...")
    export_data = rules_engine.export_rules_configuration()
    
    if "error" not in export_data:
        print(f"   ✓ Exported {export_data['metadata']['total_rules']} rules")
        print(f"   ✓ Export timestamp: {export_data['metadata']['export_timestamp']}")
        
        # Show sample rule structure
        if export_data['rules']:
            sample_rule = export_data['rules'][0]
            print(f"   ✓ Sample rule: {sample_rule['id']} ({sample_rule['priority']})")
    
    # Legal compliance summary
    print("\n8. Legal Compliance Summary:")
    print("   " + "=" * 50)
    
    legal_rules = [
        ("§4062.3 Declaration", "R001_require_4062_3"),
        ("MLPRR Billing", "R002_page_count_billable"), 
        ("Interpreter -93 Modifier", "R103_interpreter_93_modifier_compliance"),
        ("LC 4663/4664 Apportionment", "R101_lc4663_apportionment_language"),
        ("AMA Guides Citations", "R105_ama_guides_citation_accuracy"),
        ("ROM Measurements", "R106_rom_measurement_compliance"),
        ("ADL Grid", "R107_adl_grid_comprehensive"),
        ("Signature Attestation", "R110_signature_attestation_complete")
    ]
    
    rule_ids = [rule.id for rule in rules_engine.rules]
    
    for requirement, rule_id in legal_rules:
        status = "✓" if rule_id in rule_ids else "✗"
        print(f"   {status} {requirement}")
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    return {
        "compliant_issues": len(issues),
        "compliant_score": quality_score.overall_score,
        "problematic_issues": len(issues_prob),
        "problematic_score": quality_score_prob.overall_score,
        "audit_entries": len(audit_trail_prob),
        "rules_loaded": len(rules_engine.rules)
    }


if __name__ == "__main__":
    try:
        results = demonstrate_comprehensive_validation()
        
        print(f"\nFinal Results:")
        print(f"- Compliant validation: {results['compliant_issues']} issues, {results['compliant_score']:.1f}% score")
        print(f"- Problematic validation: {results['problematic_issues']} issues, {results['problematic_score']:.1f}% score")
        print(f"- Total rules loaded: {results['rules_loaded']}")
        print(f"- Audit trail entries: {results['audit_entries']}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Error running demonstration: {e}")
        sys.exit(1)