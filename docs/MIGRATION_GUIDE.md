# QME System Migration Guide

## Overview

This guide provides comprehensive instructions for migrating from the existing QME document generation system to the refactored architecture. The migration preserves all existing data while introducing enhanced quality validation, performance monitoring, and improved system architecture.

## Migration Benefits

### Quality Improvements
- **Enhanced Extraction Accuracy**: OpenRouter's Sonoma Sky Alpha model provides superior document processing
- **Comprehensive Quality Validation**: Automated quality scoring and compliance checking
- **Professional Template Assembly**: Reliable document generation with consistent formatting

### System Architecture Improvements
- **Modular Design**: Clean separation of concerns with plug-and-play components
- **Configuration-Driven**: Externalized prompts and settings for easy customization
- **Performance Monitoring**: Real-time system health monitoring and alerting
- **Better Error Handling**: Comprehensive error recovery and reporting

### Operational Benefits
- **Organized Results**: Structured document storage with date-based organization
- **Migration Safety**: Complete backup and rollback capabilities
- **Validation Testing**: End-to-end quality validation against existing templates

## Pre-Migration Checklist

### System Requirements
- [ ] Python 3.8 or higher
- [ ] All required dependencies installed (`pip install -r requirements.txt`)
- [ ] Sufficient disk space for backup (at least 2GB recommended)
- [ ] OpenRouter API key configured (if using extraction service)

### Data Preparation
- [ ] Backup any critical documents outside the system
- [ ] Ensure all pending document processing is complete
- [ ] Stop any running QME system processes
- [ ] Verify database integrity

### Environment Setup
- [ ] Create logs directory: `mkdir -p logs`
- [ ] Ensure write permissions for results and config directories
- [ ] Test database connectivity
- [ ] Verify API key access (if applicable)

## Migration Process

### Step 1: Run Migration Script

The migration script handles the complete transition automatically:

```bash
# Full migration with backup and validation
python scripts/migrate_to_refactored_system.py

# Migration options
python scripts/migrate_to_refactored_system.py --no-backup    # Skip backup creation
python scripts/migrate_to_refactored_system.py --no-validation  # Skip validation
python scripts/migrate_to_refactored_system.py --dry-run    # Preview changes only
```

### Step 2: Verify Migration Results

Check the migration report:
```bash
# View migration report
cat results/migration_reports/migration_report_YYYYMMDD_HHMMSS.json

# Check migration logs
tail -f logs/migration.log
```

### Step 3: Validate System Functionality

Run comprehensive quality validation tests:
```bash
# Run end-to-end quality validation
python -m pytest tests/test_end_to_end_quality_validation.py -v

# Run specific validation tests
python tests/test_end_to_end_quality_validation.py
```

## Migration Details

### What Gets Migrated

#### Documents and Results
- **Existing Documents**: Moved to `results/templates_archive/`
- **Generated Reports**: Organized by date in `results/generated_documents/`
- **Processing Logs**: Centralized in `results/processing_logs/`
- **Validation Reports**: Stored in `results/validation_reports/`

#### Configuration Files
- **Prompt Templates**: Externalized to `config/prompts/`
- **System Settings**: Organized in `config/settings/`
- **Template Configurations**: Stored in `config/templates/`
- **Validation Rules**: Defined in `config/validation/`

#### Database Schema
- **New Columns**: Added for quality scoring and performance tracking
- **Backward Compatibility**: Existing data preserved
- **Enhanced Indexing**: Improved query performance

#### Service Configurations
- **OpenRouter Integration**: API configuration and model settings
- **Performance Monitoring**: Thresholds and alert configurations
- **Quality Validation**: Compliance rules and scoring parameters

### Directory Structure After Migration

