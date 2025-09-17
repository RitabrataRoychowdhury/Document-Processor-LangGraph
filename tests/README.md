# Comprehensive Testing Framework

This directory contains a comprehensive testing framework for the QME system, providing automated testing for UI components, backend endpoints, end-to-end workflows, and performance characteristics.

## Overview

The testing framework consists of four main test suites:

1. **UI Component Tests** - Test Streamlit UI components for rendering, interactions, and error handling
2. **Backend Endpoint Tests** - Test all API endpoints, health checks, and service integrations
3. **End-to-End Integration Tests** - Test complete workflows from document upload to template download
4. **Performance Tests** - Test UI responsiveness, load handling, memory usage, and stability

## Quick Start

### Run All Tests
```bash
python tests/run_comprehensive_tests.py --all
```

### Run Specific Test Suites
```bash
# UI component tests only
python tests/run_comprehensive_tests.py --ui

# Backend endpoint tests only
python tests/run_comprehensive_tests.py --api

# Integration tests only
python tests/run_comprehensive_tests.py --integration

# Performance tests (resource intensive)
python tests/run_comprehensive_tests.py --performance
```

### Generate Configuration File
```bash
python tests/run_comprehensive_tests.py --create-config
```

## Test Suites

### 1. UI Component Tests (`tests/ui/test_ui_components.py`)

Tests all Streamlit UI components including:
- Main application loading and initialization
- Upload interface functionality
- Q&A interface with document context
- QME template generation interface
- Document management interface
- Health status display with ComponentHealth objects
- User interaction scenarios
- Error handling and recovery

**Coverage Tracking:**
- Tracks which UI components are tested
- Measures test coverage percentage
- Identifies untested components

### 2. Backend Endpoint Tests (`tests/api/test_backend_endpoints.py`)

Tests all backend API endpoints including:
- Health check endpoints
- Document upload and processing endpoints
- Template generation endpoints
- Q&A service endpoints
- System status and monitoring endpoints
- Gemini API integration
- OpenRouter API integration
- Error handling for invalid requests

**Service Integration Testing:**
- API provider factory functionality
- Health checker service
- Database connectivity
- Service dependency validation

### 3. End-to-End Integration Tests (`tests/integration/test_end_to_end_workflows.py`)

Tests complete workflows including:
- Document upload → processing → template generation → download
- Q&A functionality with document context and knowledge graph integration
- Error scenarios and recovery paths
- Concurrent user scenarios (multiple users simultaneously)

**Workflow Scenarios:**
- Complete document processing workflow
- Q&A with document context
- Error scenarios and recovery
- Concurrent user testing (5+ simultaneous users)

### 4. Performance Tests (`tests/performance/test_ui_performance.py`)

Tests system performance characteristics:
- **Load Testing**: Multiple concurrent users with realistic usage patterns
- **Memory Leak Detection**: Long-running tests to detect memory leaks
- **Stability Testing**: Extended operation under various conditions
- **Response Time Monitoring**: Track UI responsiveness over time

**Performance Metrics:**
- Response times (average, min, max)
- Memory usage and growth
- Throughput (actions per second)
- Error rates under load
- Stability scores

## Configuration

### Test Configuration File (`tests/test_config.json`)

The test configuration file allows customization of:
- Which test suites to run
- Test parameters (timeouts, thresholds, etc.)
- Performance test settings
- Reporting options
- Test data and mock settings

### Key Configuration Sections:

```json
{
  "ui_tests": {
    "enabled": true,
    "timeout_seconds": 300,
    "coverage_threshold": 80
  },
  "api_tests": {
    "enabled": true,
    "base_url": "http://localhost:8501",
    "test_gemini_integration": true,
    "test_openrouter_integration": true
  },
  "integration_tests": {
    "enabled": true,
    "concurrent_users": 5,
    "session_duration": 30
  },
  "performance_tests": {
    "enabled": false,
    "load_test_users": 10,
    "memory_leak_iterations": 100
  }
}
```

## Test Results and Reporting

### Output Formats

1. **Console Output**: Real-time progress and summary
2. **JSON Reports**: Detailed machine-readable results
3. **HTML Reports**: Visual reports with charts and graphs
4. **Summary Reports**: High-level text summaries

### Results Directory Structure

```
test_results/
├── comprehensive_results_20240315_143022.json
├── comprehensive_summary_20240315_143022.txt
├── test_report_20240315_143022.html
└── performance_results_20240315_143022.json
```

### Key Metrics Tracked

- **Overall Success Rate**: Percentage of tests passing
- **Test Coverage**: Percentage of components/endpoints tested
- **Performance Scores**: Response times, stability, memory usage
- **Error Rates**: Frequency and types of errors encountered
- **Recommendations**: Automated suggestions for improvements

## Running Tests in CI/CD

### Exit Codes
- `0`: Success (≥85% success rate)
- `1`: Critical failure (<70% success rate)
- `2`: Warning (70-85% success rate)
- `130`: Interrupted by user

### Example CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Comprehensive Tests
  run: |
    python tests/run_comprehensive_tests.py --all --format json --output-dir ci_results
  continue-on-error: false

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: ci_results/
```

## Test Data and Mocking

### Mock Test Documents
The framework includes mock test documents:
- PQME reports with realistic medical content
- Medical records with patient information
- Imaging reports with diagnostic findings

### API Mocking
- Mock Gemini API responses
- Mock OpenRouter API responses
- Configurable response delays
- Error scenario simulation

## Performance Considerations

### Resource Usage
- UI tests: Low resource usage
- API tests: Medium resource usage
- Integration tests: Medium-high resource usage
- Performance tests: High resource usage (CPU, memory)

### Test Duration
- UI tests: ~2-5 minutes
- API tests: ~3-8 minutes
- Integration tests: ~5-15 minutes
- Performance tests: ~10-60 minutes (configurable)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Timeout Errors**: Increase timeout values in configuration
3. **Memory Issues**: Reduce concurrent users or test duration
4. **API Connection Errors**: Check service availability and configuration

### Debug Mode
```bash
python tests/run_comprehensive_tests.py --all --verbose
```

### Test Individual Components
```bash
# Test specific UI component
python tests/ui/test_ui_components.py

# Test specific API endpoints
python tests/api/test_backend_endpoints.py

# Test specific workflow
python tests/integration/test_end_to_end_workflows.py
```

## Extending the Framework

### Adding New UI Component Tests
1. Add test method to `UIComponentTests` class
2. Update component coverage tracking
3. Add mock setup if needed

### Adding New API Endpoint Tests
1. Add endpoint to `APIEndpointTests` class
2. Define expected request/response format
3. Add error scenario tests

### Adding New Integration Workflows
1. Define workflow steps in `WorkflowTestSuite`
2. Implement step execution methods
3. Add validation and error handling

### Adding Performance Metrics
1. Extend `UIPerformanceMonitor` class
2. Add new metric collection methods
3. Update reporting and analysis

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External Dependencies**: Use mocks for API calls and external services
3. **Realistic Test Data**: Use representative test documents and scenarios
4. **Error Testing**: Include negative test cases and error scenarios
5. **Performance Baselines**: Establish performance baselines and thresholds
6. **Regular Execution**: Run tests regularly in CI/CD pipeline
7. **Result Analysis**: Review test results and recommendations regularly

## Contributing

When adding new tests:
1. Follow existing patterns and naming conventions
2. Include comprehensive error handling
3. Add appropriate mocking for external dependencies
4. Update configuration options if needed
5. Document new test capabilities
6. Ensure tests are deterministic and repeatable