"""
Health Status Adapter for UI Components

This module provides type-safe access to health check results with backward compatibility
for both ComponentHealth dataclass objects and legacy dictionary formats.
"""

from typing import Dict, Any, Union, Optional, List
from dataclasses import is_dataclass
import logging

logger = logging.getLogger(__name__)

# Import health check types
try:
    from src.infrastructure.monitoring.health_checker import ComponentHealth, SystemHealth, HealthStatus
    HEALTH_TYPES_AVAILABLE = True
except ImportError:
    HEALTH_TYPES_AVAILABLE = False
    ComponentHealth = None
    SystemHealth = None
    HealthStatus = None


class HealthStatusAdapter:
    """
    Adapter class that provides consistent interface for accessing health status
    regardless of whether the object is a ComponentHealth dataclass or legacy dictionary.
    """
    
    @staticmethod
    def is_component_health_object(health: Any) -> bool:
        """Check if the object is a ComponentHealth dataclass."""
        if not HEALTH_TYPES_AVAILABLE:
            return False
        return isinstance(health, ComponentHealth) if ComponentHealth else False
    
    @staticmethod
    def is_system_health_object(health: Any) -> bool:
        """Check if the object is a SystemHealth dataclass."""
        if not HEALTH_TYPES_AVAILABLE:
            return False
        return isinstance(health, SystemHealth) if SystemHealth else False
    
    @staticmethod
    def is_dataclass_object(obj: Any) -> bool:
        """Check if object is any dataclass."""
        return is_dataclass(obj) and not isinstance(obj, type)
    
    @staticmethod
    def adapt_component_health(health: Union[ComponentHealth, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert ComponentHealth object to UI-friendly dictionary format.
        
        Args:
            health: ComponentHealth object or legacy dictionary
            
        Returns:
            Dictionary with consistent keys for UI consumption
        """
        if health is None:
            return {
                "healthy": False,
                "message": "Health status unavailable",
                "status": "unknown",
                "details": {},
                "response_time_ms": None,
                "metrics": {}
            }
        
        try:
            # Handle ComponentHealth dataclass objects
            if HealthStatusAdapter.is_component_health_object(health):
                return {
                    "healthy": health.is_healthy,
                    "message": health.message,
                    "status": health.status.value if hasattr(health.status, 'value') else str(health.status),
                    "component": health.component,
                    "details": health.details if hasattr(health, 'details') else {},
                    "response_time_ms": health.response_time_ms if hasattr(health, 'response_time_ms') else None,
                    "metrics": health.metrics if hasattr(health, 'metrics') else {},
                    "timestamp": health.timestamp if hasattr(health, 'timestamp') else None
                }
            
            # Handle legacy dictionary format
            elif isinstance(health, dict):
                return {
                    "healthy": health.get("healthy", health.get("is_healthy", False)),
                    "message": health.get("message", "No message available"),
                    "status": health.get("status", "unknown"),
                    "component": health.get("component", "unknown"),
                    "details": health.get("details", {}),
                    "response_time_ms": health.get("response_time_ms"),
                    "metrics": health.get("metrics", {}),
                    "timestamp": health.get("timestamp")
                }
            
            # Handle other dataclass objects
            elif HealthStatusAdapter.is_dataclass_object(health):
                # Generic dataclass handling
                result = {
                    "healthy": getattr(health, 'is_healthy', getattr(health, 'healthy', False)),
                    "message": getattr(health, 'message', 'No message available'),
                    "status": str(getattr(health, 'status', 'unknown')),
                    "component": getattr(health, 'component', 'unknown'),
                    "details": getattr(health, 'details', {}),
                    "response_time_ms": getattr(health, 'response_time_ms', None),
                    "metrics": getattr(health, 'metrics', {}),
                    "timestamp": getattr(health, 'timestamp', None)
                }
                return result
            
            # Fallback for unknown types
            else:
                logger.warning(f"Unknown health object type: {type(health)}")
                return {
                    "healthy": False,
                    "message": f"Unknown health object type: {type(health).__name__}",
                    "status": "unknown",
                    "component": "unknown",
                    "details": {"original_type": str(type(health))},
                    "response_time_ms": None,
                    "metrics": {},
                    "timestamp": None
                }
                
        except Exception as e:
            logger.error(f"Error adapting component health: {e}", exc_info=True)
            return {
                "healthy": False,
                "message": f"Error processing health status: {str(e)}",
                "status": "error",
                "component": "unknown",
                "details": {"error": str(e)},
                "response_time_ms": None,
                "metrics": {},
                "timestamp": None
            }
    
    @staticmethod
    def adapt_system_health(health: Union[SystemHealth, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert SystemHealth object to UI-friendly dictionary format.
        
        Args:
            health: SystemHealth object or legacy dictionary
            
        Returns:
            Dictionary with consistent keys for UI consumption
        """
        if health is None:
            return {
                "overall_healthy": False,
                "checks": {},
                "summary": {},
                "timestamp": None
            }
        
        try:
            # Handle SystemHealth dataclass objects
            if HealthStatusAdapter.is_system_health_object(health):
                # Convert component health objects to dictionaries
                components_dict = {}
                if hasattr(health, 'components') and health.components:
                    for name, component_health in health.components.items():
                        components_dict[name] = HealthStatusAdapter.adapt_component_health(component_health)
                
                return {
                    "overall_healthy": health.is_healthy,
                    "checks": components_dict,
                    "components": components_dict,  # Alias for backward compatibility
                    "summary": health.summary if hasattr(health, 'summary') else {},
                    "timestamp": health.timestamp if hasattr(health, 'timestamp') else None,
                    "status": health.overall_status.value if hasattr(health.overall_status, 'value') else str(health.overall_status)
                }
            
            # Handle legacy dictionary format
            elif isinstance(health, dict):
                # Process nested component health objects if they exist
                checks = health.get("checks", health.get("components", {}))
                processed_checks = {}
                
                if isinstance(checks, dict):
                    for name, component_health in checks.items():
                        processed_checks[name] = HealthStatusAdapter.adapt_component_health(component_health)
                
                return {
                    "overall_healthy": health.get("overall_healthy", health.get("is_healthy", False)),
                    "checks": processed_checks,
                    "components": processed_checks,  # Alias for backward compatibility
                    "summary": health.get("summary", {}),
                    "timestamp": health.get("timestamp"),
                    "status": health.get("status", "unknown")
                }
            
            # Handle other dataclass objects
            elif HealthStatusAdapter.is_dataclass_object(health):
                # Generic dataclass handling
                components_dict = {}
                components = getattr(health, 'components', {})
                if isinstance(components, dict):
                    for name, component_health in components.items():
                        components_dict[name] = HealthStatusAdapter.adapt_component_health(component_health)
                
                return {
                    "overall_healthy": getattr(health, 'is_healthy', getattr(health, 'overall_healthy', False)),
                    "checks": components_dict,
                    "components": components_dict,
                    "summary": getattr(health, 'summary', {}),
                    "timestamp": getattr(health, 'timestamp', None),
                    "status": str(getattr(health, 'status', getattr(health, 'overall_status', 'unknown')))
                }
            
            # Fallback for unknown types
            else:
                logger.warning(f"Unknown system health object type: {type(health)}")
                return {
                    "overall_healthy": False,
                    "checks": {},
                    "components": {},
                    "summary": {"error": f"Unknown health object type: {type(health).__name__}"},
                    "timestamp": None,
                    "status": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Error adapting system health: {e}", exc_info=True)
            return {
                "overall_healthy": False,
                "checks": {},
                "components": {},
                "summary": {"error": str(e)},
                "timestamp": None,
                "status": "error"
            }
    
    @staticmethod
    def is_healthy(health: Union[ComponentHealth, SystemHealth, Dict[str, Any]]) -> bool:
        """
        Check if health object indicates healthy status.
        
        Args:
            health: Health object of any supported type
            
        Returns:
            Boolean indicating if the component/system is healthy
        """
        if health is None:
            return False
        
        try:
            # Handle ComponentHealth objects
            if HealthStatusAdapter.is_component_health_object(health):
                return health.is_healthy
            
            # Handle SystemHealth objects
            elif HealthStatusAdapter.is_system_health_object(health):
                return health.is_healthy
            
            # Handle dictionary format
            elif isinstance(health, dict):
                return health.get("healthy", health.get("is_healthy", health.get("overall_healthy", False)))
            
            # Handle other dataclass objects
            elif HealthStatusAdapter.is_dataclass_object(health):
                return getattr(health, 'is_healthy', getattr(health, 'healthy', False))
            
            # Unknown type
            else:
                logger.warning(f"Cannot determine health status for type: {type(health)}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking health status: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_status_message(health: Union[ComponentHealth, SystemHealth, Dict[str, Any]]) -> str:
        """
        Get status message from health object.
        
        Args:
            health: Health object of any supported type
            
        Returns:
            Status message string
        """
        if health is None:
            return "Health status unavailable"
        
        try:
            # Handle ComponentHealth and SystemHealth objects
            if (HealthStatusAdapter.is_component_health_object(health) or 
                HealthStatusAdapter.is_system_health_object(health)):
                return getattr(health, 'message', 'No message available')
            
            # Handle dictionary format
            elif isinstance(health, dict):
                return health.get("message", "No message available")
            
            # Handle other dataclass objects
            elif HealthStatusAdapter.is_dataclass_object(health):
                return getattr(health, 'message', 'No message available')
            
            # Unknown type
            else:
                return f"Unknown health object type: {type(health).__name__}"
                
        except Exception as e:
            logger.error(f"Error getting status message: {e}", exc_info=True)
            return f"Error retrieving status message: {str(e)}"
    
    @staticmethod
    def get_component_details(health: Union[ComponentHealth, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed information from component health object.
        
        Args:
            health: ComponentHealth object or dictionary
            
        Returns:
            Dictionary with detailed health information
        """
        if health is None:
            return {}
        
        try:
            adapted = HealthStatusAdapter.adapt_component_health(health)
            return adapted.get("details", {})
            
        except Exception as e:
            logger.error(f"Error getting component details: {e}", exc_info=True)
            return {"error": str(e)}
    
    @staticmethod
    def get_response_time(health: Union[ComponentHealth, Dict[str, Any]]) -> Optional[float]:
        """
        Get response time from health object.
        
        Args:
            health: Health object of any supported type
            
        Returns:
            Response time in milliseconds or None
        """
        if health is None:
            return None
        
        try:
            adapted = HealthStatusAdapter.adapt_component_health(health)
            return adapted.get("response_time_ms")
            
        except Exception as e:
            logger.error(f"Error getting response time: {e}", exc_info=True)
            return None


class TypeGuards:
    """Type guard functions for runtime type checking."""
    
    @staticmethod
    def is_component_health(obj: Any) -> bool:
        """Type guard for ComponentHealth objects."""
        return HealthStatusAdapter.is_component_health_object(obj)
    
    @staticmethod
    def is_system_health(obj: Any) -> bool:
        """Type guard for SystemHealth objects."""
        return HealthStatusAdapter.is_system_health_object(obj)
    
    @staticmethod
    def is_health_dict(obj: Any) -> bool:
        """Type guard for health dictionary objects."""
        if not isinstance(obj, dict):
            return False
        
        # Check for common health dictionary keys
        health_keys = {"healthy", "is_healthy", "overall_healthy", "message", "status", "checks", "components"}
        return any(key in obj for key in health_keys)


class StatusFormatter:
    """Utility class for consistent health status formatting."""
    
    @staticmethod
    def format_health_status(health: Union[ComponentHealth, SystemHealth, Dict[str, Any]]) -> str:
        """
        Format health status for display.
        
        Args:
            health: Health object of any supported type
            
        Returns:
            Formatted status string
        """
        if health is None:
            return "❓ Unknown"
        
        try:
            is_healthy = HealthStatusAdapter.is_healthy(health)
            message = HealthStatusAdapter.get_status_message(health)
            
            icon = "✅" if is_healthy else "❌"
            return f"{icon} {message}"
            
        except Exception as e:
            logger.error(f"Error formatting health status: {e}", exc_info=True)
            return f"❌ Error: {str(e)}"
    
    @staticmethod
    def format_component_list(health: Union[SystemHealth, Dict[str, Any]]) -> List[str]:
        """
        Format component health list for display.
        
        Args:
            health: SystemHealth object or dictionary
            
        Returns:
            List of formatted component status strings
        """
        if health is None:
            return ["❓ No health information available"]
        
        try:
            adapted = HealthStatusAdapter.adapt_system_health(health)
            components = adapted.get("checks", {})
            
            if not components:
                return ["❓ No components to display"]
            
            formatted_list = []
            for component_name, component_health in components.items():
                is_healthy = component_health.get("healthy", False)
                message = component_health.get("message", "No message")
                icon = "✅" if is_healthy else "❌"
                formatted_list.append(f"{icon} {component_name}: {message}")
            
            return formatted_list
            
        except Exception as e:
            logger.error(f"Error formatting component list: {e}", exc_info=True)
            return [f"❌ Error formatting components: {str(e)}"]