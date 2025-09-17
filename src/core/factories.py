"""
Service factory implementations for the QME system.

This module provides factory classes for creating and configuring service instances
with proper dependency injection and configuration management.
"""

from typing import Dict, Any, Optional, Type, TypeVar
from abc import ABC, abstractmethod
import importlib
import logging
from dataclasses import dataclass

from .interfaces import (
    IExtractionService, IValidationService, IGenerationService,
    ICalculationService, IKnowledgeService, IStorageService, IMonitoringService
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceConfig:
    """Configuration for service instantiation."""
    service_type: str
    implementation_class: str
    module_path: str
    config: Dict[str, Any]
    dependencies: Optional[Dict[str, str]] = None


class ServiceFactory(ABC):
    """Abstract base class for service factories."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._instances: Dict[str, Any] = {}
        self._service_configs: Dict[str, ServiceConfig] = {}
    
    @abstractmethod
    def create_service(self, service_type: str, **kwargs) -> Any:
        """Create a service instance."""
        pass
    
    def register_service_config(self, service_name: str, service_config: ServiceConfig):
        """Register a service configuration."""
        self._service_configs[service_name] = service_config
    
    def get_service(self, service_name: str, **kwargs) -> Any:
        """Get or create a service instance (singleton pattern)."""
        if service_name not in self._instances:
            self._instances[service_name] = self.create_service(service_name, **kwargs)
        return self._instances[service_name]
    
    def _load_class(self, module_path: str, class_name: str) -> Type:
        """Dynamically load a class from module path."""
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load class {class_name} from {module_path}: {e}")
            raise


class ExtractionServiceFactory(ServiceFactory):
    """Factory for extraction services."""
    
    def create_service(self, service_type: str, **kwargs) -> IExtractionService:
        """Create an extraction service instance."""
        if service_type not in self._service_configs:
            raise ValueError(f"Unknown extraction service type: {service_type}")
        
        config = self._service_configs[service_type]
        service_class = self._load_class(config.module_path, config.implementation_class)
        
        # Merge factory config with service-specific config and kwargs
        service_config = {**self.config, **config.config, **kwargs}
        
        logger.info(f"Creating extraction service: {service_type}")
        return service_class(**service_config)


class ValidationServiceFactory(ServiceFactory):
    """Factory for validation services."""
    
    def create_service(self, service_type: str, **kwargs) -> IValidationService:
        """Create a validation service instance."""
        if service_type not in self._service_configs:
            raise ValueError(f"Unknown validation service type: {service_type}")
        
        config = self._service_configs[service_type]
        service_class = self._load_class(config.module_path, config.implementation_class)
        
        service_config = {**self.config, **config.config, **kwargs}
        
        logger.info(f"Creating validation service: {service_type}")
        return service_class(**service_config)


class GenerationServiceFactory(ServiceFactory):
    """Factory for generation services."""
    
    def create_service(self, service_type: str, **kwargs) -> IGenerationService:
        """Create a generation service instance."""
        if service_type not in self._service_configs:
            raise ValueError(f"Unknown generation service type: {service_type}")
        
        config = self._service_configs[service_type]
        service_class = self._load_class(config.module_path, config.implementation_class)
        
        service_config = {**self.config, **config.config, **kwargs}
        
        logger.info(f"Creating generation service: {service_type}")
        return service_class(**service_config)


class CalculationServiceFactory(ServiceFactory):
    """Factory for calculation services."""
    
    def create_service(self, service_type: str, **kwargs) -> ICalculationService:
        """Create a calculation service instance."""
        if service_type not in self._service_configs:
            raise ValueError(f"Unknown calculation service type: {service_type}")
        
        config = self._service_configs[service_type]
        service_class = self._load_class(config.module_path, config.implementation_class)
        
        service_config = {**self.config, **config.config, **kwargs}
        
        logger.info(f"Creating calculation service: {service_type}")
        return service_class(**service_config)


class ServiceRegistry:
    """Central registry for all service factories and instances."""
    
    def __init__(self, global_config: Dict[str, Any]):
        self.global_config = global_config
        self._factories: Dict[str, ServiceFactory] = {}
        self._initialize_factories()
    
    def _initialize_factories(self):
        """Initialize all service factories."""
        self._factories['extraction'] = ExtractionServiceFactory(self.global_config)
        self._factories['validation'] = ValidationServiceFactory(self.global_config)
        self._factories['generation'] = GenerationServiceFactory(self.global_config)
        self._factories['calculation'] = CalculationServiceFactory(self.global_config)
    
    def register_service_configs(self, service_configs: Dict[str, Dict[str, ServiceConfig]]):
        """Register service configurations for all factories."""
        for factory_type, configs in service_configs.items():
            if factory_type in self._factories:
                for service_name, config in configs.items():
                    self._factories[factory_type].register_service_config(service_name, config)
    
    def get_service(self, factory_type: str, service_name: str, **kwargs) -> Any:
        """Get a service instance from the appropriate factory."""
        if factory_type not in self._factories:
            raise ValueError(f"Unknown factory type: {factory_type}")
        
        return self._factories[factory_type].get_service(service_name, **kwargs)
    
    def get_extraction_service(self, service_name: str, **kwargs) -> IExtractionService:
        """Get an extraction service instance."""
        return self.get_service('extraction', service_name, **kwargs)
    
    def get_validation_service(self, service_name: str, **kwargs) -> IValidationService:
        """Get a validation service instance."""
        return self.get_service('validation', service_name, **kwargs)
    
    def get_generation_service(self, service_name: str, **kwargs) -> IGenerationService:
        """Get a generation service instance."""
        return self.get_service('generation', service_name, **kwargs)
    
    def get_calculation_service(self, service_name: str, **kwargs) -> ICalculationService:
        """Get a calculation service instance."""
        return self.get_service('calculation', service_name, **kwargs)


def create_default_service_registry(config: Dict[str, Any]) -> ServiceRegistry:
    """Create a service registry with default service configurations."""
    registry = ServiceRegistry(config)
    
    # Default service configurations
    service_configs = {
        'extraction': {
            'document_processor': ServiceConfig(
                service_type='document_processor',
                implementation_class='DocumentProcessor',
                module_path='src.core.extraction.document_processor',
                config={}
            ),
            'field_extractor': ServiceConfig(
                service_type='field_extractor',
                implementation_class='FieldExtractionService',
                module_path='src.core.extraction.field_extraction_service',
                config={}
            ),
            'openrouter_extractor': ServiceConfig(
                service_type='openrouter_extractor',
                implementation_class='OpenRouterExtractionService',
                module_path='src.core.extraction.openrouter_extraction_service',
                config={}
            )
        },
        'validation': {
            'qme_validator': ServiceConfig(
                service_type='qme_validator',
                implementation_class='QMEFieldValidator',
                module_path='src.core.validation.qme_field_validator',
                config={}
            ),
            'quality_validator': ServiceConfig(
                service_type='quality_validator',
                implementation_class='QualityValidationService',
                module_path='src.core.validation.quality_validation_service',
                config={}
            ),
            'rules_engine': ServiceConfig(
                service_type='rules_engine',
                implementation_class='AdvancedQMERulesEngine',
                module_path='src.core.validation.advanced_qme_rules_engine',
                config={}
            )
        },
        'generation': {
            'template_assembler': ServiceConfig(
                service_type='template_assembler',
                implementation_class='TemplateAssemblyService',
                module_path='src.core.generation.template_assembly_service',
                config={}
            ),
            'content_generator': ServiceConfig(
                service_type='content_generator',
                implementation_class='IntelligentContentGenerator',
                module_path='src.core.generation.intelligent_content_generator',
                config={}
            ),
            'qme_generator': ServiceConfig(
                service_type='qme_generator',
                implementation_class='EnhancedQMEGenerator',
                module_path='src.core.generation.enhanced_qme_generator',
                config={}
            )
        },
        'calculation': {
            'impairment_calculator': ServiceConfig(
                service_type='impairment_calculator',
                implementation_class='EnhancedImpairmentCalculator',
                module_path='src.core.calculation.enhanced_impairment_calculator',
                config={}
            )
        }
    }
    
    registry.register_service_configs(service_configs)
    return registry