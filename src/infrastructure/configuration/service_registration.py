"""
Service Registration Module

This module provides comprehensive service registration for the QME system,
integrating all backend services with the dependency injection container.
"""

import logging
from typing import Dict, Any, Optional, Type, List
from pathlib import Path

# Import service registry
from src.infrastructure.configuration.service_registry import (
    service_registry, 
    ServiceLifetime,
    get_service,
    register_service
)

# Import configuration service
from src.infrastructure.configuration.configuration_service import (
    ConfigurationService,
    create_configuration_service
)

# Import core interfaces
from src.core.interfaces import (
    IExtractionService,
    IValidationService,
    IGenerationService,
    ICalculationService,
    IKnowledgeService,
    IStorageService,
    IMonitoringService
)

# Optional dependencies with graceful degradation
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)


class ServiceRegistrationError(Exception):
    """Service registration related errors."""
    pass


class ServiceRegistrationManager:
    """
    Manager for registering all backend services with the dependency injection container.
    
    Features:
    - Automatic service discovery and registration
    - Dependency resolution and validation
    - Service health monitoring
    - Configuration-based service instantiation
    - Error handling and fallback mechanisms
    """
    
    def __init__(self, config_service: Optional[ConfigurationService] = None):
        """Initialize the service registration manager."""
        self.config_service = config_service or create_configuration_service()
        self.registered_services: Dict[str, Type] = {}
        self.registration_errors: List[str] = []
        
        extraction_logger.info("Initialized ServiceRegistrationManager")
    
    def register_all_services(self) -> Dict[str, Any]:
        """
        Register all backend services with the dependency injection container.
        
        Returns:
            Dictionary with registration results and statistics
        """
        registration_results = {
            "total_services": 0,
            "successful_registrations": 0,
            "failed_registrations": 0,
            "errors": [],
            "registered_services": []
        }
        
        try:
            # Register core infrastructure services first
            self._register_infrastructure_services(registration_results)
            
            # Register extraction services
            self._register_extraction_services(registration_results)
            
            # Register generation services
            self._register_generation_services(registration_results)
            
            # Register validation services
            self._register_validation_services(registration_results)
            
            # Register calculation services
            self._register_calculation_services(registration_results)
            
            # Register knowledge services
            self._register_knowledge_services(registration_results)
            
            # Register storage services
            self._register_storage_services(registration_results)
            
            # Register monitoring services
            self._register_monitoring_services(registration_results)
            
            # Register strategy services
            self._register_strategy_services(registration_results)
            
            # Validate all registrations
            validation_errors = service_registry.validate_registrations()
            if validation_errors:
                registration_results["errors"].extend(validation_errors)
                registration_results["failed_registrations"] += len(validation_errors)
            
            extraction_logger.info(
                f"Service registration completed: {registration_results['successful_registrations']} successful, "
                f"{registration_results['failed_registrations']} failed"
            )
            
        except Exception as e:
            error_msg = f"Critical error during service registration: {str(e)}"
            extraction_logger.error(error_msg)
            registration_results["errors"].append(error_msg)
            registration_results["failed_registrations"] += 1
        
        return registration_results
    
    def _register_infrastructure_services(self, results: Dict[str, Any]) -> None:
        """Register infrastructure services."""
        try:
            # Configuration Service
            service_registry.register_singleton(
                ConfigurationService,
                instance=self.config_service
            )
            self._record_success("ConfigurationService", results)
            
            # Results Storage Service
            try:
                from src.infrastructure.storage.results_storage_service import ResultsStorageService
                service_registry.register_singleton(
                    ResultsStorageService,
                    factory_func=lambda: ResultsStorageService(
                        base_storage_path=self.config_service.get("storage.base_path", "results")
                    )
                )
                service_registry.register_singleton(IStorageService, factory_func=lambda: service_registry.get(ResultsStorageService))
                self._record_success("ResultsStorageService", results)
            except ImportError as e:
                self._record_error(f"ResultsStorageService: {str(e)}", results)
            
            # Comprehensive Logging Service
            try:
                from src.infrastructure.monitoring.comprehensive_logging_service import ComprehensiveLoggingService
                service_registry.register_singleton(
                    ComprehensiveLoggingService,
                    factory_func=lambda: ComprehensiveLoggingService(
                        log_directory=self.config_service.get("logging.directory", "logs")
                    )
                )
                self._record_success("ComprehensiveLoggingService", results)
            except ImportError as e:
                self._record_error(f"ComprehensiveLoggingService: {str(e)}", results)
            
            # Performance Monitoring Service
            try:
                from src.infrastructure.monitoring.performance_monitoring_service import PerformanceMonitoringService
                service_registry.register_singleton(
                    PerformanceMonitoringService,
                    factory_func=lambda: PerformanceMonitoringService()
                )
                service_registry.register_singleton(IMonitoringService, factory_func=lambda: service_registry.get(PerformanceMonitoringService))
                self._record_success("PerformanceMonitoringService", results)
            except ImportError as e:
                self._record_error(f"PerformanceMonitoringService: {str(e)}", results)
            
            # Metadata Tracking Service
            try:
                from src.infrastructure.storage.metadata_tracking_service import MetadataTrackingService
                service_registry.register_singleton(
                    MetadataTrackingService,
                    factory_func=lambda: MetadataTrackingService()
                )
                self._record_success("MetadataTrackingService", results)
            except ImportError as e:
                self._record_error(f"MetadataTrackingService: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Infrastructure services registration error: {str(e)}", results)
    
    def _register_extraction_services(self, results: Dict[str, Any]) -> None:
        """Register extraction services."""
        try:
            # Comprehensive QME Field Service
            try:
                from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
                service_registry.register_singleton(
                    ComprehensiveQMEFieldService,
                    factory_func=lambda: ComprehensiveQMEFieldService()
                )
                service_registry.register_singleton(IExtractionService, factory_func=lambda: service_registry.get(ComprehensiveQMEFieldService))
                self._record_success("ComprehensiveQMEFieldService", results)
            except ImportError as e:
                self._record_error(f"ComprehensiveQMEFieldService: {str(e)}", results)
            
            # Field Extraction Service
            try:
                from src.core.extraction.field_extraction_service import FieldExtractionService
                service_registry.register_singleton(
                    FieldExtractionService,
                    factory_func=lambda: FieldExtractionService(
                        config=self.config_service.get_section("extraction")
                    )
                )
                self._record_success("FieldExtractionService", results)
            except ImportError as e:
                self._record_error(f"FieldExtractionService: {str(e)}", results)
            
            # OpenRouter Extraction Service
            try:
                from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
                openrouter_api_key = self.config_service.get("openrouter.api_key")
                if openrouter_api_key:
                    service_registry.register_singleton(
                        OpenRouterExtractionService,
                        factory_func=lambda: OpenRouterExtractionService(
                            api_key=openrouter_api_key,
                            timeout=self.config_service.get("api.timeout", 60)
                        )
                    )
                    self._record_success("OpenRouterExtractionService", results)
                else:
                    self._record_error("OpenRouterExtractionService: API key not configured", results)
            except ImportError as e:
                self._record_error(f"OpenRouterExtractionService: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Extraction services registration error: {str(e)}", results)
    
    def _register_generation_services(self, results: Dict[str, Any]) -> None:
        """Register generation services."""
        try:
            # Professional Template Assembler
            try:
                from src.services.professional_template_assembler_simple import ProfessionalTemplateAssembler
                service_registry.register_singleton(
                    ProfessionalTemplateAssembler,
                    factory_func=lambda: ProfessionalTemplateAssembler()
                )
                from src.infrastructure.storage.results_storage_service import ResultsStorageService
                service_registry.register_singleton(IGenerationService, factory_func=lambda: service_registry.get(ProfessionalTemplateAssembler))
                self._record_success("ProfessionalTemplateAssembler", results)
            except ImportError as e:
                self._record_error(f"ProfessionalTemplateAssembler: {str(e)}", results)
            
            # Template Assembly Service
            try:
                from src.core.generation.template_assembly_service import TemplateAssemblyService
                service_registry.register_singleton(
                    TemplateAssemblyService,
                    factory_func=lambda: TemplateAssemblyService(
                        config=self.config_service.get_section("templates")
                    )
                )
                self._record_success("TemplateAssemblyService", results)
            except ImportError as e:
                self._record_error(f"TemplateAssemblyService: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Generation services registration error: {str(e)}", results)
    
    def _register_validation_services(self, results: Dict[str, Any]) -> None:
        """Register validation services."""
        try:
            # Quality Validation Service
            try:
                from src.core.validation.quality_validation_service import QualityValidationService
                service_registry.register_singleton(
                    QualityValidationService,
                    factory_func=lambda: QualityValidationService(
                        config_path=self.config_service.get("quality.config_path", "config/validation/quality_validation_config.yaml")
                    )
                )
                service_registry.register_singleton(IValidationService, factory_func=lambda: service_registry.get(QualityValidationService))
                self._record_success("QualityValidationService", results)
            except ImportError as e:
                self._record_error(f"QualityValidationService: {str(e)}", results)
            
            # Comprehensive Quality Validation Service
            try:
                from src.core.validation.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
                service_registry.register_singleton(
                    ComprehensiveQualityValidationService,
                    factory_func=lambda: ComprehensiveQualityValidationService()
                )
                self._record_success("ComprehensiveQualityValidationService", results)
            except ImportError as e:
                self._record_error(f"ComprehensiveQualityValidationService: {str(e)}", results)
            
            # Evidence First Validator
            try:
                from src.validation.evidence_first_validator import EvidenceFirstValidator
                service_registry.register_singleton(
                    EvidenceFirstValidator,
                    factory_func=lambda: EvidenceFirstValidator()
                )
                self._record_success("EvidenceFirstValidator", results)
            except ImportError as e:
                self._record_error(f"EvidenceFirstValidator: {str(e)}", results)
            
            # Compliance Quality Validator
            try:
                from src.validation.compliance_quality_validator import ComplianceQualityValidator
                service_registry.register_singleton(
                    ComplianceQualityValidator,
                    factory_func=lambda: ComplianceQualityValidator()
                )
                self._record_success("ComplianceQualityValidator", results)
            except ImportError as e:
                self._record_error(f"ComplianceQualityValidator: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Validation services registration error: {str(e)}", results)
    
    def _register_calculation_services(self, results: Dict[str, Any]) -> None:
        """Register calculation services."""
        try:
            # Programmatic Calculation Validator
            try:
                from src.validation.programmatic_calculation_validator import ProgrammaticCalculationValidator
                service_registry.register_singleton(
                    ProgrammaticCalculationValidator,
                    factory_func=lambda: ProgrammaticCalculationValidator()
                )
                self._record_success("ProgrammaticCalculationValidator", results)
            except ImportError as e:
                self._record_error(f"ProgrammaticCalculationValidator: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Calculation services registration error: {str(e)}", results)
    
    def _register_knowledge_services(self, results: Dict[str, Any]) -> None:
        """Register knowledge services."""
        try:
            # Knowledge Graph Vector Service
            try:
                from src.infrastructure.knowledge.knowledge_graph_vector_service import KnowledgeGraphVectorService
                service_registry.register_singleton(
                    KnowledgeGraphVectorService,
                    factory_func=lambda: KnowledgeGraphVectorService()
                )
                self._record_success("KnowledgeGraphVectorService", results)
            except ImportError as e:
                self._record_error(f"KnowledgeGraphVectorService: {str(e)}", results)
            
            # Evidence RAG Service - Skip for now due to complex dependencies
            # try:
            #     from src.infrastructure.knowledge.evidence_rag_service import EvidenceRAGService
            #     service_registry.register_singleton(
            #         EvidenceRAGService,
            #         factory_func=lambda: EvidenceRAGService(
            #             knowledge_graph=None,  # Would need proper initialization
            #             ama_engine=None  # Would need proper initialization
            #         )
            #     )
            #     service_registry.register_singleton(IKnowledgeService, factory_func=lambda: service_registry.get(EvidenceRAGService))
            #     self._record_success("EvidenceRAGService", results)
            # except ImportError as e:
            #     self._record_error(f"EvidenceRAGService: {str(e)}", results)
            
            # Knowledge Base Initializer - Skip for now due to complex dependencies
            # try:
            #     from src.infrastructure.knowledge.knowledge_base_initializer import KnowledgeBaseInitializer
            #     service_registry.register_singleton(
            #         KnowledgeBaseInitializer,
            #         factory_func=lambda: KnowledgeBaseInitializer(
            #             config=None,  # Would need proper AppConfig
            #             ingestion_pipeline=None  # Would need proper IngestionPipeline
            #         )
            #     )
            #     self._record_success("KnowledgeBaseInitializer", results)
            # except ImportError as e:
            #     self._record_error(f"KnowledgeBaseInitializer: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Knowledge services registration error: {str(e)}", results)
    
    def _register_storage_services(self, results: Dict[str, Any]) -> None:
        """Register additional storage services."""
        # Most storage services are already registered in infrastructure
        pass
    
    def _register_monitoring_services(self, results: Dict[str, Any]) -> None:
        """Register additional monitoring services."""
        # Most monitoring services are already registered in infrastructure
        pass
    
    def _register_strategy_services(self, results: Dict[str, Any]) -> None:
        """Register strategy services."""
        try:
            # QA Strategy
            try:
                from src.strategies.qa_strategy import QAStrategy, QAStrategyFactory
                
                # Create QA strategy based on configuration
                qa_provider = self.config_service.get("api.qa_provider", "gemini")
                api_key = None
                
                if qa_provider == "gemini":
                    api_key = self.config_service.get("gemini.api_key")
                elif qa_provider == "openrouter":
                    api_key = self.config_service.get("openrouter.api_key")
                elif qa_provider == "openai":
                    api_key = self.config_service.get("openai.api_key")
                
                if api_key:
                    service_registry.register_singleton(
                        QAStrategy,
                        factory_func=lambda: QAStrategyFactory.create_hybrid_strategy(
                            retrieval_type="keyword",
                            llm_type=qa_provider,
                            api_key=api_key
                        )
                    )
                    self._record_success("QAStrategy", results)
                else:
                    self._record_error(f"QAStrategy: No API key configured for provider {qa_provider}", results)
                    
            except ImportError as e:
                self._record_error(f"QAStrategy: {str(e)}", results)
            
            # Embedding Strategy
            try:
                from src.strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
                
                embedding_provider = self.config_service.get("api.embedding_provider", "local")
                
                if embedding_provider == "local":
                    service_registry.register_singleton(
                        EmbeddingStrategy,
                        factory_func=lambda: EmbeddingStrategyFactory.create_local_strategy()
                    )
                    self._record_success("EmbeddingStrategy", results)
                elif embedding_provider == "openai":
                    openai_api_key = self.config_service.get("openai.api_key")
                    if openai_api_key:
                        service_registry.register_singleton(
                            EmbeddingStrategy,
                            factory_func=lambda: EmbeddingStrategyFactory.create_openai_strategy(
                                api_key=openai_api_key
                            )
                        )
                        self._record_success("EmbeddingStrategy", results)
                    else:
                        self._record_error("EmbeddingStrategy: OpenAI API key not configured", results)
                        
            except ImportError as e:
                self._record_error(f"EmbeddingStrategy: {str(e)}", results)
                
        except Exception as e:
            self._record_error(f"Strategy services registration error: {str(e)}", results)
    
    def _record_success(self, service_name: str, results: Dict[str, Any]) -> None:
        """Record successful service registration."""
        results["successful_registrations"] += 1
        results["total_services"] += 1
        results["registered_services"].append(service_name)
        extraction_logger.debug(f"Successfully registered service: {service_name}")
    
    def _record_error(self, error_message: str, results: Dict[str, Any]) -> None:
        """Record service registration error."""
        results["failed_registrations"] += 1
        results["total_services"] += 1
        results["errors"].append(error_message)
        extraction_logger.warning(f"Service registration error: {error_message}")
    
    def get_service_health_report(self) -> Dict[str, Any]:
        """Get comprehensive service health report."""
        try:
            service_health = service_registry.get_service_health()
            registered_services = service_registry.get_registered_services()
            
            return {
                "service_registry_health": service_health,
                "registered_services": registered_services,
                "configuration_status": {
                    "environment": self.config_service.environment.value,
                    "validation_errors": self.config_service.validate_configuration()
                },
                "registration_errors": self.registration_errors
            }
            
        except Exception as e:
            extraction_logger.error(f"Failed to generate service health report: {str(e)}")
            return {
                "error": f"Failed to generate health report: {str(e)}",
                "service_registry_health": {"health_status": "unknown"},
                "registered_services": {},
                "configuration_status": {"validation_errors": [str(e)]},
                "registration_errors": self.registration_errors
            }
    
    def test_service_instantiation(self) -> Dict[str, Any]:
        """Test that all registered services can be instantiated."""
        test_results = {
            "total_services": 0,
            "successful_instantiations": 0,
            "failed_instantiations": 0,
            "errors": []
        }
        
        registered_services = service_registry.get_registered_services()
        
        for service_name, service_info in registered_services.items():
            test_results["total_services"] += 1
            
            try:
                # Try to get the service (this will instantiate it if it's a singleton)
                service_type = None
                for registered_type in service_registry._services.keys():
                    if registered_type.__name__ == service_name:
                        service_type = registered_type
                        break
                
                if service_type:
                    instance = service_registry.get(service_type)
                    if instance:
                        test_results["successful_instantiations"] += 1
                        extraction_logger.debug(f"Successfully instantiated service: {service_name}")
                    else:
                        test_results["failed_instantiations"] += 1
                        test_results["errors"].append(f"Service {service_name} returned None instance")
                else:
                    test_results["failed_instantiations"] += 1
                    test_results["errors"].append(f"Could not find service type for {service_name}")
                    
            except Exception as e:
                test_results["failed_instantiations"] += 1
                error_msg = f"Failed to instantiate service {service_name}: {str(e)}"
                test_results["errors"].append(error_msg)
                extraction_logger.error(error_msg)
        
        return test_results


