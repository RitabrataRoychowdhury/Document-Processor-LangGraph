"""
Tests for Professional Template Assembly System.

This module tests the professional template assembler, validation system,
and quality assurance components.
"""

import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

try:
    from tests.template.test_enhanced_professional_template_assembler import (
        ProfessionalTemplateAssembler,
        TemplateAssemblyConfig,
        GoldStandardFormatter,
        ContentValidator,
        ProfessionalTemplateResult
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
except ImportError:
    from src.services.professional_template_assembler_simple import (
        ProfessionalTemplateAssembler,
        TemplateAssemblyConfig,
        GoldStandardFormatter,
        ContentValidator,
        ProfessionalTemplateResult
    )
    from src.core.generation.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.core.validation.qme_rules_engine import ValidationIssue, QualityScore, ValidationSeverity
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating


class TestTemplateAssemblyConfig:
    """Test TemplateAssemblyConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TemplateAssemblyConfig()
        
        assert config.include_quality_indicators is False
        assert config.include_missing_placeholders is True
        assert config.apply_professional_formatting is True
        assert config.validate_before_assembly is True
        assert config.validate_after_assembly is True
        assert config.generate_quality_report is True
        assert config.output_format == "docx"
        assert config.template_version == "1.0"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TemplateAssemblyConfig(
            include_quality_indicators=True,
            include_missing_placeholders=False,
            template_version="2.0"
        )
        
        assert config.include_quality_indicators is True
        assert config.include_missing_placeholders is False
        assert config.template_version == "2.0"


class TestGoldStandardFormatter:
    """Test GoldStandardFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = GoldStandardFormatter()
    
    @patch('src.services.professional_template_assembler.Document')
    def test_apply_document_formatting(self, mock_document):
        """Test applying document formatting."""
        mock_doc = Mock()
        mock_section = Mock()
        mock_doc.sections = [mock_section]
        
        # Mock styles
        mock_styles = Mock()
        mock_normal_style = Mock()
        mock_font = Mock()
        mock_paragraph = Mock()
        
        mock_normal_style.font = mock_font
        mock_normal_style.paragraph_format = mock_paragraph
        mock_styles.__getitem__.return_value = mock_normal_style
        mock_doc.styles = mock_styles
        
        self.formatter.apply_document_formatting(mock_doc)
        
        # Verify margins were set
        assert mock_section.top_margin is not None
        assert mock_section.bottom_margin is not None
        assert mock_section.left_margin is not None
        assert mock_section.right_margin is not None
    
    @patch('src.services.professional_template_assembler.Document')
    def test_create_professional_header(self, mock_document):
        """Test creating professional header."""
        mock_doc = Mock()
        mock_section = Mock()
        mock_header = Mock()
        mock_para = Mock()
        
        mock_section.header = mock_header
        mock_header.paragraphs = [mock_para]
        mock_doc.sections = [mock_section]
        
        doctor_info = {
            'name': 'John Smith',
            'specialty': 'Orthopaedic Surgery',
            'license': 'CA12345',
            'phone': '555-1234'
        }
        
        self.formatter.create_professional_header(mock_doc, doctor_info)
        
        # Verify header was configured
        mock_para.clear.assert_called_once()
    
    def test_create_professional_header_no_doctor_info(self):
        """Test creating header without doctor info."""
        mock_doc = Mock()
        mock_section = Mock()
        mock_header = Mock()
        mock_para = Mock()
        
        mock_section.header = mock_header
        mock_header.paragraphs = [mock_para]
        mock_doc.sections = [mock_section]
        
        self.formatter.create_professional_header(mock_doc, None)
        
        # Should still clear the paragraph
        mock_para.clear.assert_called_once()


class TestContentValidator:
    """Test ContentValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ContentValidator()
    
    def create_sample_template_data(self):
        """Create sample template data for testing."""
        patient_info = PatientInfo(
            name="John Doe",
            age=45,
            gender="Male",
            case_number="WC2024-001",
            injury_date=datetime(2024, 1, 15),
            employer="ABC Corp",
            occupation="Worker"
        )
        
        diagnosis = Diagnosis(
            id="diag_001",
            icd_code="M54.5",
            description="Low back pain",
            severity="moderate",
            certainty=0.9
        )
        
        finding = Finding(
            id="find_001",
            section_id="exam_001",
            finding_type="examination",
            description="Decreased ROM"
        )
        
        rating = ImpairmentRating(
            id="rating_001",
            diagnosis_id="diag_001",
            percentage=15,
            ama_table="15-3",
            rationale="DRE Category II"
        )
        
        medical_findings = MedicalFindings(
            diagnoses=[diagnosis],
            findings=[finding],
            impairment_ratings=[rating]
        )
        
        return QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings
        )
    
    @patch('src.services.professional_template_assembler.QMERulesEngine')
    def test_validate_pre_assembly_valid_data(self, mock_rules_engine):
        """Test pre-assembly validation with valid data."""
        # Mock rules engine
        mock_engine = Mock()
        mock_rules_engine.return_value = mock_engine
        
        mock_engine.validate_qme_report.return_value = (
            [],  # No issues
            QualityScore(
                overall_score=85.0,
                completeness_score=90.0,
                accuracy_score=85.0,
                compliance_score=80.0
            )
        )
        
        template_data = self.create_sample_template_data()
        result = self.validator.validate_pre_assembly(template_data)
        
        assert result.is_valid is True
        assert result.compliance_status == "compliant"
        assert len(result.validation_issues) == 0
    
    @patch('src.services.professional_template_assembler.QMERulesEngine')
    def test_validate_pre_assembly_critical_issues(self, mock_rules_engine):
        """Test pre-assembly validation with critical issues."""
        # Mock rules engine
        mock_engine = Mock()
        mock_rules_engine.return_value = mock_engine
        
        critical_issue = ValidationIssue(
            section="patient_demographics",
            severity=ValidationSeverity.CRITICAL,
            title="Missing Patient Name",
            description="Patient name is required"
        )
        
        mock_engine.validate_qme_report.return_value = (
            [critical_issue],
            QualityScore(
                overall_score=45.0,
                completeness_score=50.0,
                accuracy_score=40.0,
                compliance_score=45.0,
                critical_issues=1
            )
        )
        
        template_data = self.create_sample_template_data()
        template_data.patient_info.name = ""  # Remove name to trigger issue
        
        result = self.validator.validate_pre_assembly(template_data)
        
        assert result.is_valid is False
        assert result.compliance_status == "non_compliant"
        assert len(result.validation_issues) == 1
        assert result.validation_issues[0].severity == ValidationSeverity.CRITICAL
    
    def test_identify_missing_sections(self):
        """Test identifying missing sections."""
        template_data = self.create_sample_template_data()
        
        # Remove some required information
        template_data.patient_info.name = ""
        template_data.patient_info.case_number = ""
        template_data.medical_findings.diagnoses = []
        
        missing = self.validator._identify_missing_sections(template_data)
        
        assert "Patient Name" in missing
        assert "Case Number" in missing
        assert "Primary Diagnosis" in missing
    
    def test_estimate_placeholder_count(self):
        """Test estimating placeholder count."""
        template_data = self.create_sample_template_data()
        
        # Remove some information to create placeholders
        template_data.patient_info.age = None
        template_data.patient_info.gender = None
        template_data.medical_findings.findings = []
        
        count = self.validator._estimate_placeholder_count(template_data)
        
        assert count > 0  # Should have some placeholders
    
    @patch('src.services.professional_template_assembler.Document')
    def test_validate_post_assembly(self, mock_document_class):
        """Test post-assembly validation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
            doc_path = tmp_file.name
        
        try:
            # Mock document
            mock_doc = Mock()
            mock_para1 = Mock()
            mock_para1.text = "PATIENT IDENTIFICATION"
            mock_para2 = Mock()
            mock_para2.text = "Some content with [MISSING INFO] placeholder"
            
            mock_doc.paragraphs = [mock_para1, mock_para2]
            mock_doc.sections = [Mock()]
            mock_doc.tables = []
            
            mock_document_class.return_value = mock_doc
            
            template_data = self.create_sample_template_data()
            result = self.validator.validate_post_assembly(doc_path, template_data)
            
            assert result is not None
            assert isinstance(result.quality_score, QualityScore)
            
        finally:
            # Clean up
            if os.path.exists(doc_path):
                os.unlink(doc_path)


class TestProfessionalTemplateAssembler:
    """Test ProfessionalTemplateAssembler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assembler = ProfessionalTemplateAssembler()
    
    def create_sample_template_data(self):
        """Create sample template data for testing."""
        patient_info = PatientInfo(
            name="Jane Smith",
            age=35,
            gender="Female",
            case_number="WC2024-002",
            injury_date=datetime(2024, 2, 20),
            employer="XYZ Company",
            occupation="Office Worker"
        )
        
        diagnosis = Diagnosis(
            id="diag_002",
            icd_code="S83.5",
            description="Sprain of cruciate ligament of knee",
            severity="mild",
            certainty=0.8
        )
        
        medical_findings = MedicalFindings(
            diagnoses=[diagnosis],
            findings=[],
            impairment_ratings=[]
        )
        
        return QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings
        )
    
    @patch('src.services.professional_template_assembler.Document')
    def test_assemble_professional_template_basic(self, mock_document_class):
        """Test basic template assembly."""
        # Mock document
        mock_doc = Mock()
        mock_document_class.return_value = mock_doc
        
        template_data = self.create_sample_template_data()
        config = TemplateAssemblyConfig(
            validate_before_assembly=False,
            validate_after_assembly=False,
            generate_quality_report=False
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_template.docx")
            
            result = self.assembler.assemble_professional_template(
                template_data=template_data,
                output_path=output_path,
                assembly_config=config
            )
            
            assert isinstance(result, ProfessionalTemplateResult)
            assert result.file_path == output_path
            assert result.template_data == template_data
            assert result.assembly_config == config
    
    @patch('src.services.professional_template_assembler.Document')
    @patch('src.services.professional_template_assembler.ContentValidator')
    def test_assemble_with_validation(self, mock_validator_class, mock_document_class):
        """Test template assembly with validation."""
        # Mock document
        mock_doc = Mock()
        mock_document_class.return_value = mock_doc
        
        # Mock validator
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        
        # Mock validation results
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validation_result.validation_issues = []
        mock_validation_result.quality_score = QualityScore(85, 90, 85, 80)
        mock_validation_result.missing_sections = []
        mock_validation_result.placeholder_count = 0
        mock_validation_result.compliance_status = "compliant"
        
        mock_validator.validate_pre_assembly.return_value = mock_validation_result
        mock_validator.validate_post_assembly.return_value = mock_validation_result
        
        template_data = self.create_sample_template_data()
        config = TemplateAssemblyConfig(
            validate_before_assembly=True,
            validate_after_assembly=True,
            generate_quality_report=False
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_template.docx")
            
            result = self.assembler.assemble_professional_template(
                template_data=template_data,
                output_path=output_path,
                assembly_config=config
            )
            
            assert result.pre_assembly_validation.is_valid is True
            assert result.post_assembly_validation.is_valid is True
            
            # Verify validation methods were called
            mock_validator.validate_pre_assembly.assert_called_once()
            mock_validator.validate_post_assembly.assert_called_once()
    
    def test_generate_download_package(self):
        """Test generating download package."""
        # Create a mock result
        template_data = self.create_sample_template_data()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock template file
            template_path = os.path.join(temp_dir, "template.docx")
            with open(template_path, 'w') as f:
                f.write("Mock template content")
            
            # Create mock validation results
            mock_validation = Mock()
            mock_validation.is_valid = True
            mock_validation.validation_issues = []
            mock_validation.quality_score = QualityScore(85, 90, 85, 80)
            mock_validation.missing_sections = []
            mock_validation.placeholder_count = 0
            mock_validation.compliance_status = "compliant"
            
            result = ProfessionalTemplateResult(
                file_path=template_path,
                template_data=template_data,
                assembly_config=TemplateAssemblyConfig(),
                pre_assembly_validation=mock_validation,
                post_assembly_validation=mock_validation,
                file_size_bytes=1024,
                page_count=5,
                word_count=500
            )
            
            package_dir = self.assembler.generate_download_package(result)
            
            assert os.path.exists(package_dir)
            assert os.path.isdir(package_dir)
            
            # Check package contents
            package_files = os.listdir(package_dir)
            assert "template.docx" in package_files
            assert "package_info.txt" in package_files
    
    @patch('src.services.professional_template_assembler.Document')
    def test_create_professional_document_with_doctor_info(self, mock_document_class):
        """Test creating document with doctor information."""
        mock_doc = Mock()
        mock_document_class.return_value = mock_doc
        
        template_data = self.create_sample_template_data()
        config = TemplateAssemblyConfig()
        
        doctor_info = {
            'name': 'Dr. Sarah Johnson',
            'license': 'CA67890',
            'specialty': 'Orthopaedic Surgery',
            'phone': '555-9876'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_template.docx")
            
            result_path = self.assembler._create_professional_document(
                template_data, output_path, doctor_info, config
            )
            
            assert result_path == output_path
            mock_doc.save.assert_called_once_with(output_path)
    
    def test_get_file_statistics(self):
        """Test getting file statistics."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("Test content for statistics")
            tmp_path = tmp_file.name
        
        try:
            # Test with non-DOCX file (will have limited stats)
            stats = self.assembler._get_file_statistics(tmp_path)
            
            assert 'size' in stats
            assert 'pages' in stats
            assert 'words' in stats
            assert stats['size'] > 0
            
        finally:
            os.unlink(tmp_path)
    
    def test_get_file_statistics_nonexistent_file(self):
        """Test getting statistics for non-existent file."""
        stats = self.assembler._get_file_statistics("nonexistent_file.docx")
        
        assert stats['size'] == 0
        assert stats['pages'] == 0
        assert stats['words'] == 0


class TestIntegration:
    """Integration tests for the complete template assembly system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.assembler = ProfessionalTemplateAssembler()
    
    def create_complete_template_data(self):
        """Create complete template data for integration testing."""
        patient_info = PatientInfo(
            name="Integration Test Patient",
            age=40,
            gender="Male",
            case_number="INT2024-001",
            injury_date=datetime(2024, 3, 1),
            employer="Integration Corp",
            occupation="Test Engineer",
            body_parts=["Shoulder", "Neck"]
        )
        
        diagnosis = Diagnosis(
            id="diag_int_001",
            icd_code="M75.3",
            description="Calcific tendinitis of shoulder",
            severity="moderate",
            certainty=0.85
        )
        
        finding = Finding(
            id="find_int_001",
            section_id="exam_int_001",
            finding_type="examination",
            description="Limited shoulder abduction to 90 degrees"
        )
        
        rating = ImpairmentRating(
            id="rating_int_001",
            diagnosis_id="diag_int_001",
            percentage=10,
            ama_table="16-3",
            rationale="Based on ROM limitations per AMA Guides"
        )
        
        medical_findings = MedicalFindings(
            diagnoses=[diagnosis],
            findings=[finding],
            impairment_ratings=[rating],
            imaging_studies=["MRI right shoulder showing calcific deposits"],
            treatment_history=["Physical therapy", "Corticosteroid injection"]
        )
        
        return QMETemplateData(
            patient_info=patient_info,
            medical_findings=medical_findings,
            missing_sections=[],
            recommendations=["Continue conservative treatment"]
        )
    
    @patch('src.services.professional_template_assembler.Document')
    def test_end_to_end_template_assembly(self, mock_document_class):
        """Test complete end-to-end template assembly process."""
        # Mock document
        mock_doc = Mock()
        mock_document_class.return_value = mock_doc
        
        template_data = self.create_complete_template_data()
        
        config = TemplateAssemblyConfig(
            include_quality_indicators=True,
            include_missing_placeholders=True,
            validate_before_assembly=True,
            validate_after_assembly=True,
            generate_quality_report=True
        )
        
        doctor_info = {
            'name': 'Integration Test Doctor',
            'license': 'TEST123',
            'specialty': 'Orthopaedic Surgery',
            'phone': '555-TEST'
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "integration_test_template.docx")
            
            # This should work without raising exceptions
            result = self.assembler.assemble_professional_template(
                template_data=template_data,
                output_path=output_path,
                doctor_info=doctor_info,
                assembly_config=config
            )
            
            # Verify result structure
            assert isinstance(result, ProfessionalTemplateResult)
            assert result.file_path == output_path
            assert result.template_data == template_data
            assert result.assembly_config == config
            
            # Verify validation was performed
            assert result.pre_assembly_validation is not None
            assert result.post_assembly_validation is not None
            
            # Verify file statistics
            assert result.file_size_bytes >= 0
            assert result.page_count >= 0
            assert result.word_count >= 0


if __name__ == "__main__":
    pytest.main([__file__])