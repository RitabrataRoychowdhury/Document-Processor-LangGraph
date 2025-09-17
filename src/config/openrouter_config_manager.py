"""
OpenRouter Configuration Management System

This module provides centralized configuration management for the OpenRouter
integration service, including prompt templates, API settings, and quality thresholds.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationMetadata:
    """Metadata for configuration files"""
    file_path: str
    last_modified: datetime
    version: str = "1.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class PromptTemplate:
    """Structured prompt template with metadata"""
    name: str
    type: str  # extraction, generation, validation
    system_prompt: str
    main_prompt: str
    validation_rules: Dict[str, str] = field(default_factory=dict)
    metadata: Optional[ConfigurationMetadata] = None
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


class OpenRouterConfigManager:
    """
    Centralized configuration manager for OpenRouter integration.
    
    Handles loading, validation, and management of:
    - API configuration
    - Prompt templates
    - Quality thresholds
    - Model settings
    """
    
    def __init__(self, config_root: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_root: Root directory for configuration files
        """
        self.config_root = Path(config_root)
        self.api_config: Optional[Dict[str, Any]] = None
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.quality_thresholds: Optional[Dict[str, float]] = None
        self._config_cache: Dict[str, Any] = {}
        
        # Ensure configuration directories exist
        self._ensure_config_structure()
    
    def _ensure_config_structure(self) -> None:
        """Ensure required configuration directory structure exists"""
        required_dirs = [
            self.config_root / "settings",
            self.config_root / "prompts" / "extraction",
            self.config_root / "prompts" / "generation", 
            self.config_root / "prompts" / "validation",
            self.config_root / "templates"
        ]
        
        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    
    def load_api_config(self, config_file: str = "openrouter_config.yaml") -> Dict[str, Any]:
        """
        Load API configuration from YAML file.
        
        Args:
            config_file: Name of the configuration file
            
        Returns:
            Dictionary containing API configuration
        """
        config_path = self.config_root / "settings" / config_file
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate configuration
            self._validate_api_config(config)
            
            self.api_config = config
            logger.info(f"Loaded API configuration from {config_path}")
            
            return config
            
        except FileNotFoundError:
            logger.error(f"API configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing API configuration: {e}")
            raise
    
    def load_prompt_template(self, prompt_type: str, template_name: str) -> PromptTemplate:
        """
        Load a specific prompt template.
        
        Args:
            prompt_type: Type of prompt (extraction, generation, validation)
            template_name: Name of the template file (without .yaml extension)
            
        Returns:
            PromptTemplate object
        """
        cache_key = f"{prompt_type}_{template_name}"
        
        if cache_key in self.prompt_templates:
            return self.prompt_templates[cache_key]
        
        template_path = self.config_root / "prompts" / prompt_type / f"{template_name}.yaml"
        
        try:
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            # Determine main prompt key based on type
            main_prompt_key = f"{prompt_type}_prompt"
            if main_prompt_key not in template_data:
                # Fallback to common prompt keys
                for key in ['extraction_prompt', 'generation_prompt', 'validation_prompt', 'compliance_prompt']:
                    if key in template_data:
                        main_prompt_key = key
                        break
                else:
                    raise ValueError(f"No main prompt found in template {template_name}")
            
            # Create metadata
            metadata = ConfigurationMetadata(
                file_path=str(template_path),
                last_modified=datetime.fromtimestamp(template_path.stat().st_mtime),
                description=template_data.get('description', ''),
                tags=template_data.get('tags', [])
            )
            
            # Create prompt template
            prompt_template = PromptTemplate(
                name=template_name,
                type=prompt_type,
                system_prompt=template_data.get('system_prompt', ''),
                main_prompt=template_data[main_prompt_key],
                validation_rules=template_data.get('validation_rules', {}),
                metadata=metadata,
                custom_parameters=template_data.get('custom_parameters', {})
            )
            
            self.prompt_templates[cache_key] = prompt_template
            logger.debug(f"Loaded prompt template: {cache_key}")
            
            return prompt_template
            
        except FileNotFoundError:
            logger.error(f"Prompt template not found: {template_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing prompt template: {e}")
            raise
    
    def load_all_prompt_templates(self) -> Dict[str, List[PromptTemplate]]:
        """
        Load all available prompt templates organized by type.
        
        Returns:
            Dictionary with prompt types as keys and lists of templates as values
        """
        templates_by_type = {}
        
        prompt_types = ['extraction', 'generation', 'validation']
        
        for prompt_type in prompt_types:
            templates_by_type[prompt_type] = []
            prompt_dir = self.config_root / "prompts" / prompt_type
            
            if prompt_dir.exists():
                for template_file in prompt_dir.glob("*.yaml"):
                    template_name = template_file.stem
                    try:
                        template = self.load_prompt_template(prompt_type, template_name)
                        templates_by_type[prompt_type].append(template)
                    except Exception as e:
                        logger.warning(f"Failed to load template {template_name}: {e}")
        
        return templates_by_type
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """
        Get quality thresholds from API configuration.
        
        Returns:
            Dictionary of quality thresholds
        """
        if self.api_config is None:
            self.load_api_config()
        
        return self.api_config.get('quality_thresholds', {
            'minimum_confidence': 0.7,
            'extraction_completeness': 0.8,
            'field_accuracy': 0.85
        })
    
    def get_model_config(self) -> Dict[str, Any]:
        """
        Get model configuration settings.
        
        Returns:
            Dictionary of model configuration
        """
        if self.api_config is None:
            self.load_api_config()
        
        return {
            'model': self.api_config['api']['model'],
            'max_tokens': self.api_config['extraction']['max_tokens'],
            'temperature': self.api_config['extraction']['temperature'],
            'top_p': self.api_config['extraction']['top_p'],
            'presence_penalty': self.api_config['extraction'].get('presence_penalty', 0.0),
            'frequency_penalty': self.api_config['extraction'].get('frequency_penalty', 0.0)
        }
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate all configuration files and return status.
        
        Returns:
            Dictionary with validation results for each configuration type
        """
        validation_results = {}
        
        # Validate API configuration
        try:
            self.load_api_config()
            validation_results['api_config'] = True
        except Exception as e:
            logger.error(f"API configuration validation failed: {e}")
            validation_results['api_config'] = False
        
        # Validate prompt templates
        try:
            templates = self.load_all_prompt_templates()
            validation_results['prompt_templates'] = len(templates) > 0
        except Exception as e:
            logger.error(f"Prompt template validation failed: {e}")
            validation_results['prompt_templates'] = False
        
        # Check for required environment variables
        validation_results['api_key'] = 'OPENROUTER_API_KEY' in os.environ
        
        return validation_results
    
    def create_prompt_template(
        self, 
        prompt_type: str, 
        template_name: str, 
        system_prompt: str,
        main_prompt: str,
        validation_rules: Optional[Dict[str, str]] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> PromptTemplate:
        """
        Create a new prompt template and save it to file.
        
        Args:
            prompt_type: Type of prompt (extraction, generation, validation)
            template_name: Name for the template
            system_prompt: System prompt text
            main_prompt: Main prompt text
            validation_rules: Optional validation rules
            description: Optional description
            tags: Optional tags for categorization
            
        Returns:
            Created PromptTemplate object
        """
        template_data = {
            'description': description,
            'tags': tags or [],
            'system_prompt': system_prompt,
            f'{prompt_type}_prompt': main_prompt,
            'validation_rules': validation_rules or {}
        }
        
        template_path = self.config_root / "prompts" / prompt_type / f"{template_name}.yaml"
        
        # Ensure directory exists
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save template
        with open(template_path, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created prompt template: {template_path}")
        
        # Load and return the template
        return self.load_prompt_template(prompt_type, template_name)
    
    def update_quality_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Update quality thresholds in the API configuration.
        
        Args:
            thresholds: Dictionary of threshold values to update
        """
        if self.api_config is None:
            self.load_api_config()
        
        # Validate threshold values
        for key, value in thresholds.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Threshold {key} must be between 0.0 and 1.0, got {value}")
        
        # Update configuration
        self.api_config['quality_thresholds'].update(thresholds)
        
        # Save updated configuration
        config_path = self.config_root / "settings" / "openrouter_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(self.api_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Updated quality thresholds: {thresholds}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all configuration settings.
        
        Returns:
            Dictionary containing configuration summary
        """
        summary = {
            'api_config_loaded': self.api_config is not None,
            'prompt_templates_count': len(self.prompt_templates),
            'configuration_validation': self.validate_configuration()
        }
        
        if self.api_config:
            summary['model'] = self.api_config['api']['model']
            summary['quality_thresholds'] = self.get_quality_thresholds()
            summary['vision_enabled'] = self.api_config.get('vision', {}).get('enabled', False)
            summary['error_handling'] = self.api_config.get('error_handling', {})
            summary['performance_monitoring'] = self.api_config.get('performance', {}).get('enable_monitoring', False)
        
        # Count templates by type
        templates_by_type = self.load_all_prompt_templates()
        summary['templates_by_type'] = {
            prompt_type: len(templates) 
            for prompt_type, templates in templates_by_type.items()
        }
        
        return summary
    
    def export_configuration(self, export_path: str) -> None:
        """
        Export all configuration settings to a single file for backup or sharing.
        
        Args:
            export_path: Path where to save the exported configuration
        """
        export_data = {
            'api_config': self.api_config,
            'prompt_templates': {},
            'export_timestamp': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        # Export all prompt templates
        templates_by_type = self.load_all_prompt_templates()
        for prompt_type, templates in templates_by_type.items():
            export_data['prompt_templates'][prompt_type] = {}
            for template in templates:
                export_data['prompt_templates'][prompt_type][template.name] = {
                    'system_prompt': template.system_prompt,
                    'main_prompt': template.main_prompt,
                    'validation_rules': template.validation_rules,
                    'custom_parameters': template.custom_parameters,
                    'metadata': {
                        'description': template.metadata.description if template.metadata else '',
                        'tags': template.metadata.tags if template.metadata else []
                    }
                }
        
        # Save export data
        with open(export_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration exported to {export_path}")
    
    def import_configuration(self, import_path: str, overwrite: bool = False) -> None:
        """
        Import configuration settings from an exported file.
        
        Args:
            import_path: Path to the configuration file to import
            overwrite: Whether to overwrite existing configurations
        """
        with open(import_path, 'r') as f:
            import_data = yaml.safe_load(f)
        
        # Import API configuration
        if 'api_config' in import_data and (overwrite or self.api_config is None):
            self.api_config = import_data['api_config']
            # Save to file
            config_path = self.config_root / "settings" / "openrouter_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(self.api_config, f, default_flow_style=False, sort_keys=False)
        
        # Import prompt templates
        if 'prompt_templates' in import_data:
            for prompt_type, templates in import_data['prompt_templates'].items():
                for template_name, template_data in templates.items():
                    if overwrite or not (self.config_root / "prompts" / prompt_type / f"{template_name}.yaml").exists():
                        self.create_prompt_template(
                            prompt_type=prompt_type,
                            template_name=template_name,
                            system_prompt=template_data['system_prompt'],
                            main_prompt=template_data['main_prompt'],
                            validation_rules=template_data.get('validation_rules', {}),
                            description=template_data.get('metadata', {}).get('description', ''),
                            tags=template_data.get('metadata', {}).get('tags', [])
                        )
        
        logger.info(f"Configuration imported from {import_path}")
    
    def optimize_configuration_for_sonoma_sky_alpha(self) -> None:
        """
        Optimize configuration settings specifically for Sonoma Sky Alpha model.
        """
        if self.api_config is None:
            self.load_api_config()
        
        # Optimize API settings for Sonoma Sky Alpha
        optimizations = {
            'api': {
                'model': 'anthropic/claude-3.5-sonnet:beta',  # Ensure correct model
                'timeout': 120,  # Longer timeout for complex documents
                'max_retries': 5,  # More retries for reliability
                'rate_limit_buffer': 1.5
            },
            'extraction': {
                'max_tokens': 8000,  # Higher token limit
                'temperature': 0.05,  # Lower for consistency
                'top_p': 0.95,
                'vision_enabled': True,
                'structured_output': True,
                'confidence_scoring': True
            },
            'quality_thresholds': {
                'minimum_confidence': 0.75,
                'extraction_completeness': 0.85,
                'field_accuracy': 0.90,
                'consistency_threshold': 0.80,
                'compliance_threshold': 0.85
            },
            'vision': {
                'enabled': True,
                'max_image_size': 20971520,  # 20MB
                'dpi': 300,
                'preprocessing': {
                    'enhance_contrast': True,
                    'noise_reduction': True,
                    'text_enhancement': True
                }
            }
        }
        
        # Apply optimizations
        for section, settings in optimizations.items():
            if section in self.api_config:
                self.api_config[section].update(settings)
            else:
                self.api_config[section] = settings
        
        # Save optimized configuration
        config_path = self.config_root / "settings" / "openrouter_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(self.api_config, f, default_flow_style=False, sort_keys=False)
        
        logger.info("Configuration optimized for Sonoma Sky Alpha model")
    
    def _validate_api_config(self, config: Dict[str, Any]) -> None:
        """Validate API configuration structure and values"""
        required_sections = ['api', 'extraction', 'quality_thresholds']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate API section
        api_config = config['api']
        required_api_fields = ['base_url', 'model', 'timeout', 'max_retries', 'retry_delay']
        
        for field in required_api_fields:
            if field not in api_config:
                raise ValueError(f"Missing required API field: {field}")
        
        # Validate numeric values
        if api_config['timeout'] <= 0:
            raise ValueError("API timeout must be positive")
        
        if api_config['max_retries'] < 0:
            raise ValueError("Max retries must be non-negative")
        
        # Validate extraction section
        extraction_config = config['extraction']
        if extraction_config.get('temperature', 0) < 0 or extraction_config.get('temperature', 0) > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if extraction_config.get('top_p', 0) < 0 or extraction_config.get('top_p', 0) > 1:
            raise ValueError("Top_p must be between 0 and 1")
        
        # Validate quality thresholds
        quality_config = config['quality_thresholds']
        for key, value in quality_config.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Quality threshold {key} must be between 0.0 and 1.0")


# Convenience functions for common operations
def get_default_config_manager() -> OpenRouterConfigManager:
    """Get default configuration manager instance"""
    return OpenRouterConfigManager()


def load_extraction_prompt(template_name: str) -> PromptTemplate:
    """Load an extraction prompt template"""
    manager = get_default_config_manager()
    return manager.load_prompt_template("extraction", template_name)


def load_generation_prompt(template_name: str) -> PromptTemplate:
    """Load a generation prompt template"""
    manager = get_default_config_manager()
    return manager.load_prompt_template("generation", template_name)


def validate_all_configurations() -> bool:
    """Validate all configurations and return True if all are valid"""
    manager = get_default_config_manager()
    results = manager.validate_configuration()
    return all(results.values())