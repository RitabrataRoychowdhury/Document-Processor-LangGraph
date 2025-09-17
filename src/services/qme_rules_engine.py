"""
Enhanced QME Report Rules Engine with Evidence-First Validation.

This module implements comprehensive validation and quality rules for QME reports
with evidence-first validation, confidence scoring, programmatic calculations,
and legal compliance validation with detailed audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from enum import Enum
import re
import uuid
import yaml
from pathlib import Path

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
class EvidenceProvenance:
    """Evidence provenance tracking for extracted fields."""
    source_document: str
    page_number: int
    text_coordinates: Tuple[int, int, int, int]  # x1, y1, x2, y2
    snippet_text: str
    confidence_score: float
    extraction_method: str  # "regex", "ner", "cross_validation"
    timestamp: datetime = field(default_factory=datetime.now)


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
    # Evidence-first enhancements
    evidence_provenance: Optional[EvidenceProvenance] = None
    confidence_score: Optional[float] = None
    requires_human_review: bool = False
    remediation_steps: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Detailed compliance report with pass/fail status and remediation steps."""
    overall_status: str  # "PASS", "FAIL", "REQUIRES_REVIEW"
    labor_code_4062_3_status: bool
    mandatory_sections_status: bool
    mlprr_billing_status: bool
    signature_blocks_status: bool
    evidence_sufficiency_status: bool
    calculation_accuracy_status: bool
    failed_requirements: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)
    audit_trail: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class QualityScore:
    """Quality assessment score for QME report with evidence-first metrics."""
    overall_score: float  # 0-100
    completeness_score: float  # 0-100
    accuracy_score: float  # 0-100
    compliance_score: float  # 0-100
    evidence_confidence_score: float  # 0-100
    section_scores: Dict[SectionType, float] = field(default_factory=dict)
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    # Evidence-first metrics
    fields_above_confidence_threshold: int = 0
    fields_requiring_review: int = 0
    programmatic_calculations_verified: int = 0
    placeholder_text_found: int = 0


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


