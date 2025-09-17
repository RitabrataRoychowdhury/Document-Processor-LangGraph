# QME System Developer Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup and Installation](#setup-and-installation)
4. [Development Workflow](#development-workflow)
5. [Code Organization](#code-organization)
6. [API Documentation](#api-documentation)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Contributing](#contributing)

## Overview

The QME (Qualified Medical Evaluator) System is a production-ready application for processing medical documents, extracting structured data, and generating professional QME reports. The system implements a dual-pipeline architecture with evidence-first validation and programmatic calculations.

### Key Features

- **Document Processing**: Automated extraction of medical information from PQME documents
- **Evidence Validation**: Confidence-based validation with threshold management
- **Template Generation**: Professional DOCX template generation with compliance checking
- **Knowledge Base**: RAG-powered Q&A system with AMA Guidelines integration
- **Audit Trails**: Complete traceability and compliance reporting
- **Production Ready**: Monitoring, logging, error handling, and scalability features

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface │    │   REST API      │    │   CLI Tools     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Workflow Manager       │
                    └─────────────┬─────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
        ┌───────▼────────┐ ┌─────▼─────┐ ┌────────▼────────┐
        │   Pipeline 1   │ │ Pipeline 2│ │   Monitoring    │
        │ Extract/Validate│ │Gen/Comply │ │   & Logging     │
        └────────────────┘ └───────────┘ └─────────────────┘
                │                 │                 │
        ┌───────▼────────┐ ┌─────▼─────┐ ┌────────▼────────┐
        │  Core Services │ │Infra Svcs │ │   Data Layer    │
        └────────────────┘ └───────────┘ └─────────────────┘
```

### Service Organization

```
src/
├── core/                    # Core business logic
│   ├── extraction/          # Document and field extraction
│   ├── validation/          # Evidence and compliance validation
│   ├── generation/          # Content and template generation
│   ├── calculation/         # Programmatic calculations
│   ├── interfaces.py        # Service interfaces
│   └── factories.py         # Service factories
├── infrastructure/          # Infrastructure services
│   ├── knowledge/           # Knowledge base and graph
│   ├── storage/             # Data persistence
│   ├── monitoring/          # Health checks and performance
│   └── configuration/       # Configuration management
├── workflow/                # Workflow orchestration
│   ├── pipelines/           # Pipeline implementations
│   ├── managers/            # Workflow managers
│   └── state/               # State management
└── interfaces/              # External interfaces
    ├── ui/                  # User interface components
    ├── api/                 # REST API endpoints
    └── cli/                 # Command-line interface
```

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for production) or SQLite (for development)
- Redis (for caching)
- Docker and Docker Compose (optional)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd qme-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   python scripts/initialize_knowledge_base.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Web UI: http://localhost:8501
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health

## Development Workflow

### Code Style and Standards

- **Python Style**: Follow PEP 8 with Black formatting
- **Type Hints**: Use type hints for all public methods
- **Docstrings**: Use Google-style docstrings
- **Imports**: Use absolute imports, organize with isort

### Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pip install pre-commit
pre-commit install
```

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `hotfix/*`: Critical bug fixes

### Commit Messages

Use conventional commit format:
```
type(scope): description

feat(extraction): add confidence scoring for medical fields
fix(validation): resolve threshold comparison logic
docs(api): update OpenAPI specification
```

## Code Organization

### Service Interfaces

All services implement interfaces defined in `src/core/interfaces.py`:

```python
from src.core.interfaces import IExtractionService

class MyExtractionService(IExtractionService):
    async def extract_fields(self, document_path: str, **kwargs) -> ExtractionResult:
        # Implementation
        pass
```

### Service Factory Pattern

Services are created using factories for dependency injection:

```python
from src.core.factories import create_default_service_registry

# Create service registry
registry = create_default_service_registry(config)

# Get service instance
extraction_service = registry.get_extraction_service('document_processor')
```

### Configuration Management

Environment-specific configuration:

```python
from src.infrastructure.configuration.config_manager import ConfigManager

config_manager = ConfigManager(environment='production')
config = config_manager.get_config()
```

### Error Handling

Use custom exception hierarchy:

```python
from src.core.exceptions import ExtractionError, ValidationError

try:
    result = await extraction_service.extract_fields(document_path)
except ExtractionError as e:
    logger.error(f"Extraction failed: {e}")
    # Handle extraction-specific error
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle general error
```

## API Documentation

### OpenAPI Specification

The complete API specification is available at `docs/api/openapi.yaml`.

### Key Endpoints

- `POST /documents` - Upload and process documents
- `GET /documents/{id}/status` - Get processing status
- `GET /documents/{id}/extraction` - Get extraction results
- `POST /templates` - Generate QME templates
- `POST /qa/query` - Query knowledge base

### Authentication

The API supports two authentication methods:
- API Key: `X-API-Key` header
- JWT Bearer Token: `Authorization: Bearer <token>`

### Rate Limiting

- Development: 100 requests/minute
- Production: 1000 requests/minute
- Burst: 2x rate limit for 1 minute

## Testing

### Test Organization

```
tests/
├── unit/                    # Unit tests
├── integration/             # Integration tests
├── end_to_end/             # End-to-end tests
├── performance/            # Performance tests
├── fixtures/               # Test data and fixtures
└── conftest.py             # Pytest configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html

# Run performance tests
pytest tests/performance/ --benchmark-only
```

### Test Data

Test data is organized in `tests/fixtures/`:
- `sample_documents/` - Sample PQME documents
- `expected_results/` - Expected extraction results
- `mock_responses/` - Mock API responses

### Writing Tests

```python
import pytest
from src.core.extraction.document_processor import DocumentProcessor

class TestDocumentProcessor:
    @pytest.fixture
    def processor(self):
        return DocumentProcessor(config={'test': True})
    
    @pytest.mark.asyncio
    async def test_extract_fields(self, processor, sample_document):
        result = await processor.extract_fields(sample_document)
        assert result.success
        assert 'patient_name' in result.extracted_fields
```

## Deployment

### Environment Configuration

1. **Development**: SQLite, debug enabled, verbose logging
2. **Staging**: PostgreSQL, production-like settings, integration testing
3. **Production**: PostgreSQL, security enabled, monitoring, alerting

### Docker Deployment

```bash
# Build production image
docker build -t qme-system:latest .

# Run with environment variables
docker run -d \
  --name qme-system \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e OPENROUTER_API_KEY=... \
  qme-system:latest
```

### Health Checks

The system provides comprehensive health checks:
- `/health` - Overall system health
- `/health/database` - Database connectivity
- `/health/knowledge-base` - Knowledge base status
- `/health/services` - Individual service health

### Monitoring

- **Metrics**: Prometheus metrics on `/metrics`
- **Logging**: Structured JSON logging
- **Tracing**: Request correlation IDs
- **Alerting**: Configurable alerts for errors and performance

### Scaling

The system supports horizontal scaling:
- Stateless service design
- Shared database and file storage
- Load balancer compatible
- Container orchestration ready

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Peer Review**: At least one team member reviews the code
3. **Documentation**: Update documentation for new features
4. **Testing**: Ensure adequate test coverage

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Issue Reporting

When reporting issues, include:
- Environment details (OS, Python version, etc.)
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs
- Sample data (if applicable)

### Feature Requests

For feature requests, provide:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact assessment

## Additional Resources

- [API Documentation](api/openapi.yaml)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Performance Tuning](PERFORMANCE.md)

## Support

- **Documentation**: Check this guide and API docs first
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Email**: support@qmesystem.com for urgent issues