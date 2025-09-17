"""
Service Integration Validator

This module provides comprehensive service integration validation for UI components,
ensuring proper service availability and graceful degradation when services are unavailable.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service availability status"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of service validation"""
    service_name: str
    status: ServiceStatus
    response_time_ms: Optional[float]
    error_message: Optional[str]
    dependencies_met: bool
    fallback_available: bool


@dataclass
class DependencyStatus:
    """Status of component dependencies"""
    component_name: str
    required_services: List[str]
    available_services: List[str]
    missing_services: List[str]
    can_function: bool
    degraded_functionality: List[str]


class ServiceIntegrationValidator:
    """
    Validates service availability and manages graceful degradation for UI components
    """
    
    def __init__(self):
        self.service_checkers: Dict[str, Callable] = {}
        self.dependency_map: Dict[str, List[str]] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.service_cache: Dict[str, ValidationResult] = {}
        self.cache_ttl_seconds = 30
        self.timeout_seconds = 5
        
        # Initialize default service checkers
        self._initialize_default_checkers()
        self._initialize_dependency_map()
    
    def _initialize_default_checkers(self):
        """Initialize default service availability checkers"""
        self.service_checkers.update({
            'database': self._check_database_service,
            'openrouter_api': self._check_openrouter_service,
            'gemini_api': self._check_gemini_service,
            'knowledge_graph': self._check_knowledge_graph_service,
            'document_processor': self._check_document_processor_service,
            'template_generator': self._check_template_generator_service,
            'qa_engine': self._check_qa_engine_service,
            'file_storage': self._check_file_storage_service
        })
    
    def _initialize_dependency_map(self):
        """Initialize component dependency mapping"""
        self.dependency_map.update({
            'upload_interface': ['file_storage', 'document_processor'],
            'qa_interface': ['qa_engine', 'knowledge_graph', 'openrouter_api'],
            'template_interface': ['template_generator', 'document_processor', 'database'],
            'health_status': ['database', 'openrouter_api'],
            'document_manager': ['database', 'file_storage', 'document_processor'],
            'main_app': ['database', 'file_storage']
        })
    
    def register_service_checker(self, service_name: str, checker: Callable) -> None:
        """Register a custom service availability checker"""
        self.service_checkers[service_name] = checker
        logger.info(f"Registered service checker for: {service_name}")
    
    def register_dependency(self, component: str, services: List[str]) -> None:
        """Register component dependencies"""
        self.dependency_map[component] = services
        logger.info(f"Registered dependencies for {component}: {services}")
    
    def register_fallback_handler(self, service_name: str, handler: Callable) -> None:
        """Register fallback handler for when service is unavailable"""
        self.fallback_handlers[service_name] = handler
        logger.info(f"Registered fallback handler for: {service_name}")
    
    def validate_service_availability(self, service_name: str, use_cache: bool = True) -> ValidationResult:
        """
        Validate if a specific service is available
        
        Args:
            service_name: Name of the service to check
            use_cache: Whether to use cached results
            
        Returns:
            ValidationResult with service status and details
        """
        # Check cache first
        if use_cache and service_name in self.service_cache:
            cached_result = self.service_cache[service_name]
            if time.time() - getattr(cached_result, '_timestamp', 0) < self.cache_ttl_seconds:
                return cached_result
        
        start_time = time.time()
        
        try:
            if service_name not in self.service_checkers:
                result = ValidationResult(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    response_time_ms=None,
                    error_message=f"No checker registered for service: {service_name}",
                    dependencies_met=False,
                    fallback_available=service_name in self.fallback_handlers
                )
            else:
                # Execute service check with timeout
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.service_checkers[service_name])
                    try:
                        is_available = future.result(timeout=self.timeout_seconds)
                        response_time = (time.time() - start_time) * 1000
                        
                        result = ValidationResult(
                            service_name=service_name,
                            status=ServiceStatus.AVAILABLE if is_available else ServiceStatus.UNAVAILABLE,
                            response_time_ms=response_time,
                            error_message=None if is_available else f"Service {service_name} is not responding",
                            dependencies_met=is_available,
                            fallback_available=service_name in self.fallback_handlers
                        )
                    except FutureTimeoutError:
                        result = ValidationResult(
                            service_name=service_name,
                            status=ServiceStatus.UNAVAILABLE,
                            response_time_ms=self.timeout_seconds * 1000,
                            error_message=f"Service {service_name} timed out after {self.timeout_seconds}s",
                            dependencies_met=False,
                            fallback_available=service_name in self.fallback_handlers
                        )
        
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {str(e)}")
            result = ValidationResult(
                service_name=service_name,
                status=ServiceStatus.UNAVAILABLE,
                response_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                dependencies_met=False,
                fallback_available=service_name in self.fallback_handlers
            )
        
        # Cache result with timestamp
        setattr(result, '_timestamp', time.time())
        self.service_cache[service_name] = result
        
        return result
    
    def check_dependencies(self, component: str) -> DependencyStatus:
        """
        Check all dependencies for a UI component
        
        Args:
            component: Name of the UI component
            
        Returns:
            DependencyStatus with availability information
        """
        if component not in self.dependency_map:
            logger.warning(f"No dependencies registered for component: {component}")
            return DependencyStatus(
                component_name=component,
                required_services=[],
                available_services=[],
                missing_services=[],
                can_function=True,
                degraded_functionality=[]
            )
        
        required_services = self.dependency_map[component]
        available_services = []
        missing_services = []
        degraded_functionality = []
        
        for service in required_services:
            validation_result = self.validate_service_availability(service)
            
            if validation_result.status == ServiceStatus.AVAILABLE:
                available_services.append(service)
            elif validation_result.status == ServiceStatus.DEGRADED:
                available_services.append(service)
                degraded_functionality.append(f"{service} is running with degraded performance")
            else:
                missing_services.append(service)
        
        # Determine if component can function
        critical_services = self._get_critical_services(component)
        can_function = all(service in available_services for service in critical_services)
        
        return DependencyStatus(
            component_name=component,
            required_services=required_services,
            available_services=available_services,
            missing_services=missing_services,
            can_function=can_function,
            degraded_functionality=degraded_functionality
        )
    
    def enable_graceful_degradation(self, failed_services: List[str]) -> Dict[str, Any]:
        """
        Enable graceful degradation for failed services
        
        Args:
            failed_services: List of service names that have failed
            
        Returns:
            Dictionary with degradation status and fallback information
        """
        degradation_status = {
            'enabled_fallbacks': [],
            'disabled_features': [],
            'warnings': [],
            'recovery_suggestions': []
        }
        
        for service in failed_services:
            if service in self.fallback_handlers:
                try:
                    fallback_result = self.fallback_handlers[service]()
                    degradation_status['enabled_fallbacks'].append({
                        'service': service,
                        'fallback': 'enabled',
                        'details': fallback_result
                    })
                except Exception as e:
                    logger.error(f"Failed to enable fallback for {service}: {str(e)}")
                    degradation_status['disabled_features'].append(service)
            else:
                degradation_status['disabled_features'].append(service)
                degradation_status['warnings'].append(
                    f"No fallback available for {service} - feature will be disabled"
                )
            
            # Add recovery suggestions
            recovery_suggestions = self._get_recovery_suggestions(service)
            degradation_status['recovery_suggestions'].extend(recovery_suggestions)
        
        return degradation_status
    
    def validate_all_services(self) -> Dict[str, ValidationResult]:
        """Validate all registered services"""
        results = {}
        
        for service_name in self.service_checkers.keys():
            results[service_name] = self.validate_service_availability(service_name)
        
        return results
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        all_results = self.validate_all_services()
        
        available_count = sum(1 for r in all_results.values() if r.status == ServiceStatus.AVAILABLE)
        total_count = len(all_results)
        
        return {
            'overall_health': 'healthy' if available_count == total_count else 'degraded',
            'available_services': available_count,
            'total_services': total_count,
            'health_percentage': (available_count / total_count * 100) if total_count > 0 else 0,
            'service_details': all_results,
            'timestamp': time.time()
        }
    
    def _get_critical_services(self, component: str) -> List[str]:
        """Get critical services that component cannot function without"""
        critical_map = {
            'upload_interface': ['file_storage'],
            'qa_interface': ['qa_engine'],
            'template_interface': ['template_generator'],
            'health_status': [],
            'document_manager': ['database'],
            'main_app': []
        }
        return critical_map.get(component, [])
    
    def _get_recovery_suggestions(self, service: str) -> List[str]:
        """Get recovery suggestions for failed service"""
        suggestions_map = {
            'database': [
                "Check database connection settings",
                "Verify database server is running",
                "Check database credentials"
            ],
            'openrouter_api': [
                "Verify OpenRouter API key is set",
                "Check internet connectivity",
                "Verify API quota and billing status"
            ],
            'gemini_api': [
                "Verify Gemini API key is set",
                "Check internet connectivity",
                "Verify API quota and billing status"
            ],
            'knowledge_graph': [
                "Check knowledge graph initialization",
                "Verify graph database connectivity",
                "Run knowledge base initialization script"
            ],
            'document_processor': [
                "Check document processing dependencies",
                "Verify file system permissions",
                "Check temporary directory availability"
            ],
            'template_generator': [
                "Check template configuration files",
                "Verify template dependencies",
                "Check output directory permissions"
            ],
            'qa_engine': [
                "Check QA engine configuration",
                "Verify embedding service availability",
                "Check vector database connectivity"
            ],
            'file_storage': [
                "Check file system permissions",
                "Verify storage directory exists",
                "Check available disk space"
            ]
        }
        return suggestions_map.get(service, [f"Check {service} configuration and dependencies"])
    
    # Default service checker implementations
    def _check_database_service(self) -> bool:
        """Check database service availability"""
        try:
            from src.storage.database import DatabaseManager
            db_manager = DatabaseManager()
            return db_manager.test_connection()
        except Exception as e:
            logger.debug(f"Database check failed: {str(e)}")
            return False
    
    def _check_openrouter_service(self) -> bool:
        """Check OpenRouter API service availability"""
        try:
            from src.infrastructure.api.api_provider_factory import APIProviderFactory
            factory = APIProviderFactory()
            provider = factory.create_openrouter_provider()
            # Simple test call
            return provider is not None
        except Exception as e:
            logger.debug(f"OpenRouter check failed: {str(e)}")
            return False
    
    def _check_gemini_service(self) -> bool:
        """Check Gemini API service availability"""
        try:
            from src.infrastructure.api.api_provider_factory import APIProviderFactory
            factory = APIProviderFactory()
            provider = factory.create_gemini_provider()
            return provider is not None
        except Exception as e:
            logger.debug(f"Gemini check failed: {str(e)}")
            return False
    
    def _check_knowledge_graph_service(self) -> bool:
        """Check knowledge graph service availability"""
        try:
            from src.models.knowledge_graph import KnowledgeGraph
            kg = KnowledgeGraph()
            return kg.is_initialized()
        except Exception as e:
            logger.debug(f"Knowledge graph check failed: {str(e)}")
            return False
    
    def _check_document_processor_service(self) -> bool:
        """Check document processor service availability"""
        try:
            from src.services.comprehensive_qme_field_service import ComprehensiveQMEFieldService
            service = ComprehensiveQMEFieldService()
            return service is not None
        except Exception as e:
            logger.debug(f"Document processor check failed: {str(e)}")
            return False
    
    def _check_template_generator_service(self) -> bool:
        """Check template generator service availability"""
        try:
            from src.services.professional_template_assembler_simple import ProfessionalTemplateAssemblerSimple
            service = ProfessionalTemplateAssemblerSimple()
            return service is not None
        except Exception as e:
            logger.debug(f"Template generator check failed: {str(e)}")
            return False
    
    def _check_qa_engine_service(self) -> bool:
        """Check QA engine service availability"""
        try:
            from src.strategies.qa_strategy import QAStrategy
            strategy = QAStrategy()
            return strategy is not None
        except Exception as e:
            logger.debug(f"QA engine check failed: {str(e)}")
            return False
    
    def _check_file_storage_service(self) -> bool:
        """Check file storage service availability"""
        try:
            import os
            from src.config.app_config import AppConfig
            config = AppConfig()
            storage_paths = [
                config.get('storage.documents_path', 'data/documents'),
                config.get('storage.results_path', 'results'),
                config.get('storage.cache_path', 'data/cache')
            ]
            return all(os.path.exists(path) or os.access(os.path.dirname(path), os.W_OK) for path in storage_paths)
        except Exception as e:
            logger.debug(f"File storage check failed: {str(e)}")
            return False


# Global instance for easy access
service_validator = ServiceIntegrationValidator()