"""
Component Manager

Manages QME system components following SOLID principles:
- Clear separation of concerns
- Dependency inversion through interfaces
- Open/closed principle for extensibility
- Single responsibility for each component

This manager orchestrates the interaction between different system components
while maintaining loose coupling and high cohesion.
"""

from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

from .service_registry import (
    ServiceRegistry, 
    IExtractionService, 
    ITemplateAssemblyService,
    IQualityValidationService,
    IStorageService,
    ILoggingService,
    ServiceInterface
)
from .results_storage_service import ResultsStorageService
from .comprehensive_logging_service import ComprehensiveLoggingService, ProcessingStage

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of system components"""
    EXTRACTION = "extraction"
    TEMPLATE_ASSEMBLY = "template_assembly"
    QUALITY_VALIDATION = "quality_validation"
    STORAGE = "storage"
    LOGGING = "logging"
    CONFIGURATION = "configuration"


@dataclass
class ComponentInfo:
    """Information about a system component"""
    name: str
    component_type: ComponentType
    version: str
    description: str
    dependencies: List[str]
    is_active: bool = False
    health_status: str = "unknown"


@dataclass
class ProcessingPipeline:
    """Defines a processing pipeline configuration"""
    name: str
    stages: List[ProcessingStage]
    components: Dict[ProcessingStage, str]  # Maps stages to component names
    configuration: Dict[str, Any]


class ComponentManager:
    """
    Manages QME system components with clear separation of concerns.
    
    Provides component registration, lifecycle management, health monitoring,
    and pipeline orchestration while maintaining SOLID principles.
    """
    
    def __init__(self, service_registry: ServiceRegistry):
        """
        Initialize the component manager.
        
        Args:
            service_registry: Service registry for dependency injection
        """
        self.service_registry = service_registry
        self.components: Dict[str, ComponentInfo] = {}
        self.pipelines: Dict[str, ProcessingPipeline] = {}
        self._initialize_core_components()
        
    def _initialize_core_components(self) -> None:
        """Initialize core system components"""
        # Register core components
        self.register_component(ComponentInfo(
            name="results_storage",
            component_type=ComponentType.STORAGE,
            version="1.0.0",
            description="Organized storage for QME results with date-based archiving",
            dependencies=[]
        ))
        
        self.register_component(ComponentInfo(
            name="comprehensive_logging",
            component_type=ComponentType.LOGGING,
            version="1.0.0",
            description="Comprehensive logging and monitoring for all processing stages",
            dependencies=["results_storage"]
        ))
        
        self.register_component(ComponentInfo(
            name="openrouter_extraction",
            component_type=ComponentType.EXTRACTION,
            version="1.0.0",
            description="OpenRouter-based document extraction service",
            dependencies=["comprehensive_logging"]
        ))
        
        self.register_component(ComponentInfo(
            name="professional_template_assembly",
            component_type=ComponentType.TEMPLATE_ASSEMBLY,
            version="1.0.0",
            description="Professional template assembly with quality validation",
            dependencies=["openrouter_extraction", "comprehensive_logging"]
        ))
        
        self.register_component(ComponentInfo(
            name="quality_validation",
            component_type=ComponentType.QUALITY_VALIDATION,
            version="1.0.0",
            description="Comprehensive quality validation and compliance checking",
            dependencies=["comprehensive_logging", "results_storage"]
        ))
        
        logger.info("Core components initialized")
        
    def register_component(self, component_info: ComponentInfo) -> None:
        """
        Register a system component.
        
        Args:
            component_info: Information about the component
        """
        self.components[component_info.name] = component_info
        logger.info(f"Registered component: {component_info.name} ({component_info.component_type.value})")
        
    def activate_component(self, component_name: str) -> bool:
        """
        Activate a system component.
        
        Args:
            component_name: Name of the component to activate
            
        Returns:
            True if activation successful, False otherwise
        """
        if component_name not in self.components:
            logger.error(f"Component not found: {component_name}")
            return False
            
        component = self.components[component_name]
        
        try:
            # Check dependencies
            for dependency in component.dependencies:
                if dependency not in self.components:
                    logger.error(f"Dependency not found for {component_name}: {dependency}")
                    return False
                    
                if not self.components[dependency].is_active:
                    logger.info(f"Activating dependency: {dependency}")
                    if not self.activate_component(dependency):
                        logger.error(f"Failed to activate dependency: {dependency}")
                        return False
                        
            # Activate the component
            component.is_active = True
            component.health_status = "active"
            
            logger.info(f"Activated component: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate component {component_name}: {e}")
            component.health_status = "error"
            return False
            
    def deactivate_component(self, component_name: str) -> bool:
        """
        Deactivate a system component.
        
        Args:
            component_name: Name of the component to deactivate
            
        Returns:
            True if deactivation successful, False otherwise
        """
        if component_name not in self.components:
            logger.error(f"Component not found: {component_name}")
            return False
            
        try:
            component = self.components[component_name]
            component.is_active = False
            component.health_status = "inactive"
            
            logger.info(f"Deactivated component: {component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate component {component_name}: {e}")
            return False
            
    def get_component_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get health status of all components.
        
        Returns:
            Dictionary with component health information
        """
        health_info = {}
        
        for name, component in self.components.items():
            health_info[name] = {
                "type": component.component_type.value,
                "version": component.version,
                "is_active": component.is_active,
                "health_status": component.health_status,
                "dependencies": component.dependencies,
                "description": component.description
            }
            
        return health_info
        
    def register_pipeline(self, pipeline: ProcessingPipeline) -> None:
        """
        Register a processing pipeline.
        
        Args:
            pipeline: Pipeline configuration
        """
        self.pipelines[pipeline.name] = pipeline
        logger.info(f"Registered pipeline: {pipeline.name}")
        
    def execute_pipeline(
        self,
        pipeline_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a processing pipeline.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            input_data: Input data for the pipeline
            
        Returns:
            Pipeline execution results
        """
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_name}")
            
        pipeline = self.pipelines[pipeline_name]
        
        # Get logging service for tracking
        try:
            logging_service = self.service_registry.resolve(ILoggingService)
        except:
            logging_service = None
            
        results = {"pipeline": pipeline_name, "stages": {}}
        current_data = input_data.copy()
        
        for stage in pipeline.stages:
            stage_component = pipeline.components.get(stage)
            if not stage_component:
                logger.warning(f"No component configured for stage: {stage.value}")
                continue
                
            if stage_component not in self.components:
                logger.error(f"Component not found: {stage_component}")
                continue
                
            if not self.components[stage_component].is_active:
                logger.error(f"Component not active: {stage_component}")
                continue
                
            try:
                # Execute stage with logging
                operation_id = f"{pipeline_name}_{stage.value}_{id(current_data)}"
                
                if logging_service:
                    with logging_service.track_processing_stage(stage, operation_id):
                        stage_result = self._execute_stage(
                            stage, 
                            stage_component, 
                            current_data, 
                            pipeline.configuration
                        )
                else:
                    stage_result = self._execute_stage(
                        stage, 
                        stage_component, 
                        current_data, 
                        pipeline.configuration
                    )
                    
                results["stages"][stage.value] = stage_result
                current_data.update(stage_result)
                
            except Exception as e:
                logger.error(f"Pipeline stage failed: {stage.value} - {e}")
                results["stages"][stage.value] = {"error": str(e)}
                break
                
        return results
        
    def _execute_stage(
        self,
        stage: ProcessingStage,
        component_name: str,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single pipeline stage"""
        component = self.components[component_name]
        
        if component.component_type == ComponentType.EXTRACTION:
            service = self.service_registry.resolve(IExtractionService)
            return service.extract_from_document(
                data.get("document_path", ""),
                config.get("extraction", {})
            )
            
        elif component.component_type == ComponentType.TEMPLATE_ASSEMBLY:
            service = self.service_registry.resolve(ITemplateAssemblyService)
            return {"output_path": service.assemble_template(data, config.get("assembly", {}))}
            
        elif component.component_type == ComponentType.QUALITY_VALIDATION:
            service = self.service_registry.resolve(IQualityValidationService)
            return service.validate_document(data.get("output_path", ""))
            
        else:
            logger.warning(f"Unknown component type for stage execution: {component.component_type}")
            return {"status": "skipped"}
            
    def get_pipeline_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all registered pipelines.
        
        Returns:
            Dictionary with pipeline information
        """
        pipeline_info = {}
        
        for name, pipeline in self.pipelines.items():
            pipeline_info[name] = {
                "stages": [stage.value for stage in pipeline.stages],
                "components": {stage.value: component for stage, component in pipeline.components.items()},
                "configuration_keys": list(pipeline.configuration.keys())
            }
            
        return pipeline_info
        
    def validate_system_integrity(self) -> Dict[str, Any]:
        """
        Validate the integrity of the entire system.
        
        Returns:
            System integrity report
        """
        report = {
            "overall_status": "healthy",
            "components": {},
            "pipelines": {},
            "issues": []
        }
        
        # Check component dependencies
        for name, component in self.components.items():
            component_status = {
                "is_active": component.is_active,
                "health_status": component.health_status,
                "dependency_issues": []
            }
            
            for dependency in component.dependencies:
                if dependency not in self.components:
                    issue = f"Missing dependency: {dependency}"
                    component_status["dependency_issues"].append(issue)
                    report["issues"].append(f"{name}: {issue}")
                elif not self.components[dependency].is_active:
                    issue = f"Inactive dependency: {dependency}"
                    component_status["dependency_issues"].append(issue)
                    report["issues"].append(f"{name}: {issue}")
                    
            report["components"][name] = component_status
            
        # Check pipeline configurations
        for name, pipeline in self.pipelines.items():
            pipeline_status = {
                "configured_stages": len(pipeline.stages),
                "missing_components": []
            }
            
            for stage, component_name in pipeline.components.items():
                if component_name not in self.components:
                    issue = f"Missing component for stage {stage.value}: {component_name}"
                    pipeline_status["missing_components"].append(issue)
                    report["issues"].append(f"Pipeline {name}: {issue}")
                    
            report["pipelines"][name] = pipeline_status
            
        # Set overall status
        if report["issues"]:
            report["overall_status"] = "degraded" if len(report["issues"]) < 5 else "unhealthy"
            
        return report
        
    def generate_system_report(self) -> str:
        """
        Generate a comprehensive system report.
        
        Returns:
            Formatted system report
        """
        health = self.get_component_health()
        integrity = self.validate_system_integrity()
        pipeline_info = self.get_pipeline_info()
        
        report = f"""
QME System Component Report
Generated: {logger.handlers[0].formatter.formatTime(logger.makeRecord('', 0, '', 0, '', (), None)) if logger.handlers else 'Unknown'}

=== SYSTEM STATUS ===
Overall Status: {integrity['overall_status'].upper()}
Total Components: {len(self.components)}
Active Components: {sum(1 for c in self.components.values() if c.is_active)}
Registered Pipelines: {len(self.pipelines)}

=== COMPONENT HEALTH ===
"""
        
        for name, info in health.items():
            status_icon = "✓" if info["is_active"] else "✗"
            report += f"{status_icon} {name} ({info['type']}) - {info['health_status']}\n"
            
        if integrity["issues"]:
            report += f"\n=== SYSTEM ISSUES ===\n"
            for issue in integrity["issues"]:
                report += f"⚠ {issue}\n"
                
        report += f"\n=== REGISTERED PIPELINES ===\n"
        for name, info in pipeline_info.items():
            report += f"• {name}: {len(info['stages'])} stages\n"
            
        return report


def create_default_component_manager() -> ComponentManager:
    """Create a component manager with default configuration"""
    from .service_registry import service_registry, configure_default_services
    
    # Configure default services
    configure_default_services()
    
    # Create component manager
    manager = ComponentManager(service_registry)
    
    # Register default pipeline
    default_pipeline = ProcessingPipeline(
        name="qme_document_processing",
        stages=[
            ProcessingStage.DOCUMENT_INGESTION,
            ProcessingStage.INFORMATION_EXTRACTION,
            ProcessingStage.TEMPLATE_ASSEMBLY,
            ProcessingStage.QUALITY_VALIDATION,
            ProcessingStage.DOCUMENT_OUTPUT
        ],
        components={
            ProcessingStage.INFORMATION_EXTRACTION: "openrouter_extraction",
            ProcessingStage.TEMPLATE_ASSEMBLY: "professional_template_assembly",
            ProcessingStage.QUALITY_VALIDATION: "quality_validation"
        },
        configuration={
            "extraction": {"model": "sonoma_sky_alpha"},
            "assembly": {"format": "professional"},
            "validation": {"strict_mode": True}
        }
    )
    
    manager.register_pipeline(default_pipeline)
    
    # Activate core components
    manager.activate_component("results_storage")
    manager.activate_component("comprehensive_logging")
    
    return manager