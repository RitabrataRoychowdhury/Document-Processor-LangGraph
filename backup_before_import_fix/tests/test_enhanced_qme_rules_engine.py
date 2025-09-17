"""
Test suite for Enhanced QME Rules Engine with Evidence-First Validation.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

try:
    from src.services.qme_rules_engine import (
        QMERulesEngine, ValidationIssue, ValidationSeverity, SectionType,
        EvidenceProvenance, ComplianceReport, QualityScore,
        EvidenceFirstValidator, PostGenerationValidator, LegalComplianceEnhanced
    )
    from src.services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, ImpairmentRating
except ImportError:
    from services.qme_rules_engine import (
        QMERulesEngine, ValidationIssue, ValidationSeverity, SectionType,
        EvidenceProvenance, ComplianceReport, QualityScore,
        EvidenceFirstValidator, PostGenerationValidator, LegalComplianceEnhanced
    )
    from services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from models.knowledge_graph import Diagnosis, ImpairmentRating


class TestEvidenceFirstValidator:
    """Test evidence-first validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.confidence_thresholds = {
            "critical_fields": 0.8,
            "standard_fields": 0.5
        }
        self.validator = EvidenceFirstValidator(self.confidence_thresholds)
    
    def test_validate_critical_field_high_confidence(self):
        """Test validation of critical field with high confidence."""
        provenance = EvidenceProvenance(
            source_document="test.pdf",
            page_number=1,
            text_coordinates=(100, 200, 300, 220),
            snippet_text="John Doe",
            confidence_score=0.95,
            extraction_method="regex"
        )
        
        issue = self.validator.validate_field_confidence("patient_name", 0.95, provenance)
        assert issue is None
    
    def test_validate_critical_field_low_confidence(self):
        """Test validation of critical field with low confidence."""
        provenance = EvidenceProvenance(
            source_document="test.pdf",
            page_number=1,
            text_coordinates=(100, 200, 300, 220),
            snippet_text="unclear text",
            confidence_score=0.6,
            extraction_method="ner"
        )
        
        issue = self.validator.validate_field_confidence("patient_name", 0.6, provenance)
        assert issue is not None
        assert issue.severity == ValidationSeverity.CRITICAL
        assert issue.requires_human_review is True
        assert "patient_name" in issue.title
    
    def test_validate_evidence_sufficiency_missing_critical(self):
        """Test evidence sufficiency with missing critical fields."""
        extracted_fields = {
            "diagnosis": {"confidence": 0.8},
            "impairment_percentage": {"confidence": 0.7}
        }
        
        issues = self.validator.validate_evidence_sufficiency(extracted_fields)
        assert len(issues) > 0
        assert any("Missing Critical Fields" in issue.title for issue in issues)


