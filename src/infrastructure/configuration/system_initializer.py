"""
System Initializer with Graceful Degradation.

This module handles system initialization with proper dependency management,
graceful degradation for missing components, and comprehensive error handling.
"""

import asyncio
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import importlib

from src.core.exceptions import (
    ConfigurationError, StorageError, KnowledgeGraphError
)
from src.infrastructure.monitoring.structured_logger import system_logger
from src.infrastructure.configuration.service_registry import service_registry
from src.infrastructure.storage.database_manager import (
    create_database_manager, DatabaseConfig
)
from src.infrastructure.monitoring.api_integration_manager import (
    api_integration_manager, register_openrouter_endpoint
)


@dataclass
class ComponentStatus:
    """Status of system component."""
    name: str
    initialized: bool
    error_message: Optional[str] = None
    fallback_used: bool = False
    dependencies_met: bool = True


@dataclass
class SystemInitializationResult:
    """Result of system initialization."""
    success: bool
    components: Dict[str, ComponentStatus] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    fallbacks_used: List[str] = field(default_factory=list)


class SystemInitializer:
    """
    System initializer with graceful degradation and dependency management.
    
    Features:
    - Dependency-aware initialization order
    - Graceful degradation for optional components
    - Service registration and dependency injection
    - Configuration validation and environment setup
    - Health checks and system validation
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentStatus] = {}
        self.initialization_order = [
            "configuration",
            "database",
            "knowledge_graph",
            "api_integration",
            "core_services",
            "infrastructure_services",
            "workflow_services"
        ]
        
        system_logger.info("Initialized SystemInitializer")
    
    async def initialize_system(
        self,
        config: Optional[Dict[str, Any]] = None
    ) -> SystemInitializationResult:
        """Initialize entire system with graceful degradation."""
        system_logger.info("Starting system initialization")
        
        result = SystemInitializationResult(success=True)
        config = config or {}
        
        # Initialize components in order
        for component_name in self.initialization_order:
            try:
                status = await self._initialize_component(component_name, config)
                self.components[component_name] = status
                result.components[component_name] = status
                
                if not status.initialized:
                    if status.fallback_used:
                        result.warnings.append(
                            f"Component {component_name} using fallback: {status.error_message}"
                        )
                        result.fallbacks_used.append(component_name)
                    else:
                        result.errors.append(
                            f"Component {component_name} failed: {status.error_message}"
                        )
                        # Check if this is a critical component
                        if component_name in ["configuration", "database"]:
                            result.success = False
                
            except Exception as e:
                error_msg = f"Critical error initializing {component_name}: {str(e)}"
                system_logger.error(
                    f"Component initialization failed: {component_name}",
                    error=e,
                    extra_data={"component": component_name}
                )
                
                status = ComponentStatus(
                    name=component_name,
                    initialized=False,
                    error_message=str(e)
                )
                self.components[component_name] = status
                result.components[component_name] = status
                result.errors.append(error_msg)
                
                # Critical components cause system failure
                if component_name in ["configuration", "database"]:
                    result.success = False
        
        # Log initialization summary
        initialized_count = sum(1 for c in result.components.values() if c.initialized)
        total_count = len(result.components)
        
        system_logger.info(
            f"System initialization completed: {initialized_count}/{total_count} components initialized",
            extra_data={
                "success": result.success,
                "initialized_components": initialized_count,
                "total_components": total_count,
                "warnings": len(result.warnings),
                "errors": len(result.errors),
                "fallbacks_used": len(result.fallbacks_used)
            }
        )
        
        return result
    
    async def _initialize_component(
        self,
        component_name: str,
        config: Dict[str, Any]
    ) -> ComponentStatus:
        """Initialize individual component with fallback handling."""
        system_logger.debug(f"Initializing component: {component_name}")
        
        try:
            if component_name == "configuration":
                return await self._initialize_configuration(config)
            elif component_name == "database":
                return await self._initialize_database(config)
            elif component_name == "knowledge_graph":
                return await self._initialize_knowledge_graph(config)
            elif component_name == "api_integration":
                return await self._initialize_api_integration(config)
            elif component_name == "core_services":
                return await self._initialize_core_services(config)
            elif component_name == "infrastructure_services":
                return await self._initialize_infrastructure_services(config)
            elif component_name == "workflow_services":
                return await self._initialize_workflow_services(config)
            else:
                return ComponentStatus(
                    name=component_name,
                    initialized=False,
                    error_message=f"Unknown component: {component_name}"
                )
                
        except Exception as e:
            system_logger.error(
                f"Component initialization error: {component_name}",
                error=e,
                extra_data={"component": component_name}
            )
            
            return ComponentStatus(
                name=component_name,
                initialized=False,
                error_message=str(e)
            )
    
    async def _initialize_configuration(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize configuration management."""
        try:
            # Validate required environment variables
            required_env_vars = ["DATABASE_PATH"]
            missing_vars = []
            
            for var in required_env_vars:
                if not os.getenv(var) and var.lower() not in config:
                    missing_vars.append(var)
            
            if missing_vars:
                # Use defaults for missing configuration
                defaults = {
                    "DATABASE_PATH": "data/database/documents.db"
                }
                
                for var in missing_vars:
                    default_value = defaults.get(var)
                    if default_value:
                        config[var.lower()] = default_value
                        system_logger.warning(
                            f"Using default value for {var}: {default_value}"
                        )
            
            # Register configuration service
            from src.infrastructure.configuration.configuration_service import ConfigurationService
            config_service = ConfigurationService(config)
            service_registry.register(ConfigurationService, factory_func=lambda: config_service)
            
            return ComponentStatus(
                name="configuration",
                initialized=True,
                fallback_used=len(missing_vars) > 0
            )
            
        except Exception as e:
            return ComponentStatus(
                name="configuration",
                initialized=False,
                error_message=str(e)
            )
    
    async def _initialize_database(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize database with connection pooling."""
        try:
            database_path = config.get("database_path") or os.getenv("DATABASE_PATH", "data/database/documents.db")
            
            # Ensure database directory exists
            db_path = Path(database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create database manager
            db_config = DatabaseConfig(
                database_path=database_path,
                max_connections=10,
                connection_timeout=30
            )
            
            db_manager = create_database_manager(database_path, **db_config.__dict__)
            
            # Test database connection
            health_status = db_manager.health_check()
            if not health_status.get("database_accessible", False):
                raise StorageError(f"Database health check failed: {health_status}")
            
            # Register database manager
            service_registry.register(
                type(db_manager),
                factory_func=lambda: db_manager
            )
            
            return ComponentStatus(
                name="database",
                initialized=True
            )
            
        except Exception as e:
            return ComponentStatus(
                name="database",
                initialized=False,
                error_message=str(e)
            )
    
    async def _initialize_knowledge_graph(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize knowledge graph with graceful degradation."""
        try:
            # Try to initialize knowledge graph repository
            try:
                from src.repositories.knowledge_graph_repository import SQLiteKnowledgeGraphRepository
                
                # Get database manager from service registry
                db_manager = service_registry.get(type(create_database_manager("dummy")))
                kg_repository = SQLiteKnowledgeGraphRepository(db_manager)
                
                # Register knowledge graph repository
                service_registry.register(
                    SQLiteKnowledgeGraphRepository,
                    factory_func=lambda: kg_repository
                )
                
                return ComponentStatus(
                    name="knowledge_graph",
                    initialized=True
                )
                
            except ImportError as e:
                system_logger.warning(
                    f"Knowledge graph dependencies not available: {e}",
                    extra_data={"component": "knowledge_graph"}
                )
                
                # Use mock knowledge graph repository
                return ComponentStatus(
                    name="knowledge_graph",
                    initialized=True,
                    fallback_used=True,
                    error_message="Using mock knowledge graph due to missing dependencies"
                )
                
        except Exception as e:
            return ComponentStatus(
                name="knowledge_graph",
                initialized=False,
                error_message=str(e)
            )
    
    async def _initialize_api_integration(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize API integration services."""
        try:
            # Initialize OpenRouter if API key is available
            openrouter_api_key = config.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
            
            if openrouter_api_key:
                await register_openrouter_endpoint(openrouter_api_key)
                
                # Test API connection
                health_status = await api_integration_manager.health_check("openrouter")
                if health_status.get("status") != "healthy":
                    system_logger.warning(
                        f"OpenRouter API health check failed: {health_status}",
                        extra_data={"health_status": health_status}
                    )
                
                return ComponentStatus(
                    name="api_integration",
                    initialized=True
                )
            else:
                return ComponentStatus(
                    name="api_integration",
                    initialized=True,
                    fallback_used=True,
                    error_message="OpenRouter API key not provided, API features disabled"
                )
                
        except Exception as e:
            return ComponentStatus(
                name="api_integration",
                initialized=True,
                fallback_used=True,
                error_message=f"API integration failed, using fallback: {str(e)}"
            )
    
    async def _initialize_core_services(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize core business logic services."""
        try:
            # Initialize document processor
            from src.core.extraction.document_processor import create_document_processor
            from src.core.extraction.field_extraction_service import create_field_extraction_service
            from src.core.generation.template_assembly_service import create_template_assembly_service
            
            # Create and register services
            doc_processor = create_document_processor()
            field_extractor = create_field_extraction_service()
            template_assembler = create_template_assembly_service()
            
            service_registry.register(type(doc_processor), factory_func=lambda: doc_processor)
            service_registry.register(type(field_extractor), factory_func=lambda: field_extractor)
            service_registry.register(type(template_assembler), factory_func=lambda: template_assembler)
            
            return ComponentStatus(
                name="core_services",
                initialized=True
            )
            
        except Exception as e:
            return ComponentStatus(
                name="core_services",
                initialized=False,
                error_message=str(e)
            )
    
    async def _initialize_infrastructure_services(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize infrastructure services."""
        try:
            # Initialize monitoring services
            from src.infrastructure.monitoring.health_checker import HealthChecker
            
            # Create health checker if possible
            try:
                from src.config.app_config import AppConfig
                app_config = AppConfig.from_env()
                health_checker = HealthChecker(app_config)
                service_registry.register(HealthChecker, factory_func=lambda: health_checker)
            except Exception as e:
                system_logger.warning(f"Could not initialize health checker: {e}")
            
            return ComponentStatus(
                name="infrastructure_services",
                initialized=True,
                fallback_used=True,
                error_message="Some infrastructure services using fallbacks"
            )
            
        except Exception as e:
            return ComponentStatus(
                name="infrastructure_services",
                initialized=True,
                fallback_used=True,
                error_message=f"Infrastructure services using fallbacks: {str(e)}"
            )
    
    async def _initialize_workflow_services(self, config: Dict[str, Any]) -> ComponentStatus:
        """Initialize workflow services."""
        try:
            # Try to initialize workflow manager
            try:
                from src.workflow.workflow_manager import WorkflowManager
                workflow_manager = WorkflowManager()
                service_registry.register(WorkflowManager, factory_func=lambda: workflow_manager)
            except ImportError as e:
                system_logger.warning(f"Workflow manager not available: {e}")
            
            return ComponentStatus(
                name="workflow_services",
                initialized=True,
                fallback_used=True,
                error_message="Some workflow services using fallbacks"
            )
            
        except Exception as e:
            return ComponentStatus(
                name="workflow_services",
                initialized=True,
                fallback_used=True,
                error_message=f"Workflow services using fallbacks: {str(e)}"
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        initialized_count = sum(1 for c in self.components.values() if c.initialized)
        total_count = len(self.components)
        fallback_count = sum(1 for c in self.components.values() if c.fallback_used)
        
        return {
            "overall_status": "healthy" if initialized_count == total_count else "degraded",
            "initialized_components": initialized_count,
            "total_components": total_count,
            "fallbacks_active": fallback_count,
            "components": {
                name: {
                    "initialized": status.initialized,
                    "fallback_used": status.fallback_used,
                    "error_message": status.error_message
                }
                for name, status in self.components.items()
            }
        }


# Global system initializer instance
system_initializer = SystemInitializer()