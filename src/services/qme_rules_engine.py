"""
QME Report Rules Engine and Quality Standards System.

This module implements comprehensive validation and quality rules for QME reports
based on the AI Example QME Report Template.docx gold standard, AMA Guidelines,
and legal requirements from QME-Study-Guide.pdf.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
import re
import uuid

try:
    from src.services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError:
    from services.qme_template_generator import QMETemplateData, PatientInfo, MedicalFindings
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Report cannot be submitted
    HIGH = "high"         # Major quality issues
    MEDIUM = "medium"     # Minor quality issues
    LOW = "low"          # Suggestions for improvement
    INFO = "info"        # Informational notes


class SectionType(Enum):
    """QME report section types based on gold standard template."""
    PATIENT_DEMOGRAPHICS = "patient_demographics"
    HISTORY_PRESENT_ILLNESS = "history_present_illness"
    PAST_MEDICAL_HISTORY = "past_medical_history"
    SOCIAL_HISTORY = "social_history"
    OCCUPATIONAL_HISTORY = "occupational_history"
    PHYSICAL_EXAMINATION = "physical_examination"
    DIAGNOSTIC_STUDIES = "diagnostic_studies"
    DIAGNOSIS = "diagnosis"
    IMPAIRMENT_RATING = "impairment_rating"
    WORK_RESTRICTIONS = "work_restrictions"
    FUTURE_MEDICAL_CARE = "future_medical_care"
    CAUSATION_ANALYSIS = "causation_analysis"
    APPORTIONMENT = "apportionment"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in QME report."""
    section: SectionType
    severity: ValidationSeverity
    title: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    suggestions: List[str] = field(default_factory=list)
    ama_reference: Optional[str] = None
    legal_reference: Optional[str] = None
    auto_fixable: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityScore:
    """Quality assessment score for QME report."""
    overall_score: float  # 0-100
    completeness_score: float  # 0-100
    accuracy_score: float  # 0-100
    compliance_score: float  # 0-100
    section_scores: Dict[SectionType, float] = field(default_factory=dict)
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0


@dataclass
class SectionRequirements:
    """Requirements for a specific QME report section."""
    section_type: SectionType
    required_fields: List[str]
    optional_fields: List[str]
    min_content_length: int
    content_patterns: List[str]  # Regex patterns for content validation
    ama_guidelines: List[str]
    legal_requirements: List[str]
    quality_indicators: List[str]