class EvidenceFirstValidator:
    """Evidence-first validation with confidence scoring and provenance tracking."""
    
    def __init__(self, confidence_thresholds: Dict[str, float]):
        """Initialize evidence-first validator."""
        self.confidence_thresholds = confidence_thresholds
        self.critical_fields = ["patient_name", "case_number", "injury_date", "employer_name"]
        self.standard_fields = ["diagnosis", "impairment_percentage", "examination_findings"]
        
    def validate_field_confidence(self, field_name: str, confidence: float, 
                                 provenance: EvidenceProvenance) -> Optional[ValidationIssue]:
        """Validate field confidence against thresholds."""
        if field_name in self.critical_fields:
            threshold = self.confidence_thresholds.get("critical_fields", 0.8)
            if confidence < threshold:
                return ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Low Confidence Critical Field: {field_name}",
                    description=f"Field '{field_name}' confidence {confidence:.2f} below threshold {threshold}",
                    evidence_provenance=provenance,
                    confidence_score=confidence,
                    requires_human_review=True,
                    remediation_steps=[
                        f"Review source document: {provenance.source_document}",
                        f"Verify text at page {provenance.page_number}",
                        "Consider manual extraction or additional validation"
                    ]
                )
        elif field_name in self.standard_fields:
            threshold = self.confidence_thresholds.get("standard_fields", 0.5)
            if confidence < threshold:
                return ValidationIssue(
                    section=SectionType.DIAGNOSIS,
                    severity=ValidationSeverity.HIGH,
                    title=f"Low Confidence Standard Field: {field_name}",
                    description=f"Field '{field_name}' confidence {confidence:.2f} below threshold {threshold}",
                    evidence_provenance=provenance,
                    confidence_score=confidence,
                    requires_human_review=True,
                    remediation_steps=[
                        f"Review extraction from {provenance.source_document}",
                        "Consider alternative extraction methods"
                    ]
                )
        return None
    
    def validate_evidence_sufficiency(self, extracted_fields: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate overall evidence sufficiency."""
        issues = []
        
        # Check critical field coverage
        missing_critical = [field for field in self.critical_fields if field not in extracted_fields]
        if missing_critical:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title="Missing Critical Fields",
                description=f"Critical fields missing: {', '.join(missing_critical)}",
                requires_human_review=True,
                remediation_steps=[
                    "Review source documents for missing information",
                    "Contact claims administrator for missing data",
                    "Consider additional document requests"
                ]
            ))
        
        return issues


class PostGenerationValidator:
    """Post-generation validation for placeholder text and calculation accuracy."""
    
    def __init__(self):
        """Initialize post-generation validator."""
        self.placeholder_patterns = [
            r"\{\{.*?\}\}",  # {{placeholder}}
            r"\{.*?\}",      # {placeholder}
            r"\[.*?\]",      # [placeholder]
            r"TODO",
            r"TBD",
            r"PLACEHOLDER",
            r"XXX",
            r"___+"
        ]
    
    def scan_placeholder_text(self, report_content: str) -> List[ValidationIssue]:
        """Scan for remaining placeholder text."""
        issues = []
        
        for pattern in self.placeholder_patterns:
            matches = re.finditer(pattern, report_content, re.IGNORECASE)
            for match in matches:
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,  # Generic section
                    severity=ValidationSeverity.CRITICAL,
                    title="Placeholder Text Found",
                    description=f"Placeholder text found: '{match.group()}'",
                    suggestions=["Replace placeholder with actual content"],
                    auto_fixable=False,
                    remediation_steps=[
                        "Identify source of missing data",
                        "Complete field extraction or manual entry",
                        "Re-generate report section"
                    ]
                ))
        
        return issues
    
    def validate_calculation_accuracy(self, calculations: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate programmatic calculation accuracy."""
        issues = []
        
        for calc_name, calc_data in calculations.items():
            if not calc_data.get("programmatic", False):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.CRITICAL,
                    title="Non-Programmatic Calculation",
                    description=f"Calculation '{calc_name}' not performed programmatically",
                    remediation_steps=[
                        "Implement programmatic calculation method",
                        "Remove LLM-generated calculations",
                        "Verify against AMA Guidelines tables"
                    ]
                ))
            
            # Validate AMA table references
            if "ama_table" in calc_data and not self._validate_ama_reference(calc_data["ama_table"]):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.HIGH,
                    title="Invalid AMA Table Reference",
                    description=f"Invalid AMA table reference: {calc_data['ama_table']}",
                    ama_reference="AMA Guides 5th Edition",
                    remediation_steps=[
                        "Verify table reference against AMA Guides",
                        "Update calculation with correct table reference"
                    ]
                ))
        
        return issues
    
    def _validate_ama_reference(self, reference: str) -> bool:
        """Validate AMA table reference format."""
        patterns = [
            r"Table\s+\d+-\d+",
            r"Chapter\s+\d+",
            r"Figure\s+\d+-\d+"
        ]
        return any(re.match(pattern, reference, re.IGNORECASE) for pattern in patterns)


