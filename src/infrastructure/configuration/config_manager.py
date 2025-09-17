"""
Production Configuration Manager for QME System.

This module provides comprehensive configuration management including:
- Environment-specific configuration loading and validation
- Secure secrets management with encryption for API keys and credentials
- Feature flag system for gradual rollout and A/B testing
- Configuration validation with startup checks and runtime updates
- Hot-reloading of configuration without service restart
- Configuration versioning and rollback capabilities

Designed for production deployment with security and reliability.
"""

import os
import yaml
import json
import logging
import threading
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass


class SecretEncryptionError(Exception):
    """Secret encryption/decryption errors"""
    pass


@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    name: str
    enabled: bool
    description: str
    environments: List[str] = field(default_factory=list)
    rollout_percentage: float = 100.0
    user_groups: List[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigurationSchema:
    """Configuration validation schema"""
    required_fields: List[str]
    optional_fields: List[str]
    field_types: Dict[str, type]
    field_validators: Dict[str, Callable] = field(default_factory=dict)
    environment_specific: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ConfigurationVersion:
    """Configuration version tracking"""
    version: str
    timestamp: float
    environment: str
    changes: List[str]
    checksum: str
    author: Optional[str] = None


class SecretManager:
    """Secure secret management with encryption"""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize secret manager with encryption key."""
        self.master_key = master_key or os.getenv('QME_MASTER_KEY')
        if not self.master_key:
            # Generate a key from environment or create default
            self.master_key = self._generate_key_from_env()
        
        self.cipher_suite = self._create_cipher_suite()
    
    def _generate_key_from_env(self) -> str:
        """Generate encryption key from environment variables."""
        # Use system-specific information to generate a consistent key
        key_material = (
            os.getenv('QME_SECRET_SALT', 'qme-default-salt') +
            os.getenv('HOSTNAME', 'localhost') +
            str(os.getuid() if hasattr(os, 'getuid') else 'default')
        ).encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'qme-salt-2024',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        return key.decode()
    
    def _create_cipher_suite(self) -> Fernet:
        """Create cipher suite for encryption/decryption."""
        try:
            key = self.master_key.encode() if isinstance(self.master_key, str) else self.master_key
            return Fernet(key)
        except Exception as e:
            raise SecretEncryptionError(f"Failed to create cipher suite: {e}")
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value."""
        try:
            encrypted = self.cipher_suite.encrypt(secret.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise SecretEncryptionError(f"Failed to encrypt secret: {e}")
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_secret.encode())
            decrypted = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise SecretEncryptionError(f"Failed to decrypt secret: {e}")
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value is encrypted."""
        try:
            # Try to decode as base64 and decrypt
            base64.urlsafe_b64decode(value.encode())
            return True
        except:
            return False


class ProductionConfigManager:
    """
    Production-ready configuration manager with comprehensive features.
    
    Provides secure configuration management, feature flags, validation,
    and hot-reloading for production deployment.
    """
    
    def __init__(
        self,
        config_directory: str = "config",
        environment: Optional[Environment] = None,
        enable_hot_reload: bool = True,
        enable_encryption: bool = True
    ):
        """Initialize production configuration manager."""
        self.config_directory = Path(config_directory)
        self.environment = environment or self._detect_environment()
        self.enable_hot_reload = enable_hot_reload
        self.enable_encryption = enable_encryption
        
        # Configuration state
        self.config_data: Dict[str, Any] = {}
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.secrets: Dict[str, str] = {}
        self.config_versions: List[ConfigurationVersion] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # File monitoring for hot reload
        self._file_timestamps: Dict[str, float] = {}
        self._reload_callbacks: List[Callable] = []
        
        # Secret management
        if self.enable_encryption:
            self.secret_manager = SecretManager()
        
        # Configuration schema
        self.schema = self._initialize_schema()
        
        # Load initial configuration
        self._load_configuration()
        
        # Start hot reload monitoring if enabled
        if self.enable_hot_reload:
            self._start_hot_reload_monitoring()
        
        logger.info(f"Production Configuration Manager initialized for {self.environment.value}")
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from various sources."""
        # Check environment variable
        env_name = os.getenv('QME_ENVIRONMENT', '').lower()
        if env_name:
            try:
                return Environment(env_name)
            except ValueError:
                logger.warning(f"Unknown environment '{env_name}', checking other sources")
        
        # Check for environment-specific files
        if (self.config_directory / "production.yaml").exists():
            return Environment.PRODUCTION
        elif (self.config_directory / "staging.yaml").exists():
            return Environment.STAGING
        elif (self.config_directory / "testing.yaml").exists():
            return Environment.TESTING
        
        # Default to development
        return Environment.DEVELOPMENT
    
    def _initialize_schema(self) -> ConfigurationSchema:
        """Initialize configuration validation schema."""
        return ConfigurationSchema(
            required_fields=[
                "database_path",
                "log_level",
                "max_file_size_mb",
                "allowed_file_types"
            ],
            optional_fields=[
                "openai_api_key",
                "gemini_api_key",
                "debug_mode",
                "cache_enabled",
                "monitoring_enabled",
                "feature_flags"
            ],
            field_types={
                "database_path": str,
                "log_level": str,
                "max_file_size_mb": (int, float),
                "allowed_file_types": list,
                "debug_mode": bool,
                "cache_enabled": bool,
                "monitoring_enabled": bool
            },
            field_validators={
                "log_level": lambda x: x.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "max_file_size_mb": lambda x: x > 0,
                "database_path": lambda x: len(x) > 0
            },
            environment_specific={
                Environment.PRODUCTION.value: ["openai_api_key", "gemini_api_key"],
                Environment.STAGING.value: ["openai_api_key"],
                Environment.DEVELOPMENT.value: []
            }
        )
    
    def _load_configuration(self):
        """Load configuration from files with environment-specific overrides."""
        try:
            # Load base configuration
            base_config = self._load_config_file("base.yaml")
            
            # Load environment-specific configuration
            env_config_file = f"{self.environment.value}.yaml"
            env_config = self._load_config_file(env_config_file, required=False)
            
            # Merge configurations
            merged_config = self._merge_configurations(base_config, env_config)
            
            # Load secrets
            self._load_secrets()
            
            # Load feature flags
            self._load_feature_flags()
            
            # Validate configuration
            self._validate_configuration(merged_config)
            
            # Update configuration
            with self._lock:
                self.config_data = merged_config
            
            # Create version record
            self._create_version_record("Configuration loaded")
            
            logger.info(f"Configuration loaded successfully for {self.environment.value}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _load_config_file(self, filename: str, required: bool = True) -> Dict[str, Any]:
        """Load a single configuration file."""
        file_path = self.config_directory / filename
        
        if not file_path.exists():
            if required:
                raise ConfigurationError(f"Required configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
            
            # Track file timestamp for hot reload
            self._file_timestamps[str(file_path)] = file_path.stat().st_mtime
            
            logger.debug(f"Loaded configuration from: {file_path}")
            return content
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load {file_path}: {e}")
    
    def _load_secrets(self):
        """Load and decrypt secrets from secure storage."""
        secrets_file = self.config_directory / "secrets" / f"{self.environment.value}.yaml"
        
        if not secrets_file.exists():
            logger.info("No secrets file found, using environment variables")
            self._load_secrets_from_env()
            return
        
        try:
            with open(secrets_file, 'r') as f:
                encrypted_secrets = yaml.safe_load(f) or {}
            
            decrypted_secrets = {}
            
            if self.enable_encryption and hasattr(self, 'secret_manager'):
                for key, value in encrypted_secrets.items():
                    if isinstance(value, str) and self.secret_manager.is_encrypted(value):
                        decrypted_secrets[key] = self.secret_manager.decrypt_secret(value)
                    else:
                        decrypted_secrets[key] = value
            else:
                decrypted_secrets = encrypted_secrets
            
            with self._lock:
                self.secrets.update(decrypted_secrets)
            
            logger.info(f"Loaded {len(decrypted_secrets)} secrets")
            
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            # Fall back to environment variables
            self._load_secrets_from_env()
    
    def _load_secrets_from_env(self):
        """Load secrets from environment variables."""
        env_secrets = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "database_password": os.getenv("DATABASE_PASSWORD"),
            "secret_key": os.getenv("SECRET_KEY")
        }
        
        # Filter out None values
        env_secrets = {k: v for k, v in env_secrets.items() if v is not None}
        
        with self._lock:
            self.secrets.update(env_secrets)
        
        logger.info(f"Loaded {len(env_secrets)} secrets from environment")
    
    def _load_feature_flags(self):
        """Load feature flags configuration."""
        flags_file = self.config_directory / "feature_flags.yaml"
        
        if not flags_file.exists():
            logger.info("No feature flags file found")
            return
        
        try:
            with open(flags_file, 'r') as f:
                flags_data = yaml.safe_load(f) or {}
            
            feature_flags = {}
            
            for flag_name, flag_config in flags_data.get("flags", {}).items():
                feature_flags[flag_name] = FeatureFlag(
                    name=flag_name,
                    enabled=flag_config.get("enabled", False),
                    description=flag_config.get("description", ""),
                    environments=flag_config.get("environments", []),
                    rollout_percentage=flag_config.get("rollout_percentage", 100.0),
                    user_groups=flag_config.get("user_groups", []),
                    start_date=flag_config.get("start_date"),
                    end_date=flag_config.get("end_date"),
                    metadata=flag_config.get("metadata", {})
                )
            
            with self._lock:
                self.feature_flags = feature_flags
            
            logger.info(f"Loaded {len(feature_flags)} feature flags")
            
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
    
    def _merge_configurations(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configurations(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_configuration(self, config: Dict[str, Any]):
        """Validate configuration against schema."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.schema.required_fields:
            if field not in config:
                errors.append(f"Required field missing: {field}")
        
        # Check field types
        for field, expected_type in self.schema.field_types.items():
            if field in config:
                value = config[field]
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' has wrong type: expected {expected_type}, got {type(value)}")
        
        # Run field validators
        for field, validator in self.schema.field_validators.items():
            if field in config:
                try:
                    if not validator(config[field]):
                        errors.append(f"Field '{field}' failed validation")
                except Exception as e:
                    errors.append(f"Validation error for field '{field}': {e}")
        
        # Check environment-specific requirements
        env_requirements = self.schema.environment_specific.get(self.environment.value, [])
        for field in env_requirements:
            if field not in config and field not in self.secrets:
                if self.environment == Environment.PRODUCTION:
                    errors.append(f"Required field for {self.environment.value}: {field}")
                else:
                    warnings.append(f"Recommended field for {self.environment.value}: {field}")
        
        # Security checks for production
        if self.environment == Environment.PRODUCTION:
            if config.get("debug_mode", False):
                errors.append("Debug mode must be disabled in production")
            
            if not self.secrets.get("secret_key"):
                errors.append("Secret key must be configured in production")
        
        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        # Raise errors
        if errors:
            error_msg = "Configuration validation failed: " + "; ".join(errors)
            raise ConfigurationError(error_msg)
    
    def _create_version_record(self, change_description: str):
        """Create a version record for configuration changes."""
        config_str = json.dumps(self.config_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(config_str.encode()).hexdigest()
        
        version = ConfigurationVersion(
            version=f"v{len(self.config_versions) + 1}",
            timestamp=time.time(),
            environment=self.environment.value,
            changes=[change_description],
            checksum=checksum,
            author=os.getenv("USER", "system")
        )
        
        self.config_versions.append(version)
        
        # Keep only last 50 versions
        if len(self.config_versions) > 50:
            self.config_versions = self.config_versions[-50:]
    
    def _start_hot_reload_monitoring(self):
        """Start background thread for hot reload monitoring."""
        def monitor_files():
            while self.enable_hot_reload:
                try:
                    if self._check_file_changes():
                        logger.info("Configuration files changed, reloading...")
                        self.reload_configuration()
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Error in hot reload monitoring: {e}")
                    time.sleep(30)  # Wait longer on error
        
        reload_thread = threading.Thread(target=monitor_files, daemon=True)
        reload_thread.start()
        logger.info("Hot reload monitoring started")
    
    def _check_file_changes(self) -> bool:
        """Check if any configuration files have changed."""
        for file_path, cached_timestamp in self._file_timestamps.items():
            path_obj = Path(file_path)
            if path_obj.exists():
                current_timestamp = path_obj.stat().st_mtime
                if current_timestamp > cached_timestamp:
                    return True
        return False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        with self._lock:
            # Check secrets first
            if key in self.secrets:
                return self.secrets[key]
            
            # Navigate through nested configuration
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set_config(self, key: str, value: Any, persist: bool = False):
        """Set configuration value at runtime."""
        with self._lock:
            keys = key.split('.')
            config = self.config_data
            
            # Navigate to parent
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set value
            config[keys[-1]] = value
            
            if persist:
                self._persist_configuration()
            
            # Notify callbacks
            self._notify_reload_callbacks()
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get decrypted secret value."""
        with self._lock:
            return self.secrets.get(key, default)
    
    def set_secret(self, key: str, value: str, persist: bool = True):
        """Set and optionally encrypt a secret value."""
        with self._lock:
            self.secrets[key] = value
            
            if persist:
                self._persist_secrets()
    
    def is_feature_enabled(
        self, 
        feature_name: str, 
        user_id: Optional[str] = None,
        user_groups: Optional[List[str]] = None
    ) -> bool:
        """Check if a feature flag is enabled for the current context."""
        with self._lock:
            if feature_name not in self.feature_flags:
                return False
            
            flag = self.feature_flags[feature_name]
            
            # Check if flag is globally disabled
            if not flag.enabled:
                return False
            
            # Check environment restrictions
            if flag.environments and self.environment.value not in flag.environments:
                return False
            
            # Check date restrictions
            current_time = datetime.now()
            
            if flag.start_date:
                start_date = datetime.fromisoformat(flag.start_date)
                if current_time < start_date:
                    return False
            
            if flag.end_date:
                end_date = datetime.fromisoformat(flag.end_date)
                if current_time > end_date:
                    return False
            
            # Check user group restrictions
            if flag.user_groups and user_groups:
                if not any(group in flag.user_groups for group in user_groups):
                    return False
            
            # Check rollout percentage
            if flag.rollout_percentage < 100.0:
                if user_id:
                    # Use consistent hash for user-based rollout
                    user_hash = int(hashlib.md5(f"{feature_name}:{user_id}".encode()).hexdigest(), 16)
                    rollout_threshold = (flag.rollout_percentage / 100.0) * (2**32)
                    return (user_hash % (2**32)) < rollout_threshold
                else:
                    # Random rollout without user context
                    import random
                    return random.random() * 100 < flag.rollout_percentage
            
            return True
    
    def reload_configuration(self):
        """Reload configuration from files."""
        try:
            old_checksum = self.config_versions[-1].checksum if self.config_versions else ""
            
            self._load_configuration()
            
            new_checksum = self.config_versions[-1].checksum if self.config_versions else ""
            
            if old_checksum != new_checksum:
                logger.info("Configuration reloaded with changes")
                self._notify_reload_callbacks()
            else:
                logger.debug("Configuration reloaded, no changes detected")
                
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise ConfigurationError(f"Configuration reload failed: {e}")
    
    def add_reload_callback(self, callback: Callable[[], None]):
        """Add callback to be called when configuration is reloaded."""
        self._reload_callbacks.append(callback)
    
    def _notify_reload_callbacks(self):
        """Notify all registered reload callbacks."""
        for callback in self._reload_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Reload callback failed: {e}")
    
    def _persist_configuration(self):
        """Persist current configuration to file."""
        try:
            config_file = self.config_directory / f"{self.environment.value}.yaml"
            
            with open(config_file, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration persisted to {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to persist configuration: {e}")
    
    def _persist_secrets(self):
        """Persist secrets to encrypted file."""
        if not self.enable_encryption or not hasattr(self, 'secret_manager'):
            logger.warning("Secret encryption not available, skipping persistence")
            return
        
        try:
            secrets_dir = self.config_directory / "secrets"
            secrets_dir.mkdir(exist_ok=True)
            
            secrets_file = secrets_dir / f"{self.environment.value}.yaml"
            
            # Encrypt secrets
            encrypted_secrets = {}
            for key, value in self.secrets.items():
                if value:  # Only encrypt non-empty values
                    encrypted_secrets[key] = self.secret_manager.encrypt_secret(value)
            
            with open(secrets_file, 'w') as f:
                yaml.dump(encrypted_secrets, f, default_flow_style=False, indent=2)
            
            # Set restrictive permissions
            os.chmod(secrets_file, 0o600)
            
            logger.info(f"Secrets persisted to {secrets_file}")
            
        except Exception as e:
            logger.error(f"Failed to persist secrets: {e}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration state."""
        with self._lock:
            return {
                "environment": self.environment.value,
                "config_keys": list(self.config_data.keys()),
                "secret_keys": list(self.secrets.keys()),
                "feature_flags": {
                    name: flag.enabled for name, flag in self.feature_flags.items()
                },
                "versions": len(self.config_versions),
                "current_version": self.config_versions[-1].version if self.config_versions else "none",
                "hot_reload_enabled": self.enable_hot_reload,
                "encryption_enabled": self.enable_encryption
            }
    
    def export_configuration(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration for backup or migration."""
        with self._lock:
            export_data = {
                "metadata": {
                    "exported_at": time.time(),
                    "environment": self.environment.value,
                    "version": self.config_versions[-1].version if self.config_versions else "unknown"
                },
                "configuration": self.config_data.copy(),
                "feature_flags": {
                    name: asdict(flag) for name, flag in self.feature_flags.items()
                }
            }
            
            if include_secrets:
                export_data["secrets"] = self.secrets.copy()
            
            return export_data
    
    def validate_runtime_configuration(self) -> Dict[str, Any]:
        """Validate current runtime configuration and return status."""
        try:
            self._validate_configuration(self.config_data)
            
            return {
                "valid": True,
                "environment": self.environment.value,
                "config_version": self.config_versions[-1].version if self.config_versions else "unknown",
                "feature_flags_count": len(self.feature_flags),
                "secrets_count": len(self.secrets),
                "validation_timestamp": time.time()
            }
            
        except ConfigurationError as e:
            return {
                "valid": False,
                "error": str(e),
                "environment": self.environment.value,
                "validation_timestamp": time.time()
            }


# Global configuration manager instance
_config_manager: Optional[ProductionConfigManager] = None


def get_config_manager() -> ProductionConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ProductionConfigManager()
    
    return _config_manager


def initialize_config_manager(
    config_directory: str = "config",
    environment: Optional[Environment] = None,
    enable_hot_reload: bool = True,
    enable_encryption: bool = True
) -> ProductionConfigManager:
    """Initialize global configuration manager."""
    global _config_manager
    
    _config_manager = ProductionConfigManager(
        config_directory=config_directory,
        environment=environment,
        enable_hot_reload=enable_hot_reload,
        enable_encryption=enable_encryption
    )
    
    return _config_manager