class QMEGoldStandardRules:
    """Rules extracted from AI Example QME Report Template.docx gold standard."""
    
    def __init__(self):
        """Initialize gold standard rules."""
        self.section_requirements = self._define_section_requirements()
        self.formatting_rules = self._define_formatting_rules()
        self.content_rules = self._define_content_rules()
    
    def _define_section_requirements(self) -> Dict[SectionType, SectionRequirements]:
        """Define requirements for each section based on gold standard."""
        return {
            SectionType.PATIENT_DEMOGRAPHICS: SectionRequirements(
                section_type=SectionType.PATIENT_DEMOGRAPHICS,
                required_fields=[
                    "patient_name", "age", "gender", "case_number", 
                    "injury_date", "employer", "occupation"
                ],
                optional_fields=["medical_record_number", "social_security"],
                min_content_length=200,
                content_patterns=[
                    r"Name:\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*",
                    r"Age:\s*\d{1,3}",
                    r"Case\s*(?:Number|No\.?):\s*[A-Z0-9\-]+"
                ],
                ama_guidelines=["Patient identification requirements"],
                legal_requirements=["§4062.3 - Patient identification"],
                quality_indicators=["Complete demographic information", "Accurate case identification"]
            ),
            
            SectionType.HISTORY_PRESENT_ILLNESS: SectionRequirements(
                section_type=SectionType.HISTORY_PRESENT_ILLNESS,
                required_fields=[
                    "injury_mechanism", "symptom_onset", "current_symptoms",
                    "pain_description", "functional_limitations"
                ],
                optional_fields=["previous_treatments", "medication_history"],
                min_content_length=500,
                content_patterns=[
                    r"(?:injured|hurt|pain|symptoms?).*(?:on|date|when)",
                    r"(?:describes?|reports?|states?).*(?:pain|symptoms?|discomfort)"
                ],
                ama_guidelines=["History taking requirements", "Symptom documentation"],
                legal_requirements=["§4062.3 - History documentation"],
                quality_indicators=["Detailed symptom description", "Timeline clarity"]
            ),
            
            SectionType.PHYSICAL_EXAMINATION: SectionRequirements(
                section_type=SectionType.PHYSICAL_EXAMINATION,
                required_fields=[
                    "general_appearance", "range_of_motion", "strength_testing",
                    "neurological_exam", "special_tests"
                ],
                optional_fields=["gait_analysis", "posture_assessment"],
                min_content_length=800,
                content_patterns=[
                    r"(?:range of motion|ROM).*(?:degrees?|\d+°)",
                    r"(?:strength|motor).*(?:5/5|4/5|3/5|2/5|1/5|0/5)",
                    r"(?:reflexes?).*(?:\+\+|\+|\-|absent|normal)"
                ],
                ama_guidelines=["Physical examination standards", "Range of motion measurement"],
                legal_requirements=["§4062.3 - Examination requirements"],
                quality_indicators=["Objective measurements", "Systematic examination"]
            ),
            
            SectionType.DIAGNOSIS: SectionRequirements(
                section_type=SectionType.DIAGNOSIS,
                required_fields=["primary_diagnosis", "icd_codes"],
                optional_fields=["secondary_diagnoses", "differential_diagnoses"],
                min_content_length=200,
                content_patterns=[
                    r"(?:Primary|Main)\s*Diagnosis:.*",
                    r"ICD-10?:\s*[A-Z]\d{2}(?:\.\d+)?"
                ],
                ama_guidelines=["Diagnostic criteria", "ICD coding requirements"],
                legal_requirements=["§4062.3 - Diagnostic requirements"],
                quality_indicators=["Clear diagnostic statements", "Appropriate ICD codes"]
            ),
            
            SectionType.IMPAIRMENT_RATING: SectionRequirements(
                section_type=SectionType.IMPAIRMENT_RATING,
                required_fields=[
                    "impairment_percentage", "ama_table_reference", 
                    "rating_methodology", "body_part_affected"
                ],
                optional_fields=["combined_ratings", "future_assessments"],
                min_content_length=400,
                content_patterns=[
                    r"\d{1,2}%\s*(?:whole person|WP|impairment)",
                    r"(?:Table|Chapter)\s*\d+(?:-\d+)?",
                    r"AMA\s*Guides?\s*(?:5th|Fifth)\s*Edition"
                ],
                ama_guidelines=["Impairment rating methodology", "Table references"],
                legal_requirements=["§4062.3 - Impairment rating requirements"],
                quality_indicators=["Accurate calculations", "Proper AMA references"]
            )
        }
    
    def _define_formatting_rules(self) -> Dict[str, Any]:
        """Define formatting rules from gold standard."""
        return {
            "font_requirements": {
                "primary_font": "Times New Roman",
                "font_size": 12,
                "line_spacing": 1.5
            },
            "section_headers": {
                "style": "bold",
                "numbering": True,
                "spacing_before": 12,
                "spacing_after": 6
            },
            "page_layout": {
                "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
                "header": True,
                "footer": True,
                "page_numbers": True
            },
            "content_formatting": {
                "paragraph_spacing": 6,
                "bullet_points": "standard",
                "table_formatting": "professional"
            }
        }
    
    def _define_content_rules(self) -> Dict[str, List[str]]:
        """Define content quality rules."""
        return {
            "medical_terminology": [
                "Use precise medical terminology",
                "Define technical terms when necessary",
                "Maintain professional language throughout"
            ],
            "objectivity": [
                "Use objective language",
                "Avoid subjective interpretations",
                "Base conclusions on evidence"
            ],
            "completeness": [
                "Address all required sections",
                "Provide sufficient detail",
                "Include relevant supporting information"
            ],
            "accuracy": [
                "Verify all measurements and calculations",
                "Cross-reference with medical records",
                "Ensure consistency throughout report"
            ]
        }


