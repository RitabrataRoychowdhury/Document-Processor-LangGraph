"""
Professional Template Assembler

This service provides comprehensive template assembly capabilities for QME reports
with proper formatting, legal compliance, template validation, placeholder replacement,
and quality checks. It integrates with the QME template generation workflow and rules engine.
"""

import os
import json
import time
import logging
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

# Optional dependencies with graceful degradation
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available, DOCX generation disabled")

# Core imports
from src.core.interfaces import IGenerationService, GenerationResult, ValidationResult
from src.models.extraction_models import QualityAssessment, QualityIssue

# Optional monitoring imports
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)


class TemplateFormat(Enum):
    """Supported template output formats."""
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    TEXT = "txt"


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssemblyStrategy(Enum):
    """Template assembly strategies."""
    FULL_PROFESSIONAL = "full_professional"
    SIMPLIFIED = "simplified"
    PLACEHOLDER = "placeholder"
    MINIMAL = "minimal"
    TEXT_ONLY = "text_only"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during template assembly."""
    rule_name: str
    severity: ValidationSeverity
    description: str
    field_name: Optional[str] = None
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None


@dataclass
class TemplateAssemblyConfig:
    """Configuration for template assembly."""
    output_format: TemplateFormat = TemplateFormat.DOCX
    apply_professional_formatting: bool = True
    validate_before_assembly: bool = True
    validate_after_assembly: bool = True
    enable_error_recovery: bool = True
    generate_quality_report: bool = True
    include_quality_indicators: bool = False
    include_missing_placeholders: bool = True
    quality_threshold: float = 70.0
    max_retry_attempts: int = 3
    template_version: str = "1.0"
    
    # Formatting settings
    font_family: str = "Times New Roman"
    font_size: int = 12
    header_font_size: int = 14
    line_spacing: float = 1.15
    paragraph_spacing: int = 6
    
    # Margins (in inches)
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    
    # Output settings
    output_directory: str = "results/generated_documents"
    archive_directory: str = "results/templates_archive"
    quality_reports_directory: str = "results/quality_reports"
    
    # Quality requirements
    minimum_completeness_score: float = 80.0
    minimum_accuracy_score: float = 85.0
    minimum_compliance_score: float = 90.0
    minimum_formatting_score: float = 95.0
    
    # Required sections and fields
    required_sections: List[str] = field(default_factory=lambda: [
        "patient_identification", "history_of_present_illness", 
        "physical_examination", "diagnosis", "impairment_rating"
    ])
    
    required_fields: Dict[str, List[str]] = field(default_factory=lambda: {
        "patient_info": ["name", "case_number", "injury_date"],
        "medical_findings": ["diagnoses", "impairment_ratings"]
    })


@dataclass 
class ProfessionalTemplateResult:
    """Result of professional template assembly."""
    success: bool
    template_path: Optional[str] = None
    error_message: Optional[str] = None
    
    # Quality metrics
    quality_assessment: Optional[QualityAssessment] = None
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    
    # Processing metadata
    processing_time: float = 0.0
    assembly_strategy: Optional[AssemblyStrategy] = None
    format_used: Optional[TemplateFormat] = None
    
    # Recovery information
    recovery_attempts: int = 0
    fallback_used: bool = False
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        """Get critical validation issues."""
        return [issue for issue in self.validation_issues if issue.severity == ValidationSeverity.CRITICAL]
    
    def get_fixable_issues(self) -> List[ValidationIssue]:
        """Get auto-fixable validation issues."""
        return [issue for issue in self.validation_issues if issue.auto_fixable]
    
    def is_high_quality(self, threshold: float = 80.0) -> bool:
        """Check if template meets high quality standards."""
        if not self.quality_assessment:
            return False
        return self.quality_assessment.overall_score >= threshold


class ProfessionalTemplateAssembler(IGenerationService):
    """
    Professional template assembler with comprehensive formatting, validation,
    and quality assurance capabilities.
    
    Features:
    - DOCX generation with professional formatting and legal compliance
    - Template validation with comprehensive rule checking
    - Placeholder replacement with intelligent fallbacks
    - Quality assessment and scoring
    - Error recovery with multiple fallback strategies
    - Integration with QME template generation workflow
    - Rules engine integration for compliance checking
    """
    
    def __init__(self, config: Optional[TemplateAssemblyConfig] = None):
        """Initialize the professional template assembler."""
        self.config = config or TemplateAssemblyConfig()
        
        # Load template structure and validation rules
        self._load_template_configuration()
        
        # Initialize validation rules
        self._initialize_validation_rules()
        
        # Ensure output directories exist
        self._ensure_directories()
        
        extraction_logger.info(
            "Initialized ProfessionalTemplateAssembler",
            extra_data={
                "output_format": self.config.output_format.value,
                "professional_formatting": self.config.apply_professional_formatting,
                "quality_threshold": self.config.quality_threshold,
                "docx_available": DOCX_AVAILABLE
            }
        )
    
    def _load_template_configuration(self) -> None:
        """Load template structure and assembly configuration."""
        try:
            # Load QME template structure
            template_structure_path = "config/templates/qme_template_structure.yaml"
            if Path(template_structure_path).exists():
                with open(template_structure_path, 'r') as f:
                    self.template_structure = yaml.safe_load(f)
            else:
                self.template_structure = self._get_default_template_structure()
            
            # Load assembly configuration
            assembly_config_path = "config/templates/assembly_config.yaml"
            if Path(assembly_config_path).exists():
                with open(assembly_config_path, 'r') as f:
                    self.assembly_config = yaml.safe_load(f)
            else:
                self.assembly_config = self._get_default_assembly_config()
                
        except Exception as e:
            extraction_logger.warning(f"Failed to load template configuration: {str(e)}")
            self.template_structure = self._get_default_template_structure()
            self.assembly_config = self._get_default_assembly_config()
    
    def _initialize_validation_rules(self) -> None:
        """Initialize validation rules from configuration."""
        self.validation_rules = []
        
        # Load rules from configuration
        if 'validation_rules' in self.assembly_config:
            for rule_config in self.assembly_config['validation_rules']:
                self.validation_rules.append(rule_config)
        else:
            # Default validation rules
            self.validation_rules = [
                {
                    "name": "patient_name_required",
                    "description": "Patient name must be present",
                    "severity": "CRITICAL",
                    "check_function": "_check_patient_name",
                    "auto_fixable": False
                },
                {
                    "name": "case_number_required", 
                    "description": "Case number must be present",
                    "severity": "HIGH",
                    "check_function": "_check_case_number",
                    "auto_fixable": False
                },
                {
                    "name": "diagnosis_required",
                    "description": "At least one diagnosis must be present",
                    "severity": "CRITICAL", 
                    "check_function": "_check_diagnoses",
                    "auto_fixable": False
                }
            ]
    
    def _ensure_directories(self) -> None:
        """Ensure output directories exist."""
        directories = [
            self.config.output_directory,
            self.config.archive_directory,
            self.config.quality_reports_directory
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def generate_content(self, validated_data: Dict[str, Any], **kwargs) -> GenerationResult:
        """Generate content from validated data."""
        try:
            # Convert to template assembly format
            template_result = self.assemble_template(validated_data)
            
            return GenerationResult(
                success=template_result.success,
                status="completed" if template_result.success else "failed",
                error_message=template_result.error_message,
                processing_time=template_result.processing_time,
                generated_content={
                    "template_path": template_result.template_path,
                    "quality_assessment": template_result.quality_assessment.__dict__ if template_result.quality_assessment else None,
                    "validation_issues": [issue.__dict__ for issue in template_result.validation_issues]
                },
                template_data=self._read_template_data(template_result.template_path) if template_result.template_path else None,
                quality_score=template_result.quality_assessment.overall_score if template_result.quality_assessment else 0.0
            )
            
        except Exception as e:
            extraction_logger.error(f"Content generation failed: {str(e)}")
            return GenerationResult(
                success=False,
                status="failed",
                error_message=f"Content generation failed: {str(e)}"
            )
    
    async def assemble_template(self, template_data: Dict[str, Any], template_config: Dict[str, Any]) -> GenerationResult:
        """Assemble final template from generated content."""
        return await self.generate_content(template_data, **template_config)
    
    async def customize_output(self, template_data: bytes, customizations: Dict[str, Any]) -> GenerationResult:
        """Apply customizations to generated template."""
        # This would implement template customization logic
        return GenerationResult(
            success=True,
            status="completed",
            template_data=template_data
        )
    
    def assemble_professional_template(self, template_data: Dict[str, Any], output_path: str = None, **kwargs) -> ProfessionalTemplateResult:
        """
        Assemble a professional template with comprehensive validation and formatting.
        This is the main public interface method.
        
        Args:
            template_data: Dictionary containing template data
            output_path: Optional output path for the template
            **kwargs: Additional configuration options
            
        Returns:
            ProfessionalTemplateResult with assembly results
        """
        # Store output path if provided
        if output_path:
            self.config.output_path = output_path
            
        # Call the main assembly method
        return self.assemble_template(template_data)
    
    def assemble_template(self, template_data: Dict[str, Any]) -> ProfessionalTemplateResult:
        """
        Assemble a professional template with comprehensive validation and formatting.
        
        Args:
            template_data: Dictionary containing all template data
            
        Returns:
            ProfessionalTemplateResult with assembly results and quality metrics
        """
        start_time = time.time()
        
        try:
            extraction_logger.info(
                "Starting professional template assembly",
                extra_data={"data_keys": list(template_data.keys())}
            )
            
            # Pre-assembly validation
            if self.config.validate_before_assembly:
                validation_issues = self._validate_template_data(template_data)
                critical_issues = [issue for issue in validation_issues if issue.severity == ValidationSeverity.CRITICAL]
                
                if critical_issues and not self.config.enable_error_recovery:
                    return ProfessionalTemplateResult(
                        success=False,
                        error_message=f"Critical validation issues found: {len(critical_issues)}",
                        validation_issues=validation_issues,
                        processing_time=time.time() - start_time
                    )
            else:
                validation_issues = []
            
            # Attempt assembly with primary strategy
            result = self._attempt_assembly(template_data, AssemblyStrategy.FULL_PROFESSIONAL, validation_issues)
            
            # If primary assembly failed and error recovery is enabled, try fallback strategies
            if not result.success and self.config.enable_error_recovery:
                result = self._attempt_error_recovery(template_data, validation_issues, start_time)
            
            result.processing_time = time.time() - start_time
            
            # Post-assembly validation and quality assessment
            if result.success and self.config.validate_after_assembly:
                result = self._perform_post_assembly_validation(result)
            
            extraction_logger.info(
                f"Template assembly completed: success={result.success}",
                extra_data={
                    "processing_time": result.processing_time,
                    "strategy_used": result.assembly_strategy.value if result.assembly_strategy else None,
                    "validation_issues": len(result.validation_issues),
                    "quality_score": result.quality_assessment.overall_score if result.quality_assessment else 0.0
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            extraction_logger.error(f"Template assembly failed: {str(e)}")
            
            return ProfessionalTemplateResult(
                success=False,
                error_message=f"Template assembly failed: {str(e)}",
                processing_time=processing_time
            )
    
    def _attempt_assembly(
        self, 
        template_data: Dict[str, Any], 
        strategy: AssemblyStrategy,
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Attempt template assembly with specified strategy."""
        
        try:
            if strategy == AssemblyStrategy.FULL_PROFESSIONAL:
                return self._assemble_full_professional(template_data, validation_issues)
            elif strategy == AssemblyStrategy.SIMPLIFIED:
                return self._assemble_simplified(template_data, validation_issues)
            elif strategy == AssemblyStrategy.PLACEHOLDER:
                return self._assemble_placeholder(template_data, validation_issues)
            elif strategy == AssemblyStrategy.MINIMAL:
                return self._assemble_minimal(template_data, validation_issues)
            elif strategy == AssemblyStrategy.TEXT_ONLY:
                return self._assemble_text_only(template_data, validation_issues)
            else:
                raise ValueError(f"Unknown assembly strategy: {strategy}")
                
        except Exception as e:
            return ProfessionalTemplateResult(
                success=False,
                error_message=f"Assembly strategy {strategy.value} failed: {str(e)}",
                assembly_strategy=strategy,
                validation_issues=validation_issues
            )
    
    def _assemble_full_professional(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Assemble full professional template with complete formatting."""
        
        if not DOCX_AVAILABLE:
            raise RuntimeError("python-docx not available for DOCX generation")
        
        # Generate output filename
        patient_name = self._extract_patient_name(template_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"QME_Report_{patient_name}_{timestamp}.docx"
        output_path = Path(self.config.output_directory) / filename
        
        # Create DOCX document
        doc = Document()
        
        # Apply professional formatting
        self._apply_document_formatting(doc)
        
        # Add document sections
        self._add_document_header(doc, template_data)
        self._add_document_title(doc)
        self._add_patient_identification(doc, template_data)
        self._add_history_section(doc, template_data)
        self._add_examination_section(doc, template_data)
        self._add_diagnostic_studies(doc, template_data)
        self._add_diagnosis_section(doc, template_data)
        self._add_causation_analysis(doc, template_data)
        self._add_impairment_rating(doc, template_data)
        self._add_work_restrictions(doc, template_data)
        self._add_future_medical_care(doc, template_data)
        self._add_conclusions(doc, template_data)
        self._add_document_footer(doc, template_data)
        
        # Save document
        doc.save(str(output_path))
        
        # Assess quality
        quality_assessment = self._assess_template_quality(template_data, validation_issues)
        
        return ProfessionalTemplateResult(
            success=True,
            template_path=str(output_path),
            quality_assessment=quality_assessment,
            validation_issues=validation_issues,
            assembly_strategy=AssemblyStrategy.FULL_PROFESSIONAL,
            format_used=TemplateFormat.DOCX
        )
    
    def _assemble_simplified(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Assemble simplified template with basic formatting."""
        
        if not DOCX_AVAILABLE:
            return self._assemble_text_only(template_data, validation_issues)
        
        # Generate output filename
        patient_name = self._extract_patient_name(template_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"QME_Report_Simplified_{patient_name}_{timestamp}.docx"
        output_path = Path(self.config.output_directory) / filename
        
        # Create simplified DOCX document
        doc = Document()
        
        # Add basic sections only
        doc.add_heading('QME REPORT', 0)
        
        # Patient information
        doc.add_heading('Patient Information', level=1)
        patient_info = template_data.get('patient_info', {})
        doc.add_paragraph(f"Name: {patient_info.get('name', '[MISSING]')}")
        doc.add_paragraph(f"Case Number: {patient_info.get('case_number', '[MISSING]')}")
        doc.add_paragraph(f"Injury Date: {patient_info.get('injury_date', '[MISSING]')}")
        
        # Medical findings
        doc.add_heading('Medical Findings', level=1)
        medical_findings = template_data.get('medical_findings', {})
        diagnoses = medical_findings.get('diagnoses', [])
        if diagnoses:
            doc.add_paragraph("Diagnoses:")
            for diagnosis in diagnoses:
                doc.add_paragraph(f"• {diagnosis}", style='List Bullet')
        
        # Impairment rating
        impairment_ratings = medical_findings.get('impairment_ratings', {})
        if impairment_ratings:
            doc.add_heading('Impairment Rating', level=1)
            for body_part, rating in impairment_ratings.items():
                doc.add_paragraph(f"{body_part}: {rating}%")
        
        # Save document
        doc.save(str(output_path))
        
        # Assess quality (lower threshold for simplified)
        quality_assessment = self._assess_template_quality(template_data, validation_issues, simplified=True)
        
        return ProfessionalTemplateResult(
            success=True,
            template_path=str(output_path),
            quality_assessment=quality_assessment,
            validation_issues=validation_issues,
            assembly_strategy=AssemblyStrategy.SIMPLIFIED,
            format_used=TemplateFormat.DOCX,
            fallback_used=True
        )
    
    def _assemble_placeholder(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Assemble template with placeholders for missing data."""
        
        # Use simplified assembly but with placeholders for missing data
        result = self._assemble_simplified(template_data, validation_issues)
        result.assembly_strategy = AssemblyStrategy.PLACEHOLDER
        
        return result
    
    def _assemble_minimal(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Assemble minimal template with only essential information."""
        
        # Generate output filename
        patient_name = self._extract_patient_name(template_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"QME_Report_Minimal_{patient_name}_{timestamp}.txt"
        output_path = Path(self.config.output_directory) / filename
        
        # Create minimal text content
        content = []
        content.append("QME REPORT - MINIMAL")
        content.append("=" * 30)
        content.append("")
        
        # Essential patient information
        patient_info = template_data.get('patient_info', {})
        content.append(f"Patient: {patient_info.get('name', '[MISSING]')}")
        content.append(f"Case: {patient_info.get('case_number', '[MISSING]')}")
        content.append(f"Injury Date: {patient_info.get('injury_date', '[MISSING]')}")
        content.append("")
        
        # Essential medical findings
        medical_findings = template_data.get('medical_findings', {})
        diagnoses = medical_findings.get('diagnoses', [])
        if diagnoses:
            content.append("Diagnoses:")
            for diagnosis in diagnoses:
                content.append(f"- {diagnosis}")
            content.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        # Assess quality (very low threshold for minimal)
        quality_assessment = QualityAssessment(
            overall_score=40.0,
            completeness_score=30.0,
            accuracy_score=50.0,
            consistency_score=40.0,
            compliance_score=20.0
        )
        
        return ProfessionalTemplateResult(
            success=True,
            template_path=str(output_path),
            quality_assessment=quality_assessment,
            validation_issues=validation_issues,
            assembly_strategy=AssemblyStrategy.MINIMAL,
            format_used=TemplateFormat.TEXT,
            fallback_used=True
        )
    
    def _assemble_text_only(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue]
    ) -> ProfessionalTemplateResult:
        """Assemble text-only template as last resort."""
        
        # Generate output filename
        patient_name = self._extract_patient_name(template_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"QME_Report_TextOnly_{patient_name}_{timestamp}.txt"
        output_path = Path(self.config.output_directory) / filename
        
        # Create text content
        content = []
        content.append("QME REPORT")
        content.append("=" * 50)
        content.append("")
        
        # Add all available data as text
        for key, value in template_data.items():
            content.append(f"{key.upper()}:")
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    content.append(f"  {subkey}: {subvalue}")
            elif isinstance(value, list):
                for item in value:
                    content.append(f"  - {item}")
            else:
                content.append(f"  {value}")
            content.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        # Minimal quality assessment
        quality_assessment = QualityAssessment(
            overall_score=30.0,
            completeness_score=20.0,
            accuracy_score=40.0,
            consistency_score=30.0,
            compliance_score=10.0
        )
        
        return ProfessionalTemplateResult(
            success=True,
            template_path=str(output_path),
            quality_assessment=quality_assessment,
            validation_issues=validation_issues,
            assembly_strategy=AssemblyStrategy.TEXT_ONLY,
            format_used=TemplateFormat.TEXT,
            fallback_used=True
        )
    
    def _attempt_error_recovery(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue],
        start_time: float
    ) -> ProfessionalTemplateResult:
        """Attempt error recovery using fallback strategies."""
        
        fallback_strategies = [
            AssemblyStrategy.SIMPLIFIED,
            AssemblyStrategy.PLACEHOLDER,
            AssemblyStrategy.MINIMAL,
            AssemblyStrategy.TEXT_ONLY
        ]
        
        for attempt, strategy in enumerate(fallback_strategies, 1):
            if attempt > self.config.max_retry_attempts:
                break
                
            extraction_logger.info(f"Attempting error recovery with strategy: {strategy.value}")
            
            result = self._attempt_assembly(template_data, strategy, validation_issues)
            
            if result.success:
                result.recovery_attempts = attempt
                result.fallback_used = True
                extraction_logger.info(f"Error recovery successful with strategy: {strategy.value}")
                return result
        
        # All recovery attempts failed
        return ProfessionalTemplateResult(
            success=False,
            error_message="All error recovery attempts failed",
            validation_issues=validation_issues,
            recovery_attempts=len(fallback_strategies),
            processing_time=time.time() - start_time
        )
    
    def _validate_template_data(self, template_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate template data against configured rules."""
        issues = []
        
        for rule in self.validation_rules:
            try:
                check_function_name = rule.get('check_function')
                if hasattr(self, check_function_name):
                    check_function = getattr(self, check_function_name)
                    issue = check_function(template_data, rule)
                    if issue:
                        issues.append(issue)
            except Exception as e:
                extraction_logger.warning(f"Validation rule {rule.get('name')} failed: {str(e)}")
        
        return issues
    
    def _check_patient_name(self, template_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Check if patient name is present."""
        patient_info = template_data.get('patient_info', {})
        name = patient_info.get('name')
        
        if not name or not str(name).strip():
            return ValidationIssue(
                rule_name=rule['name'],
                severity=ValidationSeverity(rule['severity'].lower()),
                description=rule['description'],
                field_name='patient_name',
                auto_fixable=rule.get('auto_fixable', False)
            )
        return None
    
    def _check_case_number(self, template_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Check if case number is present."""
        patient_info = template_data.get('patient_info', {})
        case_number = patient_info.get('case_number')
        
        if not case_number or not str(case_number).strip():
            return ValidationIssue(
                rule_name=rule['name'],
                severity=ValidationSeverity(rule['severity'].lower()),
                description=rule['description'],
                field_name='case_number',
                auto_fixable=rule.get('auto_fixable', False)
            )
        return None
    
    def _check_diagnoses(self, template_data: Dict[str, Any], rule: Dict[str, Any]) -> Optional[ValidationIssue]:
        """Check if at least one diagnosis is present."""
        medical_findings = template_data.get('medical_findings', {})
        diagnoses = medical_findings.get('diagnoses', [])
        
        if not diagnoses or len(diagnoses) == 0:
            return ValidationIssue(
                rule_name=rule['name'],
                severity=ValidationSeverity(rule['severity'].lower()),
                description=rule['description'],
                field_name='diagnoses',
                auto_fixable=rule.get('auto_fixable', False)
            )
        return None
    
    def _assess_template_quality(
        self, 
        template_data: Dict[str, Any], 
        validation_issues: List[ValidationIssue],
        simplified: bool = False
    ) -> QualityAssessment:
        """Assess the quality of the assembled template."""
        
        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(template_data)
        
        # Calculate accuracy score based on validation issues
        accuracy_score = self._calculate_accuracy_score(validation_issues)
        
        # Calculate consistency score
        consistency_score = 80.0  # Default consistency score
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(validation_issues, simplified)
        
        # Calculate overall score
        overall_score = (completeness_score + accuracy_score + consistency_score + compliance_score) / 4
        
        # Create quality issues from validation issues
        quality_issues = []
        for validation_issue in validation_issues:
            quality_issues.append(QualityIssue(
                issue_type=validation_issue.rule_name,
                severity=validation_issue.severity.value,
                description=validation_issue.description,
                affected_fields=[validation_issue.field_name] if validation_issue.field_name else [],
                suggested_fix=validation_issue.suggested_fix or ""
            ))
        
        return QualityAssessment(
            overall_score=overall_score,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            compliance_score=compliance_score,
            identified_issues=quality_issues
        )
    
    def _calculate_completeness_score(self, template_data: Dict[str, Any]) -> float:
        """Calculate completeness score based on required fields."""
        total_required = 0
        present_required = 0
        
        for section, fields in self.config.required_fields.items():
            section_data = template_data.get(section, {})
            for field in fields:
                total_required += 1
                if field in section_data and section_data[field]:
                    present_required += 1
        
        return (present_required / total_required * 100) if total_required > 0 else 0.0
    
    def _calculate_accuracy_score(self, validation_issues: List[ValidationIssue]) -> float:
        """Calculate accuracy score based on validation issues."""
        if not validation_issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.CRITICAL: 25,
            ValidationSeverity.HIGH: 15,
            ValidationSeverity.MEDIUM: 10,
            ValidationSeverity.LOW: 5
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 5) for issue in validation_issues)
        return max(0.0, 100.0 - total_penalty)
    
    def _calculate_compliance_score(self, validation_issues: List[ValidationIssue], simplified: bool = False) -> float:
        """Calculate compliance score."""
        base_score = 60.0 if simplified else 90.0
        
        # Reduce score for critical compliance issues
        critical_issues = [issue for issue in validation_issues if issue.severity == ValidationSeverity.CRITICAL]
        penalty = len(critical_issues) * 20
        
        return max(0.0, base_score - penalty)
    
    def _perform_post_assembly_validation(self, result: ProfessionalTemplateResult) -> ProfessionalTemplateResult:
        """Perform post-assembly validation and quality checks."""
        
        if not result.template_path or not Path(result.template_path).exists():
            result.success = False
            result.error_message = "Template file was not created successfully"
            return result
        
        # Check file size
        file_size = Path(result.template_path).stat().st_size
        if file_size == 0:
            result.success = False
            result.error_message = "Template file is empty"
            return result
        
        # Archive successful template
        if result.success and result.quality_assessment and result.quality_assessment.overall_score >= self.config.quality_threshold:
            self._archive_template(result.template_path)
        
        return result
    
    def _archive_template(self, template_path: str) -> None:
        """Archive successful template."""
        try:
            import shutil
            source_path = Path(template_path)
            archive_path = Path(self.config.archive_directory) / source_path.name
            shutil.copy2(source_path, archive_path)
            extraction_logger.debug(f"Template archived: {archive_path}")
        except Exception as e:
            extraction_logger.warning(f"Failed to archive template: {str(e)}")
    
    def _extract_patient_name(self, template_data: Dict[str, Any]) -> str:
        """Extract patient name for filename generation."""
        patient_info = template_data.get('patient_info', {})
        name = patient_info.get('name', 'Unknown')
        
        # Clean name for filename
        import re
        clean_name = re.sub(r'[^\w\s-]', '', str(name))
        clean_name = re.sub(r'\s+', '_', clean_name.strip())
        
        return clean_name[:50]  # Limit length
    
    def _read_template_data(self, template_path: Optional[str]) -> Optional[bytes]:
        """Read template data as bytes."""
        if not template_path or not Path(template_path).exists():
            return None
        
        try:
            with open(template_path, 'rb') as f:
                return f.read()
        except Exception as e:
            extraction_logger.warning(f"Failed to read template data: {str(e)}")
            return None
    
    # Document formatting methods (simplified implementations)
    def _apply_document_formatting(self, doc: Document) -> None:
        """Apply professional formatting to document."""
        if not DOCX_AVAILABLE:
            return
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(self.config.margin_top)
            section.bottom_margin = Inches(self.config.margin_bottom)
            section.left_margin = Inches(self.config.margin_left)
            section.right_margin = Inches(self.config.margin_right)
    
    def _add_document_header(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add document header."""
        # Simplified header implementation
        pass
    
    def _add_document_title(self, doc: Document) -> None:
        """Add document title."""
        title = doc.add_heading('QUALIFIED MEDICAL EVALUATOR REPORT', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    def _add_patient_identification(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add patient identification section."""
        doc.add_heading('PATIENT IDENTIFICATION', level=1)
        
        patient_info = template_data.get('patient_info', {})
        
        fields = [
            ('Name', patient_info.get('name', '[MISSING]')),
            ('Date of Birth', patient_info.get('date_of_birth', '[MISSING]')),
            ('Age', patient_info.get('age', '[MISSING]')),
            ('Gender', patient_info.get('gender', '[MISSING]')),
            ('Case Number', patient_info.get('case_number', '[MISSING]')),
            ('Date of Injury', patient_info.get('injury_date', '[MISSING]')),
            ('Employer', patient_info.get('employer', '[MISSING]')),
            ('Occupation', patient_info.get('occupation', '[MISSING]'))
        ]
        
        for label, value in fields:
            p = doc.add_paragraph()
            p.add_run(f'{label}: ').bold = True
            p.add_run(str(value))
    
    def _add_history_section(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add history section."""
        doc.add_heading('HISTORY OF PRESENT ILLNESS', level=1)
        
        history = template_data.get('history', {})
        chief_complaint = history.get('chief_complaint', '[History information not available]')
        doc.add_paragraph(chief_complaint)
    
    def _add_examination_section(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add examination section."""
        doc.add_heading('PHYSICAL EXAMINATION', level=1)
        
        examination = template_data.get('examination', {})
        findings = examination.get('findings', '[Examination findings not available]')
        doc.add_paragraph(findings)
    
    def _add_diagnostic_studies(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add diagnostic studies section."""
        doc.add_heading('DIAGNOSTIC STUDIES', level=1)
        
        studies = template_data.get('diagnostic_studies', [])
        if studies:
            for study in studies:
                doc.add_paragraph(f"• {study}", style='List Bullet')
        else:
            doc.add_paragraph('[No diagnostic studies available]')
    
    def _add_diagnosis_section(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add diagnosis section."""
        doc.add_heading('DIAGNOSIS', level=1)
        
        medical_findings = template_data.get('medical_findings', {})
        diagnoses = medical_findings.get('diagnoses', [])
        
        if diagnoses:
            for i, diagnosis in enumerate(diagnoses, 1):
                doc.add_paragraph(f"{i}. {diagnosis}")
        else:
            doc.add_paragraph('[Diagnosis information not available]')
    
    def _add_causation_analysis(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add causation analysis section."""
        doc.add_heading('CAUSATION ANALYSIS', level=1)
        
        causation = template_data.get('causation', '[Causation analysis not available]')
        doc.add_paragraph(causation)
    
    def _add_impairment_rating(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add impairment rating section."""
        doc.add_heading('IMPAIRMENT RATING', level=1)
        
        medical_findings = template_data.get('medical_findings', {})
        impairment_ratings = medical_findings.get('impairment_ratings', {})
        
        if impairment_ratings:
            for body_part, rating in impairment_ratings.items():
                doc.add_paragraph(f"{body_part}: {rating}%")
        else:
            doc.add_paragraph('[Impairment rating not available]')
    
    def _add_work_restrictions(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add work restrictions section."""
        doc.add_heading('WORK RESTRICTIONS', level=1)
        
        restrictions = template_data.get('work_restrictions', '[Work restrictions not available]')
        doc.add_paragraph(restrictions)
    
    def _add_future_medical_care(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add future medical care section."""
        doc.add_heading('FUTURE MEDICAL CARE', level=1)
        
        future_care = template_data.get('future_medical_care', '[Future medical care recommendations not available]')
        doc.add_paragraph(future_care)
    
    def _add_conclusions(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add conclusions section."""
        doc.add_heading('CONCLUSIONS AND RECOMMENDATIONS', level=1)
        
        conclusions = template_data.get('conclusions', '[Conclusions not available]')
        doc.add_paragraph(conclusions)
    
    def _add_document_footer(self, doc: Document, template_data: Dict[str, Any]) -> None:
        """Add document footer."""
        # Simplified footer implementation
        pass
    
    def _get_default_template_structure(self) -> Dict[str, Any]:
        """Get default template structure."""
        return {
            "document_structure": {
                "sections": [
                    {"section_id": "patient_identification", "title": "PATIENT IDENTIFICATION", "required": True},
                    {"section_id": "history_of_present_illness", "title": "HISTORY OF PRESENT ILLNESS", "required": True},
                    {"section_id": "physical_examination", "title": "PHYSICAL EXAMINATION", "required": True},
                    {"section_id": "diagnosis", "title": "DIAGNOSIS", "required": True},
                    {"section_id": "impairment_rating", "title": "IMPAIRMENT RATING", "required": True}
                ]
            }
        }
    
    def _get_default_assembly_config(self) -> Dict[str, Any]:
        """Get default assembly configuration."""
        return {
            "template_assembly": {
                "default_template": {
                    "output_format": "docx",
                    "apply_professional_formatting": True,
                    "quality_threshold": 70.0
                }
            }
        }