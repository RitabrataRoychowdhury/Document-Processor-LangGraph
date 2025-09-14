"""
Professional Template Assembly System with Gold Standard Compliance.

This service creates professional QME templates that exactly match the AI Example QME Report Template.docx
structure and formatting, with comprehensive validation and quality assurance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import tempfile
import uuid
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

try:
    from src.services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.services.qme_rules_engine import QMERulesEngine, ValidationIssue, QualityScore, ValidationSeverity
    from src.services.enhanced_qme_generator import EnhancedQMEResult
    from src.config.qme_gold_standard_config import qme_config
    from src.utils.logging_config import get_logger
except ImportError:
    from services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from services.qme_rules_engine import QMERulesEngine, ValidationIssue, QualityScore, ValidationSeverity
    from services.enhanced_qme_generator import EnhancedQMEResult
    from config.qme_gold_standard_config import qme_config
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TemplateAssemblyConfig:
    """Configuration for template assembly."""
    include_quality_indicators: bool = False
    include_missing_placeholders: bool = True
    apply_professional_formatting: bool = True
    validate_before_assembly: bool = True
    validate_after_assembly: bool = True
    generate_quality_report: bool = True
    output_format: str = "docx"  # docx, pdf
    template_version: str = "1.0"


@dataclass
class AssemblyValidationResult:
    """Result from template assembly validation."""
    is_valid: bool
    validation_issues: List[ValidationIssue]
    quality_score: QualityScore
    missing_sections: List[str]
    placeholder_count: int
    compliance_status: str  # "compliant", "non_compliant", "needs_review"


@dataclass
class ProfessionalTemplateResult:
    """Result from professional template assembly."""
    file_path: str
    template_data: QMETemplateData
    assembly_config: TemplateAssemblyConfig
    pre_assembly_validation: AssemblyValidationResult
    post_assembly_validation: AssemblyValidationResult
    quality_report_path: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    file_size_bytes: int = 0
    page_count: int = 0
    word_count: int = 0


class GoldStandardFormatter:
    """Handles gold standard formatting based on AI Example QME Report Template.docx."""
    
    def __init__(self):
        """Initialize the gold standard formatter."""
        self.formatting_config = qme_config.FORMATTING_REQUIREMENTS
        
    def apply_document_formatting(self, doc: Document) -> None:
        """Apply gold standard document formatting."""
        try:
            # Set document margins
            sections = doc.sections
            for section in sections:
                margins = self.formatting_config['document_structure']['margins']
                section.top_margin = Inches(margins['top'])
                section.bottom_margin = Inches(margins['bottom'])
                section.left_margin = Inches(margins['left'])
                section.right_margin = Inches(margins['right'])
            
            # Apply typography settings
            self._apply_typography_settings(doc)
            
            # Create custom styles
            self._create_custom_styles(doc)
            
            logger.info("Applied gold standard document formatting")
            
        except Exception as e:
            logger.error(f"Error applying document formatting: {e}")
            raise
    
    def _apply_typography_settings(self, doc: Document) -> None:
        """Apply typography settings from gold standard."""
        try:
            typography = self.formatting_config['typography']
            
            # Update Normal style
            normal_style = doc.styles['Normal']
            normal_font = normal_style.font
            normal_font.name = typography['font_family']
            normal_font.size = Pt(typography['font_size'])
            
            # Set paragraph formatting
            normal_paragraph = normal_style.paragraph_format
            normal_paragraph.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            normal_paragraph.line_spacing = typography['line_spacing']
            normal_paragraph.space_after = Pt(typography['paragraph_spacing'])
            
        except Exception as e:
            logger.error(f"Error applying typography settings: {e}")
            raise
    
    def _create_custom_styles(self, doc: Document) -> None:
        """Create custom styles for QME template."""
        try:
            styles = doc.styles
            
            # QME Header style
            if 'QME Header' not in [style.name for style in styles]:
                header_style = styles.add_style('QME Header', WD_STYLE_TYPE.PARAGRAPH)
                header_font = header_style.font
                header_font.name = self.formatting_config['typography']['font_family']
                header_font.size = Pt(16)
                header_font.bold = True
                
                header_paragraph = header_style.paragraph_format
                header_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                header_paragraph.space_before = Pt(12)
                header_paragraph.space_after = Pt(12)
            
            # QME Section Header style
            if 'QME Section Header' not in [style.name for style in styles]:
                section_style = styles.add_style('QME Section Header', WD_STYLE_TYPE.PARAGRAPH)
                section_font = section_style.font
                section_font.name = self.formatting_config['typography']['font_family']
                section_font.size = Pt(14)
                section_font.bold = True
                
                section_paragraph = section_style.paragraph_format
                section_paragraph.space_before = Pt(self.formatting_config['section_formatting']['headers']['spacing_before'])
                section_paragraph.space_after = Pt(self.formatting_config['section_formatting']['headers']['spacing_after'])
            
            # QME Table style
            if 'QME Table' not in [style.name for style in styles]:
                table_style = styles.add_style('QME Table', WD_STYLE_TYPE.TABLE)
                # Table formatting would be applied here
            
        except Exception as e:
            logger.error(f"Error creating custom styles: {e}")
            raise
    
    def create_professional_header(self, doc: Document, doctor_info: Optional[Dict[str, str]] = None) -> None:
        """Create professional header following gold standard."""
        try:
            section = doc.sections[0]
            header = section.header
            
            # Clear existing header
            header_para = header.paragraphs[0]
            header_para.clear()
            
            if doctor_info:
                # Doctor name and title
                name_run = header_para.add_run(f"Dr. {doctor_info.get('name', '[Doctor Name]')}")
                name_run.font.name = self.formatting_config['typography']['font_family']
                name_run.font.size = Pt(12)
                name_run.font.bold = True
                
                header_para.add_run(f", {doctor_info.get('specialty', 'QME')}")
                header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Add second line with license and contact
                license_para = header.add_paragraph()
                license_text = f"License: {doctor_info.get('license', '[License Number]')}"
                if doctor_info.get('phone'):
                    license_text += f" | Phone: {doctor_info['phone']}"
                
                license_para.text = license_text
                license_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                license_font = license_para.runs[0].font
                license_font.name = self.formatting_config['typography']['font_family']
                license_font.size = Pt(10)
            
        except Exception as e:
            logger.error(f"Error creating professional header: {e}")
            raise
    
    def create_professional_footer(self, doc: Document, doctor_info: Optional[Dict[str, str]] = None) -> None:
        """Create professional footer following gold standard."""
        try:
            section = doc.sections[0]
            footer = section.footer
            
            # Clear existing footer
            footer_para = footer.paragraphs[0]
            footer_para.clear()
            
            # Confidentiality notice
            footer_para.text = "CONFIDENTIAL MEDICAL REPORT - QME EVALUATION"
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            footer_font = footer_para.runs[0].font
            footer_font.name = self.formatting_config['typography']['font_family']
            footer_font.size = Pt(10)
            footer_font.italic = True
            
            # Add page numbers
            page_para = footer.add_paragraph()
            page_para.text = "Page "
            page_run = page_para.add_run()
            
            # Add page number field
            fldChar1 = OxmlElement('w:fldChar')
            fldChar1.set(qn('w:fldCharType'), 'begin')
            page_run._r.append(fldChar1)
            
            instrText = OxmlElement('w:instrText')
            instrText.text = "PAGE"
            page_run._r.append(instrText)
            
            fldChar2 = OxmlElement('w:fldChar')
            fldChar2.set(qn('w:fldCharType'), 'end')
            page_run._r.append(fldChar2)
            
            page_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        except Exception as e:
            logger.error(f"Error creating professional footer: {e}")
            raise


class ContentValidator:
    """Validates template content for completeness and compliance."""
    
    def __init__(self):
        """Initialize the content validator."""
        self.rules_engine = QMERulesEngine()
    
    def validate_pre_assembly(self, template_data: QMETemplateData) -> AssemblyValidationResult:
        """Validate template data before assembly."""
        try:
            logger.info("Starting pre-assembly validation")
            
            # Run comprehensive validation
            validation_issues, quality_score = self.rules_engine.validate_qme_report(template_data)
            
            # Check for missing sections
            missing_sections = self._identify_missing_sections(template_data)
            
            # Count placeholders (estimated)
            placeholder_count = self._estimate_placeholder_count(template_data)
            
            # Determine compliance status
            compliance_status = self._determine_compliance_status(validation_issues, quality_score)
            
            # Overall validity
            is_valid = (
                quality_score.overall_score >= 70 and
                len([issue for issue in validation_issues if issue.severity == ValidationSeverity.CRITICAL]) == 0
            )
            
            result = AssemblyValidationResult(
                is_valid=is_valid,
                validation_issues=validation_issues,
                quality_score=quality_score,
                missing_sections=missing_sections,
                placeholder_count=placeholder_count,
                compliance_status=compliance_status
            )
            
            logger.info(f"Pre-assembly validation complete: {len(validation_issues)} issues, quality score: {quality_score.overall_score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in pre-assembly validation: {e}")
            return AssemblyValidationResult(
                is_valid=False,
                validation_issues=[],
                quality_score=QualityScore(overall_score=0, completeness_score=0, accuracy_score=0, compliance_score=0),
                missing_sections=[],
                placeholder_count=0,
                compliance_status="error"
            )
    
    def validate_post_assembly(self, doc_path: str, template_data: QMETemplateData) -> AssemblyValidationResult:
        """Validate assembled document."""
        try:
            logger.info("Starting post-assembly validation")
            
            # Load and analyze document
            doc = Document(doc_path)
            
            # Check document structure
            structure_issues = self._validate_document_structure(doc)
            
            # Check for remaining placeholders
            placeholder_issues = self._check_remaining_placeholders(doc)
            
            # Check formatting compliance
            formatting_issues = self._validate_formatting_compliance(doc)
            
            # Combine all issues
            all_issues = structure_issues + placeholder_issues + formatting_issues
            
            # Calculate post-assembly quality score
            quality_score = self._calculate_post_assembly_quality(doc, all_issues)
            
            # Determine compliance
            compliance_status = self._determine_compliance_status(all_issues, quality_score)
            
            is_valid = len([issue for issue in all_issues if issue.severity == ValidationSeverity.CRITICAL]) == 0
            
            result = AssemblyValidationResult(
                is_valid=is_valid,
                validation_issues=all_issues,
                quality_score=quality_score,
                missing_sections=[],
                placeholder_count=len(placeholder_issues),
                compliance_status=compliance_status
            )
            
            logger.info(f"Post-assembly validation complete: {len(all_issues)} issues")
            return result
            
        except Exception as e:
            logger.error(f"Error in post-assembly validation: {e}")
            return AssemblyValidationResult(
                is_valid=False,
                validation_issues=[],
                quality_score=QualityScore(overall_score=0, completeness_score=0, accuracy_score=0, compliance_score=0),
                missing_sections=[],
                placeholder_count=0,
                compliance_status="error"
            )
    
    def _identify_missing_sections(self, template_data: QMETemplateData) -> List[str]:
        """Identify missing required sections."""
        missing = []
        
        # Check patient info completeness
        if not template_data.patient_info.name:
            missing.append("Patient Name")
        if not template_data.patient_info.case_number:
            missing.append("Case Number")
        if not template_data.patient_info.injury_date:
            missing.append("Injury Date")
        
        # Check medical findings
        if not template_data.medical_findings.diagnoses:
            missing.append("Primary Diagnosis")
        if not template_data.medical_findings.impairment_ratings:
            missing.append("Impairment Rating")
        
        return missing
    
    def _estimate_placeholder_count(self, template_data: QMETemplateData) -> int:
        """Estimate number of placeholders that will be in final document."""
        count = 0
        
        # Count missing patient info fields
        patient_fields = [
            template_data.patient_info.name,
            template_data.patient_info.age,
            template_data.patient_info.gender,
            template_data.patient_info.case_number,
            template_data.patient_info.injury_date,
            template_data.patient_info.employer,
            template_data.patient_info.occupation
        ]
        
        count += sum(1 for field in patient_fields if not field)
        
        # Count missing medical findings
        if not template_data.medical_findings.diagnoses:
            count += 1
        if not template_data.medical_findings.impairment_ratings:
            count += 1
        if not template_data.medical_findings.findings:
            count += 3  # Estimate for examination findings
        
        return count
    
    def _determine_compliance_status(self, issues: List[ValidationIssue], quality_score: QualityScore) -> str:
        """Determine overall compliance status."""
        critical_issues = len([issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL])
        high_issues = len([issue for issue in issues if issue.severity == ValidationSeverity.HIGH])
        
        if critical_issues > 0:
            return "non_compliant"
        elif high_issues > 3 or quality_score.overall_score < 70:
            return "needs_review"
        else:
            return "compliant"
    
    def _validate_document_structure(self, doc: Document) -> List[ValidationIssue]:
        """Validate document structure against gold standard."""
        issues = []
        
        try:
            # Check for required sections by looking for headings
            required_headings = [
                "PATIENT IDENTIFICATION",
                "HISTORY OF PRESENT ILLNESS",
                "PHYSICAL EXAMINATION",
                "DIAGNOSIS",
                "IMPAIRMENT RATING"
            ]
            
            doc_text = "\n".join([para.text for para in doc.paragraphs])
            
            for heading in required_headings:
                if heading not in doc_text:
                    issues.append(ValidationIssue(
                        section=heading.lower().replace(" ", "_"),
                        severity=ValidationSeverity.HIGH,
                        title=f"Missing Required Section: {heading}",
                        description=f"Required section '{heading}' not found in document",
                        suggestions=[f"Add {heading} section to document"]
                    ))
            
        except Exception as e:
            logger.error(f"Error validating document structure: {e}")
        
        return issues
    
    def _check_remaining_placeholders(self, doc: Document) -> List[ValidationIssue]:
        """Check for remaining placeholder text in document."""
        issues = []
        
        try:
            placeholder_patterns = [
                r'\[MISSING[^\]]*\]',
                r'\[ERROR[^\]]*\]',
                r'\[TODO[^\]]*\]',
                r'\+[A-Za-z\s]+\+',  # Template placeholders like +Patient Name+
                r'__+',  # Blank lines
            ]
            
            doc_text = "\n".join([para.text for para in doc.paragraphs])
            
            import re
            for pattern in placeholder_patterns:
                matches = re.findall(pattern, doc_text)
                for match in matches:
                    issues.append(ValidationIssue(
                        section="content_completeness",
                        severity=ValidationSeverity.MEDIUM,
                        title="Placeholder Text Found",
                        description=f"Placeholder text found: {match}",
                        suggestions=["Replace placeholder with actual content"],
                        auto_fixable=False
                    ))
            
        except Exception as e:
            logger.error(f"Error checking placeholders: {e}")
        
        return issues
    
    def _validate_formatting_compliance(self, doc: Document) -> List[ValidationIssue]:
        """Validate formatting compliance with gold standard."""
        issues = []
        
        try:
            # Check margins
            section = doc.sections[0]
            expected_margin = Inches(1.0)
            
            if abs(section.top_margin - expected_margin) > Inches(0.1):
                issues.append(ValidationIssue(
                    section="formatting",
                    severity=ValidationSeverity.LOW,
                    title="Incorrect Top Margin",
                    description=f"Top margin is {section.top_margin.inches:.1f} inches, expected 1.0 inches",
                    suggestions=["Adjust top margin to 1.0 inches"],
                    auto_fixable=True
                ))
            
            # Check font consistency (simplified check)
            font_issues = 0
            for para in doc.paragraphs:
                for run in para.runs:
                    if run.font.name and run.font.name != qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']:
                        font_issues += 1
            
            if font_issues > 0:
                issues.append(ValidationIssue(
                    section="formatting",
                    severity=ValidationSeverity.LOW,
                    title="Inconsistent Font Usage",
                    description=f"Found {font_issues} text runs with non-standard fonts",
                    suggestions=["Apply consistent font formatting throughout document"],
                    auto_fixable=True
                ))
            
        except Exception as e:
            logger.error(f"Error validating formatting: {e}")
        
        return issues
    
    def _calculate_post_assembly_quality(self, doc: Document, issues: List[ValidationIssue]) -> QualityScore:
        """Calculate quality score for assembled document."""
        try:
            # Count different severity levels
            critical_count = len([i for i in issues if i.severity == ValidationSeverity.CRITICAL])
            high_count = len([i for i in issues if i.severity == ValidationSeverity.HIGH])
            medium_count = len([i for i in issues if i.severity == ValidationSeverity.MEDIUM])
            low_count = len([i for i in issues if i.severity == ValidationSeverity.LOW])
            
            # Calculate scores (simplified scoring)
            completeness_score = max(0, 100 - (critical_count * 25) - (high_count * 10) - (medium_count * 5))
            accuracy_score = max(0, 100 - (critical_count * 30) - (high_count * 15))
            compliance_score = max(0, 100 - (critical_count * 40) - (high_count * 20) - (medium_count * 5))
            
            overall_score = (completeness_score + accuracy_score + compliance_score) / 3
            
            return QualityScore(
                overall_score=overall_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                compliance_score=compliance_score,
                total_issues=len(issues),
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return QualityScore(
                overall_score=0,
                completeness_score=0,
                accuracy_score=0,
                compliance_score=0
            )


class ProfessionalTemplateAssembler:
    """Main service for assembling professional QME templates with gold standard compliance."""
    
    def __init__(self):
        """Initialize the professional template assembler."""
        self.formatter = GoldStandardFormatter()
        self.validator = ContentValidator()
        
        logger.info("Initialized Professional Template Assembler")
    
    def assemble_professional_template(self,
                                     template_data: QMETemplateData,
                                     output_path: Optional[str] = None,
                                     doctor_info: Optional[Dict[str, str]] = None,
                                     assembly_config: Optional[TemplateAssemblyConfig] = None) -> ProfessionalTemplateResult:
        """
        Assemble a professional QME template with gold standard compliance.
        
        Args:
            template_data: QME template data
            output_path: Optional output file path
            doctor_info: Doctor information for template
            assembly_config: Assembly configuration options
            
        Returns:
            ProfessionalTemplateResult with assembled template and validation results
        """
        try:
            logger.info("Starting professional template assembly")
            
            # Use default config if not provided
            if assembly_config is None:
                assembly_config = TemplateAssemblyConfig()
            
            # Pre-assembly validation
            pre_validation = None
            if assembly_config.validate_before_assembly:
                pre_validation = self.validator.validate_pre_assembly(template_data)
                
                if not pre_validation.is_valid and assembly_config.validate_before_assembly:
                    logger.warning(f"Pre-assembly validation failed with {len(pre_validation.validation_issues)} issues")
            
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                patient_name = template_data.patient_info.name or "Unknown"
                safe_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"QME_Report_{safe_name}_{timestamp}.docx"
            
            # Create the document
            doc_path = self._create_professional_document(
                template_data, output_path, doctor_info, assembly_config
            )
            
            # Post-assembly validation
            post_validation = None
            if assembly_config.validate_after_assembly:
                post_validation = self.validator.validate_post_assembly(doc_path, template_data)
            
            # Generate quality report
            quality_report_path = None
            if assembly_config.generate_quality_report:
                quality_report_path = self._generate_quality_report(
                    template_data, pre_validation, post_validation, doc_path
                )
            
            # Get file statistics
            file_stats = self._get_file_statistics(doc_path)
            
            # Create result
            result = ProfessionalTemplateResult(
                file_path=doc_path,
                template_data=template_data,
                assembly_config=assembly_config,
                pre_assembly_validation=pre_validation or AssemblyValidationResult(
                    is_valid=True, validation_issues=[], quality_score=QualityScore(0,0,0,0), 
                    missing_sections=[], placeholder_count=0, compliance_status="not_validated"
                ),
                post_assembly_validation=post_validation or AssemblyValidationResult(
                    is_valid=True, validation_issues=[], quality_score=QualityScore(0,0,0,0),
                    missing_sections=[], placeholder_count=0, compliance_status="not_validated"
                ),
                quality_report_path=quality_report_path,
                file_size_bytes=file_stats['size'],
                page_count=file_stats['pages'],
                word_count=file_stats['words']
            )
            
            logger.info(f"Professional template assembly complete: {doc_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error assembling professional template: {e}")
            raise  
  
    def _create_professional_document(self,
                                    template_data: QMETemplateData,
                                    output_path: str,
                                    doctor_info: Optional[Dict[str, str]],
                                    assembly_config: TemplateAssemblyConfig) -> str:
        """Create the professional DOCX document."""
        try:
            # Create new document
            doc = Document()
            
            # Apply gold standard formatting
            self.formatter.apply_document_formatting(doc)
            
            # Add professional header and footer
            self.formatter.create_professional_header(doc, doctor_info)
            self.formatter.create_professional_footer(doc, doctor_info)
            
            # Add document title
            self._add_document_title(doc, template_data)
            
            # Add quality indicators if requested
            if assembly_config.include_quality_indicators:
                self._add_quality_indicators_section(doc, template_data)
            
            # Add all required sections in gold standard order
            self._add_patient_identification_section(doc, template_data, assembly_config)
            self._add_history_sections(doc, template_data, assembly_config)
            self._add_physical_examination_section(doc, template_data, assembly_config)
            self._add_diagnostic_studies_section(doc, template_data, assembly_config)
            self._add_diagnosis_section(doc, template_data, assembly_config)
            self._add_impairment_rating_section(doc, template_data, assembly_config)
            self._add_work_restrictions_section(doc, template_data, assembly_config)
            self._add_future_medical_care_section(doc, template_data, assembly_config)
            self._add_causation_analysis_section(doc, template_data, assembly_config)
            self._add_apportionment_section(doc, template_data, assembly_config)
            self._add_signature_section(doc, doctor_info)
            
            # Save document
            doc.save(output_path)
            
            logger.info(f"Professional document created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating professional document: {e}")
            raise
    
    def _add_document_title(self, doc: Document, template_data: QMETemplateData) -> None:
        """Add document title following gold standard format."""
        try:
            # Main title
            title_para = doc.add_paragraph()
            title_run = title_para.add_run("PANEL QUALIFIED MEDICAL EVALUATION")
            title_run.font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            title_run.font.size = Pt(16)
            title_run.font.bold = True
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Specialty subtitle
            subtitle_para = doc.add_paragraph()
            subtitle_run = subtitle_para.add_run("IN THE SPECIALTY OF ORTHOPAEDIC SURGERY")
            subtitle_run.font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            subtitle_run.font.size = Pt(14)
            subtitle_run.font.bold = True
            subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Date and case information
            doc.add_paragraph()  # Spacing
            
            case_info = [
                f"Date: {datetime.now().strftime('%B %d, %Y')}",
                f"Patient: {template_data.patient_info.name or '[Patient Name Required]'}",
                f"Case No.: {template_data.patient_info.case_number or '[Case Number Required]'}",
                f"Date of Injury: {template_data.patient_info.injury_date.strftime('%B %d, %Y') if template_data.patient_info.injury_date else '[Injury Date Required]'}"
            ]
            
            for info in case_info:
                info_para = doc.add_paragraph(info)
                info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            doc.add_paragraph()  # Spacing
            
        except Exception as e:
            logger.error(f"Error adding document title: {e}")
            raise    
    
    def _add_quality_indicators_section(self, doc: Document, template_data: QMETemplateData) -> None:
        """Add quality indicators section for draft review."""
        try:
            # Quality assessment header
            quality_heading = doc.add_paragraph()
            quality_run = quality_heading.add_run("DRAFT - QUALITY ASSESSMENT")
            quality_run.font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            quality_run.font.size = Pt(14)
            quality_run.font.bold = True
            quality_run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
            quality_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Quality indicators
            doc.add_paragraph("This section will be removed in the final version.")
            
            # Missing information summary
            missing_sections = self.validator._identify_missing_sections(template_data)
            if missing_sections:
                missing_para = doc.add_paragraph()
                missing_para.add_run("Missing Information: ").bold = True
                missing_para.add_run(", ".join(missing_sections))
            
            doc.add_page_break()
            
        except Exception as e:
            logger.error(f"Error adding quality indicators: {e}")
            raise
    
    # def _add_patient_identification_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
    # """Add patient identification section following gold standard."""
    # try:
    # # Section header
    # self._add_section_header(doc, "IDENTIFYING DATA")
    #     # patient_info = template_data.patient_info
    #     # # Patient description paragraph
    # description_parts = []
    #     # # Name and age
    # if patient_info.name and patient_info.age:
    # description_parts.append(f"Mr./Ms. {patient_info.name} is a {patient_info.age}-year-old")
    # elif patient_info.name:
    # description_parts.append(f"Mr./Ms. {patient_info.name} is a")
    # if config.include_missing_placeholders:
    # description_parts.append("[AGE REQUIRED]")
    # else:
    # if config.include_missing_placeholders:
    # description_parts.append("[PATIENT NAME REQUIRED] is a [AGE REQUIRED]-year-old")
    #     # # Gender and other details
    # gender_text = patient_info.gender or ("[GENDER REQUIRED]" if config.include_missing_placeholders else "")
    # if gender_text:
    # description_parts.append(gender_text.lower())
    #     # # Occupation and employer
    # if patient_info.occupation:
    # description_parts.append(f"who works as a {patient_info.occupation}")
    # if patient_info.employer:
    # description_parts.append(f"for {patient_info.employer}")
    # elif config.include_missing_placeholders:
    # description_parts.append("who works as [OCCUPATION REQUIRED] for [EMPLOYER REQUIRED]")
    #     # # Injury information
    # if patient_info.injury_date:
    # injury_text = f"The patient sustained an injury on {patient_info.injury_date.strftime('%B %d, %Y')}"
    # if patient_info.body_parts:
    # injury_text += f" involving the {', '.join(patient_info.body_parts)}"
    # description_parts.append(injury_text + ".")
    # elif config.include_missing_placeholders:
    # description_parts.append("The patient sustained an injury on [INJURY DATE REQUIRED] involving [BODY PARTS REQUIRED].")
    #     # # Create paragraph
    # description_text = " ".join(description_parts)
    # doc.add_paragraph(description_text)
    #     # # Case information table
    # self._add_case_information_table(doc, patient_info, config)
    #     # except Exception as e:
    # logger.error(f"Error adding patient identification section: {e}")
    # raise    def _add_case_information_table(self, doc: Document, patient_info: PatientInfo, config: TemplateAssemblyConfig) -> None:
    # """Add case information table."""
    # try:
    # # Create table
    # table = doc.add_table(rows=6, cols=2)
    # table.style = 'Table Grid'
    # table.alignment = WD_TABLE_ALIGNMENT.LEFT
    #     # # Table data
    # table_data = [
    # ("Case Number:", patient_info.case_number or ("[CASE NUMBER REQUIRED]" if config.include_missing_placeholders else "")),
    # ("Date of Birth:", "[DATE OF BIRTH REQUIRED]" if config.include_missing_placeholders else ""),
    # ("Date of Injury:", patient_info.injury_date.strftime('%m/%d/%Y') if patient_info.injury_date else ("[INJURY DATE REQUIRED]" if config.include_missing_placeholders else "")),
    # ("Employer:", patient_info.employer or ("[EMPLOYER REQUIRED]" if config.include_missing_placeholders else "")),
    # ("Occupation:", patient_info.occupation or ("[OCCUPATION REQUIRED]" if config.include_missing_placeholders else "")),
    # ("Medical Record Number:", patient_info.medical_record_number or ("[MRN OPTIONAL]" if config.include_missing_placeholders else ""))
    # ]
    #     # # Populate table
    # for i, (label, value) in enumerate(table_data):
    # # Label cell
    # label_cell = table.cell(i, 0)
    # label_para = label_cell.paragraphs[0]
    # label_run = label_para.add_run(label)
    # label_run.font.bold = True
    #     # # Value cell
    # value_cell = table.cell(i, 1)
    # value_para = value_cell.paragraphs[0]
    # value_run = value_para.add_run(value)
    # # Highlight missing information
    # if "[" in value and "REQUIRED" in value:
    
    def _add_history_sections(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add history sections following gold standard structure."""
        try:
            # History of Present Illness
            self._add_section_header(doc, "HISTORY OF INJURY AS DESCRIBED BY INJURED WORKER")
            
            hpi_content = self._generate_history_content(template_data, config)
            doc.add_paragraph(hpi_content)
            
            # Job Description
            self._add_section_header(doc, "JOB DESCRIPTION")
            job_content = self._generate_job_description(template_data, config)
            doc.add_paragraph(job_content)
            
            # Current Condition
            self._add_section_header(doc, "CURRENT CONDITION")
            current_content = self._generate_current_condition(template_data, config)
            doc.add_paragraph(current_content)
            
            # Current Employment
            self._add_section_header(doc, "CURRENT EMPLOYMENT")
            employment_content = self._generate_current_employment(template_data, config)
            doc.add_paragraph(employment_content)
            
            # Current Treatment
            self._add_section_header(doc, "CURRENT TREATMENT")
            treatment_content = self._generate_current_treatment(template_data, config)
            doc.add_paragraph(treatment_content)
            
            # Prior Injuries
            self._add_section_header(doc, "PRIOR INJURIES")
            self._add_subsection_header(doc, "Industrial injuries:")
            doc.add_paragraph("[INDUSTRIAL INJURY HISTORY REQUIRED]" if config.include_missing_placeholders else "")
            
            self._add_subsection_header(doc, "Nonindustrial injuries:")
            doc.add_paragraph("[NON-INDUSTRIAL INJURY HISTORY REQUIRED]" if config.include_missing_placeholders else "")
            
            # Occupational History
            self._add_section_header(doc, "OCCUPATIONAL HISTORY")
            occ_content = self._generate_occupational_history(template_data, config)
            doc.add_paragraph(occ_content)
            
        except Exception as e:
            logger.error(f"Error adding history sections: {e}")
            raise
    
    def _generate_history_content(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate history of present illness content."""
        try:
            content_parts = []
            
            patient_info = template_data.patient_info
            
            # Injury description
            if patient_info.injury_date:
                content_parts.append(f"The applicant states that on {patient_info.injury_date.strftime('%B %d, %Y')}")
            elif config.include_missing_placeholders:
                content_parts.append("The applicant states that on [INJURY DATE REQUIRED]")
            
            # Add injury mechanism if available from findings
            if template_data.medical_findings.findings:
                injury_findings = [f.description for f in template_data.medical_findings.findings if 'injury' in f.description.lower()]
                if injury_findings:
                    content_parts.append(f"while {injury_findings[0].lower()}")
            elif config.include_missing_placeholders:
                content_parts.append("[INJURY MECHANISM AND DETAILS REQUIRED]")
            
            if not content_parts and config.include_missing_placeholders:
                return "[DETAILED HISTORY OF PRESENT ILLNESS REQUIRED - Include injury mechanism, initial symptoms, symptom progression, current complaints, and functional limitations]"
            
            return " ".join(content_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating history content: {e}")
            return "[ERROR GENERATING HISTORY CONTENT]" if config.include_missing_placeholders else ""
    
    def _generate_job_description(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate job description content."""
        if template_data.patient_info.occupation:
            return f"The applicant works as a {template_data.patient_info.occupation}. [DETAILED JOB DUTIES AND PHYSICAL DEMANDS REQUIRED]"
        elif config.include_missing_placeholders:
            return "[JOB DESCRIPTION INCLUDING PHYSICAL DEMANDS AND WORK ENVIRONMENT REQUIRED]"
        return ""
    
    def _generate_current_condition(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate current condition content."""
        if template_data.medical_findings.findings:
            symptoms = [f.description for f in template_data.medical_findings.findings[:3]]
            return f"The applicant reports {', '.join(symptoms)}."
        elif config.include_missing_placeholders:
            return "[CURRENT SYMPTOMS AND FUNCTIONAL STATUS REQUIRED]"
        return ""
    
    def _generate_current_employment(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate current employment content."""
        if config.include_missing_placeholders:
            return "[CURRENT EMPLOYMENT STATUS - Same employer or new employer? Working full or modified duties? Collecting any benefits?]"
        return ""
    
    def _generate_current_treatment(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate current treatment content."""
        if template_data.medical_findings.treatment_history:
            return f"The applicant is currently receiving {', '.join(template_data.medical_findings.treatment_history)}."
        elif config.include_missing_placeholders:
            return "The applicant is currently not receiving any treatment.\n\nOR\n\nThe applicant is currently seeing [CURRENT TREATING PHYSICIAN REQUIRED]"
        return ""
    
    def _generate_occupational_history(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate occupational history content."""
        content = ""
        if template_data.patient_info.occupation and template_data.patient_info.employer:
            content = f"Current: {template_data.patient_info.occupation} at {template_data.patient_info.employer}. "
        
        if config.include_missing_placeholders:
            content += "[MINIMUM 10 YEARS OF EMPLOYMENT HISTORY REQUIRED]"
        
        return content or ("[OCCUPATIONAL HISTORY REQUIRED]" if config.include_missing_placeholders else "")   
 
    def _add_physical_examination_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add physical examination section with ROM tables."""
        try:
            self._add_section_header(doc, "PHYSICAL EXAMINATION")
            
            # General appearance
            self._add_subsection_header(doc, "GENERAL")
            general_content = self._generate_general_examination(template_data, config)
            doc.add_paragraph(general_content)
            
            # Vitals table
            self._add_subsection_header(doc, "VITALS")
            self._add_vitals_table(doc, config)
            
            # Spine examination sections
            spine_sections = ["CERVICAL SPINE", "THORACIC SPINE", "LUMBAR SPINE"]
            
            for spine_section in spine_sections:
                self._add_subsection_header(doc, spine_section)
                
                # Inspection and palpation
                inspection_content = self._generate_spine_inspection(spine_section, template_data, config)
                doc.add_paragraph(inspection_content)
                
                # Range of motion tables
                self._add_spine_rom_tables(doc, spine_section, config)
            
            # Neurological examination
            self._add_subsection_header(doc, "NEUROLOGICAL EXAMINATION")
            neuro_content = self._generate_neurological_examination(template_data, config)
            doc.add_paragraph(neuro_content)
            
            # Add neurological tables
            self._add_neurological_tables(doc, config)
            
        except Exception as e:
            logger.error(f"Error adding physical examination section: {e}")
            raise
    
    def _generate_general_examination(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate general examination content."""
        if config.include_missing_placeholders:
            return "[GENERAL APPEARANCE, DISTRESS LEVEL, COOPERATION, AND GAIT OBSERVATION REQUIRED]"
        return ""
    
    def _add_vitals_table(self, doc: Document, config: TemplateAssemblyConfig) -> None:
        """Add vitals table."""
        try:
            table = doc.add_table(rows=4, cols=2)
            table.style = 'Table Grid'
            
            vitals = [
                ("Temperature", "[TEMP]" if config.include_missing_placeholders else ""),
                ("Heart Rate", "[HR]" if config.include_missing_placeholders else ""),
                ("Respiratory Rate", "[RR]" if config.include_missing_placeholders else ""),
                ("Blood Pressure", "[BP]" if config.include_missing_placeholders else "")
            ]
            
            for i, (vital, value) in enumerate(vitals):
                table.cell(i, 0).text = vital
                table.cell(i, 1).text = value
            
            doc.add_paragraph()  # Spacing
            
        except Exception as e:
            logger.error(f"Error adding vitals table: {e}")
            raise
    
    def _generate_spine_inspection(self, spine_section: str, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate spine inspection content."""
        base_text = "Normal alignment without visible deformity, no spasms observed, skin intact, no surgical scars."
        
        if config.include_missing_placeholders:
            base_text += "\n\n[DETAILED PALPATION FINDINGS REQUIRED]\n[MUSCLE SPASM AND TENDERNESS ASSESSMENT REQUIRED]"
        
        return base_text
    
    def _add_spine_rom_tables(self, doc: Document, spine_section: str, config: TemplateAssemblyConfig) -> None:
        """Add range of motion tables for spine sections."""
        try:
            movements = {
                "CERVICAL SPINE": ["FLEXION", "EXTENSION", "RIGHT LATERAL BENDING", "LEFT LATERAL BENDING", "ROTATION"],
                "THORACIC SPINE": ["FLEXION", "EXTENSION", "RIGHT LATERAL ROTATION", "LEFT LATERAL ROTATION"],
                "LUMBAR SPINE": ["FLEXION", "EXTENSION", "RIGHT LATERAL BENDING", "LEFT LATERAL BENDING"]
            }
            
            for movement in movements.get(spine_section, []):
                # Movement header
                movement_header = f"{spine_section} {movement}"
                self._add_subsection_header(doc, movement_header)
                
                # ROM table
                table = doc.add_table(rows=4, cols=5)
                table.style = 'Table Grid'
                
                # Headers
                headers = ["", "1st Measure", "2nd Measure", "3rd Measure", "Average"]
                for i, header in enumerate(headers):
                    cell = table.cell(0, i)
                    cell.text = header
                    if header:
                        cell.paragraphs[0].runs[0].font.bold = True
                
                # Angle measurements (simplified for cervical)
                if "CERVICAL" in spine_section:
                    angle_types = ["Calvarium Angle", "T1 Angle", f"{movement.title()} Angle"]
                elif "THORACIC" in spine_section:
                    angle_types = ["T1 Angle", "T12 Angle", f"{movement.title()} Angle"]
                else:  # LUMBAR
                    angle_types = ["T12 Angle", "Sacral Angle", f"{movement.title()} Angle"]
                
                for i, angle_type in enumerate(angle_types, 1):
                    table.cell(i, 0).text = angle_type
                    if i == len(angle_types):  # Last row (actual measurement)
                        table.cell(i, 0).paragraphs[0].runs[0].font.bold = True
                    
                    # Add placeholder values
                    if config.include_missing_placeholders:
                        for j in range(1, 5):
                            table.cell(i, j).text = "[°]"
                
                doc.add_paragraph()  # Spacing
            
            # Add measurement note
            if config.include_missing_placeholders:
                note_para = doc.add_paragraph()
                note_para.text = "Spine range of motion values obtained after appropriate warm-up and with adequate motivational instruction. The applicant was compliant and put forth a strong effort to achieve the highest possible motion for measurement. Two inclinometers were utilized for measurements and the values recorded above."
            
        except Exception as e:
            logger.error(f"Error adding spine ROM tables: {e}")
            raise 
   
    def _generate_neurological_examination(self, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> str:
        """Generate neurological examination content."""
        if config.include_missing_placeholders:
            return "[DETAILED NEUROLOGICAL EXAMINATION INCLUDING SENSORY TESTING, MOTOR FUNCTION, REFLEXES, AND COORDINATION REQUIRED]"
        return ""
    
    def _add_neurological_tables(self, doc: Document, config: TemplateAssemblyConfig) -> None:
        """Add neurological examination tables."""
        try:
            # Sensory and Motor table
            self._add_subsection_header(doc, "CERVICAL SPINE SENSORY AND MOTOR")
            
            table = doc.add_table(rows=7, cols=5)
            table.style = 'Table Grid'
            
            # Headers
            headers = ["", "SENSORY", "", "MOTOR", ""]
            subheaders = ["", "RIGHT", "LEFT", "RIGHT", "LEFT"]
            
            for i, header in enumerate(headers):
                table.cell(0, i).text = header
                if header:
                    table.cell(0, i).paragraphs[0].runs[0].font.bold = True
            
            for i, subheader in enumerate(subheaders):
                table.cell(1, i).text = subheader
                if subheader:
                    table.cell(1, i).paragraphs[0].runs[0].font.bold = True
            
            # Nerve levels
            nerve_levels = ["C4", "C5", "C6", "C7", "C8", "T1"]
            for i, level in enumerate(nerve_levels, 2):
                table.cell(i, 0).text = level
                table.cell(i, 0).paragraphs[0].runs[0].font.bold = True
                
                if config.include_missing_placeholders:
                    table.cell(i, 1).text = "Intact"
                    table.cell(i, 2).text = "Intact"
                    table.cell(i, 3).text = "5"
                    table.cell(i, 4).text = "5"
            
            doc.add_paragraph()  # Spacing
            
            # Reflexes table
            self._add_subsection_header(doc, "CERVICAL SPINE REFLEXES")
            
            reflex_table = doc.add_table(rows=4, cols=3)
            reflex_table.style = 'Table Grid'
            
            # Headers
            reflex_table.cell(0, 0).text = ""
            reflex_table.cell(0, 1).text = "RIGHT"
            reflex_table.cell(0, 2).text = "LEFT"
            
            for i in range(3):
                reflex_table.cell(0, i).paragraphs[0].runs[0].font.bold = True
            
            # Reflex data
            reflexes = ["C5 (biceps)", "C6 (brachioradialis)", "C7 (triceps)"]
            for i, reflex in enumerate(reflexes, 1):
                reflex_table.cell(i, 0).text = reflex
                if config.include_missing_placeholders:
                    reflex_table.cell(i, 1).text = "2+"
                    reflex_table.cell(i, 2).text = "2+"
            
            doc.add_paragraph()  # Spacing
            
        except Exception as e:
            logger.error(f"Error adding neurological tables: {e}")
            raise
    
    def _add_diagnostic_studies_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add diagnostic studies section."""
        try:
            self._add_section_header(doc, "DIAGNOSTIC STUDIES")
            
            if template_data.medical_findings.imaging_studies:
                for study in template_data.medical_findings.imaging_studies:
                    doc.add_paragraph(f"• {study}")
            elif config.include_missing_placeholders:
                doc.add_paragraph("[REVIEW OF DIAGNOSTIC STUDIES INCLUDING IMAGING AND LABORATORY TESTS REQUIRED]")
            else:
                doc.add_paragraph("No diagnostic studies available for review.")
            
        except Exception as e:
            logger.error(f"Error adding diagnostic studies section: {e}")
            raise
    
    def _add_diagnosis_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add diagnosis section."""
        try:
            self._add_section_header(doc, "DIAGNOSIS")
            
            if template_data.medical_findings.diagnoses:
                for i, diagnosis in enumerate(template_data.medical_findings.diagnoses, 1):
                    diag_para = doc.add_paragraph()
                    diag_para.add_run(f"{i}. ").bold = True
                    diag_para.add_run(diagnosis.description)
                    
                    if diagnosis.icd_code:
                        diag_para.add_run(f" (ICD-10: {diagnosis.icd_code})")
                    elif config.include_missing_placeholders:
                        icd_run = diag_para.add_run(" [ICD-10 CODE REQUIRED]")
                        icd_run.font.color.rgb = RGBColor(255, 0, 0)
            elif config.include_missing_placeholders:
                missing_para = doc.add_paragraph()
                missing_run = missing_para.add_run("[PRIMARY DIAGNOSIS WITH ICD-10 CODE REQUIRED]")
                missing_run.font.color.rgb = RGBColor(255, 0, 0)
            
        except Exception as e:
            logger.error(f"Error adding diagnosis section: {e}")
            raise
    
    def _add_impairment_rating_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add impairment rating section."""
        try:
            self._add_section_header(doc, "IMPAIRMENT RATING")
            
            if template_data.medical_findings.impairment_ratings:
                for rating in template_data.medical_findings.impairment_ratings:
                    # Rating percentage
                    rating_para = doc.add_paragraph()
                    rating_para.add_run("Impairment Rating: ").bold = True
                    rating_para.add_run(f"{rating.percentage}% whole person impairment")
                    
                    # AMA reference
                    if rating.ama_table:
                        ama_para = doc.add_paragraph()
                        ama_para.add_run("AMA Reference: ").bold = True
                        ama_para.add_run(f"AMA Guides to the Evaluation of Permanent Impairment, 5th Edition, Table {rating.ama_table}")
                    elif config.include_missing_placeholders:
                        ama_para = doc.add_paragraph()
                        ama_para.add_run("AMA Reference: ").bold = True
                        ama_run = ama_para.add_run("[AMA TABLE REFERENCE REQUIRED]")
                        ama_run.font.color.rgb = RGBColor(255, 0, 0)
                    
                    # Methodology
                    if rating.rationale:
                        method_para = doc.add_paragraph()
                        method_para.add_run("Methodology: ").bold = True
                        method_para.add_run(rating.rationale)
                    elif config.include_missing_placeholders:
                        method_para = doc.add_paragraph()
                        method_para.add_run("Methodology: ").bold = True
                        method_run = method_para.add_run("[DETAILED CALCULATION METHODOLOGY REQUIRED]")
                        method_run.font.color.rgb = RGBColor(255, 0, 0)
            elif config.include_missing_placeholders:
                missing_para = doc.add_paragraph()
                missing_run = missing_para.add_run("[IMPAIRMENT RATING CALCULATION USING AMA GUIDES 5TH EDITION REQUIRED]")
                missing_run.font.color.rgb = RGBColor(255, 0, 0)
            
        except Exception as e:
            logger.error(f"Error adding impairment rating section: {e}")
            raise 
   
    def _add_work_restrictions_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add work restrictions section."""
        try:
            self._add_section_header(doc, "WORK RESTRICTIONS")
            
            if config.include_missing_placeholders:
                doc.add_paragraph("[SPECIFIC WORK RESTRICTIONS AND LIMITATIONS BASED ON EXAMINATION FINDINGS REQUIRED]")
                
                # Add standard restriction categories
                restriction_categories = [
                    "Lifting restrictions: [SPECIFY WEIGHT LIMITS]",
                    "Carrying restrictions: [SPECIFY LIMITATIONS]", 
                    "Pushing/pulling restrictions: [SPECIFY LIMITATIONS]",
                    "Postural restrictions: [SPECIFY LIMITATIONS]",
                    "Environmental restrictions: [SPECIFY LIMITATIONS]",
                    "Repetitive motion restrictions: [SPECIFY LIMITATIONS]"
                ]
                
                for restriction in restriction_categories:
                    doc.add_paragraph(f"• {restriction}")
            else:
                doc.add_paragraph("Work restrictions to be determined based on examination findings.")
            
        except Exception as e:
            logger.error(f"Error adding work restrictions section: {e}")
            raise
    
    def _add_future_medical_care_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add future medical care section."""
        try:
            self._add_section_header(doc, "FUTURE MEDICAL CARE")
            
            if config.include_missing_placeholders:
                doc.add_paragraph("[FUTURE MEDICAL CARE RECOMMENDATIONS BASED ON DIAGNOSIS AND PROGNOSIS REQUIRED]")
                
                # Add standard care categories
                care_categories = [
                    "Ongoing treatment: [SPECIFY TREATMENTS]",
                    "Medications: [SPECIFY MEDICATIONS AND DURATION]",
                    "Physical therapy: [SPECIFY TYPE AND DURATION]",
                    "Diagnostic studies: [SPECIFY FOLLOW-UP STUDIES]",
                    "Surgical interventions: [IF APPLICABLE]",
                    "Medical equipment: [IF APPLICABLE]"
                ]
                
                for care in care_categories:
                    doc.add_paragraph(f"• {care}")
            else:
                doc.add_paragraph("Future medical care recommendations to be determined based on diagnosis and prognosis.")
            
        except Exception as e:
            logger.error(f"Error adding future medical care section: {e}")
            raise
    
    def _add_causation_analysis_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add causation analysis section."""
        try:
            self._add_section_header(doc, "CAUSATION ANALYSIS")
            
            if config.include_missing_placeholders:
                doc.add_paragraph("[MEDICAL CAUSATION ANALYSIS WITH REASONABLE MEDICAL PROBABILITY STATEMENT REQUIRED]")
                
                analysis_elements = [
                    "Industrial causation: [ANALYSIS OF WORK-RELATED FACTORS]",
                    "Pre-existing conditions: [ASSESSMENT OF NON-INDUSTRIAL FACTORS]",
                    "Temporal relationship: [ANALYSIS OF TIMING]",
                    "Medical probability: [STATEMENT OF REASONABLE MEDICAL PROBABILITY]"
                ]
                
                for element in analysis_elements:
                    doc.add_paragraph(f"• {element}")
            else:
                doc.add_paragraph("Causation analysis to be provided based on examination findings and medical history.")
            
        except Exception as e:
            logger.error(f"Error adding causation analysis section: {e}")
            raise
    
    def _add_apportionment_section(self, doc: Document, template_data: QMETemplateData, config: TemplateAssemblyConfig) -> None:
        """Add apportionment section."""
        try:
            self._add_section_header(doc, "APPORTIONMENT")
            
            if config.include_missing_placeholders:
                doc.add_paragraph("[APPORTIONMENT ANALYSIS CONSIDERING PRE-EXISTING CONDITIONS AND OTHER FACTORS REQUIRED]")
                
                apportionment_elements = [
                    "Industrial factors: [PERCENTAGE AND RATIONALE]",
                    "Non-industrial factors: [PERCENTAGE AND RATIONALE]",
                    "Pre-existing conditions: [ASSESSMENT AND PERCENTAGE]",
                    "Legal basis: [LC 4663/4664 REFERENCES AS APPLICABLE]"
                ]
                
                for element in apportionment_elements:
                    doc.add_paragraph(f"• {element}")
            else:
                doc.add_paragraph("Apportionment analysis to be provided if applicable based on examination findings.")
            
        except Exception as e:
            logger.error(f"Error adding apportionment section: {e}")
            raise
    
    def _add_signature_section(self, doc: Document, doctor_info: Optional[Dict[str, str]]) -> None:
        """Add signature section."""
        try:
            doc.add_paragraph()  # Spacing
            doc.add_paragraph()  # More spacing
            
            # Signature line
            sig_para = doc.add_paragraph()
            sig_para.text = "_" * 50
            
            # Doctor name and title
            if doctor_info:
                name_para = doc.add_paragraph()
                name_para.text = f"Dr. {doctor_info.get('name', '[Doctor Name]')}"
                name_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
                title_para = doc.add_paragraph()
                title_para.text = f"Qualified Medical Evaluator"
                title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
                if doctor_info.get('license'):
                    license_para = doc.add_paragraph()
                    license_para.text = f"Medical License: {doctor_info['license']}"
                    license_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                name_para = doc.add_paragraph()
                name_para.text = "[Doctor Name]"
                name_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
                title_para = doc.add_paragraph()
                title_para.text = "Qualified Medical Evaluator"
                title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
        except Exception as e:
            logger.error(f"Error adding signature section: {e}")
            raise
    
    def _add_section_header(self, doc: Document, title: str) -> None:
        """Add a section header with gold standard formatting."""
        try:
            header_para = doc.add_paragraph()
            header_run = header_para.add_run(title)
            header_run.font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            header_run.font.size = Pt(12)
            header_run.font.bold = True
            header_run.font.underline = True
            
            header_para.space_before = Pt(12)
            header_para.space_after = Pt(6)
            
        except Exception as e:
            logger.error(f"Error adding section header: {e}")
            raise
    
    def _add_subsection_header(self, doc: Document, title: str) -> None:
        """Add a subsection header."""
        try:
            header_para = doc.add_paragraph()
            header_run = header_para.add_run(title)
            header_run.font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            header_run.font.size = Pt(12)
            header_run.font.bold = True
            
            header_para.space_before = Pt(6)
            header_para.space_after = Pt(3)
            
        except Exception as e:
            logger.error(f"Error adding subsection header: {e}")
            raise    

    def _generate_quality_report(self,
                                template_data: QMETemplateData,
                                pre_validation: Optional[AssemblyValidationResult],
                                post_validation: Optional[AssemblyValidationResult],
                                doc_path: str) -> str:
        """Generate comprehensive quality report."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = doc_path.replace('.docx', f'_quality_report_{timestamp}.txt')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("QME TEMPLATE QUALITY REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Template File: {os.path.basename(doc_path)}\n")
                f.write(f"Patient: {template_data.patient_info.name or 'Unknown'}\n\n")
                
                # Pre-assembly validation
                if pre_validation:
                    f.write("PRE-ASSEMBLY VALIDATION\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Overall Score: {pre_validation.quality_score.overall_score:.1f}/100\n")
                    f.write(f"Completeness: {pre_validation.quality_score.completeness_score:.1f}/100\n")
                    f.write(f"Compliance: {pre_validation.quality_score.compliance_score:.1f}/100\n")
                    f.write(f"Status: {pre_validation.compliance_status}\n")
                    f.write(f"Issues Found: {len(pre_validation.validation_issues)}\n")
                    
                    if pre_validation.validation_issues:
                        f.write("\nPre-Assembly Issues:\n")
                        for issue in pre_validation.validation_issues[:10]:  # Top 10 issues
                            f.write(f"  • [{issue.severity.value.upper()}] {issue.title}\n")
                            f.write(f"    {issue.description}\n")
                    f.write("\n")
                
                # Post-assembly validation
                if post_validation:
                    f.write("POST-ASSEMBLY VALIDATION\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Overall Score: {post_validation.quality_score.overall_score:.1f}/100\n")
                    f.write(f"Status: {post_validation.compliance_status}\n")
                    f.write(f"Issues Found: {len(post_validation.validation_issues)}\n")
                    f.write(f"Placeholders Remaining: {post_validation.placeholder_count}\n")
                    
                    if post_validation.validation_issues:
                        f.write("\nPost-Assembly Issues:\n")
                        for issue in post_validation.validation_issues[:10]:  # Top 10 issues
                            f.write(f"  • [{issue.severity.value.upper()}] {issue.title}\n")
                            f.write(f"    {issue.description}\n")
                    f.write("\n")
                
                # Missing sections summary
                missing_sections = self.validator._identify_missing_sections(template_data)
                if missing_sections:
                    f.write("MISSING INFORMATION\n")
                    f.write("-" * 30 + "\n")
                    for section in missing_sections:
                        f.write(f"  • {section}\n")
                    f.write("\n")
                
                # Recommendations
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 30 + "\n")
                
                if pre_validation and pre_validation.quality_score.overall_score < 80:
                    f.write("• Review and complete missing patient information\n")
                    f.write("• Ensure all required sections have substantive content\n")
                    f.write("• Verify AMA Guidelines compliance for impairment ratings\n")
                
                if post_validation and post_validation.placeholder_count > 0:
                    f.write("• Replace all placeholder text with actual content\n")
                    f.write("• Review document for completeness before finalization\n")
                
                f.write("• Conduct final medical review before submission\n")
                f.write("• Ensure all legal requirements are met\n")
            
            logger.info(f"Quality report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return ""
    
    def _get_file_statistics(self, doc_path: str) -> Dict[str, int]:
        """Get file statistics for the generated document."""
        try:
            stats = {
                'size': 0,
                'pages': 0,
                'words': 0
            }
            
            if os.path.exists(doc_path):
                # File size
                stats['size'] = os.path.getsize(doc_path)
                
                # Load document for content statistics
                doc = Document(doc_path)
                
                # Word count (approximate)
                word_count = 0
                for para in doc.paragraphs:
                    word_count += len(para.text.split())
                
                # Add table text
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            word_count += len(cell.text.split())
                
                stats['words'] = word_count
                
                # Page count (estimate based on content)
                # Rough estimate: 250 words per page
                stats['pages'] = max(1, word_count // 250)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting file statistics: {e}")
            return {'size': 0, 'pages': 0, 'words': 0}
    
    def generate_download_package(self,
                                result: ProfessionalTemplateResult,
                                include_quality_report: bool = True,
                                include_validation_summary: bool = True) -> str:
        """Generate a complete download package with template and reports."""
        try:
            # Create package directory
            package_dir = tempfile.mkdtemp(prefix="qme_package_")
            
            # Copy main template
            import shutil
            template_name = os.path.basename(result.file_path)
            package_template_path = os.path.join(package_dir, template_name)
            shutil.copy2(result.file_path, package_template_path)
            
            # Copy quality report if available
            if include_quality_report and result.quality_report_path:
                quality_name = os.path.basename(result.quality_report_path)
                package_quality_path = os.path.join(package_dir, quality_name)
                shutil.copy2(result.quality_report_path, package_quality_path)
            
            # Generate validation summary
            if include_validation_summary:
                summary_path = os.path.join(package_dir, "validation_summary.txt")
                self._generate_validation_summary(result, summary_path)
            
            # Create package info file
            info_path = os.path.join(package_dir, "package_info.txt")
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write("QME TEMPLATE PACKAGE\n")
                f.write("=" * 30 + "\n\n")
                f.write(f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Patient: {result.template_data.patient_info.name or 'Unknown'}\n")
                f.write(f"Template Version: {result.assembly_config.template_version}\n")
                f.write(f"File Size: {result.file_size_bytes / 1024:.1f} KB\n")
                f.write(f"Page Count: {result.page_count}\n")
                f.write(f"Word Count: {result.word_count}\n\n")
                
                f.write("PACKAGE CONTENTS:\n")
                f.write(f"• {template_name} - Main QME template\n")
                if include_quality_report and result.quality_report_path:
                    f.write(f"• {quality_name} - Quality assessment report\n")
                if include_validation_summary:
                    f.write("• validation_summary.txt - Validation summary\n")
                f.write("• package_info.txt - This file\n")
            
            logger.info(f"Download package created: {package_dir}")
            return package_dir
            
        except Exception as e:
            logger.error(f"Error creating download package: {e}")
            raise
    
    def _generate_validation_summary(self, result: ProfessionalTemplateResult, output_path: str) -> None:
        """Generate validation summary file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("VALIDATION SUMMARY\n")
                f.write("=" * 30 + "\n\n")
                
                # Pre-assembly summary
                pre_val = result.pre_assembly_validation
                f.write("PRE-ASSEMBLY VALIDATION\n")
                f.write(f"Status: {'PASSED' if pre_val.is_valid else 'FAILED'}\n")
                f.write(f"Quality Score: {pre_val.quality_score.overall_score:.1f}/100\n")
                f.write(f"Critical Issues: {pre_val.quality_score.critical_issues}\n")
                f.write(f"High Priority Issues: {pre_val.quality_score.high_issues}\n\n")
                
                # Post-assembly summary
                post_val = result.post_assembly_validation
                f.write("POST-ASSEMBLY VALIDATION\n")
                f.write(f"Status: {'PASSED' if post_val.is_valid else 'FAILED'}\n")
                f.write(f"Quality Score: {post_val.quality_score.overall_score:.1f}/100\n")
                f.write(f"Placeholders Remaining: {post_val.placeholder_count}\n")
                f.write(f"Compliance Status: {post_val.compliance_status.upper()}\n\n")
                
                # Overall assessment
                f.write("OVERALL ASSESSMENT\n")
                overall_score = (pre_val.quality_score.overall_score + post_val.quality_score.overall_score) / 2
                
                if overall_score >= 90:
                    assessment = "EXCELLENT - Ready for submission"
                elif overall_score >= 80:
                    assessment = "GOOD - Minor improvements recommended"
                elif overall_score >= 70:
                    assessment = "ACCEPTABLE - Review recommended"
                else:
                    assessment = "NEEDS IMPROVEMENT - Significant issues to address"
                
                f.write(f"Overall Score: {overall_score:.1f}/100\n")
                f.write(f"Assessment: {assessment}\n")
                
        except Exception as e:
            logger.error(f"Error generating validation summary: {e}")
            raise