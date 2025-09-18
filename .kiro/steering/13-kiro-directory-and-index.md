---
inclusion: always
---

# .kiro Directory and Comprehensive Index

## Purpose
The `.kiro` directory contains Kiro-specific configuration, specifications, and steering documentation for the QME system.

## .kiro Directory Structure

### `/.kiro/secure/` - Secure Storage
- **`api_keys.enc`**: Encrypted API keys and sensitive configuration
- **Purpose**: Secure storage of sensitive data with encryption
- **Access**: Restricted access, encrypted at rest

### `/.kiro/specs/` - Project Specifications
Comprehensive project specifications and design documents:

- **`backend-frontend-integration-fix/`**: Backend-frontend integration specifications
- **`document-qa-system/`**: Document Q&A system specifications
- **`enhanced-qme-template-generation/`**: Enhanced QME template generation specs
- **`evidence-first-qme-system/`**: Evidence-first system architecture specs
- **`production-ready-qme-system/`**: Production readiness specifications
- **`qme-system-refactor/`**: System refactoring specifications
- **`ui-component-fixes-and-testing/`**: UI component fixes and testing specs
- **`backend-frontend-integration-fix.md`**: Integration fix documentation

### `/.kiro/steering/` - Steering Documentation
This directory contains comprehensive project steering documentation:

## Complete Steering Documentation Index

### 00-12: Core Steering Documents
1. **`00-project-overview.md`**: Project purpose, architecture, and compliance requirements
2. **`01-src-directory-structure.md`**: Source code organization and development guidelines
3. **`02-config-directory.md`**: Configuration management and environment setup
4. **`03-data-directory.md`**: Data storage, management, and privacy guidelines
5. **`04-tests-directory.md`**: Testing standards, categories, and execution
6. **`05-scripts-directory.md`**: Automation scripts and deployment tools
7. **`06-results-directory.md`**: Results storage, validation reports, and outputs
8. **`07-docs-directory.md`**: Documentation standards and maintenance
9. **`08-examples-directory.md`**: Example scripts and demonstration code
10. **`09-logs-directory.md`**: Logging standards, monitoring, and analysis
11. **`10-root-project-files.md`**: Root configuration files and entry points
12. **`11-backup-directory.md`**: Backup strategy and rollback procedures
13. **`12-development-workflow.md`**: Development standards and best practices
14. **`13-kiro-directory-and-index.md`**: This comprehensive index document

## Project Directory Quick Reference

### Core Development Directories
- **`/src/`**: Source code (core, infrastructure, UI, services)
- **`/tests/`**: Testing suite (unit, integration, end-to-end, performance)
- **`/config/`**: Configuration files (environments, prompts, settings)
- **`/scripts/`**: Automation and deployment scripts

### Data and Results
- **`/data/`**: Data storage (documents, database, references, samples)
- **`/results/`**: Processing results (templates, validation, performance)
- **`/logs/`**: System logs (application, errors, performance, audit)

### Documentation and Examples
- **`/docs/`**: Documentation (API, implementation, migration guides)
- **`/examples/`**: Demonstration scripts and usage examples
- **`/backup_before_import_fix/`**: System backup before major changes

### Project Management
- **`/.kiro/`**: Kiro configuration (specs, steering, secure storage)
- **Root Files**: Entry points, configuration, Docker setup

## Key Development Principles

### Evidence-First Architecture
- All content generation based on extracted evidence with confidence scoring
- Dual-pipeline architecture: extraction/validation → generation/compliance
- Programmatic AMA calculations with zero LLM involvement
- Complete audit trails for regulatory compliance

### Service-Oriented Design
- Modular services with dependency injection and loose coupling
- Comprehensive error handling and graceful degradation
- Production-ready monitoring, logging, and health checks
- Scalable infrastructure with Docker containerization

### Quality Standards
- Minimum 80% code coverage with comprehensive testing
- Type hints, docstrings, and structured logging required
- Security-first approach with encrypted secrets management
- Continuous validation and performance monitoring

## Navigation Guide

### For New Developers
1. Start with `00-project-overview.md` for system understanding
2. Review `12-development-workflow.md` for setup and standards
3. Examine `01-src-directory-structure.md` for code organization
4. Check `10-root-project-files.md` for configuration setup

### For System Administration
1. Review `05-scripts-directory.md` for deployment tools
2. Check `02-config-directory.md` for configuration management
3. Examine `09-logs-directory.md` for monitoring and logging
4. Review `06-results-directory.md` for output management

### For Testing and Validation
1. Start with `04-tests-directory.md` for testing standards
2. Review `12-development-workflow.md` for validation workflows
3. Check `05-scripts-directory.md` for testing automation
4. Examine `06-results-directory.md` for validation results

### For Documentation and Examples
1. Review `07-docs-directory.md` for documentation standards
2. Check `08-examples-directory.md` for usage examples
3. Examine `/docs/implementation/` for detailed guides
4. Review specification files in `/.kiro/specs/`

## Maintenance and Updates

### Steering Documentation Maintenance
- Update steering docs when major architectural changes occur
- Synchronize with actual implementation and file structure
- Review and validate steering accuracy quarterly
- Update development workflows based on team feedback

### Integration with Development
- Steering rules are automatically included in Kiro context
- Development decisions should align with steering principles
- New features should update relevant steering documentation
- Code reviews should validate adherence to steering guidelines

This comprehensive steering system ensures consistent development practices, maintains architectural integrity, and provides clear guidance for all aspects of the QME system development and maintenance.