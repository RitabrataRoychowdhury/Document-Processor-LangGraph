#!/usr/bin/env python3
"""
Validation Script for QME System Refactor
Tests the refactored system against real documents (Injured worker PDFs) with quality metrics
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.validation.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
from tests.test_professional_template_assembly_engine import ProfessionalTemplateAssemblyEngine
from src.infrastructure.knowledge.enhanced_rag_pipeline import EnhancedRAGPipeline
from src.infrastructure.monitoring.system_performance_monitor import SystemPerformanceMonitor
from src.config.openrouter_config_manager import OpenRouterConfigManager


class RealDocumentValidator:
    """
    Validator for testing the refactored system against real documents
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # Initialize services
        try:
            self.quality_validator = ComprehensiveQualityValidationService()
            self.extraction_service = OpenRouterExtractionService()
            self.template_engine = ProfessionalTemplateAssemblyEngine()
            self.rag_pipeline = EnhancedRAGPipeline()
            self.performance_monitor = SystemPerformanceMonitor()
            
            self.logger.info("All services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
        
        # Test configuration
        self.test_config = {
            "max_documents": 10,
            "timeout_per_document": 60,  # seconds
            "quality_threshold": 0.75,
            "compliance_required": True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/real_document_validation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def find_real_documents(self) -> list[Path]:
        """Find real documents for testing"""
        document_paths = []
        
        # Look for injured worker PDFs
        injured_worker_patterns = [
            "Injured worker*.pdf",
            "injured worker*.pdf", 
            "INJURED WORKER*.pdf"
        ]
        
        for pattern in injured_worker_patterns:
            found_docs = list(Path(".").glob(pattern))
            document_paths.extend(found_docs)
        
        # Look for sample documents
        sample_patterns = ["Sample*.pdf", "sample*.pdf"]
        for pattern in sample_patterns:
            found_docs = list(Path(".").glob(pattern))
            document_paths.extend(found_docs)
        
        # Look in data/documents directory
        data_docs_path = Path("data/documents")
        if data_docs_path.exists():
            pdf_docs = list(data_docs_path.glob("*.pdf"))
            document_paths.extend(pdf_docs)
        
        # Remove duplicates and limit
        unique_docs = list(set(document_paths))
        limited_docs = unique_docs[:self.test_config["max_documents"]]
        
        self.logger.info(f"Found {len(unique_docs)} unique documents, testing {len(limited_docs)}")
        return limited_docs
    
    def validate_single_document(self, doc_path: Path) -> dict:
        """
        Validate processing of a single document
        """
        self.logger.info(f"Validating document: {doc_path}")
        
        validation_result = {
            "document_path": str(doc_path),
            "document_name": doc_path.name,
            "file_size_mb": doc_path.stat().st_size / (1024 * 1024),
            "validation_timestamp": datetime.now().isoformat(),
            "success": False,
            "extraction_result": None,
            "quality_validation": None,
            "template_generation": None,
            "performance_metrics": {},
            "errors": [],
            "warnings": []
        }
        
        # Start performance monitoring for this document
        with self.performance_monitor.track_document_processing(doc_path.name, "real_doc_validation"):
            try:
                # Step 1: Document Extraction
                self.logger.info(f"Step 1: Extracting information from {doc_path.name}")
                extraction_result = self.extraction_service.extract_from_document(str(doc_path))
                validation_result["extraction_result"] = self._serialize_extraction_result(extraction_result)
                
                # Step 2: Quality Validation
                self.logger.info(f"Step 2: Validating extraction quality for {doc_path.name}")
                quality_result = self.quality_validator.validate_extraction_quality(extraction_result)
                validation_result["quality_validation"] = self._serialize_quality_result(quality_result)
                
                # Step 3: Enhanced RAG Processing
                self.logger.info(f"Step 3: Enhancing context with RAG pipeline for {doc_path.name}")
                enhanced_context = self.rag_pipeline.enhance_extraction_context(extraction_result)
                
                # Step 4: Template Generation
                self.logger.info(f"Step 4: Generating professional template for {doc_path.name}")
                template_result = self.template_engine.generate_professional_template(
                    extraction_result, enhanced_context
                )
                validation_result["template_generation"] = self._serialize_template_result(template_result)
                
                # Check quality thresholds
                if quality_result.weighted_score >= self.test_config["quality_threshold"]:
                    validation_result["success"] = True
                    self.logger.info(f"Document {doc_path.name} passed validation with score {quality_result.weighted_score:.3f}")
                else:
                    validation_result["warnings"].append(
                        f"Quality score {quality_result.weighted_score:.3f} below threshold {self.test_config['quality_threshold']}"
                    )
                    self.logger.warning(f"Document {doc_path.name} below quality threshold")
                
                # Check compliance requirements
                if self.test_config["compliance_required"]:
                    critical_failures = [check for check in quality_result.compliance_checks 
                                       if not check.passed and check.severity == "critical"]
                    if critical_failures:
                        validation_result["success"] = False
                        validation_result["errors"].append(f"Critical compliance failures: {len(critical_failures)}")
                
            except Exception as e:
                self.logger.error(f"Error validating document {doc_path.name}: {e}")
                validation_result["errors"].append(f"Processing error: {str(e)}")
                validation_result["success"] = False
        
        return validation_result
    
    def _serialize_extraction_result(self, extraction_result) -> dict:
        """Serialize extraction result for JSON storage"""
        if not extraction_result:
            return None
        
        return {
            "document_id": extraction_result.document_id,
            "extraction_method": extraction_result.extraction_method,
            "confidence_score": extraction_result.confidence_score,
            "fields_extracted": len(extraction_result.extracted_fields),
            "field_summary": {
                field_name: {
                    "has_value": bool(field.value),
                    "confidence": field.confidence,
                    "value_length": len(str(field.value)) if field.value else 0
                }
                for field_name, field in extraction_result.extracted_fields.items()
            }
        }
    
    def _serialize_quality_result(self, quality_result) -> dict:
        """Serialize quality validation result for JSON storage"""
        if not quality_result:
            return None
        
        return {
            "overall_score": quality_result.overall_score,
            "weighted_score": quality_result.weighted_score,
            "processing_time": quality_result.processing_time,
            "metrics": [
                {
                    "name": metric.name,
                    "score": metric.score,
                    "weight": metric.weight,
                    "issues_count": len(metric.issues),
                    "suggestions_count": len(metric.suggestions)
                }
                for metric in quality_result.metrics
            ],
            "compliance_summary": {
                "total_checks": len(quality_result.compliance_checks),
                "passed_checks": sum(1 for check in quality_result.compliance_checks if check.passed),
                "critical_failures": sum(1 for check in quality_result.compliance_checks 
                                       if not check.passed and check.severity == "critical"),
                "warning_failures": sum(1 for check in quality_result.compliance_checks 
                                      if not check.passed and check.severity == "warning")
            },
            "recommendations_count": len(quality_result.recommendations)
        }
    
    def _serialize_template_result(self, template_result) -> dict:
        """Serialize template generation result for JSON storage"""
        if not template_result:
            return None
        
        return {
            "success": template_result.get("success", False),
            "output_path": template_result.get("output_path"),
            "generation_time": template_result.get("generation_time", 0),
            "template_sections": template_result.get("sections_generated", []),
            "word_count": template_result.get("word_count", 0),
            "quality_score": template_result.get("quality_score", 0)
        }
    
    def run_comprehensive_validation(self) -> dict:
        """
        Run comprehensive validation against all available real documents
        """
        self.logger.info("Starting comprehensive validation with real documents")
        
        # Start system monitoring
        self.performance_monitor.start_monitoring()
        
        validation_session = {
            "session_id": f"real_doc_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "test_configuration": self.test_config,
            "documents_tested": [],
            "summary_metrics": {},
            "system_performance": {},
            "recommendations": []
        }
        
        try:
            # Find documents to test
            documents = self.find_real_documents()
            
            if not documents:
                self.logger.warning("No real documents found for validation")
                validation_session["error"] = "No documents available for testing"
                return validation_session
            
            # Process each document
            with self.performance_monitor.track_processing_session(validation_session["session_id"]):
                for doc_path in documents:
                    doc_result = self.validate_single_document(doc_path)
                    validation_session["documents_tested"].append(doc_result)
            
            # Calculate summary metrics
            validation_session["summary_metrics"] = self._calculate_summary_metrics(
                validation_session["documents_tested"]
            )
            
            # Get system performance data
            validation_session["system_performance"] = self.performance_monitor.get_performance_summary(1)
            
            # Generate recommendations
            validation_session["recommendations"] = self._generate_validation_recommendations(
                validation_session["documents_tested"],
                validation_session["summary_metrics"]
            )
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive validation: {e}")
            validation_session["error"] = str(e)
        
        finally:
            # Stop monitoring
            self.performance_monitor.stop_monitoring()
            validation_session["end_time"] = datetime.now().isoformat()
        
        # Save results
        self._save_validation_results(validation_session)
        
        return validation_session
    
    def _calculate_summary_metrics(self, document_results: list) -> dict:
        """Calculate summary metrics from document results"""
        if not document_results:
            return {}
        
        successful_docs = [doc for doc in document_results if doc["success"]]
        quality_scores = [
            doc["quality_validation"]["weighted_score"] 
            for doc in document_results 
            if doc["quality_validation"] and "weighted_score" in doc["quality_validation"]
        ]
        
        extraction_success = [
            doc for doc in document_results 
            if doc["extraction_result"] and doc["extraction_result"]["fields_extracted"] > 0
        ]
        
        template_success = [
            doc for doc in document_results 
            if doc["template_generation"] and doc["template_generation"]["success"]
        ]
        
        return {
            "total_documents": len(document_results),
            "successful_documents": len(successful_docs),
            "success_rate": len(successful_docs) / len(document_results),
            "extraction_success_rate": len(extraction_success) / len(document_results),
            "template_generation_success_rate": len(template_success) / len(document_results),
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "min_quality_score": min(quality_scores) if quality_scores else 0,
            "max_quality_score": max(quality_scores) if quality_scores else 0,
            "documents_above_threshold": sum(1 for score in quality_scores 
                                           if score >= self.test_config["quality_threshold"]),
            "total_errors": sum(len(doc["errors"]) for doc in document_results),
            "total_warnings": sum(len(doc["warnings"]) for doc in document_results)
        }
    
    def _generate_validation_recommendations(self, document_results: list, summary_metrics: dict) -> list:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Success rate recommendations
        if summary_metrics.get("success_rate", 0) < 0.8:
            recommendations.append("Overall success rate is below 80% - investigate common failure patterns")
        
        # Quality score recommendations
        avg_quality = summary_metrics.get("average_quality_score", 0)
        if avg_quality < 0.75:
            recommendations.append(f"Average quality score ({avg_quality:.3f}) is below acceptable threshold - review extraction prompts")
        
        # Extraction recommendations
        extraction_rate = summary_metrics.get("extraction_success_rate", 0)
        if extraction_rate < 0.9:
            recommendations.append("Extraction success rate is low - check OpenRouter configuration and document preprocessing")
        
        # Template generation recommendations
        template_rate = summary_metrics.get("template_generation_success_rate", 0)
        if template_rate < 0.85:
            recommendations.append("Template generation success rate is low - validate template configurations")
        
        # Error pattern analysis
        common_errors = {}
        for doc in document_results:
            for error in doc["errors"]:
                if "Processing error:" in error:
                    error_type = error.split(":")[1].strip().split()[0]
                    common_errors[error_type] = common_errors.get(error_type, 0) + 1
        
        if common_errors:
            most_common = max(common_errors.items(), key=lambda x: x[1])
            if most_common[1] > 1:
                recommendations.append(f"Common error pattern detected: {most_common[0]} ({most_common[1]} occurrences)")
        
        return recommendations
    
    def _save_validation_results(self, validation_session: dict) -> str:
        """Save validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"results/validation_reports/real_document_validation_{timestamp}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(validation_session, f, indent=2)
        
        self.logger.info(f"Validation results saved to {output_path}")
        return str(output_path)
    
    def print_validation_summary(self, validation_session: dict):
        """Print a summary of validation results"""
        print("\n" + "="*60)
        print("QME SYSTEM REAL DOCUMENT VALIDATION SUMMARY")
        print("="*60)
        
        if "error" in validation_session:
            print(f"❌ Validation failed: {validation_session['error']}")
            return
        
        summary = validation_session.get("summary_metrics", {})
        
        print(f"📊 Documents Tested: {summary.get('total_documents', 0)}")
        print(f"✅ Success Rate: {summary.get('success_rate', 0):.1%}")
        print(f"📈 Average Quality Score: {summary.get('average_quality_score', 0):.3f}")
        print(f"🎯 Documents Above Threshold: {summary.get('documents_above_threshold', 0)}")
        print(f"⚠️  Total Warnings: {summary.get('total_warnings', 0)}")
        print(f"❌ Total Errors: {summary.get('total_errors', 0)}")
        
        # Performance metrics
        perf = validation_session.get("system_performance", {}).get("processing_metrics", {})
        if perf:
            print(f"⏱️  Average Processing Time: {perf.get('avg_processing_time', 0):.2f}s")
        
        # Recommendations
        recommendations = validation_session.get("recommendations", [])
        if recommendations:
            print("\n🔧 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function for command-line execution"""
    parser = argparse.ArgumentParser(description="Validate QME system with real documents")
    parser.add_argument("--max-docs", type=int, default=10, help="Maximum number of documents to test")
    parser.add_argument("--quality-threshold", type=float, default=0.75, help="Quality score threshold")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize validator
        validator = RealDocumentValidator()
        
        # Update configuration
        validator.test_config["max_documents"] = args.max_docs
        validator.test_config["quality_threshold"] = args.quality_threshold
        
        # Run validation
        results = validator.run_comprehensive_validation()
        
        # Print summary
        validator.print_validation_summary(results)
        
        # Return appropriate exit code
        if "error" in results:
            sys.exit(1)
        
        summary = results.get("summary_metrics", {})
        if summary.get("success_rate", 0) < 0.8:
            print("\n⚠️  Warning: Success rate below 80%")
            sys.exit(2)
        
        print("\n✅ Validation completed successfully!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()