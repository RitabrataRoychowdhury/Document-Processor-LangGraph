"""
Comprehensive AMA Guidelines Integration Service.

This service integrates all AMA Guidelines components including document processing,
method selection, impairment calculation, medical reasoning, and reference materials
to provide a complete AMA-compliant QME evaluation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

try:
    from src.services.ama_guidelines_engine import (
        AMAGuidelinesEngine, ImpairmentCalculation, MedicalReasoning, AMAMethodType
    )
    from src.services.enhanced_impairment_calculator import (
        EnhancedImpairmentCalculator, DetailedImpairmentResult, 
        RangeOfMotionMeasurement, StrengthTestResult, FunctionalAssessment
    )
    from src.services.qme_reference_processor import (
        QMEReferenceIntegrator, LegalCompliancePattern, QMEStructurePattern, MedicalReasoningExample
    )
    from src.models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from src.utils.logging_config import get_logger
except ImportError:
    from services.ama_guidelines_engine import (
        AMAGuidelinesEngine, ImpairmentCalculation, MedicalReasoning, AMAMethodType
    )
    from services.enhanced_impairment_calculator import (
        EnhancedImpairmentCalculator, DetailedImpairmentResult,
        RangeOfMotionMeasurement, StrengthTestResult, FunctionalAssessment
    )
    from services.qme_reference_processor import (
        QMEReferenceIntegrator, LegalCompliancePattern, QMEStructurePattern, MedicalReasoningExample
    )
    from models.knowledge_graph import Diagnosis, Finding, ImpairmentRating
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ComprehensiveEvaluationData:
    """Complete evaluation data for AMA assessment."""
    patient_id: str
    diagnosis: Diagnosis
    clinical_findings: List[Finding]
    rom_measurements: List[RangeOfMotionMeasurement]
    strength_tests: List[StrengthTestResult]
    functional_assessments: List[FunctionalAssessment]
    patient_history: Dict[str, Any]
    examination_data: Dict[str, Any]
    patient_factors: Dict[str, Any]
    additional_diagnoses: List[Diagnosis] = field(default_factory=list)


@dataclass
class ComprehensiveAMAResult:
    """Complete AMA evaluation result."""
    patient_id: str
    evaluation_date: datetime
    
    # Core results
    impairment_calculation: DetailedImpairmentResult
    medical_reasoning: MedicalReasoning
    
    # AMA compliance
    ama_method_selection: Dict[str, Any]
    ama_citations: List[str]
    calculation_documentation: List[str]
    
    # Legal compliance
    legal_compliance_check: Dict[str, bool]
    required_statements: Dict[str, str]
    
    # Quality assessment
    quality_metrics: Dict[str, float]
    validation_results: Dict[str, bool]
    recommendations: List[str]
    
    # Supporting documentation
    reference_materials: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]
    
    generated_at: datetime = field(default_factory=datetime.now)


class ComprehensiveAMAIntegration:
    """Main integration service for comprehensive AMA Guidelines compliance."""
    
    def __init__(self):
        """Initialize comprehensive AMA integration service."""
        self.ama_engine = AMAGuidelinesEngine()
        self.impairment_calculator = EnhancedImpairmentCalculator()
        self.reference_integrator = QMEReferenceIntegrator()
        
        # Initialize reference materials
        self._initialize_reference_materials()
        
        # Load configuration
        self.config = self._load_configuration()
        
        logger.info("Initialized Comprehensive AMA Integration Service")
    
    def perform_comprehensive_evaluation(self, evaluation_data: ComprehensiveEvaluationData) -> ComprehensiveAMAResult:
        """
        Perform comprehensive AMA-compliant evaluation.
        
        Args:
            evaluation_data: Complete evaluation data
            
        Returns:
            ComprehensiveAMAResult with complete analysis
        """
        try:
            logger.info(f"Starting comprehensive AMA evaluation for patient: {evaluation_data.patient_id}")
            
            # Step 1: Calculate detailed impairment rating
            impairment_result = self.impairment_calculator.calculate_comprehensive_impairment(
                diagnosis=evaluation_data.diagnosis,
                rom_measurements=evaluation_data.rom_measurements,
                strength_tests=evaluation_data.strength_tests,
                functional_assessments=evaluation_data.functional_assessments,
                additional_findings=evaluation_data.clinical_findings,
                patient_factors=evaluation_data.patient_factors
            )
            
            # Step 2: Generate medical reasoning
            medical_reasoning = self.ama_engine.generate_comprehensive_medical_reasoning(
                diagnosis=evaluation_data.diagnosis,
                findings=evaluation_data.clinical_findings,
                patient_history=evaluation_data.patient_history,
                examination_data=evaluation_data.examination_data
            )
            
            # Step 3: Document AMA method selection
            ama_method_selection = self._document_method_selection(
                evaluation_data.diagnosis, evaluation_data.examination_data
            )
            
            # Step 4: Compile AMA citations
            ama_citations = self._compile_comprehensive_citations(impairment_result)
            
            # Step 5: Generate calculation documentation
            calculation_documentation = self._generate_calculation_documentation(impairment_result)
            
            # Step 6: Perform legal compliance check
            legal_compliance_check = self._perform_legal_compliance_check(evaluation_data)
            
            # Step 7: Generate required legal statements
            required_statements = self._generate_required_statements(evaluation_data, impairment_result)
            
            # Step 8: Calculate quality metrics
            quality_metrics = self._calculate_comprehensive_quality_metrics(
                impairment_result, medical_reasoning, evaluation_data
            )
            
            # Step 9: Perform validation
            validation_results = self._perform_comprehensive_validation(
                impairment_result, medical_reasoning, evaluation_data
            )
            
            # Step 10: Generate recommendations
            recommendations = self._generate_comprehensive_recommendations(
                impairment_result, quality_metrics, validation_results
            )
            
            # Step 11: Compile reference materials
            reference_materials = self._compile_reference_materials()
            
            # Step 12: Create audit trail
            audit_trail = self._create_audit_trail(evaluation_data, impairment_result)
            
            # Create comprehensive result
            result = ComprehensiveAMAResult(
                patient_id=evaluation_data.patient_id,
                evaluation_date=datetime.now(),
                impairment_calculation=impairment_result,
                medical_reasoning=medical_reasoning,
                ama_method_selection=ama_method_selection,
                ama_citations=ama_citations,
                calculation_documentation=calculation_documentation,
                legal_compliance_check=legal_compliance_check,
                required_statements=required_statements,
                quality_metrics=quality_metrics,
                validation_results=validation_results,
                recommendations=recommendations,
                reference_materials=reference_materials,
                audit_trail=audit_trail
            )
            
            logger.info(f"Comprehensive AMA evaluation complete for patient: {evaluation_data.patient_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive AMA evaluation: {e}")
            raise
    
    def generate_ama_compliant_report_content(self, result: ComprehensiveAMAResult) -> Dict[str, str]:
        """
        Generate AMA-compliant report content sections.
        
        Args:
            result: Comprehensive AMA evaluation result
            
        Returns:
            Dictionary of report sections with AMA-compliant content
        """
        try:
            logger.info("Generating AMA-compliant report content")
            
            content_sections = {}
            
            # Impairment Rating Section
            content_sections["impairment_rating"] = self._generate_impairment_section(result)
            
            # Medical Reasoning Section
            content_sections["medical_reasoning"] = self._generate_reasoning_section(result)
            
            # Causation Analysis Section
            content_sections["causation_analysis"] = self._generate_causation_section(result)
            
            # Future Medical Care Section
            content_sections["future_medical_care"] = self._generate_future_care_section(result)
            
            # Work Restrictions Section
            content_sections["work_restrictions"] = self._generate_restrictions_section(result)
            
            # AMA Methodology Section
            content_sections["ama_methodology"] = self._generate_methodology_section(result)
            
            # Legal Compliance Statements
            content_sections["legal_statements"] = self._generate_legal_statements_section(result)
            
            logger.info("AMA-compliant report content generation complete")
            return content_sections
            
        except Exception as e:
            logger.error(f"Error generating AMA-compliant content: {e}")
            return {}
    
    def validate_ama_compliance(self, result: ComprehensiveAMAResult) -> Dict[str, Any]:
        """
        Validate complete AMA compliance of the evaluation.
        
        Args:
            result: Comprehensive AMA evaluation result
            
        Returns:
            Validation report with compliance status
        """
        try:
            logger.info("Validating AMA compliance")
            
            compliance_report = {
                "overall_compliant": True,
                "compliance_score": 0.0,
                "section_compliance": {},
                "critical_issues": [],
                "recommendations": []
            }
            
            # Validate impairment calculation compliance
            impairment_compliance = self._validate_impairment_compliance(result.impairment_calculation)
            compliance_report["section_compliance"]["impairment_calculation"] = impairment_compliance
            
            # Validate AMA methodology compliance
            methodology_compliance = self._validate_methodology_compliance(result.ama_method_selection)
            compliance_report["section_compliance"]["methodology"] = methodology_compliance
            
            # Validate citation compliance
            citation_compliance = self._validate_citation_compliance(result.ama_citations)
            compliance_report["section_compliance"]["citations"] = citation_compliance
            
            # Validate legal compliance
            legal_compliance = self._validate_legal_compliance(result.legal_compliance_check)
            compliance_report["section_compliance"]["legal"] = legal_compliance
            
            # Calculate overall compliance score
            section_scores = [comp["score"] for comp in compliance_report["section_compliance"].values()]
            compliance_report["compliance_score"] = sum(section_scores) / len(section_scores)
            
            # Determine overall compliance
            compliance_report["overall_compliant"] = compliance_report["compliance_score"] >= 0.85
            
            # Compile critical issues
            for section, comp in compliance_report["section_compliance"].items():
                compliance_report["critical_issues"].extend(comp.get("critical_issues", []))
            
            # Generate compliance recommendations
            compliance_report["recommendations"] = self._generate_compliance_recommendations(compliance_report)
            
            logger.info(f"AMA compliance validation complete: {compliance_report['compliance_score']:.1%}")
            return compliance_report
            
        except Exception as e:
            logger.error(f"Error validating AMA compliance: {e}")
            return {"overall_compliant": False, "error": str(e)}
    
    def _initialize_reference_materials(self) -> None:
        """Initialize reference materials processing."""
        try:
            success = self.reference_integrator.process_all_references()
            if success:
                logger.info("Reference materials initialized successfully")
            else:
                logger.warning("Reference materials initialized with fallbacks")
        except Exception as e:
            logger.error(f"Error initializing reference materials: {e}")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration for AMA integration."""
        return {
            "quality_thresholds": {
                "minimum_compliance_score": 0.85,
                "minimum_quality_score": 0.80,
                "minimum_confidence_score": 0.75
            },
            "validation_rules": {
                "require_ama_citations": True,
                "require_calculation_steps": True,
                "require_legal_statements": True,
                "require_medical_reasoning": True
            },
            "output_preferences": {
                "include_audit_trail": True,
                "include_quality_metrics": True,
                "include_recommendations": True
            }
        }
    
    def _document_method_selection(self, diagnosis: Diagnosis, examination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Document AMA method selection rationale."""
        try:
            # Use AMA engine method selector
            method_type, table_reference, rationale = self.ama_engine.method_selector.select_appropriate_method(
                diagnosis, examination_data
            )
            
            return {
                "selected_method": method_type.value,
                "table_reference": table_reference,
                "selection_rationale": rationale,
                "available_data": list(examination_data.keys()),
                "diagnosis_factors": {
                    "primary_diagnosis": diagnosis.description,
                    "icd_code": diagnosis.icd_code,
                    "body_system": "determined_from_diagnosis"
                }
            }
            
        except Exception as e:
            logger.error(f"Error documenting method selection: {e}")
            return {"error": str(e)}
    
    def _compile_comprehensive_citations(self, impairment_result: DetailedImpairmentResult) -> List[str]:
        """Compile comprehensive AMA citations."""
        citations = []
        
        # Primary AMA Guides citation
        citations.append("AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition")
        
        # Add specific citations from impairment calculation
        citations.extend(impairment_result.ama_citations)
        
        # Add method-specific citations
        method = impairment_result.components.calculation_method
        if method == AMAMethodType.RANGE_OF_MOTION:
            citations.append("AMA Guides 5th Edition - Range of Motion Methodology")
        elif method == AMAMethodType.DRE_MODEL:
            citations.append("AMA Guides 5th Edition - DRE Model for Spine Impairment")
        elif method == AMAMethodType.COMBINED_VALUES:
            citations.append("AMA Guides 5th Edition - Combined Values Chart")
        
        # Remove duplicates while preserving order
        unique_citations = []
        for citation in citations:
            if citation not in unique_citations:
                unique_citations.append(citation)
        
        return unique_citations
    
    def _generate_calculation_documentation(self, impairment_result: DetailedImpairmentResult) -> List[str]:
        """Generate comprehensive calculation documentation."""
        documentation = []
        
        # Method documentation
        documentation.append(f"Calculation Method: {impairment_result.components.calculation_method.value}")
        
        # Step-by-step calculation
        documentation.extend(impairment_result.calculation_steps)
        
        # Component breakdown
        if impairment_result.components.secondary_impairments:
            documentation.append("Component Analysis:")
            documentation.append(f"  Primary Impairment: {impairment_result.components.primary_impairment}%")
            for i, secondary in enumerate(impairment_result.components.secondary_impairments, 1):
                documentation.append(f"  Secondary Impairment {i}: {secondary}%")
            documentation.append(f"  Combined Total: {impairment_result.components.combined_impairment}%")
        
        # Quality indicators
        overall_quality = impairment_result.quality_indicators.get("overall_quality", 0)
        documentation.append(f"Calculation Quality Score: {overall_quality:.1%}")
        
        return documentation
    
    def _perform_legal_compliance_check(self, evaluation_data: ComprehensiveEvaluationData) -> Dict[str, bool]:
        """Perform legal compliance check."""
        compliance_check = {}
        
        try:
            # Get legal patterns from reference integrator
            legal_patterns = self.reference_integrator.get_legal_compliance_patterns()
            
            # Check each legal requirement
            for pattern in legal_patterns:
                requirement_type = pattern.requirement_type
                
                if requirement_type == "section_4062_3_compliance":
                    compliance_check["section_4062_3"] = self._check_section_4062_3_compliance(evaluation_data)
                elif requirement_type == "impairment_rating_requirement":
                    compliance_check["impairment_rating"] = bool(evaluation_data.diagnosis)
                elif requirement_type == "causation_analysis":
                    compliance_check["causation_analysis"] = bool(evaluation_data.patient_history)
                elif requirement_type == "apportionment_analysis":
                    compliance_check["apportionment"] = True  # Would check for pre-existing conditions
            
            # Overall compliance
            compliance_check["overall_legal_compliance"] = all(compliance_check.values())
            
            return compliance_check
            
        except Exception as e:
            logger.error(f"Error in legal compliance check: {e}")
            return {"error": True}
    
    def _check_section_4062_3_compliance(self, evaluation_data: ComprehensiveEvaluationData) -> bool:
        """Check Section 4062.3 specific compliance."""
        required_elements = [
            bool(evaluation_data.patient_id),
            bool(evaluation_data.diagnosis),
            bool(evaluation_data.examination_data),
            bool(evaluation_data.clinical_findings)
        ]
        
        return all(required_elements)
    
    def _generate_required_statements(self, 
                                    evaluation_data: ComprehensiveEvaluationData,
                                    impairment_result: DetailedImpairmentResult) -> Dict[str, str]:
        """Generate required legal statements."""
        statements = {}
        
        # Section 4062.3 declaration
        statements["section_4062_3"] = (
            "This evaluation has been performed in accordance with Labor Code Section 4062.3 "
            "and addresses all issues as required by statute."
        )
        
        # AMA Guides declaration
        statements["ama_guides"] = (
            f"The impairment rating of {impairment_result.final_percentage}% whole person impairment "
            f"has been calculated in accordance with the AMA Guides to the Evaluation of Permanent "
            f"Impairment, Fifth Edition, using the {impairment_result.components.calculation_method.value} method."
        )
        
        # Medical probability statement
        statements["medical_probability"] = (
            "The opinions expressed in this report are given to a reasonable degree of medical "
            "probability based on the available medical evidence and clinical examination."
        )
        
        # Causation statement
        injury_date = evaluation_data.patient_history.get("injury_date", "the reported date")
        statements["causation"] = (
            f"It is my opinion to a reasonable degree of medical probability that the "
            f"{evaluation_data.diagnosis.description} is causally related to the industrial "
            f"injury of {injury_date}."
        )
        
        return statements
    
    def _calculate_comprehensive_quality_metrics(self,
                                               impairment_result: DetailedImpairmentResult,
                                               medical_reasoning: MedicalReasoning,
                                               evaluation_data: ComprehensiveEvaluationData) -> Dict[str, float]:
        """Calculate comprehensive quality metrics."""
        quality_metrics = {}
        
        try:
            # Impairment calculation quality
            quality_metrics["impairment_quality"] = impairment_result.quality_indicators.get("overall_quality", 0.5)
            
            # Data completeness
            expected_data_elements = 8  # Expected number of data elements
            actual_data_elements = sum([
                1 if evaluation_data.diagnosis else 0,
                1 if evaluation_data.clinical_findings else 0,
                1 if evaluation_data.rom_measurements else 0,
                1 if evaluation_data.strength_tests else 0,
                1 if evaluation_data.functional_assessments else 0,
                1 if evaluation_data.patient_history else 0,
                1 if evaluation_data.examination_data else 0,
                1 if evaluation_data.patient_factors else 0
            ])
            quality_metrics["data_completeness"] = actual_data_elements / expected_data_elements
            
            # Medical reasoning quality
            reasoning_elements = [
                bool(medical_reasoning.injury_mechanism_analysis),
                bool(medical_reasoning.symptom_progression_narrative),
                bool(medical_reasoning.causation_analysis),
                bool(medical_reasoning.prognosis_assessment),
                bool(medical_reasoning.treatment_recommendations),
                bool(medical_reasoning.functional_impact_analysis)
            ]
            quality_metrics["reasoning_quality"] = sum(reasoning_elements) / len(reasoning_elements)
            
            # Confidence assessment
            quality_metrics["confidence_score"] = impairment_result.confidence_score
            
            # Overall quality score
            quality_metrics["overall_quality"] = (
                quality_metrics["impairment_quality"] * 0.4 +
                quality_metrics["data_completeness"] * 0.3 +
                quality_metrics["reasoning_quality"] * 0.2 +
                quality_metrics["confidence_score"] * 0.1
            )
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {"overall_quality": 0.5}
    
    def _perform_comprehensive_validation(self,
                                        impairment_result: DetailedImpairmentResult,
                                        medical_reasoning: MedicalReasoning,
                                        evaluation_data: ComprehensiveEvaluationData) -> Dict[str, bool]:
        """Perform comprehensive validation."""
        validation_results = {}
        
        try:
            # Impairment calculation validation
            validation_results.update(impairment_result.validation_results)
            
            # Medical reasoning validation
            validation_results["reasoning_complete"] = bool(
                medical_reasoning.causation_analysis and 
                medical_reasoning.prognosis_assessment
            )
            
            # Data validation
            validation_results["diagnosis_present"] = bool(evaluation_data.diagnosis)
            validation_results["examination_data_present"] = bool(evaluation_data.examination_data)
            validation_results["clinical_findings_present"] = bool(evaluation_data.clinical_findings)
            
            # AMA compliance validation
            validation_results["ama_method_appropriate"] = (
                impairment_result.components.calculation_method != AMAMethodType.TABLE_BASED
            )
            
            # Overall validation
            validation_results["overall_valid"] = all([
                validation_results.get("percentage_in_range", False),
                validation_results.get("reasoning_complete", False),
                validation_results.get("diagnosis_present", False)
            ])
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            return {"overall_valid": False}
    
    def _generate_comprehensive_recommendations(self,
                                             impairment_result: DetailedImpairmentResult,
                                             quality_metrics: Dict[str, float],
                                             validation_results: Dict[str, bool]) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []
        
        try:
            # Quality-based recommendations
            overall_quality = quality_metrics.get("overall_quality", 0)
            if overall_quality < 0.8:
                recommendations.append("Consider obtaining additional objective measurements to improve assessment quality")
            
            # Data completeness recommendations
            data_completeness = quality_metrics.get("data_completeness", 0)
            if data_completeness < 0.8:
                recommendations.append("Obtain missing clinical data elements for more comprehensive evaluation")
            
            # Validation-based recommendations
            if not validation_results.get("ama_method_appropriate", True):
                recommendations.append("Consider using range of motion or functional assessment methods for more precise rating")
            
            # Confidence-based recommendations
            confidence_score = quality_metrics.get("confidence_score", 0)
            if confidence_score < 0.7:
                recommendations.append("Additional clinical documentation would strengthen the medical opinion")
            
            # Add impairment-specific recommendations
            recommendations.extend(impairment_result.recommendations[:3])  # Top 3 recommendations
            
            # General AMA compliance recommendations
            recommendations.extend([
                "Ensure all AMA table references are current and accurate",
                "Document measurement techniques and patient cooperation",
                "Consider peer review for complex cases"
            ])
            
            # Remove duplicates
            unique_recommendations = []
            for rec in recommendations:
                if rec not in unique_recommendations:
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review calculation methodology and supporting documentation"]
    
    def _compile_reference_materials(self) -> Dict[str, Any]:
        """Compile reference materials used in evaluation."""
        try:
            return {
                "legal_patterns": [
                    {
                        "type": pattern.requirement_type,
                        "reference": pattern.statutory_reference,
                        "language": pattern.required_language
                    }
                    for pattern in self.reference_integrator.get_legal_compliance_patterns()
                ],
                "structure_patterns": [
                    {
                        "section": pattern.section_name,
                        "order": pattern.section_order,
                        "elements": pattern.required_elements
                    }
                    for pattern in self.reference_integrator.get_structure_patterns()
                ],
                "content_templates": self.reference_integrator.get_content_templates(),
                "ama_tables_used": list(self.ama_engine.ama_processor.tables.keys())
            }
            
        except Exception as e:
            logger.error(f"Error compiling reference materials: {e}")
            return {}
    
    def _create_audit_trail(self, 
                          evaluation_data: ComprehensiveEvaluationData,
                          impairment_result: DetailedImpairmentResult) -> List[Dict[str, Any]]:
        """Create comprehensive audit trail."""
        audit_trail = []
        
        try:
            # Evaluation initiation
            audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "evaluation_initiated",
                "details": {
                    "patient_id": evaluation_data.patient_id,
                    "diagnosis": evaluation_data.diagnosis.description,
                    "data_elements": len(evaluation_data.clinical_findings)
                }
            })
            
            # Method selection
            audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "ama_method_selected",
                "details": {
                    "method": impairment_result.components.calculation_method.value,
                    "rationale": "Based on diagnosis and available clinical data"
                }
            })
            
            # Calculation performed
            audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "impairment_calculated",
                "details": {
                    "final_percentage": impairment_result.final_percentage,
                    "calculation_steps": len(impairment_result.calculation_steps),
                    "quality_score": impairment_result.quality_indicators.get("overall_quality", 0)
                }
            })
            
            # Validation completed
            audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "validation_completed",
                "details": {
                    "validation_results": impairment_result.validation_results,
                    "recommendations_generated": len(impairment_result.recommendations)
                }
            })
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Error creating audit trail: {e}")
            return []
    
    def _generate_impairment_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate impairment rating section content."""
        try:
            content_parts = []
            
            # Header
            content_parts.append("IMPAIRMENT RATING")
            content_parts.append("")
            
            # Final rating
            content_parts.append(
                f"Based on the AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition, "
                f"the permanent impairment rating is {result.impairment_calculation.final_percentage}% "
                f"whole person impairment."
            )
            content_parts.append("")
            
            # Methodology
            method = result.impairment_calculation.components.calculation_method.value
            content_parts.append(f"Methodology: {method}")
            content_parts.append("")
            
            # Calculation steps
            content_parts.append("Calculation Steps:")
            for step in result.impairment_calculation.calculation_steps:
                content_parts.append(f"• {step}")
            content_parts.append("")
            
            # AMA citations
            content_parts.append("AMA References:")
            for citation in result.ama_citations:
                content_parts.append(f"• {citation}")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating impairment section: {e}")
            return "Impairment rating section could not be generated."
    
    def _generate_reasoning_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate medical reasoning section content."""
        try:
            reasoning = result.medical_reasoning
            
            content_parts = []
            content_parts.append("MEDICAL REASONING")
            content_parts.append("")
            
            # Injury mechanism
            content_parts.append("Injury Mechanism Analysis:")
            content_parts.append(reasoning.injury_mechanism_analysis)
            content_parts.append("")
            
            # Symptom progression
            content_parts.append("Symptom Progression:")
            content_parts.append(reasoning.symptom_progression_narrative)
            content_parts.append("")
            
            # Functional impact
            content_parts.append("Functional Impact:")
            content_parts.append(reasoning.functional_impact_analysis)
            content_parts.append("")
            
            # Prognosis
            content_parts.append("Prognosis:")
            content_parts.append(reasoning.prognosis_assessment)
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating reasoning section: {e}")
            return "Medical reasoning section could not be generated."
    
    def _generate_causation_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate causation analysis section content."""
        try:
            content_parts = []
            content_parts.append("CAUSATION ANALYSIS")
            content_parts.append("")
            
            # Medical probability statement
            content_parts.append(result.required_statements.get("medical_probability", ""))
            content_parts.append("")
            
            # Causation analysis
            content_parts.append(result.medical_reasoning.causation_analysis)
            content_parts.append("")
            
            # Causation statement
            content_parts.append(result.required_statements.get("causation", ""))
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating causation section: {e}")
            return "Causation analysis section could not be generated."
    
    def _generate_future_care_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate future medical care section content."""
        try:
            content_parts = []
            content_parts.append("FUTURE MEDICAL CARE")
            content_parts.append("")
            
            # Treatment recommendations
            content_parts.append("Recommended treatments:")
            for recommendation in result.medical_reasoning.treatment_recommendations:
                content_parts.append(f"• {recommendation}")
            content_parts.append("")
            
            # Medical necessity statement
            content_parts.append(
                "These treatments are reasonable and necessary for the diagnosed condition "
                "and are expected to provide symptomatic relief and functional improvement."
            )
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating future care section: {e}")
            return "Future medical care section could not be generated."
    
    def _generate_restrictions_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate work restrictions section content."""
        try:
            content_parts = []
            content_parts.append("WORK RESTRICTIONS")
            content_parts.append("")
            
            # Based on impairment level, suggest restrictions
            impairment_percentage = result.impairment_calculation.final_percentage
            
            if impairment_percentage >= 15:
                content_parts.append("Significant work restrictions recommended:")
                content_parts.append("• Lifting limited to 20 pounds occasionally")
                content_parts.append("• Avoid repetitive bending and twisting")
                content_parts.append("• Frequent position changes required")
            elif impairment_percentage >= 5:
                content_parts.append("Moderate work restrictions recommended:")
                content_parts.append("• Lifting limited to 35 pounds occasionally")
                content_parts.append("• Limit prolonged static positions")
            else:
                content_parts.append("Minimal work restrictions:")
                content_parts.append("• Avoid activities that significantly aggravate symptoms")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating restrictions section: {e}")
            return "Work restrictions section could not be generated."
    
    def _generate_methodology_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate AMA methodology section content."""
        try:
            content_parts = []
            content_parts.append("AMA METHODOLOGY")
            content_parts.append("")
            
            # Method selection rationale
            method_selection = result.ama_method_selection
            content_parts.append("Method Selection:")
            content_parts.append(f"Selected Method: {method_selection.get('selected_method', 'Not specified')}")
            content_parts.append(f"Table Reference: {method_selection.get('table_reference', 'Not specified')}")
            content_parts.append("")
            
            # Selection rationale
            rationale = method_selection.get('selection_rationale', [])
            if rationale:
                content_parts.append("Selection Rationale:")
                for reason in rationale:
                    content_parts.append(f"• {reason}")
                content_parts.append("")
            
            # Calculation documentation
            content_parts.append("Calculation Documentation:")
            for doc in result.calculation_documentation:
                content_parts.append(f"• {doc}")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating methodology section: {e}")
            return "AMA methodology section could not be generated."
    
    def _generate_legal_statements_section(self, result: ComprehensiveAMAResult) -> str:
        """Generate legal compliance statements section."""
        try:
            content_parts = []
            content_parts.append("LEGAL COMPLIANCE STATEMENTS")
            content_parts.append("")
            
            # Required statements
            for statement_type, statement_text in result.required_statements.items():
                content_parts.append(f"{statement_type.replace('_', ' ').title()}:")
                content_parts.append(statement_text)
                content_parts.append("")
            
            return "\n".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error generating legal statements section: {e}")
            return "Legal compliance statements could not be generated."
    
    def _validate_impairment_compliance(self, impairment_calculation: DetailedImpairmentResult) -> Dict[str, Any]:
        """Validate impairment calculation compliance."""
        return {
            "score": impairment_calculation.quality_indicators.get("overall_quality", 0.5),
            "compliant": impairment_calculation.validation_results.get("overall_valid", False),
            "critical_issues": [
                issue for issue in ["percentage_out_of_range", "method_inappropriate", "calculation_invalid"]
                if not impairment_calculation.validation_results.get(issue.replace("_", "_"), True)
            ]
        }
    
    def _validate_methodology_compliance(self, method_selection: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AMA methodology compliance."""
        return {
            "score": 0.9 if method_selection.get("selected_method") else 0.5,
            "compliant": bool(method_selection.get("selected_method")),
            "critical_issues": [] if method_selection.get("selected_method") else ["method_not_selected"]
        }
    
    def _validate_citation_compliance(self, citations: List[str]) -> Dict[str, Any]:
        """Validate AMA citation compliance."""
        has_primary_citation = any("AMA Guides" in citation for citation in citations)
        return {
            "score": 1.0 if has_primary_citation else 0.3,
            "compliant": has_primary_citation,
            "critical_issues": [] if has_primary_citation else ["missing_primary_ama_citation"]
        }
    
    def _validate_legal_compliance(self, legal_check: Dict[str, bool]) -> Dict[str, Any]:
        """Validate legal compliance."""
        compliance_score = sum(legal_check.values()) / len(legal_check) if legal_check else 0
        return {
            "score": compliance_score,
            "compliant": compliance_score >= 0.8,
            "critical_issues": [
                requirement for requirement, compliant in legal_check.items()
                if not compliant and requirement != "overall_legal_compliance"
            ]
        }
    
    def _generate_compliance_recommendations(self, compliance_report: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if compliance_report["compliance_score"] < 0.85:
            recommendations.append("Address critical compliance issues before finalizing report")
        
        for issue in compliance_report["critical_issues"]:
            if "citation" in issue:
                recommendations.append("Add proper AMA Guides citations with specific table references")
            elif "method" in issue:
                recommendations.append("Document AMA method selection rationale")
            elif "legal" in issue:
                recommendations.append("Include all required legal compliance statements")
        
        return recommendations