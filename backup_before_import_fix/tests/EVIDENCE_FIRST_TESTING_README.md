# Evidence-First QME System Testing Framework

This document describes the comprehensive testing and validation framework for the Evidence-First QME System, implementing task 10 from the evidence-first QME system specification.

## Overview

The testing framework provides end-to-end validation of the evidence-first QME system with focus on:

- **End-to-end pipeline testing** using Sample3.pdf and PQME documents with known expected values
- **Confidence scoring validation** ensuring ≥95% precision for critical fields and ≥90% overall field coverage
- **Programmatic calculation testing** validating AMA table accuracy, ROM calculations, and Combined Values Chart applications
- **Knowledge graph initialization testing** confirming canonical document processing and entity/relationship counts
- **Integration testing** for complete workflow execution with audit trail validation

## Requirements Coverage

The testing framework validates the following requirements:

- **1.1** - Evidence-First Structured Extraction Pipeline
- **1.2** - Evidence Validation Gateway and Threshold Management  
- **2.1** - Programmatic Impairment Calculation Engine
- **2.5** - Calculation Documentation and Validation
- **3.2** - Knowledge Graph Complete Initialization
- **4.5** - Two-Pipeline Workflow Integration
- **5.5** - Enhanced Rules Engine and Legal Compliance

## Test Structure

### Core Test Files

#### 1. `test_evidence_first_pipeline.py`
**Main end-to-end pipeline testing**

- Tests complete pipeline using Sample3.pdf with known expected values
- Validates PQME document processing with Nick Diaz Jr. data
- Verifies confidence scoring with ≥95% precision for critical fields
- Tests programmatic calculation accuracy
- Validates knowledge graph initialization with ≥1000 nodes and ≥500 relationships
- Comprehensive audit trail validation

**Key Test Methods:**
- `test_sample3_pdf_end_to_end_pipeline()` - Complete Sample3.pdf workflow
- `test_pqme_document_confidence_scoring()` - PQME confidence validation
- `test_programmatic_calculation_accuracy()` - Calculation accuracy testing
- `test_knowledge_graph_initialization_validation()` - KG initialization testing
- `test_complete_workflow_audit_trail_validation()` - Audit trail validation

#### 2. `test_confidence_scoring_validation.py`
**Dedicated confidence scoring validation**

- Tests critical field precision ≥95% threshold
- Validates overall field coverage ≥90% threshold
- Verifies confidence algorithm components (regex, NER, cross-validation)
- Tests evidence snippet collection and source coordinate tracking
- Validates confidence threshold enforcement

**Key Test Methods:**
- `test_critical_field_precision_threshold()` - Critical field precision validation
- `test_overall_field_coverage_threshold()` - Field coverage validation
- `test_confidence_algorithm_components()` - Algorithm component testing
- `test_evidence_snippet_collection()` - Evidence provenance testing

#### 3. `test_programmatic_calculation_validation.py`
**Programmatic calculation accuracy testing**

- Tests AMA table accuracy and data integrity
- Validates ROM calculation accuracy with known values
- Tests Combined Values Chart application accuracy
- Verifies minimum measurement requirements (3 per motion type)
- Tests calculation step documentation and audit trails
- Validates body system specific limits

**Key Test Methods:**
- `test_ama_table_accuracy_validation()` - AMA table integrity testing
- `test_rom_calculation_accuracy_with_known_values()` - ROM calculation testing
- `test_combined_values_chart_accuracy()` - Combined Values Chart testing
- `test_minimum_measurement_requirements()` - Measurement validation
- `test_zero_llm_involvement_verification()` - Zero LLM involvement verification

#### 4. `test_knowledge_graph_initialization.py`
**Knowledge graph initialization testing**

- Tests canonical document processing (AMA Guides, QME Study Guide, Sample3.pdf)
- Validates entity and relationship count requirements (≥1000 nodes, ≥500 relationships)
- Tests AMA table accessibility for programmatic calculations
- Validates legal compliance template accessibility
- Tests initialization status reporting and system readiness