def initialize_service_container(config_directory: str = "config") -> ServiceRegistrationManager:
    """
    Initialize the service container with all backend services.
    
    Args:
        config_directory: Directory containing configuration files
        
    Returns:
        ServiceRegistrationManager instance
    """
    try:
        # Create configuration service
        config_service = create_configuration_service(config_directory=config_directory)
        
        # Create service registration manager
        registration_manager = ServiceRegistrationManager(config_service=config_service)
        
        # Register all services
        registration_results = registration_manager.register_all_services()
        
        extraction_logger.info(
            f"Service container initialized: {registration_results['successful_registrations']} services registered, "
            f"{registration_results['failed_registrations']} failed"
        )
        
        if registration_results["errors"]:
            extraction_logger.warning(f"Service registration errors: {registration_results['errors']}")
        
        return registration_manager
        
    except Exception as e:
        extraction_logger.error(f"Failed to initialize service container: {str(e)}")
        raise ServiceRegistrationError(f"Failed to initialize service container: {str(e)}")


def get_registered_service(service_type: Type) -> Any:
    """
    Get a registered service instance.
    
    Args:
        service_type: Type of service to retrieve
        
    Returns:
        Service instance
        
    Raises:
        ValueError: If service is not registered
    """
    return service_registry.get(service_type)


def is_service_registered(service_type: Type) -> bool:
    """
    Check if a service type is registered.
    
    Args:
        service_type: Type of service to check
        
    Returns:
        True if service is registered, False otherwise
    """
    return service_registry.is_registered(service_type)


# Global service registration manager
_registration_manager: Optional[ServiceRegistrationManager] = None


def get_registration_manager() -> ServiceRegistrationManager:
    """Get the global service registration manager."""
    global _registration_manager
    if _registration_manager is None:
        _registration_manager = initialize_service_container()
    return _registration_manager


def reset_registration_manager() -> None:
    """Reset the global service registration manager (useful for testing)."""
    global _registration_manager
    _registration_manager = None
    service_registry.clear()