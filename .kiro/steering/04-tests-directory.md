---
inclusion: always
---

# Tests Directory (/tests)

## Purpose
Comprehensive testing suite covering unit, integration, end-to-end, and performance testing for the QME system.

## Directory Structure

### `/tests/api/` - API Testing
- **`test_backend_endpoints.py`**: Backend API endpoint testing and validation

### `/tests/end_to_end/` - End-to-End Testing
- **`test_end_to_end_integration.py`**: Complete workflow testing from upload to template generation
- **`test_end_to_end_quality_validation.py`**: Quality validation across entire pipeline
- **`test_end_to_end_system_comparison.py`**: System comparison and regression testing

### `/tests/evidence/` - Evidence-First Testing
- **`test_enhanced_evidence_first_rules.py`**: Enhanced evidence-first rule validation
- **`test_evidence_content_generation.py`**: Evidence-based content generation testing
- **`test_evidence_first_core.py`**: Core evidence-first functionality testing
- **`test_evidence_first_workflow.py`**: Evidence-first workflow testing

### `/tests/fixtures/` - Test Data and Fixtures
- **`documents/`**: Sample documents for testing
- **`expected_results/`**: Expected test results and validation data

### `/tests/integration/` - Integration Testing
- **`api/`**: API integration tests
- **`pipelines/`**: Pipeline integration tests
- **`services/`**: Service integration tests
- **`test_end_to_end_workflows.py`**: Workflow integration testing
- **`test_knowledge_base_initialization.py`**: Knowledge base integration testing
- **`test_service_integration_validation.py`**: Service integration validation

### `/tests/performance/` - Performance Testing
- **`test_performance_stability.py`**: System performance and stability testing
- **`test_system_performance.py`**: System-wide performance benchmarks
- **`test_ui_performance.py`**: UI performance and responsiveness testing

### `/tests/results/` - Test Results Storage
- **`quality_validation/`**: Quality validation test results
- **`system_comparison/`**: System comparison test results

### `/tests/template/` - Template Testing
- **`test_enhanced_professional_template_assembler.py`**: Professional template assembly testing
- **`test_professional_template_assembler_validation.py`**: Template assembler validation
- **`test_professional_template_fix.py`**: Template fix and correction testing

### `/tests/ui/` - UI Component Testing
- **`test_ui_components.py`**: Streamlit UI component testing

### `/tests/unit/` - Unit Testing
- **`core/`**: Core business logic unit tests
- **`infrastructure/`**: Infrastructure service unit tests
- **`ui/`**: UI component unit tests
- **`workflow/`**: Workflow management unit tests

### `/tests/validation/` - Validation Testing
- **`validate_evidence_enhancement.py`**: Evidence enhancement validation

### `/tests/workflow/` - Workflow Testing
- **`test_qme_interface.py`**: QME interface workflow testing
- **`test_qme_workflow.py`**: QME workflow testing
- **`test_workflow_imports.py`**: Workflow import validation

## Root Test Files
- **`conftest.py`**: Pytest configuration and shared fixtures
- **`README.md`**: Testing documentation and guidelines
- **`test_config.json`**: Test configuration settings
- **`run_comprehensive_tests.py`**: Comprehensive test suite runner
- **`run_evidence_first_tests.py`**: Evidence-first test suite runner

## Testing Standards
- **Coverage**: Minimum 80% code coverage for all modules
- **Isolation**: Tests must be independent and not affect each other
- **Data**: Use fixtures and mocks, never real patient data
- **Performance**: Include performance benchmarks and regression tests
- **Documentation**: All test functions must have descriptive docstrings

## Test Categories
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service interaction testing
3. **End-to-End Tests**: Complete workflow testing
4. **Performance Tests**: Load and stress testing
5. **Validation Tests**: Compliance and quality testing

## Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/end_to_end/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run performance tests
python -m pytest tests/performance/ -v
```

## Test Data Management
- Use anonymized/synthetic data only
- Store test fixtures in `/tests/fixtures/`
- Clean up test data after test completion
- Version control test data and expected results