class TestPostGenerationValidator:
    """Test post-generation validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PostGenerationValidator()
    
    def test_scan_placeholder_text_found(self):
        """Test scanning for placeholder text."""
        report_content = """
        Patient Name: {{PATIENT_NAME}}
        Case Number: {CASE_NUMBER}
        Diagnosis: [DIAGNOSIS]
        TODO: Complete examination section
        """
        
        issues = self.validator.scan_placeholder_text(report_content)
        assert len(issues) >= 4  # Should find all placeholder patterns
        assert all(issue.severity == ValidationSeverity.CRITICAL for issue in issues)
    
    def test_scan_placeholder_text_clean(self):
        """Test scanning clean report with no placeholders."""
        report_content = """
        Patient Name: John Doe
        Case Number: WC12345
        Diagnosis: Lumbar strain
        Examination completed successfully.
        """
        
        issues = self.validator.scan_placeholder_text(report_content)
        assert len(issues) == 0
    
    def test_validate_calculation_accuracy_programmatic(self):
        """Test validation of programmatic calculations."""
        calculations = {
            "impairment_1": {
                "percentage": 15.0,
                "ama_table": "Table 15-3",
                "programmatic": True,
                "rationale": "Based on ROM measurements"
            }
        }
        
        issues = self.validator.validate_calculation_accuracy(calculations)
        assert len(issues) == 0
    
    def test_validate_calculation_accuracy_non_programmatic(self):
        """Test validation of non-programmatic calculations."""
        calculations = {
            "impairment_1": {
                "percentage": 15.0,
                "ama_table": "Table 15-3",
                "programmatic": False,
                "rationale": "LLM generated"
            }
        }
        
        issues = self.validator.validate_calculation_accuracy(calculations)
        assert len(issues) > 0
        assert any("Non-Programmatic Calculation" in issue.title for issue in issues)


class TestLegalComplianceEnhanced:
    """Test enhanced legal compliance validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = LegalComplianceEnhanced()
    
    def test_validate_labor_code_4062_3_complete(self):
        """Test validation of complete Labor Code 4062.3 declaration."""
        report_content = """
        Any documents sent to the physician for record review must be accompanied by a 
        declaration under penalty of perjury that the provider of the documents has 
        complied with the provisions of Labor Code section 4062.3 before providing the 
        documents to the physician. The declaration must also contain an attestation as 
        to the total page count of the documents provided.
        
        Under penalty of perjury, I attest to the total page count.
        """
        
        valid, issues = self.validator.validate_labor_code_4062_3(report_content)
        assert valid is True
        assert len(issues) == 0
    
    def test_validate_labor_code_4062_3_incomplete(self):
        """Test validation of incomplete Labor Code 4062.3 declaration."""
        report_content = "Some incomplete declaration text."
        
        valid, issues = self.validator.validate_labor_code_4062_3(report_content)
        assert valid is False
        assert len(issues) > 0
    
    def test_validate_mandatory_sections_complete(self):
        """Test validation of complete mandatory sections."""
        report_sections = {
            "patient_demographics": "present",
            "records_reviewed": "present",
            "physical_examination": "present",
            "diagnosis": "present",
            "impairment_rating": "present",
            "signature_blocks": "present"
        }
        
        valid, missing = self.validator.validate_mandatory_sections(report_sections)
        assert valid is True
        assert len(missing) == 0
    
    def test_validate_mandatory_sections_missing(self):
        """Test validation with missing mandatory sections."""
        report_sections = {
            "patient_demographics": "present",
            "diagnosis": "present"
        }
        
        valid, missing = self.validator.validate_mandatory_sections(report_sections)
        assert valid is False
        assert len(missing) > 0
        assert "records_reviewed" in missing
    
    def test_validate_signature_blocks_complete(self):
        """Test validation of complete signature blocks."""
        signature_data = {
            "examiner_name": "Dr. John Smith",
            "license_number": "12345",
            "signature_date": "2025-09-16",
            "declaration_text": "Pursuant to AB 1300, LC Sec. 5703, I have not violated Labor Code section 139.3"
        }
        
        valid, issues = self.validator.validate_signature_blocks(signature_data)
        assert valid is True
        assert len(issues) == 0
    
    def test_generate_compliance_report_pass(self):
        """Test generation of passing compliance report."""
        validation_results = {
            "labor_code_4062_3": True,
            "mandatory_sections": True,
            "mlprr_billing": True,
            "signature_blocks": True,
            "evidence_sufficiency": True,
            "calculation_accuracy": True
        }
        
        report = self.validator.generate_compliance_report(validation_results)
        assert report.overall_status == "PASS"
        assert len(report.failed_requirements) == 0
        assert len(report.remediation_steps) == 0
    
    def test_generate_compliance_report_fail(self):
        """Test generation of failing compliance report."""
        validation_results = {
            "labor_code_4062_3": False,
            "mandatory_sections": False,
            "signature_blocks": True,
            "evidence_sufficiency": True,
            "calculation_accuracy": False
        }
        
        report = self.validator.generate_compliance_report(validation_results)
        assert report.overall_status == "FAIL"
        assert len(report.failed_requirements) > 0
        assert len(report.remediation_steps) > 0


