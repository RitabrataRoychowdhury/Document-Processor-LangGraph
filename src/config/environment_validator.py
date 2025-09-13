"""
Environment configuration validator.

This module validates that all required environment variables and configuration
settings are properly configured for the system to function correctly.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .app_config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of environment validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


@dataclass
class ConfigRequirement:
    """Configuration requirement definition."""
    name: str
    description: str
    required: bool
    validator: Optional[callable] = None
    recommendation: Optional[str] = None


class EnvironmentValidator:
    """Validates environment configuration and settings."""
    
    def __init__(self):
        """Initialize environment validator."""
        self.requirements = self._define_requirements()
    
    def _define_requirements(self) -> List[ConfigRequirement]:
        """Define configuration requirements."""
        return [
            # Database configuration
            ConfigRequirement(
                name="DATABASE_PATH",
                description="Path to SQLite database file",
                required=True,
                validator=self._validate_database_path,
                recommendation="Use 'data/database/documents.db' for default setup"
            ),
            
            # API Keys based on provider selection
            ConfigRequirement(
                name="GEMINI_API_KEY",
                description="Google Gemini API key for QA provider",
                required=False,  # Conditional based on QA_PROVIDER
                validator=self._validate_gemini_api_key,
                recommendation="Required when QA_PROVIDER=gemini. Get key from Google AI Studio"
            ),
            
            ConfigRequirement(
                name="OPENAI_API_KEY",
                description="OpenAI API key for embeddings/QA",
                required=False,  # Conditional based on providers
                validator=self._validate_openai_api_key,
                recommendation="Required when EMBEDDING_PROVIDER=openai or QA_PROVIDER=openai"
            ),
            
            # Provider configuration
            ConfigRequirement(
                name="EMBEDDING_PROVIDER",
                description="Embedding provider selection",
                required=True,
                validator=self._validate_embedding_provider,
                recommendation="Use 'local' for offline operation or 'openai' for better quality"
            ),
            
            ConfigRequirement(
                name="QA_PROVIDER",
                description="QA provider selection",
                required=True,
                validator=self._validate_qa_provider,
                recommendation="Use 'gemini' for best results, 'openai' as alternative"
            ),
            
            # File processing configuration
            ConfigRequirement(
                name="MAX_FILE_SIZE_MB",
                description="Maximum file size for processing",
                required=False,
                validator=self._validate_max_file_size,
                recommendation="Default 10MB is suitable for most documents"
            ),
            
            ConfigRequirement(
                name="ALLOWED_FILE_TYPES",
                description="Comma-separated list of allowed file types",
                required=False,
                validator=self._validate_allowed_file_types,
                recommendation="Default 'pdf,docx,txt' covers most use cases"
            ),
            
            # Directory structure
            ConfigRequirement(
                name="DATA_DIRECTORIES",
                description="Required data directories exist",
                required=True,
                validator=self._validate_data_directories,
                recommendation="Ensure data/documents and data/database directories exist"
            ),
            
            # Canonical documents
            ConfigRequirement(
                name="CANONICAL_DOCUMENTS",
                description="Canonical medical documents for knowledge base",
                required=False,
                validator=self._validate_canonical_documents,
                recommendation="Place AMAGuides 5th Edition.pdf, QME-Study-Guide.pdf, Sample3.pdf in project root"
            )
        ]
    
    def validate_environment(self, config: AppConfig) -> ValidationResult:
        """Validate complete environment configuration."""
        errors = []
        warnings = []
        recommendations = []
        
        for requirement in self.requirements:
            try:
                # Check if requirement is conditionally required
                if self._is_conditionally_required(requirement, config):
                    requirement.required = True
                
                # Run validator if provided
                if requirement.validator:
                    result = requirement.validator(config)
                    
                    if result is False and requirement.required:
                        errors.append(f"{requirement.name}: {requirement.description} - FAILED")
                        if requirement.recommendation:
                            recommendations.append(f"{requirement.name}: {requirement.recommendation}")
                    elif result is False and not requirement.required:
                        warnings.append(f"{requirement.name}: {requirement.description} - WARNING")
                        if requirement.recommendation:
                            recommendations.append(f"{requirement.name}: {requirement.recommendation}")
                    elif isinstance(result, str):
                        # Validator returned a specific message
                        if requirement.required:
                            errors.append(f"{requirement.name}: {result}")
                        else:
                            warnings.append(f"{requirement.name}: {result}")
                
            except Exception as e:
                error_msg = f"{requirement.name}: Validation error - {str(e)}"
                if requirement.required:
                    errors.append(error_msg)
                else:
                    warnings.append(error_msg)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _is_conditionally_required(self, requirement: ConfigRequirement, config: AppConfig) -> bool:
        """Check if a requirement is conditionally required based on configuration."""
        if requirement.name == "GEMINI_API_KEY":
            return config.qa_provider == "gemini"
        elif requirement.name == "OPENAI_API_KEY":
            return config.qa_provider == "openai" or config.embedding_provider == "openai"
        
        return False
    
    def _validate_database_path(self, config: AppConfig) -> bool:
        """Validate database path configuration."""
        if not config.database_path:
            return False
        
        db_path = Path(config.database_path)
        
        # Check if parent directory exists or can be created
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def _validate_gemini_api_key(self, config: AppConfig) -> bool:
        """Validate Gemini API key."""
        if config.qa_provider != "gemini":
            return True  # Not required
        
        if not config.gemini_api_key:
            return False
        
        # Basic format validation (Gemini keys typically start with specific patterns)
        if len(config.gemini_api_key) < 20:
            return "API key appears too short"
        
        return True
    
    def _validate_openai_api_key(self, config: AppConfig) -> bool:
        """Validate OpenAI API key."""
        needs_openai = (config.qa_provider == "openai" or 
                       config.embedding_provider == "openai")
        
        if not needs_openai:
            return True  # Not required
        
        if not config.openai_api_key:
            return False
        
        # Basic format validation (OpenAI keys start with 'sk-')
        if not config.openai_api_key.startswith('sk-'):
            return "OpenAI API key should start with 'sk-'"
        
        if len(config.openai_api_key) < 40:
            return "API key appears too short"
        
        return True
    
    def _validate_embedding_provider(self, config: AppConfig) -> bool:
        """Validate embedding provider configuration."""
        valid_providers = ["local", "openai"]
        
        if config.embedding_provider not in valid_providers:
            return f"Invalid embedding provider. Must be one of: {', '.join(valid_providers)}"
        
        return True
    
    def _validate_qa_provider(self, config: AppConfig) -> bool:
        """Validate QA provider configuration."""
        valid_providers = ["gemini", "openai", "local"]
        
        if config.qa_provider not in valid_providers:
            return f"Invalid QA provider. Must be one of: {', '.join(valid_providers)}"
        
        return True
    
    def _validate_max_file_size(self, config: AppConfig) -> bool:
        """Validate maximum file size configuration."""
        if config.max_file_size_mb <= 0:
            return "Maximum file size must be greater than 0"
        
        if config.max_file_size_mb > 100:
            return "Maximum file size is very large (>100MB), consider reducing for performance"
        
        return True
    
    def _validate_allowed_file_types(self, config: AppConfig) -> bool:
        """Validate allowed file types configuration."""
        if not config.allowed_file_types:
            return "No allowed file types configured"
        
        supported_types = ["pdf", "docx", "txt"]
        unsupported = [ft for ft in config.allowed_file_types if ft not in supported_types]
        
        if unsupported:
            return f"Unsupported file types: {', '.join(unsupported)}. Supported: {', '.join(supported_types)}"
        
        return True
    
    def _validate_data_directories(self, config: AppConfig) -> bool:
        """Validate required data directories exist."""
        required_dirs = [
            "data",
            "data/database",
            "data/documents",
            "logs"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                except Exception:
                    missing_dirs.append(dir_path)
        
        if missing_dirs:
            return f"Cannot create required directories: {', '.join(missing_dirs)}"
        
        return True
    
    def _validate_canonical_documents(self, config: AppConfig) -> bool:
        """Validate canonical documents availability."""
        canonical_docs = [
            "AMAGuides 5th Edition.pdf",
            "QME-Study-Guide.pdf",
            "Sample3.pdf"
        ]
        
        missing_docs = []
        for doc in canonical_docs:
            if not Path(doc).exists():
                missing_docs.append(doc)
        
        if missing_docs:
            return f"Missing canonical documents: {', '.join(missing_docs)}"
        
        return True
    
    def generate_setup_instructions(self, validation_result: ValidationResult) -> str:
        """Generate setup instructions based on validation results."""
        instructions = []
        
        if not validation_result.is_valid:
            instructions.append("SETUP REQUIRED - The following issues must be resolved:")
            instructions.append("")
            
            for error in validation_result.errors:
                instructions.append(f"❌ {error}")
            
            instructions.append("")
        
        if validation_result.warnings:
            instructions.append("WARNINGS - The following issues should be addressed:")
            instructions.append("")
            
            for warning in validation_result.warnings:
                instructions.append(f"⚠️  {warning}")
            
            instructions.append("")
        
        if validation_result.recommendations:
            instructions.append("RECOMMENDATIONS:")
            instructions.append("")
            
            for rec in validation_result.recommendations:
                instructions.append(f"💡 {rec}")
            
            instructions.append("")
        
        # Add general setup instructions
        instructions.extend([
            "SETUP STEPS:",
            "",
            "1. Create .env file from .env.example:",
            "   cp .env.example .env",
            "",
            "2. Edit .env file with your API keys:",
            "   - Set GEMINI_API_KEY if using Gemini for QA",
            "   - Set OPENAI_API_KEY if using OpenAI for embeddings/QA",
            "",
            "3. Place canonical documents in project root:",
            "   - AMAGuides 5th Edition.pdf",
            "   - QME-Study-Guide.pdf",
            "   - Sample3.pdf",
            "",
            "4. Run deployment script:",
            "   ./scripts/deploy.sh",
            "",
            "5. Or start manually:",
            "   streamlit run src/ui/main_app.py"
        ])
        
        return "\n".join(instructions)


def validate_environment_config(config: AppConfig) -> ValidationResult:
    """Validate environment configuration."""
    validator = EnvironmentValidator()
    return validator.validate_environment(config)


def print_validation_results(validation_result: ValidationResult):
    """Print validation results to console."""
    if validation_result.is_valid:
        logger.info("✅ Environment configuration is valid")
    else:
        logger.error("❌ Environment configuration has errors")
    
    for error in validation_result.errors:
        logger.error(f"ERROR: {error}")
    
    for warning in validation_result.warnings:
        logger.warning(f"WARNING: {warning}")
    
    for rec in validation_result.recommendations:
        logger.info(f"RECOMMENDATION: {rec}")


def ensure_environment_ready(config: AppConfig) -> bool:
    """Ensure environment is ready for system startup."""
    validation_result = validate_environment_config(config)
    
    if not validation_result.is_valid:
        logger.error("Environment validation failed. System cannot start.")
        print_validation_results(validation_result)
        
        validator = EnvironmentValidator()
        instructions = validator.generate_setup_instructions(validation_result)
        print("\n" + instructions)
        
        return False
    
    if validation_result.warnings:
        logger.warning("Environment has warnings but can start")
        print_validation_results(validation_result)
    
    return True