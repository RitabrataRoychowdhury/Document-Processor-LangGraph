"""
Comprehensive Quality Validation Service for QME System

This service provides quality validation with scoring and compliance checking
for the refactored QME document generation system.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import re
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStandard(Enum):
    """Compliance standards for QME documents"""
    AMA_GUIDELINES = "ama_guidelines"
    QME_REGULATIONS = "qme_regulations"
    PROFESSIONAL_STANDARDS = "professional_standards"
    LEGAL_REQUIREMENTS = "legal_requirements"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during quality assessment"""
    issue_id: str
    severity: ValidationSeverity
    category: str
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    compliance_standard: Optional[ComplianceStandard] = None
    confidence: float = 1.0


@dataclass
class QualityMetrics:
    """Quality metrics for document assessment"""
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    consistency_score: float = 0.0
    compliance_score: float = 0.0
    readability_score: float = 0.0
    professional_formatting_score: float = 0.0
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall quality score"""
        weights = {
            'completeness': 0.25,
            'accuracy': 0.30,
            'consistency': 0.20,
            'compliance': 0.15,
            'readability': 0.05,
            'formatting': 0.05
        }
        
        return (
            self.completeness_score * weights['completeness'] +
            self.accuracy_score * weights['accuracy'] +
            self.consistency_score * weights['consistency'] +
            self.compliance_score * weights['compliance'] +
            self.readability_score * weights['readability'] +
            self.professional_formatting_score * weights['formatting']
        )


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment result"""
    document_id: str
    assessment_timestamp: str
    metrics: QualityMetrics
    issues: List[ValidationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    compliance_status: Dict[ComplianceStandard, bool] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_acceptable_quality(self) -> bool:
        """Determine if document meets minimum quality standards"""
        return (
            self.metrics.overall_score >= 0.75 and
            self.metrics.accuracy_score >= 0.80 and
            self.metrics.compliance_score >= 0.90 and
            not any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)
        )


