---
inclusion: always
---

# Source Code Directory Structure (/src)

## Core Application Files
- **`src/app.py`**: Main application entry point with FastAPI setup and dependency injection
- **`src/startup.py`**: System initialization and startup sequence management
- **`src/config.py`**: Legacy configuration management (being phased out)
- **`src/__init__.py`**: Package initialization

## Directory Organization

### `/src/config/` - Configuration Management
- **`app_config.py`**: Main application configuration with environment variable handling
- **`dependency_injection.py`**: Dependency injection container and service registration
- **`environment_validator.py`**: Environment validation and health checks
- **`openrouter_config_manager.py`**: OpenRouter API configuration and management
- **`qme_gold_standard_config.py`**: QME compliance and quality standards configuration
- **`secure_api_key_manager.py`**: Secure API key storage and retrieval

### `/src/core/` - Core Business Logic
- **`/extraction/`**: Document processing and field extraction services
- **`/generation/`**: Content generation and template assembly
- **`/validation/`**: Evidence validation and compliance checking
- **`/calculation/`**: AMA guideline calculations (programmatic, no LLM)
- **`exceptions.py`**: Custom exception hierarchy
- **`factories.py`**: Factory patterns for service creation
- **`interfaces.py`**: Abstract interfaces and contracts

### `/src/infrastructure/` - Infrastructure Services
- **`/api/`**: API providers and external service integrations
- **`/configuration/`**: Advanced configuration management and service registry
- **`/knowledge/`**: Knowledge graph and knowledge base management
- **`/monitoring/`**: Health checks, performance monitoring, error handling
- **`/storage/`**: Data persistence and storage services

### `/src/ui/` - User Interface Components
- **`main_app.py`**: Main Streamlit application with workflow management
- **`upload_interface.py`**: Document upload and processing interface
- **`qa_interface.py`**: Question-answering interface with knowledge graph integration
- **`qme_template_interface.py`**: QME template generation interface
- **`document_manager.py`**: Document management and history interface
- **`professional_template_interface.py`**: Professional template assembly interface

### `/src/services/` - Business Services
- **`comprehensive_qme_field_service.py`**: QME field extraction and validation
- **`professional_template_assembler_simple.py`**: Template assembly service

### `/src/workflow/` - Workflow Management
- **`evidence_first_workflow_manager.py`**: Evidence-first workflow orchestration
- **`enhanced_workflow_manager.py`**: Enhanced workflow with dual-pipeline support
- **`workflow_manager.py`**: Base workflow management

## Development Guidelines
- All services must implement proper interfaces from `/src/core/interfaces.py`
- Use dependency injection from `/src/config/dependency_injection.py`
- Follow the evidence-first approach with confidence scoring
- Implement comprehensive error handling and logging
- Maintain backward compatibility during refactoring