"""
Integration tests for Results Management and Code Organization

Tests the complete results management system including:
- Results storage service functionality
- Comprehensive logging service
- Component manager integration
- Configuration service
- SOLID principles compliance

This test suite validates that all components work together correctly
and follow the specified requirements.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import yaml

from src.services.results_storage_service import (
    ResultsStorageService, 
    DocumentMetadata, 
    StorageResult,
    ResultType
)
from src.services.comprehensive_logging_service import (
    ComprehensiveLoggingService,
    ProcessingStage,
    ProcessingMetrics,
    QualityMetrics,
    SystemHealthMetrics
)
from src.services.component_manager import (
    ComponentManager,
    ComponentInfo,
    ComponentType,
    ProcessingPipeline,
    create_default_component_manager
)
from src.services.configuration_service import (
    ConfigurationService,
    Environment,
    ConfigurationError
)
from src.services.service_registry import ServiceRegistry, ServiceLifetime


class TestResultsStorageService:
    """Test the results storage service functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_service = ResultsStorageService(self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_directory_structure_creation(self):
        """Test that required directory structure is created"""
        base_path = Path(self.temp_dir)
        
        assert (base_path / "generated_documents").exists()
        assert (base_path / "processing_logs").exists()
        assert (base_path / "validation_reports").exists()
        assert (base_path / "templates_archive").exists()
        
    def test_store_generated_document(self):
        """Test storing generated documents with date organization"""
        # Create a test document
        test_doc_path = Path(self.temp_dir) / "test_document.docx"
        test_doc_path.write_text("Test document content")
        
        # Store the document
        result = self.storage_service.store_generated_document(
            str(test_doc_path),
            "John Doe",
            DocumentMetadata(
                patient_name="John Doe",
                generation_timestamp=datetime.now(),
                document_type="QME Report",
                file_size=100,
                quality_score=85.5
            )
        )
        
        assert result.success
        assert "generated_documents" in result.file_path
        assert "John" in result.file_path  # Check for part of the name since sanitization may change format
        
        # Verify file exists in date-organized structure
        stored_path = Path(result.file_path)
        assert stored_path.exists()
        assert stored_path.parent.name == f"{datetime.now().month:02d}"
        assert stored_path.parent.parent.name == str(datetime.now().year)
        
    def test_store_processing_log(self):
        """Test storing processing logs"""
        log_content = "Test processing log content"
        result = self.storage_service.store_processing_log(
            log_content,
            "extraction",
            datetime.now()
        )
        
        assert result.success
        assert "processing_logs" in result.file_path
        assert "extraction" in result.file_path
        
        # Verify log content
        with open(result.file_path, 'r') as f:
            assert f.read() == log_content
            
    def test_store_validation_report(self):
        """Test storing validation reports"""
        report_content = "Test validation report"
        result = self.storage_service.store_validation_report(
            report_content,
            "test_document.docx",
            92.5
        )
        
        assert result.success
        assert "validation_reports" in result.file_path
        assert "Quality_Report" in result.file_path
        
    def test_archive_template(self):
        """Test archiving existing templates"""
        # Create a test template
        test_template_path = Path(self.temp_dir) / "test_template.docx"
        test_template_path.write_text("Test template content")
        
        result = self.storage_service.archive_template(
            str(test_template_path),
            preserve_original=True
        )
        
        assert result.success
        assert "templates_archive" in result.file_path
        
        # Verify both original and archived files exist
        assert test_template_path.exists()
        assert Path(result.file_path).exists()
        
    def test_storage_statistics(self):
        """Test storage statistics generation"""
        # Create some test files
        test_doc = Path(self.temp_dir) / "test.docx"
        test_doc.write_text("test")
        
        self.storage_service.store_generated_document(str(test_doc), "Test Patient")
        self.storage_service.store_processing_log("test log", "test")
        
        stats = self.storage_service.get_storage_statistics()
        
        assert "generated_documents" in stats
        assert "processing_logs" in stats
        assert "total_storage_size" in stats
        assert stats["generated_documents"] >= 1
        assert stats["processing_logs"] >= 1


class TestComprehensiveLoggingService:
    """Test the comprehensive logging service"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.logging_service = ComprehensiveLoggingService(
            log_directory=self.temp_dir,
            max_memory_logs=100
        )
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_processing_stage_tracking(self):
        """Test processing stage tracking with context manager"""
        operation_id = "test_operation_123"
        
        with self.logging_service.track_processing_stage(
            ProcessingStage.INFORMATION_EXTRACTION,
            operation_id,
            input_size=1000
        ) as metrics:
            # Simulate some processing
            metrics.quality_score = 85.0
            
        # Verify metrics were recorded
        assert len(self.logging_service.processing_metrics) == 1
        recorded_metrics = self.logging_service.processing_metrics[0]
        
        assert recorded_metrics.stage == ProcessingStage.INFORMATION_EXTRACTION
        assert recorded_metrics.success is True
        assert recorded_metrics.duration is not None
        assert recorded_metrics.quality_score == 85.0
        
    def test_quality_metrics_logging(self):
        """Test quality metrics logging"""
        quality_metrics = QualityMetrics(
            document_id="test_doc_123",
            overall_score=88.5,
            completeness_score=90.0,
            accuracy_score=87.0,
            consistency_score=89.0,
            compliance_score=88.0,
            processing_time=2.5,
            validation_issues=["Minor formatting issue"],
            timestamp=datetime.now()
        )
        
        self.logging_service.log_quality_metrics(quality_metrics)
        
        # Verify metrics were recorded
        assert len(self.logging_service.quality_metrics) == 1
        recorded_metrics = self.logging_service.quality_metrics[0]
        
        assert recorded_metrics.document_id == "test_doc_123"
        assert recorded_metrics.overall_score == 88.5
        
    def test_error_logging(self):
        """Test error logging with context"""
        test_error = ValueError("Test error message")
        context = {"operation": "test", "document_id": "123"}
        
        self.logging_service.log_error(
            test_error,
            context,
            ProcessingStage.TEMPLATE_ASSEMBLY
        )
        
        # Verify error was recorded
        assert len(self.logging_service.error_log) == 1
        error_record = self.logging_service.error_log[0]
        
        assert error_record["error_type"] == "ValueError"
        assert error_record["error_message"] == "Test error message"
        assert error_record["stage"] == ProcessingStage.TEMPLATE_ASSEMBLY.value
        
    def test_processing_statistics(self):
        """Test processing statistics generation"""
        # Create some test metrics
        with self.logging_service.track_processing_stage(
            ProcessingStage.INFORMATION_EXTRACTION,
            "op1"
        ):
            pass
            
        with self.logging_service.track_processing_stage(
            ProcessingStage.TEMPLATE_ASSEMBLY,
            "op2"
        ):
            pass
            
        stats = self.logging_service.get_processing_statistics()
        
        assert stats["total_operations"] == 2
        assert stats["successful_operations"] == 2
        assert stats["success_rate"] == 1.0
        assert "stage_statistics" in stats
        
    def test_monitoring_report_generation(self):
        """Test comprehensive monitoring report generation"""
        # Add some test data
        with self.logging_service.track_processing_stage(
            ProcessingStage.INFORMATION_EXTRACTION,
            "test_op"
        ):
            pass
            
        report = self.logging_service.generate_monitoring_report()
        
        assert "QME System Monitoring Report" in report
        assert "PROCESSING STATISTICS" in report
        assert "QUALITY STATISTICS" in report
        assert "ERROR ANALYSIS" in report


class TestComponentManager:
    """Test the component manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service_registry = ServiceRegistry()
        self.component_manager = ComponentManager(self.service_registry)
        
    def test_component_registration(self):
        """Test component registration"""
        component_info = ComponentInfo(
            name="test_component",
            component_type=ComponentType.EXTRACTION,
            version="1.0.0",
            description="Test component",
            dependencies=[]
        )
        
        self.component_manager.register_component(component_info)
        
        assert "test_component" in self.component_manager.components
        registered = self.component_manager.components["test_component"]
        assert registered.name == "test_component"
        assert registered.component_type == ComponentType.EXTRACTION
        
    def test_component_activation_with_dependencies(self):
        """Test component activation with dependency resolution"""
        # Register components with dependencies
        base_component = ComponentInfo(
            name="base_service",
            component_type=ComponentType.STORAGE,
            version="1.0.0",
            description="Base service",
            dependencies=[]
        )
        
        dependent_component = ComponentInfo(
            name="dependent_service",
            component_type=ComponentType.LOGGING,
            version="1.0.0",
            description="Dependent service",
            dependencies=["base_service"]
        )
        
        self.component_manager.register_component(base_component)
        self.component_manager.register_component(dependent_component)
        
        # Activate dependent component (should activate base component first)
        result = self.component_manager.activate_component("dependent_service")
        
        assert result is True
        assert self.component_manager.components["base_service"].is_active
        assert self.component_manager.components["dependent_service"].is_active
        
    def test_system_integrity_validation(self):
        """Test system integrity validation"""
        # Register component with missing dependency
        component_info = ComponentInfo(
            name="broken_component",
            component_type=ComponentType.EXTRACTION,
            version="1.0.0",
            description="Component with missing dependency",
            dependencies=["missing_dependency"]
        )
        
        self.component_manager.register_component(component_info)
        
        integrity_report = self.component_manager.validate_system_integrity()
        
        assert integrity_report["overall_status"] != "healthy"
        assert len(integrity_report["issues"]) > 0
        assert any("missing_dependency" in issue for issue in integrity_report["issues"])
        
    def test_default_component_manager_creation(self):
        """Test creation of default component manager"""
        manager = create_default_component_manager()
        
        assert len(manager.components) > 0
        assert len(manager.pipelines) > 0
        
        # Verify core components are registered
        assert "results_storage" in manager.components
        assert "comprehensive_logging" in manager.components
        
        # Verify default pipeline is registered
        assert "qme_document_processing" in manager.pipelines


class TestConfigurationService:
    """Test the configuration service"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # Create test configuration
        self._create_test_config()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_test_config(self):
        """Create test configuration files"""
        system_config = {
            "system": {
                "name": "Test QME System",
                "version": "1.0.0",
                "environment": "testing"
            },
            "components": {
                "test_component": {
                    "type": "extraction",
                    "class": "TestExtractionService",
                    "config": {"setting1": "value1"},
                    "dependencies": []
                }
            },
            "pipelines": {
                "test_pipeline": {
                    "description": "Test pipeline",
                    "stages": ["extraction"],
                    "components": {"extraction": "test_component"},
                    "configuration": {"test_setting": "test_value"}
                }
            },
            "monitoring": {"enabled": True},
            "storage": {"base_path": "results"},
            "security": {"encryption": True}
        }
        
        system_dir = self.config_dir / "system"
        system_dir.mkdir()
        
        with open(system_dir / "component_config.yaml", 'w') as f:
            yaml.dump(system_config, f)
            
    def test_configuration_loading(self):
        """Test configuration loading from files"""
        config_service = ConfigurationService(str(self.config_dir))
        
        assert config_service.system_config.name == "Test QME System"
        assert config_service.system_config.version == "1.0.0"
        assert config_service.system_config.environment == Environment.TESTING
        
    def test_component_config_access(self):
        """Test accessing component configuration"""
        config_service = ConfigurationService(str(self.config_dir))
        
        component_config = config_service.get_component_config("test_component")
        
        assert component_config.name == "test_component"
        assert component_config.type == "extraction"
        assert component_config.class_name == "TestExtractionService"
        assert component_config.config["setting1"] == "value1"
        
    def test_pipeline_config_access(self):
        """Test accessing pipeline configuration"""
        config_service = ConfigurationService(str(self.config_dir))
        
        pipeline_config = config_service.get_pipeline_config("test_pipeline")
        
        assert pipeline_config.name == "test_pipeline"
        assert pipeline_config.description == "Test pipeline"
        assert "extraction" in pipeline_config.stages
        
    def test_setting_access_with_dot_notation(self):
        """Test accessing settings with dot notation"""
        config_service = ConfigurationService(str(self.config_dir))
        
        storage_path = config_service.get_setting("storage.base_path")
        assert storage_path == "results"
        
        encryption_enabled = config_service.get_setting("security.encryption")
        assert encryption_enabled is True
        
        missing_setting = config_service.get_setting("missing.setting", "default")
        assert missing_setting == "default"
        
    def test_configuration_validation(self):
        """Test configuration validation"""
        config_service = ConfigurationService(str(self.config_dir))
        
        issues = config_service.validate_configuration()
        
        # Should have minimal issues with our test config
        assert isinstance(issues, dict)
        assert "components" in issues
        assert "pipelines" in issues
        assert "dependencies" in issues
        assert "files" in issues


class TestSystemIntegration:
    """Test complete system integration"""
    
    def setup_method(self):
        """Setup integrated test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup results storage
        self.results_storage = ResultsStorageService(self.temp_dir)
        
        # Setup logging service
        self.logging_service = ComprehensiveLoggingService(
            log_directory=str(Path(self.temp_dir) / "logs"),
            results_storage=self.results_storage
        )
        
    def teardown_method(self):
        """Cleanup integrated test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_integrated_document_processing_workflow(self):
        """Test complete document processing workflow"""
        # Create test document
        test_doc_path = Path(self.temp_dir) / "test_document.docx"
        test_doc_path.write_text("Test QME document content")
        
        operation_id = "integration_test_001"
        
        # Simulate complete processing workflow with logging
        with self.logging_service.track_processing_stage(
            ProcessingStage.DOCUMENT_INGESTION,
            operation_id,
            input_size=len(test_doc_path.read_text())
        ) as ingestion_metrics:
            ingestion_metrics.output_size = 500
            
        with self.logging_service.track_processing_stage(
            ProcessingStage.INFORMATION_EXTRACTION,
            operation_id + "_extraction"
        ) as extraction_metrics:
            extraction_metrics.quality_score = 88.5
            
        with self.logging_service.track_processing_stage(
            ProcessingStage.TEMPLATE_ASSEMBLY,
            operation_id + "_assembly"
        ) as assembly_metrics:
            assembly_metrics.output_size = 2000
            
        # Store the processed document
        storage_result = self.results_storage.store_generated_document(
            str(test_doc_path),
            "Integration Test Patient",
            DocumentMetadata(
                patient_name="Integration Test Patient",
                generation_timestamp=datetime.now(),
                document_type="QME Report",
                file_size=2000,
                quality_score=88.5,
                processing_time=5.2
            )
        )
        
        # Log quality metrics
        quality_metrics = QualityMetrics(
            document_id=operation_id,
            overall_score=88.5,
            completeness_score=90.0,
            accuracy_score=87.0,
            consistency_score=89.0,
            compliance_score=88.0,
            processing_time=5.2,
            validation_issues=["Minor formatting adjustment needed"],
            timestamp=datetime.now()
        )
        
        self.logging_service.log_quality_metrics(quality_metrics)
        
        # Verify integrated workflow results
        assert storage_result.success
        assert len(self.logging_service.processing_metrics) == 3
        assert len(self.logging_service.quality_metrics) == 1
        
        # Verify processing statistics
        stats = self.logging_service.get_processing_statistics()
        assert stats["total_operations"] == 3
        assert stats["successful_operations"] == 3
        assert stats["success_rate"] == 1.0
        
        # Verify storage statistics
        storage_stats = self.results_storage.get_storage_statistics()
        assert storage_stats["generated_documents"] >= 1
        assert storage_stats["validation_reports"] >= 1
        
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        operation_id = "error_test_001"
        
        # Simulate processing with error
        try:
            with self.logging_service.track_processing_stage(
                ProcessingStage.INFORMATION_EXTRACTION,
                operation_id
            ):
                raise ValueError("Simulated extraction error")
        except ValueError:
            pass  # Expected error
            
        # Verify error was logged
        assert len(self.logging_service.error_log) == 1
        assert len(self.logging_service.processing_metrics) == 1
        
        error_record = self.logging_service.error_log[0]
        assert error_record.get("error_type") == "ValueError" or "ValueError" in str(error_record)
        
        processing_record = self.logging_service.processing_metrics[0]
        assert processing_record.success is False
        assert processing_record.error_message == "Simulated extraction error"
        
        # Test error analysis
        error_analysis = self.logging_service.get_error_analysis()
        assert error_analysis["total_errors"] == 1
        assert error_analysis["most_common_error"] == "ValueError"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])