```
project_root/
├── config/
│   ├── prompts/
│   │   ├── extraction/
│   │   │   ├── patient_info.yaml
│   │   │   ├── medical_findings.yaml
│   │   │   └── impairment_rating.yaml
│   │   ├── generation/
│   │   │   ├── history_section.yaml
│   │   │   ├── examination_section.yaml
│   │   │   └── diagnosis_section.yaml
│   │   └── validation/
│   │       ├── quality_checks.yaml
│   │       └── compliance_rules.yaml
│   ├── templates/
│   │   ├── qme_template_structure.yaml
│   │   └── assembly_config.yaml
│   ├── settings/
│   │   └── openrouter_config.yaml
│   ├── system/
│   │   └── component_config.yaml
│   ├── validation/
│   │   └── quality_validation_config.yaml
│   └── monitoring/
│       └── performance_config.yaml
├── results/
│   ├── generated_documents/
│   │   └── YYYY/
│   │       └── MM/
│   ├── templates_archive/
│   │   └── YYYY/
│   │       └── MM/
│   ├── processing_logs/
│   ├── validation_reports/
│   └── migration_reports/
├── src/
│   └── services/
│       ├── quality_validation_service.py
│       ├── performance_monitoring_service.py
│       └── [existing services...]
└── tests/
    └── test_end_to_end_quality_validation.py
```

## Post-Migration Configuration

### OpenRouter API Configuration

If using OpenRouter extraction service, configure your API key:

```bash
# Set API key securely
python scripts/manage_api_keys.py --set-openrouter-key

# Or set environment variable
export OPENROUTER_API_KEY="your_api_key_here"
```

### Quality Validation Settings

Customize quality validation thresholds in `config/validation/quality_validation_config.yaml`:

```yaml
quality_thresholds:
  minimum_overall_score: 0.75
  minimum_accuracy_score: 0.80
  minimum_compliance_score: 0.90
  minimum_completeness_score: 0.85
```

### Performance Monitoring

Configure performance monitoring in `config/monitoring/performance_config.yaml`:

```yaml
performance_thresholds:
  processing_time_seconds: 30.0
  memory_usage_percent: 80.0
  error_rate_percent: 5.0
  quality_score_minimum: 0.75
```

## Testing the Migrated System

### Basic Functionality Test

```bash
# Test document processing
python run_professional_qme_system.py

# Test quality validation
python -c "
from src.services.quality_validation_service import QualityValidationService
validator = QualityValidationService()
print('Quality validation service initialized successfully')
"
```

### Comprehensive Quality Tests

```bash
# Run all quality validation tests
python tests/test_end_to_end_quality_validation.py

# Run performance monitoring tests
python -m pytest tests/test_end_to_end_quality_validation.py::test_performance_monitoring -v

# Run template comparison tests
python -m pytest tests/test_end_to_end_quality_validation.py::test_template_comparison -v
```

### Real Document Validation

Test with actual documents:
```bash
# Validate against real documents
python -c "
from tests.test_end_to_end_quality_validation import EndToEndQualityTestSuite
suite = EndToEndQualityTestSuite()
results = suite.run_comprehensive_quality_tests()
print(f'Overall quality improvement: {results[\"test_summary\"][\"overall_quality_improvement\"]}')
"
```

## Troubleshooting

### Common Migration Issues

#### Migration Script Fails
```bash
# Check logs for detailed error information
tail -f logs/migration.log

# Verify permissions
ls -la results/ config/

# Check disk space
df -h
```

#### Service Initialization Errors
```bash
# Test individual services
python -c "from src.services.quality_validation_service import QualityValidationService; QualityValidationService()"

# Check configuration files
python -c "import yaml; print(yaml.safe_load(open('config/system/component_config.yaml')))"
```

#### Quality Validation Issues
```bash
# Run validation with debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.services.quality_validation_service import QualityValidationService
validator = QualityValidationService()
"
```

### Performance Issues

#### Slow Processing
- Check system resources: `htop` or `top`
- Review performance monitoring logs
- Adjust processing timeouts in configuration

#### Memory Usage
- Monitor memory with: `free -h`
- Check for memory leaks in logs
- Adjust batch processing sizes

#### API Rate Limits
- Review OpenRouter API usage
- Implement request throttling
- Check API key limits

## Rollback Procedure

If migration issues occur, you can rollback to the previous system:

### Automatic Rollback
```bash
# Restore from backup (if backup was created)
python scripts/rollback_migration.py --backup-dir migration_backup_YYYYMMDD_HHMMSS
```

