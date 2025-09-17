"""
QME Field Validator - Evidence-first validation system with confidence thresholds.

This module implements the evidence validation gateway with configurable confidence
thresholds, human-in-the-loop review queue, and comprehensive audit trails for
complete evidence traceability.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
import json
from enum import Enum
from pathlib import Path

from src.core.extraction.field_extraction_service import QMEFieldData, ExtractionResult, FieldExtraction, EvidenceSnippet
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ValidationStatus(Enum):
    """Validation status for fields based on confidence thresholds."""
    ACCEPTED = "accepted"      # confidence >= 0.8
    FLAGGED = "flagged"        # 0.5 <= confidence < 0.8
    MISSING = "missing"        # confidence < 0.5 or not found
    REJECTED = "rejected"      # failed validation rules


class FieldCategory(Enum):
    """Field categories for validation prioritization."""
    CRITICAL = "critical"      # Must have confidence >= 0.8
    STANDARD = "standard"      # Must have confidence >= 0.5
    OPTIONAL = "optional"      # No minimum confidence required


@dataclass
class ConfidenceThresholds:
    """Configurable confidence thresholds for validation."""
    critical_threshold: float = 0.8    # Critical fields (patient name, case number, etc.)
    standard_threshold: float = 0.5    # Standard fields
    flagged_threshold: float = 0.5     # Below this = flagged for review
    accepted_threshold: float = 0.8    # Above this = auto-accepted


@dataclass
class ValidationRule:
    """Enhanced validation rule with confidence and evidence requirements."""
    field_name: str
    rule_type: str  # 'required', 'format', 'range', 'custom', 'confidence'
    description: str
    field_category: FieldCategory
    validation_function: Optional[callable] = None
    error_message: str = ""
    severity: str = "error"  # 'error', 'warning', 'info'
    requires_evidence: bool = True
    min_confidence: Optional[float] = None


@dataclass
class ValidationIssue:
    """Enhanced validation issue with evidence context."""
    field_name: str
    issue_type: str
    severity: str
    message: str
    confidence: float = 0.0
    evidence_snippet: Optional[EvidenceSnippet] = None
    suggested_fix: Optional[str] = None
    confidence_impact: float = 0.0
    requires_human_review: bool = False


@dataclass
class ReviewQueueItem:
    """Item in human-in-the-loop review queue."""
    field_name: str
    extracted_value: Any
    confidence: float
    evidence_snippet: EvidenceSnippet
    validation_issues: List[ValidationIssue]
    source_context: str
    timestamp: datetime = field(default_factory=datetime.now)
    reviewer_notes: Optional[str] = None
    review_decision: Optional[str] = None  # 'accept', 'reject', 'modify'
    modified_value: Optional[Any] = None


@dataclass
class CrossValidationResult:
    """Result of cross-document validation."""
    field_name: str
    values_found: List[Any]
    consistency_score: float
    conflicting_values: List[Tuple[Any, float]]  # (value, confidence)
    recommended_value: Optional[Any] = None
    requires_disambiguation: bool = False


@dataclass
class ValidationReport:
    """Comprehensive evidence-first validation report."""
    # Field categorization by confidence
    accepted_fields: Dict[str, Any] = field(default_factory=dict)      # confidence >= 0.8
    flagged_fields: Dict[str, Any] = field(default_factory=dict)       # 0.5 <= confidence < 0.8
    missing_fields: List[str] = field(default_factory=list)            # confidence < 0.5
    rejected_fields: Dict[str, str] = field(default_factory=dict)      # failed validation
    
    # Confidence and evidence metrics
    overall_confidence: float = 0.0
    evidence_completeness: float = 0.0
    critical_field_coverage: float = 0.0
    
    # Review queue and validation issues
    review_queue: List[ReviewQueueItem] = field(default_factory=list)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    cross_validation_results: List[CrossValidationResult] = field(default_factory=list)
    
    # Status and recommendations
    can_generate_report: bool = False
    validation_status: ValidationStatus = ValidationStatus.MISSING
    recommendations: List[str] = field(default_factory=list)
    
    # Audit trail
    validation_timestamp: datetime = field(default_factory=datetime.now)
    thresholds_used: Optional[ConfidenceThresholds] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationAuditEntry:
    """Single entry in validation audit trail."""
    timestamp: datetime
    action: str  # 'field_validated', 'threshold_applied', 'review_queued', etc.
    field_name: str
    details: Dict[str, Any]
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    evidence_id: Optional[str] = None


@dataclass
class FieldValidationResult:
    """Result of field validation process."""
    validation_score: float
    ready_for_template_generation: bool
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    field_scores: Dict[str, float] = field(default_factory=dict)
    missing_critical_fields: List[str] = field(default_factory=list)


class EvidenceFirstValidator:
    """
    Evidence-first validation gateway with configurable confidence thresholds.
    
    Implements:
    - Confidence threshold enforcement (critical: ≥0.8, standard: ≥0.5)
    - Human-in-the-loop review queue for flagged fields
    - Cross-document validation and entity disambiguation
    - Complete audit trail generation for evidence traceability
    - Validation status tracking with detailed reporting
    """
    
    def __init__(self, thresholds: Optional[ConfidenceThresholds] = None):
        """Initialize the evidence-first validator."""
        self.thresholds = thresholds or ConfidenceThresholds()
        self.validation_rules = self._initialize_validation_rules()
        
        # Field categorization for validation prioritization
        self.critical_fields = {
            'name': FieldCategory.CRITICAL,
            'case_number': FieldCategory.CRITICAL,
            'claim_number': FieldCategory.CRITICAL,
            'injury_date': FieldCategory.CRITICAL
        }
        
        self.standard_fields = {
            'age': FieldCategory.STANDARD,
            'gender': FieldCategory.STANDARD,
            'body_parts': FieldCategory.STANDARD,
            'occupation': FieldCategory.STANDARD,
            'employer': FieldCategory.STANDARD,
            'scheduled_exam_date': FieldCategory.STANDARD
        }
        
        self.optional_fields = {
            'rom_measurements': FieldCategory.OPTIONAL,
            'ama_table_references': FieldCategory.OPTIONAL
        }
        
        # Cross-validation storage for consistency checking
        self.cross_validation_cache: Dict[str, List[Tuple[Any, float, str]]] = {}
        
        # Review queue management
        self.review_queue: List[ReviewQueueItem] = []
        
        # Audit trail storage
        self.audit_trail: List[ValidationAuditEntry] = []
    
    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize enhanced validation rules with confidence and evidence requirements."""
        rules = []
        
        # Critical field validation rules
        rules.append(ValidationRule(
            field_name='name',
            rule_type='required',
            description='Patient name must be present with high confidence',
            field_category=FieldCategory.CRITICAL,
            validation_function=self._validate_name,
            error_message='Patient name is required for QME template generation',
            severity='error',
            requires_evidence=True,
            min_confidence=self.thresholds.critical_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='case_number',
            rule_type='format',
            description='Case number must follow standard format with high confidence',
            field_category=FieldCategory.CRITICAL,
            validation_function=self._validate_case_number,
            error_message='Case number must be in valid format (e.g., ADJ19802400)',
            severity='error',
            requires_evidence=True,
            min_confidence=self.thresholds.critical_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='claim_number',
            rule_type='format',
            description='Claim number must follow WC format with high confidence',
            field_category=FieldCategory.CRITICAL,
            validation_function=self._validate_claim_number,
            error_message='Claim number must be in WC format (e.g., WC608-H07190)',
            severity='error',
            requires_evidence=True,
            min_confidence=self.thresholds.critical_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='injury_date',
            rule_type='format',
            description='Injury date must be valid with high confidence',
            field_category=FieldCategory.CRITICAL,
            validation_function=self._validate_injury_date,
            error_message='Injury date must be a valid date',
            severity='error',
            requires_evidence=True,
            min_confidence=self.thresholds.critical_threshold
        ))
        
        # Standard field validation rules
        rules.append(ValidationRule(
            field_name='age',
            rule_type='range',
            description='Age must be reasonable (18-100)',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_age,
            error_message='Age must be between 18 and 100 years',
            severity='warning',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='gender',
            rule_type='format',
            description='Gender must be Male or Female',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_gender,
            error_message='Gender must be specified as Male or Female',
            severity='warning',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='body_parts',
            rule_type='required',
            description='At least one body part must be specified',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_body_parts,
            error_message='At least one injured body part must be specified',
            severity='error',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='occupation',
            rule_type='format',
            description='Occupation should be descriptive',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_occupation,
            error_message='Occupation should be a descriptive job title',
            severity='warning',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='employer',
            rule_type='format',
            description='Employer name should be present',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_employer,
            error_message='Employer name should be specified',
            severity='warning',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        rules.append(ValidationRule(
            field_name='scheduled_exam_date',
            rule_type='format',
            description='Scheduled exam date must be valid',
            field_category=FieldCategory.STANDARD,
            validation_function=self._validate_exam_date,
            error_message='Scheduled exam date must be a valid future date',
            severity='warning',
            requires_evidence=True,
            min_confidence=self.thresholds.standard_threshold
        ))
        
        # Optional field validation rules
        rules.append(ValidationRule(
            field_name='rom_measurements',
            rule_type='format',
            description='ROM measurements should be valid numeric values',
            field_category=FieldCategory.OPTIONAL,
            validation_function=self._validate_rom_measurements,
            error_message='ROM measurements should be valid numeric values',
            severity='info',
            requires_evidence=False,
            min_confidence=0.3
        ))
        
        rules.append(ValidationRule(
            field_name='ama_table_references',
            rule_type='format',
            description='AMA table references should be valid table identifiers',
            field_category=FieldCategory.OPTIONAL,
            validation_function=self._validate_ama_references,
            error_message='AMA table references should be valid identifiers',
            severity='info',
            requires_evidence=False,
            min_confidence=0.3
        ))
        
        return rules
    
    def validate_evidence_first(self, extraction_result: ExtractionResult, 
                               document_id: str = None) -> ValidationReport:
        """
        Perform evidence-first validation with configurable confidence thresholds.
        
        Args:
            extraction_result: Result from structured extraction with confidence scores
            document_id: Optional document identifier for audit trail
            
        Returns:
            ValidationReport with accepted/flagged/missing field categorization
        """
        logger.info(f"Performing evidence-first validation for document {document_id}")
        
        # Initialize validation report
        report = ValidationReport(
            thresholds_used=self.thresholds,
            validation_timestamp=datetime.now()
        )
        
        # Clear previous audit trail for this validation
        self.audit_trail.clear()
        
        # Process each field with confidence-based validation
        field_data = extraction_result.field_data
        all_fields = {**self.critical_fields, **self.standard_fields, **self.optional_fields}
        
        for field_name, field_category in all_fields.items():
            self._validate_field_with_confidence(
                field_name, field_category, field_data, report, document_id
            )
        
        # Perform cross-document validation
        cross_validation_results = self._perform_cross_validation(field_data, report)
        report.cross_validation_results = cross_validation_results
        
        # Calculate overall metrics
        report.overall_confidence = self._calculate_overall_confidence(field_data)
        report.evidence_completeness = self._calculate_evidence_completeness(field_data)
        report.critical_field_coverage = self._calculate_critical_field_coverage(report)
        
        # Determine validation status and report generation readiness
        report.validation_status = self._determine_validation_status(report)
        report.can_generate_report = self._can_generate_report(report)
        
        # Generate recommendations
        report.recommendations = self._generate_evidence_recommendations(report)
        
        # Store audit trail in report
        report.audit_trail = [self._audit_entry_to_dict(entry) for entry in self.audit_trail]
        
        logger.info(f"Validation complete: {len(report.accepted_fields)} accepted, "
                   f"{len(report.flagged_fields)} flagged, {len(report.missing_fields)} missing")
        
        return report
    
    def _validate_field_with_confidence(self, field_name: str, field_category: FieldCategory,
                                      field_data: QMEFieldData, report: ValidationReport,
                                      document_id: str = None) -> None:
        """Validate individual field with confidence threshold enforcement."""
        field_value = getattr(field_data, field_name, None)
        field_extraction = field_data.field_extractions.get(field_name)
        confidence = field_data.extraction_confidence.get(field_name, 0.0)
        
        # Create audit entry
        audit_entry = ValidationAuditEntry(
            timestamp=datetime.now(),
            action='field_validated',
            field_name=field_name,
            details={
                'field_category': field_category.value,
                'has_value': field_value is not None,
                'has_extraction': field_extraction is not None
            },
            confidence_before=confidence
        )
        
        # Determine threshold based on field category
        if field_category == FieldCategory.CRITICAL:
            required_threshold = self.thresholds.critical_threshold
        elif field_category == FieldCategory.STANDARD:
            required_threshold = self.thresholds.standard_threshold
        else:  # OPTIONAL
            required_threshold = 0.0  # No minimum for optional fields
        
        # Check if field exists and has sufficient confidence
        if field_value is None or not field_extraction:
            # Field is missing
            report.missing_fields.append(field_name)
            audit_entry.details['status'] = 'missing'
            audit_entry.details['reason'] = 'no_extraction_found'
            
            if field_category in [FieldCategory.CRITICAL, FieldCategory.STANDARD]:
                issue = ValidationIssue(
                    field_name=field_name,
                    issue_type='missing_field',
                    severity='error' if field_category == FieldCategory.CRITICAL else 'warning',
                    message=f"{field_category.value.title()} field '{field_name}' is missing",
                    confidence=0.0,
                    suggested_fix=f"Extract {field_name} from document with confidence ≥{required_threshold}",
                    requires_human_review=True
                )
                report.validation_issues.append(issue)
        
        elif confidence < required_threshold:
            # Field has insufficient confidence
            if confidence >= self.thresholds.flagged_threshold:
                # Flag for human review
                report.flagged_fields[field_name] = field_value
                audit_entry.details['status'] = 'flagged'
                audit_entry.details['reason'] = f'confidence_{confidence:.2f}_below_threshold_{required_threshold}'
                
                # Add to review queue
                review_item = ReviewQueueItem(
                    field_name=field_name,
                    extracted_value=field_value,
                    confidence=confidence,
                    evidence_snippet=field_extraction.evidence,
                    validation_issues=[],
                    source_context=self._get_source_context(field_extraction)
                )
                report.review_queue.append(review_item)
                self.review_queue.append(review_item)
                
            else:
                # Confidence too low, treat as missing
                report.missing_fields.append(field_name)
                audit_entry.details['status'] = 'missing'
                audit_entry.details['reason'] = f'confidence_{confidence:.2f}_too_low'
                
            issue = ValidationIssue(
                field_name=field_name,
                issue_type='low_confidence',
                severity='warning' if confidence >= self.thresholds.flagged_threshold else 'error',
                message=f"Field '{field_name}' confidence {confidence:.2f} below required {required_threshold}",
                confidence=confidence,
                evidence_snippet=field_extraction.evidence if field_extraction else None,
                suggested_fix=f"Improve extraction accuracy or manually verify {field_name}",
                requires_human_review=True
            )
            report.validation_issues.append(issue)
        
        else:
            # Field meets confidence threshold, validate content
            content_valid, validation_issues = self._validate_field_content(
                field_name, field_value, field_extraction
            )
            
            if content_valid:
                # Accept field
                report.accepted_fields[field_name] = field_value
                audit_entry.details['status'] = 'accepted'
                audit_entry.details['reason'] = f'confidence_{confidence:.2f}_above_threshold_{required_threshold}'
            else:
                # Content validation failed
                report.rejected_fields[field_name] = f"Content validation failed: {validation_issues[0].message if validation_issues else 'Unknown error'}"
                audit_entry.details['status'] = 'rejected'
                audit_entry.details['reason'] = 'content_validation_failed'
                
                report.validation_issues.extend(validation_issues)
        
        # Store audit entry
        self.audit_trail.append(audit_entry)
    
    def _validate_field_content(self, field_name: str, field_value: Any, 
                              field_extraction: FieldExtraction) -> Tuple[bool, List[ValidationIssue]]:
        """Validate field content using validation rules."""
        issues = []
        
        # Find validation rule for this field
        rule = next((r for r in self.validation_rules if r.field_name == field_name), None)
        if not rule or not rule.validation_function:
            return True, []  # No validation rule, assume valid
        
        # Run validation function
        try:
            is_valid, error_msg, suggestion = rule.validation_function(field_value)
            
            if not is_valid:
                issue = ValidationIssue(
                    field_name=field_name,
                    issue_type='content_validation_failed',
                    severity=rule.severity,
                    message=error_msg or rule.error_message,
                    confidence=field_extraction.confidence if field_extraction else 0.0,
                    evidence_snippet=field_extraction.evidence if field_extraction else None,
                    suggested_fix=suggestion,
                    requires_human_review=rule.severity == 'error'
                )
                issues.append(issue)
                return False, issues
            
            return True, []
            
        except Exception as e:
            logger.error(f"Error validating field {field_name}: {e}")
            issue = ValidationIssue(
                field_name=field_name,
                issue_type='validation_error',
                severity='error',
                message=f"Validation error: {str(e)}",
                confidence=field_extraction.confidence if field_extraction else 0.0,
                suggested_fix="Check field extraction and validation logic",
                requires_human_review=True
            )
            issues.append(issue)
            return False, issues
    
    def _perform_cross_validation(self, field_data: QMEFieldData, 
                                report: ValidationReport) -> List[CrossValidationResult]:
        """Perform cross-document validation for consistency checking."""
        cross_validation_results = []
        
        # Check each field against cached values from previous documents
        for field_name in {**self.critical_fields, **self.standard_fields}.keys():
            field_value = getattr(field_data, field_name, None)
            if field_value is None:
                continue
            
            confidence = field_data.extraction_confidence.get(field_name, 0.0)
            
            # Get cached values for this field
            cached_values = self.cross_validation_cache.get(field_name, [])
            
            if not cached_values:
                # First occurrence, cache it
                self.cross_validation_cache[field_name] = [(field_value, confidence, datetime.now().isoformat())]
                continue
            
            # Check for consistency with cached values
            conflicting_values = []
            consistency_scores = []
            
            for cached_value, cached_confidence, cached_timestamp in cached_values:
                if self._values_are_consistent(field_value, cached_value, field_name):
                    # Values are consistent
                    consistency_scores.append(min(confidence, cached_confidence))
                else:
                    # Values conflict
                    conflicting_values.append((cached_value, cached_confidence))
            
            # Calculate overall consistency score
            if consistency_scores:
                avg_consistency = sum(consistency_scores) / len(consistency_scores)
            else:
                avg_consistency = 0.1  # Low consistency if no matches
            
            # Determine if disambiguation is needed
            requires_disambiguation = len(conflicting_values) > 0 and avg_consistency < 0.7
            
            # Recommend value based on highest confidence
            all_values = [(field_value, confidence)] + conflicting_values
            recommended_value = max(all_values, key=lambda x: x[1])[0]
            
            cross_validation_result = CrossValidationResult(
                field_name=field_name,
                values_found=[field_value] + [v[0] for v in conflicting_values],
                consistency_score=avg_consistency,
                conflicting_values=conflicting_values,
                recommended_value=recommended_value,
                requires_disambiguation=requires_disambiguation
            )
            
            cross_validation_results.append(cross_validation_result)
            
            # Add to validation issues if disambiguation needed
            if requires_disambiguation:
                issue = ValidationIssue(
                    field_name=field_name,
                    issue_type='cross_validation_conflict',
                    severity='warning',
                    message=f"Field '{field_name}' conflicts with previous extractions",
                    confidence=confidence,
                    suggested_fix=f"Manually verify {field_name} value across documents",
                    requires_human_review=True
                )
                report.validation_issues.append(issue)
            
            # Cache current value
            self.cross_validation_cache[field_name].append((field_value, confidence, datetime.now().isoformat()))
        
        return cross_validation_results
    
    def _values_are_consistent(self, value1: Any, value2: Any, field_name: str) -> bool:
        """Check if two field values are consistent."""
        if value1 == value2:
            return True
        
        # Handle string comparisons with normalization
        if isinstance(value1, str) and isinstance(value2, str):
            # Normalize whitespace and case
            norm1 = re.sub(r'\s+', ' ', value1.strip().lower())
            norm2 = re.sub(r'\s+', ' ', value2.strip().lower())
            
            if norm1 == norm2:
                return True
            
            # Check for partial matches (e.g., "John Smith" vs "John A. Smith")
            if field_name == 'name':
                # Split names and check if all parts of shorter name are in longer name
                parts1 = norm1.split()
                parts2 = norm2.split()
                shorter_parts = parts1 if len(parts1) <= len(parts2) else parts2
                longer_parts = parts2 if len(parts1) <= len(parts2) else parts1
                
                return all(part in longer_parts for part in shorter_parts)
            
            # For other string fields, check similarity
            similarity = self._calculate_string_similarity(norm1, norm2)
            return similarity > 0.8
        
        # Handle list comparisons (e.g., body_parts)
        if isinstance(value1, list) and isinstance(value2, list):
            # Check if there's significant overlap
            set1 = set(str(v).lower() for v in value1)
            set2 = set(str(v).lower() for v in value2)
            
            if not set1 or not set2:
                return False
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union > 0.6  # 60% overlap threshold
        
        return False
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using simple character overlap."""
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        chars1 = set(str1.lower())
        chars2 = set(str2.lower())
        
        if not chars1 or not chars2:
            return 0.0
        
        intersection = len(chars1.intersection(chars2))
        union = len(chars1.union(chars2))
        
        return intersection / union if union > 0 else 0.0
    
    def _get_source_context(self, field_extraction: FieldExtraction) -> str:
        """Get source context for review queue item."""
        if not field_extraction or not field_extraction.evidence:
            return "No source context available"
        
        evidence = field_extraction.evidence
        return f"Page {evidence.coordinates.page_number}, Line {evidence.coordinates.line_number or 'N/A'}: {evidence.context[:200]}..."
    
    def _calculate_overall_confidence(self, field_data: QMEFieldData) -> float:
        """Calculate overall confidence across all extracted fields."""
        confidences = []
        
        # Weight critical fields more heavily
        for field_name in self.critical_fields.keys():
            confidence = field_data.extraction_confidence.get(field_name, 0.0)
            confidences.extend([confidence] * 3)  # Triple weight for critical fields
        
        # Add standard fields
        for field_name in self.standard_fields.keys():
            confidence = field_data.extraction_confidence.get(field_name, 0.0)
            confidences.append(confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _calculate_evidence_completeness(self, field_data: QMEFieldData) -> float:
        """Calculate evidence completeness based on field coverage."""
        total_fields = len(self.critical_fields) + len(self.standard_fields)
        fields_with_evidence = 0
        
        for field_name in {**self.critical_fields, **self.standard_fields}.keys():
            if (field_name in field_data.field_extractions and 
                field_data.extraction_confidence.get(field_name, 0.0) >= self.thresholds.flagged_threshold):
                fields_with_evidence += 1
        
        return fields_with_evidence / total_fields if total_fields > 0 else 0.0
    
    def _calculate_critical_field_coverage(self, report: ValidationReport) -> float:
        """Calculate coverage of critical fields."""
        total_critical = len(self.critical_fields)
        covered_critical = len([f for f in self.critical_fields.keys() 
                               if f in report.accepted_fields or f in report.flagged_fields])
        
        return covered_critical / total_critical if total_critical > 0 else 0.0
    
    def _determine_validation_status(self, report: ValidationReport) -> ValidationStatus:
        """Determine overall validation status."""
        critical_missing = [f for f in self.critical_fields.keys() if f in report.missing_fields]
        critical_rejected = [f for f in self.critical_fields.keys() if f in report.rejected_fields]
        
        if critical_missing or critical_rejected:
            return ValidationStatus.MISSING
        
        if report.flagged_fields:
            return ValidationStatus.FLAGGED
        
        if report.accepted_fields:
            return ValidationStatus.ACCEPTED
        
        return ValidationStatus.MISSING
    
    def _can_generate_report(self, report: ValidationReport) -> bool:
        """Determine if report can be generated based on validation results."""
        # All critical fields must be accepted or flagged (not missing/rejected)
        for field_name in self.critical_fields.keys():
            if field_name in report.missing_fields or field_name in report.rejected_fields:
                return False
        
        # Must have minimum evidence completeness
        if report.evidence_completeness < 0.6:  # 60% minimum
            return False
        
        # Must have minimum critical field coverage
        if report.critical_field_coverage < 1.0:  # 100% critical field coverage required
            return False
        
        return True
    
    def _generate_evidence_recommendations(self, report: ValidationReport) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Missing critical fields
        critical_missing = [f for f in self.critical_fields.keys() if f in report.missing_fields]
        if critical_missing:
            recommendations.append(f"Extract missing critical fields: {', '.join(critical_missing)}")
        
        # Low confidence fields
        if report.flagged_fields:
            recommendations.append(f"Review {len(report.flagged_fields)} flagged fields for accuracy")
        
        # Cross-validation conflicts
        conflicts = [r for r in report.cross_validation_results if r.requires_disambiguation]
        if conflicts:
            recommendations.append(f"Resolve {len(conflicts)} cross-document conflicts")
        
        # Evidence completeness
        if report.evidence_completeness < 0.8:
            recommendations.append("Improve document quality or extraction patterns to increase evidence completeness")
        
        # Review queue items
        if report.review_queue:
            recommendations.append(f"Complete human review of {len(report.review_queue)} flagged items")
        
        return recommendations
    
    def _audit_entry_to_dict(self, entry: ValidationAuditEntry) -> Dict[str, Any]:
        """Convert audit entry to dictionary for serialization."""
        return {
            'timestamp': entry.timestamp.isoformat(),
            'action': entry.action,
            'field_name': entry.field_name,
            'details': entry.details,
            'confidence_before': entry.confidence_before,
            'confidence_after': entry.confidence_after,
            'evidence_id': entry.evidence_id
        }
    
    def update_confidence_thresholds(self, new_thresholds: ConfidenceThresholds) -> None:
        """Update confidence thresholds for validation."""
        self.thresholds = new_thresholds
        logger.info(f"Updated confidence thresholds: critical={new_thresholds.critical_threshold}, "
                   f"standard={new_thresholds.standard_threshold}")
    
    def get_review_queue(self) -> List[ReviewQueueItem]:
        """Get current human review queue."""
        return self.review_queue.copy()
    
    def process_review_decision(self, field_name: str, decision: str, 
                              modified_value: Any = None, reviewer_notes: str = None) -> bool:
        """Process human review decision for flagged field."""
        # Find review item
        review_item = next((item for item in self.review_queue 
                           if item.field_name == field_name), None)
        
        if not review_item:
            logger.warning(f"Review item not found for field {field_name}")
            return False
        
        # Update review item
        review_item.review_decision = decision
        review_item.modified_value = modified_value
        review_item.reviewer_notes = reviewer_notes
        
        # Create audit entry
        audit_entry = ValidationAuditEntry(
            timestamp=datetime.now(),
            action='human_review_processed',
            field_name=field_name,
            details={
                'decision': decision,
                'original_value': review_item.extracted_value,
                'modified_value': modified_value,
                'reviewer_notes': reviewer_notes
            }
        )
        self.audit_trail.append(audit_entry)
        
        logger.info(f"Processed review decision for {field_name}: {decision}")
        return True
    
    def clear_review_queue(self) -> None:
        """Clear the human review queue."""
        self.review_queue.clear()
        logger.info("Review queue cleared")
    
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
    
    def _validate_rom_measurements(self, rom_data: Dict[str, List[float]]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate ROM measurements data structure and values."""
        if not isinstance(rom_data, dict):
            return False, "ROM measurements must be a dictionary", "Ensure ROM data is properly structured"
        
        if not rom_data:
            return False, "No ROM measurements found", "Extract ROM measurements from document"
        
        for body_part, measurements in rom_data.items():
            if not isinstance(measurements, list):
                return False, f"ROM measurements for {body_part} must be a list", "Check ROM data structure"
            
            if not measurements:
                return False, f"No measurements found for {body_part}", f"Extract measurements for {body_part}"
            
            # Check for reasonable ROM values (0-360 degrees typically)
            for measurement in measurements:
                if not isinstance(measurement, (int, float)):
                    return False, f"Invalid measurement type for {body_part}", "Ensure measurements are numeric"
                
                if measurement < 0 or measurement > 360:
                    return False, f"ROM measurement {measurement} for {body_part} outside valid range", "Check measurement values (0-360 degrees)"
        
        return True, None, None
    
    def _validate_ama_references(self, references: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate AMA table references."""
        if not isinstance(references, list):
            return False, "AMA references must be a list", "Ensure AMA references are properly structured"
        
        if not references:
            return False, "No AMA table references found", "Extract AMA table references from document"
        
        # Common AMA table patterns
        valid_patterns = [
            r'Table\s+\d+[A-Z]?-\d+',  # Table 15-3, Table 16A-1, etc.
            r'Combined\s+Values\s+Chart',
            r'Figure\s+\d+-\d+',
            r'Page\s+\d+',
            r'Chapter\s+\d+'
        ]
        
        for reference in references:
            if not isinstance(reference, str):
                return False, f"Invalid reference type: {type(reference)}", "Ensure references are strings"
            
            # Check if reference matches any valid pattern
            is_valid_reference = any(re.search(pattern, reference, re.IGNORECASE) 
                                   for pattern in valid_patterns)
            
            if not is_valid_reference:
                return False, f"Invalid AMA reference format: {reference}", "Check AMA reference format (e.g., Table 15-3)"
        
        return True, None, None
    
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
    
    def generate_evidence_validation_report(self, validation_report: ValidationReport) -> str:
        """Generate comprehensive evidence-first validation report."""
        report_lines = []
        report_lines.append("=== Evidence-First QME Validation Report ===")
        report_lines.append(f"Validation Timestamp: {validation_report.validation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Overall Status: {validation_report.validation_status.value.upper()}")
        report_lines.append(f"Can Generate Report: {'Yes' if validation_report.can_generate_report else 'No'}")
        report_lines.append("")
        
        # Confidence metrics
        report_lines.append("=== Confidence Metrics ===")
        report_lines.append(f"Overall Confidence: {validation_report.overall_confidence:.2%}")
        report_lines.append(f"Evidence Completeness: {validation_report.evidence_completeness:.2%}")
        report_lines.append(f"Critical Field Coverage: {validation_report.critical_field_coverage:.2%}")
        report_lines.append("")
        
        # Thresholds used
        if validation_report.thresholds_used:
            thresholds = validation_report.thresholds_used
            report_lines.append("=== Confidence Thresholds ===")
            report_lines.append(f"Critical Fields: ≥{thresholds.critical_threshold}")
            report_lines.append(f"Standard Fields: ≥{thresholds.standard_threshold}")
            report_lines.append(f"Flagged Threshold: ≥{thresholds.flagged_threshold}")
            report_lines.append("")
        
        # Field status breakdown
        report_lines.append("=== Field Status Breakdown ===")
        
        # Accepted fields
        if validation_report.accepted_fields:
            report_lines.append(f"✅ Accepted Fields ({len(validation_report.accepted_fields)}):")
            for field_name, value in validation_report.accepted_fields.items():
                report_lines.append(f"  • {field_name}: {value}")
            report_lines.append("")
        
        # Flagged fields
        if validation_report.flagged_fields:
            report_lines.append(f"⚠️  Flagged Fields ({len(validation_report.flagged_fields)}) - Require Review:")
            for field_name, value in validation_report.flagged_fields.items():
                report_lines.append(f"  • {field_name}: {value}")
            report_lines.append("")
        
        # Missing fields
        if validation_report.missing_fields:
            report_lines.append(f"❌ Missing Fields ({len(validation_report.missing_fields)}):")
            for field_name in validation_report.missing_fields:
                field_category = self._get_field_category(field_name)
                criticality = " (CRITICAL)" if field_category == FieldCategory.CRITICAL else ""
                report_lines.append(f"  • {field_name}{criticality}")
            report_lines.append("")
        
        # Rejected fields
        if validation_report.rejected_fields:
            report_lines.append(f"🚫 Rejected Fields ({len(validation_report.rejected_fields)}):")
            for field_name, reason in validation_report.rejected_fields.items():
                report_lines.append(f"  • {field_name}: {reason}")
            report_lines.append("")
        
        # Validation issues
        if validation_report.validation_issues:
            report_lines.append("=== Validation Issues ===")
            for issue in validation_report.validation_issues:
                severity_icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(issue.severity, "❓")
                report_lines.append(f"{severity_icon} {issue.field_name}: {issue.message}")
                if issue.suggested_fix:
                    report_lines.append(f"   → Fix: {issue.suggested_fix}")
                if issue.confidence > 0:
                    report_lines.append(f"   → Confidence: {issue.confidence:.2%}")
                if issue.requires_human_review:
                    report_lines.append(f"   → Requires human review")
            report_lines.append("")
        
        # Cross-validation results
        if validation_report.cross_validation_results:
            conflicts = [r for r in validation_report.cross_validation_results if r.requires_disambiguation]
            if conflicts:
                report_lines.append("=== Cross-Validation Conflicts ===")
                for conflict in conflicts:
                    report_lines.append(f"🔄 {conflict.field_name}:")
                    report_lines.append(f"   Values found: {conflict.values_found}")
                    report_lines.append(f"   Consistency score: {conflict.consistency_score:.2%}")
                    if conflict.recommended_value:
                        report_lines.append(f"   Recommended: {conflict.recommended_value}")
                report_lines.append("")
        
        # Review queue
        if validation_report.review_queue:
            report_lines.append(f"=== Human Review Queue ({len(validation_report.review_queue)} items) ===")
            for item in validation_report.review_queue:
                report_lines.append(f"📋 {item.field_name}:")
                report_lines.append(f"   Value: {item.extracted_value}")
                report_lines.append(f"   Confidence: {item.confidence:.2%}")
                report_lines.append(f"   Source: {item.source_context[:100]}...")
                if item.review_decision:
                    report_lines.append(f"   Decision: {item.review_decision}")
                    if item.reviewer_notes:
                        report_lines.append(f"   Notes: {item.reviewer_notes}")
            report_lines.append("")
        
        # Recommendations
        if validation_report.recommendations:
            report_lines.append("=== Recommendations ===")
            for i, rec in enumerate(validation_report.recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        # Audit trail summary
        if validation_report.audit_trail:
            report_lines.append(f"=== Audit Trail Summary ===")
            report_lines.append(f"Total audit entries: {len(validation_report.audit_trail)}")
            
            # Count actions
            action_counts = {}
            for entry in validation_report.audit_trail:
                action = entry.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
            
            for action, count in action_counts.items():
                report_lines.append(f"  • {action}: {count}")
        
        return "\n".join(report_lines)
    
    def _get_field_category(self, field_name: str) -> FieldCategory:
        """Get the category of a field."""
        if field_name in self.critical_fields:
            return FieldCategory.CRITICAL
        elif field_name in self.standard_fields:
            return FieldCategory.STANDARD
        else:
            return FieldCategory.OPTIONAL
    
    def export_validation_report_json(self, validation_report: ValidationReport) -> str:
        """Export validation report as JSON string."""
        report_dict = {
            'validation_timestamp': validation_report.validation_timestamp.isoformat(),
            'validation_status': validation_report.validation_status.value,
            'can_generate_report': validation_report.can_generate_report,
            'metrics': {
                'overall_confidence': validation_report.overall_confidence,
                'evidence_completeness': validation_report.evidence_completeness,
                'critical_field_coverage': validation_report.critical_field_coverage
            },
            'fields': {
                'accepted': validation_report.accepted_fields,
                'flagged': validation_report.flagged_fields,
                'missing': validation_report.missing_fields,
                'rejected': validation_report.rejected_fields
            },
            'thresholds': {
                'critical_threshold': validation_report.thresholds_used.critical_threshold if validation_report.thresholds_used else None,
                'standard_threshold': validation_report.thresholds_used.standard_threshold if validation_report.thresholds_used else None,
                'flagged_threshold': validation_report.thresholds_used.flagged_threshold if validation_report.thresholds_used else None,
                'accepted_threshold': validation_report.thresholds_used.accepted_threshold if validation_report.thresholds_used else None
            },
            'validation_issues': [
                {
                    'field_name': issue.field_name,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'message': issue.message,
                    'confidence': issue.confidence,
                    'suggested_fix': issue.suggested_fix,
                    'requires_human_review': issue.requires_human_review
                }
                for issue in validation_report.validation_issues
            ],
            'cross_validation_results': [
                {
                    'field_name': result.field_name,
                    'values_found': result.values_found,
                    'consistency_score': result.consistency_score,
                    'conflicting_values': result.conflicting_values,
                    'recommended_value': result.recommended_value,
                    'requires_disambiguation': result.requires_disambiguation
                }
                for result in validation_report.cross_validation_results
            ],
            'review_queue': [
                {
                    'field_name': item.field_name,
                    'extracted_value': item.extracted_value,
                    'confidence': item.confidence,
                    'source_context': item.source_context,
                    'timestamp': item.timestamp.isoformat(),
                    'review_decision': item.review_decision,
                    'reviewer_notes': item.reviewer_notes,
                    'modified_value': item.modified_value
                }
                for item in validation_report.review_queue
            ],
            'recommendations': validation_report.recommendations,
            'audit_trail': validation_report.audit_trail
        }
        
        return json.dumps(report_dict, indent=2, default=str)


# Maintain backward compatibility with old class name
QMEFieldValidator = EvidenceFirstValidator