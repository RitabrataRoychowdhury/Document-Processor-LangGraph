"""
Service Registry and Dependency Injection

Provides centralized service management following SOLID principles:
- Single Responsibility: Each service has one clear purpose
- Open/Closed: Services can be extended without modification
- Liskov Substitution: Services implement clear interfaces
- Interface Segregation: Focused service interfaces
- Dependency Inversion: Services depend on abstractions

This registry enables plug-and-play architecture with clear component separation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar, Generic, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from threading import Lock

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed"""
    service_type: Type
    implementation_type: Type
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    dependencies: Optional[Dict[str, str]] = None


class ServiceInterface(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service"""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup service resources"""
        pass
        
    @property
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        pass


class IExtractionService(ServiceInterface):
    """Interface for document extraction services"""
    
    @abstractmethod
    def extract_from_document(self, document_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from a document"""
        pass


class ITemplateAssemblyService(ServiceInterface):
    """Interface for template assembly services"""
    
    @abstractmethod
    def assemble_template(self, template_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Assemble a template from extracted data"""
        pass


class IQualityValidationService(ServiceInterface):
    """Interface for quality validation services"""
    
    @abstractmethod
    def validate_document(self, document_path: str) -> Dict[str, Any]:
        """Validate document quality"""
        pass


class IStorageService(ServiceInterface):
    """Interface for storage services"""
    
    @abstractmethod
    def store_document(self, document_path: str, metadata: Dict[str, Any]) -> bool:
        """Store a document with metadata"""
        pass


class ILoggingService(ServiceInterface):
    """Interface for logging services"""
    
    @abstractmethod
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an event"""
        pass


class ServiceRegistry:
    """
    Central registry for service management and dependency injection.
    
    Provides service registration, resolution, and lifetime management
    following SOLID principles and enabling plug-and-play architecture.
    """
    
    def __init__(self):
        """Initialize the service registry"""
        self._services: Dict[str, ServiceDescriptor] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._current_scope: Optional[str] = None
        
    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceRegistry':
        """
        Register a singleton service.
        
        Args:
            service_type: Interface or base type
            implementation_type: Concrete implementation
            factory: Optional factory function
            
        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type,
            implementation_type,
            ServiceLifetime.SINGLETON,
            factory
        )
        
    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceRegistry':
        """
        Register a transient service (new instance each time).
        
        Args:
            service_type: Interface or base type
            implementation_type: Concrete implementation
            factory: Optional factory function
            
        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type,
            implementation_type,
            ServiceLifetime.TRANSIENT,
            factory
        )
        
    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceRegistry':
        """
        Register a scoped service (one instance per scope).
        
        Args:
            service_type: Interface or base type
            implementation_type: Concrete implementation
            factory: Optional factory function
            
        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type,
            implementation_type,
            ServiceLifetime.SCOPED,
            factory
        )
        
    def _register_service(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        lifetime: ServiceLifetime,
        factory: Optional[Callable[[], T]] = None
    ) -> 'ServiceRegistry':
        """Internal method to register a service"""
        service_name = service_type.__name__
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime,
            factory=factory
        )
        
        with self._lock:
            self._services[service_name] = descriptor
            
        logger.info(f"Registered {lifetime.value} service: {service_name} -> {implementation_type.__name__}")
        return self
        
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        service_name = service_type.__name__
        
        if service_name not in self._services:
            raise ValueError(f"Service {service_name} is not registered")
            
        descriptor = self._services[service_name]
        
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._get_singleton_instance(service_name, descriptor)
        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._get_scoped_instance(service_name, descriptor)
        else:
            raise ValueError(f"Unknown service lifetime: {descriptor.lifetime}")
            
    def _get_singleton_instance(self, service_name: str, descriptor: ServiceDescriptor) -> Any:
        """Get or create singleton instance"""
        with self._lock:
            if service_name not in self._instances:
                self._instances[service_name] = self._create_instance(descriptor)
            return self._instances[service_name]
            
    def _get_scoped_instance(self, service_name: str, descriptor: ServiceDescriptor) -> Any:
        """Get or create scoped instance"""
        if self._current_scope is None:
            raise ValueError("No active scope for scoped service")
            
        scope_key = self._current_scope
        
        with self._lock:
            if scope_key not in self._scoped_instances:
                self._scoped_instances[scope_key] = {}
                
            if service_name not in self._scoped_instances[scope_key]:
                self._scoped_instances[scope_key][service_name] = self._create_instance(descriptor)
                
            return self._scoped_instances[scope_key][service_name]
            
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new service instance"""
        try:
            if descriptor.factory:
                instance = descriptor.factory()
            else:
                # Try to resolve constructor dependencies
                instance = self._create_with_dependencies(descriptor.implementation_type)
                
            # Initialize if it's a ServiceInterface
            if isinstance(instance, ServiceInterface):
                if not instance.initialize():
                    raise RuntimeError(f"Failed to initialize service {descriptor.implementation_type.__name__}")
                    
            logger.debug(f"Created instance of {descriptor.implementation_type.__name__}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create instance of {descriptor.implementation_type.__name__}: {e}")
            raise
            
    def _create_with_dependencies(self, implementation_type: Type) -> Any:
        """Create instance with dependency injection"""
        try:
            # For now, create without dependencies
            # In a full implementation, this would analyze constructor parameters
            # and resolve dependencies recursively
            return implementation_type()
        except Exception as e:
            logger.error(f"Failed to create {implementation_type.__name__} with dependencies: {e}")
            raise
            
    def create_scope(self, scope_id: str) -> 'ServiceScope':
        """
        Create a new service scope.
        
        Args:
            scope_id: Unique identifier for the scope
            
        Returns:
            ServiceScope context manager
        """
        return ServiceScope(self, scope_id)
        
    def _enter_scope(self, scope_id: str) -> None:
        """Enter a service scope"""
        self._current_scope = scope_id
        
    def _exit_scope(self, scope_id: str) -> None:
        """Exit a service scope and cleanup scoped instances"""
        if self._current_scope == scope_id:
            self._current_scope = None
            
        # Cleanup scoped instances
        with self._lock:
            if scope_id in self._scoped_instances:
                for instance in self._scoped_instances[scope_id].values():
                    if isinstance(instance, ServiceInterface):
                        try:
                            instance.cleanup()
                        except Exception as e:
                            logger.error(f"Error cleaning up scoped instance: {e}")
                            
                del self._scoped_instances[scope_id]
                
    def get_service_health(self) -> Dict[str, bool]:
        """
        Get health status of all registered services.
        
        Returns:
            Dictionary mapping service names to health status
        """
        health_status = {}
        
        with self._lock:
            for service_name, instance in self._instances.items():
                if isinstance(instance, ServiceInterface):
                    try:
                        health_status[service_name] = instance.is_healthy
                    except Exception as e:
                        logger.error(f"Error checking health of {service_name}: {e}")
                        health_status[service_name] = False
                else:
                    health_status[service_name] = True  # Assume healthy if not ServiceInterface
                    
        return health_status
        
    def cleanup_all(self) -> None:
        """Cleanup all service instances"""
        with self._lock:
            # Cleanup singleton instances
            for instance in self._instances.values():
                if isinstance(instance, ServiceInterface):
                    try:
                        instance.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up singleton instance: {e}")
                        
            self._instances.clear()
            
            # Cleanup scoped instances
            for scope_instances in self._scoped_instances.values():
                for instance in scope_instances.values():
                    if isinstance(instance, ServiceInterface):
                        try:
                            instance.cleanup()
                        except Exception as e:
                            logger.error(f"Error cleaning up scoped instance: {e}")
                            
            self._scoped_instances.clear()
            
        logger.info("All service instances cleaned up")
        
    def get_registered_services(self) -> Dict[str, ServiceDescriptor]:
        """Get all registered service descriptors"""
        with self._lock:
            return self._services.copy()


class ServiceScope:
    """Context manager for service scopes"""
    
    def __init__(self, registry: ServiceRegistry, scope_id: str):
        """
        Initialize service scope.
        
        Args:
            registry: Service registry
            scope_id: Unique scope identifier
        """
        self.registry = registry
        self.scope_id = scope_id
        
    def __enter__(self) -> 'ServiceScope':
        """Enter the service scope"""
        self.registry._enter_scope(self.scope_id)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the service scope"""
        self.registry._exit_scope(self.scope_id)


# Global service registry instance
service_registry = ServiceRegistry()


def configure_default_services() -> None:
    """Configure default service registrations"""
    from src.infrastructure.storage.results_storage_service import ResultsStorageService
    from src.infrastructure.monitoring.comprehensive_logging_service import ComprehensiveLoggingService
    
    # Register core services as singletons
    service_registry.register_singleton(
        IStorageService,
        ResultsStorageService
    )
    
    service_registry.register_singleton(
        ILoggingService,
        ComprehensiveLoggingService
    )
    
    logger.info("Default services configured")


# Convenience functions
def get_service(service_type: Type[T]) -> T:
    """Get a service instance from the global registry"""
    return service_registry.resolve(service_type)


def register_service(
    service_type: Type[T],
    implementation_type: Type[T],
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
) -> None:
    """Register a service with the global registry"""
    if lifetime == ServiceLifetime.SINGLETON:
        service_registry.register_singleton(service_type, implementation_type)
    elif lifetime == ServiceLifetime.TRANSIENT:
        service_registry.register_transient(service_type, implementation_type)
    elif lifetime == ServiceLifetime.SCOPED:
        service_registry.register_scoped(service_type, implementation_type)