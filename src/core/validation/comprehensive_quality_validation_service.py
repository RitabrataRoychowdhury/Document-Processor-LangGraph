"""
Comprehensive Quality Validation Service for QME System Refactor
Provides scoring, compliance checking, and detailed quality assessments
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml

from src.models.extraction_models import ExtractionResult, QualityAssessment
from src.config.openrouter_config_manager import OpenRouterConfigManager


@dataclass
class QualityMetric:
    """Individual quality metric with score and details"""
    name: str
    score: float  # 0.0 to 1.0
    weight: float
    details: str
    issues: List[str]
    suggestions: List[str]


@dataclass
class ComplianceCheck:
    """Compliance validation result"""
    rule_name: str
    passed: bool
    severity: str  # 'critical', 'warning', 'info'
    message: str
    reference: Optional[str] = None


@dataclass
class QualityValidationResult:
    """Comprehensive quality validation result"""
    document_id: str
    overall_score: float
    weighted_score: float
    metrics: List[QualityMetric]
    compliance_checks: List[ComplianceCheck]
    processing_time: float
    timestamp: datetime
    validation_version: str
    recommendations: List[str]


class ComprehensiveQualityValidationService:
    """
    Comprehensive quality validation service with scoring and compliance checking
    """
    
    def __init__(self, config_path: str = "config/validation/quality_validation_config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.validation_config = self._load_validation_config()
        self.openrouter_config = OpenRouterConfigManager()
        
    def _load_validation_config(self) -> Dict[str, Any]:
        """Load quality validation configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading validation config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default validation configuration"""
        return {
            "quality_metrics": {
                "completeness": {"weight": 0.25, "threshold": 0.8},
                "accuracy": {"weight": 0.30, "threshold": 0.85},
                "consistency": {"weight": 0.20, "threshold": 0.75},
                "compliance": {"weight": 0.25, "threshold": 0.90}
            },
            "compliance_rules": {
                "ama_guidelines": {"severity": "critical", "enabled": True},
                "qme_standards": {"severity": "critical", "enabled": True},
                "formatting_rules": {"severity": "warning", "enabled": True},
                "data_completeness": {"severity": "critical", "enabled": True}
            },
            "thresholds": {
                "minimum_overall_score": 0.75,
                "critical_compliance_required": True,
                "warning_threshold": 0.65
            }
        }
    
    def validate_extraction_quality(self, extraction_result: ExtractionResult) -> QualityValidationResult:
        """
        Validate quality of extraction results with comprehensive scoring
        """
        start_time = datetime.now()
        
        # Calculate quality metrics
        metrics = []
        
        # Completeness metric
        completeness_metric = self._calculate_completeness_metric(extraction_result)
        metrics.append(completeness_metric)
        
        # Accuracy metric
        accuracy_metric = self._calculate_accuracy_metric(extraction_result)
        metrics.append(accuracy_metric)
        
        # Consistency metric
        consistency_metric = self._calculate_consistency_metric(extraction_result)
        metrics.append(consistency_metric)
        
        # Compliance checks
        compliance_checks = self._perform_compliance_checks(extraction_result)
        compliance_metric = self._calculate_compliance_metric(compliance_checks)
        metrics.append(compliance_metric)
        
        # Calculate overall scores
        overall_score = sum(m.score for m in metrics) / len(metrics)
        weighted_score = sum(m.score * m.weight for m in metrics) / sum(m.weight for m in metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, compliance_checks)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QualityValidationResult(
            document_id=extraction_result.document_id,
            overall_score=overall_score,
            weighted_score=weighted_score,
            metrics=metrics,
            compliance_checks=compliance_checks,
            processing_time=processing_time,
            timestamp=datetime.now(),
            validation_version="1.0.0",
            recommendations=recommendations
        )
    
    def _calculate_completeness_metric(self, extraction_result: ExtractionResult) -> QualityMetric:
        """Calculate completeness metric based on required fields"""
        required_fields = [
            "patient_name", "date_of_birth", "date_of_injury", 
            "medical_history", "examination_findings", "diagnosis",
            "impairment_rating", "work_restrictions"
        ]
        
        completed_fields = 0
        missing_fields = []
        issues = []
        
        for field in required_fields:
            if field in extraction_result.extracted_fields:
                field_data = extraction_result.extracted_fields[field]
                if field_data.value and field_data.confidence > 0.5:
                    completed_fields += 1
                else:
                    missing_fields.append(field)
                    if field_data.confidence <= 0.5:
                        issues.append(f"Low confidence for {field}: {field_data.confidence:.2f}")
            else:
                missing_fields.append(field)
                issues.append(f"Missing required field: {field}")
        
        score = completed_fields / len(required_fields)
        weight = self.validation_config["quality_metrics"]["completeness"]["weight"]
        
        suggestions = []
        if missing_fields:
            suggestions.append(f"Complete missing fields: {', '.join(missing_fields)}")
        if score < 0.8:
            suggestions.append("Review extraction prompts for better field coverage")
        
        return QualityMetric(
            name="completeness",
            score=score,
            weight=weight,
            details=f"Completed {completed_fields}/{len(required_fields)} required fields",
            issues=issues,
            suggestions=suggestions
        )
    
    def _calculate_accuracy_metric(self, extraction_result: ExtractionResult) -> QualityMetric:
        """Calculate accuracy metric based on confidence scores and validation"""
        total_confidence = 0
        field_count = 0
        low_confidence_fields = []
        issues = []
        
        for field_name, field_data in extraction_result.extracted_fields.items():
            if field_data.value:
                total_confidence += field_data.confidence
                field_count += 1
                
                if field_data.confidence < 0.7:
                    low_confidence_fields.append(field_name)
                    issues.append(f"Low confidence for {field_name}: {field_data.confidence:.2f}")
        
        score = total_confidence / field_count if field_count > 0 else 0
        weight = self.validation_config["quality_metrics"]["accuracy"]["weight"]
        
        suggestions = []
        if low_confidence_fields:
            suggestions.append(f"Review and validate low-confidence fields: {', '.join(low_confidence_fields)}")
        if score < 0.85:
            suggestions.append("Consider using alternative extraction prompts or manual review")
        
        return QualityMetric(
            name="accuracy",
            score=score,
            weight=weight,
            details=f"Average confidence: {score:.2f}, {len(low_confidence_fields)} low-confidence fields",
            issues=issues,
            suggestions=suggestions
        )
    
    def _calculate_consistency_metric(self, extraction_result: ExtractionResult) -> QualityMetric:
        """Calculate consistency metric by checking for contradictions"""
        consistency_checks = []
        issues = []
        
        # Check date consistency
        if "date_of_birth" in extraction_result.extracted_fields and "date_of_injury" in extraction_result.extracted_fields:
            dob_field = extraction_result.extracted_fields["date_of_birth"]
            doi_field = extraction_result.extracted_fields["date_of_injury"]
            
            # Check if dates are valid and injury date is after birth date
            try:
                from datetime import datetime
                if dob_field.value and doi_field.value:
                    # Simple date format validation
                    dob_str = str(dob_field.value).strip()
                    doi_str = str(doi_field.value).strip()
                    
                    # Check if dates look reasonable (basic format check)
                    date_consistent = len(dob_str) >= 8 and len(doi_str) >= 8
                    consistency_checks.append(date_consistent)
                    
                    if not date_consistent:
                        issues.append("Date format inconsistency detected")
                else:
                    consistency_checks.append(False)
                    issues.append("Missing date values for consistency check")
            except Exception:
                consistency_checks.append(False)
                issues.append("Date validation error")
        
        # Check medical consistency
        if "diagnosis" in extraction_result.extracted_fields and "examination_findings" in extraction_result.extracted_fields:
            diagnosis_field = extraction_result.extracted_fields["diagnosis"]
            findings_field = extraction_result.extracted_fields["examination_findings"]
            
            # Check if diagnosis and findings are both present and substantial
            if diagnosis_field.value and findings_field.value:
                diagnosis_text = str(diagnosis_field.value).lower()
                findings_text = str(findings_field.value).lower()
                
                # Basic consistency check - both should have medical content
                has_medical_content = (
                    len(diagnosis_text) > 10 and len(findings_text) > 20 and
                    any(term in diagnosis_text for term in ['pain', 'injury', 'condition', 'syndrome', 'disorder']) and
                    any(term in findings_text for term in ['examination', 'finding', 'observed', 'noted', 'present'])
                )
                consistency_checks.append(has_medical_content)
                
                if not has_medical_content:
                    issues.append("Medical diagnosis and findings lack sufficient detail or consistency")
            else:
                consistency_checks.append(False)
                issues.append("Missing diagnosis or examination findings for consistency check")
        
        # Check impairment rating consistency
        if "impairment_rating" in extraction_result.extracted_fields and "work_restrictions" in extraction_result.extracted_fields:
            rating_field = extraction_result.extracted_fields["impairment_rating"]
            restrictions_field = extraction_result.extracted_fields["work_restrictions"]
            
            # Check if impairment rating and work restrictions are consistent
            if rating_field.value and restrictions_field.value:
                rating_text = str(rating_field.value).lower()
                restrictions_text = str(restrictions_field.value).lower()
                
                # Extract percentage if present
                import re
                rating_match = re.search(r'(\d+)%', rating_text)
                
                if rating_match:
                    rating_percent = int(rating_match.group(1))
                    
                    # High impairment should have more restrictions
                    has_restrictions = any(term in restrictions_text for term in 
                                         ['no', 'avoid', 'limit', 'restrict', 'unable', 'cannot'])
                    
                    # Basic consistency: higher impairment should correlate with restrictions
                    if rating_percent > 15:  # Significant impairment
                        consistency_checks.append(has_restrictions)
                        if not has_restrictions:
                            issues.append("High impairment rating without corresponding work restrictions")
                    else:
                        consistency_checks.append(True)  # Lower ratings may not need restrictions
                else:
                    consistency_checks.append(True)  # No percentage found, assume consistent
            else:
                consistency_checks.append(False)
                issues.append("Missing impairment rating or work restrictions for consistency check")
        
        score = sum(consistency_checks) / len(consistency_checks) if consistency_checks else 1.0
        weight = self.validation_config["quality_metrics"]["consistency"]["weight"]
        
        suggestions = []
        if score < 0.75:
            suggestions.append("Review extracted data for internal consistency")
            suggestions.append("Cross-validate related fields for logical coherence")
        
        return QualityMetric(
            name="consistency",
            score=score,
            weight=weight,
            details=f"Passed {sum(consistency_checks)}/{len(consistency_checks)} consistency checks",
            issues=issues,
            suggestions=suggestions
        )
    
    def _perform_compliance_checks(self, extraction_result: ExtractionResult) -> List[ComplianceCheck]:
        """Perform compliance checks against QME and AMA standards"""
        compliance_checks = []
        
        # AMA Guidelines compliance
        if self.validation_config["compliance_rules"]["ama_guidelines"]["enabled"]:
            ama_check = self._check_ama_compliance(extraction_result)
            compliance_checks.append(ama_check)
        
        # QME Standards compliance
        if self.validation_config["compliance_rules"]["qme_standards"]["enabled"]:
            qme_check = self._check_qme_compliance(extraction_result)
            compliance_checks.append(qme_check)
        
        # Data completeness compliance
        if self.validation_config["compliance_rules"]["data_completeness"]["enabled"]:
            completeness_check = self._check_data_completeness_compliance(extraction_result)
            compliance_checks.append(completeness_check)
        
        return compliance_checks
    
    def _check_ama_compliance(self, extraction_result: ExtractionResult) -> ComplianceCheck:
        """Check compliance with AMA Guidelines"""
        compliance_issues = []
        
        # Required AMA fields with quality thresholds
        ama_requirements = {
            "impairment_rating": {"min_confidence": 0.7, "required_content": ["percent", "%", "impairment"]},
            "examination_findings": {"min_confidence": 0.6, "required_content": ["examination", "finding", "observed"]},
            "diagnosis": {"min_confidence": 0.7, "required_content": ["diagnosis", "condition"]},
            "medical_history": {"min_confidence": 0.5, "required_content": ["history", "complaint"]},
            "date_of_injury": {"min_confidence": 0.8, "required_content": ["date", "injury"]}
        }
        
        for field_name, requirements in ama_requirements.items():
            if field_name not in extraction_result.extracted_fields:
                compliance_issues.append(f"Missing required AMA field: {field_name}")
            else:
                field = extraction_result.extracted_fields[field_name]
                
                # Check confidence threshold
                if field.confidence < requirements["min_confidence"]:
                    compliance_issues.append(f"Low confidence for {field_name}: {field.confidence:.2f}")
                
                # Check content requirements
                if field.value:
                    field_text = str(field.value).lower()
                    has_required_content = any(content in field_text for content in requirements["required_content"])
                    if not has_required_content:
                        compliance_issues.append(f"Field {field_name} lacks required AMA content indicators")
        
        # Check for AMA table references in impairment rating
        if "impairment_rating" in extraction_result.extracted_fields:
            rating_field = extraction_result.extracted_fields["impairment_rating"]
            if rating_field.value:
                rating_text = str(rating_field.value).lower()
                has_table_ref = any(ref in rating_text for ref in ["table", "chapter", "section", "ama"])
                if not has_table_ref:
                    compliance_issues.append("Impairment rating lacks AMA table/chapter reference")
        
        passed = len(compliance_issues) == 0
        message = "AMA Guidelines compliance check passed" if passed else f"AMA compliance issues: {'; '.join(compliance_issues)}"
        
        return ComplianceCheck(
            rule_name="ama_guidelines",
            passed=passed,
            severity="critical",
            message=message,
            reference="AMA Guides 5th Edition"
        )
    
    def _check_qme_compliance(self, extraction_result: ExtractionResult) -> ComplianceCheck:
        """Check compliance with QME Standards"""
        compliance_issues = []
        
        # Required QME fields with specific requirements
        qme_requirements = {
            "patient_name": {"min_confidence": 0.9, "min_length": 3},
            "date_of_injury": {"min_confidence": 0.8, "min_length": 8},
            "date_of_birth": {"min_confidence": 0.8, "min_length": 8},
            "work_restrictions": {"min_confidence": 0.6, "min_length": 10},
            "examination_findings": {"min_confidence": 0.6, "min_length": 50},
            "diagnosis": {"min_confidence": 0.7, "min_length": 10},
            "impairment_rating": {"min_confidence": 0.7, "min_length": 5}
        }
        
        for field_name, requirements in qme_requirements.items():
            if field_name not in extraction_result.extracted_fields:
                compliance_issues.append(f"Missing required QME field: {field_name}")
            else:
                field = extraction_result.extracted_fields[field_name]
                
                # Check confidence threshold
                if field.confidence < requirements["min_confidence"]:
                    compliance_issues.append(f"QME field {field_name} confidence too low: {field.confidence:.2f}")
                
                # Check minimum content length
                if field.value and len(str(field.value)) < requirements["min_length"]:
                    compliance_issues.append(f"QME field {field_name} content too brief")
        
        # Check for QME-specific requirements
        if "impairment_rating" in extraction_result.extracted_fields:
            rating_field = extraction_result.extracted_fields["impairment_rating"]
            if rating_field.value:
                rating_text = str(rating_field.value)
                # QME reports should have percentage-based ratings
                import re
                if not re.search(r'\d+%', rating_text):
                    compliance_issues.append("QME impairment rating should include percentage")
        
        # Check for proper medical evaluation structure
        required_sections = ["examination_findings", "diagnosis", "impairment_rating"]
        missing_sections = [section for section in required_sections 
                          if section not in extraction_result.extracted_fields or 
                          not extraction_result.extracted_fields[section].value]
        
        if missing_sections:
            compliance_issues.append(f"Missing QME evaluation sections: {', '.join(missing_sections)}")
        
        passed = len(compliance_issues) == 0
        message = "QME Standards compliance check passed" if passed else f"QME compliance issues: {'; '.join(compliance_issues)}"
        
        return ComplianceCheck(
            rule_name="qme_standards",
            passed=passed,
            severity="critical",
            message=message,
            reference="California QME Regulations"
        )
    
    def _check_data_completeness_compliance(self, extraction_result: ExtractionResult) -> ComplianceCheck:
        """Check data completeness compliance"""
        total_fields = len(extraction_result.extracted_fields)
        complete_fields = sum(1 for field in extraction_result.extracted_fields.values() 
                            if field.value and field.confidence > 0.5)
        
        completeness_ratio = complete_fields / total_fields if total_fields > 0 else 0
        passed = completeness_ratio >= 0.8
        
        message = f"Data completeness: {completeness_ratio:.1%} ({complete_fields}/{total_fields} fields)"
        
        return ComplianceCheck(
            rule_name="data_completeness",
            passed=passed,
            severity="critical",
            message=message
        )
    
    def _calculate_compliance_metric(self, compliance_checks: List[ComplianceCheck]) -> QualityMetric:
        """Calculate compliance metric from compliance checks"""
        if not compliance_checks:
            return QualityMetric("compliance", 1.0, 0.25, "No compliance checks performed", [], [])
        
        passed_checks = sum(1 for check in compliance_checks if check.passed)
        critical_failed = sum(1 for check in compliance_checks 
                            if not check.passed and check.severity == "critical")
        
        score = passed_checks / len(compliance_checks)
        weight = self.validation_config["quality_metrics"]["compliance"]["weight"]
        
        issues = [check.message for check in compliance_checks if not check.passed]
        suggestions = []
        
        if critical_failed > 0:
            suggestions.append("Address critical compliance failures immediately")
        if score < 0.9:
            suggestions.append("Review compliance requirements and update extraction process")
        
        return QualityMetric(
            name="compliance",
            score=score,
            weight=weight,
            details=f"Passed {passed_checks}/{len(compliance_checks)} compliance checks",
            issues=issues,
            suggestions=suggestions
        )
    
    def _generate_recommendations(self, metrics: List[QualityMetric], 
                                compliance_checks: List[ComplianceCheck]) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Collect suggestions from metrics
        for metric in metrics:
            recommendations.extend(metric.suggestions)
        
        # Add compliance-based recommendations
        critical_failures = [check for check in compliance_checks 
                           if not check.passed and check.severity == "critical"]
        
        if critical_failures:
            recommendations.append("CRITICAL: Address compliance failures before proceeding")
        
        # Add overall recommendations based on scores
        overall_score = sum(m.score for m in metrics) / len(metrics)
        if overall_score < 0.7:
            recommendations.append("Overall quality is below acceptable threshold - comprehensive review needed")
        elif overall_score < 0.85:
            recommendations.append("Quality improvements recommended for production use")
        
        return list(set(recommendations))  # Remove duplicates
    
    def save_validation_report(self, result: QualityValidationResult, 
                             output_path: Optional[str] = None) -> str:
        """Save validation report to file"""
        if output_path is None:
            timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
            output_path = f"results/validation_reports/quality_validation_{result.document_id}_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        report_data = {
            "document_id": result.document_id,
            "overall_score": result.overall_score,
            "weighted_score": result.weighted_score,
            "metrics": [asdict(metric) for metric in result.metrics],
            "compliance_checks": [asdict(check) for check in result.compliance_checks],
            "processing_time": result.processing_time,
            "timestamp": result.timestamp.isoformat(),
            "validation_version": result.validation_version,
            "recommendations": result.recommendations
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Quality validation report saved to {output_file}")
        return str(output_file)
    
    def validate_system_performance(self, test_results: List[QualityValidationResult]) -> Dict[str, Any]:
        """Validate overall system performance from multiple test results"""
        if not test_results:
            return {"error": "No test results provided"}
        
        # Calculate aggregate metrics
        avg_overall_score = sum(r.overall_score for r in test_results) / len(test_results)
        avg_weighted_score = sum(r.weighted_score for r in test_results) / len(test_results)
        avg_processing_time = sum(r.processing_time for r in test_results) / len(test_results)
        
        # Count compliance failures
        total_compliance_checks = sum(len(r.compliance_checks) for r in test_results)
        failed_compliance_checks = sum(
            sum(1 for check in r.compliance_checks if not check.passed)
            for r in test_results
        )
        
        compliance_rate = 1 - (failed_compliance_checks / total_compliance_checks) if total_compliance_checks > 0 else 1
        
        # Performance assessment
        performance_assessment = {
            "total_documents": len(test_results),
            "average_overall_score": avg_overall_score,
            "average_weighted_score": avg_weighted_score,
            "average_processing_time": avg_processing_time,
            "compliance_rate": compliance_rate,
            "documents_above_threshold": sum(1 for r in test_results if r.weighted_score >= 0.75),
            "documents_needing_review": sum(1 for r in test_results if r.weighted_score < 0.65),
            "critical_compliance_failures": sum(
                sum(1 for check in r.compliance_checks if not check.passed and check.severity == "critical")
                for r in test_results
            )
        }
        
        return performance_assessment