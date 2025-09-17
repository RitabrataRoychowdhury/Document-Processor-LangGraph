"""
Enhanced QME Template Generator with Rules Engine Integration.

This service generates high-quality QME templates using the rules engine
for validation and quality assurance based on the gold standard template.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import os
import tempfile
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.shared import OxmlElement, qn

try:
    from src.core.generation.qme_template_generator import QMETemplateGenerator, QMETemplateData, PatientInfo, MedicalFindings
    from src.services.qme_rules_engine import QMERulesEngine, ValidationIssue, QualityScore, ValidationSeverity
    from src.config.qme_gold_standard_config import qme_config
    from src.utils.logging_config import get_logger
except ImportError:
    from core.generation.qme_template_generator import QMETemplateGenerator, QMETemplateData, PatientInfo, MedicalFindings
    from services.qme_rules_engine import QMERulesEngine, ValidationIssue, QualityScore, ValidationSeverity
    from config.qme_gold_standard_config import qme_config
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EnhancedQMEResult:
    """Result from enhanced QME generation with quality assessment."""
    file_path: str
    template_data: QMETemplateData
    validation_issues: List[ValidationIssue]
    quality_score: QualityScore
    quality_report: str
    improvement_suggestions: Dict[str, List[str]]
    generated_at: datetime = field(default_factory=datetime.now)


class EnhancedQMETemplateGenerator:
    """Enhanced QME Template Generator with integrated rules engine."""
    
    def __init__(self):
        """Initialize the enhanced generator."""
        self.base_generator = QMETemplateGenerator()
        self.rules_engine = QMERulesEngine()
        
        logger.info("Initialized Enhanced QME Template Generator with Rules Engine")
    
    def generate_enhanced_qme_template(self, 
                                     patient_id: str, 
                                     output_path: Optional[str] = None,
                                     doctor_info: Optional[Dict[str, str]] = None,
                                     template_preferences: Optional[Dict[str, Any]] = None) -> EnhancedQMEResult:
        """
        Generate an enhanced QME template with quality validation.
        
        Args:
            patient_id: Patient identifier
            output_path: Optional output file path
            doctor_info: Doctor information for template
            template_preferences: Template formatting preferences
            
        Returns:
            EnhancedQMEResult with template and quality assessment
        """
        try:
            logger.info(f"Generating enhanced QME template for patient: {patient_id}")
            
            # Generate base template data
            base_path, template_data = self.base_generator.generate_qme_template(patient_id, output_path)
            
            # Validate template data using rules engine
            validation_issues, quality_score = self.rules_engine.validate_qme_report(template_data)
            
            # Generate quality report
            quality_report = self.rules_engine.generate_quality_report(validation_issues, quality_score)
            
            # Get improvement suggestions
            improvement_suggestions = self.rules_engine.get_improvement_suggestions(validation_issues)
            
            # Create enhanced DOCX with quality indicators
            enhanced_path = self._create_enhanced_docx(
                template_data, 
                validation_issues, 
                quality_score,
                base_path,
                doctor_info,
                template_preferences
            )
            
            # Create result
            result = EnhancedQMEResult(
                file_path=enhanced_path,
                template_data=template_data,
                validation_issues=validation_issues,
                quality_score=quality_score,
                quality_report=quality_report,
                improvement_suggestions=improvement_suggestions
            )
            
            logger.info(f"Enhanced QME template generated: {enhanced_path} (Quality Score: {quality_score.overall_score:.1f})")
            return result
            
        except Exception as e:
            logger.error(f"Error generating enhanced QME template: {e}")
            raise
    
    def _create_enhanced_docx(self, 
                            template_data: QMETemplateData,
                            validation_issues: List[ValidationIssue],
                            quality_score: QualityScore,
                            base_path: str,
                            doctor_info: Optional[Dict[str, str]] = None,
                            template_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Create enhanced DOCX with quality indicators and formatting."""
        try:
            # Create new document with gold standard formatting
            doc = Document()
            
            # Apply gold standard formatting
            self._apply_gold_standard_formatting(doc, template_preferences)
            
            # Add header with doctor information
            self._add_professional_header(doc, doctor_info)
            
            # Add title
            self._add_title(doc)
            
            # Add quality indicator section (for draft review)
            if validation_issues or quality_score.overall_score < 90:
                self._add_quality_indicators(doc, validation_issues, quality_score)
            
            # Add all required sections following gold standard order
            self._add_patient_identification_section(doc, template_data)
            self._add_history_sections(doc, template_data)
            self._add_examination_section(doc, template_data)
            self._add_diagnostic_studies_section(doc, template_data)
            self._add_diagnosis_section(doc, template_data)
            self._add_impairment_rating_section(doc, template_data)
            self._add_work_restrictions_section(doc, template_data)
            self._add_future_medical_care_section(doc, template_data)
            self._add_causation_analysis_section(doc, template_data)
            self._add_apportionment_section(doc, template_data)
            
            # Add footer
            self._add_professional_footer(doc, doctor_info)
            
            # Generate enhanced filename
            enhanced_path = base_path.replace('.docx', '_enhanced.docx')
            
            # Save document
            doc.save(enhanced_path)
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error creating enhanced DOCX: {e}")
            raise
    
    def _apply_gold_standard_formatting(self, doc: Document, preferences: Optional[Dict[str, Any]] = None):
        """Apply gold standard formatting to document."""
        try:
            # Get or create styles
            styles = doc.styles
            
            # Normal style
            normal_style = styles['Normal']
            normal_font = normal_style.font
            normal_font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
            normal_font.size = Pt(qme_config.FORMATTING_REQUIREMENTS['typography']['font_size'])
            
            # Paragraph formatting
            normal_paragraph = normal_style.paragraph_format
            normal_paragraph.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
            normal_paragraph.line_spacing = qme_config.FORMATTING_REQUIREMENTS['typography']['line_spacing']
            normal_paragraph.space_after = Pt(qme_config.FORMATTING_REQUIREMENTS['typography']['paragraph_spacing'])
            
            # Create heading styles
            self._create_heading_styles(doc)
            
            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(qme_config.FORMATTING_REQUIREMENTS['document_structure']['margins']['top'])
                section.bottom_margin = Inches(qme_config.FORMATTING_REQUIREMENTS['document_structure']['margins']['bottom'])
                section.left_margin = Inches(qme_config.FORMATTING_REQUIREMENTS['document_structure']['margins']['left'])
                section.right_margin = Inches(qme_config.FORMATTING_REQUIREMENTS['document_structure']['margins']['right'])
            
        except Exception as e:
            logger.error(f"Error applying formatting: {e}")
    
    def _create_heading_styles(self, doc: Document):
        """Create custom heading styles following gold standard."""
        try:
            styles = doc.styles
            
            # Heading 1 style
            if 'QME Heading 1' not in [style.name for style in styles]:
                heading1_style = styles.add_style('QME Heading 1', WD_STYLE_TYPE.PARAGRAPH)
                heading1_font = heading1_style.font
                heading1_font.name = qme_config.FORMATTING_REQUIREMENTS['typography']['font_family']
                heading1_font.size = Pt(14)
                heading1_font.bold = True
                
                heading1_paragraph = heading1_style.paragraph_format
                heading1_paragraph.space_before = Pt(qme_config.FORMATTING_REQUIREMENTS['section_formatting']['headers']['spacing_before'])
                heading1_paragraph.space_after = Pt(qme_config.FORMATTING_REQUIREMENTS['section_formatting']['headers']['spacing_after'])
            
        except Exception as e:
            logger.error(f"Error creating heading styles: {e}")
    
    def _add_professional_header(self, doc: Document, doctor_info: Optional[Dict[str, str]] = None):
        """Add professional header with doctor information."""
        try:
            section = doc.sections[0]
            header = section.header
            
            if doctor_info:
                header_para = header.paragraphs[0]
                header_para.text = f"Dr. {doctor_info.get('name', '[Doctor Name]')}, {doctor_info.get('specialty', 'QME')}"
                header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Add license and contact info
                license_para = header.add_paragraph()
                license_para.text = f"License: {doctor_info.get('license', '[License Number]')} | {doctor_info.get('phone', '[Phone]')}"
                license_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
        except Exception as e:
            logger.error(f"Error adding header: {e}")
    
    def _add_title(self, doc: Document):
        """Add document title."""
        title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR\'S REPORT', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add date
        date_para = doc.add_paragraph()
        date_para.text = f"Date of Report: {datetime.now().strftime('%B %d, %Y')}"
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()  # Spacing
    
    def _add_quality_indicators(self, doc: Document, issues: List[ValidationIssue], quality_score: QualityScore):
        """Add quality indicators section for draft review."""
        try:
            # Add quality section (will be removed in final version)
            quality_heading = doc.add_heading('DRAFT - QUALITY ASSESSMENT', level=1)
            quality_heading.style.font.color.rgb = None  # Red color would be set here
            
            # Quality score summary
            score_para = doc.add_paragraph()
            score_para.add_run('Overall Quality Score: ').bold = True
            score_para.add_run(f'{quality_score.overall_score:.1f}/100')
            
            # Issue summary
            if issues:
                issues_para = doc.add_paragraph()
                issues_para.add_run('Issues Found: ').bold = True
                issues_para.add_run(f'{len(issues)} total ({quality_score.critical_issues} critical, {quality_score.high_issues} high priority)')
                
                # List critical issues
                critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
                if critical_issues:
                    doc.add_paragraph('Critical Issues to Address:', style='List Bullet')
                    for issue in critical_issues[:5]:  # Limit to top 5
                        issue_para = doc.add_paragraph(f'{issue.title}: {issue.description}', style='List Bullet 2')
            
            doc.add_page_break()
            
        except Exception as e:
            logger.error(f"Error adding quality indicators: {e}")
    
    def _add_patient_identification_section(self, doc: Document, template_data: QMETemplateData):
        """Add patient identification section following gold standard."""
        try:
            doc.add_heading('I. PATIENT IDENTIFICATION', level=1)
            
            patient_info = template_data.patient_info
            
            # Create patient info table
            table = doc.add_table(rows=8, cols=2)
            table.style = 'Table Grid'
            
            # Patient information rows
            info_rows = [
                ('Name:', patient_info.name or '[MISSING - Patient name required]'),
                ('Date of Birth:', '[MISSING - Date of birth required]'),
                ('Age:', str(patient_info.age) if patient_info.age else '[MISSING - Age required]'),
                ('Gender:', patient_info.gender or '[MISSING - Gender required]'),
                ('Case Number:', patient_info.case_number or '[MISSING - Case number required]'),
                ('Date of Injury:', patient_info.injury_date.strftime('%m/%d/%Y') if patient_info.injury_date else '[MISSING - Injury date required]'),
                ('Employer:', patient_info.employer or '[MISSING - Employer information required]'),
                ('Occupation:', patient_info.occupation or '[MISSING - Occupation required]')
            ]
            
            for i, (label, value) in enumerate(info_rows):
                table.cell(i, 0).text = label
                table.cell(i, 0).paragraphs[0].runs[0].bold = True
                table.cell(i, 1).text = value
                
                # Highlight missing information
                if '[MISSING' in value:
                    table.cell(i, 1).paragraphs[0].runs[0].font.color.rgb = None  # Red color
            
            doc.add_paragraph()
            
        except Exception as e:
            logger.error(f"Error adding patient identification: {e}")
    
    def _add_history_sections(self, doc: Document, template_data: QMETemplateData):
        """Add history sections following gold standard structure."""
        try:
            # History of Present Illness
            doc.add_heading('II. HISTORY OF PRESENT ILLNESS', level=1)
            
            hpi_content = self._generate_hpi_content(template_data)
            doc.add_paragraph(hpi_content)
            
            # Past Medical History
            doc.add_heading('III. PAST MEDICAL HISTORY', level=1)
            doc.add_paragraph('[MISSING - Past medical history information required for comprehensive evaluation]')
            
            # Social History
            doc.add_heading('IV. SOCIAL HISTORY', level=1)
            doc.add_paragraph('[MISSING - Social history including smoking, alcohol use, and activities required]')
            
            # Occupational History
            doc.add_heading('V. OCCUPATIONAL HISTORY', level=1)
            
            if template_data.patient_info.occupation:
                occ_para = doc.add_paragraph()
                occ_para.add_run('Current Occupation: ').bold = True
                occ_para.add_run(template_data.patient_info.occupation)
                
                if template_data.patient_info.employer:
                    emp_para = doc.add_paragraph()
                    emp_para.add_run('Employer: ').bold = True
                    emp_para.add_run(template_data.patient_info.employer)
            else:
                doc.add_paragraph('[MISSING - Detailed occupational history and job demands required]')
            
        except Exception as e:
            logger.error(f"Error adding history sections: {e}")
    
    def _generate_hpi_content(self, template_data: QMETemplateData) -> str:
        """Generate history of present illness content."""
        try:
            content_parts = []
            
            patient_info = template_data.patient_info
            
            # Injury information
            if patient_info.injury_date:
                content_parts.append(f"The patient reports sustaining an injury on {patient_info.injury_date.strftime('%B %d, %Y')}.")
            
            # Body parts affected
            if patient_info.body_parts:
                body_parts_str = ', '.join(patient_info.body_parts)
                content_parts.append(f"The injury involved the {body_parts_str}.")
            
            # Current symptoms from findings
            if template_data.medical_findings.findings:
                symptoms = [finding.description for finding in template_data.medical_findings.findings[:3]]
                if symptoms:
                    content_parts.append(f"Current symptoms include {', '.join(symptoms)}.")
            
            if not content_parts:
                return '[MISSING - Detailed history of present illness required including mechanism of injury, symptom onset, current symptoms, and functional limitations]'
            
            return ' '.join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating HPI content: {e}")
            return '[ERROR - Unable to generate history content]'
    
    def _add_examination_section(self, doc: Document, template_data: QMETemplateData):
        """Add physical examination section."""
        try:
            doc.add_heading('VI. PHYSICAL EXAMINATION', level=1)
            
            # General Appearance
            doc.add_heading('A. General Appearance', level=2)
            doc.add_paragraph('[MISSING - General appearance, distress level, and cooperation assessment required]')
            
            # Musculoskeletal Examination
            doc.add_heading('B. Musculoskeletal Examination', level=2)
            
            if template_data.medical_findings.findings:
                for finding in template_data.medical_findings.findings:
                    if 'examination' in finding.finding_type.lower():
                        doc.add_paragraph(f"• {finding.description}")
            else:
                doc.add_paragraph('[MISSING - Detailed musculoskeletal examination including range of motion, strength testing, and special tests required]')
            
            # Neurological Examination
            doc.add_heading('C. Neurological Examination', level=2)
            doc.add_paragraph('[MISSING - Neurological examination including sensory testing, motor function, and reflexes required]')
            
        except Exception as e:
            logger.error(f"Error adding examination section: {e}")
    
    def _add_diagnostic_studies_section(self, doc: Document, template_data: QMETemplateData):
        """Add diagnostic studies section."""
        try:
            doc.add_heading('VII. DIAGNOSTIC STUDIES', level=1)
            
            if template_data.medical_findings.imaging_studies:
                for study in template_data.medical_findings.imaging_studies:
                    doc.add_paragraph(f"• {study}")
            else:
                doc.add_paragraph('[MISSING - Review of diagnostic studies including imaging and laboratory tests required]')
            
        except Exception as e:
            logger.error(f"Error adding diagnostic studies: {e}")
    
    def _add_diagnosis_section(self, doc: Document, template_data: QMETemplateData):
        """Add diagnosis section."""
        try:
            doc.add_heading('VIII. DIAGNOSIS', level=1)
            
            if template_data.medical_findings.diagnoses:
                for i, diagnosis in enumerate(template_data.medical_findings.diagnoses, 1):
                    diag_para = doc.add_paragraph()
                    diag_para.add_run(f'{i}. ').bold = True
                    diag_para.add_run(diagnosis.description)
                    
                    if diagnosis.icd_code:
                        diag_para.add_run(f' (ICD-10: {diagnosis.icd_code})')
                    else:
                        diag_para.add_run(' [MISSING - ICD-10 code required]')
            else:
                doc.add_paragraph('[MISSING - Primary diagnosis with ICD-10 code required]')
            
        except Exception as e:
            logger.error(f"Error adding diagnosis section: {e}")
    
    def _add_impairment_rating_section(self, doc: Document, template_data: QMETemplateData):
        """Add impairment rating section."""
        try:
            doc.add_heading('IX. IMPAIRMENT RATING', level=1)
            
            if template_data.medical_findings.impairment_ratings:
                for rating in template_data.medical_findings.impairment_ratings:
                    rating_para = doc.add_paragraph()
                    rating_para.add_run('Impairment Rating: ').bold = True
                    rating_para.add_run(f'{rating.percentage}% whole person impairment')
                    
                    if rating.ama_table:
                        table_para = doc.add_paragraph()
                        table_para.add_run('AMA Reference: ').bold = True
                        table_para.add_run(f'AMA Guides 5th Edition, Table {rating.ama_table}')
                    
                    if rating.rationale:
                        method_para = doc.add_paragraph()
                        method_para.add_run('Methodology: ').bold = True
                        method_para.add_run(rating.rationale)
            else:
                doc.add_paragraph('[MISSING - Impairment rating calculation using AMA Guides 5th Edition required]')
            
        except Exception as e:
            logger.error(f"Error adding impairment rating: {e}")
    
    def _add_work_restrictions_section(self, doc: Document, template_data: QMETemplateData):
        """Add work restrictions section."""
        try:
            doc.add_heading('X. WORK RESTRICTIONS', level=1)
            doc.add_paragraph('[MISSING - Specific work restrictions and limitations based on examination findings required]')
            
        except Exception as e:
            logger.error(f"Error adding work restrictions: {e}")
    
    def _add_future_medical_care_section(self, doc: Document, template_data: QMETemplateData):
        """Add future medical care section."""
        try:
            doc.add_heading('XI. FUTURE MEDICAL CARE', level=1)
            doc.add_paragraph('[MISSING - Future medical care recommendations based on diagnosis and prognosis required]')
            
        except Exception as e:
            logger.error(f"Error adding future medical care: {e}")
    
    def _add_causation_analysis_section(self, doc: Document, template_data: QMETemplateData):
        """Add causation analysis section."""
        try:
            doc.add_heading('XII. CAUSATION ANALYSIS', level=1)
            doc.add_paragraph('[MISSING - Medical causation analysis with reasonable medical probability statement required]')
            
        except Exception as e:
            logger.error(f"Error adding causation analysis: {e}")
    
    def _add_apportionment_section(self, doc: Document, template_data: QMETemplateData):
        """Add apportionment section."""
        try:
            doc.add_heading('XIII. APPORTIONMENT', level=1)
            doc.add_paragraph('[MISSING - Apportionment analysis considering pre-existing conditions and other factors required]')
            
        except Exception as e:
            logger.error(f"Error adding apportionment: {e}")
    
    def _add_professional_footer(self, doc: Document, doctor_info: Optional[Dict[str, str]] = None):
        """Add professional footer."""
        try:
            section = doc.sections[0]
            footer = section.footer
            
            footer_para = footer.paragraphs[0]
            footer_para.text = "CONFIDENTIAL MEDICAL REPORT"
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            if doctor_info:
                signature_para = footer.add_paragraph()
                signature_para.text = f"\n\n_________________________\nDr. {doctor_info.get('name', '[Doctor Name]')}\nQualified Medical Evaluator"
                signature_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
        except Exception as e:
            logger.error(f"Error adding footer: {e}")
    
    def generate_quality_summary_report(self, result: EnhancedQMEResult) -> str:
        """Generate a summary quality report for the template."""
        try:
            summary_lines = []
            
            summary_lines.append("QME TEMPLATE QUALITY SUMMARY")
            summary_lines.append("=" * 40)
            summary_lines.append("")
            
            # Overall assessment
            quality_level = "Excellent" if result.quality_score.overall_score >= 90 else \
                           "Good" if result.quality_score.overall_score >= 80 else \
                           "Needs Improvement" if result.quality_score.overall_score >= 70 else \
                           "Poor"
            
            summary_lines.append(f"Overall Quality: {quality_level} ({result.quality_score.overall_score:.1f}/100)")
            summary_lines.append(f"Completeness: {result.quality_score.completeness_score:.1f}/100")
            summary_lines.append(f"Compliance: {result.quality_score.compliance_score:.1f}/100")
            summary_lines.append("")
            
            # Top issues
            if result.validation_issues:
                critical_issues = [issue for issue in result.validation_issues if issue.severity == ValidationSeverity.CRITICAL]
                if critical_issues:
                    summary_lines.append("CRITICAL ISSUES TO ADDRESS:")
                    for issue in critical_issues[:3]:
                        summary_lines.append(f"• {issue.title}")
                    summary_lines.append("")
            
            # Recommendations
            if result.improvement_suggestions:
                summary_lines.append("TOP RECOMMENDATIONS:")
                all_suggestions = []
                for suggestions in result.improvement_suggestions.values():
                    all_suggestions.extend(suggestions)
                
                for suggestion in list(set(all_suggestions))[:5]:
                    summary_lines.append(f"• {suggestion}")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Error generating quality summary: {e}")
            return f"Error generating summary: {str(e)}"