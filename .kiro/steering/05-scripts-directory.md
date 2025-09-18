---
inclusion: always
---

# Scripts Directory (/scripts)

## Purpose
Automation scripts for deployment, testing, validation, and system management.

## Deployment Scripts
- **`deploy.sh`**: Main deployment script for production environments
- **`deploy.bat`**: Windows deployment script
- **`deploy-production.sh`**: Production-specific deployment with health checks
- **`setup.sh`**: Initial system setup and dependency installation
- **`start.sh`**: Quick start script for development
- **`run.sh`**: Main application runner with environment setup
- **`cleanup.sh`**: System cleanup and reset script

## Docker Scripts
- **`docker-build.sh`**: Docker image building automation
- **`docker-run.sh`**: Docker container execution
- **`docker-compose-up.sh`**: Docker Compose orchestration
- **`docker-entrypoint.sh`**: Docker container entry point script

## Testing and Validation Scripts
- **`comprehensive_system_validation.py`**: Complete system validation suite
- **`performance_stability_test.py`**: Performance and stability testing
- **`run_comprehensive_service_validation.py`**: Service validation runner
- **`test_basic_functionality.py`**: Basic functionality testing
- **`test_complete_pipeline.py`**: End-to-end pipeline testing
- **`test_qme_performance.py`**: QME-specific performance testing
- **`test_qme_with_sample_data.py`**: QME testing with sample documents
- **`validate_qme_workflow.py`**: QME workflow validation
- **`validate_refactored_system.py`**: System refactoring validation
- **`validate_system_with_real_documents.py`**: Real document validation
- **`validate_task_implementation.py`**: Task implementation validation

## API Testing Scripts
- **`test_openrouter_sonoma_sky.py`**: OpenRouter Sonoma Sky model testing
- **`test_sonoma_sky_extraction.py`**: Sonoma Sky extraction testing
- **`test_sonoma_sky_simple.py`**: Simple Sonoma Sky testing
- **`test_service_validation_simple.py`**: Simple service validation

## Task-Specific Scripts
- **`run_task5_validation.py`**: Task 5 validation runner
- **`test_task5_integration.py`**: Task 5 integration testing
- **`test_task5_quick.py`**: Quick Task 5 testing
- **`test_task5_simple.py`**: Simple Task 5 testing
- **`task5_implementation_demo.py`**: Task 5 implementation demonstration
- **`verify_task5_integration.py`**: Task 5 integration verification

## Quality and Integration Scripts
- **`integrate_quality_validation.py`**: Quality validation integration
- **`test_quality_validation_integration.py`**: Quality validation testing

## System Management Scripts
- **`fix_imports.py`**: Import fixing and dependency resolution
- **`import_analyzer.py`**: Import analysis and validation
- **`initialize_knowledge_base.py`**: Knowledge base initialization
- **`manage_api_keys.py`**: API key management and security
- **`migrate_existing_data.py`**: Data migration utilities
- **`migrate_to_refactored_system.py`**: System refactoring migration
- **`migrate_to_refactored_system_v2.py`**: Enhanced system migration
- **`rollback_migration.py`**: Migration rollback utilities
- **`run_tests.py`**: Test suite runner

## Documentation
- **`SCRIPTS_README.md`**: Comprehensive scripts documentation

## Usage Guidelines

### Development Workflow
```bash
# Initial setup
./scripts/setup.sh

# Start development server
./scripts/start.sh

# Run comprehensive tests
./scripts/run_tests.py

# Validate system
python scripts/comprehensive_system_validation.py
```

### Production Deployment
```bash
# Deploy to production
./scripts/deploy-production.sh

# Docker deployment
./scripts/docker-compose-up.sh

# Validate deployment
python scripts/validate_system_with_real_documents.py
```

### Testing and Validation
```bash
# Basic functionality test
python scripts/test_basic_functionality.py

# Performance testing
python scripts/performance_stability_test.py

# QME workflow validation
python scripts/validate_qme_workflow.py
```

## Script Standards
- **Error Handling**: All scripts must handle errors gracefully
- **Logging**: Comprehensive logging for debugging and monitoring
- **Documentation**: Clear usage instructions and parameter descriptions
- **Idempotency**: Scripts should be safe to run multiple times
- **Validation**: Include pre-flight checks and validation steps

## Security Considerations
- **API Keys**: Never hardcode API keys in scripts
- **Permissions**: Set appropriate file permissions for security
- **Input Validation**: Validate all user inputs and parameters
- **Audit Trails**: Log all significant operations for audit purposes