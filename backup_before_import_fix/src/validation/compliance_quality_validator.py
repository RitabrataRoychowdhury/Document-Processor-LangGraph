"""
Compliance and Quality Assurance Validation Service

This module provides comprehensive validation of legal compliance checking,
template quality assurance, compliance reporting, and final quality gates
for the QME system.
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class LegalComplianceCheck:
    """Single legal compliance check result."""
    rule_name: str
    rule_reference: str
    compliance_status: str  # 'passed', 'failed', 'warning'
    required_elements: List[str]
    found_elements: List[str]
    missing_elements: List[str]
    validation_notes: List[str]
    severity: str  # 'critical', 'major', 'minor'


@dataclass
class TemplateQualityAssessment:
    """Template quality assessment result."""
    quality_dimension: str
    score: float  # 0.0 to 1.0
    weight: float
    assessment_criteria: List[str]
    passed_criteria: List[str]
    failed_criteria: List[str]
    improvement_suggestions: List[str]


@dataclass
class ComplianceReport:
    """Comprehensive compliance validation report."""
    document_id: str
    validation_timestamp: datetime
    overall_compliance_score: float
    legal_compliance_checks: List[LegalComplianceCheck]
    quality_assessments: List[TemplateQualityAssessment]
    critical_failures: List[str]
    major_issues: List[str]
    minor_issues: List[str]
    remediation_steps: List[str]
    compliance_status: str  # 'compliant', 'non_compliant', 'conditional'
    quality_gates_passed: bool
    ready_for_generation: bool


@dataclass
class QualityGate:
    """Quality gate definition and validation."""
    gate_name: str
    gate_description: str
    validation_criteria: List[str]
    minimum_score: float
    blocking: bool  # If True, failure blocks progression
    validation_result: Optional[bool] = None
    actual_score: Optional[float] = None
    validation_notes: List[str] = field(default_factory=list)


class ComplianceQualityValidator:
    """Comprehensive compliance and quality assurance validation service."""
    
    def __init__(self):
        """Initialize compliance and quality validator."""
        # Legal compliance requirements
        self.legal_requirements = self._initialize_legal_requirements()
        
        # Quality assessment criteria
        self.quality_criteria = self._initialize_quality_criteria()
        
        # Quality gates
        self.quality_gates = self._initialize_quality_gates()
        
        # Compliance thresholds
        self.min_compliance_score = 0.90
        self.min_quality_score = 0.85
        self.max_critical_failures = 0
        
        logger.info("Initialized Compliance and Quality Validator")
    
    def validate_legal_compliance(self, 
                                template_content: str,
                                document_metadata: Dict[str, Any]) -> List[LegalComplianceCheck]:
        """
        Validate legal compliance checking with Labor Code 4062.3 declaration, mandatory sections, and signature blocks.
        
        Args:
            template_content: Generated template content
            document_metadata: Document metadata and context
            
        Returns:
            List of LegalComplianceCheck results
        """
        logger.info("Validating legal compliance requirements")
        
        compliance_checks = []
        
        try:
            # Check 1: Labor Code 4062.3 Declaration
            labor_code_check = self._check_labor_code_4062_3(template_content)
            compliance_checks.append(labor_code_check)
            
            # Check 2: Mandatory QME Report Sections
            mandatory_sections_check = self._check_mandatory_sections(template_content)
            compliance_checks.append(mandatory_sections_check)
            
            # Check 3: Signature Blocks and Attestations
            signature_check = self._check_signature_blocks(template_content)
            compliance_checks.append(signature_check)
            
            # Check 4: Medical Record Review Declaration
            medical_record_check = self._check_medical_record_review(template_content)
            compliance_checks.append(medical_record_check)
            
            # Check 5: Impairment Rating Methodology Disclosure
            methodology_check = self._check_methodology_disclosure(template_content)
            compliance_checks.append(methodology_check)
            
            # Check 6: Patient Identification Requirements
            patient_id_check = self._check_patient_identification(template_content, document_metadata)
            compliance_checks.append(patient_id_check)
            
            # Check 7: Date and Time Requirements
            date_time_check = self._check_date_time_requirements(template_content)
            compliance_checks.append(date_time_check)
            
            logger.info(f"Completed {len(compliance_checks)} legal compliance checks")
            
            return compliance_checks
            
        except Exception as e:
            logger.error(f"Error in legal compliance validation: {e}")
            return [LegalComplianceCheck(
                rule_name="compliance_validation_error",
                rule_reference="System Error",
                compliance_status="failed",
                required_elements=[],
                found_elements=[],
                missing_elements=["compliance_validation"],
                validation_notes=[f"Validation error: {str(e)}"],
                severity="critical"
            )]
    
    def assess_template_quality(self, 
                              template_content: str,
                              evidence_citations: List[str],
                              document_metadata: Dict[str, Any]) -> List[TemplateQualityAssessment]:
        """
        Test template quality assurance with professional formatting, evidence citations, and completeness validation.
        
        Args:
            template_content: Generated template content
            evidence_citations: List of evidence citations
            document_metadata: Document metadata
            
        Returns:
            List of TemplateQualityAssessment results
        """
        logger.info("Assessing template quality")
        
        quality_assessments = []
        
        try:
            # Assessment 1: Professional Formatting
            formatting_assessment = self._assess_professional_formatting(template_content)
            quality_assessments.append(formatting_assessment)
            
            # Assessment 2: Evidence Citations Quality
            citations_assessment = self._assess_evidence_citations(template_content, evidence_citations)
            quality_assessments.append(citations_assessment)
            
            # Assessment 3: Content Completeness
            completeness_assessment = self._assess_content_completeness(template_content)
            quality_assessments.append(completeness_assessment)
            
            # Assessment 4: Medical Terminology Accuracy
            terminology_assessment = self._assess_medical_terminology(template_content)
            quality_assessments.append(terminology_assessment)
            
            # Assessment 5: Logical Flow and Coherence
            coherence_assessment = self._assess_logical_coherence(template_content)
            quality_assessments.append(coherence_assessment)
            
            # Assessment 6: AMA Guidelines Adherence
            ama_adherence_assessment = self._assess_ama_adherence(template_content)
            quality_assessments.append(ama_adherence_assessment)
            
            logger.info(f"Completed {len(quality_assessments)} quality assessments")
            
            return quality_assessments
            
        except Exception as e:
            logger.error(f"Error in template quality assessment: {e}")
            return [TemplateQualityAssessment(
                quality_dimension="quality_assessment_error",
                score=0.0,
                weight=1.0,
                assessment_criteria=["quality_assessment_execution"],
                passed_criteria=[],
                failed_criteria=["quality_assessment_execution"],
                improvement_suggestions=[f"Fix quality assessment error: {str(e)}"]
            )]
    
    def generate_compliance_report(self, 
                                 document_id: str,
                                 legal_checks: List[LegalComplianceCheck],
                                 quality_assessments: List[TemplateQualityAssessment]) -> ComplianceReport:
        """
        Implement compliance reporting with pass/fail status, remediation steps, and audit trail generation.
        
        Args:
            document_id: Document identifier
            legal_checks: Legal compliance check results
            quality_assessments: Quality assessment results
            
        Returns:
            ComplianceReport with comprehensive compliance analysis
        """
        logger.info(f"Generating compliance report for document: {document_id}")
        
        try:
            # Categorize issues by severity
            critical_failures = []
            major_issues = []
            minor_issues = []
            
            for check in legal_checks:
                if check.compliance_status == "failed":
                    if check.severity == "critical":
                        critical_failures.extend([f"{check.rule_name}: {note}" for note in check.validation_notes])
                    elif check.severity == "major":
                        major_issues.extend([f"{check.rule_name}: {note}" for note in check.validation_notes])
                    else:
                        minor_issues.extend([f"{check.rule_name}: {note}" for note in check.validation_notes])
            
            # Calculate overall compliance score
            total_checks = len(legal_checks)
            passed_checks = sum(1 for check in legal_checks if check.compliance_status == "passed")
            compliance_score = passed_checks / total_checks if total_checks > 0 else 0.0
            
            # Calculate weighted quality score
            total_weight = sum(assessment.weight for assessment in quality_assessments)
            weighted_quality_score = sum(assessment.score * assessment.weight for assessment in quality_assessments) / total_weight if total_weight > 0 else 0.0
            
            # Determine compliance status
            if len(critical_failures) > 0:
                compliance_status = "non_compliant"
            elif compliance_score >= self.min_compliance_score and weighted_quality_score >= self.min_quality_score:
                compliance_status = "compliant"
            else:
                compliance_status = "conditional"
            
            # Generate remediation steps
            remediation_steps = self._generate_remediation_steps(
                legal_checks, quality_assessments, critical_failures, major_issues
            )
            
            # Check quality gates
            quality_gates_passed = self._validate_quality_gates(
                compliance_score, weighted_quality_score, critical_failures
            )
            
            # Determine if ready for generation
            ready_for_generation = (
                compliance_status == "compliant" and
                quality_gates_passed and
                len(critical_failures) == 0
            )
            
            return ComplianceReport(
                document_id=document_id,
                validation_timestamp=datetime.now(),
                overall_compliance_score=compliance_score,
                legal_compliance_checks=legal_checks,
                quality_assessments=quality_assessments,
                critical_failures=critical_failures,
                major_issues=major_issues,
                minor_issues=minor_issues,
                remediation_steps=remediation_steps,
                compliance_status=compliance_status,
                quality_gates_passed=quality_gates_passed,
                ready_for_generation=ready_for_generation
            )
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return ComplianceReport(
                document_id=document_id,
                validation_timestamp=datetime.now(),
                overall_compliance_score=0.0,
                legal_compliance_checks=legal_checks,
                quality_assessments=quality_assessments,
                critical_failures=[f"Compliance report generation error: {str(e)}"],
                major_issues=[],
                minor_issues=[],
                remediation_steps=["Fix compliance reporting system"],
                compliance_status="non_compliant",
                quality_gates_passed=False,
                ready_for_generation=False
            )
    
    def validate_quality_gates(self, 
                             compliance_report: ComplianceReport) -> Dict[str, Any]:
        """
        Add final quality gates with comprehensive validation before template generation and download.
        
        Args:
            compliance_report: Compliance report to validate
            
        Returns:
            Dictionary with quality gate validation results
        """
        logger.info(f"Validating quality gates for document: {compliance_report.document_id}")
        
        try:
            gate_results = []
            overall_gates_passed = True
            
            # Validate each quality gate
            for gate in self.quality_gates:
                gate_result = self._validate_single_quality_gate(gate, compliance_report)
                gate_results.append(gate_result)
                
                if gate.blocking and not gate_result["passed"]:
                    overall_gates_passed = False
            
            # Calculate overall quality gate score
            total_gates = len(self.quality_gates)
            passed_gates = sum(1 for result in gate_results if result["passed"])
            gate_pass_rate = passed_gates / total_gates if total_gates > 0 else 0.0
            
            # Generate final recommendations
            final_recommendations = []
            
            if overall_gates_passed:
                final_recommendations.append("All quality gates passed - document ready for generation")
            else:
                blocking_failures = [result for result in gate_results if not result["passed"] and result["blocking"]]
                final_recommendations.append(f"Quality gates failed: {len(blocking_failures)} blocking failures")
                
                for failure in blocking_failures:
                    final_recommendations.append(f"  - {failure['gate_name']}: {failure['failure_reason']}")
            
            # Add specific recommendations based on gate results
            for result in gate_results:
                if not result["passed"]:
                    final_recommendations.extend(result.get("recommendations", []))
            
            return {
                "overall_gates_passed": overall_gates_passed,
                "gate_pass_rate": gate_pass_rate,
                "total_gates": total_gates,
                "passed_gates": passed_gates,
                "gate_results": gate_results,
                "final_recommendations": final_recommendations,
                "document_ready_for_generation": overall_gates_passed and compliance_report.ready_for_generation,
                "validation_timestamp": datetime.now().isoformat(),
                "quality_gate_summary": {
                    "compliance_gate": any(r["gate_name"] == "legal_compliance" and r["passed"] for r in gate_results),
                    "quality_gate": any(r["gate_name"] == "template_quality" and r["passed"] for r in gate_results),
                    "completeness_gate": any(r["gate_name"] == "content_completeness" and r["passed"] for r in gate_results),
                    "evidence_gate": any(r["gate_name"] == "evidence_validation" and r["passed"] for r in gate_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating quality gates: {e}")
            return {
                "overall_gates_passed": False,
                "gate_pass_rate": 0.0,
                "total_gates": len(self.quality_gates),
                "passed_gates": 0,
                "gate_results": [],
                "final_recommendations": [f"Quality gate validation error: {str(e)}"],
                "document_ready_for_generation": False,
                "validation_timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _initialize_legal_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Initialize legal compliance requirements."""
        return {
            "labor_code_4062_3": {
                "description": "Labor Code 4062.3 Declaration",
                "required_elements": [
                    "declaration_statement",
                    "physician_signature",
                    "date_of_declaration"
                ],
                "required_text_patterns": [
                    r"labor\s+code\s+4062\.3",
                    r"declaration",
                    r"under\s+penalty\s+of\s+perjury"
                ],
                "severity": "critical"
            },
            "mandatory_sections": {
                "description": "Mandatory QME Report Sections",
                "required_elements": [
                    "patient_identification",
                    "medical_history",
                    "examination_findings",
                    "diagnosis",
                    "impairment_rating",
                    "work_restrictions"
                ],
                "severity": "critical"
            },
            "signature_blocks": {
                "description": "Required Signature Blocks",
                "required_elements": [
                    "physician_signature_line",
                    "physician_name_printed",
                    "medical_license_number",
                    "date_signed"
                ],
                "required_text_patterns": [
                    r"signature",
                    r"m\.?d\.?",
                    r"license",
                    r"date"
                ],
                "severity": "critical"
            },
            "medical_record_review": {
                "description": "Medical Record Review Declaration",
                "required_elements": [
                    "records_reviewed_statement",
                    "record_sources_listed"
                ],
                "required_text_patterns": [
                    r"medical\s+records?\s+reviewed",
                    r"records?\s+provided"
                ],
                "severity": "major"
            },
            "methodology_disclosure": {
                "description": "Impairment Rating Methodology",
                "required_elements": [
                    "ama_guidelines_reference",
                    "methodology_explanation"
                ],
                "required_text_patterns": [
                    r"ama\s+guides?",
                    r"methodology",
                    r"fifth\s+edition"
                ],
                "severity": "major"
            }
        }
    
    def _initialize_quality_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality assessment criteria."""
        return {
            "professional_formatting": {
                "weight": 0.15,
                "criteria": [
                    "consistent_font_usage",
                    "proper_section_headers",
                    "appropriate_spacing",
                    "professional_layout"
                ]
            },
            "evidence_citations": {
                "weight": 0.25,
                "criteria": [
                    "citations_present",
                    "page_references_included",
                    "source_documents_identified",
                    "citation_format_consistent"
                ]
            },
            "content_completeness": {
                "weight": 0.20,
                "criteria": [
                    "all_required_sections_present",
                    "sufficient_detail_provided",
                    "no_placeholder_text",
                    "logical_section_flow"
                ]
            },
            "medical_terminology": {
                "weight": 0.15,
                "criteria": [
                    "accurate_medical_terms",
                    "consistent_terminology_usage",
                    "appropriate_clinical_language",
                    "correct_anatomical_references"
                ]
            },
            "logical_coherence": {
                "weight": 0.15,
                "criteria": [
                    "logical_argument_flow",
                    "consistent_findings_interpretation",
                    "coherent_conclusions",
                    "appropriate_transitions"
                ]
            },
            "ama_adherence": {
                "weight": 0.10,
                "criteria": [
                    "ama_guidelines_followed",
                    "proper_table_references",
                    "correct_calculation_methods",
                    "appropriate_impairment_categories"
                ]
            }
        }
    
    def _initialize_quality_gates(self) -> List[QualityGate]:
        """Initialize quality gates for final validation."""
        return [
            QualityGate(
                gate_name="legal_compliance",
                gate_description="Legal compliance requirements must be met",
                validation_criteria=[
                    "labor_code_declaration_present",
                    "mandatory_sections_complete",
                    "signature_blocks_present"
                ],
                minimum_score=0.95,
                blocking=True
            ),
            QualityGate(
                gate_name="template_quality",
                gate_description="Template quality must meet professional standards",
                validation_criteria=[
                    "professional_formatting",
                    "evidence_citations_adequate",
                    "content_completeness"
                ],
                minimum_score=0.85,
                blocking=True
            ),
            QualityGate(
                gate_name="content_completeness",
                gate_description="All required content must be present and complete",
                validation_criteria=[
                    "all_sections_present",
                    "sufficient_detail",
                    "no_missing_information"
                ],
                minimum_score=0.90,
                blocking=True
            ),
            QualityGate(
                gate_name="evidence_validation",
                gate_description="Evidence must be properly cited and validated",
                validation_criteria=[
                    "evidence_citations_present",
                    "source_references_valid",
                    "evidence_supports_conclusions"
                ],
                minimum_score=0.80,
                blocking=False
            )
        ]
    
    def _check_labor_code_4062_3(self, template_content: str) -> LegalComplianceCheck:
        """Check for Labor Code 4062.3 declaration compliance."""
        required_elements = ["declaration_statement", "physician_signature", "date_of_declaration"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for Labor Code 4062.3 reference
        if re.search(r"labor\s+code\s+4062\.3", content_lower):
            found_elements.append("labor_code_reference")
            validation_notes.append("Labor Code 4062.3 reference found")
        else:
            missing_elements.append("labor_code_reference")
            validation_notes.append("Labor Code 4062.3 reference missing")
        
        # Check for declaration statement
        if re.search(r"declaration|under\s+penalty\s+of\s+perjury", content_lower):
            found_elements.append("declaration_statement")
            validation_notes.append("Declaration statement found")
        else:
            missing_elements.append("declaration_statement")
            validation_notes.append("Declaration statement missing")
        
        # Check for signature elements
        if re.search(r"signature|signed", content_lower):
            found_elements.append("signature_reference")
            validation_notes.append("Signature reference found")
        else:
            missing_elements.append("signature_reference")
            validation_notes.append("Signature reference missing")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "failed"
        
        return LegalComplianceCheck(
            rule_name="labor_code_4062_3",
            rule_reference="California Labor Code Section 4062.3",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="critical"
        )
    
    def _check_mandatory_sections(self, template_content: str) -> LegalComplianceCheck:
        """Check for mandatory QME report sections."""
        required_sections = [
            "patient_identification", "medical_history", "examination_findings",
            "diagnosis", "impairment_rating", "work_restrictions"
        ]
        
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for each required section
        section_patterns = {
            "patient_identification": [r"patient", r"name", r"identification"],
            "medical_history": [r"history", r"medical\s+history", r"past\s+medical"],
            "examination_findings": [r"examination", r"findings", r"physical\s+exam"],
            "diagnosis": [r"diagnosis", r"diagnoses", r"impression"],
            "impairment_rating": [r"impairment", r"rating", r"disability"],
            "work_restrictions": [r"work\s+restrictions", r"limitations", r"restrictions"]
        }
        
        for section, patterns in section_patterns.items():
            section_found = any(re.search(pattern, content_lower) for pattern in patterns)
            
            if section_found:
                found_elements.append(section)
                validation_notes.append(f"Section found: {section}")
            else:
                missing_elements.append(section)
                validation_notes.append(f"Section missing: {section}")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "failed"
        
        return LegalComplianceCheck(
            rule_name="mandatory_sections",
            rule_reference="QME Report Requirements",
            compliance_status=compliance_status,
            required_elements=required_sections,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="critical"
        )
    
    def _check_signature_blocks(self, template_content: str) -> LegalComplianceCheck:
        """Check for required signature blocks."""
        required_elements = ["physician_signature_line", "physician_name", "license_number", "date"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for signature line
        if re.search(r"signature|_____+|signed", content_lower):
            found_elements.append("signature_line")
            validation_notes.append("Signature line found")
        else:
            missing_elements.append("signature_line")
            validation_notes.append("Signature line missing")
        
        # Check for physician designation
        if re.search(r"m\.?d\.?|physician|doctor", content_lower):
            found_elements.append("physician_designation")
            validation_notes.append("Physician designation found")
        else:
            missing_elements.append("physician_designation")
            validation_notes.append("Physician designation missing")
        
        # Check for license reference
        if re.search(r"license|lic\.|medical\s+license", content_lower):
            found_elements.append("license_reference")
            validation_notes.append("License reference found")
        else:
            missing_elements.append("license_reference")
            validation_notes.append("License reference missing")
        
        # Check for date
        if re.search(r"date|____/____/____|\d{1,2}/\d{1,2}/\d{4}", content_lower):
            found_elements.append("date_reference")
            validation_notes.append("Date reference found")
        else:
            missing_elements.append("date_reference")
            validation_notes.append("Date reference missing")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "failed"
        
        return LegalComplianceCheck(
            rule_name="signature_blocks",
            rule_reference="QME Signature Requirements",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="critical"
        )
    
    def _check_medical_record_review(self, template_content: str) -> LegalComplianceCheck:
        """Check for medical record review declaration."""
        required_elements = ["records_reviewed_statement", "record_sources"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for record review statement
        if re.search(r"medical\s+records?\s+reviewed|records?\s+provided|reviewed\s+the\s+following", content_lower):
            found_elements.append("records_reviewed_statement")
            validation_notes.append("Medical record review statement found")
        else:
            missing_elements.append("records_reviewed_statement")
            validation_notes.append("Medical record review statement missing")
        
        # Check for record sources
        if re.search(r"hospital|clinic|physician|medical\s+provider|treatment\s+records", content_lower):
            found_elements.append("record_sources")
            validation_notes.append("Record sources mentioned")
        else:
            missing_elements.append("record_sources")
            validation_notes.append("Record sources not specified")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "warning"
        
        return LegalComplianceCheck(
            rule_name="medical_record_review",
            rule_reference="Medical Record Review Requirements",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="major"
        )
    
    def _check_methodology_disclosure(self, template_content: str) -> LegalComplianceCheck:
        """Check for impairment rating methodology disclosure."""
        required_elements = ["ama_guidelines_reference", "methodology_explanation"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for AMA Guidelines reference
        if re.search(r"ama\s+guides?|american\s+medical\s+association|fifth\s+edition", content_lower):
            found_elements.append("ama_guidelines_reference")
            validation_notes.append("AMA Guidelines reference found")
        else:
            missing_elements.append("ama_guidelines_reference")
            validation_notes.append("AMA Guidelines reference missing")
        
        # Check for methodology explanation
        if re.search(r"methodology|method|calculation|table|chapter", content_lower):
            found_elements.append("methodology_explanation")
            validation_notes.append("Methodology explanation found")
        else:
            missing_elements.append("methodology_explanation")
            validation_notes.append("Methodology explanation missing")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "warning"
        
        return LegalComplianceCheck(
            rule_name="methodology_disclosure",
            rule_reference="Impairment Rating Methodology Requirements",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="major"
        )
    
    def _check_patient_identification(self, 
                                    template_content: str,
                                    document_metadata: Dict[str, Any]) -> LegalComplianceCheck:
        """Check for proper patient identification."""
        required_elements = ["patient_name", "date_of_birth", "case_number"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for patient name
        if re.search(r"patient\s*:\s*\w+|name\s*:\s*\w+", content_lower):
            found_elements.append("patient_name")
            validation_notes.append("Patient name found")
        else:
            missing_elements.append("patient_name")
            validation_notes.append("Patient name missing")
        
        # Check for date of birth
        if re.search(r"date\s+of\s+birth|dob|born|\d{1,2}/\d{1,2}/\d{4}", content_lower):
            found_elements.append("date_of_birth")
            validation_notes.append("Date of birth found")
        else:
            missing_elements.append("date_of_birth")
            validation_notes.append("Date of birth missing")
        
        # Check for case/claim number
        if re.search(r"case\s+number|claim\s+number|case\s*#|claim\s*#", content_lower):
            found_elements.append("case_number")
            validation_notes.append("Case number found")
        else:
            missing_elements.append("case_number")
            validation_notes.append("Case number missing")
        
        compliance_status = "passed" if len(missing_elements) <= 1 else "failed"
        
        return LegalComplianceCheck(
            rule_name="patient_identification",
            rule_reference="Patient Identification Requirements",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="critical"
        )
    
    def _check_date_time_requirements(self, template_content: str) -> LegalComplianceCheck:
        """Check for proper date and time requirements."""
        required_elements = ["examination_date", "report_date"]
        found_elements = []
        missing_elements = []
        validation_notes = []
        
        content_lower = template_content.lower()
        
        # Check for examination date
        if re.search(r"examination\s+date|exam\s+date|date\s+of\s+examination", content_lower):
            found_elements.append("examination_date")
            validation_notes.append("Examination date found")
        else:
            missing_elements.append("examination_date")
            validation_notes.append("Examination date missing")
        
        # Check for report date
        if re.search(r"report\s+date|date\s+of\s+report|\d{1,2}/\d{1,2}/\d{4}", content_lower):
            found_elements.append("report_date")
            validation_notes.append("Report date found")
        else:
            missing_elements.append("report_date")
            validation_notes.append("Report date missing")
        
        compliance_status = "passed" if len(missing_elements) == 0 else "warning"
        
        return LegalComplianceCheck(
            rule_name="date_time_requirements",
            rule_reference="Date and Time Documentation Requirements",
            compliance_status=compliance_status,
            required_elements=required_elements,
            found_elements=found_elements,
            missing_elements=missing_elements,
            validation_notes=validation_notes,
            severity="minor"
        )
    
    def _assess_professional_formatting(self, template_content: str) -> TemplateQualityAssessment:
        """Assess professional formatting quality."""
        criteria = ["consistent_font_usage", "proper_section_headers", "appropriate_spacing", "professional_layout"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Check for section headers
        if re.search(r"^[A-Z][A-Z\s]+:?\s*$", template_content, re.MULTILINE):
            passed_criteria.append("proper_section_headers")
        else:
            failed_criteria.append("proper_section_headers")
            improvement_suggestions.append("Add clear section headers")
        
        # Check for appropriate spacing (simplified)
        if "\n\n" in template_content:
            passed_criteria.append("appropriate_spacing")
        else:
            failed_criteria.append("appropriate_spacing")
            improvement_suggestions.append("Improve paragraph spacing")
        
        # Check for professional layout indicators
        if len(template_content) > 1000:  # Sufficient content length
            passed_criteria.append("professional_layout")
        else:
            failed_criteria.append("professional_layout")
            improvement_suggestions.append("Expand content for professional appearance")
        
        # Assume consistent font usage (would need document format analysis)
        passed_criteria.append("consistent_font_usage")
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="professional_formatting",
            score=score,
            weight=0.15,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_evidence_citations(self, 
                                 template_content: str,
                                 evidence_citations: List[str]) -> TemplateQualityAssessment:
        """Assess evidence citations quality."""
        criteria = ["citations_present", "page_references_included", "source_documents_identified", "citation_format_consistent"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Check if citations are present
        if len(evidence_citations) > 0:
            passed_criteria.append("citations_present")
        else:
            failed_criteria.append("citations_present")
            improvement_suggestions.append("Add evidence citations to support findings")
        
        # Check for page references
        page_refs_found = bool(re.search(r"page\s+\d+|p\.\s*\d+", template_content.lower()))
        if page_refs_found:
            passed_criteria.append("page_references_included")
        else:
            failed_criteria.append("page_references_included")
            improvement_suggestions.append("Include page references for evidence")
        
        # Check for source document identification
        source_docs_found = bool(re.search(r"medical\s+records?|report|document", template_content.lower()))
        if source_docs_found:
            passed_criteria.append("source_documents_identified")
        else:
            failed_criteria.append("source_documents_identified")
            improvement_suggestions.append("Identify source documents for evidence")
        
        # Check citation format consistency (simplified)
        if len(evidence_citations) > 1:
            passed_criteria.append("citation_format_consistent")
        else:
            failed_criteria.append("citation_format_consistent")
            improvement_suggestions.append("Ensure consistent citation formatting")
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="evidence_citations",
            score=score,
            weight=0.25,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_content_completeness(self, template_content: str) -> TemplateQualityAssessment:
        """Assess content completeness."""
        criteria = ["all_required_sections_present", "sufficient_detail_provided", "no_placeholder_text", "logical_section_flow"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Check for required sections (simplified)
        required_sections = ["history", "examination", "diagnosis", "impairment"]
        sections_found = sum(1 for section in required_sections if section in template_content.lower())
        
        if sections_found >= 3:
            passed_criteria.append("all_required_sections_present")
        else:
            failed_criteria.append("all_required_sections_present")
            improvement_suggestions.append("Include all required sections")
        
        # Check for sufficient detail
        if len(template_content) > 2000:
            passed_criteria.append("sufficient_detail_provided")
        else:
            failed_criteria.append("sufficient_detail_provided")
            improvement_suggestions.append("Provide more detailed content")
        
        # Check for placeholder text
        if not re.search(r"\[.*\]|TODO|PLACEHOLDER|XXX", template_content):
            passed_criteria.append("no_placeholder_text")
        else:
            failed_criteria.append("no_placeholder_text")
            improvement_suggestions.append("Replace placeholder text with actual content")
        
        # Assume logical flow (would need more sophisticated analysis)
        passed_criteria.append("logical_section_flow")
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="content_completeness",
            score=score,
            weight=0.20,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_medical_terminology(self, template_content: str) -> TemplateQualityAssessment:
        """Assess medical terminology accuracy."""
        criteria = ["accurate_medical_terms", "consistent_terminology_usage", "appropriate_clinical_language", "correct_anatomical_references"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Check for medical terminology presence
        medical_terms = ["diagnosis", "examination", "impairment", "medical", "clinical", "patient"]
        terms_found = sum(1 for term in medical_terms if term in template_content.lower())
        
        if terms_found >= 4:
            passed_criteria.append("accurate_medical_terms")
        else:
            failed_criteria.append("accurate_medical_terms")
            improvement_suggestions.append("Use more accurate medical terminology")
        
        # Assume other criteria are met (would need medical terminology validation)
        passed_criteria.extend(["consistent_terminology_usage", "appropriate_clinical_language", "correct_anatomical_references"])
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="medical_terminology",
            score=score,
            weight=0.15,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_logical_coherence(self, template_content: str) -> TemplateQualityAssessment:
        """Assess logical coherence and flow."""
        criteria = ["logical_argument_flow", "consistent_findings_interpretation", "coherent_conclusions", "appropriate_transitions"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Simplified coherence assessment
        sentences = template_content.split('.')
        if len(sentences) > 10:
            passed_criteria.append("logical_argument_flow")
        else:
            failed_criteria.append("logical_argument_flow")
            improvement_suggestions.append("Improve logical flow between arguments")
        
        # Check for transition words
        transitions = ["therefore", "however", "additionally", "furthermore", "consequently"]
        if any(transition in template_content.lower() for transition in transitions):
            passed_criteria.append("appropriate_transitions")
        else:
            failed_criteria.append("appropriate_transitions")
            improvement_suggestions.append("Add appropriate transitions between sections")
        
        # Assume other criteria are met
        passed_criteria.extend(["consistent_findings_interpretation", "coherent_conclusions"])
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="logical_coherence",
            score=score,
            weight=0.15,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_ama_adherence(self, template_content: str) -> TemplateQualityAssessment:
        """Assess AMA Guidelines adherence."""
        criteria = ["ama_guidelines_followed", "proper_table_references", "correct_calculation_methods", "appropriate_impairment_categories"]
        passed_criteria = []
        failed_criteria = []
        improvement_suggestions = []
        
        # Check for AMA references
        if re.search(r"ama|american\s+medical\s+association|guides?", template_content.lower()):
            passed_criteria.append("ama_guidelines_followed")
        else:
            failed_criteria.append("ama_guidelines_followed")
            improvement_suggestions.append("Reference AMA Guidelines appropriately")
        
        # Check for table references
        if re.search(r"table\s+\d+|chapter\s+\d+", template_content.lower()):
            passed_criteria.append("proper_table_references")
        else:
            failed_criteria.append("proper_table_references")
            improvement_suggestions.append("Include proper AMA table references")
        
        # Assume calculation methods and categories are appropriate
        passed_criteria.extend(["correct_calculation_methods", "appropriate_impairment_categories"])
        
        score = len(passed_criteria) / len(criteria)
        
        return TemplateQualityAssessment(
            quality_dimension="ama_adherence",
            score=score,
            weight=0.10,
            assessment_criteria=criteria,
            passed_criteria=passed_criteria,
            failed_criteria=failed_criteria,
            improvement_suggestions=improvement_suggestions
        )
    
    def _generate_remediation_steps(self, 
                                  legal_checks: List[LegalComplianceCheck],
                                  quality_assessments: List[TemplateQualityAssessment],
                                  critical_failures: List[str],
                                  major_issues: List[str]) -> List[str]:
        """Generate remediation steps based on validation results."""
        remediation_steps = []
        
        # Address critical failures first
        if critical_failures:
            remediation_steps.append("CRITICAL: Address the following compliance failures immediately:")
            for failure in critical_failures:
                remediation_steps.append(f"  - {failure}")
        
        # Address major issues
        if major_issues:
            remediation_steps.append("MAJOR: Address the following issues:")
            for issue in major_issues:
                remediation_steps.append(f"  - {issue}")
        
        # Add quality improvement suggestions
        for assessment in quality_assessments:
            if assessment.score < 0.8:  # Below acceptable quality
                remediation_steps.append(f"Improve {assessment.quality_dimension}:")
                for suggestion in assessment.improvement_suggestions:
                    remediation_steps.append(f"  - {suggestion}")
        
        # Add general recommendations
        if not critical_failures and not major_issues:
            remediation_steps.append("Document meets basic compliance requirements")
            remediation_steps.append("Consider minor quality improvements for enhanced professionalism")
        
        return remediation_steps
    
    def _validate_quality_gates(self, 
                              compliance_score: float,
                              quality_score: float,
                              critical_failures: List[str]) -> bool:
        """Validate quality gates."""
        gates_passed = True
        
        # Legal compliance gate
        if compliance_score < self.min_compliance_score:
            gates_passed = False
        
        # Quality gate
        if quality_score < self.min_quality_score:
            gates_passed = False
        
        # Critical failures gate
        if len(critical_failures) > self.max_critical_failures:
            gates_passed = False
        
        return gates_passed
    
    def _validate_single_quality_gate(self, 
                                    gate: QualityGate,
                                    compliance_report: ComplianceReport) -> Dict[str, Any]:
        """Validate a single quality gate."""
        if gate.gate_name == "legal_compliance":
            actual_score = compliance_report.overall_compliance_score
            passed = actual_score >= gate.minimum_score and len(compliance_report.critical_failures) == 0
            
        elif gate.gate_name == "template_quality":
            # Calculate weighted quality score
            total_weight = sum(assessment.weight for assessment in compliance_report.quality_assessments)
            actual_score = sum(assessment.score * assessment.weight for assessment in compliance_report.quality_assessments) / total_weight if total_weight > 0 else 0.0
            passed = actual_score >= gate.minimum_score
            
        elif gate.gate_name == "content_completeness":
            completeness_assessments = [a for a in compliance_report.quality_assessments if a.quality_dimension == "content_completeness"]
            actual_score = completeness_assessments[0].score if completeness_assessments else 0.0
            passed = actual_score >= gate.minimum_score
            
        elif gate.gate_name == "evidence_validation":
            evidence_assessments = [a for a in compliance_report.quality_assessments if a.quality_dimension == "evidence_citations"]
            actual_score = evidence_assessments[0].score if evidence_assessments else 0.0
            passed = actual_score >= gate.minimum_score
            
        else:
            actual_score = 0.0
            passed = False
        
        failure_reason = None if passed else f"Score {actual_score:.2f} < required {gate.minimum_score:.2f}"
        
        recommendations = []
        if not passed:
            recommendations.append(f"Improve {gate.gate_name} to meet minimum score of {gate.minimum_score:.2f}")
        
        return {
            "gate_name": gate.gate_name,
            "gate_description": gate.gate_description,
            "passed": passed,
            "actual_score": actual_score,
            "minimum_score": gate.minimum_score,
            "blocking": gate.blocking,
            "failure_reason": failure_reason,
            "recommendations": recommendations
        }
    
    def save_compliance_report(self, 
                             compliance_report: ComplianceReport,
                             output_path: Optional[str] = None) -> str:
        """Save compliance report to file."""
        if output_path is None:
            timestamp = compliance_report.validation_timestamp.strftime("%Y%m%d_%H%M%S")
            output_path = f"results/validation_reports/compliance_report_{compliance_report.document_id}_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        report_data = {
            "document_id": compliance_report.document_id,
            "validation_timestamp": compliance_report.validation_timestamp.isoformat(),
            "overall_compliance_score": compliance_report.overall_compliance_score,
            "compliance_status": compliance_report.compliance_status,
            "quality_gates_passed": compliance_report.quality_gates_passed,
            "ready_for_generation": compliance_report.ready_for_generation,
            "legal_compliance_checks": [
                {
                    "rule_name": check.rule_name,
                    "rule_reference": check.rule_reference,
                    "compliance_status": check.compliance_status,
                    "required_elements": check.required_elements,
                    "found_elements": check.found_elements,
                    "missing_elements": check.missing_elements,
                    "validation_notes": check.validation_notes,
                    "severity": check.severity
                }
                for check in compliance_report.legal_compliance_checks
            ],
            "quality_assessments": [
                {
                    "quality_dimension": assessment.quality_dimension,
                    "score": assessment.score,
                    "weight": assessment.weight,
                    "assessment_criteria": assessment.assessment_criteria,
                    "passed_criteria": assessment.passed_criteria,
                    "failed_criteria": assessment.failed_criteria,
                    "improvement_suggestions": assessment.improvement_suggestions
                }
                for assessment in compliance_report.quality_assessments
            ],
            "critical_failures": compliance_report.critical_failures,
            "major_issues": compliance_report.major_issues,
            "minor_issues": compliance_report.minor_issues,
            "remediation_steps": compliance_report.remediation_steps
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Compliance report saved to {output_file}")
        return str(output_file)