**Key Test Methods:**
- `test_canonical_document_processing()` - Canonical document processing
- `test_entity_relationship_count_validation()` - Count validation
- `test_ama_table_accessibility_validation()` - AMA table accessibility
- `test_legal_compliance_template_accessibility()` - Legal template accessibility
- `test_initialization_status_reporting()` - Status reporting

#### 5. `test_evidence_first_integration.py`
**Comprehensive integration testing**

- Tests complete Sample3.pdf workflow integration
- Validates PQME document workflow integration
- Tests audit trail completeness validation
- Validates legal compliance integration
- Tests performance benchmarks and error handling

**Key Test Methods:**
- `test_complete_sample3_workflow_integration()` - Complete Sample3 workflow
- `test_pqme_document_workflow_integration()` - PQME workflow integration
- `test_audit_trail_completeness_validation()` - Audit trail validation
- `test_legal_compliance_validation_integration()` - Legal compliance testing

## Test Data

### Sample3.pdf Test Data
```
Patient: Jane Doe, Age: 52, Female
Case: WC-2024-005678, Injury: March 10, 2024
Right shoulder: 15% UE impairment (AMA Table 16-3)
Cervical spine: 8% WP impairment (AMA Table 15-5)
Combined: 22% WP impairment (Combined Values Chart)
```

### PQME Test Data (Nick Diaz Jr.)
```
Patient: Nick Diaz Jr, Age: 43, Male
Employer: Costco, Occupation: Front-End Supervisor
Case: ADJ19802400, Claim: WC608-H07190
Injury: Left knee, July 24, 2024
Exam: September 9, 2025
Impairment: 12% LE → 5% WP (AMA Table 17-5)
```

### AMA Tables Test Data
- **Table 15-5**: Cervical Spine Range of Motion
- **Table 16-3**: Upper Extremity Shoulder Impairment
- **Table 17-5**: Lower Extremity Knee Impairment
- **Combined Values Chart**: Multiple impairment combination

## Running Tests

### Quick Start
```bash
# Run all evidence-first tests
python tests/run_evidence_first_tests.py

# Run specific test category
python tests/run_evidence_first_tests.py --test-type confidence

# Run with verbose output and generate report
python tests/run_evidence_first_tests.py --verbose --report

# Run quick smoke tests
python tests/run_evidence_first_tests.py --test-type smoke
```

### Individual Test Files
```bash
# Run specific test file with pytest
pytest tests/test_evidence_first_pipeline.py -v
pytest tests/test_confidence_scoring_validation.py -v
pytest tests/test_programmatic_calculation_validation.py -v
pytest tests/test_knowledge_graph_initialization.py -v
pytest tests/test_evidence_first_integration.py -v
```

### Test Categories

#### 1. Pipeline Tests (`--test-type pipeline`)
- End-to-end pipeline testing
- Sample3.pdf and PQME document processing
- Confidence scoring validation
- Programmatic calculation testing

#### 2. Confidence Tests (`--test-type confidence`)
- Critical field precision ≥95%
- Overall field coverage ≥90%
- Confidence algorithm validation
- Evidence snippet collection

#### 3. Calculation Tests (`--test-type calculation`)
- AMA table accuracy
- ROM calculation validation
- Combined Values Chart testing
- Zero LLM involvement verification

#### 4. Knowledge Graph Tests (`--test-type knowledge_graph`)
- Canonical document processing
- Entity/relationship count validation
- AMA table accessibility
- System readiness confirmation

#### 5. Integration Tests (`--test-type integration`)
- Complete workflow integration
- Audit trail validation
- Legal compliance testing
- Performance benchmarks

## Expected Results

### Performance Benchmarks
- **Pipeline 1 (Extraction)**: <2 minutes per document
- **Pipeline 2 (Generation)**: <3 minutes per report
- **Complete Workflow**: <5 minutes total
- **Knowledge Graph Query**: <500ms response time