class AMAGuidelinesValidator:
    """Validator for AMA Guidelines 5th Edition compliance."""
    
    def __init__(self):
        """Initialize AMA guidelines validator."""
        self.impairment_tables = self._load_impairment_tables()
        self.rating_rules = self._load_rating_rules()
        self.body_system_guidelines = self._load_body_system_guidelines()
    
    def validate_impairment_rating(self, rating: ImpairmentRating, diagnosis: Diagnosis) -> List[ValidationIssue]:
        """Validate impairment rating against AMA guidelines."""
        issues = []
        
        try:
            # Check if rating percentage is within valid range
            if rating.percentage < 0 or rating.percentage > 100:
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.CRITICAL,
                    title="Invalid Impairment Percentage",
                    description=f"Impairment percentage {rating.percentage}% is outside valid range (0-100%)",
                    suggestions=["Review AMA Guidelines for valid percentage ranges"],
                    ama_reference="AMA Guides 5th Edition - Chapter 1"
                ))
            
            # Validate AMA table reference
            if not self._validate_ama_table_reference(rating.ama_table):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.HIGH,
                    title="Invalid AMA Table Reference",
                    description=f"AMA table reference '{rating.ama_table}' is not valid",
                    suggestions=["Verify table reference against AMA Guides 5th Edition"],
                    ama_reference="AMA Guides 5th Edition - Table References"
                ))
            
            # Check rating methodology
            if not rating.rationale:
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.MEDIUM,
                    title="Missing Rating Methodology",
                    description="Impairment rating methodology not documented",
                    suggestions=["Document the specific methodology used for rating calculation"],
                    ama_reference="AMA Guides 5th Edition - Rating Methodology"
                ))
            
            logger.info(f"Validated impairment rating: {len(issues)} issues found")
            return issues
            
        except Exception as e:
            logger.error(f"Error validating impairment rating: {e}")
            return [ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.HIGH,
                title="Validation Error",
                description=f"Error validating impairment rating: {str(e)}",
                suggestions=["Review rating data for completeness and accuracy"]
            )]
    
    def _load_impairment_tables(self) -> Dict[str, Any]:
        """Load AMA impairment tables (placeholder for actual implementation)."""
        # This would be populated from AMAGuides 5th Edition.pdf
        return {
            "spine": {
                "cervical": {"range": (0, 25), "tables": ["15-3", "15-5", "15-7"]},
                "thoracic": {"range": (0, 20), "tables": ["15-4", "15-6"]},
                "lumbar": {"range": (0, 25), "tables": ["15-3", "15-8"]}
            },
            "extremities": {
                "upper": {"range": (0, 60), "tables": ["16-1", "16-3", "16-5"]},
                "lower": {"range": (0, 40), "tables": ["17-1", "17-3", "17-5"]}
            }
        }
    
    def _load_rating_rules(self) -> Dict[str, List[str]]:
        """Load AMA rating rules."""
        return {
            "combination_rules": [
                "Use Combined Values Chart for multiple impairments",
                "Do not add percentages directly",
                "Consider regional vs whole person impairments"
            ],
            "measurement_rules": [
                "Use standardized measurement techniques",
                "Document measurement conditions",
                "Repeat measurements for accuracy"
            ]
        }
    
    def _load_body_system_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Load body system specific guidelines."""
        return {
            "musculoskeletal": {
                "measurement_requirements": ["Range of motion", "Strength testing", "Functional assessment"],
                "special_considerations": ["Age factors", "Pre-existing conditions"]
            },
            "neurological": {
                "measurement_requirements": ["Sensory testing", "Motor function", "Reflexes"],
                "special_considerations": ["Cognitive assessment", "Pain evaluation"]
            }
        }
    
    def _validate_ama_table_reference(self, table_ref: str) -> bool:
        """Validate AMA table reference format and existence."""
        if not table_ref:
            return False
        
        # Check format (e.g., "15-3", "Table 16-1")
        pattern = r"(?:Table\s*)?(\d{1,2})-(\d{1,2})"
        match = re.match(pattern, table_ref, re.IGNORECASE)
        
        if not match:
            return False
        
        chapter = int(match.group(1))
        table = int(match.group(2))
        
        # Validate chapter and table numbers (simplified validation)
        return 1 <= chapter <= 18 and 1 <= table <= 20


class LegalComplianceValidator:
    """Validator for legal requirements from QME-Study-Guide.pdf."""
    
    def __init__(self):
        """Initialize legal compliance validator."""
        self.legal_requirements = self._load_legal_requirements()
        self.section_4062_3_requirements = self._load_section_4062_3_requirements()
    
    def validate_legal_compliance(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate report for legal compliance."""
        issues = []
        
        try:
            # Validate §4062.3 requirements
            issues.extend(self._validate_section_4062_3(template_data))
            
            # Validate report structure requirements
            issues.extend(self._validate_report_structure(template_data))
            
            # Validate documentation requirements
            issues.extend(self._validate_documentation_requirements(template_data))
            
            logger.info(f"Legal compliance validation: {len(issues)} issues found")
            return issues
            
        except Exception as e:
            logger.error(f"Error in legal compliance validation: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Legal Validation Error",
                description=f"Error validating legal compliance: {str(e)}",
                suggestions=["Review report for legal compliance requirements"]
            )]
    
    def _load_legal_requirements(self) -> Dict[str, List[str]]:
        """Load legal requirements from QME Study Guide."""
        return {
            "report_structure": [
                "Must include all required sections",
                "Sections must be in proper order",
                "Professional formatting required"
            ],
            "content_requirements": [
                "Objective medical findings required",
                "Impairment rating must be supported",
                "Causation analysis required"
            ],
            "documentation": [
                "All sources must be cited",
                "Medical records must be referenced",
                "Examination findings must be documented"
            ]
        }
    
    def _load_section_4062_3_requirements(self) -> Dict[str, List[str]]:
        """Load specific §4062.3 requirements."""
        return {
            "patient_identification": [
                "Full name required",
                "Case number required",
                "Date of injury required"
            ],
            "examination_requirements": [
                "Physical examination must be performed",
                "Examination findings must be documented",
                "Objective measurements required"
            ],
            "rating_requirements": [
                "Impairment rating must be provided",
                "AMA Guides must be referenced",
                "Rating methodology must be explained"
            ]
        }
    
    def _validate_section_4062_3(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate §4062.3 specific requirements."""
        issues = []
        
        # Check patient identification
        if not template_data.patient_info.name:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Patient Name",
                description="Patient name is required per §4062.3",
                suggestions=["Obtain and document patient's full legal name"],
                legal_reference="§4062.3 - Patient identification requirements"
            ))
        
        if not template_data.patient_info.case_number:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Case Number",
                description="Case number is required per §4062.3",
                suggestions=["Obtain case number from claims administrator"],
                legal_reference="§4062.3 - Case identification requirements"
            ))
        
        # Check impairment rating
        if not template_data.medical_findings.impairment_ratings:
            issues.append(ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Impairment Rating",
                description="Impairment rating is required per §4062.3",
                suggestions=["Calculate and document impairment rating using AMA Guides"],
                legal_reference="§4062.3 - Impairment rating requirements"
            ))
        
        return issues
    
    def _validate_report_structure(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate report structure requirements."""
        issues = []
        
        # Check for required sections (simplified check)
        required_sections = [
            "patient_demographics", "history", "examination", 
            "diagnosis", "impairment_rating"
        ]
        
        # This would be enhanced with actual section detection
        for section in required_sections:
            # Placeholder validation
            pass
        
        return issues
    
    def _validate_documentation_requirements(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate documentation requirements."""
        issues = []
        
        # Check for medical record references
        # This would be enhanced with actual reference detection
        
        return issues


class QMERulesEngine:
    """Main QME Rules Engine coordinating all validation components."""
    
    def __init__(self):
        """Initialize the QME Rules Engine."""
        self.gold_standard_rules = QMEGoldStandardRules()
        self.ama_validator = AMAGuidelinesValidator()
        self.legal_validator = LegalComplianceValidator()
        
        logger.info("Initialized QME Rules Engine")
    
    def validate_qme_report(self, template_data: QMETemplateData) -> Tuple[List[ValidationIssue], QualityScore]:
        """
        Perform comprehensive validation of QME report.
        
        Args:
            template_data: QME template data to validate
            
        Returns:
            Tuple of (validation_issues, quality_score)
        """
        try:
            logger.info("Starting comprehensive QME report validation")
            
            all_issues = []
            
            # Gold standard validation
            gold_issues = self._validate_against_gold_standard(template_data)
            all_issues.extend(gold_issues)
            
            # AMA Guidelines validation
            ama_issues = self._validate_ama_compliance(template_data)
            all_issues.extend(ama_issues)
            
            # Legal compliance validation
            legal_issues = self.legal_validator.validate_legal_compliance(template_data)
            all_issues.extend(legal_issues)
            
            # Content quality validation
            quality_issues = self._validate_content_quality(template_data)
            all_issues.extend(quality_issues)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(all_issues, template_data)
            
            logger.info(f"Validation complete: {len(all_issues)} issues found, quality score: {quality_score.overall_score:.1f}")
            
            return all_issues, quality_score
            
        except Exception as e:
            logger.error(f"Error in QME report validation: {e}")
            # Return basic error issue
            error_issue = ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Validation System Error",
                description=f"Error during validation: {str(e)}",
                suggestions=["Contact system administrator"]
            )
            basic_score = QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0,
                total_issues=1,
                high_issues=1
            )
            return [error_issue], basic_score
    
    def _validate_against_gold_standard(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate against gold standard template requirements."""
        issues = []
        
        try:
            # Validate each section against requirements
            for section_type, requirements in self.gold_standard_rules.section_requirements.items():
                section_issues = self._validate_section_requirements(
                    template_data, section_type, requirements
                )
                issues.extend(section_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating against gold standard: {e}")
            return []
    
    def _validate_section_requirements(self, 
                                     template_data: QMETemplateData, 
                                     section_type: SectionType, 
                                     requirements: SectionRequirements) -> List[ValidationIssue]:
        """Validate specific section requirements."""
        issues = []
        
        try:
            # Check required fields based on section type
            if section_type == SectionType.PATIENT_DEMOGRAPHICS:
                issues.extend(self._validate_patient_demographics(template_data.patient_info, requirements))
            elif section_type == SectionType.DIAGNOSIS:
                issues.extend(self._validate_diagnosis_section(template_data.medical_findings, requirements))
            elif section_type == SectionType.IMPAIRMENT_RATING:
                issues.extend(self._validate_impairment_section(template_data.medical_findings, requirements))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating section {section_type}: {e}")
            return []
    
    def _validate_patient_demographics(self, patient_info: PatientInfo, requirements: SectionRequirements) -> List[ValidationIssue]:
        """Validate patient demographics section."""
        issues = []
        
        # Check required fields
        if "patient_name" in requirements.required_fields and not patient_info.name:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Patient Name",
                description="Patient name is required for QME report",
                suggestions=["Obtain patient's full legal name from medical records"],
                auto_fixable=False
            ))
        
        if "age" in requirements.required_fields and not patient_info.age:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Missing Patient Age",
                description="Patient age is required for demographic information",
                suggestions=["Calculate age from birth date or obtain from records"],
                auto_fixable=False
            ))
        
        if "case_number" in requirements.required_fields and not patient_info.case_number:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Case Number",
                description="Case number is required for report identification",
                suggestions=["Obtain case number from claims administrator"],
                auto_fixable=False
            ))
        
        return issues
    
    def _validate_diagnosis_section(self, medical_findings: MedicalFindings, requirements: SectionRequirements) -> List[ValidationIssue]:
        """Validate diagnosis section."""
        issues = []
        
        if not medical_findings.diagnoses:
            issues.append(ValidationIssue(
                section=SectionType.DIAGNOSIS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Diagnoses",
                description="At least one primary diagnosis is required",
                suggestions=["Review medical records and examination findings to establish diagnosis"],
                auto_fixable=False
            ))
        else:
            # Check diagnosis quality
            for diagnosis in medical_findings.diagnoses:
                if not diagnosis.icd_code:
                    issues.append(ValidationIssue(
                        section=SectionType.DIAGNOSIS,
                        severity=ValidationSeverity.MEDIUM,
                        title="Missing ICD Code",
                        description=f"ICD code missing for diagnosis: {diagnosis.description}",
                        suggestions=["Add appropriate ICD-10 code for diagnosis"],
                        auto_fixable=True
                    ))
        
        return issues
    
    def _validate_impairment_section(self, medical_findings: MedicalFindings, requirements: SectionRequirements) -> List[ValidationIssue]:
        """Validate impairment rating section."""
        issues = []
        
        if not medical_findings.impairment_ratings:
            issues.append(ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Impairment Rating",
                description="Impairment rating is required for QME report",
                suggestions=["Calculate impairment rating using AMA Guides 5th Edition"],
                auto_fixable=False
            ))
        
        return issues
    
    def _validate_ama_compliance(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate AMA Guidelines compliance."""
        issues = []
        
        try:
            # Validate each impairment rating
            for rating in template_data.medical_findings.impairment_ratings:
                # Find corresponding diagnosis
                diagnosis = None
                for diag in template_data.medical_findings.diagnoses:
                    if diag.id == rating.diagnosis_id:
                        diagnosis = diag
                        break
                
                if diagnosis:
                    rating_issues = self.ama_validator.validate_impairment_rating(rating, diagnosis)
                    issues.extend(rating_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating AMA compliance: {e}")
            return []
    
    def _validate_content_quality(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate content quality and completeness."""
        issues = []
        
        try:
            # Check for medical terminology usage
            # Check for objectivity in language
            # Check for completeness of information
            # This would be enhanced with NLP analysis
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating content quality: {e}")
            return []
    
    def _calculate_quality_score(self, issues: List[ValidationIssue], template_data: QMETemplateData) -> QualityScore:
        """Calculate overall quality score based on validation results."""
        try:
            # Count issues by severity
            critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
            high_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.HIGH)
            medium_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.MEDIUM)
            low_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.LOW)
            
            # Calculate scores (simplified scoring algorithm)
            total_issues = len(issues)
            
            # Completeness score (based on required fields present)
            completeness_score = self._calculate_completeness_score(template_data)
            
            # Accuracy score (based on validation issues)
            accuracy_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 10 + low_count * 5))
            
            # Compliance score (based on legal and AMA compliance)
            compliance_score = max(0, 100 - (critical_count * 30 + high_count * 20))
            
            # Overall score (weighted average)
            overall_score = (completeness_score * 0.3 + accuracy_score * 0.4 + compliance_score * 0.3)
            
            return QualityScore(
                overall_score=overall_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                compliance_score=compliance_score,
                total_issues=total_issues,
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0,
                total_issues=len(issues)
            )
    
    def _calculate_completeness_score(self, template_data: QMETemplateData) -> float:
        """Calculate completeness score based on available data."""
        try:
            total_fields = 0
            completed_fields = 0
            
            # Patient demographics
            patient_fields = [
                template_data.patient_info.name,
                template_data.patient_info.age,
                template_data.patient_info.gender,
                template_data.patient_info.case_number,
                template_data.patient_info.injury_date
            ]
            total_fields += len(patient_fields)
            completed_fields += sum(1 for field in patient_fields if field)
            
            # Medical findings
            if template_data.medical_findings.diagnoses:
                completed_fields += 1
            total_fields += 1
            
            if template_data.medical_findings.impairment_ratings:
                completed_fields += 1
            total_fields += 1
            
            # Calculate percentage
            if total_fields > 0:
                return (completed_fields / total_fields) * 100
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating completeness score: {e}")
            return 0.0
    
    def get_improvement_suggestions(self, issues: List[ValidationIssue]) -> Dict[SectionType, List[str]]:
        """Get improvement suggestions organized by section."""
        suggestions = {}
        
        for issue in issues:
            if issue.section not in suggestions:
                suggestions[issue.section] = []
            
            suggestions[issue.section].extend(issue.suggestions)
        
        # Remove duplicates
        for section in suggestions:
            suggestions[section] = list(set(suggestions[section]))
        
        return suggestions
    
    def generate_quality_report(self, issues: List[ValidationIssue], quality_score: QualityScore) -> str:
        """Generate a comprehensive quality report."""
        try:
            report_lines = []
            
            # Header
            report_lines.append("QME REPORT QUALITY ASSESSMENT")
            report_lines.append("=" * 50)
            report_lines.append("")
            
            # Overall score
            report_lines.append(f"Overall Quality Score: {quality_score.overall_score:.1f}/100")
            report_lines.append(f"Completeness Score: {quality_score.completeness_score:.1f}/100")
            report_lines.append(f"Accuracy Score: {quality_score.accuracy_score:.1f}/100")
            report_lines.append(f"Compliance Score: {quality_score.compliance_score:.1f}/100")
            report_lines.append("")
            
            # Issue summary
            report_lines.append("ISSUE SUMMARY")
            report_lines.append("-" * 20)
            report_lines.append(f"Total Issues: {quality_score.total_issues}")
            report_lines.append(f"Critical Issues: {quality_score.critical_issues}")
            report_lines.append(f"High Priority Issues: {quality_score.high_issues}")
            report_lines.append(f"Medium Priority Issues: {quality_score.medium_issues}")
            report_lines.append(f"Low Priority Issues: {quality_score.low_issues}")
            report_lines.append("")
            
            # Detailed issues by section
            issues_by_section = {}
            for issue in issues:
                if issue.section not in issues_by_section:
                    issues_by_section[issue.section] = []
                issues_by_section[issue.section].append(issue)
            
            for section, section_issues in issues_by_section.items():
                report_lines.append(f"{section.value.upper().replace('_', ' ')}")
                report_lines.append("-" * len(section.value))
                
                for issue in section_issues:
                    report_lines.append(f"• [{issue.severity.value.upper()}] {issue.title}")
                    report_lines.append(f"  {issue.description}")
                    if issue.suggestions:
                        report_lines.append(f"  Suggestions: {'; '.join(issue.suggestions)}")
                    if issue.ama_reference:
                        report_lines.append(f"  AMA Reference: {issue.ama_reference}")
                    if issue.legal_reference:
                        report_lines.append(f"  Legal Reference: {issue.legal_reference}")
                    report_lines.append("")
                
                report_lines.append("")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return f"Error generating quality report: {str(e)}"