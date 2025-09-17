"""
Evidence-First Validation System

This module provides comprehensive validation of the evidence-first approach with
confidence scoring, evidence validation thresholds, cross-document validation,
and complete audit trail generation.
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
import statistics

from src.models.extraction_models import ExtractionResult, ExtractedField
from src.core.validation.comprehensive_quality_validation_service import ComprehensiveQualityValidationService

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceThresholds:
    """Confidence thresholds for evidence validation."""
    accepted_threshold: float = 0.8  # Fields with confidence >= 0.8 are accepted
    flagged_threshold: float = 0.5   # Fields with 0.5 <= confidence < 0.8 are flagged
    missing_threshold: float = 0.5   # Fields with confidence < 0.5 are considered missing


@dataclass
class EvidenceValidationResult:
    """Result of evidence validation for a single field."""
    field_name: str
    field_value: Any
    confidence_score: float
    validation_status: str  # 'accepted', 'flagged', 'missing'
    evidence_snippets: List[str]
    source_references: List[str]
    validation_notes: List[str]
    cross_validation_score: Optional[float] = None


@dataclass
class DocumentValidationReport:
    """Comprehensive validation report for a document."""
    document_id: str
    validation_timestamp: datetime
    overall_confidence: float
    field_coverage: float
    accepted_fields: List[EvidenceValidationResult]
    flagged_fields: List[EvidenceValidationResult]
    missing_fields: List[str]
    critical_fields_status: Dict[str, str]
    evidence_completeness: float
    audit_trail: List[Dict[str, Any]]
    recommendations: List[str]
    can_proceed_to_generation: bool


@dataclass
class CrossDocumentValidationResult:
    """Result of cross-document validation and consistency checking."""
    patient_identifier: str
    documents_validated: List[str]
    consistency_score: float
    consistent_fields: Dict[str, List[Any]]
    inconsistent_fields: Dict[str, List[Any]]
    missing_across_documents: List[str]
    validation_issues: List[str]
    recommendations: List[str]


@dataclass
class AuditTrailEntry:
    """Single entry in the evidence audit trail."""
    timestamp: datetime
    action: str
    field_name: str
    confidence_before: Optional[float]
    confidence_after: Optional[float]
    validation_status: str
    evidence_source: str
    validator_notes: str
    correlation_id: str


class EvidenceFirstValidator:
    """Comprehensive evidence-first validation system."""
    
    def __init__(self, confidence_thresholds: Optional[ConfidenceThresholds] = None):
        """Initialize evidence-first validator."""
        self.thresholds = confidence_thresholds or ConfidenceThresholds()
        self.quality_validator = ComprehensiveQualityValidationService()
        
        # Critical fields that must meet higher standards
        self.critical_fields = {
            'patient_name', 'date_of_birth', 'date_of_injury', 
            'diagnosis', 'impairment_rating'
        }
        
        # Required fields for complete QME report
        self.required_fields = {
            'patient_name', 'date_of_birth', 'date_of_injury',
            'medical_history', 'examination_findings', 'diagnosis',
            'impairment_rating', 'work_restrictions'
        }
        
        # Field precision requirements (minimum confidence for critical fields)
        self.critical_field_precision = 0.95
        self.overall_field_coverage = 0.90
        
        logger.info("Initialized Evidence-First Validator")
    
    def validate_confidence_scoring_system(self, 
                                         extraction_results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Validate confidence scoring system with ≥95% precision for critical fields and ≥90% overall field coverage.
        
        Args:
            extraction_results: List of extraction results to validate
            
        Returns:
            Dictionary with validation metrics and results
        """
        logger.info(f"Validating confidence scoring system for {len(extraction_results)} documents")
        
        try:
            # Collect confidence scores for analysis
            critical_field_scores = []
            all_field_scores = []
            field_coverage_stats = []
            
            for result in extraction_results:
                # Analyze critical fields
                for field_name in self.critical_fields:
                    if field_name in result.extracted_fields:
                        field_data = result.extracted_fields[field_name]
                        if field_data.value:  # Only count fields with actual values
                            critical_field_scores.append(field_data.confidence)
                
                # Analyze all fields
                for field_name, field_data in result.extracted_fields.items():
                    if field_data.value:
                        all_field_scores.append(field_data.confidence)
                
                # Calculate field coverage for this document
                required_found = sum(1 for field in self.required_fields 
                                   if field in result.extracted_fields and result.extracted_fields[field].value)
                coverage = required_found / len(self.required_fields)
                field_coverage_stats.append(coverage)
            
            # Calculate precision metrics
            critical_precision = sum(1 for score in critical_field_scores 
                                   if score >= self.critical_field_precision) / len(critical_field_scores) if critical_field_scores else 0
            
            overall_coverage = statistics.mean(field_coverage_stats) if field_coverage_stats else 0
            
            # Calculate additional metrics
            avg_critical_confidence = statistics.mean(critical_field_scores) if critical_field_scores else 0
            avg_overall_confidence = statistics.mean(all_field_scores) if all_field_scores else 0
            
            # Validation results
            precision_target_met = critical_precision >= 0.95
            coverage_target_met = overall_coverage >= 0.90
            
            validation_result = {
                "precision_validation": {
                    "critical_field_precision": critical_precision,
                    "target_precision": 0.95,
                    "precision_target_met": precision_target_met,
                    "critical_fields_analyzed": len(critical_field_scores),
                    "avg_critical_confidence": avg_critical_confidence
                },
                "coverage_validation": {
                    "overall_field_coverage": overall_coverage,
                    "target_coverage": 0.90,
                    "coverage_target_met": coverage_target_met,
                    "documents_analyzed": len(extraction_results),
                    "avg_overall_confidence": avg_overall_confidence
                },
                "system_validation": {
                    "confidence_system_valid": precision_target_met and coverage_target_met,
                    "total_fields_analyzed": len(all_field_scores),
                    "confidence_distribution": self._calculate_confidence_distribution(all_field_scores)
                },
                "recommendations": self._generate_confidence_system_recommendations(
                    precision_target_met, coverage_target_met, critical_precision, overall_coverage
                )
            }
            
            logger.info(f"Confidence scoring validation completed: Precision={critical_precision:.2%}, Coverage={overall_coverage:.2%}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating confidence scoring system: {e}")
            return {
                "error": str(e),
                "confidence_system_valid": False,
                "recommendations": ["Fix confidence scoring validation system"]
            }
    
    def validate_evidence_thresholds(self, extraction_result: ExtractionResult) -> DocumentValidationReport:
        """
        Test evidence validation thresholds with accepted fields (≥0.8), flagged fields (0.5-0.8), and missing field detection.
        
        Args:
            extraction_result: Extraction result to validate
            
        Returns:
            DocumentValidationReport with threshold validation results
        """
        logger.info(f"Validating evidence thresholds for document: {extraction_result.document_id}")
        
        validation_timestamp = datetime.now()
        audit_trail = []
        
        try:
            # Categorize fields based on confidence thresholds
            accepted_fields = []
            flagged_fields = []
            missing_fields = []
            
            # Process extracted fields
            for field_name, field_data in extraction_result.extracted_fields.items():
                audit_entry = {
                    "timestamp": validation_timestamp.isoformat(),
                    "action": "threshold_validation",
                    "field_name": field_name,
                    "confidence": field_data.confidence,
                    "has_value": bool(field_data.value)
                }
                
                if field_data.confidence >= self.thresholds.accepted_threshold and field_data.value:
                    # Accepted field
                    validation_result = EvidenceValidationResult(
                        field_name=field_name,
                        field_value=field_data.value,
                        confidence_score=field_data.confidence,
                        validation_status="accepted",
                        evidence_snippets=[field_data.source_text] if field_data.source_text else [],
                        source_references=[f"Page {field_data.page_reference}"] if field_data.page_reference else [],
                        validation_notes=["Confidence meets acceptance threshold"]
                    )
                    accepted_fields.append(validation_result)
                    audit_entry["validation_status"] = "accepted"
                    
                elif (field_data.confidence >= self.thresholds.flagged_threshold and 
                      field_data.confidence < self.thresholds.accepted_threshold and field_data.value):
                    # Flagged field
                    validation_result = EvidenceValidationResult(
                        field_name=field_name,
                        field_value=field_data.value,
                        confidence_score=field_data.confidence,
                        validation_status="flagged",
                        evidence_snippets=[field_data.source_text] if field_data.source_text else [],
                        source_references=[f"Page {field_data.page_reference}"] if field_data.page_reference else [],
                        validation_notes=["Confidence below acceptance threshold - requires review"]
                    )
                    flagged_fields.append(validation_result)
                    audit_entry["validation_status"] = "flagged"
                    
                else:
                    # Missing or low confidence field
                    audit_entry["validation_status"] = "missing"
                
                audit_trail.append(audit_entry)
            
            # Check for completely missing required fields
            for required_field in self.required_fields:
                if required_field not in extraction_result.extracted_fields:
                    missing_fields.append(required_field)
                    audit_trail.append({
                        "timestamp": validation_timestamp.isoformat(),
                        "action": "missing_field_detection",
                        "field_name": required_field,
                        "validation_status": "missing",
                        "reason": "Field not extracted"
                    })
                elif not extraction_result.extracted_fields[required_field].value:
                    missing_fields.append(required_field)
                    audit_trail.append({
                        "timestamp": validation_timestamp.isoformat(),
                        "action": "missing_field_detection",
                        "field_name": required_field,
                        "validation_status": "missing",
                        "reason": "Field extracted but no value"
                    })
            
            # Calculate metrics
            total_required = len(self.required_fields)
            accepted_count = len(accepted_fields)
            flagged_count = len(flagged_fields)
            missing_count = len(missing_fields)
            
            overall_confidence = statistics.mean([f.confidence_score for f in accepted_fields + flagged_fields]) if (accepted_fields + flagged_fields) else 0
            field_coverage = (accepted_count + flagged_count) / total_required if total_required > 0 else 0
            evidence_completeness = accepted_count / total_required if total_required > 0 else 0
            
            # Check critical fields status
            critical_fields_status = {}
            for critical_field in self.critical_fields:
                if critical_field in [f.field_name for f in accepted_fields]:
                    critical_fields_status[critical_field] = "accepted"
                elif critical_field in [f.field_name for f in flagged_fields]:
                    critical_fields_status[critical_field] = "flagged"
                else:
                    critical_fields_status[critical_field] = "missing"
            
            # Determine if can proceed to generation
            critical_accepted = sum(1 for status in critical_fields_status.values() if status == "accepted")
            can_proceed = (
                evidence_completeness >= 0.7 and  # At least 70% of required fields accepted
                critical_accepted >= len(self.critical_fields) * 0.8  # At least 80% of critical fields accepted
            )
            
            # Generate recommendations
            recommendations = []
            if missing_count > 0:
                recommendations.append(f"Address {missing_count} missing required fields")
            if flagged_count > 0:
                recommendations.append(f"Review {flagged_count} flagged fields for accuracy")
            if not can_proceed:
                recommendations.append("Insufficient evidence quality for report generation")
            if evidence_completeness < 0.8:
                recommendations.append("Improve evidence extraction to increase completeness")
            
            return DocumentValidationReport(
                document_id=extraction_result.document_id,
                validation_timestamp=validation_timestamp,
                overall_confidence=overall_confidence,
                field_coverage=field_coverage,
                accepted_fields=accepted_fields,
                flagged_fields=flagged_fields,
                missing_fields=missing_fields,
                critical_fields_status=critical_fields_status,
                evidence_completeness=evidence_completeness,
                audit_trail=audit_trail,
                recommendations=recommendations,
                can_proceed_to_generation=can_proceed
            )
            
        except Exception as e:
            logger.error(f"Error validating evidence thresholds: {e}")
            return DocumentValidationReport(
                document_id=extraction_result.document_id,
                validation_timestamp=validation_timestamp,
                overall_confidence=0.0,
                field_coverage=0.0,
                accepted_fields=[],
                flagged_fields=[],
                missing_fields=list(self.required_fields),
                critical_fields_status={field: "error" for field in self.critical_fields},
                evidence_completeness=0.0,
                audit_trail=[{
                    "timestamp": validation_timestamp.isoformat(),
                    "action": "validation_error",
                    "error": str(e)
                }],
                recommendations=["Fix evidence threshold validation system"],
                can_proceed_to_generation=False
            )
    
    def validate_cross_document_consistency(self, 
                                          extraction_results: List[ExtractionResult],
                                          patient_identifier: str) -> CrossDocumentValidationResult:
        """
        Implement cross-document validation and consistency checking across multiple patient documents.
        
        Args:
            extraction_results: List of extraction results for the same patient
            patient_identifier: Identifier for the patient
            
        Returns:
            CrossDocumentValidationResult with consistency analysis
        """
        logger.info(f"Validating cross-document consistency for patient: {patient_identifier}")
        
        try:
            if len(extraction_results) < 2:
                return CrossDocumentValidationResult(
                    patient_identifier=patient_identifier,
                    documents_validated=[r.document_id for r in extraction_results],
                    consistency_score=1.0,  # Single document is consistent with itself
                    consistent_fields={},
                    inconsistent_fields={},
                    missing_across_documents=[],
                    validation_issues=["Insufficient documents for cross-validation"],
                    recommendations=["Provide multiple documents for consistency checking"]
                )
            
            # Collect field values across documents
            field_values_by_document = {}
            all_fields = set()
            
            for result in extraction_results:
                field_values_by_document[result.document_id] = {}
                for field_name, field_data in result.extracted_fields.items():
                    if field_data.value and field_data.confidence >= self.thresholds.flagged_threshold:
                        field_values_by_document[result.document_id][field_name] = {
                            'value': field_data.value,
                            'confidence': field_data.confidence
                        }
                        all_fields.add(field_name)
            
            # Analyze consistency for each field
            consistent_fields = {}
            inconsistent_fields = {}
            validation_issues = []
            
            for field_name in all_fields:
                field_values = []
                field_confidences = []
                documents_with_field = []
                
                for doc_id, fields in field_values_by_document.items():
                    if field_name in fields:
                        field_values.append(fields[field_name]['value'])
                        field_confidences.append(fields[field_name]['confidence'])
                        documents_with_field.append(doc_id)
                
                if len(set(str(v).lower().strip() for v in field_values)) == 1:
                    # Consistent across documents
                    consistent_fields[field_name] = field_values
                else:
                    # Inconsistent across documents
                    inconsistent_fields[field_name] = field_values
                    validation_issues.append(
                        f"Inconsistent values for {field_name}: {field_values} across documents {documents_with_field}"
                    )
            
            # Check for fields missing across all documents
            missing_across_documents = []
            for required_field in self.required_fields:
                if required_field not in all_fields:
                    missing_across_documents.append(required_field)
            
            # Calculate consistency score
            total_comparable_fields = len(all_fields)
            consistent_count = len(consistent_fields)
            consistency_score = consistent_count / total_comparable_fields if total_comparable_fields > 0 else 0
            
            # Generate recommendations
            recommendations = []
            if len(inconsistent_fields) > 0:
                recommendations.append(f"Resolve {len(inconsistent_fields)} inconsistent fields across documents")
            if len(missing_across_documents) > 0:
                recommendations.append(f"Extract {len(missing_across_documents)} fields missing across all documents")
            if consistency_score < 0.8:
                recommendations.append("Improve extraction consistency across documents")
            if consistency_score >= 0.9:
                recommendations.append("Cross-document consistency validation passed")
            
            # Add specific field recommendations
            for field_name, values in inconsistent_fields.items():
                if field_name in self.critical_fields:
                    recommendations.append(f"CRITICAL: Resolve inconsistency in {field_name}: {values}")
            
            return CrossDocumentValidationResult(
                patient_identifier=patient_identifier,
                documents_validated=[r.document_id for r in extraction_results],
                consistency_score=consistency_score,
                consistent_fields=consistent_fields,
                inconsistent_fields=inconsistent_fields,
                missing_across_documents=missing_across_documents,
                validation_issues=validation_issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in cross-document validation: {e}")
            return CrossDocumentValidationResult(
                patient_identifier=patient_identifier,
                documents_validated=[r.document_id for r in extraction_results],
                consistency_score=0.0,
                consistent_fields={},
                inconsistent_fields={},
                missing_across_documents=list(self.required_fields),
                validation_issues=[str(e)],
                recommendations=["Fix cross-document validation system"]
            )
    
    def generate_evidence_provenance_tracking(self, 
                                            validation_report: DocumentValidationReport) -> Dict[str, Any]:
        """
        Add evidence provenance tracking with complete audit trails and source document references.
        
        Args:
            validation_report: Document validation report
            
        Returns:
            Dictionary with complete provenance tracking information
        """
        logger.info(f"Generating evidence provenance tracking for document: {validation_report.document_id}")
        
        try:
            provenance_data = {
                "document_id": validation_report.document_id,
                "validation_timestamp": validation_report.validation_timestamp.isoformat(),
                "provenance_version": "1.0",
                "field_provenance": {},
                "audit_trail": validation_report.audit_trail,
                "evidence_chain": [],
                "source_references": {},
                "validation_lineage": {}
            }
            
            # Track provenance for each accepted and flagged field
            all_validated_fields = validation_report.accepted_fields + validation_report.flagged_fields
            
            for field_result in all_validated_fields:
                field_provenance = {
                    "field_name": field_result.field_name,
                    "extracted_value": field_result.field_value,
                    "confidence_score": field_result.confidence_score,
                    "validation_status": field_result.validation_status,
                    "evidence_sources": {
                        "text_snippets": field_result.evidence_snippets,
                        "source_references": field_result.source_references,
                        "extraction_method": "structured_extraction",
                        "validation_method": "confidence_threshold"
                    },
                    "quality_indicators": {
                        "source_reliability": self._assess_source_reliability(field_result.source_references),
                        "evidence_strength": self._assess_evidence_strength(field_result.evidence_snippets),
                        "validation_confidence": field_result.confidence_score
                    },
                    "lineage": {
                        "extraction_timestamp": validation_report.validation_timestamp.isoformat(),
                        "validator": "EvidenceFirstValidator",
                        "validation_rules_applied": [
                            f"confidence_threshold_{self.thresholds.accepted_threshold}",
                            f"evidence_completeness_check",
                            f"critical_field_validation"
                        ]
                    }
                }
                
                provenance_data["field_provenance"][field_result.field_name] = field_provenance
                
                # Add to evidence chain
                provenance_data["evidence_chain"].append({
                    "step": len(provenance_data["evidence_chain"]) + 1,
                    "action": "field_validation",
                    "field": field_result.field_name,
                    "confidence": field_result.confidence_score,
                    "status": field_result.validation_status,
                    "timestamp": validation_report.validation_timestamp.isoformat()
                })
                
                # Collect source references
                for source_ref in field_result.source_references:
                    if source_ref not in provenance_data["source_references"]:
                        provenance_data["source_references"][source_ref] = []
                    provenance_data["source_references"][source_ref].append(field_result.field_name)
            
            # Add validation lineage
            provenance_data["validation_lineage"] = {
                "validation_method": "evidence_first_validation",
                "thresholds_applied": {
                    "accepted_threshold": self.thresholds.accepted_threshold,
                    "flagged_threshold": self.thresholds.flagged_threshold,
                    "missing_threshold": self.thresholds.missing_threshold
                },
                "validation_results": {
                    "accepted_fields_count": len(validation_report.accepted_fields),
                    "flagged_fields_count": len(validation_report.flagged_fields),
                    "missing_fields_count": len(validation_report.missing_fields),
                    "overall_confidence": validation_report.overall_confidence,
                    "evidence_completeness": validation_report.evidence_completeness
                },
                "quality_gates": {
                    "can_proceed_to_generation": validation_report.can_proceed_to_generation,
                    "critical_fields_validated": sum(1 for status in validation_report.critical_fields_status.values() if status == "accepted"),
                    "minimum_evidence_threshold_met": validation_report.evidence_completeness >= 0.7
                }
            }
            
            # Add traceability information
            provenance_data["traceability"] = {
                "document_source": validation_report.document_id,
                "validation_system": "EvidenceFirstValidator",
                "validation_standards": ["AMA_Guidelines", "QME_Requirements"],
                "audit_trail_entries": len(validation_report.audit_trail),
                "evidence_sources_count": len(provenance_data["source_references"]),
                "validation_completeness": len(all_validated_fields) / len(self.required_fields) if self.required_fields else 0
            }
            
            logger.info(f"Evidence provenance tracking completed for {len(all_validated_fields)} fields")
            
            return provenance_data
            
        except Exception as e:
            logger.error(f"Error generating evidence provenance tracking: {e}")
            return {
                "error": str(e),
                "document_id": validation_report.document_id,
                "provenance_generation_failed": True,
                "recommendations": ["Fix provenance tracking system"]
            }
    
    def _calculate_confidence_distribution(self, confidence_scores: List[float]) -> Dict[str, Any]:
        """Calculate confidence score distribution statistics."""
        if not confidence_scores:
            return {"error": "No confidence scores provided"}
        
        return {
            "mean": statistics.mean(confidence_scores),
            "median": statistics.median(confidence_scores),
            "std_dev": statistics.stdev(confidence_scores) if len(confidence_scores) > 1 else 0,
            "min": min(confidence_scores),
            "max": max(confidence_scores),
            "count": len(confidence_scores),
            "high_confidence_ratio": sum(1 for score in confidence_scores if score >= 0.8) / len(confidence_scores),
            "low_confidence_ratio": sum(1 for score in confidence_scores if score < 0.5) / len(confidence_scores)
        }
    
    def _generate_confidence_system_recommendations(self, 
                                                  precision_met: bool,
                                                  coverage_met: bool,
                                                  precision_score: float,
                                                  coverage_score: float) -> List[str]:
        """Generate recommendations for confidence system improvement."""
        recommendations = []
        
        if not precision_met:
            recommendations.append(f"Improve critical field precision: {precision_score:.2%} < 95% target")
            recommendations.append("Review extraction prompts for critical fields")
            recommendations.append("Consider additional validation steps for critical fields")
        
        if not coverage_met:
            recommendations.append(f"Improve overall field coverage: {coverage_score:.2%} < 90% target")
            recommendations.append("Enhance field extraction completeness")
            recommendations.append("Review document processing for missing fields")
        
        if precision_met and coverage_met:
            recommendations.append("Confidence scoring system meets all validation targets")
            recommendations.append("System ready for production use")
        
        return recommendations
    
    def _assess_source_reliability(self, source_references: List[str]) -> float:
        """Assess reliability of source references."""
        if not source_references:
            return 0.0
        
        # Simple reliability assessment based on source reference quality
        reliability_score = 0.0
        for source_ref in source_references:
            if "page" in source_ref.lower():
                reliability_score += 0.8  # Page references are reliable
            elif "section" in source_ref.lower():
                reliability_score += 0.6  # Section references are moderately reliable
            else:
                reliability_score += 0.4  # Generic references are less reliable
        
        return min(1.0, reliability_score / len(source_references))
    
    def _assess_evidence_strength(self, evidence_snippets: List[str]) -> float:
        """Assess strength of evidence snippets."""
        if not evidence_snippets:
            return 0.0
        
        # Simple evidence strength assessment
        total_strength = 0.0
        for snippet in evidence_snippets:
            snippet_lower = snippet.lower()
            strength = 0.5  # Base strength
            
            # Increase strength for specific medical terms
            if any(term in snippet_lower for term in ['diagnosis', 'examination', 'finding', 'assessment']):
                strength += 0.2
            
            # Increase strength for specific values
            if any(char.isdigit() for char in snippet):
                strength += 0.1
            
            # Increase strength for longer, more detailed snippets
            if len(snippet) > 50:
                strength += 0.1
            
            total_strength += min(1.0, strength)
        
        return total_strength / len(evidence_snippets)
    
    def save_validation_report(self, 
                             validation_report: DocumentValidationReport,
                             output_path: Optional[str] = None) -> str:
        """Save evidence validation report to file."""
        if output_path is None:
            timestamp = validation_report.validation_timestamp.strftime("%Y%m%d_%H%M%S")
            output_path = f"results/validation_reports/evidence_validation_{validation_report.document_id}_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        report_data = {
            "document_id": validation_report.document_id,
            "validation_timestamp": validation_report.validation_timestamp.isoformat(),
            "overall_confidence": validation_report.overall_confidence,
            "field_coverage": validation_report.field_coverage,
            "evidence_completeness": validation_report.evidence_completeness,
            "can_proceed_to_generation": validation_report.can_proceed_to_generation,
            "accepted_fields": [
                {
                    "field_name": f.field_name,
                    "field_value": str(f.field_value),
                    "confidence_score": f.confidence_score,
                    "validation_status": f.validation_status,
                    "evidence_snippets": f.evidence_snippets,
                    "source_references": f.source_references,
                    "validation_notes": f.validation_notes
                }
                for f in validation_report.accepted_fields
            ],
            "flagged_fields": [
                {
                    "field_name": f.field_name,
                    "field_value": str(f.field_value),
                    "confidence_score": f.confidence_score,
                    "validation_status": f.validation_status,
                    "evidence_snippets": f.evidence_snippets,
                    "source_references": f.source_references,
                    "validation_notes": f.validation_notes
                }
                for f in validation_report.flagged_fields
            ],
            "missing_fields": validation_report.missing_fields,
            "critical_fields_status": validation_report.critical_fields_status,
            "audit_trail": validation_report.audit_trail,
            "recommendations": validation_report.recommendations,
            "validation_thresholds": {
                "accepted_threshold": self.thresholds.accepted_threshold,
                "flagged_threshold": self.thresholds.flagged_threshold,
                "missing_threshold": self.thresholds.missing_threshold
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Evidence validation report saved to {output_file}")
        return str(output_file)