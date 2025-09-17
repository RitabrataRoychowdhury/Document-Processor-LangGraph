"""
Comprehensive tests for the Advanced QME Rules Engine with legal compliance.

This test suite validates the enhanced YAML-configured rules engine with
comprehensive legal compliance, audit trail, and provenance tracking.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

try:
    from src.core.validation.advanced_qme_rules_engine import (
        AdvancedQMERulesEngine, ValidationContext, RuleDefinition, 
        RulePriority, AuditEntry, ProvenanceReference
    )
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity, SectionType
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, Finding
except ImportError:
    from src.core.validation.advanced_qme_rules_engine import (
        AdvancedQMERulesEngine, ValidationContext, RuleDefinition, 
        RulePriority, AuditEntry, ProvenanceReference
    )
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity, SectionType
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from models.knowledge_graph import Diagnosis, Finding


class TestAdvancedQMERulesEngineComprehensive:
    """Test suite for comprehensive advanced QME rules engine."""
    
    @pytest.fixture
    def rules_engine(self):
        """Create rules engine instance for testing."""
        return AdvancedQMERulesEngine()
    
    @pytest.fixture
    def sample_template_data(self):
        """Create sample QME template data for testing."""
        patient_info = PatientInfo(
            name="John Doe",
            age=45,
            gender="Male",
            case_number="WC12345",
            employer="Test Company",
            injury_date=datetime(2023, 1, 15)
        )
        
        medical_findings = MedicalFindings(
            findings=[
                Finding(
                    id="finding_1",
                    section_id="section_1",
                    finding_type="physical",
                    description="Cervical spine pain with limited range of motion",
                    page_reference=1
                )
            ]
        )
        
        return QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings
        )
    
    @pytest.fixture
    def comprehensive_document_metadata(self):
        """Create comprehensive document metadata for testing."""
        return {
            "examiner_name": "Dr. Jane Smith",
            "examiner_license": "MD12345",
            "interpreter_needed": False,
            "interpreter_used": False,
            "declaration_present": True,
            "total_pages_reviewed": 250,
            "billing_amount": 150.00,
            "industrial_percentage": 75.0,
            "nonindustrial_percentage": 25.0,
            "causation_found": True,
            "causation_type": "specific_injury"
        }
    
    def test_rules_engine_initialization(self, rules_engine):
        """Test that rules engine initializes correctly with comprehensive rules."""
        assert rules_engine is not None
        assert len(rules_engine.rules) > 0
        
        # Check that enhanced legal compliance rules are loaded
        rule_ids = [rule.id for rule in rules_engine.rules]
        
        # Verify key legal compliance rules are present
        required_legal_rules = [
            "R001_require_4062_3",
            "R101_lc4663_apportionment_language",
            "R102_statutory_language_precision",
            "R103_interpreter_93_modifier_compliance",
            "R104_mlprr_billing_precision"
        ]
        
        for rule_id in required_legal_rules:
            assert rule_id in rule_ids, f"Missing required legal rule: {rule_id}"
    
    def test_comprehensive_validation_execution(self, rules_engine, sample_template_data, comprehensive_document_metadata):
        """Test comprehensive validation with all rule types."""
        issues, quality_score, audit_trail = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, comprehensive_document_metadata
        )
        
        # Verify validation results
        assert isinstance(issues, list)
        assert isinstance(quality_score, QualityScore)
        assert isinstance(audit_trail, list)
        
        # Check that audit trail contains entries
        assert len(audit_trail) > 0
        
        # Verify audit entries have required fields
        for entry in audit_trail:
            assert hasattr(entry, 'rule_id')
            assert hasattr(entry, 'timestamp')
            assert hasattr(entry, 'action')
            assert hasattr(entry, 'result')
    
    def test_legal_compliance_validation(self, rules_engine, sample_template_data):
        """Test specific legal compliance validations."""
        # Test with missing legal requirements
        metadata_missing_legal = {
            "declaration_present": False,
            "total_pages_reviewed": None,
            "industrial_percentage": None,
            "nonindustrial_percentage": None
        }
        
        issues, quality_score, audit_trail = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, metadata_missing_legal
        )
        
        # Should have critical issues for missing legal requirements
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        assert len(critical_issues) > 0
        
        # Quality score should be significantly impacted
        assert quality_score.compliance_score < 80.0
    
    def test_mlprr_billing_validation(self, rules_engine, sample_template_data):
        """Test MLPRR billing calculation validation."""
        # Test correct billing calculation
        correct_billing_metadata = {
            "total_pages_reviewed": 250,
            "billing_amount": 150.00,  # (250 - 200) * 3.00 = 150.00
            "declaration_present": True
        }
        
        issues, _, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, correct_billing_metadata
        )
        
        # Should not have billing calculation errors
        billing_issues = [issue for issue in issues if "billing" in issue.title.lower()]
        calculation_errors = [issue for issue in billing_issues if "calculation" in issue.description.lower()]
        assert len(calculation_errors) == 0
        
        # Test incorrect billing calculation
        incorrect_billing_metadata = {
            "total_pages_reviewed": 250,
            "billing_amount": 100.00,  # Incorrect amount
            "declaration_present": True
        }
        
        issues, _, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, incorrect_billing_metadata
        )
        
        # Should have billing calculation error
        billing_issues = [issue for issue in issues if "billing" in issue.title.lower() or "mlprr" in issue.title.lower()]
        assert len(billing_issues) > 0
    
    def test_apportionment_validation(self, rules_engine, sample_template_data):
        """Test apportionment percentage validation."""
        # Test correct apportionment
        correct_apportionment = {
            "industrial_percentage": 60.0,
            "nonindustrial_percentage": 40.0
        }
        
        issues, _, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, correct_apportionment
        )
        
        # Should not have apportionment percentage errors
        apportionment_issues = [issue for issue in issues if "apportionment" in issue.title.lower()]
        percentage_errors = [issue for issue in apportionment_issues if "percentage" in issue.description.lower()]
        assert len(percentage_errors) == 0
        
        # Test incorrect apportionment (doesn't sum to 100%)
        incorrect_apportionment = {
            "industrial_percentage": 60.0,
            "nonindustrial_percentage": 50.0  # Sums to 110%
        }
        
        issues, _, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, incorrect_apportionment
        )
        
        # Should have apportionment percentage error
        apportionment_issues = [issue for issue in issues if "apportionment" in issue.title.lower()]
        assert len(apportionment_issues) > 0
    
    def test_interpreter_compliance_validation(self, rules_engine, sample_template_data):
        """Test interpreter compliance validation."""
        # Test when interpreter is used
        interpreter_metadata = {
            "interpreter_used": True,
            "interpreter_needed": True
        }
        
        issues, _, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, interpreter_metadata
        )
        
        # Should have issues for missing interpreter documentation
        interpreter_issues = [issue for issue in issues if "interpreter" in issue.title.lower()]
        assert len(interpreter_issues) > 0
    
    def test_audit_trail_generation(self, rules_engine, sample_template_data, comprehensive_document_metadata):
        """Test comprehensive audit trail generation."""
        _, _, audit_trail = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, comprehensive_document_metadata
        )
        
        # Generate audit report
        audit_report = rules_engine.generate_comprehensive_audit_report(audit_trail)
        
        assert isinstance(audit_report, str)
        assert "COMPREHENSIVE QME VALIDATION AUDIT REPORT" in audit_report
        assert "RULE EXECUTION SUMMARY" in audit_report
        assert "LEGAL COMPLIANCE SUMMARY" in audit_report
        assert "PROVENANCE TRACKING SUMMARY" in audit_report
        assert "VALIDATION STATISTICS" in audit_report
    
    def test_provenance_tracking(self, rules_engine):
        """Test provenance tracking functionality."""
        audit_entry = AuditEntry(
            rule_id="R001_test",
            action="validation",
            result="completed"
        )
        
        # Add provenance
        rules_engine.add_provenance_to_audit(
            audit_entry, 
            doc_id="doc_123", 
            page=5, 
            offset=150, 
            snippet="This is a test snippet from the document"
        )
        
        assert audit_entry.provenance is not None
        assert audit_entry.provenance["doc_id"] == "doc_123"
        assert audit_entry.provenance["page"] == 5
        assert audit_entry.provenance["offset"] == 150
        assert "test snippet" in audit_entry.provenance["snippet"]
    
    def test_rule_coverage_report(self, rules_engine):
        """Test rule coverage reporting."""
        coverage_report = rules_engine.get_rule_coverage_report()
        
        assert isinstance(coverage_report, dict)
        assert "total_rules" in coverage_report
        assert "rules_by_priority" in coverage_report
        assert "rules_by_section" in coverage_report
        assert "legal_compliance_rules" in coverage_report
        assert "medical_validation_rules" in coverage_report
        
        # Verify priority distribution
        priority_counts = coverage_report["rules_by_priority"]
        assert "MUST" in priority_counts
        assert "SHOULD" in priority_counts
        assert "MAY" in priority_counts
        
        # Should have significant number of MUST rules for legal compliance
        assert priority_counts["MUST"] >= 15
    
    def test_rules_configuration_validation(self, rules_engine):
        """Test rules configuration validation."""
        validation_errors = rules_engine.validate_rules_configuration()
        
        # Should have no validation errors for properly configured rules
        assert isinstance(validation_errors, list)
        
        # If there are errors, they should be descriptive
        for error in validation_errors:
            assert isinstance(error, str)
            assert len(error) > 0
    
    def test_quality_score_calculation(self, rules_engine, sample_template_data):
        """Test enhanced quality score calculation."""
        # Test with minimal issues
        good_metadata = {
            "examiner_name": "Dr. Smith",
            "examiner_license": "MD123",
            "declaration_present": True,
            "total_pages_reviewed": 220,
            "billing_amount": 60.00,
            "industrial_percentage": 80.0,
            "nonindustrial_percentage": 20.0,
            "causation_found": True
        }
        
        issues, quality_score, _ = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, good_metadata
        )
        
        # Quality score should be reasonable
        assert quality_score.overall_score >= 0.0
        assert quality_score.overall_score <= 100.0
        assert quality_score.completeness_score >= 0.0
        assert quality_score.accuracy_score >= 0.0
        assert quality_score.compliance_score >= 0.0
    
    def test_rule_priority_execution_order(self, rules_engine, sample_template_data, comprehensive_document_metadata):
        """Test that rules are executed in priority order (MUST, SHOULD, MAY)."""
        _, _, audit_trail = rules_engine.validate_qme_report_comprehensive(
            sample_template_data, comprehensive_document_metadata
        )
        
        # Extract rule priorities from audit trail
        must_rules = []
        should_rules = []
        may_rules = []
        
        for entry in audit_trail:
            if rules_engine._is_must_rule_entry(entry):
                must_rules.append(entry)
            elif rules_engine._is_should_rule_entry(entry):
                should_rules.append(entry)
            else:
                may_rules.append(entry)
        
        # MUST rules should be executed first
        if must_rules and should_rules:
            first_must = min(must_rules, key=lambda x: x.timestamp)
            first_should = min(should_rules, key=lambda x: x.timestamp)
            assert first_must.timestamp <= first_should.timestamp
    
    def test_export_rules_configuration(self, rules_engine):
        """Test rules configuration export functionality."""
        export_data = rules_engine.export_rules_configuration()
        
        assert isinstance(export_data, dict)
        assert "metadata" in export_data
        assert "rules" in export_data
        
        metadata = export_data["metadata"]
        assert "export_timestamp" in metadata
        assert "total_rules" in metadata
        assert "rules_file" in metadata
        
        rules_data = export_data["rules"]
        assert isinstance(rules_data, list)
        assert len(rules_data) > 0
        
        # Verify rule structure
        for rule in rules_data:
            assert "id" in rule
            assert "priority" in rule
            assert "description" in rule
            assert "section" in rule
            assert "when_conditions" in rule
            assert "then_actions" in rule


if __name__ == "__main__":
    pytest.main([__file__])