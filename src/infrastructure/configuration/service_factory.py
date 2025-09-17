"""
Service Factory

This module provides a high-level factory interface for creating and accessing
services through the dependency injection container.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Union
from dataclasses import dataclass

# Import service registry and registration
from src.infrastructure.configuration.service_registry import service_registry, get_service
from src.infrastructure.configuration.service_registration import (
    get_registration_manager,
    get_registered_service,
    is_service_registered
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

T = TypeVar('T')


@dataclass
class ServiceFactoryConfig:
    """Configuration for service factory."""
    auto_initialize: bool = True
    validate_on_creation: bool = True
    enable_fallbacks: bool = True
    log_service_access: bool = False


class ServiceFactoryError(Exception):
    """Service factory related errors."""
    pass


class ServiceFactory:
    """
    High-level factory for creating and accessing services.
    
    Features:
    - Automatic service initialization
    - Interface-based service access
    - Service validation and health checking
    - Fallback mechanisms for missing services
    - Service lifecycle management
    """
    
    def __init__(self, config: Optional[ServiceFactoryConfig] = None):
        """Initialize the service factory."""
        self.config = config or ServiceFactoryConfig()
        self._initialized = False
        self._initialization_errors: list = []
        
        if self.config.auto_initialize:
            self.initialize()
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the service factory and register all services.
        
        Returns:
            Dictionary with initialization results
        """
        if self._initialized:
            extraction_logger.debug("Service factory already initialized")
            return {"status": "already_initialized"}
        
        try:
            # Get registration manager and ensure services are registered
            registration_manager = get_registration_manager()
            
            # Get registration results
            health_report = registration_manager.get_service_health_report()
            
            # Test service instantiation if validation is enabled
            instantiation_results = None
            if self.config.validate_on_creation:
                instantiation_results = registration_manager.test_service_instantiation()
            
            self._initialized = True
            
            initialization_results = {
                "status": "initialized",
                "service_health": health_report,
                "instantiation_results": instantiation_results,
                "total_registered_services": len(service_registry.get_registered_services())
            }
            
            extraction_logger.info(
                f"Service factory initialized successfully with {initialization_results['total_registered_services']} services"
            )
            
            return initialization_results
            
        except Exception as e:
            error_msg = f"Failed to initialize service factory: {str(e)}"
            self._initialization_errors.append(error_msg)
            extraction_logger.error(error_msg)
            raise ServiceFactoryError(error_msg)
    
    def get_extraction_service(self) -> IExtractionService:
        """Get extraction service instance."""
        return self._get_service_with_fallback(
            IExtractionService,
            "extraction service",
            self._create_fallback_extraction_service
        )
    
    def get_validation_service(self) -> IValidationService:
        """Get validation service instance."""
        return self._get_service_with_fallback(
            IValidationService,
            "validation service",
            self._create_fallback_validation_service
        )
    
    def get_generation_service(self) -> IGenerationService:
        """Get generation service instance."""
        return self._get_service_with_fallback(
            IGenerationService,
            "generation service",
            self._create_fallback_generation_service
        )
    
    def get_calculation_service(self) -> ICalculationService:
        """Get calculation service instance."""
        return self._get_service_with_fallback(
            ICalculationService,
            "calculation service",
            self._create_fallback_calculation_service
        )
    
    def get_knowledge_service(self) -> IKnowledgeService:
        """Get knowledge service instance."""
        return self._get_service_with_fallback(
            IKnowledgeService,
            "knowledge service",
            self._create_fallback_knowledge_service
        )
    
    def get_storage_service(self) -> IStorageService:
        """Get storage service instance."""
        return self._get_service_with_fallback(
            IStorageService,
            "storage service",
            self._create_fallback_storage_service
        )
    
    def get_monitoring_service(self) -> IMonitoringService:
        """Get monitoring service instance."""
        return self._get_service_with_fallback(
            IMonitoringService,
            "monitoring service",
            self._create_fallback_monitoring_service
        )
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get service instance by type.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            ServiceFactoryError: If service cannot be retrieved
        """
        if not self._initialized:
            self.initialize()
        
        try:
            if self.config.log_service_access:
                extraction_logger.debug(f"Accessing service: {service_type.__name__}")
            
            return get_registered_service(service_type)
            
        except Exception as e:
            error_msg = f"Failed to get service {service_type.__name__}: {str(e)}"
            extraction_logger.error(error_msg)
            raise ServiceFactoryError(error_msg)
    
    def try_get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to get service instance, return None if not available.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            Service instance or None
        """
        try:
            return self.get_service(service_type)
        except Exception:
            return None
    
    def is_service_available(self, service_type: Type) -> bool:
        """
        Check if service is available.
        
        Args:
            service_type: Type of service to check
            
        Returns:
            True if service is available, False otherwise
        """
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                return False
        
        return is_service_registered(service_type)
    
    def get_available_services(self) -> Dict[str, Any]:
        """Get information about all available services."""
        if not self._initialized:
            self.initialize()
        
        return service_registry.get_registered_services()
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get service health information."""
        if not self._initialized:
            self.initialize()
        
        try:
            registration_manager = get_registration_manager()
            return registration_manager.get_service_health_report()
        except Exception as e:
            return {
                "error": f"Failed to get service health: {str(e)}",
                "status": "unhealthy"
            }
    
    def validate_services(self) -> Dict[str, Any]:
        """Validate all registered services."""
        if not self._initialized:
            self.initialize()
        
        try:
            registration_manager = get_registration_manager()
            return registration_manager.test_service_instantiation()
        except Exception as e:
            return {
                "error": f"Failed to validate services: {str(e)}",
                "total_services": 0,
                "successful_instantiations": 0,
                "failed_instantiations": 0,
                "errors": [str(e)]
            }
    
    def _get_service_with_fallback(self, 
                                  service_type: Type[T], 
                                  service_name: str,
                                  fallback_factory: callable) -> T:
        """Get service with fallback mechanism."""
        try:
            return self.get_service(service_type)
        except Exception as e:
            if self.config.enable_fallbacks:
                extraction_logger.warning(
                    f"Failed to get {service_name}, using fallback: {str(e)}"
                )
                return fallback_factory()
            else:
                raise ServiceFactoryError(f"Failed to get {service_name}: {str(e)}")
    
    def _create_fallback_extraction_service(self) -> IExtractionService:
        """Create fallback extraction service."""
        from src.core.interfaces import IExtractionService
        
        class FallbackExtractionService(IExtractionService):
            def extract_fields(self, document: Any, field_definitions: list) -> Dict[str, Any]:
                extraction_logger.warning("Using fallback extraction service")
                return {"error": "Extraction service not available", "fields": {}}
            
            def get_supported_formats(self) -> list:
                return ["pdf", "docx", "txt"]
            
            def validate_document(self, document: Any) -> bool:
                return True
        
        return FallbackExtractionService()
    
    def _create_fallback_validation_service(self) -> IValidationService:
        """Create fallback validation service."""
        from src.core.interfaces import IValidationService
        
        class FallbackValidationService(IValidationService):
            def validate_content(self, content: Any, rules: list) -> Dict[str, Any]:
                extraction_logger.warning("Using fallback validation service")
                return {"valid": True, "score": 0.5, "errors": [], "warnings": ["Validation service not available"]}
            
            def get_validation_rules(self) -> list:
                return []
            
            def validate_structure(self, structure: Any) -> bool:
                return True
        
        return FallbackValidationService()
    
    def _create_fallback_generation_service(self) -> IGenerationService:
        """Create fallback generation service."""
        from src.core.interfaces import IGenerationService
        
        class FallbackGenerationService(IGenerationService):
            def generate_content(self, template: Any, data: Dict[str, Any]) -> Any:
                extraction_logger.warning("Using fallback generation service")
                return {"error": "Generation service not available", "content": ""}
            
            def get_supported_templates(self) -> list:
                return []
            
            def validate_template(self, template: Any) -> bool:
                return False
        
        return FallbackGenerationService()
    
    def _create_fallback_calculation_service(self) -> ICalculationService:
        """Create fallback calculation service."""
        from src.core.interfaces import ICalculationService
        
        class FallbackCalculationService(ICalculationService):
            def calculate_impairment(self, data: Dict[str, Any]) -> Dict[str, Any]:
                extraction_logger.warning("Using fallback calculation service")
                return {"error": "Calculation service not available", "result": 0}
            
            def get_calculation_methods(self) -> list:
                return []
            
            def validate_input_data(self, data: Dict[str, Any]) -> bool:
                return False
        
        return FallbackCalculationService()
    
    def _create_fallback_knowledge_service(self) -> IKnowledgeService:
        """Create fallback knowledge service."""
        from src.core.interfaces import IKnowledgeService
        
        class FallbackKnowledgeService(IKnowledgeService):
            def query_knowledge_base(self, query: str) -> Dict[str, Any]:
                extraction_logger.warning("Using fallback knowledge service")
                return {"error": "Knowledge service not available", "results": []}
            
            def add_knowledge(self, knowledge: Dict[str, Any]) -> bool:
                return False
            
            def get_knowledge_stats(self) -> Dict[str, Any]:
                return {"total_entries": 0, "status": "unavailable"}
        
        return FallbackKnowledgeService()
    
    def _create_fallback_storage_service(self) -> IStorageService:
        """Create fallback storage service."""
        from src.core.interfaces import IStorageService
        
        class FallbackStorageService(IStorageService):
            def store_document(self, document: Any, metadata: Dict[str, Any]) -> str:
                extraction_logger.warning("Using fallback storage service")
                return "fallback_storage_id"
            
            def retrieve_document(self, document_id: str) -> Any:
                return None
            
            def delete_document(self, document_id: str) -> bool:
                return False
            
            def list_documents(self) -> list:
                return []
        
        return FallbackStorageService()
    
    def _create_fallback_monitoring_service(self) -> IMonitoringService:
        """Create fallback monitoring service."""
        from src.core.interfaces import IMonitoringService
        
        class FallbackMonitoringService(IMonitoringService):
            def log_event(self, event: Dict[str, Any]) -> None:
                extraction_logger.warning("Using fallback monitoring service")
            
            def get_metrics(self) -> Dict[str, Any]:
                return {"status": "monitoring_unavailable"}
            
            def get_health_status(self) -> Dict[str, Any]:
                return {"status": "unknown", "services": []}
        
        return FallbackMonitoringService()


# Global service factory instance
_service_factory: Optional[ServiceFactory] = None


def get_service_factory(config: Optional[ServiceFactoryConfig] = None) -> ServiceFactory:
    """
    Get the global service factory instance.
    
    Args:
        config: Optional configuration for service factory
        
    Returns:
        ServiceFactory instance
    """
    global _service_factory
    if _service_factory is None:
        _service_factory = ServiceFactory(config=config)
    return _service_factory


def reset_service_factory() -> None:
    """Reset the global service factory (useful for testing)."""
    global _service_factory
    _service_factory = None


# Convenience functions for common service access
def get_extraction_service() -> IExtractionService:
    """Get extraction service instance."""
    return get_service_factory().get_extraction_service()


def get_validation_service() -> IValidationService:
    """Get validation service instance."""
    return get_service_factory().get_validation_service()


def get_generation_service() -> IGenerationService:
    """Get generation service instance."""
    return get_service_factory().get_generation_service()


def get_storage_service() -> IStorageService:
    """Get storage service instance."""
    return get_service_factory().get_storage_service()


def get_monitoring_service() -> IMonitoringService:
    """Get monitoring service instance."""
    return get_service_factory().get_monitoring_service()