### Manual Rollback
```bash
# Stop any running processes
pkill -f "python.*qme"

# Restore backup directories
cp -r migration_backup_YYYYMMDD_HHMMSS/results_backup/* results/
cp -r migration_backup_YYYYMMDD_HHMMSS/config_backup/* config/
cp -r migration_backup_YYYYMMDD_HHMMSS/services_backup/* src/services/

# Restore database
cp migration_backup_YYYYMMDD_HHMMSS/documents_backup.db data/database/documents.db

# Restart old system
python main.py
```

## Validation and Quality Assurance

### Quality Metrics

The migrated system tracks comprehensive quality metrics:

- **Completeness Score**: Percentage of required sections present
- **Accuracy Score**: Medical information accuracy and consistency
- **Compliance Score**: Adherence to QME regulations and AMA guidelines
- **Consistency Score**: Internal document consistency
- **Professional Formatting Score**: Document presentation quality

### Performance Metrics

Monitor system performance with:

- **Processing Time**: Document processing duration
- **Memory Usage**: System memory consumption
- **Error Rate**: Processing error frequency
- **Throughput**: Documents processed per unit time
- **Quality Score Trends**: Quality improvement over time

### Compliance Validation

Ensure compliance with:

- **AMA Guidelines**: Impairment rating calculations and methodology
- **QME Regulations**: Required sections and professional standards
- **Legal Requirements**: Documentation and audit trail requirements
- **Professional Standards**: Medical accuracy and clinical reasoning

## Support and Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review performance monitoring reports
- Check quality validation trends
- Update prompt configurations as needed

#### Monthly
- Analyze quality improvement metrics
- Review and update compliance rules
- Backup configuration changes

#### Quarterly
- Comprehensive system performance review
- Update documentation and procedures
- Review and optimize processing workflows

### Getting Help

#### Log Analysis
```bash
# View recent errors
grep -i error logs/*.log | tail -20

# Monitor real-time logs
tail -f logs/document_qa_system.log

# Check performance logs
grep -i "performance" logs/*.log
```

#### System Health Check
```bash
# Run health check
python -c "
from src.services.performance_monitoring_service import PerformanceMonitoringService
monitor = PerformanceMonitoringService()
report = monitor.generate_health_report()
print(f'Overall Health: {report.overall_health_score:.2f}')
"
```

#### Quality Assessment
```bash
# Generate quality report
python -c "
from tests.test_end_to_end_quality_validation import EndToEndQualityTestSuite
suite = EndToEndQualityTestSuite()
results = suite.run_comprehensive_quality_tests()
print('Quality validation completed - check results/quality_validation/')
"
```

## Conclusion

The migration to the refactored QME system provides significant improvements in quality, performance, and maintainability. The comprehensive validation and monitoring capabilities ensure reliable document generation while maintaining compliance with professional standards.

For additional support or questions about the migration process, refer to the system logs and validation reports generated during migration.

## Appendix

### Configuration File Templates

#### Quality Validation Configuration
```yaml
# config/validation/quality_validation_config.yaml
required_sections:
  - patient_information
  - history_of_present_illness
  - physical_examination
  - medical_findings
  - diagnosis
  - impairment_rating
  - recommendations

quality_thresholds:
  minimum_overall_score: 0.75
  minimum_accuracy_score: 0.80
  minimum_compliance_score: 0.90

validation_weights:
  completeness: 0.25
  accuracy: 0.30
  consistency: 0.20
  compliance: 0.15
  readability: 0.05
  formatting: 0.05
```

#### Performance Monitoring Configuration
```yaml
# config/monitoring/performance_config.yaml
performance_thresholds:
  processing_time_seconds: 30.0
  memory_usage_percent: 80.0
  cpu_usage_percent: 85.0
  error_rate_percent: 5.0
  quality_score_minimum: 0.75

alert_settings:
  email_notifications: false
  log_alerts: true
  alert_cooldown_minutes: 15

monitoring_intervals:
  system_metrics_seconds: 30
  component_health_minutes: 5
  quality_assessment_hours: 1
```

### Migration Checklist

- [ ] Pre-migration backup completed
- [ ] Migration script executed successfully
- [ ] Configuration files validated
- [ ] Directory structure verified
- [ ] Database schema updated
- [ ] Services initialized successfully
- [ ] Quality validation tests passed
- [ ] Performance monitoring active
- [ ] Real document validation completed
- [ ] Migration report reviewed
- [ ] System documentation updated
- [ ] User training completed (if applicable)