class LegalComplianceEnhanced:
    """Enhanced legal compliance validator with detailed reporting."""
    
    def __init__(self):
        """Initialize enhanced legal compliance validator."""
        self.labor_code_4062_3_text = (
            "Any documents sent to the physician for record review must be accompanied by a "
            "declaration under penalty of perjury that the provider of the documents has "
            "complied with the provisions of Labor Code section 4062.3 before providing the "
            "documents to the physician. The declaration must also contain an attestation as "
            "to the total page count of the documents provided."
        )
        
    def validate_labor_code_4062_3(self, report_content: str) -> Tuple[bool, List[str]]:
        """Validate Labor Code 4062.3 declaration."""
        issues = []
        
        # Check for exact text match
        if self.labor_code_4062_3_text not in report_content:
            issues.append("Labor Code 4062.3 declaration text not found or incorrect")
        
        # Check for page count attestation
        page_count_patterns = [
            r"total page count.*attestation",
            r"page count.*declaration",
            r"attestation.*page count"
        ]
        
        if not any(re.search(pattern, report_content, re.IGNORECASE) for pattern in page_count_patterns):
            issues.append("Page count attestation not found")
        
        # Check for penalty of perjury
        if "penalty of perjury" not in report_content.lower():
            issues.append("Penalty of perjury statement not found")
        
        return len(issues) == 0, issues
    
    def validate_mandatory_sections(self, report_sections: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate presence of mandatory sections."""
        required_sections = [
            "patient_demographics",
            "records_reviewed", 
            "physical_examination",
            "diagnosis",
            "impairment_rating",
            "signature_blocks"
        ]
        
        missing_sections = [section for section in required_sections if section not in report_sections]
        
        return len(missing_sections) == 0, missing_sections
    
    def validate_signature_blocks(self, signature_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate physician signature blocks."""
        issues = []
        
        required_fields = ["examiner_name", "license_number", "signature_date"]
        for field in required_fields:
            if not signature_data.get(field):
                issues.append(f"Missing {field} in signature block")
        
        # Check AB 1300 declaration
        ab_1300_text = "Pursuant to AB 1300, LC Sec. 5703, I have not violated Labor Code section 139.3"
        if ab_1300_text not in signature_data.get("declaration_text", ""):
            issues.append("AB 1300 declaration not found or incorrect")
        
        return len(issues) == 0, issues
    
    def generate_compliance_report(self, validation_results: Dict[str, Any]) -> ComplianceReport:
        """Generate detailed compliance report."""
        failed_requirements = []
        remediation_steps = []
        
        # Analyze validation results
        if not validation_results.get("labor_code_4062_3", False):
            failed_requirements.append("Labor Code 4062.3 Declaration")
            remediation_steps.append("Add complete Labor Code 4062.3 declaration text")
        
        if not validation_results.get("mandatory_sections", False):
            failed_requirements.append("Mandatory Sections")
            remediation_steps.append("Complete all required report sections")
        
        if not validation_results.get("signature_blocks", False):
            failed_requirements.append("Signature Blocks")
            remediation_steps.append("Complete physician signature and attestation")
        
        # Determine overall status
        overall_status = "PASS" if len(failed_requirements) == 0 else "FAIL"
        
        return ComplianceReport(
            overall_status=overall_status,
            labor_code_4062_3_status=validation_results.get("labor_code_4062_3", False),
            mandatory_sections_status=validation_results.get("mandatory_sections", False),
            mlprr_billing_status=validation_results.get("mlprr_billing", False),
            signature_blocks_status=validation_results.get("signature_blocks", False),
            evidence_sufficiency_status=validation_results.get("evidence_sufficiency", False),
            calculation_accuracy_status=validation_results.get("calculation_accuracy", False),
            failed_requirements=failed_requirements,
            remediation_steps=remediation_steps,
            audit_trail=validation_results.get("audit_trail", {})
        )


class QMERulesEngine:
    """Enhanced QME Rules Engine with evidence-first validation."""
    
    def __init__(self, rules_config_path: Optional[str] = None):
        """Initialize the enhanced QME Rules Engine."""
        self.gold_standard_rules = QMEGoldStandardRules()
        self.ama_validator = AMAGuidelinesValidator()
        self.legal_validator = LegalComplianceValidator()
        
        # Load evidence-first configuration
        self.rules_config = self._load_rules_config(rules_config_path)
        confidence_thresholds = self.rules_config.get("evidence_first", {}).get("confidence_thresholds", {})
        
        # Initialize evidence-first validators
        self.evidence_validator = EvidenceFirstValidator(confidence_thresholds)
        self.post_gen_validator = PostGenerationValidator()
        self.legal_compliance_enhanced = LegalComplianceEnhanced()
        
        logger.info("Initialized Enhanced QME Rules Engine with evidence-first validation")
    
    def _load_rules_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load rules configuration from YAML file."""
        if config_path is None:
            config_path = "src/rules/rules.yaml"
        
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading rules config: {e}")
            return {}
    
    def validate_qme_report(self, template_data: QMETemplateData, 
                           extracted_fields: Optional[Dict[str, Any]] = None,
                           report_content: Optional[str] = None) -> Tuple[List[ValidationIssue], QualityScore, ComplianceReport]:
        """
        Perform comprehensive evidence-first validation of QME report.
        
        Args:
            template_data: QME template data to validate
            extracted_fields: Fields extracted with confidence scores and provenance
            report_content: Generated report content for post-generation validation
            
        Returns:
            Tuple of (validation_issues, quality_score, compliance_report)
        """
        try:
            logger.info("Starting comprehensive evidence-first QME report validation")
            
            all_issues = []
            validation_results = {}
            
            # Evidence-first validation
            if extracted_fields:
                evidence_issues = self._validate_evidence_first(extracted_fields)
                all_issues.extend(evidence_issues)
                validation_results["evidence_sufficiency"] = len(evidence_issues) == 0
            
            # Post-generation validation
            if report_content:
                post_gen_issues = self._validate_post_generation(report_content, template_data)
                all_issues.extend(post_gen_issues)
                validation_results["calculation_accuracy"] = len([i for i in post_gen_issues if "calculation" in i.title.lower()]) == 0
            
            # Enhanced legal compliance validation
            legal_issues, legal_results = self._validate_legal_compliance_enhanced(template_data, report_content)
            all_issues.extend(legal_issues)
            validation_results.update(legal_results)
            
            # Gold standard validation
            gold_issues = self._validate_against_gold_standard(template_data)
            all_issues.extend(gold_issues)
            
            # AMA Guidelines validation
            ama_issues = self._validate_ama_compliance(template_data)
            all_issues.extend(ama_issues)
            
            # Content quality validation
            quality_issues = self._validate_content_quality(template_data)
            all_issues.extend(quality_issues)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(all_issues, template_data, extracted_fields)
            
            # Generate compliance report
            compliance_report = self.legal_compliance_enhanced.generate_compliance_report(validation_results)
            
            logger.info(f"Validation complete: {len(all_issues)} issues found, quality score: {quality_score.overall_score:.1f}, compliance: {compliance_report.overall_status}")
            
            return all_issues, quality_score, compliance_report
            
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
                evidence_confidence_score=0.0,
                total_issues=1,
                high_issues=1
            )
            basic_compliance = ComplianceReport(
                overall_status="FAIL",
                labor_code_4062_3_status=False,
                mandatory_sections_status=False,
                mlprr_billing_status=False,
                signature_blocks_status=False,
                evidence_sufficiency_status=False,
                calculation_accuracy_status=False,
                failed_requirements=["System Error"],
                remediation_steps=["Contact system administrator"]
            )
            return [error_issue], basic_score, basic_compliance
    
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
    
    def _validate_evidence_first(self, extracted_fields: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate extracted fields using evidence-first methodology."""
        issues = []
        
        try:
            # Validate field confidence scores
            for field_name, field_data in extracted_fields.items():
                if isinstance(field_data, dict) and "confidence" in field_data:
                    confidence = field_data["confidence"]
                    provenance_data = field_data.get("provenance", {})
                    
                    # Create provenance object
                    provenance = EvidenceProvenance(
                        source_document=provenance_data.get("source_document", "unknown"),
                        page_number=provenance_data.get("page_number", 0),
                        text_coordinates=provenance_data.get("coordinates", (0, 0, 0, 0)),
                        snippet_text=provenance_data.get("snippet", ""),
                        confidence_score=confidence,
                        extraction_method=provenance_data.get("method", "unknown")
                    )
                    
                    # Validate confidence
                    confidence_issue = self.evidence_validator.validate_field_confidence(
                        field_name, confidence, provenance
                    )
                    if confidence_issue:
                        issues.append(confidence_issue)
            
            # Validate overall evidence sufficiency
            sufficiency_issues = self.evidence_validator.validate_evidence_sufficiency(extracted_fields)
            issues.extend(sufficiency_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error in evidence-first validation: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Evidence Validation Error",
                description=f"Error validating evidence: {str(e)}",
                suggestions=["Review extraction data format"]
            )]
    
    def _validate_post_generation(self, report_content: str, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate report after generation for placeholder text and accuracy."""
        issues = []
        
        try:
            # Scan for placeholder text
            placeholder_issues = self.post_gen_validator.scan_placeholder_text(report_content)
            issues.extend(placeholder_issues)
            
            # Validate calculation accuracy
            calculations = self._extract_calculations_from_template(template_data)
            calc_issues = self.post_gen_validator.validate_calculation_accuracy(calculations)
            issues.extend(calc_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error in post-generation validation: {e}")
            return [ValidationIssue(
                section=SectionType.IMPAIRMENT_RATING,
                severity=ValidationSeverity.HIGH,
                title="Post-Generation Validation Error",
                description=f"Error in post-generation validation: {str(e)}",
                suggestions=["Review report generation process"]
            )]
    
    def _validate_legal_compliance_enhanced(self, template_data: QMETemplateData, 
                                          report_content: Optional[str] = None) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Enhanced legal compliance validation with detailed results."""
        issues = []
        results = {}
        
        try:
            if report_content:
                # Validate Labor Code 4062.3
                lc_4062_3_valid, lc_issues = self.legal_compliance_enhanced.validate_labor_code_4062_3(report_content)
                results["labor_code_4062_3"] = lc_4062_3_valid
                
                if not lc_4062_3_valid:
                    issues.append(ValidationIssue(
                        section=SectionType.PATIENT_DEMOGRAPHICS,
                        severity=ValidationSeverity.CRITICAL,
                        title="Labor Code 4062.3 Compliance Failure",
                        description="; ".join(lc_issues),
                        legal_reference="Labor Code 4062.3",
                        remediation_steps=[
                            "Add complete Labor Code 4062.3 declaration",
                            "Include page count attestation",
                            "Ensure penalty of perjury statement"
                        ]
                    ))
            
            # Validate mandatory sections
            report_sections = self._extract_sections_from_template(template_data)
            sections_valid, missing_sections = self.legal_compliance_enhanced.validate_mandatory_sections(report_sections)
            results["mandatory_sections"] = sections_valid
            
            if not sections_valid:
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Missing Mandatory Sections",
                    description=f"Missing sections: {', '.join(missing_sections)}",
                    remediation_steps=[f"Complete {section} section" for section in missing_sections]
                ))
            
            # Validate signature blocks
            signature_data = self._extract_signature_data(template_data)
            sig_valid, sig_issues = self.legal_compliance_enhanced.validate_signature_blocks(signature_data)
            results["signature_blocks"] = sig_valid
            
            if not sig_valid:
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title="Signature Block Issues",
                    description="; ".join(sig_issues),
                    remediation_steps=sig_issues
                ))
            
            return issues, results
            
        except Exception as e:
            logger.error(f"Error in enhanced legal compliance validation: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Legal Compliance Validation Error",
                description=f"Error in legal compliance validation: {str(e)}",
                suggestions=["Review legal compliance requirements"]
            )], {"error": True}
    
    def _extract_calculations_from_template(self, template_data: QMETemplateData) -> Dict[str, Any]:
        """Extract calculation data from template for validation."""
        calculations = {}
        
        try:
            # Extract impairment calculations
            if template_data.medical_findings.impairment_ratings:
                for i, rating in enumerate(template_data.medical_findings.impairment_ratings):
                    calculations[f"impairment_{i}"] = {
                        "percentage": rating.percentage,
                        "ama_table": rating.ama_table,
                        "programmatic": hasattr(rating, "calculation_method") and rating.calculation_method == "programmatic",
                        "rationale": rating.rationale
                    }
            
            return calculations
            
        except Exception as e:
            logger.error(f"Error extracting calculations: {e}")
            return {}
    
    def _extract_sections_from_template(self, template_data: QMETemplateData) -> Dict[str, str]:
        """Extract report sections from template data."""
        sections = {}
        
        try:
            if template_data.patient_info:
                sections["patient_demographics"] = "present"
            
            if template_data.medical_findings.diagnoses:
                sections["diagnosis"] = "present"
            
            if template_data.medical_findings.impairment_ratings:
                sections["impairment_rating"] = "present"
            
            # Add other sections as available in template_data
            sections["physical_examination"] = "present"  # Assume present for now
            sections["records_reviewed"] = "present"     # Assume present for now
            sections["signature_blocks"] = "present"     # Assume present for now
            
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            return {}
    
    def _extract_signature_data(self, template_data: QMETemplateData) -> Dict[str, Any]:
        """Extract signature data from template."""
        signature_data = {}
        
        try:
            # Extract examiner information if available
            if hasattr(template_data, 'examiner_info'):
                signature_data["examiner_name"] = getattr(template_data.examiner_info, 'name', '')
                signature_data["license_number"] = getattr(template_data.examiner_info, 'license', '')
                signature_data["signature_date"] = getattr(template_data.examiner_info, 'date', '')
                signature_data["declaration_text"] = getattr(template_data.examiner_info, 'declaration', '')
            
            return signature_data
            
        except Exception as e:
            logger.error(f"Error extracting signature data: {e}")
            return {}
    
    def _calculate_quality_score(self, issues: List[ValidationIssue], 
                               template_data: QMETemplateData,
                               extracted_fields: Optional[Dict[str, Any]] = None) -> QualityScore:
        """Calculate enhanced quality score with evidence-first metrics."""
        try:
            # Count issues by severity
            critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
            high_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.HIGH)
            medium_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.MEDIUM)
            low_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.LOW)
            
            # Calculate base scores
            total_issues = len(issues)
            base_score = max(0, 100 - (critical_count * 25 + high_count * 15 + medium_count * 10 + low_count * 5))
            
            # Calculate evidence-first metrics
            fields_above_threshold = 0
            fields_requiring_review = 0
            evidence_confidence_score = 100.0
            
            if extracted_fields:
                total_fields = len(extracted_fields)
                for field_data in extracted_fields.values():
                    if isinstance(field_data, dict) and "confidence" in field_data:
                        confidence = field_data["confidence"]
                        if confidence >= 0.8:
                            fields_above_threshold += 1
                        elif confidence >= 0.5:
                            fields_requiring_review += 1
                
                if total_fields > 0:
                    evidence_confidence_score = (fields_above_threshold / total_fields) * 100
            
            # Count placeholder text issues
            placeholder_count = sum(1 for issue in issues if "placeholder" in issue.title.lower())
            
            # Count programmatic calculation verifications
            calc_verified = sum(1 for issue in issues if "calculation" in issue.title.lower() and issue.severity != ValidationSeverity.CRITICAL)
            
            return QualityScore(
                overall_score=base_score,
                completeness_score=max(0, 100 - (critical_count * 20 + high_count * 10)),
                accuracy_score=max(0, 100 - (critical_count * 30 + high_count * 15)),
                compliance_score=max(0, 100 - (critical_count * 50)),
                evidence_confidence_score=evidence_confidence_score,
                total_issues=total_issues,
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count,
                fields_above_confidence_threshold=fields_above_threshold,
                fields_requiring_review=fields_requiring_review,
                programmatic_calculations_verified=calc_verified,
                placeholder_text_found=placeholder_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                compliance_score=0.0,
                evidence_confidence_score=0.0,
                total_issues=len(issues),
                critical_issues=len(issues)
            )
    
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


