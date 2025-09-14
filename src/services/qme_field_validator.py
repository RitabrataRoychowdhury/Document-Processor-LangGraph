"""
QME Field Validator - Validation system for QME template fields.

This module ensures all required QME template fields are populated with 
extracted data before template generation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from .qme_field_extractor import QMEFieldData, ExtractionResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationRule:
    """Represents a validation rule for QME fields."""
    field_name: str
    rule_type: str  # 'required', 'format', 'range', 'custom'
    description: str
    validation_function: Optional[callable] = None
    error_message: str = ""
    severity: str = "error"  # 'error', 'warning', 'info'


@dataclass
class ValidationIssue:
    """Represents a validation issue found during field validation."""
    field_name: str
    issue_type: str
    severity: str
    message: str
    suggested_fix: Optional[str] = None
    confidence_impact: float = 0.0


@dataclass
class FieldValidationResult:
    """Result of comprehensive field validation."""
    is_valid: bool
    validation_score: float
    issues: List[ValidationIssue]
    missing_required_fields: List[str]
    warnings: List[str]
    recommendations: List[str]
    ready_for_template_generation: bool


class QMEFieldValidator:
    """
    Comprehensive validation system for QME template fields.
    
    Validates:
    - Required field presence
    - Field format and content quality
    - Data consistency and relationships
    - Template generation readiness
    """
    
    def __init__(self):
        """Initialize the QME field validator."""
        self.validation_rules = self._initialize_validation_rules()
        
        # Field requirements for template generation
        self.required_fields = [
            'name', 'age', 'gender', 'case_number', 'claim_number',
            'injury_date', 'body_parts', 'occupation', 'employer', 'scheduled_exam_date'
        ]
        
        # Critical fields that must be present
        self.critical_fields = ['name', 'case_number', 'claim_number', 'injury_date']
        
        # Optional but recommended fields
        self.recommended_fields = ['age', 'gender', 'occupation', 'employer']
    
    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize validation rules for QME fields."""
        rules = []
        
        # Name validation
        rules.append(ValidationRule(
            field_name='name',
            rule_type='required',
            description='Patient name must be present',
            validation_function=self._validate_name,
            error_message='Patient name is required for QME template generation',
            severity='error'
        ))
        
        # Age validation
        rules.append(ValidationRule(
            field_name='age',
            rule_type='range',
            description='Age must be reasonable (18-100)',
            validation_function=self._validate_age,
            error_message='Age must be between 18 and 100 years',
            severity='warning'
        ))
        
        # Gender validation
        rules.append(ValidationRule(
            field_name='gender',
            rule_type='format',
            description='Gender must be Male or Female',
            validation_function=self._validate_gender,
            error_message='Gender must be specified as Male or Female',
            severity='warning'
        ))
        
        # Case number validation
        rules.append(ValidationRule(
            field_name='case_number',
            rule_type='format',
            description='Case number must follow standard format',
            validation_function=self._validate_case_number,
            error_message='Case number must be in valid format (e.g., ADJ19802400)',
            severity='error'
        ))
        
        # Claim number validation
        rules.append(ValidationRule(
            field_name='claim_number',
            rule_type='format',
            description='Claim number must follow WC format',
            validation_function=self._validate_claim_number,
            error_message='Claim number must be in WC format (e.g., WC608-H07190)',
            severity='error'
        ))
        
        # Injury date validation
        rules.append(ValidationRule(
            field_name='injury_date',
            rule_type='format',
            description='Injury date must be valid date',
            validation_function=self._validate_injury_date,
            error_message='Injury date must be a valid date',
            severity='error'
        ))
        
        # Body parts validation
        rules.append(ValidationRule(
            field_name='body_parts',
            rule_type='required',
            description='At least one body part must be specified',
            validation_function=self._validate_body_parts,
            error_message='At least one injured body part must be specified',
            severity='error'
        ))
        
        # Occupation validation
        rules.append(ValidationRule(
            field_name='occupation',
            rule_type='format',
            description='Occupation should be descriptive',
            validation_function=self._validate_occupation,
            error_message='Occupation should be a descriptive job title',
            severity='warning'
        ))
        
        # Employer validation
        rules.append(ValidationRule(
            field_name='employer',
            rule_type='format',
            description='Employer name should be present',
            validation_function=self._validate_employer,
            error_message='Employer name should be specified',
            severity='warning'
        ))
        
        # Exam date validation
        rules.append(ValidationRule(
            field_name='scheduled_exam_date',
            rule_type='format',
            description='Scheduled exam date must be valid',
            validation_function=self._validate_exam_date,
            error_message='Scheduled exam date must be a valid future date',
            severity='warning'
        ))
        
        return rules
    
    def validate_qme_fields(self, field_data: QMEFieldData) -> FieldValidationResult:
        """
        Perform comprehensive validation of QME field data.
        
        Args:
            field_data: Extracted QME field data to validate
            
        Returns:
            FieldValidationResult with validation status and issues
        """
        logger.info("Performing comprehensive QME field validation")
        
        issues = []
        warnings = []
        recommendations = []
        missing_required_fields = []
        
        # Run all validation rules
        for rule in self.validation_rules:
            field_value = getattr(field_data, rule.field_name, None)
            
            # Check if required field is missing
            if rule.rule_type == 'required' and (field_value is None or 
                (isinstance(field_value, list) and not field_value)):
                missing_required_fields.append(rule.field_name)
                issues.append(ValidationIssue(
                    field_name=rule.field_name,
                    issue_type='missing_required',
                    severity=rule.severity,
                    message=rule.error_message,
                    suggested_fix=f"Extract {rule.field_name} from document",
                    confidence_impact=0.2
                ))
                continue
            
            # Run validation function if field has value
            if field_value is not None and rule.validation_function:
                is_valid, error_msg, suggestion = rule.validation_function(field_value)
                if not is_valid:
                    issues.append(ValidationIssue(
                        field_name=rule.field_name,
                        issue_type='validation_failed',
                        severity=rule.severity,
                        message=error_msg or rule.error_message,
                        suggested_fix=suggestion,
                        confidence_impact=0.1 if rule.severity == 'warning' else 0.2
                    ))
        
        # Check for critical field coverage
        critical_missing = [f for f in self.critical_fields if f in missing_required_fields]
        if critical_missing:
            issues.append(ValidationIssue(
                field_name='critical_fields',
                issue_type='critical_missing',
                severity='error',
                message=f"Critical fields missing: {', '.join(critical_missing)}",
                suggested_fix="Ensure document contains all critical patient information",
                confidence_impact=0.5
            ))
        
        # Generate recommendations
        recommendations.extend(self._generate_recommendations(field_data, issues))
        
        # Calculate validation score
        validation_score = self._calculate_validation_score(field_data, issues)
        
        # Determine if ready for template generation
        error_issues = [i for i in issues if i.severity == 'error']
        ready_for_template = len(error_issues) == 0 and len(critical_missing) == 0
        
        is_valid = len(missing_required_fields) == 0 and len(error_issues) == 0
        
        return FieldValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            issues=issues,
            missing_required_fields=missing_required_fields,
            warnings=[i.message for i in issues if i.severity == 'warning'],
            recommendations=recommendations,
            ready_for_template_generation=ready_for_template
        )
    
    def _validate_name(self, name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate patient name."""
        if not name or len(name.strip()) < 3:
            return False, "Name is too short", "Ensure full patient name is extracted"
        
        # Check for reasonable name format
        if not re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', name):
            return False, "Name format appears invalid", "Verify name extraction accuracy"
        
        return True, None, None
    
    def _validate_age(self, age: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate patient age."""
        if not isinstance(age, int) or age < 18 or age > 100:
            return False, f"Age {age} is outside reasonable range", "Verify age extraction from document"
        
        return True, None, None
    
    def _validate_gender(self, gender: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate patient gender."""
        if gender not in ['Male', 'Female']:
            return False, f"Gender '{gender}' is not standard format", "Use 'Male' or 'Female'"
        
        return True, None, None
    
    def _validate_case_number(self, case_number: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate case number format."""
        if not re.match(r'^[A-Z]{3}\d+$', case_number):
            return False, f"Case number '{case_number}' format invalid", "Should be format like ADJ19802400"
        
        return True, None, None
    
    def _validate_claim_number(self, claim_number: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate claim number format."""
        if not re.match(r'^WC\d+[A-Z0-9\-]*$', claim_number):
            return False, f"Claim number '{claim_number}' format invalid", "Should be WC format like WC608-H07190"
        
        return True, None, None
    
    def _validate_injury_date(self, injury_date: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate injury date."""
        # Check common date formats
        date_patterns = [
            r'[A-Z][a-z]+\s+\d{1,2},\s+\d{4}',  # July 24, 2024
            r'\d{1,2}/\d{1,2}/\d{4}',            # 07/24/2024
            r'\d{4}-\d{1,2}-\d{1,2}'             # 2024-07-24
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, injury_date):
                return True, None, None
        
        return False, f"Date format '{injury_date}' not recognized", "Use standard date format"
    
    def _validate_body_parts(self, body_parts: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate body parts list."""
        if not body_parts or len(body_parts) == 0:
            return False, "No body parts specified", "Extract injured body part from document"
        
        # Check for reasonable body part names
        valid_parts = ['knee', 'shoulder', 'back', 'neck', 'ankle', 'wrist', 'hand', 'foot', 
                      'hip', 'elbow', 'spine', 'lumbar', 'cervical', 'thoracic']
        
        for part in body_parts:
            if not any(valid_part in part.lower() for valid_part in valid_parts):
                return False, f"Body part '{part}' may not be valid", "Verify body part extraction"
        
        return True, None, None
    
    def _validate_occupation(self, occupation: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate occupation."""
        if not occupation or len(occupation.strip()) < 3:
            return False, "Occupation is too short", "Extract full job title"
        
        return True, None, None
    
    def _validate_employer(self, employer: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate employer name."""
        if not employer or len(employer.strip()) < 2:
            return False, "Employer name is too short", "Extract full employer name"
        
        return True, None, None
    
    def _validate_exam_date(self, exam_date: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate scheduled exam date."""
        # Similar to injury date validation
        date_patterns = [
            r'[A-Z][a-z]+\s+\d{1,2},\s+\d{4}',  # September 9, 2025
            r'\d{1,2}/\d{1,2}/\d{4}',            # 09/09/2025
        ]
        
        for pattern in date_patterns:
            if re.match(pattern, exam_date):
                return True, None, None
        
        return False, f"Exam date format '{exam_date}' not recognized", "Use standard date format"
    
    def _generate_recommendations(self, field_data: QMEFieldData, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations for improving field data quality."""
        recommendations = []
        
        # Check field completeness
        missing_count = len([f for f in self.required_fields 
                           if getattr(field_data, f, None) is None])
        
        if missing_count > 0:
            recommendations.append(f"Extract {missing_count} missing fields to improve template quality")
        
        # Check for warning-level issues
        warning_count = len([i for i in issues if i.severity == 'warning'])
        if warning_count > 0:
            recommendations.append(f"Address {warning_count} field format warnings")
        
        # Specific recommendations based on field data
        if not field_data.age:
            recommendations.append("Patient age helps with medical assessment accuracy")
        
        if not field_data.gender:
            recommendations.append("Patient gender may be needed for medical evaluation")
        
        if not field_data.occupation:
            recommendations.append("Occupation details help assess work-related injury impact")
        
        return recommendations
    
    def _calculate_validation_score(self, field_data: QMEFieldData, issues: List[ValidationIssue]) -> float:
        """Calculate overall validation score (0.0 to 1.0)."""
        # Start with perfect score
        score = 1.0
        
        # Deduct for each issue based on severity and confidence impact
        for issue in issues:
            score -= issue.confidence_impact
        
        # Bonus for having all recommended fields
        present_fields = len([f for f in self.required_fields 
                            if getattr(field_data, f, None) is not None])
        completeness_bonus = (present_fields / len(self.required_fields)) * 0.1
        score += completeness_bonus
        
        # Ensure score stays within bounds
        return max(0.0, min(1.0, score))
    
    def generate_validation_report(self, validation_result: FieldValidationResult, 
                                 field_data: QMEFieldData) -> str:
        """Generate a comprehensive validation report."""
        report_lines = []
        report_lines.append("=== QME Field Validation Report ===")
        report_lines.append(f"Validation Score: {validation_result.validation_score:.2%}")
        report_lines.append(f"Ready for Template Generation: {'Yes' if validation_result.ready_for_template_generation else 'No'}")
        report_lines.append("")
        
        # Field status summary
        report_lines.append("Field Status Summary:")
        for field_name in self.required_fields:
            field_value = getattr(field_data, field_name, None)
            status = "✓" if field_value is not None else "✗"
            criticality = " (Critical)" if field_name in self.critical_fields else ""
            report_lines.append(f"  {status} {field_name.replace('_', ' ').title()}{criticality}")
        
        # Issues
        if validation_result.issues:
            report_lines.append("")
            report_lines.append("Validation Issues:")
            for issue in validation_result.issues:
                severity_icon = "🔴" if issue.severity == 'error' else "🟡"
                report_lines.append(f"  {severity_icon} {issue.field_name}: {issue.message}")
                if issue.suggested_fix:
                    report_lines.append(f"     → Suggestion: {issue.suggested_fix}")
        
        # Recommendations
        if validation_result.recommendations:
            report_lines.append("")
            report_lines.append("Recommendations:")
            for rec in validation_result.recommendations:
                report_lines.append(f"  • {rec}")
        
        return "\n".join(report_lines)