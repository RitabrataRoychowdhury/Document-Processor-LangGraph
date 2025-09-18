---
inclusion: always
---

# Documentation Directory (/docs)

## Purpose
Comprehensive documentation for the QME system including API documentation, implementation guides, and migration instructions.

## Root Documentation Files
- **`COMPREHENSIVE_MIGRATION_GUIDE.md`**: Complete system migration documentation
- **`COMPREHENSIVE_QME_RULES_IMPLEMENTATION.md`**: QME rules engine implementation guide
- **`DEVELOPER_GUIDE.md`**: Developer setup and contribution guidelines
- **`DOCKER_README.md`**: Docker deployment and containerization guide
- **`MIGRATION_GUIDE.md`**: System migration instructions
- **`MIGRATION_GUIDE_V2.md`**: Enhanced migration guide version 2
- **`QME_RULES_ENGINE_README.md`**: QME rules engine documentation
- **`SYSTEM_READY_GUIDE.md`**: System readiness and deployment checklist

## Directory Structure

### `/docs/api/` - API Documentation
- **`openapi.yaml`**: OpenAPI specification for all system APIs
- **Purpose**: Complete API documentation for integration and development
- **Usage**: API client generation, integration testing, developer reference

### `/docs/archive/` - Archived Documentation
- **`_MConverter.eu_AI EXample QME Report Template.md`**: AI example QME report template
- **`claude_code_refactor_prompt.md`**: Code refactoring prompts and guidelines
- **Purpose**: Historical documentation and reference materials
- **Content**: Deprecated guides, legacy templates, refactoring notes

### `/docs/implementation/` - Implementation Documentation
Comprehensive implementation summaries for all major system components:

#### Core Implementation Summaries
- **`AMA_GUIDELINES_IMPLEMENTATION_SUMMARY.md`**: AMA Guidelines integration
- **`CONFIGURATION_MANAGEMENT_IMPLEMENTATION_SUMMARY.md`**: Configuration system
- **`ENHANCED_RULES_ENGINE_IMPLEMENTATION_SUMMARY.md`**: Enhanced rules engine
- **`EVIDENCE_FIRST_WORKFLOW_IMPLEMENTATION_SUMMARY.md`**: Evidence-first workflows
- **`EVIDENCE_VALIDATOR_IMPLEMENTATION_SUMMARY.md`**: Evidence validation system
- **`INTELLIGENT_CONTENT_GENERATOR_IMPLEMENTATION_SUMMARY.md`**: Content generation
- **`KNOWLEDGE_BASE_INITIALIZATION_IMPLEMENTATION_SUMMARY.md`**: Knowledge base setup

#### Template and QME Implementation
- **`PROFESSIONAL_QME_SYSTEM_USAGE.md`**: Professional QME system usage guide
- **`PROFESSIONAL_TEMPLATE_ASSEMBLER_IMPLEMENTATION_SUMMARY.md`**: Template assembler
- **`PROFESSIONAL_TEMPLATE_ASSEMBLY_ENGINE_IMPLEMENTATION_SUMMARY.md`**: Assembly engine
- **`QME_TEMPLATE_IMPLEMENTATION_SUMMARY.md`**: QME template system
- **`QME_WORKFLOW_STATUS_SUMMARY.md`**: Workflow status tracking

#### Task Implementation Documentation
- **`SCRIPT_MODIFICATIONS_TASK5.md`**: Task 5 script modifications
- **`TASK_1_IMPLEMENTATION_SUMMARY.md`**: Task 1 implementation details
- **`TASK_2_IMPLEMENTATION_SUMMARY.md`**: Task 2 implementation details
- **`TASK_4_IMPLEMENTATION_SUMMARY.md`**: Task 4 implementation details
- **`TASK_5_IMPLEMENTATION_SUMMARY.md`**: Task 5 implementation details
- **`TASK_5_QUALITY_VALIDATION_IMPLEMENTATION_SUMMARY.md`**: Task 5 quality validation
- **`TASK_5_SCRIPT_INTEGRATION_SUMMARY.md`**: Task 5 script integration
- **`TASK_5_VALIDATION_IMPLEMENTATION_SUMMARY.md`**: Task 5 validation system
- **`TASK_9_IMPLEMENTATION_SUMMARY.md`**: Task 9 implementation details

#### Integration and Testing Documentation
- **`UI_BACKEND_INTEGRATION_TEST_SUMMARY.md`**: UI-backend integration testing

## Documentation Standards
- **Format**: Markdown format for all documentation
- **Structure**: Consistent heading structure and organization
- **Code Examples**: Include working code examples and snippets
- **Diagrams**: Use mermaid diagrams for architecture and workflows
- **Updates**: Keep documentation synchronized with code changes

## Documentation Categories
1. **API Documentation**: Complete API specifications and examples
2. **Implementation Guides**: Detailed implementation documentation
3. **Migration Guides**: System migration and upgrade instructions
4. **Developer Guides**: Setup, contribution, and development guidelines
5. **Deployment Guides**: Production deployment and configuration
6. **Architecture Documentation**: System design and component relationships

## Maintenance Guidelines
- **Version Control**: All documentation is version controlled
- **Review Process**: Documentation changes require review
- **Accuracy**: Regular validation against actual implementation
- **Completeness**: Comprehensive coverage of all system components
- **Accessibility**: Clear, well-organized, and searchable content

## Usage Patterns
- **New Developers**: Start with `DEVELOPER_GUIDE.md`
- **Deployment**: Use `DOCKER_README.md` and `SYSTEM_READY_GUIDE.md`
- **API Integration**: Reference `/docs/api/openapi.yaml`
- **System Migration**: Follow migration guides in sequence
- **Implementation Details**: Check `/docs/implementation/` for specific components

## Integration with Development
- Documentation is automatically generated where possible
- Code comments and docstrings feed into documentation
- API documentation is generated from OpenAPI specifications
- Implementation summaries are updated with each major change
- Testing documentation validates implementation accuracy