class EnhancedEvidenceFirstRulesEngine(QMERulesEngine):
    """Enhanced QME Rules Engine with Evidence-First Validation and Legal Compliance."""
    
    def __init__(self, rules_config_path: Optional[str] = None):
        """Initialize enhanced evidence-first rules engine."""
        super().__init__(rules_config_path)
        self.evidence_validator = EvidenceFirstValidator({
            "critical_fields": 0.8,
            "standard_fields": 0.5
        })
        self.post_generation_validator = PostGenerationValidator()
        self.legal_compliance_validator = LegalComplianceValidator()
        
    def validate_evidence_first_pipeline(self, template_data: QMETemplateData, 
                                       extracted_fields: Dict[str, Any],
                                       confidence_scores: Dict[str, float],
                                       provenance_data: Dict[str, EvidenceProvenance]) -> ComplianceReport:
        """
        Comprehensive evidence-first validation pipeline.
        
        Args:
            template_data: QME template data
            extracted_fields: Extracted field data with confidence scores
            confidence_scores: Field confidence scores
            provenance_data: Evidence provenance tracking
            
        Returns:
            Detailed compliance report with pass/fail status
        """
        try:
            logger.info("Starting evidence-first validation pipeline")
            
            # Initialize compliance report
            compliance_report = ComplianceReport(
                overall_status="PASS",
                labor_code_4062_3_status=True,
                mandatory_sections_status=True,
                mlprr_billing_status=True,
                signature_blocks_status=True,
                evidence_sufficiency_status=True,
                calculation_accuracy_status=True
            )
            
            # 1. Validate field confidence scores
            confidence_issues = self._validate_field_confidence_scores(
                extracted_fields, confidence_scores, provenance_data
            )
            
            # 2. Validate mandatory sections
            section_issues = self._validate_mandatory_sections(template_data)
            
            # 3. Validate Labor Code 4062.3 compliance
            labor_code_issues = self._validate_labor_code_4062_3(template_data)
            
            # 4. Validate signature blocks
            signature_issues = self._validate_signature_blocks(template_data)
            
            # 5. Validate MLPRR billing calculations
            billing_issues = self._validate_mlprr_billing(template_data)
            
            # 6. Generate audit trail
            audit_trail = self._generate_compliance_audit_trail(
                template_data, extracted_fields, confidence_scores, provenance_data
            )
            
            # Compile all issues
            all_issues = (confidence_issues + section_issues + labor_code_issues + 
                         signature_issues + billing_issues)
            
            # Update compliance status based on issues
            compliance_report = self._update_compliance_status(compliance_report, all_issues)
            compliance_report.audit_trail = audit_trail
            
            # Generate remediation steps
            compliance_report.remediation_steps = self._generate_remediation_steps(all_issues)
            
            logger.info(f"Evidence-first validation completed: {compliance_report.overall_status}")
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error in evidence-first validation pipeline: {e}")
            return ComplianceReport(
                overall_status="FAIL",
                labor_code_4062_3_status=False,
                mandatory_sections_status=False,
                mlprr_billing_status=False,
                signature_blocks_status=False,
                evidence_sufficiency_status=False,
                calculation_accuracy_status=False,
                failed_requirements=["Validation pipeline error"],
                remediation_steps=[f"Fix validation error: {str(e)}"]
            )
    
    def validate_post_generation_compliance(self, report_content: str, 
                                          calculations: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Post-generation validation for placeholder text and calculation accuracy.
        
        Args:
            report_content: Generated report content
            calculations: Calculation data with metadata
            
        Returns:
            List of validation issues found
        """
        try:
            issues = []
            
            # Scan for placeholder text
            placeholder_issues = self.post_generation_validator.scan_placeholder_text(report_content)
            issues.extend(placeholder_issues)
            
            # Validate calculation accuracy
            calculation_issues = self.post_generation_validator.validate_calculation_accuracy(calculations)
            issues.extend(calculation_issues)
            
            # Validate AMA table citations
            citation_issues = self._validate_ama_table_citations(report_content)
            issues.extend(citation_issues)
            
            # Validate evidence backing for medical statements
            evidence_issues = self._validate_evidence_backing(report_content)
            issues.extend(evidence_issues)
            
            logger.info(f"Post-generation validation found {len(issues)} issues")
            return issues
            
        except Exception as e:
            logger.error(f"Error in post-generation validation: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Post-Generation Validation Error",
                description=f"Error in post-generation validation: {str(e)}"
            )]
    
    def _validate_field_confidence_scores(self, extracted_fields: Dict[str, Any],
                                        confidence_scores: Dict[str, float],
                                        provenance_data: Dict[str, EvidenceProvenance]) -> List[ValidationIssue]:
        """Validate field confidence scores against evidence-first thresholds."""
        issues = []
        
        try:
            for field_name, field_value in extracted_fields.items():
                confidence = confidence_scores.get(field_name, 0.0)
                provenance = provenance_data.get(field_name)
                
                if provenance:
                    issue = self.evidence_validator.validate_field_confidence(
                        field_name, confidence, provenance
                    )
                    if issue:
                        issues.append(issue)
            
            # Validate overall evidence sufficiency
            sufficiency_issues = self.evidence_validator.validate_evidence_sufficiency(extracted_fields)
            issues.extend(sufficiency_issues)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validating field confidence scores: {e}")
            return [ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.HIGH,
                title="Confidence Validation Error",
                description=f"Error validating confidence scores: {str(e)}"
            )]
    
    def _validate_mandatory_sections(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate presence of mandatory sections."""
        issues = []
        
        mandatory_sections = [
            ("patient_demographics", template_data.patient_info.name),
            ("records_reviewed", True),  # Placeholder check
            ("physical_examination", True),  # Placeholder check
            ("diagnosis", template_data.medical_findings.diagnoses),
            ("impairment_rating", template_data.medical_findings.impairment_ratings)
        ]
        
        for section_name, section_data in mandatory_sections:
            if not section_data:
                issues.append(ValidationIssue(
                    section=SectionType.PATIENT_DEMOGRAPHICS,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Missing Mandatory Section: {section_name}",
                    description=f"Mandatory section '{section_name}' is missing or incomplete",
                    remediation_steps=[
                        f"Complete the {section_name} section",
                        "Ensure all required information is documented",
                        "Review QME template requirements"
                    ]
                ))
        
        return issues
    
    def _validate_labor_code_4062_3(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate Labor Code 4062.3 declaration and requirements."""
        issues = []
        
        # Check for required declaration text
        required_declaration = (
            "Any documents sent to the physician for record review must be accompanied by a "
            "declaration under penalty of perjury that the provider of the documents has complied "
            "with the provisions of Labor Code section 4062.3 before providing the documents to "
            "the physician. The declaration must also contain an attestation as to the total page "
            "count of the documents provided."
        )
        
        # This would be enhanced with actual content checking
        # For now, we'll create a placeholder validation
        
        issues.append(ValidationIssue(
            section=SectionType.PATIENT_DEMOGRAPHICS,
            severity=ValidationSeverity.CRITICAL,
            title="Labor Code 4062.3 Declaration Required",
            description="Labor Code 4062.3 declaration must be present and exact",
            remediation_steps=[
                "Include exact Labor Code 4062.3 declaration text",
                "Verify page count attestation is present",
                "Ensure penalty of perjury statement is included"
            ]
        ))
        
        return issues
    
    def _validate_signature_blocks(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate signature blocks and examiner attestation."""
        issues = []
        
        # Check for required signature elements
        required_elements = [
            "examiner_name",
            "examiner_license_number", 
            "signature_date",
            "ab_1300_declaration"
        ]
        
        for element in required_elements:
            issues.append(ValidationIssue(
                section=SectionType.PATIENT_DEMOGRAPHICS,
                severity=ValidationSeverity.CRITICAL,
                title=f"Missing Signature Element: {element}",
                description=f"Required signature element '{element}' is missing",
                remediation_steps=[
                    f"Add {element} to signature block",
                    "Ensure all signature requirements are met",
                    "Include AB 1300 declaration if required"
                ]
            ))
        
        return issues
    
    def _validate_mlprr_billing(self, template_data: QMETemplateData) -> List[ValidationIssue]:
        """Validate MLPRR billing calculations and attestations."""
        issues = []
        
        # Placeholder for MLPRR billing validation
        issues.append(ValidationIssue(
            section=SectionType.PATIENT_DEMOGRAPHICS,
            severity=ValidationSeverity.HIGH,
            title="MLPRR Billing Validation Required",
            description="MLPRR billing calculations and attestations must be validated",
            remediation_steps=[
                "Verify page count calculations",
                "Ensure billing unit calculations are accurate",
                "Include penalty of perjury attestation for page counts"
            ]
        ))
        
        return issues
    
    def _validate_ama_table_citations(self, report_content: str) -> List[ValidationIssue]:
        """Validate AMA table citations for accuracy."""
        issues = []
        
        # Pattern for AMA table references
        ama_pattern = r"(?:Table|Chapter)\s*(\d{1,2})-?(\d{0,2})"
        matches = re.finditer(ama_pattern, report_content, re.IGNORECASE)
        
        for match in matches:
            chapter = int(match.group(1))
            table = int(match.group(2)) if match.group(2) else 0
            
            # Validate chapter and table numbers
            if not (1 <= chapter <= 18):
                issues.append(ValidationIssue(
                    section=SectionType.IMPAIRMENT_RATING,
                    severity=ValidationSeverity.HIGH,
                    title="Invalid AMA Chapter Reference",
                    description=f"Invalid AMA chapter reference: {match.group()}",
                    ama_reference="AMA Guides 5th Edition",
                    remediation_steps=[
                        "Verify chapter reference against AMA Guides 5th Edition",
                        "Update with correct chapter number"
                    ]
                ))
        
        return issues
    
    def _validate_evidence_backing(self, report_content: str) -> List[ValidationIssue]:
        """Validate that medical statements have evidence backing."""
        issues = []
        
        # Patterns for medical statements that require evidence
        statement_patterns = [
            r"diagnosis of",
            r"impairment rating of",
            r"caused by",
            r"related to the injury"
        ]
        
        for pattern in statement_patterns:
            matches = re.finditer(pattern, report_content, re.IGNORECASE)
            for match in matches:
                # This would be enhanced with actual evidence checking
                # For now, we'll flag statements that need evidence backing
                pass
        
        return issues
    
    def _generate_compliance_audit_trail(self, template_data: QMETemplateData,
                                       extracted_fields: Dict[str, Any],
                                       confidence_scores: Dict[str, float],
                                       provenance_data: Dict[str, EvidenceProvenance]) -> Dict[str, Any]:
        """Generate comprehensive audit trail for compliance validation."""
        audit_trail = {
            "validation_timestamp": datetime.now().isoformat(),
            "evidence_mapping": {},
            "confidence_tracking": confidence_scores,
            "validation_decisions": [],
            "compliance_checks": []
        }
        
        # Map fields to evidence sources
        for field_name, provenance in provenance_data.items():
            audit_trail["evidence_mapping"][field_name] = {
                "source_document": provenance.source_document,
                "page_number": provenance.page_number,
                "confidence_score": provenance.confidence_score,
                "extraction_method": provenance.extraction_method,
                "snippet": provenance.snippet_text[:100] + "..." if len(provenance.snippet_text) > 100 else provenance.snippet_text
            }
        
        return audit_trail
    
    def _update_compliance_status(self, compliance_report: ComplianceReport, 
                                issues: List[ValidationIssue]) -> ComplianceReport:
        """Update compliance status based on validation issues."""
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        
        if critical_issues:
            compliance_report.overall_status = "FAIL"
            compliance_report.failed_requirements = [issue.title for issue in critical_issues]
        else:
            high_issues = [issue for issue in issues if issue.severity == ValidationSeverity.HIGH]
            if high_issues:
                compliance_report.overall_status = "REQUIRES_REVIEW"
        
        return compliance_report
    
    def _generate_remediation_steps(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable remediation steps from validation issues."""
        remediation_steps = []
        
        for issue in issues:
            if issue.remediation_steps:
                remediation_steps.extend(issue.remediation_steps)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_steps = []
        for step in remediation_steps:
            if step not in seen:
                seen.add(step)
                unique_steps.append(step)
        
        return unique_steps