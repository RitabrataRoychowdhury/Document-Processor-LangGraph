"""
Configuration Service

Provides centralized configuration management for the QME system:
- Loads configuration from YAML files
- Supports environment-specific overrides
- Validates configuration integrity
- Provides type-safe configuration access
- Supports hot-reloading of configuration

This service follows SOLID principles with clear separation of configuration concerns.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, Generic, List
from dataclasses import dataclass
from enum import Enum
import logging
from threading import Lock
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class Environment(Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class ComponentConfig:
    """Configuration for a system component"""
    name: str
    type: str
    class_name: str
    config: Dict[str, Any]
    dependencies: List[str]
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Configuration for a processing pipeline"""
    name: str
    description: str
    stages: List[str]
    components: Dict[str, str]
    configuration: Dict[str, Any]
    enabled: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration"""
    name: str
    version: str
    environment: Environment
    components: Dict[str, ComponentConfig]
    pipelines: Dict[str, PipelineConfig]
    monitoring: Dict[str, Any]
    storage: Dict[str, Any]
    security: Dict[str, Any]


class ConfigurationService:
    """
    Service for managing system configuration.
    
    Provides centralized configuration loading, validation, and access
    with support for environment-specific overrides and hot-reloading.
    """
    
    def __init__(
        self,
        config_directory: str = "config",
        environment: Optional[Environment] = None
    ):
        """
        Initialize the configuration service.
        
        Args:
            config_directory: Base directory for configuration files
            environment: Target environment (auto-detected if None)
        """
        self.config_directory = Path(config_directory)
        self.environment = environment or self._detect_environment()
        self._config_cache: Dict[str, Any] = {}
        self._file_timestamps: Dict[str, float] = {}
        self._lock = Lock()
        
        # Load system configuration
        self.system_config = self._load_system_config()
        
    def _detect_environment(self) -> Environment:
        """Detect the current environment"""
        env_name = os.getenv("QME_ENVIRONMENT", "development").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
            
    def _load_system_config(self) -> SystemConfig:
        """Load the complete system configuration"""
        try:
            # Load base configuration
            base_config = self._load_yaml_file("system/component_config.yaml")
            
            # Load environment-specific overrides
            env_config_path = f"system/component_config.{self.environment.value}.yaml"
            env_overrides = self._load_yaml_file(env_config_path, required=False)
            
            # Merge configurations
            if env_overrides:
                base_config = self._merge_configs(base_config, env_overrides)
                
            # Parse into structured configuration
            return self._parse_system_config(base_config)
            
        except Exception as e:
            logger.error(f"Failed to load system configuration: {e}")
            raise ConfigurationError(f"System configuration loading failed: {e}")
            
    def _load_yaml_file(self, relative_path: str, required: bool = True) -> Dict[str, Any]:
        """Load a YAML configuration file"""
        file_path = self.config_directory / relative_path
        
        if not file_path.exists():
            if required:
                raise ConfigurationError(f"Required configuration file not found: {file_path}")
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            # Cache file timestamp for hot-reloading
            self._file_timestamps[str(file_path)] = file_path.stat().st_mtime
            
            logger.debug(f"Loaded configuration from: {file_path}")
            return content or {}
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load {file_path}: {e}")
            
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _parse_system_config(self, config_data: Dict[str, Any]) -> SystemConfig:
        """Parse raw configuration data into structured configuration"""
        try:
            system_info = config_data.get("system", {})
            
            # Parse components
            components = {}
            for name, comp_data in config_data.get("components", {}).items():
                components[name] = ComponentConfig(
                    name=name,
                    type=comp_data.get("type", "unknown"),
                    class_name=comp_data.get("class", ""),
                    config=comp_data.get("config", {}),
                    dependencies=comp_data.get("dependencies", []),
                    enabled=comp_data.get("enabled", True)
                )
                
            # Parse pipelines
            pipelines = {}
            for name, pipe_data in config_data.get("pipelines", {}).items():
                pipelines[name] = PipelineConfig(
                    name=name,
                    description=pipe_data.get("description", ""),
                    stages=pipe_data.get("stages", []),
                    components=pipe_data.get("components", {}),
                    configuration=pipe_data.get("configuration", {}),
                    enabled=pipe_data.get("enabled", True)
                )
                
            return SystemConfig(
                name=system_info.get("name", "QME System"),
                version=system_info.get("version", "1.0.0"),
                environment=Environment(system_info.get("environment", "development")),
                components=components,
                pipelines=pipelines,
                monitoring=config_data.get("monitoring", {}),
                storage=config_data.get("storage", {}),
                security=config_data.get("security", {})
            )
            
        except Exception as e:
            raise ConfigurationError(f"Failed to parse system configuration: {e}")
            
    def get_component_config(self, component_name: str) -> ComponentConfig:
        """
        Get configuration for a specific component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Component configuration
            
        Raises:
            ConfigurationError: If component not found
        """
        if component_name not in self.system_config.components:
            raise ConfigurationError(f"Component configuration not found: {component_name}")
            
        return self.system_config.components[component_name]
        
    def get_pipeline_config(self, pipeline_name: str) -> PipelineConfig:
        """
        Get configuration for a specific pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Pipeline configuration
            
        Raises:
            ConfigurationError: If pipeline not found
        """
        if pipeline_name not in self.system_config.pipelines:
            raise ConfigurationError(f"Pipeline configuration not found: {pipeline_name}")
            
        return self.system_config.pipelines[pipeline_name]
        
    def get_prompt_config(self, prompt_type: str, prompt_name: str) -> Dict[str, Any]:
        """
        Load prompt configuration from the prompts directory.
        
        Args:
            prompt_type: Type of prompt (extraction, generation, validation)
            prompt_name: Name of the specific prompt
            
        Returns:
            Prompt configuration
        """
        cache_key = f"prompt_{prompt_type}_{prompt_name}"
        
        with self._lock:
            if cache_key in self._config_cache:
                return self._config_cache[cache_key]
                
        prompt_path = f"prompts/{prompt_type}/{prompt_name}.yaml"
        config = self._load_yaml_file(prompt_path)
        
        with self._lock:
            self._config_cache[cache_key] = config
            
        return config
        
    def get_template_config(self, template_name: str) -> Dict[str, Any]:
        """
        Load template configuration.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template configuration
        """
        cache_key = f"template_{template_name}"
        
        with self._lock:
            if cache_key in self._config_cache:
                return self._config_cache[cache_key]
                
        template_path = f"templates/{template_name}.yaml"
        config = self._load_yaml_file(template_path)
        
        with self._lock:
            self._config_cache[cache_key] = config
            
        return config
        
    def get_setting(self, setting_path: str, default: Any = None) -> Any:
        """
        Get a configuration setting using dot notation.
        
        Args:
            setting_path: Dot-separated path to the setting (e.g., "monitoring.health_check_interval_seconds")
            default: Default value if setting not found
            
        Returns:
            Configuration value or default
        """
        try:
            # Convert system config to dictionary for path traversal
            config_dict = {
                "system": {
                    "name": self.system_config.name,
                    "version": self.system_config.version,
                    "environment": self.system_config.environment.value
                },
                "monitoring": self.system_config.monitoring,
                "storage": self.system_config.storage,
                "security": self.system_config.security
            }
            
            # Traverse the path
            current = config_dict
            for part in setting_path.split('.'):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
                    
            return current
            
        except Exception as e:
            logger.warning(f"Failed to get setting '{setting_path}': {e}")
            return default
            
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Dictionary with validation issues by category
        """
        issues = {
            "components": [],
            "pipelines": [],
            "dependencies": [],
            "files": []
        }
        
        # Validate components
        for name, component in self.system_config.components.items():
            if not component.class_name:
                issues["components"].append(f"Component '{name}' missing class name")
                
            if not component.type:
                issues["components"].append(f"Component '{name}' missing type")
                
        # Validate pipelines
        for name, pipeline in self.system_config.pipelines.items():
            if not pipeline.stages:
                issues["pipelines"].append(f"Pipeline '{name}' has no stages")
                
            for stage, component_name in pipeline.components.items():
                if component_name not in self.system_config.components:
                    issues["pipelines"].append(
                        f"Pipeline '{name}' references unknown component '{component_name}'"
                    )
                    
        # Validate dependencies
        for name, component in self.system_config.components.items():
            for dependency in component.dependencies:
                if dependency not in self.system_config.components:
                    issues["dependencies"].append(
                        f"Component '{name}' depends on unknown component '{dependency}'"
                    )
                    
        # Validate required files
        required_dirs = ["prompts", "templates"]
        for dir_name in required_dirs:
            dir_path = self.config_directory / dir_name
            if not dir_path.exists():
                issues["files"].append(f"Required directory missing: {dir_path}")
                
        return issues
        
    def reload_configuration(self) -> bool:
        """
        Reload configuration from files.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            # Clear cache
            with self._lock:
                self._config_cache.clear()
                
            # Reload system configuration
            self.system_config = self._load_system_config()
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
            
    def check_for_updates(self) -> bool:
        """
        Check if configuration files have been updated.
        
        Returns:
            True if updates detected, False otherwise
        """
        try:
            for file_path, cached_timestamp in self._file_timestamps.items():
                path_obj = Path(file_path)
                if path_obj.exists():
                    current_timestamp = path_obj.stat().st_mtime
                    if current_timestamp > cached_timestamp:
                        return True
                        
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for configuration updates: {e}")
            return False
            
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Configuration summary
        """
        return {
            "system": {
                "name": self.system_config.name,
                "version": self.system_config.version,
                "environment": self.system_config.environment.value
            },
            "components": {
                "total": len(self.system_config.components),
                "enabled": len([c for c in self.system_config.components.values() if c.enabled]),
                "types": list(set(c.type for c in self.system_config.components.values()))
            },
            "pipelines": {
                "total": len(self.system_config.pipelines),
                "enabled": len([p for p in self.system_config.pipelines.values() if p.enabled])
            },
            "configuration_files": len(self._file_timestamps),
            "cache_entries": len(self._config_cache)
        }


# Global configuration service instance
_config_service: Optional[ConfigurationService] = None


def get_config_service() -> ConfigurationService:
    """Get the global configuration service instance"""
    global _config_service
    
    if _config_service is None:
        _config_service = ConfigurationService()
        
    return _config_service


def initialize_configuration(config_directory: str = "config") -> ConfigurationService:
    """Initialize the global configuration service"""
    global _config_service
    
    _config_service = ConfigurationService(config_directory)
    return _config_service