### Accuracy Thresholds
- **Critical Field Precision**: ≥95%
- **Overall Field Coverage**: ≥90%
- **Legal Compliance Rate**: 100%
- **Calculation Accuracy**: 100% (programmatic)
- **Professional Review Acceptance**: ≥85%

### Quality Metrics
- **Node Count**: ≥1000 nodes in knowledge graph
- **Relationship Count**: ≥500 relationships in knowledge graph
- **Evidence Sources**: Complete provenance for all fields
- **Audit Trail**: Complete traceability for all calculations
- **Compliance Validation**: All legal requirements verified

## Test Reports

### Automated Report Generation
```bash
# Generate detailed test report
python tests/run_evidence_first_tests.py --report
```

Reports include:
- Test execution summary
- Requirements coverage analysis
- Performance metrics
- Failure analysis
- Recommendations

### Report Location
- Reports saved to: `tests/reports/evidence_first_test_report_YYYYMMDD_HHMMSS.json`
- Format: JSON with structured test results and metrics

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ImportError: Evidence-first components not available
```
**Solution**: Ensure all evidence-first services are implemented and available in the src/ directory.

#### 2. Database Errors
```
DatabaseError: Cannot create knowledge graph tables
```
**Solution**: Verify database permissions and schema initialization.

#### 3. Performance Issues
```
Test timeout: Execution time exceeds benchmark
```
**Solution**: Check system resources and optimize test data size.

#### 4. Confidence Scoring Issues
```
AssertionError: Critical field precision below 95% threshold
```
**Solution**: Review extraction patterns and NER model performance.

### Debug Mode
```bash
# Run tests with maximum verbosity
python tests/run_evidence_first_tests.py --verbose --test-type pipeline

# Run single test method for debugging
pytest tests/test_evidence_first_pipeline.py::TestEvidenceFirstPipeline::test_sample3_pdf_end_to_end_pipeline -v -s
```

## Continuous Integration

### GitHub Actions Integration
```yaml
name: Evidence-First QME Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Evidence-First Tests
        run: python tests/run_evidence_first_tests.py --report
```

### Test Coverage Requirements
- **Minimum Coverage**: 90% for evidence-first components
- **Critical Path Coverage**: 100% for calculation and validation logic
- **Integration Coverage**: 85% for workflow components

## Contributing

### Adding New Tests
1. Follow existing test patterns and naming conventions
2. Include comprehensive docstrings with requirement references
3. Use appropriate fixtures for test data setup
4. Verify tests pass in isolation and as part of the suite
5. Update this documentation for new test categories

### Test Data Guidelines
- Use realistic medical data that matches actual QME reports
- Include edge cases and boundary conditions
- Maintain consistency with Sample3.pdf and PQME reference data
- Document expected values and calculation methods

### Performance Considerations
- Keep individual tests under 30 seconds execution time
- Use appropriate test data sizes (not too large for CI)
- Mock external dependencies when appropriate
- Optimize database operations for test speed

## Validation Checklist

Before considering the evidence-first system ready for production:

- [ ] All pipeline tests pass with ≥95% critical field precision
- [ ] All calculation tests verify 100% programmatic accuracy
- [ ] Knowledge graph initialization creates ≥1000 nodes and ≥500 relationships
- [ ] Complete workflow executes within 5-minute benchmark
- [ ] Audit trail provides complete traceability for all operations
- [ ] Legal compliance validation achieves 100% compliance rate
- [ ] Integration tests demonstrate end-to-end functionality
- [ ] Performance benchmarks meet specified requirements
- [ ] Error handling gracefully manages edge cases
- [ ] Test coverage meets minimum requirements (90%)

## Support

For questions about the testing framework:

1. Review this documentation and test code comments
2. Check test execution logs for specific error details
3. Verify all dependencies are installed and services are running
4. Consult the main evidence-first QME system documentation
5. Review individual test files for specific validation logic

The testing framework is designed to provide comprehensive validation of the evidence-first QME system's core functionality, ensuring reliability, accuracy, and compliance with medical-legal requirements.