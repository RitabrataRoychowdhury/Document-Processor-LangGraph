"""
Configuration Validator

This module provides comprehensive configuration validation utilities
for the QME system, ensuring all components have proper configuration.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from src.infrastructure.configuration.centralized_config_manager import config_manager
except ImportError:
    config_manager = None


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationRule:
    """Configuration validation rule."""
    key: str
    description: str
    validator: Callable[[Any], bool]
    level: ValidationLevel = ValidationLevel.ERROR
    suggestion: Optional[str] = None


@dataclass
class ValidationIssue:
    """Configuration validation issue."""
    key: str
    level: ValidationLevel
    message: str
    current_value: Any
    suggestion: Optional[str] = None


class ConfigValidator:
    """
    Comprehensive configuration validator for the QME system.
    
    This class provides detailed validation of all configuration aspects,
    including API keys, database settings, file paths, and system limits.
    """
    
    def __init__(self):
        """Initialize the configuration validator."""
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> List[ValidationRule]:
        """Setup comprehensive validation rules."""
        return [
            # API Key Validations
            ValidationRule(
                key="gemini_api_key",
                description="Gemini API key validation",
                validator=lambda x: isinstance(x, str) and len(x) > 20 and x.startswith("AIza"),
                level=ValidationLevel.WARNING,
                suggestion="Ensure Gemini API key is properly formatted and valid"
            ),
            
            ValidationRule(
                key="openrouter_api_key",
                description="OpenRouter API key validation",
                validator=lambda x: isinstance(x, str) and len(x) > 20 and x.startswith("sk-or-"),
                level=ValidationLevel.WARNING,
                suggestion="Ensure OpenRouter API key is properly formatted and valid"
            ),
            
            ValidationRule(
                key="openai_api_key",
                description="OpenAI API key validation",
                validator=lambda x: isinstance(x, str) and len(x) > 20 and x.startswith("sk-"),
                level=ValidationLevel.INFO,
                suggestion="OpenAI API key is optional but recommended for enhanced functionality"
            ),
            
            # Database Validations
            ValidationRule(
                key="database_path",
                description="Database path validation",
                validator=self._validate_database_path,
                level=ValidationLevel.ERROR,
                suggestion="Ensure database path is writable and directory exists"
            ),
            
            # File Processing Validations
            ValidationRule(
                key="max_file_size_mb",
                description="Maximum file size validation",
                validator=lambda x: isinstance(x, (int, float)) and 1 <= x <= 1000,
                level=ValidationLevel.ERROR,
                suggestion="Set maximum file size between 1 and 1000 MB"
            ),
            
            ValidationRule(
                key="allowed_file_types",
                description="Allowed file types validation",
                validator=self._validate_file_types,
                level=ValidationLevel.ERROR,
                suggestion="Ensure at least one valid file type is configured (pdf, txt, docx)"
            ),
            
            # Processing Configuration Validations
            ValidationRule(
                key="max_processing_jobs",
                description="Maximum processing jobs validation",
                validator=lambda x: isinstance(x, int) and 1 <= x <= 50,
                level=ValidationLevel.ERROR,
                suggestion="Set maximum processing jobs between 1 and 50"
            ),
            
            ValidationRule(
                key="processing_timeout_seconds",
                description="Processing timeout validation",
                validator=lambda x: isinstance(x, int) and 10 <= x <= 3600,
                level=ValidationLevel.ERROR,
                suggestion="Set processing timeout between 10 and 3600 seconds"
            ),
            
            # UI Configuration Validations
            ValidationRule(
                key="streamlit_port",
                description="Streamlit port validation",
                validator=lambda x: isinstance(x, int) and 1024 <= x <= 65535,
                level=ValidationLevel.ERROR,
                suggestion="Set Streamlit port between 1024 and 65535"
            ),
            
            # Quality Configuration Validations
            ValidationRule(
                key="quality_minimum_score",
                description="Quality minimum score validation",
                validator=lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                level=ValidationLevel.WARNING,
                suggestion="Set quality minimum score between 0.0 and 1.0"
            ),
            
            ValidationRule(
                key="quality_completeness_threshold",
                description="Quality completeness threshold validation",
                validator=lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                level=ValidationLevel.WARNING,
                suggestion="Set quality completeness threshold between 0.0 and 1.0"
            ),
            
            ValidationRule(
                key="quality_accuracy_threshold",
                description="Quality accuracy threshold validation",
                validator=lambda x: isinstance(x, (int, float)) and 0.0 <= x <= 1.0,
                level=ValidationLevel.WARNING,
                suggestion="Set quality accuracy threshold between 0.0 and 1.0"
            ),
            
            # Storage Path Validations
            ValidationRule(
                key="documents_dir",
                description="Documents directory validation",
                validator=self._validate_directory_path,
                level=ValidationLevel.ERROR,
                suggestion="Ensure documents directory exists and is writable"
            ),
            
            ValidationRule(
                key="results_dir",
                description="Results directory validation",
                validator=self._validate_directory_path,
                level=ValidationLevel.ERROR,
                suggestion="Ensure results directory exists and is writable"
            ),
            
            ValidationRule(
                key="logs_dir",
                description="Logs directory validation",
                validator=self._validate_directory_path,
                level=ValidationLevel.ERROR,
                suggestion="Ensure logs directory exists and is writable"
            ),
        ]
    
    def _validate_database_path(self, path: Any) -> bool:
        """Validate database path."""
        if not isinstance(path, str) or not path:
            return False
        
        db_path = Path(path)
        
        # Check if directory exists or can be created
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def _validate_file_types(self, file_types: Any) -> bool:
        """Validate allowed file types."""
        if not isinstance(file_types, list) or not file_types:
            return False
        
        valid_types = {'pdf', 'txt', 'docx', 'doc', 'rtf'}
        return all(isinstance(ft, str) and ft.lower() in valid_types for ft in file_types)
    
    def _validate_directory_path(self, path: Any) -> bool:
        """Validate directory path."""
        if not isinstance(path, str) or not path:
            return False
        
        dir_path = Path(path)
        
        # Check if directory exists or can be created
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return dir_path.is_dir()
        except Exception:
            return False
    
    def validate_all(self) -> List[ValidationIssue]:
        """Validate all configuration using defined rules."""
        if not config_manager:
            return [ValidationIssue(
                key="config_manager",
                level=ValidationLevel.ERROR,
                message="Configuration manager not available",
                current_value=None,
                suggestion="Ensure centralized_config_manager is properly imported"
            )]
        
        issues = []
        
        for rule in self.validation_rules:
            try:
                current_value = config_manager.get(rule.key)
                
                if not rule.validator(current_value):
                    issues.append(ValidationIssue(
                        key=rule.key,
                        level=rule.level,
                        message=f"{rule.description} failed",
                        current_value=current_value,
                        suggestion=rule.suggestion
                    ))
                    
            except Exception as e:
                issues.append(ValidationIssue(
                    key=rule.key,
                    level=ValidationLevel.ERROR,
                    message=f"Validation error for {rule.key}: {str(e)}",
                    current_value=None,
                    suggestion="Check configuration value and validation logic"
                ))
        
        return issues
    
    def validate_api_connectivity(self) -> List[ValidationIssue]:
        """Validate API connectivity and configuration."""
        issues = []
        
        if not config_manager:
            return [ValidationIssue(
                key="api_connectivity",
                level=ValidationLevel.ERROR,
                message="Cannot validate API connectivity - config manager not available",
                current_value=None
            )]
        
        # Check if at least one API is configured
        gemini_configured = config_manager.is_api_configured('gemini')
        openrouter_configured = config_manager.is_api_configured('openrouter')
        openai_configured = config_manager.is_api_configured('openai')
        
        if not (gemini_configured or openrouter_configured or openai_configured):
            issues.append(ValidationIssue(
                key="api_providers",
                level=ValidationLevel.ERROR,
                message="No API providers are configured",
                current_value=None,
                suggestion="Configure at least one API provider (Gemini, OpenRouter, or OpenAI)"
            ))
        
        # Validate individual providers
        if gemini_configured:
            api_key = config_manager.get_api_key('gemini')
            if not api_key or not api_key.startswith('AIza'):
                issues.append(ValidationIssue(
                    key="gemini_api_key",
                    level=ValidationLevel.WARNING,
                    message="Gemini API key format appears invalid",
                    current_value=f"***{api_key[-4:] if api_key and len(api_key) > 4 else ''}",
                    suggestion="Ensure Gemini API key starts with 'AIza' and is properly formatted"
                ))
        
        if openrouter_configured:
            api_key = config_manager.get_api_key('openrouter')
            if not api_key or not api_key.startswith('sk-or-'):
                issues.append(ValidationIssue(
                    key="openrouter_api_key",
                    level=ValidationLevel.WARNING,
                    message="OpenRouter API key format appears invalid",
                    current_value=f"***{api_key[-4:] if api_key and len(api_key) > 4 else ''}",
                    suggestion="Ensure OpenRouter API key starts with 'sk-or-' and is properly formatted"
                ))
        
        return issues
    
    def validate_environment_setup(self) -> List[ValidationIssue]:
        """Validate environment setup and .env file loading."""
        issues = []
        
        # Check if .env file exists
        env_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent.parent.parent / ".env"
        ]
        
        env_file_found = False
        for env_path in env_paths:
            if env_path.exists():
                env_file_found = True
                break
        
        if not env_file_found:
            issues.append(ValidationIssue(
                key="env_file",
                level=ValidationLevel.WARNING,
                message=".env file not found in expected locations",
                current_value=None,
                suggestion="Create .env file in project root with required environment variables"
            ))
        
        # Check if dotenv is available
        try:
            import dotenv
        except ImportError:
            issues.append(ValidationIssue(
                key="dotenv_package",
                level=ValidationLevel.WARNING,
                message="python-dotenv package not available",
                current_value=None,
                suggestion="Install python-dotenv package for .env file support: pip install python-dotenv"
            ))
        
        # Check critical environment variables
        critical_env_vars = [
            'GEMINI_API_KEY',
            'OPENROUTER_API_KEY',
            'DATABASE_PATH'
        ]
        
        for env_var in critical_env_vars:
            if not os.getenv(env_var):
                issues.append(ValidationIssue(
                    key=f"env_{env_var.lower()}",
                    level=ValidationLevel.INFO,
                    message=f"Environment variable {env_var} not set",
                    current_value=None,
                    suggestion=f"Set {env_var} in .env file or environment"
                ))
        
        return issues
    
    def get_validation_report(self) -> str:
        """Get comprehensive validation report."""
        all_issues = []
        
        # Validate configuration
        all_issues.extend(self.validate_all())
        
        # Validate API connectivity
        all_issues.extend(self.validate_api_connectivity())
        
        # Validate environment setup
        all_issues.extend(self.validate_environment_setup())
        
        # Group issues by level
        errors = [issue for issue in all_issues if issue.level == ValidationLevel.ERROR]
        warnings = [issue for issue in all_issues if issue.level == ValidationLevel.WARNING]
        info = [issue for issue in all_issues if issue.level == ValidationLevel.INFO]
        
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append("QME SYSTEM CONFIGURATION VALIDATION REPORT")
        report_lines.append("=" * 60)
        
        # Summary
        total_issues = len(all_issues)
        if total_issues == 0:
            report_lines.append("✅ All configuration checks passed!")
        else:
            report_lines.append(f"Found {total_issues} configuration issues:")
            report_lines.append(f"  • {len(errors)} errors")
            report_lines.append(f"  • {len(warnings)} warnings")
            report_lines.append(f"  • {len(info)} informational")
        
        # Errors
        if errors:
            report_lines.append("\n❌ ERRORS (must be fixed):")
            for issue in errors:
                report_lines.append(f"  • {issue.key}: {issue.message}")
                if issue.suggestion:
                    report_lines.append(f"    → {issue.suggestion}")
        
        # Warnings
        if warnings:
            report_lines.append("\n⚠️  WARNINGS (should be addressed):")
            for issue in warnings:
                report_lines.append(f"  • {issue.key}: {issue.message}")
                if issue.suggestion:
                    report_lines.append(f"    → {issue.suggestion}")
        
        # Info
        if info:
            report_lines.append("\nℹ️  INFORMATION (optional improvements):")
            for issue in info:
                report_lines.append(f"  • {issue.key}: {issue.message}")
                if issue.suggestion:
                    report_lines.append(f"    → {issue.suggestion}")
        
        # Configuration status
        if config_manager:
            report_lines.append("\n" + "=" * 40)
            report_lines.append("CONFIGURATION STATUS")
            report_lines.append("=" * 40)
            
            # API providers
            report_lines.append("API Providers:")
            providers = ['gemini', 'openrouter', 'openai']
            for provider in providers:
                status = "✅ Configured" if config_manager.is_api_configured(provider) else "❌ Not configured"
                report_lines.append(f"  • {provider.title()}: {status}")
            
            # Key settings
            report_lines.append("\nKey Settings:")
            key_settings = [
                ('max_file_size_mb', 'Max file size'),
                ('max_processing_jobs', 'Max processing jobs'),
                ('processing_timeout_seconds', 'Processing timeout'),
                ('debug_mode', 'Debug mode')
            ]
            
            for key, description in key_settings:
                value = config_manager.get(key)
                report_lines.append(f"  • {description}: {value}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)


# Global validator instance
config_validator = ConfigValidator()


# Convenience functions
def validate_configuration() -> List[ValidationIssue]:
    """Validate configuration and return issues."""
    return config_validator.validate_all()


def get_validation_report() -> str:
    """Get comprehensive validation report."""
    return config_validator.get_validation_report()


def validate_for_ui() -> Tuple[bool, List[str], List[str]]:
    """Validate configuration for UI components."""
    issues = config_validator.validate_all()
    
    errors = [issue.message for issue in issues if issue.level == ValidationLevel.ERROR]
    warnings = [issue.message for issue in issues if issue.level == ValidationLevel.WARNING]
    
    is_valid = len(errors) == 0
    
    return is_valid, errors, warnings