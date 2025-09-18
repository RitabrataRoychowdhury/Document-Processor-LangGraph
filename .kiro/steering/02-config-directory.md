---
inclusion: always
---

# Configuration Directory (/config)

## Purpose
Centralized configuration management for all system components, environments, and templates.

## Directory Structure

### `/config/environments/` - Environment-Specific Configurations
- **`development/`**: Development environment settings
- **`production/`**: Production environment configurations
- **`staging/`**: Staging environment setup

### `/config/prompts/` - AI Prompt Templates
- **`extraction/`**: Document extraction prompts
  - `pqme_extraction.yaml`: PQME document field extraction prompts
- **`generation/`**: Content generation prompts
  - `examination_section.yaml`: Medical examination section generation
- **`validation/`**: Validation and quality check prompts

### `/config/settings/` - Service Settings
- **`openrouter_config.yaml`**: OpenRouter API configuration and model settings

### `/config/system/` - System Configuration
- **`component_config.yaml`**: System component configuration and dependencies

### `/config/templates/` - Template Configurations
- **`assembly_config.yaml`**: Template assembly configuration and rules
- **`qme_template_structure.yaml`**: QME template structure and formatting rules

### `/config/validation/` - Validation Rules
- **`quality_validation_config.yaml`**: Quality validation rules and thresholds

## Root Configuration Files
- **`schema.yaml`**: Configuration schema definitions and validation rules

## Usage Guidelines
- All configuration files use YAML format for readability
- Environment-specific overrides are supported
- Configuration validation is performed at startup
- Sensitive data (API keys) should use environment variables, not config files
- Changes to configuration files require system restart for most components

## Configuration Hierarchy
1. Environment variables (highest priority)
2. Environment-specific config files
3. Default config files (lowest priority)

## Best Practices
- Use descriptive configuration keys
- Include comments explaining complex settings
- Validate configuration at application startup
- Use type hints in configuration classes
- Document all configuration options