class QualityValidationService:
    """Comprehensive quality validation service for QME documents"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/validation/quality_validation_config.yaml"
        self.validation_rules = self._load_validation_rules()
        self.compliance_rules = self._load_compliance_rules()
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration"""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Validation config not found at {self.config_path}, using defaults")
                return self._get_default_validation_rules()
        except Exception as e:
            logger.error(f"Error loading validation rules: {e}")
            return self._get_default_validation_rules()
    
    def _load_compliance_rules(self) -> Dict[ComplianceStandard, Dict[str, Any]]:
        """Load compliance rules for different standards"""
        compliance_config_path = "config/prompts/validation/compliance_rules.yaml"
        try:
            with open(compliance_config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {
                    ComplianceStandard.AMA_GUIDELINES: config.get('ama_guidelines', {}),
                    ComplianceStandard.QME_REGULATIONS: config.get('qme_regulations', {}),
                    ComplianceStandard.PROFESSIONAL_STANDARDS: config.get('professional_standards', {}),
                    ComplianceStandard.LEGAL_REQUIREMENTS: config.get('legal_requirements', {})
                }
        except Exception as e:
            logger.error(f"Error loading compliance rules: {e}")
            return {}
    
    def _get_default_validation_rules(self) -> Dict[str, Any]:
        """Get default validation rules if config file is not available"""
        return {
            'required_sections': [
                'patient_information',
                'history_of_present_illness',
                'physical_examination',
                'medical_findings',
                'diagnosis',
                'impairment_rating',
                'recommendations'
            ],
            'minimum_content_length': {
                'history_of_present_illness': 100,
                'physical_examination': 150,
                'medical_findings': 100,
                'diagnosis': 50
            },
            'required_fields': {
                'patient_information': ['name', 'date_of_birth', 'date_of_injury'],
                'impairment_rating': ['percentage', 'body_part', 'ama_table_reference']
            },
            'formatting_requirements': {
                'professional_header': True,
                'consistent_formatting': True,
                'proper_citations': True,
                'clear_section_breaks': True
            }
        }
    
    def validate_document_quality(self, 
                                document_content: str, 
                                extracted_data: Dict[str, Any],
                                document_id: str) -> QualityAssessment:
        """Perform comprehensive quality validation on a QME document"""
        
        logger.info(f"Starting quality validation for document {document_id}")
        
        # Initialize assessment
        assessment = QualityAssessment(
            document_id=document_id,
            assessment_timestamp=self._get_timestamp(),
            metrics=QualityMetrics()
        )
        
        # Perform validation checks
        self._validate_completeness(document_content, extracted_data, assessment)
        self._validate_accuracy(document_content, extracted_data, assessment)
        self._validate_consistency(document_content, extracted_data, assessment)
        self._validate_compliance(document_content, extracted_data, assessment)
        self._validate_readability(document_content, assessment)
        self._validate_professional_formatting(document_content, assessment)
        
        # Generate recommendations
        self._generate_recommendations(assessment)
        
        logger.info(f"Quality validation completed for {document_id}. Overall score: {assessment.metrics.overall_score:.2f}")
        
        return assessment
    
    def _validate_completeness(self, content: str, data: Dict[str, Any], assessment: QualityAssessment):
        """Validate document completeness"""
        required_sections = self.validation_rules.get('required_sections', [])
        missing_sections = []
        
        for section in required_sections:
            if not self._section_exists(content, section):
                missing_sections.append(section)
                assessment.issues.append(ValidationIssue(
                    issue_id=f"missing_section_{section}",
                    severity=ValidationSeverity.HIGH,
                    category="completeness",
                    description=f"Required section '{section}' is missing",
                    suggestion=f"Add the '{section}' section to the document"
                ))
        
        # Check required fields
        required_fields = self.validation_rules.get('required_fields', {})
        for section, fields in required_fields.items():
            section_data = data.get(section, {})
            for field in fields:
                if not section_data.get(field):
                    assessment.issues.append(ValidationIssue(
                        issue_id=f"missing_field_{section}_{field}",
                        severity=ValidationSeverity.MEDIUM,
                        category="completeness",
                        description=f"Required field '{field}' missing in section '{section}'",
                        suggestion=f"Ensure '{field}' is properly extracted and included"
                    ))
        
        # Calculate completeness score
        total_required = len(required_sections) + sum(len(fields) for fields in required_fields.values())
        missing_count = len(missing_sections) + len([i for i in assessment.issues if i.category == "completeness"])
        
        if total_required > 0:
            assessment.metrics.completeness_score = max(0.0, 1.0 - (missing_count / total_required))
        else:
            # If no requirements defined, assume complete
            assessment.metrics.completeness_score = 1.0
    
    def _validate_accuracy(self, content: str, data: Dict[str, Any], assessment: QualityAssessment):
        """Validate document accuracy"""
        accuracy_score = 1.0
        
        # Check for inconsistent dates
        dates = self._extract_dates(content)
        if self._has_inconsistent_dates(dates):
            assessment.issues.append(ValidationIssue(
                issue_id="inconsistent_dates",
                severity=ValidationSeverity.HIGH,
                category="accuracy",
                description="Inconsistent dates found in document",
                suggestion="Review and correct date inconsistencies"
            ))
            accuracy_score -= 0.2
        
        # Check for medical terminology accuracy
        medical_terms = self._extract_medical_terms(content)
        incorrect_terms = self._validate_medical_terminology(medical_terms)
        for term in incorrect_terms:
            assessment.issues.append(ValidationIssue(
                issue_id=f"incorrect_medical_term_{term}",
                severity=ValidationSeverity.MEDIUM,
                category="accuracy",
                description=f"Potentially incorrect medical terminology: '{term}'",
                suggestion=f"Verify the accuracy of medical term '{term}'"
            ))
            accuracy_score -= 0.1
        
        # Check impairment rating calculations
        if 'impairment_rating' in data:
            if not self._validate_impairment_calculations(data['impairment_rating']):
                assessment.issues.append(ValidationIssue(
                    issue_id="impairment_calculation_error",
                    severity=ValidationSeverity.CRITICAL,
                    category="accuracy",
                    description="Impairment rating calculation appears incorrect",
                    suggestion="Review impairment rating calculations against AMA Guidelines"
                ))
                accuracy_score -= 0.3
        
        assessment.metrics.accuracy_score = max(0.0, accuracy_score)
    
    def _validate_consistency(self, content: str, data: Dict[str, Any], assessment: QualityAssessment):
        """Validate document consistency"""
        consistency_score = 1.0
        
        # Check for consistent patient information
        patient_refs = self._extract_patient_references(content)
        if not self._patient_references_consistent(patient_refs):
            assessment.issues.append(ValidationIssue(
                issue_id="inconsistent_patient_info",
                severity=ValidationSeverity.MEDIUM,
                category="consistency",
                description="Inconsistent patient information references",
                suggestion="Ensure patient name and details are consistent throughout"
            ))
            consistency_score -= 0.2
        
        # Check formatting consistency
        if not self._has_consistent_formatting(content):
            assessment.issues.append(ValidationIssue(
                issue_id="inconsistent_formatting",
                severity=ValidationSeverity.LOW,
                category="consistency",
                description="Inconsistent formatting detected",
                suggestion="Apply consistent formatting throughout the document"
            ))
            consistency_score -= 0.1
        
        assessment.metrics.consistency_score = max(0.0, consistency_score)
    
    def _validate_compliance(self, content: str, data: Dict[str, Any], assessment: QualityAssessment):
        """Validate compliance with various standards"""
        compliance_scores = {}
        
        for standard, rules in self.compliance_rules.items():
            score = self._check_compliance_standard(content, data, standard, rules, assessment)
            compliance_scores[standard] = score
            assessment.compliance_status[standard] = score >= 0.8
        
        # Calculate overall compliance score
        if compliance_scores:
            assessment.metrics.compliance_score = sum(compliance_scores.values()) / len(compliance_scores)
        else:
            assessment.metrics.compliance_score = 0.8  # Default if no rules loaded
    
    def _validate_readability(self, content: str, assessment: QualityAssessment):
        """Validate document readability"""
        # Simple readability checks
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        readability_score = 1.0
        
        if avg_sentence_length > 25:
            assessment.issues.append(ValidationIssue(
                issue_id="long_sentences",
                severity=ValidationSeverity.LOW,
                category="readability",
                description="Average sentence length is too long",
                suggestion="Consider breaking down long sentences for better readability"
            ))
            readability_score -= 0.2
        
        # Check for excessive jargon
        jargon_density = self._calculate_jargon_density(content)
        if jargon_density > 0.3:
            assessment.issues.append(ValidationIssue(
                issue_id="excessive_jargon",
                severity=ValidationSeverity.LOW,
                category="readability",
                description="High density of medical jargon may affect readability",
                suggestion="Consider adding explanations for complex medical terms"
            ))
            readability_score -= 0.1
        
        assessment.metrics.readability_score = max(0.0, readability_score)
    
    def _validate_professional_formatting(self, content: str, assessment: QualityAssessment):
        """Validate professional formatting standards"""
        formatting_score = 1.0
        
        # Check for proper headers
        if not self._has_professional_header(content):
            assessment.issues.append(ValidationIssue(
                issue_id="missing_professional_header",
                severity=ValidationSeverity.MEDIUM,
                category="formatting",
                description="Document lacks professional header format",
                suggestion="Add proper professional header with QME identification"
            ))
            formatting_score -= 0.3
        
        # Check for proper section breaks
        if not self._has_clear_section_breaks(content):
            assessment.issues.append(ValidationIssue(
                issue_id="unclear_section_breaks",
                severity=ValidationSeverity.LOW,
                category="formatting",
                description="Section breaks are not clearly defined",
                suggestion="Use consistent section headers and formatting"
            ))
            formatting_score -= 0.2
        
        assessment.metrics.professional_formatting_score = max(0.0, formatting_score)
    
    def _generate_recommendations(self, assessment: QualityAssessment):
        """Generate improvement recommendations based on validation results"""
        recommendations = []
        
        # Priority recommendations based on critical issues
        critical_issues = [i for i in assessment.issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("Address all critical issues immediately before document finalization")
        
        # Quality-based recommendations
        if assessment.metrics.completeness_score < 0.8:
            recommendations.append("Review document completeness - ensure all required sections are present")
        
        if assessment.metrics.accuracy_score < 0.8:
            recommendations.append("Verify accuracy of medical information and calculations")
        
        if assessment.metrics.compliance_score < 0.9:
            recommendations.append("Review compliance with QME regulations and AMA guidelines")
        
        # Overall quality recommendation
        if assessment.metrics.overall_score < 0.75:
            recommendations.append("Document requires significant improvement before professional use")
        elif assessment.metrics.overall_score < 0.85:
            recommendations.append("Document quality is acceptable but could benefit from minor improvements")
        else:
            recommendations.append("Document meets high quality standards")
        
        assessment.recommendations = recommendations
    
    # Helper methods
    def _section_exists(self, content: str, section: str) -> bool:
        """Check if a section exists in the document"""
        section_patterns = {
            'patient_information': r'patient\s+information|patient\s+data',
            'history_of_present_illness': r'history\s+of\s+present\s+illness|present\s+illness',
            'physical_examination': r'physical\s+examination|examination\s+findings',
            'medical_findings': r'medical\s+findings|clinical\s+findings',
            'diagnosis': r'diagnosis|diagnostic\s+impression',
            'impairment_rating': r'impairment\s+rating|disability\s+rating',
            'recommendations': r'recommendations|treatment\s+recommendations'
        }
        
        pattern = section_patterns.get(section, section.replace('_', r'\s+'))
        return bool(re.search(pattern, content, re.IGNORECASE))
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from document content"""
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        return re.findall(date_pattern, content)
    
    def _has_inconsistent_dates(self, dates: List[str]) -> bool:
        """Check for date inconsistencies"""
        # Simple check - in a real implementation, this would be more sophisticated
        return len(set(dates)) > 10  # Too many different dates might indicate inconsistency
    
    def _extract_medical_terms(self, content: str) -> List[str]:
        """Extract medical terminology from content"""
        # This is a simplified implementation
        medical_pattern = r'\b[A-Z][a-z]*(?:itis|osis|pathy|algia|emia|uria)\b'
        return re.findall(medical_pattern, content)
    
    def _validate_medical_terminology(self, terms: List[str]) -> List[str]:
        """Validate medical terminology accuracy"""
        # Placeholder - would integrate with medical dictionary
        return []
    
    def _validate_impairment_calculations(self, impairment_data: Dict[str, Any]) -> bool:
        """Validate impairment rating calculations"""
        # Placeholder for actual calculation validation
        return True
    
    def _extract_patient_references(self, content: str) -> List[str]:
        """Extract patient name references"""
        # Simple pattern for patient names
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        return re.findall(name_pattern, content)
    
    def _patient_references_consistent(self, refs: List[str]) -> bool:
        """Check if patient references are consistent"""
        return len(set(refs)) <= 2  # Allow for some variation
    
    def _has_consistent_formatting(self, content: str) -> bool:
        """Check for consistent formatting"""
        # Simple check for consistent section headers
        header_pattern = r'^[A-Z\s]+:?\s*$'
        headers = re.findall(header_pattern, content, re.MULTILINE)
        return len(headers) >= 3  # Assume consistent if multiple headers found
    
    def _check_compliance_standard(self, content: str, data: Dict[str, Any], 
                                 standard: ComplianceStandard, rules: Dict[str, Any],
                                 assessment: QualityAssessment) -> float:
        """Check compliance with a specific standard"""
        # Placeholder implementation
        return 0.9
    
    def _calculate_jargon_density(self, content: str) -> float:
        """Calculate density of medical jargon"""
        words = content.split()
        medical_terms = self._extract_medical_terms(content)
        return len(medical_terms) / len(words) if words else 0
    
    def _has_professional_header(self, content: str) -> bool:
        """Check for professional header format"""
        header_indicators = ['QME', 'Qualified Medical Evaluator', 'Medical Evaluation']
        return any(indicator in content[:500] for indicator in header_indicators)
    
    def _has_clear_section_breaks(self, content: str) -> bool:
        """Check for clear section breaks"""
        section_breaks = content.count('\n\n')
        return section_breaks >= 5  # Assume good structure if multiple breaks
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def export_assessment_report(self, assessment: QualityAssessment, output_path: str):
        """Export quality assessment to a detailed report"""
        report = {
            'document_id': assessment.document_id,
            'assessment_timestamp': assessment.assessment_timestamp,
            'overall_score': assessment.metrics.overall_score,
            'quality_metrics': {
                'completeness_score': assessment.metrics.completeness_score,
                'accuracy_score': assessment.metrics.accuracy_score,
                'consistency_score': assessment.metrics.consistency_score,
                'compliance_score': assessment.metrics.compliance_score,
                'readability_score': assessment.metrics.readability_score,
                'professional_formatting_score': assessment.metrics.professional_formatting_score
            },
            'is_acceptable_quality': assessment.is_acceptable_quality,
            'issues': [
                {
                    'id': issue.issue_id,
                    'severity': issue.severity.value,
                    'category': issue.category,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'location': issue.location
                }
                for issue in assessment.issues
            ],
            'recommendations': assessment.recommendations,
            'compliance_status': {
                standard.value: status 
                for standard, status in assessment.compliance_status.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Quality assessment report exported to {output_path}")