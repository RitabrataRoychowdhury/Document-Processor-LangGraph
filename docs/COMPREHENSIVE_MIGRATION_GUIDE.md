# Comprehensive Migration Guide for QME System Refactor

## Overview

This guide provides comprehensive instructions for migrating from the legacy QME system to the refactored architecture. The migration includes quality validation, system testing, performance monitoring, and complete documentation.

## Migration Architecture

### Before Migration (Legacy System)
```
Legacy QME System
├── Basic extraction
├── Simple template generation
├── Limited quality checks
├── Scattered configuration
└── Manual validation
```

### After Migration (Refactored System)
```
Refactored QME System
├── OpenRouter-powered extraction
├── Comprehensive quality validation
├── Professional template assembly
├── Enhanced RAG pipeline
├── System performance monitoring
├── Organized configuration management
└── Automated testing and validation
```

## Pre-Migration Checklist

### System Requirements
- [ ] Python 3.8+ installed
- [ ] Required dependencies installed (see requirements.txt)
- [ ] OpenRouter API key configured
- [ ] Minimum 2GB free disk space
- [ ] Backup of existing system created

### Service Dependencies
- [ ] OpenRouter API access verified
- [ ] Configuration files validated
- [ ] Existing templates archived
- [ ] Database connections tested
- [ ] Log directories created

### Quality Validation Setup
- [ ] Quality validation configuration reviewed
- [ ] AMA Guidelines compliance rules configured
- [ ] QME Standards validation rules set up
- [ ] Performance thresholds defined
- [ ] Error handling mechanisms tested

## Migration Process

### Phase 1: System Preparation

#### 1.1 Create System Backup
```bash
# Run the migration script with backup
python scripts/migrate_to_refactored_system_v2.py --backup-only
```

#### 1.2 Validate Current System
```bash
# Validate existing system before migration
python scripts/validate_system_with_real_documents.py --pre-migration
```

#### 1.3 Initialize New Configuration Structure
```bash
# Create new configuration directories
mkdir -p config/{prompts/{extraction,generation,validation},settings,templates,validation,system}
mkdir -p results/{generated_documents,templates_archive,processing_logs,validation_reports,performance_reports}
```

### Phase 2: Service Migration

#### 2.1 OpenRouter Integration Service
```bash
# Test OpenRouter configuration
python scripts/test_openrouter_sonoma_sky.py

# Configure extraction service
python -c "
from src.services.openrouter_extraction_service import OpenRouterExtractionService
service = OpenRouterExtractionService()
print('OpenRouter service initialized successfully')
"
```

#### 2.2 Quality Validation Service
```bash
# Initialize comprehensive quality validation
python -c "
from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
validator = ComprehensiveQualityValidationService()
print('Quality validation service initialized successfully')
"
```

#### 2.3 Template Assembly Engine
```bash
# Test professional template assembly
python examples/professional_template_assembly_engine_demo.py
```

#### 2.4 Performance Monitoring
```bash
# Initialize system performance monitoring
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
monitor.start_monitoring()
print('Performance monitoring started')
monitor.stop_monitoring()
"
```

### Phase 3: Data Migration

#### 3.1 Archive Existing Templates
```bash
# Move existing templates to archive
python scripts/migrate_to_refactored_system_v2.py --archive-templates
```

#### 3.2 Migrate Configuration Files
```bash
# Migrate configuration to new structure
python scripts/migrate_to_refactored_system_v2.py --migrate-config
```

#### 3.3 Update Service Registry
```bash
# Update service configurations
python -c "
from src.services.service_registry import ServiceRegistry
registry = ServiceRegistry()
registry.register_all_services()
print('Service registry updated')
"
```

### Phase 4: Quality Validation and Testing

#### 4.1 Run Comprehensive System Validation
```bash
# Run comprehensive validation with real documents
python scripts/comprehensive_system_validation.py --max-docs 5 --verbose
```

#### 4.2 Compare with Legacy System
```bash
# Run comparison tests
python tests/test_end_to_end_system_comparison.py
```

#### 4.3 Performance Validation
```bash
# Run performance tests
python scripts/test_qme_performance.py --comprehensive
```

