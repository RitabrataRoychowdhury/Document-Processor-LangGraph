---
inclusion: always
---

# Development Workflow Guide

## Purpose
Comprehensive guide for development workflows, coding standards, and best practices for the QME system.

## Development Environment Setup

### Initial Setup
```bash
# 1. Clone repository and setup environment
git clone <repository-url>
cd qme-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# 5. Initialize system
python main.py --init

# 6. Run health check
python main.py --check
```

### Development Startup
```bash
# Recommended development startup
python run_direct.py

# Alternative with shell script
./run_fixed.sh

# With specific configuration
python main.py --web --debug
```

## Code Organization Standards

### Directory Structure Rules
- **`/src/core/`**: Core business logic only, no external dependencies
- **`/src/infrastructure/`**: External integrations, monitoring, storage
- **`/src/ui/`**: User interface components and interactions
- **`/src/config/`**: Configuration management and validation
- **`/src/services/`**: Business services implementing core interfaces

### Import Standards
```python
# Standard import order
import os
import sys
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from src.core.interfaces import DocumentProcessor
from src.infrastructure.monitoring import HealthChecker
from src.config.app_config import AppConfig
```

### Code Quality Standards
- **Type Hints**: All functions must have type hints
- **Docstrings**: All public methods must have comprehensive docstrings
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Logging**: Structured logging with correlation IDs
- **Testing**: Minimum 80% code coverage

## Development Workflow

### Feature Development Process
1. **Create Feature Branch**: `git checkout -b feature/description`
2. **Implement Changes**: Follow coding standards and architecture patterns
3. **Write Tests**: Unit, integration, and end-to-end tests
4. **Run Validation**: `python scripts/comprehensive_system_validation.py`
5. **Update Documentation**: Update relevant documentation files
6. **Create Pull Request**: Include description, tests, and validation results

### Testing Workflow
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/end_to_end/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run performance tests
python scripts/performance_stability_test.py
```

### Validation Workflow
```bash
# Comprehensive system validation
python scripts/comprehensive_system_validation.py

# Basic functionality test
python scripts/test_basic_functionality.py

# QME workflow validation
python scripts/validate_qme_workflow.py

# Service integration validation
python scripts/run_comprehensive_service_validation.py
```

## Architecture Patterns

### Service Pattern
```python
from abc import ABC, abstractmethod
from src.core.interfaces import DocumentProcessor

class MyService(DocumentProcessor):
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process_document(self, document: Document) -> ProcessingResult:
        # Implementation with error handling and logging
        pass
```

### Dependency Injection Pattern
```python
from src.config.dependency_injection import ServiceContainer

# Register service
container = ServiceContainer()
container.register('document_processor', MyDocumentProcessor)

# Use service
processor = container.get('document_processor')
```

### Error Handling Pattern
```python
from src.core.exceptions import QMESystemError, ExtractionError

try:
    result = process_document(document)
except ExtractionError as e:
    logger.error(f"Extraction failed: {e}", exc_info=True)
    raise QMESystemError(f"Document processing failed: {e}") from e
```

## Configuration Management

### Environment Configuration
```python
# Use centralized configuration
from src.config.app_config import AppConfig

config = AppConfig.from_env()
if not config.is_api_configured():
    raise ConfigurationError("API keys not configured")
```

### Feature Flags
```python
# Use configuration for feature flags
if config.enable_knowledge_graph:
    # Initialize knowledge graph
    pass
```

## Quality Assurance

### Code Review Checklist
- [ ] Type hints on all functions
- [ ] Comprehensive error handling
- [ ] Structured logging with correlation IDs
- [ ] Unit tests with good coverage
- [ ] Integration tests for external dependencies
- [ ] Documentation updated
- [ ] Performance impact considered
- [ ] Security implications reviewed

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Deployment Workflow

### Development Deployment
```bash
# Local development
python run_direct.py

# Docker development
docker-compose up -d
```

### Production Deployment
```bash
# Production deployment
./scripts/deploy-production.sh

# Validate deployment
python scripts/validate_system_with_real_documents.py
```

## Monitoring and Debugging

### Log Analysis
```bash
# View system logs
tail -f logs/qme_system.log

# View error logs
tail -f logs/errors.log

# Search logs
grep "ERROR" logs/qme_system.log
```

### Performance Monitoring
```bash
# Run performance tests
python scripts/performance_stability_test.py

# Monitor system performance
python scripts/test_qme_performance.py
```

## Best Practices

### Evidence-First Development
- All content generation must be based on extracted evidence
- Implement confidence scoring for all extracted data
- Maintain audit trails for all processing decisions
- Use programmatic calculations for AMA guidelines (no LLM)

### Security Best Practices
- Never commit API keys or secrets
- Use environment variables for all configuration
- Implement proper input validation
- Maintain audit logs for all user actions

### Performance Best Practices
- Use caching for expensive operations
- Implement connection pooling for databases
- Use async/await for I/O operations
- Monitor and optimize resource usage

### Documentation Best Practices
- Keep documentation synchronized with code
- Include working code examples
- Document all configuration options
- Maintain implementation summaries for major components