class TestQMERulesEngineEnhanced:
    """Test enhanced QME Rules Engine integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QMERulesEngine()
        
        # Create test template data
        self.patient_info = PatientInfo(
            name="John Doe",
            age=45,
            case_number="WC12345"
        )
        
        self.diagnosis = Diagnosis(
            description="Lumbar strain",
            icd_code="M54.5"
        )
        
        self.impairment_rating = ImpairmentRating(
            percentage=15.0,
            ama_table="Table 15-3",
            rationale="Based on ROM measurements"
        )
        
        self.medical_findings = MedicalFindings(
            diagnoses=[self.diagnosis],
            impairment_ratings=[self.impairment_rating]
        )
        
        self.template_data = QMETemplateData(
            patient_info=self.patient_info,
            medical_findings=self.medical_findings
        )
    
    def test_validate_qme_report_basic(self):
        """Test basic QME report validation."""
        issues, quality_score, compliance_report = self.engine.validate_qme_report(self.template_data)
        
        assert isinstance(issues, list)
        assert isinstance(quality_score, QualityScore)
        assert isinstance(compliance_report, ComplianceReport)
        assert quality_score.overall_score >= 0
        assert quality_score.overall_score <= 100
    
    def test_validate_qme_report_with_extracted_fields(self):
        """Test QME report validation with extracted fields."""
        extracted_fields = {
            "patient_name": {
                "confidence": 0.95,
                "provenance": {
                    "source_document": "test.pdf",
                    "page_number": 1,
                    "coordinates": (100, 200, 300, 220),
                    "snippet": "John Doe",
                    "method": "regex"
                }
            },
            "case_number": {
                "confidence": 0.85,
                "provenance": {
                    "source_document": "test.pdf",
                    "page_number": 1,
                    "coordinates": (100, 250, 300, 270),
                    "snippet": "WC12345",
                    "method": "regex"
                }
            }
        }
        
        issues, quality_score, compliance_report = self.engine.validate_qme_report(
            self.template_data, extracted_fields=extracted_fields
        )
        
        assert quality_score.fields_above_confidence_threshold >= 0
        assert quality_score.evidence_confidence_score >= 0
    
    def test_validate_qme_report_with_report_content(self):
        """Test QME report validation with generated report content."""
        report_content = """
        Patient Name: John Doe
        Case Number: WC12345
        
        Any documents sent to the physician for record review must be accompanied by a 
        declaration under penalty of perjury that the provider of the documents has 
        complied with the provisions of Labor Code section 4062.3 before providing the 
        documents to the physician. The declaration must also contain an attestation as 
        to the total page count of the documents provided.
        """
        
        issues, quality_score, compliance_report = self.engine.validate_qme_report(
            self.template_data, report_content=report_content
        )
        
        # Should have fewer placeholder issues with clean content
        placeholder_issues = [i for i in issues if "placeholder" in i.title.lower()]
        assert len(placeholder_issues) == 0
    
    def test_evidence_first_confidence_validation(self):
        """Test evidence-first confidence validation."""
        extracted_fields = {
            "patient_name": {
                "confidence": 0.6,  # Below critical threshold
                "provenance": {
                    "source_document": "test.pdf",
                    "page_number": 1,
                    "coordinates": (100, 200, 300, 220),
                    "snippet": "unclear name",
                    "method": "ner"
                }
            }
        }
        
        issues, quality_score, compliance_report = self.engine.validate_qme_report(
            self.template_data, extracted_fields=extracted_fields
        )
        
        # Should have critical issues for low confidence critical field
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        confidence_issues = [i for i in critical_issues if "confidence" in i.title.lower()]
        assert len(confidence_issues) > 0


if __name__ == "__main__":
    pytest.main([__file__])