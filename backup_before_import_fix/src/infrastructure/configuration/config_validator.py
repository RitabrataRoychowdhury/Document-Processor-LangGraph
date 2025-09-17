"""
Configuration validation service for the QME system.

This module provides comprehensive configuration validation against schema definitions
with clear error messages and environment-specific validation rules.
"""

import yaml
import os
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a configuration validation issue."""
    path: str
    message: str
    severity: ValidationSeverity
    expected: Optional[Any] = None
    actual: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings_count: int = 0
    errors_count: int = 0
    
    def __post_init__(self):
        self.warnings_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)
        self.errors_count = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)


class ConfigValidator:
    """Configuration validator with schema-based validation."""
    
    def __init__(self, schema_path: str = "config/schema.yaml"):
        self.schema_path = schema_path
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the configuration schema."""
        try:
            with open(self.schema_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing schema file: {e}")
            return {}
    
    def validate_config(self, config: Dict[str, Any], environment: str = "development") -> ValidationResult:
        """Validate configuration against schema."""
        issues = []
        
        # Validate against schema
        issues.extend(self._validate_against_schema(config, self.schema, ""))
        
        # Environment-specific validation
        issues.extend(self._validate_environment_specific(config, environment))
        
        # Cross-field validation
        issues.extend(self._validate_cross_fields(config))
        
        # Security validation
        issues.extend(self._validate_security(config, environment))
        
        errors_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        is_valid = errors_count == 0
        
        return ValidationResult(is_valid=is_valid, issues=issues)
    
    def _validate_against_schema(self, config: Dict[str, Any], schema: Dict[str, Any], path: str) -> List[ValidationIssue]:
        """Validate configuration against schema definition."""
        issues = []
        
        for key, schema_def in schema.items():
            if key == "schema_version":
                continue
                
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(schema_def, dict) and "type" in schema_def:
                issues.extend(self._validate_field(config, key, schema_def, current_path))
            elif isinstance(schema_def, dict):
                # Nested object
                if key in config and isinstance(config[key], dict):
                    issues.extend(self._validate_against_schema(config[key], schema_def, current_path))
        
        return issues
    
    def _validate_field(self, config: Dict[str, Any], key: str, schema_def: Dict[str, Any], path: str) -> List[ValidationIssue]:
        """Validate a single field against its schema definition."""
        issues = []
        
        # Check if required field is present
        if schema_def.get("required", False) and key not in config:
            issues.append(ValidationIssue(
                path=path,
                message=f"Required field '{key}' is missing",
                severity=ValidationSeverity.ERROR
            ))
            return issues
        
        if key not in config:
            return issues
        
        value = config[key]
        field_type = schema_def.get("type")
        
        # Type validation
        if field_type == "string" and not isinstance(value, str):
            issues.append(ValidationIssue(
                path=path,
                message=f"Field '{key}' must be a string",
                severity=ValidationSeverity.ERROR,
                expected="string",
                actual=type(value).__name__
            ))
        elif field_type == "integer" and not isinstance(value, int):
            issues.append(ValidationIssue(
                path=path,
                message=f"Field '{key}' must be an integer",
                severity=ValidationSeverity.ERROR,
                expected="integer",
                actual=type(value).__name__
            ))
        elif field_type == "number" and not isinstance(value, (int, float)):
            issues.append(ValidationIssue(
                path=path,
                message=f"Field '{key}' must be a number",
                severity=ValidationSeverity.ERROR,
                expected="number",
                actual=type(value).__name__
            ))
        elif field_type == "boolean" and not isinstance(value, bool):
            issues.append(ValidationIssue(
                path=path,
                message=f"Field '{key}' must be a boolean",
                severity=ValidationSeverity.ERROR,
                expected="boolean",
                actual=type(value).__name__
            ))
        
        # Range validation
        if isinstance(value, (int, float)):
            minimum = schema_def.get("minimum")
            maximum = schema_def.get("maximum")
            
            if minimum is not None and value < minimum:
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' value {value} is below minimum {minimum}",
                    severity=ValidationSeverity.ERROR,
                    expected=f">= {minimum}",
                    actual=value
                ))
            
            if maximum is not None and value > maximum:
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' value {value} is above maximum {maximum}",
                    severity=ValidationSeverity.ERROR,
                    expected=f"<= {maximum}",
                    actual=value
                ))
        
        # String validation
        if isinstance(value, str):
            min_length = schema_def.get("minLength")
            max_length = schema_def.get("maxLength")
            pattern = schema_def.get("pattern")
            enum_values = schema_def.get("enum")
            
            if min_length is not None and len(value) < min_length:
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' length {len(value)} is below minimum {min_length}",
                    severity=ValidationSeverity.ERROR
                ))
            
            if max_length is not None and len(value) > max_length:
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' length {len(value)} is above maximum {max_length}",
                    severity=ValidationSeverity.ERROR
                ))
            
            if pattern and not re.match(pattern, value):
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' value '{value}' does not match pattern '{pattern}'",
                    severity=ValidationSeverity.ERROR
                ))
            
            if enum_values and value not in enum_values:
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Field '{key}' value '{value}' is not in allowed values: {enum_values}",
                    severity=ValidationSeverity.ERROR,
                    expected=enum_values,
                    actual=value
                ))
        
        return issues
    
    def _validate_environment_specific(self, config: Dict[str, Any], environment: str) -> List[ValidationIssue]:
        """Validate environment-specific requirements."""
        issues = []
        
        if environment == "production":
            # Production-specific validations
            if config.get("app", {}).get("debug", False):
                issues.append(ValidationIssue(
                    path="app.debug",
                    message="Debug mode should be disabled in production",
                    severity=ValidationSeverity.WARNING
                ))
            
            if config.get("app", {}).get("log_level") == "DEBUG":
                issues.append(ValidationIssue(
                    path="app.log_level",
                    message="Debug log level should not be used in production",
                    severity=ValidationSeverity.WARNING
                ))
            
            # Database validation for production
            db_config = config.get("database", {})
            if db_config.get("type") == "sqlite":
                issues.append(ValidationIssue(
                    path="database.type",
                    message="SQLite is not recommended for production use",
                    severity=ValidationSeverity.WARNING
                ))
            
            # Security validation for production
            security_config = config.get("security", {})
            if not security_config.get("enable_encryption", False):
                issues.append(ValidationIssue(
                    path="security.enable_encryption",
                    message="Encryption should be enabled in production",
                    severity=ValidationSeverity.ERROR
                ))
        
        return issues
    
    def _validate_cross_fields(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate relationships between different configuration fields."""
        issues = []
        
        # Validate threshold relationships
        validation_config = config.get("validation", {})
        confidence_threshold = validation_config.get("confidence_threshold", 0.8)
        flagged_threshold = validation_config.get("flagged_threshold", 0.5)
        
        if confidence_threshold <= flagged_threshold:
            issues.append(ValidationIssue(
                path="validation",
                message=f"Confidence threshold ({confidence_threshold}) must be greater than flagged threshold ({flagged_threshold})",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate database configuration completeness
        db_config = config.get("database", {})
        db_type = db_config.get("type")
        
        if db_type in ["postgresql", "mysql"]:
            required_fields = ["host", "database", "username", "password"]
            for field in required_fields:
                if not db_config.get(field):
                    issues.append(ValidationIssue(
                        path=f"database.{field}",
                        message=f"Field '{field}' is required for {db_type} database",
                        severity=ValidationSeverity.ERROR
                    ))
        
        return issues
    
    def _validate_security(self, config: Dict[str, Any], environment: str) -> List[ValidationIssue]:
        """Validate security-related configuration."""
        issues = []
        
        # Check for environment variables in sensitive fields
        sensitive_paths = [
            "database.password",
            "api.openrouter.api_key"
        ]
        
        for path in sensitive_paths:
            value = self._get_nested_value(config, path)
            if value and isinstance(value, str) and not value.startswith("${"):
                issues.append(ValidationIssue(
                    path=path,
                    message=f"Sensitive field '{path}' should use environment variable substitution",
                    severity=ValidationSeverity.WARNING if environment == "development" else ValidationSeverity.ERROR
                ))
        
        return issues
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get a nested configuration value by dot-separated path."""
        keys = path.split(".")
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def format_validation_report(self, result: ValidationResult) -> str:
        """Format validation result as a human-readable report."""
        if result.is_valid:
            report = "✅ Configuration validation passed"
            if result.warnings_count > 0:
                report += f" with {result.warnings_count} warning(s)"
        else:
            report = f"❌ Configuration validation failed with {result.errors_count} error(s)"
            if result.warnings_count > 0:
                report += f" and {result.warnings_count} warning(s)"
        
        report += "\n\n"
        
        # Group issues by severity
        errors = [issue for issue in result.issues if issue.severity == ValidationSeverity.ERROR]
        warnings = [issue for issue in result.issues if issue.severity == ValidationSeverity.WARNING]
        
        if errors:
            report += "ERRORS:\n"
            for issue in errors:
                report += f"  ❌ {issue.path}: {issue.message}\n"
                if issue.expected and issue.actual:
                    report += f"     Expected: {issue.expected}, Got: {issue.actual}\n"
            report += "\n"
        
        if warnings:
            report += "WARNINGS:\n"
            for issue in warnings:
                report += f"  ⚠️  {issue.path}: {issue.message}\n"
            report += "\n"
        
        return report