#### 4.4 Quality Metrics Validation
```bash
# Validate quality metrics
python tests/test_end_to_end_quality_validation.py
```

### Phase 5: Production Readiness

#### 5.1 Final System Validation
```bash
# Run final comprehensive validation
python scripts/comprehensive_system_validation.py --max-docs 10 --save-intermediate
```

#### 5.2 Generate Migration Report
```bash
# Generate comprehensive migration report
python scripts/migrate_to_refactored_system_v2.py --generate-report
```

#### 5.3 Performance Baseline
```bash
# Establish performance baseline
python scripts/test_qme_performance.py --baseline
```

## Post-Migration Validation

### Quality Assurance Tests

#### Document Processing Pipeline
```bash
# Test complete pipeline with real documents
python scripts/validate_system_with_real_documents.py --comprehensive
```

#### Template Quality Validation
```bash
# Validate generated templates
python tests/test_professional_template_assembler_validation.py
```

#### Compliance Validation
```bash
# Validate AMA and QME compliance
python tests/test_ama_guidelines_integration.py
python tests/test_comprehensive_qme_field_service.py
```

### Performance Validation

#### System Performance Monitoring
```bash
# Monitor system performance
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
monitor.start_monitoring()
# Run your tests here
summary = monitor.get_performance_summary(1)
print(f'Performance Summary: {summary}')
monitor.stop_monitoring()
"
```

#### Memory and CPU Usage
```bash
# Check resource usage
python scripts/test_qme_performance.py --resource-monitoring
```

### Error Handling Validation

#### Error Recovery Testing
```bash
# Test error handling and recovery
python tests/test_error_handling.py --comprehensive
```

#### Rollback Testing
```bash
# Test rollback capability (in safe environment)
python scripts/rollback_migration.py --test-mode
```

## Configuration Management

### Quality Validation Configuration

#### config/validation/quality_validation_config.yaml
```yaml
quality_metrics:
  completeness:
    weight: 0.25
    threshold: 0.8
  accuracy:
    weight: 0.30
    threshold: 0.85
  consistency:
    weight: 0.20
    threshold: 0.75
  compliance:
    weight: 0.25
    threshold: 0.90

compliance_rules:
  ama_guidelines:
    severity: "critical"
    enabled: true
  qme_standards:
    severity: "critical"
    enabled: true
  formatting_rules:
    severity: "warning"
    enabled: true
  data_completeness:
    severity: "critical"
    enabled: true

thresholds:
  minimum_overall_score: 0.75
  critical_compliance_required: true
  warning_threshold: 0.65
```

#### config/settings/openrouter_config.yaml
```yaml
api_endpoint: "https://openrouter.ai/api/v1/chat/completions"
model: "anthropic/claude-3.5-sonnet:beta"
max_tokens: 4000
temperature: 0.1
timeout: 30
retry_attempts: 3
retry_delay: 1.0
```

#### config/templates/assembly_config.yaml
```yaml
template_settings:
  default_template: "qme_professional_template.docx"
  output_format: "docx"
  include_metadata: true
  auto_save: true

formatting_rules:
  font_family: "Times New Roman"
  font_size: 12
  line_spacing: 1.15
  margin_inches: 1.0

quality_checks:
  validate_before_assembly: true
  validate_after_assembly: true
  require_all_sections: false
```

## Monitoring and Maintenance

### Continuous Quality Monitoring

#### Daily Quality Checks
```bash
# Set up daily quality validation
# Add to cron job:
# 0 2 * * * /path/to/python /path/to/scripts/comprehensive_system_validation.py --max-docs 3 >> /path/to/logs/daily_validation.log 2>&1
```

#### Weekly Performance Reports
```bash
# Generate weekly performance reports
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
report_path = monitor.save_performance_report()
print(f'Weekly performance report saved to: {report_path}')
"
```

#### Monthly System Health Checks
```bash
# Comprehensive monthly health check
python scripts/comprehensive_system_validation.py --max-docs 20 --save-intermediate --verbose
```

### Error Monitoring and Alerting

#### Error Pattern Analysis
```bash
# Analyze error patterns
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
error_analysis = monitor.get_error_analysis(24)  # Last 24 hours
print('Error Analysis:', error_analysis)
"
```

