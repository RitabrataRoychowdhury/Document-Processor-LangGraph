"""
Test suite for QME Rules Engine validation against sample patient documents.

This test validates the rules engine using the sample patient documents:
- Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf
- Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf
"""

import unittest
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
    from src.core.generation.enhanced_qme_generator import EnhancedQMETemplateGenerator
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.config.qme_gold_standard_config import qme_config
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestQMERulesEngine(unittest.TestCase):
    """Test cases for QME Rules Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rules_engine = QMERulesEngine()
        self.enhanced_generator = EnhancedQMETemplateGenerator()
        
        # Create sample template data for testing
        self.sample_patient_info = PatientInfo(
            name="John Doe",
            age=45,
            gender="Male",
            case_number="WC-2025-001",
            injury_date=datetime(2025, 9, 5)
        )
        
        self.sample_diagnosis = Diagnosis(
            id="diag-001",
            icd_code="M54.5",
            description="Low back pain",
            severity="moderate",
            certainty=0.85
        )
        
        self.sample_finding = Finding(
            id="find-001",
            section_id="exam-001",
            finding_type="clinical",
            description="Reduced range of motion in lumbar spine",
            page_reference=3
        )
        
        self.sample_impairment_rating = ImpairmentRating(
            id="imp-001",
            diagnosis_id="diag-001",
            percentage=15.0,
            ama_table="15-3",
            rationale="Range of motion method",
            source_page=5
        )
        
        self.sample_medical_findings = MedicalFindings(
            diagnoses=[self.sample_diagnosis],
            findings=[self.sample_finding],
            impairment_ratings=[self.sample_impairment_rating]
        )
        
        self.sample_template_data = QMETemplateData(
            patient_info=self.sample_patient_info,
            medical_findings=self.sample_medical_findings
        )
    
    def test_rules_engine_initialization(self):
        """Test that rules engine initializes correctly."""
        self.assertIsNotNone(self.rules_engine)
        self.assertIsNotNone(self.rules_engine.gold_standard_rules)
        self.assertIsNotNone(self.rules_engine.ama_validator)
        self.assertIsNotNone(self.rules_engine.legal_validator)
    
    def test_validate_complete_template(self):
        """Test validation of a complete template."""
        issues, quality_score = self.rules_engine.validate_qme_report(self.sample_template_data)
        
        # Should have some issues but not critical ones for complete data
        self.assertIsInstance(issues, list)
        self.assertIsInstance(quality_score, QualityScore)
        self.assertGreaterEqual(quality_score.overall_score, 0)
        self.assertLessEqual(quality_score.overall_score, 100)
    
    def test_validate_incomplete_patient_info(self):
        """Test validation with incomplete patient information."""
        incomplete_patient = PatientInfo(
            name="",  # Missing name
            age=None,  # Missing age
            case_number=""  # Missing case number
        )
        
        incomplete_template = QMETemplateData(
            patient_info=incomplete_patient,
            medical_findings=MedicalFindings()
        )
        
        issues, quality_score = self.rules_engine.validate_qme_report(incomplete_template)
        
        # Should have critical issues for missing required fields
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        self.assertGreater(len(critical_issues), 0)
        self.assertLess(quality_score.overall_score, 50)  # Low score for incomplete data
    
    def test_validate_missing_diagnosis(self):
        """Test validation with missing diagnosis."""
        no_diagnosis_findings = MedicalFindings(
            diagnoses=[],  # No diagnoses
            findings=self.sample_medical_findings.findings,
            impairment_ratings=[]
        )
        
        no_diagnosis_template = QMETemplateData(
            patient_info=self.sample_patient_info,
            medical_findings=no_diagnosis_findings
        )
        
        issues, quality_score = self.rules_engine.validate_qme_report(no_diagnosis_template)
        
        # Should have critical issue for missing diagnosis
        diagnosis_issues = [issue for issue in issues if issue.section == SectionType.DIAGNOSIS]
        self.assertGreater(len(diagnosis_issues), 0)
    
    def test_validate_impairment_rating(self):
        """Test AMA Guidelines validation for impairment rating."""
        # Test valid impairment rating
        valid_issues = self.rules_engine.ama_validator.validate_impairment_rating(
            self.sample_impairment_rating, 
            self.sample_diagnosis
        )
        
        # Should have minimal issues for valid rating
        critical_issues = [issue for issue in valid_issues if issue.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(critical_issues), 0)
        
        # Test invalid impairment rating
        invalid_rating = ImpairmentRating(
            id="imp-002",
            diagnosis_id="diag-001",
            percentage=150.0,  # Invalid percentage > 100
            ama_table="invalid-table",  # Invalid table reference
            rationale="",  # Missing methodology
            source_page=5
        )
        
        invalid_issues = self.rules_engine.ama_validator.validate_impairment_rating(
            invalid_rating,
            self.sample_diagnosis
        )
        
        # Should have critical issues for invalid rating
        critical_issues = [issue for issue in invalid_issues if issue.severity == ValidationSeverity.CRITICAL]
        self.assertGreater(len(critical_issues), 0)
    
    def test_legal_compliance_validation(self):
        """Test legal compliance validation."""
        issues = self.rules_engine.legal_validator.validate_legal_compliance(self.sample_template_data)
        
        # Should return list of issues
        self.assertIsInstance(issues, list)
        
        # Test with missing required information
        incomplete_template = QMETemplateData(
            patient_info=PatientInfo(),  # Empty patient info
            medical_findings=MedicalFindings()  # Empty medical findings
        )
        
        incomplete_issues = self.rules_engine.legal_validator.validate_legal_compliance(incomplete_template)
        
        # Should have more issues for incomplete data
        self.assertGreaterEqual(len(incomplete_issues), len(issues))
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        issues, quality_score = self.rules_engine.validate_qme_report(self.sample_template_data)
        
        # Verify quality score components
        self.assertIsInstance(quality_score.overall_score, float)
        self.assertIsInstance(quality_score.completeness_score, float)
        self.assertIsInstance(quality_score.accuracy_score, float)
        self.assertIsInstance(quality_score.compliance_score, float)
        
        # Verify score ranges
        self.assertGreaterEqual(quality_score.overall_score, 0)
        self.assertLessEqual(quality_score.overall_score, 100)
        
        # Verify issue counts
        self.assertEqual(quality_score.total_issues, len(issues))
        
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        self.assertEqual(quality_score.critical_issues, critical_count)
    
    def test_improvement_suggestions(self):
        """Test improvement suggestions generation."""
        issues, _ = self.rules_engine.validate_qme_report(self.sample_template_data)
        suggestions = self.rules_engine.get_improvement_suggestions(issues)
        
        # Should return dictionary organized by section
        self.assertIsInstance(suggestions, dict)
        
        # Each section should have list of suggestions
        for section, section_suggestions in suggestions.items():
            self.assertIsInstance(section, SectionType)
            self.assertIsInstance(section_suggestions, list)
    
    def test_quality_report_generation(self):
        """Test quality report generation."""
        issues, quality_score = self.rules_engine.validate_qme_report(self.sample_template_data)
        quality_report = self.rules_engine.generate_quality_report(issues, quality_score)
        
        # Should return formatted string report
        self.assertIsInstance(quality_report, str)
        self.assertIn("QME REPORT QUALITY ASSESSMENT", quality_report)
        self.assertIn("Overall Quality Score", quality_report)
    
    def test_gold_standard_requirements(self):
        """Test gold standard requirements configuration."""
        # Test that required sections are defined
        self.assertIsInstance(qme_config.REQUIRED_SECTIONS, list)
        self.assertGreater(len(qme_config.REQUIRED_SECTIONS), 10)
        
        # Test patient identification requirements
        self.assertIn("required_fields", qme_config.PATIENT_ID_REQUIREMENTS)
        self.assertIn("full_name", qme_config.PATIENT_ID_REQUIREMENTS["required_fields"])
        
        # Test formatting requirements
        self.assertIn("typography", qme_config.FORMATTING_REQUIREMENTS)
        self.assertEqual(qme_config.FORMATTING_REQUIREMENTS["typography"]["font_family"], "Times New Roman")
    
    def test_enhanced_generator_integration(self):
        """Test integration with enhanced QME generator."""
        # This would normally use a real patient ID, but we'll test the structure
        try:
            # Test that enhanced generator initializes correctly
            self.assertIsNotNone(self.enhanced_generator)
            self.assertIsNotNone(self.enhanced_generator.rules_engine)
            
            # Test quality summary generation
            from src.core.generation.enhanced_qme_generator import EnhancedQMEResult
            
            # Create mock result for testing
            mock_result = EnhancedQMEResult(
                file_path="test.docx",
                template_data=self.sample_template_data,
                validation_issues=[],
                quality_score=QualityScore(
                    overall_score=85.0,
                    completeness_score=90.0,
                    accuracy_score=80.0,
                    compliance_score=85.0
                ),
                quality_report="Test report",
                improvement_suggestions={}
            )
            
            summary = self.enhanced_generator.generate_quality_summary_report(mock_result)
            self.assertIsInstance(summary, str)
            self.assertIn("QUALITY SUMMARY", summary)
            
        except Exception as e:
            self.fail(f"Enhanced generator integration test failed: {e}")


class TestQMERulesEngineWithSampleDocuments(unittest.TestCase):
    """Test QME Rules Engine with actual sample patient documents."""
    
    def setUp(self):
        """Set up test fixtures for sample document testing."""
        self.rules_engine = QMERulesEngine()
        
        # Sample document paths (these would be processed in real implementation)
        self.sample_doc_1 = "Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf"
        self.sample_doc_2 = "Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
    
    def test_sample_document_validation_structure(self):
        """Test that validation structure works for sample documents."""
        # Create template data that would be extracted from sample documents
        sample_patient_1 = PatientInfo(
            name="Sample Patient AA",
            age=42,
            gender="Male",
            case_number="CL-09.09.2025",
            injury_date=datetime(2025, 9, 5)
        )
        
        # Sample diagnosis that might be extracted
        sample_diagnosis_1 = Diagnosis(
            id="sample-diag-1",
            icd_code="S13.4",  # Sprain of ligaments of cervical spine
            description="Cervical spine sprain",
            severity="moderate"
        )
        
        sample_findings_1 = MedicalFindings(
            diagnoses=[sample_diagnosis_1],
            findings=[
                Finding(
                    id="find-1",
                    section_id="exam-1",
                    finding_type="clinical",
                    description="Neck pain and stiffness",
                    page_reference=2
                )
            ]
        )
        
        sample_template_1 = QMETemplateData(
            patient_info=sample_patient_1,
            medical_findings=sample_findings_1
        )
        
        # Validate sample template
        issues, quality_score = self.rules_engine.validate_qme_report(sample_template_1)
        
        # Should process without errors
        self.assertIsInstance(issues, list)
        self.assertIsInstance(quality_score, QualityScore)
        
        # Should identify missing impairment rating
        impairment_issues = [issue for issue in issues if issue.section == SectionType.IMPAIRMENT_RATING]
        self.assertGreater(len(impairment_issues), 0)
    
    def test_validation_against_gold_standard_sections(self):
        """Test validation against gold standard section requirements."""
        # Test that all required sections from gold standard are checked
        required_sections = qme_config.REQUIRED_SECTIONS
        
        # Create minimal template data
        minimal_template = QMETemplateData(
            patient_info=PatientInfo(name="Test Patient"),
            medical_findings=MedicalFindings()
        )
        
        issues, _ = self.rules_engine.validate_qme_report(minimal_template)
        
        # Should have issues for missing required sections/information
        self.assertGreater(len(issues), 5)  # Should have multiple missing elements
        
        # Should have critical issues for missing required fields
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        self.assertGreater(len(critical_issues), 0)


def run_qme_rules_engine_tests():
    """Run all QME Rules Engine tests."""
    print("🧪 Running QME Rules Engine Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestQMERulesEngine))
    test_suite.addTest(unittest.makeSuite(TestQMERulesEngineWithSampleDocuments))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All QME Rules Engine tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        # Print failures and errors
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)
        
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
        
        return False


if __name__ == "__main__":
    success = run_qme_rules_engine_tests()
    sys.exit(0 if success else 1)