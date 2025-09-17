"""
Centralized Configuration Manager

This module provides a unified configuration management system that ensures
proper environment variable loading across all components of the QME system.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Load environment variables from .env file at module level
try:
    from dotenv import load_dotenv
    # Try to load from multiple possible locations
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",
        Path.cwd().parent / ".env"
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            env_loaded = True
            break
    
    if not env_loaded:
        # Try default load_dotenv() which searches up the directory tree
        load_dotenv()
        
except ImportError:
    # dotenv not available, will use system environment variables
    pass


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class APIProvider(Enum):
    """Supported API providers."""
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class ConfigurationValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_optional: List[str]


class CentralizedConfigManager:
    """
    Centralized configuration manager for the QME system.
    
    This class provides a single point of access for all configuration needs,
    ensuring consistent environment variable loading and validation across
    all system components.
    """
    
    def __init__(self):
        """Initialize the centralized configuration manager."""
        self.logger = logging.getLogger(__name__)
        self._config_cache: Dict[str, Any] = {}
        self._validation_cache: Optional[ConfigurationValidationResult] = None
        
        # Load and cache all configuration
        self._load_all_configuration()
        
        self.logger.info("Centralized Configuration Manager initialized")
    
    def _load_all_configuration(self) -> None:
        """Load all configuration from environment variables."""
        # API Configuration
        self._config_cache.update({
            # Gemini API
            'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
            
            # OpenRouter API
            'openrouter_api_key': os.getenv('OPENROUTER_API_KEY', ''),
            'openrouter_model': os.getenv('OPENROUTER_MODEL', 'openrouter/sonoma-sky-alpha'),
            'openrouter_base_url': os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'),
            
            # OpenAI API (if used)
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            
            # Database Configuration
            'database_path': os.getenv('DATABASE_PATH', 'data/database/documents.db'),
            'database_url': os.getenv('DATABASE_URL', 'sqlite:///data/database/documents.db'),
            
            # File Processing Configuration
            'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '10')),
            'allowed_file_types': os.getenv('ALLOWED_FILE_TYPES', 'pdf,txt,docx').split(','),
            
            # Processing Configuration
            'max_processing_jobs': int(os.getenv('MAX_PROCESSING_JOBS', '5')),
            'processing_timeout_seconds': int(os.getenv('PROCESSING_TIMEOUT_SECONDS', '300')),
            'max_workers': int(os.getenv('MAX_WORKERS', '4')),
            
            # UI Configuration
            'streamlit_port': int(os.getenv('STREAMLIT_PORT', '8501')),
            'debug_mode': os.getenv('DEBUG_MODE', 'False').lower() in ('true', '1', 'yes'),
            
            # Provider Selection
            'default_api_provider': os.getenv('DEFAULT_API_PROVIDER', 'gemini'),
            'fallback_api_provider': os.getenv('FALLBACK_API_PROVIDER', 'openrouter'),
            
            # Storage Paths
            'documents_dir': os.getenv('DOCUMENTS_DIR', 'data/documents'),
            'database_dir': os.getenv('DATABASE_DIR', 'data/database'),
            'results_dir': os.getenv('RESULTS_DIR', 'results'),
            'logs_dir': os.getenv('LOGS_DIR', 'logs'),
            
            # Logging Configuration
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_format': os.getenv('LOG_FORMAT', 'structured'),
            
            # Quality Configuration
            'quality_minimum_score': float(os.getenv('QUALITY_MINIMUM_SCORE', '0.7')),
            'quality_completeness_threshold': float(os.getenv('QUALITY_COMPLETENESS_THRESHOLD', '0.8')),
            'quality_accuracy_threshold': float(os.getenv('QUALITY_ACCURACY_THRESHOLD', '0.85')),
            
            # Security Configuration
            'encrypt_sensitive_data': os.getenv('ENCRYPT_SENSITIVE_DATA', 'True').lower() in ('true', '1', 'yes'),
            
            # Environment Detection
            'environment': os.getenv('QME_ENVIRONMENT', 'development'),
            
            # Feature Flags
            'enable_knowledge_graph': os.getenv('ENABLE_KNOWLEDGE_GRAPH', 'true').lower() in ('true', '1', 'yes'),
            'enable_performance_monitoring': os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() in ('true', '1', 'yes'),
            'enable_quality_validation': os.getenv('ENABLE_QUALITY_VALIDATION', 'true').lower() in ('true', '1', 'yes'),
        })
        
        # Normalize file types
        self._config_cache['allowed_file_types'] = [
            ft.lower().strip().lstrip('.') 
            for ft in self._config_cache['allowed_file_types']
        ]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config_cache.get(key, default)
    
    def get_required(self, key: str) -> Any:
        """Get required configuration value, raise error if missing."""
        value = self._config_cache.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ConfigurationError(f"Required configuration key '{key}' is missing or empty")
        return value
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider."""
        provider = provider.lower()
        key_mapping = {
            'gemini': 'gemini_api_key',
            'openrouter': 'openrouter_api_key',
            'openai': 'openai_api_key'
        }
        
        key = key_mapping.get(provider)
        if not key:
            return None
        
        api_key = self.get(key, '')
        return api_key if api_key else None
    
    def is_api_configured(self, provider: str) -> bool:
        """Check if API provider is properly configured."""
        api_key = self.get_api_key(provider)
        return bool(api_key)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'path': self.get('database_path'),
            'url': self.get('database_url'),
            'directory': self.get('database_dir')
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return {
            'max_jobs': self.get('max_processing_jobs'),
            'timeout_seconds': self.get('processing_timeout_seconds'),
            'max_workers': self.get('max_workers'),
            'max_file_size_mb': self.get('max_file_size_mb'),
            'allowed_file_types': self.get('allowed_file_types')
        }
    
    def get_api_config(self, provider: str) -> Dict[str, Any]:
        """Get API configuration for specified provider."""
        provider = provider.lower()
        
        base_config = {
            'api_key': self.get_api_key(provider),
            'timeout': self.get('processing_timeout_seconds', 300)
        }
        
        if provider == 'openrouter':
            base_config.update({
                'model': self.get('openrouter_model'),
                'base_url': self.get('openrouter_base_url')
            })
        
        return base_config
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return {
            'port': self.get('streamlit_port'),
            'debug_mode': self.get('debug_mode'),
            'max_file_size_mb': self.get('max_file_size_mb'),
            'allowed_file_types': self.get('allowed_file_types')
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return {
            'documents_dir': self.get('documents_dir'),
            'database_dir': self.get('database_dir'),
            'results_dir': self.get('results_dir'),
            'logs_dir': self.get('logs_dir')
        }
    
    def get_quality_config(self) -> Dict[str, Any]:
        """Get quality configuration."""
        return {
            'minimum_score': self.get('quality_minimum_score'),
            'completeness_threshold': self.get('quality_completeness_threshold'),
            'accuracy_threshold': self.get('quality_accuracy_threshold'),
            'enable_validation': self.get('enable_quality_validation')
        }
    
    def validate_configuration(self, force_refresh: bool = False) -> ConfigurationValidationResult:
        """Validate all configuration and return detailed results."""
        if self._validation_cache and not force_refresh:
            return self._validation_cache
        
        errors = []
        warnings = []
        missing_optional = []
        
        # Validate API configuration
        gemini_key = self.get_api_key('gemini')
        openrouter_key = self.get_api_key('openrouter')
        
        if not gemini_key and not openrouter_key:
            errors.append("At least one API provider (Gemini or OpenRouter) must be configured")
        
        if not gemini_key:
            warnings.append("Gemini API key not configured - Gemini provider will not be available")
        
        if not openrouter_key:
            warnings.append("OpenRouter API key not configured - OpenRouter provider will not be available")
        
        # Validate numeric values
        numeric_validations = [
            ('max_file_size_mb', 1, 1000, "Maximum file size must be between 1 and 1000 MB"),
            ('max_processing_jobs', 1, 50, "Maximum processing jobs must be between 1 and 50"),
            ('processing_timeout_seconds', 10, 3600, "Processing timeout must be between 10 and 3600 seconds"),
            ('streamlit_port', 1024, 65535, "Streamlit port must be between 1024 and 65535"),
            ('quality_minimum_score', 0.0, 1.0, "Quality minimum score must be between 0.0 and 1.0"),
            ('quality_completeness_threshold', 0.0, 1.0, "Quality completeness threshold must be between 0.0 and 1.0"),
            ('quality_accuracy_threshold', 0.0, 1.0, "Quality accuracy threshold must be between 0.0 and 1.0"),
        ]
        
        for key, min_val, max_val, error_msg in numeric_validations:
            value = self.get(key)
            if value is not None:
                try:
                    if isinstance(value, str):
                        value = float(value) if '.' in value else int(value)
                    
                    if not (min_val <= value <= max_val):
                        errors.append(f"{error_msg} (current: {value})")
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {key}: {value}")
        
        # Validate file types
        allowed_types = self.get('allowed_file_types', [])
        if not allowed_types:
            errors.append("At least one file type must be allowed")
        
        valid_file_types = ['pdf', 'txt', 'docx', 'doc', 'rtf']
        invalid_types = [ft for ft in allowed_types if ft not in valid_file_types]
        if invalid_types:
            warnings.append(f"Unknown file types configured: {invalid_types}")
        
        # Validate paths
        database_path = self.get('database_path')
        if database_path:
            db_dir = Path(database_path).parent
            if not db_dir.exists():
                try:
                    db_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create database directory {db_dir}: {str(e)}")
        
        # Validate provider selection
        default_provider = self.get('default_api_provider', '').lower()
        fallback_provider = self.get('fallback_api_provider', '').lower()
        
        valid_providers = ['gemini', 'openrouter', 'openai', 'local']
        if default_provider and default_provider not in valid_providers:
            errors.append(f"Invalid default API provider: {default_provider}")
        
        if fallback_provider and fallback_provider not in valid_providers:
            errors.append(f"Invalid fallback API provider: {fallback_provider}")
        
        if default_provider and not self.is_api_configured(default_provider) and default_provider != 'local':
            errors.append(f"Default API provider '{default_provider}' is not properly configured")
        
        # Check optional configurations
        optional_configs = [
            ('openai_api_key', 'OpenAI API integration'),
            ('encrypt_sensitive_data', 'Data encryption'),
            ('enable_performance_monitoring', 'Performance monitoring'),
        ]
        
        for key, description in optional_configs:
            if not self.get(key):
                missing_optional.append(f"{description} ({key})")
        
        result = ConfigurationValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_optional=missing_optional
        )
        
        self._validation_cache = result
        return result
    
    def get_validation_summary(self) -> str:
        """Get a human-readable validation summary."""
        result = self.validate_configuration()
        
        summary_lines = []
        
        if result.is_valid:
            summary_lines.append("✅ Configuration is valid")
        else:
            summary_lines.append("❌ Configuration has errors")
        
        if result.errors:
            summary_lines.append(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                summary_lines.append(f"  • {error}")
        
        if result.warnings:
            summary_lines.append(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                summary_lines.append(f"  • {warning}")
        
        if result.missing_optional:
            summary_lines.append(f"\nOptional configurations not set ({len(result.missing_optional)}):")
            for missing in result.missing_optional:
                summary_lines.append(f"  • {missing}")
        
        # Add configuration status
        summary_lines.append(f"\nAPI Providers:")
        summary_lines.append(f"  • Gemini: {'✅ Configured' if self.is_api_configured('gemini') else '❌ Not configured'}")
        summary_lines.append(f"  • OpenRouter: {'✅ Configured' if self.is_api_configured('openrouter') else '❌ Not configured'}")
        summary_lines.append(f"  • OpenAI: {'✅ Configured' if self.is_api_configured('openai') else '❌ Not configured'}")
        
        return "\n".join(summary_lines)
    
    def export_safe_config(self) -> Dict[str, Any]:
        """Export configuration with sensitive data masked."""
        safe_config = self._config_cache.copy()
        
        # Mask sensitive keys
        sensitive_keys = ['gemini_api_key', 'openrouter_api_key', 'openai_api_key']
        for key in sensitive_keys:
            if key in safe_config and safe_config[key]:
                safe_config[key] = f"***{safe_config[key][-4:]}" if len(safe_config[key]) > 4 else "***"
        
        return safe_config
    
    def reload_configuration(self) -> bool:
        """Reload configuration from environment variables."""
        try:
            # Clear caches
            self._config_cache.clear()
            self._validation_cache = None
            
            # Reload environment variables
            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except ImportError:
                pass
            
            # Reload configuration
            self._load_all_configuration()
            
            # Validate new configuration
            validation_result = self.validate_configuration(force_refresh=True)
            
            if validation_result.is_valid:
                self.logger.info("Configuration reloaded successfully")
                return True
            else:
                self.logger.error(f"Configuration reload failed validation: {validation_result.errors}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {str(e)}")
            return False


# Global configuration manager instance
config_manager = CentralizedConfigManager()


# Convenience functions for backward compatibility
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value."""
    return config_manager.get(key, default)


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for provider."""
    return config_manager.get_api_key(provider)


def is_api_configured(provider: str) -> bool:
    """Check if API provider is configured."""
    return config_manager.is_api_configured(provider)


def validate_configuration() -> ConfigurationValidationResult:
    """Validate configuration."""
    return config_manager.validate_configuration()


def get_validation_summary() -> str:
    """Get validation summary."""
    return config_manager.get_validation_summary()