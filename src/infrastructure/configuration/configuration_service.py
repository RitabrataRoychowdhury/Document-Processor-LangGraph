"""
Configuration Service

This service provides centralized configuration management for the QME system,
including environment-specific settings, validation, and secure configuration handling.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass

# Optional dependencies with graceful degradation
try:
    from src.infrastructure.monitoring.structured_logger import extraction_logger
except ImportError:
    extraction_logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


@dataclass
class ConfigurationValidationRule:
    """Configuration validation rule."""
    key: str
    required: bool = True
    data_type: type = str
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    validation_function: Optional[callable] = None


class ConfigurationService:
    """
    Centralized configuration service for the QME system.
    
    Features:
    - Environment-specific configuration loading
    - Configuration validation and type checking
    - Secure configuration handling
    - Configuration caching and hot-reloading
    - Default value management
    - Configuration export and backup
    """
    
    def __init__(self, 
                 config_directory: str = "config",
                 environment: Optional[Environment] = None):
        """Initialize the configuration service."""
        self.config_directory = Path(config_directory)
        self.environment = environment or self._detect_environment()
        
        # Configuration storage
        self.config_data: Dict[str, Any] = {}
        self.validation_rules: List[ConfigurationValidationRule] = []
        
        # Load configurations
        self._load_configurations()
        self._setup_validation_rules()
        
        extraction_logger.info(
            "Initialized ConfigurationService",
            extra_data={
                "config_directory": str(self.config_directory),
                "environment": self.environment.value,
                "config_keys": list(self.config_data.keys())
            }
        )
    
    def _detect_environment(self) -> Environment:
        """Detect the current environment."""
        env_var = os.getenv("QME_ENVIRONMENT", "development").lower()
        
        try:
            return Environment(env_var)
        except ValueError:
            extraction_logger.warning(f"Unknown environment '{env_var}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_configurations(self) -> None:
        """Load configurations from various sources."""
        # Load base configuration
        self._load_base_config()
        
        # Load environment-specific configuration
        self._load_environment_config()
        
        # Load environment variables
        self._load_environment_variables()
        
        # Load local overrides
        self._load_local_overrides()
    
    def _load_base_config(self) -> None:
        """Load base configuration."""
        base_config_file = self.config_directory / "base_config.yaml"
        
        if base_config_file.exists():
            try:
                with open(base_config_file, 'r') as f:
                    base_config = yaml.safe_load(f)
                    self.config_data.update(base_config or {})
                extraction_logger.debug(f"Loaded base configuration from {base_config_file}")
            except Exception as e:
                extraction_logger.error(f"Failed to load base configuration: {str(e)}")
        else:
            # Use default base configuration
            self.config_data.update(self._get_default_base_config())
    
    def _load_environment_config(self) -> None:
        """Load environment-specific configuration."""
        env_config_file = self.config_directory / "environments" / f"{self.environment.value}.yaml"
        
        if env_config_file.exists():
            try:
                with open(env_config_file, 'r') as f:
                    env_config = yaml.safe_load(f)
                    self._deep_merge(self.config_data, env_config or {})
                extraction_logger.debug(f"Loaded environment configuration from {env_config_file}")
            except Exception as e:
                extraction_logger.error(f"Failed to load environment configuration: {str(e)}")
    
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "QME_DATABASE_URL": "database.url",
            "QME_API_KEY": "api.key",
            "QME_OPENROUTER_API_KEY": "openrouter.api_key",
            "QME_GEMINI_API_KEY": "gemini.api_key",
            "QME_LOG_LEVEL": "logging.level",
            "QME_DEBUG": "debug",
            "QME_MAX_WORKERS": "processing.max_workers",
            "QME_TIMEOUT": "processing.timeout"
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(self.config_data, config_key, env_value)
                extraction_logger.debug(f"Set configuration from environment variable: {env_var}")
    
    def _load_local_overrides(self) -> None:
        """Load local configuration overrides."""
        local_config_file = self.config_directory / "local_config.yaml"
        
        if local_config_file.exists():
            try:
                with open(local_config_file, 'r') as f:
                    local_config = yaml.safe_load(f)
                    self._deep_merge(self.config_data, local_config or {})
                extraction_logger.debug(f"Loaded local configuration overrides from {local_config_file}")
            except Exception as e:
                extraction_logger.error(f"Failed to load local configuration: {str(e)}")
    
    def _setup_validation_rules(self) -> None:
        """Setup configuration validation rules."""
        self.validation_rules = [
            # Database configuration
            ConfigurationValidationRule(
                key="database.url",
                required=True,
                data_type=str
            ),
            
            # API configuration
            ConfigurationValidationRule(
                key="api.timeout",
                required=False,
                data_type=int,
                min_value=1,
                max_value=300
            ),
            
            # Processing configuration
            ConfigurationValidationRule(
                key="processing.max_workers",
                required=False,
                data_type=int,
                min_value=1,
                max_value=20
            ),
            
            # Logging configuration
            ConfigurationValidationRule(
                key="logging.level",
                required=False,
                data_type=str,
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            
            # Quality thresholds
            ConfigurationValidationRule(
                key="quality.minimum_score",
                required=False,
                data_type=float,
                min_value=0.0,
                max_value=1.0
            )
        ]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        try:
            return self._get_nested_value(self.config_data, key, default)
        except Exception as e:
            extraction_logger.warning(f"Failed to get configuration key '{key}': {str(e)}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        try:
            self._set_nested_value(self.config_data, key, value)
            extraction_logger.debug(f"Set configuration key '{key}' to '{value}'")
        except Exception as e:
            extraction_logger.error(f"Failed to set configuration key '{key}': {str(e)}")
            raise ConfigurationError(f"Failed to set configuration key '{key}': {str(e)}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration against rules."""
        validation_errors = []
        
        for rule in self.validation_rules:
            try:
                value = self.get(rule.key)
                
                # Check if required value is present
                if rule.required and value is None:
                    validation_errors.append(f"Required configuration key '{rule.key}' is missing")
                    continue
                
                # Skip validation if value is None and not required
                if value is None:
                    continue
                
                # Check data type
                if not isinstance(value, rule.data_type):
                    try:
                        # Try to convert to expected type
                        if rule.data_type == int:
                            value = int(value)
                        elif rule.data_type == float:
                            value = float(value)
                        elif rule.data_type == bool:
                            value = str(value).lower() in ('true', '1', 'yes', 'on')
                        elif rule.data_type == str:
                            value = str(value)
                        
                        # Update the configuration with converted value
                        self.set(rule.key, value)
                    except (ValueError, TypeError):
                        validation_errors.append(
                            f"Configuration key '{rule.key}' has invalid type. "
                            f"Expected {rule.data_type.__name__}, got {type(value).__name__}"
                        )
                        continue
                
                # Check allowed values
                if rule.allowed_values and value not in rule.allowed_values:
                    validation_errors.append(
                        f"Configuration key '{rule.key}' has invalid value '{value}'. "
                        f"Allowed values: {rule.allowed_values}"
                    )
                
                # Check numeric ranges
                if rule.data_type in (int, float):
                    if rule.min_value is not None and value < rule.min_value:
                        validation_errors.append(
                            f"Configuration key '{rule.key}' value {value} is below minimum {rule.min_value}"
                        )
                    
                    if rule.max_value is not None and value > rule.max_value:
                        validation_errors.append(
                            f"Configuration key '{rule.key}' value {value} is above maximum {rule.max_value}"
                        )
                
                # Custom validation function
                if rule.validation_function:
                    try:
                        if not rule.validation_function(value):
                            validation_errors.append(
                                f"Configuration key '{rule.key}' failed custom validation"
                            )
                    except Exception as e:
                        validation_errors.append(
                            f"Configuration key '{rule.key}' validation function error: {str(e)}"
                        )
                        
            except Exception as e:
                validation_errors.append(f"Error validating configuration key '{rule.key}': {str(e)}")
        
        return validation_errors
    
    def reload_configuration(self) -> bool:
        """Reload configuration from files."""
        try:
            old_config = self.config_data.copy()
            self.config_data.clear()
            self._load_configurations()
            
            # Validate new configuration
            validation_errors = self.validate_configuration()
            if validation_errors:
                # Restore old configuration if validation fails
                self.config_data = old_config
                extraction_logger.error(f"Configuration reload failed validation: {validation_errors}")
                return False
            
            extraction_logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            extraction_logger.error(f"Failed to reload configuration: {str(e)}")
            return False
    
    def export_configuration(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export configuration for backup or analysis."""
        config_copy = self.config_data.copy()
        
        if not include_sensitive:
            # Remove sensitive keys
            sensitive_keys = ["api.key", "openrouter.api_key", "gemini.api_key", "database.password"]
            for key in sensitive_keys:
                try:
                    self._delete_nested_value(config_copy, key)
                except KeyError:
                    pass  # Key doesn't exist
        
        return {
            "environment": self.environment.value,
            "configuration": config_copy,
            "export_timestamp": str(datetime.now()),
            "validation_status": len(self.validate_configuration()) == 0
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get_section("database")
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.get_section("api")
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.get_section("processing")
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get_section("logging")
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality configuration."""
        return self.get_section("quality")
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _delete_nested_value(self, data: Dict[str, Any], key: str) -> None:
        """Delete nested value using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                return
            current = current[k]
        
        if keys[-1] in current:
            del current[keys[-1]]
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dictionary into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _get_default_base_config(self) -> Dict[str, Any]:
        """Get default base configuration."""
        return {
            "database": {
                "url": "sqlite:///data/database/documents.db",
                "pool_size": 5,
                "timeout": 30
            },
            "api": {
                "timeout": 60,
                "max_retries": 3,
                "retry_delay": 1.0
            },
            "processing": {
                "max_workers": 4,
                "timeout": 300,
                "batch_size": 10
            },
            "logging": {
                "level": "INFO",
                "format": "structured",
                "max_file_size": "10MB",
                "max_files": 10
            },
            "quality": {
                "minimum_score": 0.7,
                "completeness_threshold": 0.8,
                "accuracy_threshold": 0.85
            },
            "storage": {
                "base_path": "results",
                "compression": False,
                "retention_days": 365
            },
            "security": {
                "encrypt_sensitive_data": True,
                "api_key_rotation_days": 90
            }
        }


# Factory function for creating configuration service
def create_configuration_service(
    config_directory: str = "config",
    environment: Optional[Environment] = None
) -> ConfigurationService:
    """Factory function to create configuration service."""
    return ConfigurationService(
        config_directory=config_directory,
        environment=environment
    )