#### Performance Threshold Monitoring
```bash
# Monitor performance thresholds
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
summary = monitor.get_performance_summary(1)
if summary['processing_metrics']['avg_processing_time'] > 30:
    print('WARNING: Processing time exceeds threshold')
"
```

## Troubleshooting

### Common Migration Issues

#### Issue: OpenRouter API Key Not Found
```bash
# Solution: Configure API key
python scripts/manage_api_keys.py --set openrouter YOUR_API_KEY
```

#### Issue: Quality Validation Fails
```bash
# Solution: Check configuration and run diagnostics
python -c "
from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
validator = ComprehensiveQualityValidationService()
# Check if configuration is loaded properly
print('Validation config loaded:', validator.validation_config)
"
```

#### Issue: Template Generation Fails
```bash
# Solution: Validate template engine configuration
python examples/professional_template_assembly_engine_demo.py --debug
```

#### Issue: Performance Degradation
```bash
# Solution: Run performance analysis
python scripts/test_qme_performance.py --analyze --verbose
```

### Rollback Procedures

#### Emergency Rollback
```bash
# If critical issues occur, rollback to previous system
python scripts/rollback_migration.py --emergency
```

#### Partial Rollback
```bash
# Rollback specific components
python scripts/rollback_migration.py --component extraction_service
python scripts/rollback_migration.py --component template_engine
```

#### Validation After Rollback
```bash
# Validate system after rollback
python scripts/validate_system_with_real_documents.py --post-rollback
```

## Success Criteria

### Migration Success Indicators

#### Quality Metrics
- [ ] Overall success rate > 85%
- [ ] Average quality score > 0.80
- [ ] Compliance rate > 90%
- [ ] Processing time < 60 seconds per document

#### System Performance
- [ ] Memory usage < 1GB during processing
- [ ] CPU usage < 80% during peak load
- [ ] Error rate < 5%
- [ ] System uptime > 99%

#### Functional Requirements
- [ ] All document types processed successfully
- [ ] Template generation quality maintained or improved
- [ ] AMA Guidelines compliance validated
- [ ] QME Standards compliance validated

### Production Readiness Checklist

#### System Validation
- [ ] Comprehensive system validation passed
- [ ] Performance benchmarks met
- [ ] Error handling tested and validated
- [ ] Rollback procedures tested

#### Documentation
- [ ] Migration documentation complete
- [ ] User guides updated
- [ ] API documentation current
- [ ] Troubleshooting guides available

#### Monitoring
- [ ] Performance monitoring active
- [ ] Error alerting configured
- [ ] Quality metrics tracking enabled
- [ ] Automated health checks running

## Support and Maintenance

### Regular Maintenance Tasks

#### Weekly Tasks
- Review performance reports
- Check error logs
- Validate quality metrics
- Update configuration if needed

#### Monthly Tasks
- Comprehensive system validation
- Performance optimization review
- Security updates
- Documentation updates

#### Quarterly Tasks
- Full system health assessment
- Capacity planning review
- Technology stack updates
- User feedback integration

### Getting Help

#### Documentation Resources
- System architecture documentation: `docs/`
- API documentation: `docs/api/`
- Configuration guides: `config/`
- Example implementations: `examples/`

#### Diagnostic Tools
- System validation: `scripts/comprehensive_system_validation.py`
- Performance analysis: `scripts/test_qme_performance.py`
- Error analysis: `src/services/system_performance_monitor.py`
- Quality validation: `tests/test_end_to_end_quality_validation.py`

#### Support Contacts
- Technical issues: Check logs and run diagnostic scripts
- Performance issues: Use performance monitoring tools
- Quality issues: Run quality validation tests
- Configuration issues: Review configuration documentation

## Conclusion

The migration to the refactored QME system provides significant improvements in:

- **Quality**: Comprehensive validation with AMA/QME compliance
- **Performance**: Enhanced processing with monitoring
- **Reliability**: Robust error handling and recovery
- **Maintainability**: Organized configuration and documentation
- **Scalability**: Modular architecture for future growth

Following this migration guide ensures a smooth transition with minimal disruption and maximum benefit from the enhanced system capabilities.