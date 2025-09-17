"""
Service registry for dependency management and loose coupling.

This module provides a service registry pattern for managing dependencies
and enabling loose coupling between services.
"""

import asyncio
from typing import Dict, Any, Optional, Type, TypeVar, Callable, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from src.core.exceptions import ConfigurationError
from src.infrastructure.monitoring.structured_logger import system_logger


T = TypeVar('T')


class ServiceLifecycle(Enum):
    """Service lifecycle states."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """Describes how a service should be created and managed."""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory_func: Optional[Callable] = None
    lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    dependencies: List[Type] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class IServiceRegistry(ABC):
    """Interface for service registry."""
    
    @abstractmethod
    def register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory_func: Optional[Callable[[], T]] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
        dependencies: Optional[List[Type]] = None
    ) -> None:
        """Register a service."""
        pass
    
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        """Get service instance."""
        pass
    
    @abstractmethod
    async def get_async(self, service_type: Type[T]) -> T:
        """Get service instance asynchronously."""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered."""
        pass


class ServiceRegistry(IServiceRegistry):
    """Service registry implementation with dependency injection."""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._initialization_lock = asyncio.Lock()
    
    def register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory_func: Optional[Callable[[], T]] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
        dependencies: Optional[List[Type]] = None
    ) -> None:
        """Register a service with the registry."""
        if service_type in self._services:
            system_logger.warning(
                f"Service {service_type.__name__} is already registered, overriding",
                extra_data={"service_type": service_type.__name__}
            )
        
        # Validate registration parameters
        if implementation_type is None and factory_func is None:
            implementation_type = service_type
        
        if implementation_type and factory_func:
            raise ConfigurationError(
                f"Cannot specify both implementation_type and factory_func for {service_type.__name__}"
            )
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type,
            factory_func=factory_func,
            lifecycle=lifecycle,
            dependencies=dependencies or []
        )
        
        self._services[service_type] = descriptor
        
        system_logger.info(
            f"Registered service {service_type.__name__}",
            extra_data={
                "service_type": service_type.__name__,
                "implementation_type": implementation_type.__name__ if implementation_type else None,
                "lifecycle": lifecycle.value,
                "dependencies": [dep.__name__ for dep in dependencies] if dependencies else []
            }
        )
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance synchronously."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_async(service_type))
        except RuntimeError:
            # No event loop running, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.get_async(service_type))
            finally:
                loop.close()
    
    async def get_async(self, service_type: Type[T]) -> T:
        """Get service instance asynchronously."""
        if not self.is_registered(service_type):
            raise ConfigurationError(
                f"Service {service_type.__name__} is not registered",
                context={"service_type": service_type.__name__}
            )
        
        descriptor = self._services[service_type]
        
        # Handle different lifecycles
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            return await self._get_singleton(service_type, descriptor)
        elif descriptor.lifecycle == ServiceLifecycle.SCOPED:
            return await self._get_scoped(service_type, descriptor)
        else:  # TRANSIENT
            return await self._create_instance(descriptor)
    
    async def _get_singleton(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Get singleton instance."""
        if service_type not in self._instances:
            async with self._initialization_lock:
                # Double-check locking pattern
                if service_type not in self._instances:
                    instance = await self._create_instance(descriptor)
                    self._instances[service_type] = instance
        
        return self._instances[service_type]
    
    async def _get_scoped(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Get scoped instance."""
        if self._current_scope is None:
            raise ConfigurationError(
                f"No active scope for scoped service {service_type.__name__}",
                context={"service_type": service_type.__name__}
            )
        
        if self._current_scope not in self._scoped_instances:
            self._scoped_instances[self._current_scope] = {}
        
        scope_instances = self._scoped_instances[self._current_scope]
        
        if service_type not in scope_instances:
            instance = await self._create_instance(descriptor)
            scope_instances[service_type] = instance
        
        return scope_instances[service_type]
    
    async def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create service instance with dependency injection."""
        try:
            # Resolve dependencies
            resolved_dependencies = []
            for dep_type in descriptor.dependencies:
                dependency = await self.get_async(dep_type)
                resolved_dependencies.append(dependency)
            
            # Create instance
            if descriptor.factory_func:
                if asyncio.iscoroutinefunction(descriptor.factory_func):
                    instance = await descriptor.factory_func(*resolved_dependencies)
                else:
                    instance = descriptor.factory_func(*resolved_dependencies)
            else:
                instance = descriptor.implementation_type(*resolved_dependencies)
            
            system_logger.debug(
                f"Created instance of {descriptor.service_type.__name__}",
                extra_data={
                    "service_type": descriptor.service_type.__name__,
                    "lifecycle": descriptor.lifecycle.value,
                    "dependencies_count": len(resolved_dependencies)
                }
            )
            
            return instance
            
        except Exception as e:
            system_logger.error(
                f"Failed to create instance of {descriptor.service_type.__name__}",
                error=e,
                extra_data={
                    "service_type": descriptor.service_type.__name__,
                    "dependencies": [dep.__name__ for dep in descriptor.dependencies]
                }
            )
            raise ConfigurationError(
                f"Failed to create instance of {descriptor.service_type.__name__}: {str(e)}",
                context={"service_type": descriptor.service_type.__name__},
                cause=e
            )
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered."""
        return service_type in self._services
    
    def create_scope(self, scope_id: str) -> 'ServiceScope':
        """Create a new service scope."""
        return ServiceScope(self, scope_id)
    
    def _enter_scope(self, scope_id: str):
        """Enter a service scope."""
        self._current_scope = scope_id
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}
    
    def _exit_scope(self, scope_id: str):
        """Exit a service scope."""
        if self._current_scope == scope_id:
            self._current_scope = None
        
        # Clean up scoped instances
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
    
    def get_registered_services(self) -> List[str]:
        """Get list of registered service names."""
        return [service_type.__name__ for service_type in self._services.keys()]
    
    def clear(self):
        """Clear all registrations and instances."""
        self._services.clear()
        self._instances.clear()
        self._scoped_instances.clear()
        self._current_scope = None


class ServiceScope:
    """Context manager for service scopes."""
    
    def __init__(self, registry: ServiceRegistry, scope_id: str):
        self.registry = registry
        self.scope_id = scope_id
    
    def __enter__(self):
        self.registry._enter_scope(self.scope_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.registry._exit_scope(self.scope_id)


# Global service registry instance
service_registry = ServiceRegistry()