"""
End-to-End Testing Suite for QME System Refactor
Compares refactored system output with existing templates
"""

import pytest
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import tempfile
import shutil

from src.core.validation.comprehensive_quality_validation_service import (
    ComprehensiveQualityValidationService,
    QualityValidationResult
)
from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
from tests.test_professional_template_assembly_engine import ProfessionalTemplateAssemblyEngine
from src.infrastructure.knowledge.enhanced_rag_pipeline import EnhancedRAGPipeline
from src.models.extraction_models import ExtractionResult


class SystemComparisonTestSuite:
    """
    Comprehensive test suite comparing refactored system with existing templates
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_validator = ComprehensiveQualityValidationService()
        self.extraction_service = OpenRouterExtractionService()
        self.template_engine = ProfessionalTemplateAssemblyEngine()
        self.rag_pipeline = EnhancedRAGPipeline()
        
        # Test configuration
        self.test_documents_path = Path("data/test_documents")
        self.existing_templates_path = Path("results/templates_archive")
        self.test_results_path = Path("tests/results/system_comparison")
        self.test_results_path.mkdir(parents=True, exist_ok=True)
    
    def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """
        Run comprehensive comparison between old and new systems
        """
        self.logger.info("Starting comprehensive system comparison")
        
        # Get test documents
        test_documents = self._get_test_documents()
        if not test_documents:
            self.logger.warning("No test documents found")
            return {"error": "No test documents available for testing"}
        
        comparison_results = {
            "test_timestamp": datetime.now().isoformat(),
            "total_documents": len(test_documents),
            "document_results": [],
            "aggregate_metrics": {},
            "performance_comparison": {},
            "quality_improvements": [],
            "regression_issues": []
        }
        
        for doc_path in test_documents:
            self.logger.info(f"Processing document: {doc_path}")
            doc_result = self._compare_document_processing(doc_path)
            comparison_results["document_results"].append(doc_result)
        
        # Calculate aggregate metrics
        comparison_results["aggregate_metrics"] = self._calculate_aggregate_metrics(
            comparison_results["document_results"]
        )
        
        # Generate performance comparison
        comparison_results["performance_comparison"] = self._generate_performance_comparison(
            comparison_results["document_results"]
        )
        
        # Identify improvements and regressions
        comparison_results["quality_improvements"] = self._identify_quality_improvements(
            comparison_results["document_results"]
        )
        comparison_results["regression_issues"] = self._identify_regression_issues(
            comparison_results["document_results"]
        )
        
        # Save results
        self._save_comparison_results(comparison_results)
        
        return comparison_results
    
    def _get_test_documents(self) -> List[Path]:
        """Get list of test documents for comparison"""
        test_docs = []
        
        # Look for injured worker PDFs
        injured_worker_docs = list(Path(".").glob("Injured worker*.pdf"))
        test_docs.extend(injured_worker_docs)
        
        # Look for sample documents
        sample_docs = list(Path(".").glob("Sample*.pdf"))
        test_docs.extend(sample_docs)
        
        # Look in data/documents if it exists
        if Path("data/documents").exists():
            data_docs = list(Path("data/documents").glob("*.pdf"))
            test_docs.extend(data_docs)
        
        return test_docs[:5]  # Limit to 5 documents for testing
    
    def _compare_document_processing(self, doc_path: Path) -> Dict[str, Any]:
        """
        Compare processing of a single document between old and new systems
        """
        doc_result = {
            "document_path": str(doc_path),
            "document_name": doc_path.name,
            "refactored_system": {},
            "baseline_comparison": {},
            "quality_comparison": {},
            "performance_metrics": {},
            "issues_identified": []
        }
        
        try:
            # Process with refactored system
            refactored_result = self._process_with_refactored_system(doc_path)
            doc_result["refactored_system"] = refactored_result
            
            # Compare with existing templates if available
            baseline_result = self._get_baseline_comparison(doc_path)
            doc_result["baseline_comparison"] = baseline_result
            
            # Quality validation
            if refactored_result.get("extraction_result"):
                quality_result = self.quality_validator.validate_extraction_quality(
                    refactored_result["extraction_result"]
                )
                doc_result["quality_comparison"] = self._serialize_quality_result(quality_result)
            
            # Performance metrics
            doc_result["performance_metrics"] = self._calculate_performance_metrics(
                refactored_result, baseline_result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing document {doc_path}: {e}")
            doc_result["issues_identified"].append(f"Processing error: {str(e)}")
        
        return doc_result
    
    def _process_with_refactored_system(self, doc_path: Path) -> Dict[str, Any]:
        """
        Process document with the refactored system
        """
        start_time = datetime.now()
        
        try:
            # Extract information using OpenRouter
            extraction_result = self.extraction_service.extract_from_document(str(doc_path))
            
            # Enhance with RAG pipeline
            enhanced_context = self.rag_pipeline.enhance_extraction_context(extraction_result)
            
            # Generate template
            template_result = self.template_engine.generate_professional_template(
                extraction_result, enhanced_context
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "extraction_result": extraction_result,
                "enhanced_context": enhanced_context,
                "template_result": template_result,
                "processing_time": processing_time,
                "success": True
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "error": str(e),
                "processing_time": processing_time,
                "success": False
            }
    
    def _get_baseline_comparison(self, doc_path: Path) -> Dict[str, Any]:
        """
        Get baseline comparison data from existing templates
        """
        # Look for existing templates that might correspond to this document
        doc_name_base = doc_path.stem.lower()
        
        # Search for similar templates in archive
        similar_templates = []
        if self.existing_templates_path.exists():
            for template_file in self.existing_templates_path.glob("*.docx"):
                if any(keyword in template_file.name.lower() for keyword in doc_name_base.split()):
                    similar_templates.append(template_file)
        
        return {
            "similar_templates_found": len(similar_templates),
            "template_files": [str(t) for t in similar_templates],
            "baseline_available": len(similar_templates) > 0
        }
    
    def _serialize_quality_result(self, quality_result: QualityValidationResult) -> Dict[str, Any]:
        """
        Serialize quality validation result for JSON storage
        """
        return {
            "document_id": quality_result.document_id,
            "overall_score": quality_result.overall_score,
            "weighted_score": quality_result.weighted_score,
            "processing_time": quality_result.processing_time,
            "metrics": [
                {
                    "name": metric.name,
                    "score": metric.score,
                    "weight": metric.weight,
                    "details": metric.details,
                    "issues_count": len(metric.issues),
                    "suggestions_count": len(metric.suggestions)
                }
                for metric in quality_result.metrics
            ],
            "compliance_checks": [
                {
                    "rule_name": check.rule_name,
                    "passed": check.passed,
                    "severity": check.severity,
                    "message": check.message
                }
                for check in quality_result.compliance_checks
            ],
            "recommendations_count": len(quality_result.recommendations)
        }
    
    def _calculate_performance_metrics(self, refactored_result: Dict[str, Any], 
                                     baseline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance metrics comparing systems
        """
        metrics = {
            "refactored_processing_time": refactored_result.get("processing_time", 0),
            "refactored_success": refactored_result.get("success", False),
            "baseline_available": baseline_result.get("baseline_available", False)
        }
        
        # Add extraction quality metrics if available
        if "extraction_result" in refactored_result:
            extraction = refactored_result["extraction_result"]
            if hasattr(extraction, 'extracted_fields'):
                metrics["fields_extracted"] = len(extraction.extracted_fields)
                metrics["avg_confidence"] = sum(
                    field.confidence for field in extraction.extracted_fields.values()
                ) / len(extraction.extracted_fields) if extraction.extracted_fields else 0
        
        return metrics
    
    def _calculate_aggregate_metrics(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics across all documents
        """
        if not document_results:
            return {}
        
        successful_docs = [doc for doc in document_results 
                          if doc["refactored_system"].get("success", False)]
        
        total_processing_time = sum(
            doc["refactored_system"].get("processing_time", 0) 
            for doc in document_results
        )
        
        # Quality metrics aggregation
        quality_scores = []
        compliance_rates = []
        
        for doc in document_results:
            quality_data = doc.get("quality_comparison", {})
            if "overall_score" in quality_data:
                quality_scores.append(quality_data["overall_score"])
            
            compliance_checks = quality_data.get("compliance_checks", [])
            if compliance_checks:
                passed_checks = sum(1 for check in compliance_checks if check["passed"])
                compliance_rates.append(passed_checks / len(compliance_checks))
        
        return {
            "total_documents": len(document_results),
            "successful_documents": len(successful_docs),
            "success_rate": len(successful_docs) / len(document_results),
            "total_processing_time": total_processing_time,
            "avg_processing_time": total_processing_time / len(document_results),
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "avg_compliance_rate": sum(compliance_rates) / len(compliance_rates) if compliance_rates else 0,
            "documents_with_baseline": sum(1 for doc in document_results 
                                         if doc["baseline_comparison"].get("baseline_available", False))
        }
    
    def _generate_performance_comparison(self, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate performance comparison analysis
        """
        performance_data = {
            "processing_speed": {
                "fastest_document": None,
                "slowest_document": None,
                "speed_variance": 0
            },
            "quality_distribution": {
                "excellent": 0,  # > 0.9
                "good": 0,       # 0.8 - 0.9
                "acceptable": 0, # 0.7 - 0.8
                "needs_improvement": 0  # < 0.7
            },
            "common_issues": [],
            "performance_trends": []
        }
        
        processing_times = []
        quality_scores = []
        
        for doc in document_results:
            # Processing time analysis
            proc_time = doc["refactored_system"].get("processing_time", 0)
            processing_times.append((doc["document_name"], proc_time))
            
            # Quality score analysis
            quality_data = doc.get("quality_comparison", {})
            if "overall_score" in quality_data:
                score = quality_data["overall_score"]
                quality_scores.append(score)
                
                if score > 0.9:
                    performance_data["quality_distribution"]["excellent"] += 1
                elif score > 0.8:
                    performance_data["quality_distribution"]["good"] += 1
                elif score > 0.7:
                    performance_data["quality_distribution"]["acceptable"] += 1
                else:
                    performance_data["quality_distribution"]["needs_improvement"] += 1
        
        # Speed analysis
        if processing_times:
            processing_times.sort(key=lambda x: x[1])
            performance_data["processing_speed"]["fastest_document"] = processing_times[0]
            performance_data["processing_speed"]["slowest_document"] = processing_times[-1]
            
            times_only = [t[1] for t in processing_times]
            avg_time = sum(times_only) / len(times_only)
            variance = sum((t - avg_time) ** 2 for t in times_only) / len(times_only)
            performance_data["processing_speed"]["speed_variance"] = variance
        
        return performance_data
    
    def _identify_quality_improvements(self, document_results: List[Dict[str, Any]]) -> List[str]:
        """
        Identify quality improvements in the refactored system
        """
        improvements = []
        
        # Analyze quality scores
        high_quality_docs = sum(1 for doc in document_results 
                               if doc.get("quality_comparison", {}).get("overall_score", 0) > 0.85)
        
        if high_quality_docs > len(document_results) * 0.7:
            improvements.append("High overall quality scores achieved (>85% for majority of documents)")
        
        # Analyze compliance
        compliant_docs = sum(1 for doc in document_results 
                           if doc.get("quality_comparison", {}).get("avg_compliance_rate", 0) > 0.9)
        
        if compliant_docs > len(document_results) * 0.8:
            improvements.append("Excellent compliance rates with QME and AMA standards")
        
        # Analyze processing consistency
        successful_docs = sum(1 for doc in document_results 
                            if doc["refactored_system"].get("success", False))
        
        if successful_docs == len(document_results):
            improvements.append("100% processing success rate achieved")
        elif successful_docs > len(document_results) * 0.9:
            improvements.append("High processing reliability (>90% success rate)")
        
        return improvements
    
    def _identify_regression_issues(self, document_results: List[Dict[str, Any]]) -> List[str]:
        """
        Identify potential regression issues
        """
        issues = []
        
        # Check for processing failures
        failed_docs = [doc for doc in document_results 
                      if not doc["refactored_system"].get("success", False)]
        
        if failed_docs:
            issues.append(f"Processing failures detected in {len(failed_docs)} documents")
        
        # Check for low quality scores
        low_quality_docs = [doc for doc in document_results 
                           if doc.get("quality_comparison", {}).get("overall_score", 1) < 0.7]
        
        if low_quality_docs:
            issues.append(f"Low quality scores (<0.7) in {len(low_quality_docs)} documents")
        
        # Check for compliance failures
        compliance_failures = []
        for doc in document_results:
            compliance_checks = doc.get("quality_comparison", {}).get("compliance_checks", [])
            critical_failures = [check for check in compliance_checks 
                               if not check["passed"] and check["severity"] == "critical"]
            if critical_failures:
                compliance_failures.append(doc["document_name"])
        
        if compliance_failures:
            issues.append(f"Critical compliance failures in documents: {', '.join(compliance_failures)}")
        
        return issues
    
    def _save_comparison_results(self, results: Dict[str, Any]) -> str:
        """
        Save comparison results to file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.test_results_path / f"system_comparison_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"System comparison results saved to {output_file}")
        return str(output_file)


# Pytest test cases
class TestEndToEndSystemComparison:
    """
    Pytest test cases for end-to-end system comparison
    """
    
    @pytest.fixture
    def comparison_suite(self):
        return SystemComparisonTestSuite()
    
    def test_system_comparison_execution(self, comparison_suite):
        """Test that system comparison executes without errors"""
        results = comparison_suite.run_comprehensive_comparison()
        
        assert "test_timestamp" in results
        assert "total_documents" in results
        assert isinstance(results["document_results"], list)
    
    def test_quality_validation_integration(self, comparison_suite):
        """Test integration with quality validation service"""
        # Test with a mock extraction result
        from src.models.extraction_models import ExtractionResult, ExtractedField, QualityAssessment, ProcessingMetadata
        
        mock_extraction = ExtractionResult(
            document_id="test_doc",
            extraction_method="openrouter_test",
            confidence_score=0.85,
            extracted_fields={
                "patient_name": ExtractedField(name="patient_name", value="Test Patient", confidence=0.9),
                "diagnosis": ExtractedField(name="diagnosis", value="Test Diagnosis", confidence=0.8)
            },
            quality_assessment=QualityAssessment(
                overall_score=0.85,
                completeness_score=0.8,
                accuracy_score=0.9,
                consistency_score=0.8,
                compliance_score=0.9
            ),
            processing_metadata=ProcessingMetadata(
                extraction_method="test",
                processing_time=5.0,
                model_used="test-model",
                prompt_template="test-prompt",
                api_version="1.0"
            )
        )
        
        quality_result = comparison_suite.quality_validator.validate_extraction_quality(mock_extraction)
        
        assert quality_result.document_id == "test_doc"
        assert 0 <= quality_result.overall_score <= 1
        assert len(quality_result.metrics) > 0
    
    def test_performance_metrics_calculation(self, comparison_suite):
        """Test performance metrics calculation"""
        mock_results = [
            {
                "document_name": "test1.pdf",
                "refactored_system": {"success": True, "processing_time": 5.0},
                "quality_comparison": {"overall_score": 0.85},
                "baseline_comparison": {"baseline_available": True}
            },
            {
                "document_name": "test2.pdf", 
                "refactored_system": {"success": True, "processing_time": 3.0},
                "quality_comparison": {"overall_score": 0.92},
                "baseline_comparison": {"baseline_available": False}
            }
        ]
        
        metrics = comparison_suite._calculate_aggregate_metrics(mock_results)
        
        assert metrics["total_documents"] == 2
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_processing_time"] == 4.0
        assert 0.85 <= metrics["avg_quality_score"] <= 0.92
    
    def test_regression_detection(self, comparison_suite):
        """Test regression issue detection"""
        mock_results = [
            {
                "document_name": "failing_doc.pdf",
                "refactored_system": {"success": False, "error": "Processing failed"},
                "quality_comparison": {"overall_score": 0.6, "compliance_checks": [
                    {"rule_name": "ama_guidelines", "passed": False, "severity": "critical"}
                ]}
            }
        ]
        
        issues = comparison_suite._identify_regression_issues(mock_results)
        
        assert len(issues) > 0
        assert any("Processing failures" in issue for issue in issues)
        assert any("Low quality scores" in issue for issue in issues)


if __name__ == "__main__":
    # Run the comparison suite directly
    suite = SystemComparisonTestSuite()
    results = suite.run_comprehensive_comparison()
    print(f"System comparison completed. Results saved.")
    print(f"Total documents processed: {results['total_documents']}")
    print(f"Success rate: {results['aggregate_metrics'].get('success_rate', 0):.1%}")