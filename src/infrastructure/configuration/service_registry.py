"""
Service Registry

This service provides dependency injection and service registration capabilities
for the QME system, enabling loose coupling and testability.
"""

import logging
import threading
from typing import Dict, Any, Type, TypeVar, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

# Optional dependencies with graceful degradation
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)


T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    """Service registration information."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory_func: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: list = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceRegistry:
    """
    Service registry for dependency injection and service management.
    
    Features:
    - Service registration with different lifetimes
    - Dependency injection and resolution
    - Circular dependency detection
    - Service factory functions
    - Thread-safe operations
    - Service health monitoring
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack = set()
        
        extraction_logger.info("Initialized ServiceRegistry")
    
    def register(self, 
                service_type: Type[T],
                implementation_type: Optional[Type[T]] = None,
                factory_func: Optional[Callable[[], T]] = None,
                instance: Optional[T] = None,
                lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                dependencies: Optional[list] = None) -> None:
        """Register a service with the registry."""
        
        with self._lock:
            if sum(x is not None for x in [implementation_type, factory_func, instance]) != 1:
                raise ValueError("Exactly one of implementation_type, factory_func, or instance must be provided")
            
            registration = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                factory_func=factory_func,
                instance=instance,
                lifetime=lifetime,
                dependencies=dependencies or []
            )
            
            self._services[service_type] = registration
            
            # If instance is provided, store it immediately
            if instance is not None:
                self._instances[service_type] = instance
            
            extraction_logger.debug(
                f"Registered service: {service_type.__name__}",
                extra_data={
                    "service_type": service_type.__name__,
                    "lifetime": lifetime.value,
                    "has_dependencies": len(registration.dependencies) > 0
                }
            )
    
    def register_singleton(self, 
                          service_type: Type[T],
                          implementation_type: Optional[Type[T]] = None,
                          factory_func: Optional[Callable[[], T]] = None,
                          instance: Optional[T] = None,
                          dependencies: Optional[list] = None) -> None:
        """Register a singleton service."""
        self.register(
            service_type=service_type,
            implementation_type=implementation_type,
            factory_func=factory_func,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON,
            dependencies=dependencies
        )
    
    def register_transient(self, 
                          service_type: Type[T],
                          implementation_type: Optional[Type[T]] = None,
                          factory_func: Optional[Callable[[], T]] = None,
                          dependencies: Optional[list] = None) -> None:
        """Register a transient service."""
        self.register(
            service_type=service_type,
            implementation_type=implementation_type,
            factory_func=factory_func,
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=dependencies
        )
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance from registry."""
        with self._lock:
            return self._resolve_service(service_type)
    
    def try_get(self, service_type: Type[T]) -> Optional[T]:
        """Try to get service instance, return None if not registered."""
        try:
            return self.get(service_type)
        except Exception:
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service type is registered."""
        with self._lock:
            return service_type in self._services
    
    def unregister(self, service_type: Type) -> bool:
        """Unregister a service."""
        with self._lock:
            if service_type in self._services:
                del self._services[service_type]
                if service_type in self._instances:
                    del self._instances[service_type]
                
                extraction_logger.debug(f"Unregistered service: {service_type.__name__}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._instances.clear()
            extraction_logger.info("Cleared all registered services")
    
    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered services."""
        with self._lock:
            services_info = {}
            
            for service_type, registration in self._services.items():
                services_info[service_type.__name__] = {
                    "service_type": service_type.__name__,
                    "implementation_type": registration.implementation_type.__name__ if registration.implementation_type else None,
                    "has_factory": registration.factory_func is not None,
                    "has_instance": registration.instance is not None,
                    "lifetime": registration.lifetime.value,
                    "dependencies": [dep.__name__ if hasattr(dep, '__name__') else str(dep) for dep in registration.dependencies],
                    "is_instantiated": service_type in self._instances
                }
            
            return services_info
    
    def _resolve_service(self, service_type: Type[T]) -> T:
        """Resolve service instance with dependency injection."""
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            raise RuntimeError(f"Circular dependency detected for service: {service_type.__name__}")
        
        if service_type not in self._services:
            raise ValueError(f"Service not registered: {service_type.__name__}")
        
        registration = self._services[service_type]
        
        # Return existing instance for singletons
        if registration.lifetime == ServiceLifetime.SINGLETON and service_type in self._instances:
            return self._instances[service_type]
        
        # Add to resolution stack to detect circular dependencies
        self._resolution_stack.add(service_type)
        
        try:
            instance = self._create_instance(registration)
            
            # Store singleton instances
            if registration.lifetime == ServiceLifetime.SINGLETON:
                self._instances[service_type] = instance
            
            return instance
            
        finally:
            # Remove from resolution stack
            self._resolution_stack.discard(service_type)
    
    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create service instance."""
        try:
            # Use pre-created instance
            if registration.instance is not None:
                return registration.instance
            
            # Use factory function
            if registration.factory_func is not None:
                # Resolve dependencies for factory function
                dependencies = self._resolve_dependencies(registration.dependencies)
                if dependencies:
                    return registration.factory_func(*dependencies)
                else:
                    return registration.factory_func()
            
            # Use implementation type
            if registration.implementation_type is not None:
                # Resolve dependencies for constructor
                dependencies = self._resolve_dependencies(registration.dependencies)
                if dependencies:
                    return registration.implementation_type(*dependencies)
                else:
                    return registration.implementation_type()
            
            raise ValueError(f"No way to create instance for service: {registration.service_type.__name__}")
            
        except Exception as e:
            extraction_logger.error(
                f"Failed to create instance for service: {registration.service_type.__name__}",
                extra_data={"error": str(e)}
            )
            raise
    
    def _resolve_dependencies(self, dependencies: list) -> list:
        """Resolve service dependencies."""
        resolved_dependencies = []
        
        for dependency in dependencies:
            if isinstance(dependency, type):
                # Dependency is a service type
                resolved_dependencies.append(self._resolve_service(dependency))
            else:
                # Dependency is a value
                resolved_dependencies.append(dependency)
        
        return resolved_dependencies
    
    def validate_registrations(self) -> list:
        """Validate all service registrations."""
        validation_errors = []
        
        with self._lock:
            for service_type, registration in self._services.items():
                try:
                    # Check if dependencies are registered
                    for dependency in registration.dependencies:
                        if isinstance(dependency, type) and dependency not in self._services:
                            validation_errors.append(
                                f"Service {service_type.__name__} depends on unregistered service: {dependency.__name__}"
                            )
                    
                    # Try to resolve the service (for singletons only to avoid side effects)
                    if registration.lifetime == ServiceLifetime.SINGLETON:
                        try:
                            self._resolve_service(service_type)
                        except Exception as e:
                            validation_errors.append(
                                f"Failed to resolve service {service_type.__name__}: {str(e)}"
                            )
                
                except Exception as e:
                    validation_errors.append(
                        f"Validation error for service {service_type.__name__}: {str(e)}"
                    )
        
        return validation_errors
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get service registry health information."""
        with self._lock:
            total_services = len(self._services)
            instantiated_services = len(self._instances)
            validation_errors = self.validate_registrations()
            
            return {
                "total_registered_services": total_services,
                "instantiated_services": instantiated_services,
                "validation_errors": validation_errors,
                "health_status": "healthy" if len(validation_errors) == 0 else "unhealthy",
                "services_by_lifetime": {
                    lifetime.value: sum(1 for reg in self._services.values() if reg.lifetime == lifetime)
                    for lifetime in ServiceLifetime
                }
            }


# Global service registry instance
service_registry = ServiceRegistry()


def configure_default_services() -> None:
    """Configure default service registrations."""
    try:
        # Import and register core services
        from src.infrastructure.storage.results_storage_service import ResultsStorageService
        from src.infrastructure.monitoring.comprehensive_logging_service import ComprehensiveLoggingService
        
        # Register core services as singletons
        service_registry.register_singleton(
            ResultsStorageService,
            factory_func=lambda: ResultsStorageService()
        )
        
        service_registry.register_singleton(
            ComprehensiveLoggingService,
            factory_func=lambda: ComprehensiveLoggingService()
        )
        
        extraction_logger.info("Configured default services")
        
    except ImportError as e:
        extraction_logger.warning(f"Some default services could not be registered: {str(e)}")
    except Exception as e:
        extraction_logger.error(f"Failed to configure default services: {str(e)}")


def get_service(service_type: Type[T]) -> T:
    """Convenience function to get service from global registry."""
    return service_registry.get(service_type)


def register_service(service_type: Type[T], 
                    implementation_type: Optional[Type[T]] = None,
                    factory_func: Optional[Callable[[], T]] = None,
                    instance: Optional[T] = None,
                    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
    """Convenience function to register service with global registry."""
    service_registry.register(
        service_type=service_type,
        implementation_type=implementation_type,
        factory_func=factory_func,
        instance=instance,
        lifetime=lifetime
    )