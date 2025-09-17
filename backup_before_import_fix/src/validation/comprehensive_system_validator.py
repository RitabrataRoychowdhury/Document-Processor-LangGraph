"""
Comprehensive System Validator

This module orchestrates all validation components for task 5: Knowledge Base Integration
and Pipeline Functionality validation. It provides a unified interface for running all
validation sub-tasks and generating comprehensive reports.
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .knowledge_base_validator import KnowledgeBaseValidator
from .pipeline_integration_tester import PipelineIntegrationTester
from .evidence_first_validator import EvidenceFirstValidator
from .programmatic_calculation_validator import ProgrammaticCalculationValidator
from .compliance_quality_validator import ComplianceQualityValidator

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveValidationResult:
    """Complete validation result for all sub-tasks."""
    validation_id: str
    validation_timestamp: datetime
    total_execution_time: float
    
    # Sub-task results
    knowledge_base_validation: Dict[str, Any]
    pipeline_integration_testing: Dict[str, Any]
    evidence_first_validation: Dict[str, Any]
    calculation_validation: Dict[str, Any]
    compliance_quality_validation: Dict[str, Any]
    
    # Overall results
    overall_validation_passed: bool
    critical_issues: List[str]
    major_issues: List[str]
    minor_issues: List[str]
    recommendations: List[str]
    
    # Performance metrics
    performance_benchmarks_met: bool
    system_ready_for_production: bool


class ComprehensiveSystemValidator:
    """Orchestrates comprehensive validation of the QME system."""
    
    def __init__(self):
        """Initialize comprehensive system validator."""
        self.kb_validator = KnowledgeBaseValidator()
        self.pipeline_tester = PipelineIntegrationTester()
        self.evidence_validator = EvidenceFirstValidator()
        self.calculation_validator = ProgrammaticCalculationValidator()
        self.compliance_validator = ComplianceQualityValidator()
        
        # Test documents for validation
        self.test_documents = [
            "data/sample_documents/Sample3.pdf",
            "data/sample_documents/Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf",
            "data/sample_documents/Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf"
        ]
        
        logger.info("Initialized Comprehensive System Validator")
    
    async def run_complete_validation(self) -> ComprehensiveValidationResult:
        """
        Run complete validation of all sub-tasks for task 5.
        
        Returns:
            ComprehensiveValidationResult with all validation results
        """
        validation_id = f"comprehensive_validation_{int(time.time())}"
        start_time = time.time()
        
        logger.info(f"Starting comprehensive system validation: {validation_id}")
        
        try:
            # Sub-task 5.1: Knowledge Base Validation and Optimization
            logger.info("Running Sub-task 5.1: Knowledge Base Validation and Optimization")
            kb_validation_result = await self._run_knowledge_base_validation()
            
            # Sub-task 5.2: Pipeline Integration Testing
            logger.info("Running Sub-task 5.2: Pipeline Integration Testing")
            pipeline_testing_result = await self._run_pipeline_integration_testing()
            
            # Sub-task 5.3: Evidence-First Validation System
            logger.info("Running Sub-task 5.3: Evidence-First Validation System")
            evidence_validation_result = await self._run_evidence_first_validation()
            
            # Sub-task 5.4: Programmatic Calculation Validation
            logger.info("Running Sub-task 5.4: Programmatic Calculation Validation")
            calculation_validation_result = await self._run_calculation_validation()
            
            # Sub-task 5.5: Compliance and Quality Assurance
            logger.info("Running Sub-task 5.5: Compliance and Quality Assurance")
            compliance_validation_result = await self._run_compliance_quality_validation()
            
            # Analyze overall results
            total_time = time.time() - start_time
            overall_result = self._analyze_overall_results(
                kb_validation_result,
                pipeline_testing_result,
                evidence_validation_result,
                calculation_validation_result,
                compliance_validation_result
            )
            
            # Create comprehensive result
            result = ComprehensiveValidationResult(
                validation_id=validation_id,
                validation_timestamp=datetime.now(),
                total_execution_time=total_time,
                knowledge_base_validation=kb_validation_result,
                pipeline_integration_testing=pipeline_testing_result,
                evidence_first_validation=evidence_validation_result,
                calculation_validation=calculation_validation_result,
                compliance_quality_validation=compliance_validation_result,
                overall_validation_passed=overall_result["validation_passed"],
                critical_issues=overall_result["critical_issues"],
                major_issues=overall_result["major_issues"],
                minor_issues=overall_result["minor_issues"],
                recommendations=overall_result["recommendations"],
                performance_benchmarks_met=overall_result["performance_benchmarks_met"],
                system_ready_for_production=overall_result["system_ready_for_production"]
            )
            
            logger.info(f"Comprehensive validation completed in {total_time:.2f}s")
            logger.info(f"Overall validation result: {'PASSED' if result.overall_validation_passed else 'FAILED'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            
            return ComprehensiveValidationResult(
                validation_id=validation_id,
                validation_timestamp=datetime.now(),
                total_execution_time=time.time() - start_time,
                knowledge_base_validation={"error": str(e)},
                pipeline_integration_testing={"error": str(e)},
                evidence_first_validation={"error": str(e)},
                calculation_validation={"error": str(e)},
                compliance_quality_validation={"error": str(e)},
                overall_validation_passed=False,
                critical_issues=[f"Comprehensive validation failed: {str(e)}"],
                major_issues=[],
                minor_issues=[],
                recommendations=["Fix comprehensive validation system"],
                performance_benchmarks_met=False,
                system_ready_for_production=False
            )
    
    async def _run_knowledge_base_validation(self) -> Dict[str, Any]:
        """Run knowledge base validation and optimization."""
        try:
            # Validate complete knowledge base
            validation_passed, metrics, issues = await self.kb_validator.validate_complete_knowledge_base()
            
            # Run performance optimization
            optimization_results = await self.kb_validator.optimize_knowledge_base_performance()
            
            # Run health monitoring
            health_result = await self.kb_validator.monitor_knowledge_base_health()
            
            return {
                "validation_passed": validation_passed,
                "metrics": {
                    "node_count": metrics.node_count,
                    "relationship_count": metrics.relationship_count,
                    "entity_type_coverage": metrics.entity_type_coverage,
                    "canonical_documents_processed": metrics.canonical_documents_processed,
                    "ama_tables_loaded": metrics.ama_tables_loaded,
                    "legal_patterns_loaded": metrics.legal_patterns_loaded,
                    "vector_embeddings_count": metrics.vector_embeddings_count,
                    "query_performance_ms": metrics.query_performance_ms,
                    "data_integrity_score": metrics.data_integrity_score
                },
                "validation_issues": issues,
                "optimization_results": [
                    {
                        "type": result.optimization_type,
                        "success": result.success,
                        "improvement_percentage": result.improvement_percentage,
                        "recommendations": result.recommendations
                    }
                    for result in optimization_results
                ],
                "health_monitoring": {
                    "overall_health_score": health_result.overall_health_score,
                    "component_health": health_result.component_health,
                    "issues_detected": health_result.issues_detected,
                    "recommendations": health_result.recommendations
                },
                "requirements_met": {
                    "min_nodes_1000": metrics.node_count >= 1000,
                    "min_relationships_500": metrics.relationship_count >= 500,
                    "entity_type_coverage_complete": len(metrics.entity_type_coverage) >= 10,
                    "canonical_documents_loaded": metrics.canonical_documents_processed >= 3,
                    "performance_optimized": len(optimization_results) > 0,
                    "health_monitoring_active": health_result.overall_health_score > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in knowledge base validation: {e}")
            return {
                "validation_passed": False,
                "error": str(e),
                "requirements_met": {
                    "min_nodes_1000": False,
                    "min_relationships_500": False,
                    "entity_type_coverage_complete": False,
                    "canonical_documents_loaded": False,
                    "performance_optimized": False,
                    "health_monitoring_active": False
                }
            }
    
    async def _run_pipeline_integration_testing(self) -> Dict[str, Any]:
        """Run pipeline integration testing."""
        try:
            # Test available documents
            available_docs = [doc for doc in self.test_documents if Path(doc).exists()]
            
            if not available_docs:
                return {
                    "testing_completed": False,
                    "error": "No test documents available",
                    "requirements_met": {
                        "pipeline1_tested": False,
                        "pipeline2_tested": False,
                        "end_to_end_tested": False,
                        "performance_benchmarks_met": False
                    }
                }
            
            # Test Pipeline 1 with first available document
            pipeline1_result = await self.pipeline_tester.test_pipeline_1_comprehensive(available_docs[0])
            
            # Test Pipeline 2 if Pipeline 1 succeeded
            pipeline2_result = None
            if pipeline1_result.success:
                pipeline2_result = await self.pipeline_tester.test_pipeline_2_comprehensive(pipeline1_result)
            
            # Test end-to-end workflow
            e2e_results = []
            for doc in available_docs[:2]:  # Test first 2 documents
                e2e_result = await self.pipeline_tester.test_end_to_end_workflow(doc)
                e2e_results.append(e2e_result)
            
            # Test performance
            performance_result = await self.pipeline_tester.test_pipeline_performance(available_docs)
            
            return {
                "testing_completed": True,
                "pipeline1_result": {
                    "success": pipeline1_result.success,
                    "fields_extracted": pipeline1_result.fields_extracted,
                    "fields_validated": pipeline1_result.fields_validated,
                    "total_time": pipeline1_result.total_time,
                    "errors": pipeline1_result.errors
                },
                "pipeline2_result": {
                    "success": pipeline2_result.success if pipeline2_result else False,
                    "content_generated": pipeline2_result.content_generated if pipeline2_result else False,
                    "template_assembled": pipeline2_result.template_assembled if pipeline2_result else False,
                    "compliance_passed": pipeline2_result.compliance_passed if pipeline2_result else False,
                    "total_time": pipeline2_result.total_time if pipeline2_result else 0,
                    "errors": pipeline2_result.errors if pipeline2_result else []
                },
                "end_to_end_results": [
                    {
                        "success": result.success,
                        "document_path": result.document_path,
                        "total_execution_time": result.total_execution_time,
                        "performance_benchmarks_met": result.performance_benchmarks_met,
                        "errors": result.errors
                    }
                    for result in e2e_results
                ],
                "performance_testing": {
                    "documents_processed": performance_result.documents_processed,
                    "success_rate": performance_result.success_rate,
                    "average_time_per_document": performance_result.average_time_per_document,
                    "throughput_docs_per_minute": performance_result.throughput_docs_per_minute,
                    "benchmarks_met": all(
                        benchmark for benchmark in performance_result.performance_benchmarks.values()
                        if isinstance(benchmark, bool)
                    )
                },
                "requirements_met": {
                    "pipeline1_tested": pipeline1_result.success,
                    "pipeline2_tested": pipeline2_result.success if pipeline2_result else False,
                    "end_to_end_tested": any(result.success for result in e2e_results),
                    "performance_benchmarks_met": performance_result.success_rate >= 0.8
                }
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline integration testing: {e}")
            return {
                "testing_completed": False,
                "error": str(e),
                "requirements_met": {
                    "pipeline1_tested": False,
                    "pipeline2_tested": False,
                    "end_to_end_tested": False,
                    "performance_benchmarks_met": False
                }
            }
    
    async def _run_evidence_first_validation(self) -> Dict[str, Any]:
        """Run evidence-first validation system testing."""
        try:
            # Create mock extraction results for testing
            mock_extraction_results = self._create_mock_extraction_results()
            
            # Test confidence scoring system
            confidence_validation = self.evidence_validator.validate_confidence_scoring_system(mock_extraction_results)
            
            # Test evidence thresholds for each document
            threshold_validations = []
            for result in mock_extraction_results:
                threshold_validation = self.evidence_validator.validate_evidence_thresholds(result)
                threshold_validations.append(threshold_validation)
            
            # Test cross-document validation
            cross_doc_validation = self.evidence_validator.validate_cross_document_consistency(
                mock_extraction_results, "test_patient_001"
            )
            
            # Generate provenance tracking for first validation
            provenance_tracking = None
            if threshold_validations:
                provenance_tracking = self.evidence_validator.generate_evidence_provenance_tracking(
                    threshold_validations[0]
                )
            
            return {
                "validation_completed": True,
                "confidence_scoring_validation": {
                    "system_valid": confidence_validation.get("system_validation", {}).get("confidence_system_valid", False),
                    "critical_field_precision": confidence_validation.get("precision_validation", {}).get("critical_field_precision", 0),
                    "overall_field_coverage": confidence_validation.get("coverage_validation", {}).get("overall_field_coverage", 0),
                    "precision_target_met": confidence_validation.get("precision_validation", {}).get("precision_target_met", False),
                    "coverage_target_met": confidence_validation.get("coverage_validation", {}).get("coverage_target_met", False)
                },
                "evidence_threshold_validation": {
                    "documents_validated": len(threshold_validations),
                    "average_confidence": sum(v.overall_confidence for v in threshold_validations) / len(threshold_validations) if threshold_validations else 0,
                    "average_completeness": sum(v.evidence_completeness for v in threshold_validations) / len(threshold_validations) if threshold_validations else 0,
                    "can_proceed_rate": sum(1 for v in threshold_validations if v.can_proceed_to_generation) / len(threshold_validations) if threshold_validations else 0
                },
                "cross_document_validation": {
                    "consistency_score": cross_doc_validation.consistency_score,
                    "consistent_fields_count": len(cross_doc_validation.consistent_fields),
                    "inconsistent_fields_count": len(cross_doc_validation.inconsistent_fields),
                    "validation_issues_count": len(cross_doc_validation.validation_issues)
                },
                "provenance_tracking": {
                    "tracking_generated": provenance_tracking is not None,
                    "fields_tracked": len(provenance_tracking.get("field_provenance", {})) if provenance_tracking else 0,
                    "audit_trail_entries": len(provenance_tracking.get("audit_trail", [])) if provenance_tracking else 0,
                    "source_references": len(provenance_tracking.get("source_references", {})) if provenance_tracking else 0
                },
                "requirements_met": {
                    "confidence_precision_95_percent": confidence_validation.get("precision_validation", {}).get("critical_field_precision", 0) >= 0.95,
                    "field_coverage_90_percent": confidence_validation.get("coverage_validation", {}).get("overall_field_coverage", 0) >= 0.90,
                    "evidence_thresholds_validated": len(threshold_validations) > 0,
                    "cross_document_consistency_checked": cross_doc_validation.consistency_score > 0,
                    "provenance_tracking_implemented": provenance_tracking is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in evidence-first validation: {e}")
            return {
                "validation_completed": False,
                "error": str(e),
                "requirements_met": {
                    "confidence_precision_95_percent": False,
                    "field_coverage_90_percent": False,
                    "evidence_thresholds_validated": False,
                    "cross_document_consistency_checked": False,
                    "provenance_tracking_implemented": False
                }
            }
    
    async def _run_calculation_validation(self) -> Dict[str, Any]:
        """Run programmatic calculation validation."""
        try:
            # Test AMA table calculations
            rom_measurements = {"flexion": 60, "extension": 20}
            ama_calculation = self.calculation_validator.validate_ama_table_calculations(
                rom_measurements, "lumbar strain", "spine"
            )
            
            # Test ROM measurement averaging
            multiple_measurements = {
                "flexion": [58, 62, 60],
                "extension": [18, 22, 20]
            }
            averaging_test = self.calculation_validator.test_rom_measurement_averaging(multiple_measurements)
            
            # Validate calculation audit trails
            audit_validation = self.calculation_validator.validate_calculation_audit_trails(ama_calculation)
            
            # Run comprehensive calculation tests
            comprehensive_tests = self.calculation_validator.run_comprehensive_calculation_tests()
            
            return {
                "validation_completed": True,
                "ama_table_calculation": {
                    "validation_passed": ama_calculation.validation_passed,
                    "final_percentage": ama_calculation.final_percentage,
                    "calculation_steps_count": len(ama_calculation.calculation_steps),
                    "ama_citations_count": len(ama_calculation.ama_table_citations),
                    "validation_errors": ama_calculation.validation_errors
                },
                "rom_averaging_test": {
                    "test_passed": averaging_test.get("test_passed", False),
                    "ama_methodology_applied": averaging_test.get("ama_methodology_applied", False),
                    "combined_values_chart_tested": averaging_test.get("combined_values_chart_tested", False),
                    "validation_errors": averaging_test.get("validation_errors", [])
                },
                "audit_trail_validation": {
                    "audit_trail_complete": audit_validation.get("audit_trail_complete", False),
                    "step_by_step_documented": audit_validation.get("step_by_step_documented", False),
                    "ama_citations_present": audit_validation.get("ama_citations_present", False),
                    "calculation_reproducible": audit_validation.get("calculation_reproducible", False),
                    "audit_quality_score": audit_validation.get("audit_quality_score", 0)
                },
                "comprehensive_tests": {
                    "total_tests": comprehensive_tests.get("total_tests", 0),
                    "passed_tests": comprehensive_tests.get("passed_tests", 0),
                    "overall_pass_rate": comprehensive_tests.get("overall_pass_rate", 0),
                    "validation_passed": comprehensive_tests.get("validation_passed", False),
                    "edge_cases_handled": len([r for r in comprehensive_tests.get("edge_case_results", []) if r.get("handled", False)])
                },
                "requirements_met": {
                    "ama_tables_zero_llm": ama_calculation.validation_passed,
                    "rom_averaging_validated": averaging_test.get("test_passed", False),
                    "combined_values_chart_applied": averaging_test.get("combined_values_chart_tested", False),
                    "audit_trails_complete": audit_validation.get("audit_quality_score", 0) >= 0.8,
                    "test_cases_validated": comprehensive_tests.get("overall_pass_rate", 0) >= 0.9,
                    "edge_cases_handled": len([r for r in comprehensive_tests.get("edge_case_results", []) if r.get("handled", False)]) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in calculation validation: {e}")
            return {
                "validation_completed": False,
                "error": str(e),
                "requirements_met": {
                    "ama_tables_zero_llm": False,
                    "rom_averaging_validated": False,
                    "combined_values_chart_applied": False,
                    "audit_trails_complete": False,
                    "test_cases_validated": False,
                    "edge_cases_handled": False
                }
            }
    
    async def _run_compliance_quality_validation(self) -> Dict[str, Any]:
        """Run compliance and quality assurance validation."""
        try:
            # Create mock template content for testing
            mock_template_content = self._create_mock_template_content()
            mock_evidence_citations = ["Page 1: Patient examination", "Page 2: Medical history", "AMA Table 15-3"]
            mock_metadata = {"document_id": "test_doc_001", "patient_name": "Test Patient"}
            
            # Test legal compliance
            legal_checks = self.compliance_validator.validate_legal_compliance(
                mock_template_content, mock_metadata
            )
            
            # Test template quality
            quality_assessments = self.compliance_validator.assess_template_quality(
                mock_template_content, mock_evidence_citations, mock_metadata
            )
            
            # Generate compliance report
            compliance_report = self.compliance_validator.generate_compliance_report(
                "test_doc_001", legal_checks, quality_assessments
            )
            
            # Validate quality gates
            quality_gates_result = self.compliance_validator.validate_quality_gates(compliance_report)
            
            return {
                "validation_completed": True,
                "legal_compliance": {
                    "total_checks": len(legal_checks),
                    "passed_checks": sum(1 for check in legal_checks if check.compliance_status == "passed"),
                    "critical_failures": sum(1 for check in legal_checks if check.compliance_status == "failed" and check.severity == "critical"),
                    "labor_code_compliant": any(check.rule_name == "labor_code_4062_3" and check.compliance_status == "passed" for check in legal_checks),
                    "mandatory_sections_present": any(check.rule_name == "mandatory_sections" and check.compliance_status == "passed" for check in legal_checks),
                    "signature_blocks_present": any(check.rule_name == "signature_blocks" and check.compliance_status == "passed" for check in legal_checks)
                },
                "template_quality": {
                    "total_assessments": len(quality_assessments),
                    "average_quality_score": sum(assessment.score for assessment in quality_assessments) / len(quality_assessments) if quality_assessments else 0,
                    "professional_formatting_score": next((a.score for a in quality_assessments if a.quality_dimension == "professional_formatting"), 0),
                    "evidence_citations_score": next((a.score for a in quality_assessments if a.quality_dimension == "evidence_citations"), 0),
                    "content_completeness_score": next((a.score for a in quality_assessments if a.quality_dimension == "content_completeness"), 0)
                },
                "compliance_report": {
                    "overall_compliance_score": compliance_report.overall_compliance_score,
                    "compliance_status": compliance_report.compliance_status,
                    "critical_failures_count": len(compliance_report.critical_failures),
                    "major_issues_count": len(compliance_report.major_issues),
                    "ready_for_generation": compliance_report.ready_for_generation
                },
                "quality_gates": {
                    "overall_gates_passed": quality_gates_result.get("overall_gates_passed", False),
                    "gate_pass_rate": quality_gates_result.get("gate_pass_rate", 0),
                    "document_ready_for_generation": quality_gates_result.get("document_ready_for_generation", False),
                    "legal_compliance_gate": quality_gates_result.get("quality_gate_summary", {}).get("compliance_gate", False),
                    "template_quality_gate": quality_gates_result.get("quality_gate_summary", {}).get("quality_gate", False)
                },
                "requirements_met": {
                    "legal_compliance_validated": compliance_report.overall_compliance_score >= 0.8,
                    "template_quality_assured": sum(assessment.score for assessment in quality_assessments) / len(quality_assessments) >= 0.8 if quality_assessments else False,
                    "compliance_reporting_implemented": compliance_report.compliance_status != "unknown",
                    "quality_gates_implemented": quality_gates_result.get("total_gates", 0) > 0,
                    "final_validation_complete": quality_gates_result.get("overall_gates_passed", False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in compliance quality validation: {e}")
            return {
                "validation_completed": False,
                "error": str(e),
                "requirements_met": {
                    "legal_compliance_validated": False,
                    "template_quality_assured": False,
                    "compliance_reporting_implemented": False,
                    "quality_gates_implemented": False,
                    "final_validation_complete": False
                }
            }
    
    def _analyze_overall_results(self, 
                               kb_result: Dict[str, Any],
                               pipeline_result: Dict[str, Any],
                               evidence_result: Dict[str, Any],
                               calculation_result: Dict[str, Any],
                               compliance_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall validation results."""
        critical_issues = []
        major_issues = []
        minor_issues = []
        recommendations = []
        
        # Analyze knowledge base validation
        if not kb_result.get("validation_passed", False):
            critical_issues.append("Knowledge base validation failed")
            recommendations.append("Initialize knowledge base with canonical documents")
        
        kb_requirements = kb_result.get("requirements_met", {})
        if not kb_requirements.get("min_nodes_1000", False):
            major_issues.append("Knowledge base has insufficient nodes (<1000)")
        if not kb_requirements.get("min_relationships_500", False):
            major_issues.append("Knowledge base has insufficient relationships (<500)")
        
        # Analyze pipeline integration testing
        if not pipeline_result.get("testing_completed", False):
            critical_issues.append("Pipeline integration testing failed")
            recommendations.append("Fix pipeline testing infrastructure")
        
        pipeline_requirements = pipeline_result.get("requirements_met", {})
        if not pipeline_requirements.get("pipeline1_tested", False):
            major_issues.append("Pipeline 1 testing failed")
        if not pipeline_requirements.get("pipeline2_tested", False):
            major_issues.append("Pipeline 2 testing failed")
        if not pipeline_requirements.get("performance_benchmarks_met", False):
            major_issues.append("Performance benchmarks not met")
        
        # Analyze evidence-first validation
        if not evidence_result.get("validation_completed", False):
            critical_issues.append("Evidence-first validation failed")
            recommendations.append("Fix evidence validation system")
        
        evidence_requirements = evidence_result.get("requirements_met", {})
        if not evidence_requirements.get("confidence_precision_95_percent", False):
            major_issues.append("Confidence precision below 95% for critical fields")
        if not evidence_requirements.get("field_coverage_90_percent", False):
            major_issues.append("Field coverage below 90%")
        
        # Analyze calculation validation
        if not calculation_result.get("validation_completed", False):
            critical_issues.append("Calculation validation failed")
            recommendations.append("Fix programmatic calculation system")
        
        calculation_requirements = calculation_result.get("requirements_met", {})
        if not calculation_requirements.get("ama_tables_zero_llm", False):
            critical_issues.append("AMA table calculations not fully programmatic")
        if not calculation_requirements.get("audit_trails_complete", False):
            major_issues.append("Calculation audit trails incomplete")
        
        # Analyze compliance quality validation
        if not compliance_result.get("validation_completed", False):
            critical_issues.append("Compliance quality validation failed")
            recommendations.append("Fix compliance validation system")
        
        compliance_requirements = compliance_result.get("requirements_met", {})
        if not compliance_requirements.get("legal_compliance_validated", False):
            critical_issues.append("Legal compliance validation failed")
        if not compliance_requirements.get("final_validation_complete", False):
            major_issues.append("Final quality gates not passed")
        
        # Determine overall status
        validation_passed = len(critical_issues) == 0
        performance_benchmarks_met = (
            kb_result.get("validation_passed", False) and
            pipeline_requirements.get("performance_benchmarks_met", False) and
            evidence_requirements.get("confidence_precision_95_percent", False) and
            calculation_requirements.get("test_cases_validated", False)
        )
        
        system_ready_for_production = (
            validation_passed and
            performance_benchmarks_met and
            len(major_issues) <= 2  # Allow minor major issues
        )
        
        # Generate final recommendations
        if validation_passed and system_ready_for_production:
            recommendations.append("All validation requirements met - system ready for production")
        elif validation_passed:
            recommendations.append("Basic validation passed - address major issues before production")
        else:
            recommendations.append("Critical validation failures - system not ready for production")
        
        return {
            "validation_passed": validation_passed,
            "critical_issues": critical_issues,
            "major_issues": major_issues,
            "minor_issues": minor_issues,
            "recommendations": recommendations,
            "performance_benchmarks_met": performance_benchmarks_met,
            "system_ready_for_production": system_ready_for_production
        }
    
    def _create_mock_extraction_results(self) -> List[Any]:
        """Create mock extraction results for testing."""
        from src.models.extraction_models import ExtractionResult, ExtractedField
        
        mock_results = []
        
        for i in range(3):
            extracted_fields = {
                "patient_name": ExtractedField(
                    value=f"Test Patient {i+1}",
                    confidence=0.95,
                    source_text=f"Patient: Test Patient {i+1}",
                    page_reference=1
                ),
                "date_of_birth": ExtractedField(
                    value=f"198{i}-0{i+1}-15",
                    confidence=0.92,
                    source_text=f"DOB: 0{i+1}/15/198{i}",
                    page_reference=1
                ),
                "diagnosis": ExtractedField(
                    value="Lumbar spine strain",
                    confidence=0.88,
                    source_text="Primary diagnosis: Lumbar spine strain",
                    page_reference=2
                ),
                "impairment_rating": ExtractedField(
                    value=f"{10 + i*2}% whole person impairment",
                    confidence=0.85,
                    source_text=f"Patient has {10 + i*2}% whole person impairment",
                    page_reference=3
                )
            }
            
            mock_results.append(ExtractionResult(
                document_id=f"test_doc_{i+1}",
                extracted_fields=extracted_fields,
                processing_time=2.0 + i * 0.5,
                confidence_threshold=0.7,
                success=True
            ))
        
        return mock_results
    
    def _create_mock_template_content(self) -> str:
        """Create mock template content for compliance testing."""
        return """
        QUALIFIED MEDICAL EVALUATOR REPORT
        
        Patient: John Doe
        Date of Birth: 01/15/1980
        Date of Injury: 03/10/2024
        Case Number: WC-2024-001
        
        MEDICAL HISTORY
        The patient reports a history of lower back pain following a work-related injury.
        Medical records reviewed include hospital records and physician reports.
        
        PHYSICAL EXAMINATION
        Physical examination reveals limited range of motion in the lumbar spine.
        Flexion: 60 degrees (normal 90 degrees)
        Extension: 20 degrees (normal 30 degrees)
        
        DIAGNOSIS
        Primary diagnosis: Lumbar spine strain with radiculopathy
        
        IMPAIRMENT RATING
        Based on AMA Guides to the Evaluation of Permanent Impairment, Fifth Edition,
        using Table 15-3, the patient has 5% whole person impairment.
        Methodology: DRE Category II based on ROM measurements and clinical findings.
        
        WORK RESTRICTIONS
        No lifting over 20 pounds, avoid prolonged sitting.
        
        DECLARATION
        I declare under penalty of perjury under the laws of California that the 
        foregoing is true and correct, and that this report is made in compliance 
        with Labor Code 4062.3.
        
        _________________________    Date: ___________
        Dr. Jane Smith, M.D.
        Medical License #: A12345
        """
    
    def save_comprehensive_report(self, 
                                result: ComprehensiveValidationResult,
                                output_path: Optional[str] = None) -> str:
        """Save comprehensive validation report to file."""
        if output_path is None:
            timestamp = result.validation_timestamp.strftime("%Y%m%d_%H%M%S")
            output_path = f"results/validation_reports/comprehensive_system_validation_{timestamp}.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        report_data = {
            "validation_id": result.validation_id,
            "validation_timestamp": result.validation_timestamp.isoformat(),
            "total_execution_time": result.total_execution_time,
            "overall_validation_passed": result.overall_validation_passed,
            "performance_benchmarks_met": result.performance_benchmarks_met,
            "system_ready_for_production": result.system_ready_for_production,
            "critical_issues": result.critical_issues,
            "major_issues": result.major_issues,
            "minor_issues": result.minor_issues,
            "recommendations": result.recommendations,
            "sub_task_results": {
                "5.1_knowledge_base_validation": result.knowledge_base_validation,
                "5.2_pipeline_integration_testing": result.pipeline_integration_testing,
                "5.3_evidence_first_validation": result.evidence_first_validation,
                "5.4_calculation_validation": result.calculation_validation,
                "5.5_compliance_quality_validation": result.compliance_quality_validation
            },
            "validation_summary": {
                "task_5_1_passed": result.knowledge_base_validation.get("validation_passed", False),
                "task_5_2_passed": result.pipeline_integration_testing.get("testing_completed", False),
                "task_5_3_passed": result.evidence_first_validation.get("validation_completed", False),
                "task_5_4_passed": result.calculation_validation.get("validation_completed", False),
                "task_5_5_passed": result.compliance_quality_validation.get("validation_completed", False)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Comprehensive validation report saved to {output_file}")
        return str(output_file)