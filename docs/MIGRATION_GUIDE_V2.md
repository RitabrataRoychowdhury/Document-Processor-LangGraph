# QME System Refactor Migration Guide v2.0

## Overview

This guide provides comprehensive instructions for migrating from the existing QME system to the refactored architecture. The migration includes enhanced quality validation, performance monitoring, and system testing capabilities.

## Table of Contents

1. [Pre-Migration Preparation](#pre-migration-preparation)
2. [Migration Process](#migration-process)
3. [Post-Migration Validation](#post-migration-validation)
4. [Rollback Procedures](#rollback-procedures)
5. [Troubleshooting](#troubleshooting)
6. [Performance Monitoring](#performance-monitoring)
7. [Quality Validation](#quality-validation)

## Pre-Migration Preparation

### System Requirements

**Minimum Requirements:**
- Python 3.8+
- 4GB RAM available
- 2GB free disk space
- Network connectivity for OpenRouter API

**Recommended Requirements:**
- Python 3.9+
- 8GB RAM available
- 5GB free disk space
- Stable internet connection

### Dependency Check

Run the dependency check script:

```bash
python scripts/migrate_to_refactored_system_v2.py --dry-run --verbose
```

### Backup Current System

**Critical:** Always create a backup before migration:

```bash
# Create manual backup
cp -r config config_backup_$(date +%Y%m%d)
cp -r results results_backup_$(date +%Y%m%d)
cp -r src/config src_config_backup_$(date +%Y%m%d)
```

### Environment Validation

Verify your environment meets requirements:

```bash
# Check Python version
python --version

# Check available disk space
df -h

# Check memory
free -h

# Verify required packages
pip list | grep -E "(openai|requests|pyyaml|psutil|python-docx)"
```

## Migration Process

### Phase 1: Automated Migration

Run the automated migration script:

```bash
# Dry run first (recommended)
python scripts/migrate_to_refactored_system_v2.py --dry-run

# Actual migration
python scripts/migrate_to_refactored_system_v2.py
```

### Phase 2: Manual Configuration

#### 2.1 OpenRouter Configuration

Update `config/settings/openrouter_config.yaml`:

```yaml
api_endpoint: "https://openrouter.ai/api/v1/chat/completions"
model: "anthropic/claude-3.5-sonnet:beta"
max_tokens: 4000
temperature: 0.1
timeout: 30
retry_attempts: 3
retry_delay: 1.0
```

#### 2.2 Quality Validation Configuration

Configure `config/validation/quality_validation_config.yaml`:

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

#### 2.3 Template Assembly Configuration

Configure `config/templates/assembly_config.yaml`:

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

### Phase 3: Service Integration

#### 3.1 Update Service Registry

Ensure `src/services/service_registry.py` includes new services:

```python
from .comprehensive_quality_validation_service import ComprehensiveQualityValidationService
from .system_performance_monitor import SystemPerformanceMonitor
```

#### 3.2 Initialize New Services

Test service initialization:

```python
# Test script
from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
from src.services.system_performance_monitor import SystemPerformanceMonitor

# Initialize services
quality_validator = ComprehensiveQualityValidationService()
performance_monitor = SystemPerformanceMonitor()

print("✅ Services initialized successfully")
```

## Post-Migration Validation

### Automated Validation

Run the comprehensive validation suite:

```bash
# System comparison test
python tests/test_end_to_end_system_comparison.py

# Real document validation
python scripts/validate_system_with_real_documents.py --max-docs 5
```

### Manual Validation Checklist

- [ ] Configuration files are valid YAML
- [ ] All required directories exist
- [ ] Services initialize without errors
- [ ] OpenRouter API connectivity works
- [ ] Quality validation produces scores
- [ ] Template generation succeeds
- [ ] Performance monitoring is active

### Validation Commands

```bash
# Test configuration loading
python -c "
from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService
validator = ComprehensiveQualityValidationService()
print('✅ Quality validator initialized')
"

# Test performance monitoring
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
monitor.start_monitoring()
print('✅ Performance monitor started')
monitor.stop_monitoring()
"

# Test end-to-end processing
python -c "
from tests.test_end_to_end_system_comparison import SystemComparisonTestSuite
suite = SystemComparisonTestSuite()
print('✅ End-to-end test suite ready')
"
```

## Rollback Procedures

### Automatic Rollback

If migration fails, automatic rollback may be triggered:

```bash
# Check for rollback script
ls scripts/rollback_migration_*.py

# Execute manual rollback if needed
python scripts/rollback_migration_YYYYMMDD_HHMMSS.py
```

### Manual Rollback

If automatic rollback fails:

```bash
# Restore from backup
rm -rf config
cp -r config_backup_YYYYMMDD config

rm -rf results
cp -r results_backup_YYYYMMDD results

rm -rf src/config
cp -r src_config_backup_YYYYMMDD src/config

# Restart services
python src/app.py
```

### Rollback Verification

After rollback:

```bash
# Test basic functionality
python examples/qme_template_demo.py

# Check logs for errors
tail -f logs/system.log
```

## Performance Monitoring

### Starting Performance Monitoring

```python
from src.services.system_performance_monitor import SystemPerformanceMonitor

monitor = SystemPerformanceMonitor()
monitor.start_monitoring()

# Process documents with monitoring
with monitor.track_processing_session("test_session"):
    # Your processing code here
    pass

# Get performance summary
summary = monitor.get_performance_summary(24)  # Last 24 hours
print(f"Average processing time: {summary['processing_metrics']['avg_processing_time']:.2f}s")
```

### Performance Metrics

The system tracks:

- **Processing Time**: Per document and average
- **Resource Usage**: CPU, memory, disk I/O
- **Error Rates**: By type and component
- **Quality Scores**: Distribution and trends
- **Compliance Rates**: AMA and QME standards

### Performance Alerts

Automatic alerts for:

- High CPU usage (>80%)
- High memory usage (>85%)
- Slow processing (>30s per document)
- High error rates (>10%)

## Quality Validation

### Quality Metrics

The system evaluates four key metrics:

1. **Completeness** (25% weight): Required fields present
2. **Accuracy** (30% weight): Confidence scores and validation
3. **Consistency** (20% weight): Internal data coherence
4. **Compliance** (25% weight): AMA and QME standards

### Quality Thresholds

- **Minimum Overall Score**: 0.75
- **Production Ready**: 0.85+
- **Excellent Quality**: 0.90+

### Running Quality Validation

```python
from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService

validator = ComprehensiveQualityValidationService()

# Validate extraction result
quality_result = validator.validate_extraction_quality(extraction_result)

print(f"Overall Score: {quality_result.overall_score:.3f}")
print(f"Weighted Score: {quality_result.weighted_score:.3f}")

# Save detailed report
report_path = validator.save_validation_report(quality_result)
print(f"Report saved: {report_path}")
```

### Quality Reports

Quality reports include:

- Individual metric scores and details
- Compliance check results
- Specific issues identified
- Actionable recommendations
- Processing performance data

## Troubleshooting

### Common Issues

#### 1. Configuration File Errors

**Error**: `yaml.scanner.ScannerError`

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/settings/openrouter_config.yaml'))"

# Fix common YAML issues
# - Check indentation (use spaces, not tabs)
# - Ensure proper quoting of strings
# - Validate special characters
```

#### 2. Service Initialization Failures

**Error**: `ImportError` or `ModuleNotFoundError`

**Solution**:
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall dependencies
pip install -r requirements.txt

# Verify imports
python -c "from src.services.comprehensive_quality_validation_service import ComprehensiveQualityValidationService"
```

#### 3. OpenRouter API Issues

**Error**: `Connection timeout` or `API key invalid`

**Solution**:
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Test connectivity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Update configuration
vim config/settings/openrouter_config.yaml
```

#### 4. Performance Issues

**Symptoms**: Slow processing, high memory usage

**Solution**:
```bash
# Check system resources
htop
df -h

# Monitor performance
python -c "
from src.services.system_performance_monitor import SystemPerformanceMonitor
monitor = SystemPerformanceMonitor()
summary = monitor.get_performance_summary(1)
print(summary)
"

# Optimize configuration
# - Reduce max_tokens in OpenRouter config
# - Increase timeout values
# - Enable caching
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Log Analysis

Check logs for issues:

```bash
# System logs
tail -f logs/system.log

# Migration logs
tail -f logs/migration_*.log

# Performance logs
tail -f logs/performance.log

# Error patterns
grep -i error logs/*.log | tail -20
```

## Migration Checklist

### Pre-Migration
- [ ] System requirements verified
- [ ] Dependencies installed
- [ ] Backup created
- [ ] Dry run completed successfully

### During Migration
- [ ] Automated migration script executed
- [ ] Configuration files updated
- [ ] Services integrated
- [ ] No critical errors reported

### Post-Migration
- [ ] Validation tests passed
- [ ] Services initialize correctly
- [ ] Quality validation working
- [ ] Performance monitoring active
- [ ] End-to-end processing successful

### Production Readiness
- [ ] Real document testing completed
- [ ] Performance benchmarks met
- [ ] Quality thresholds achieved
- [ ] Error handling verified
- [ ] Monitoring and alerting configured

## Support and Resources

### Documentation
- [Quality Validation Service](../src/services/comprehensive_quality_validation_service.py)
- [Performance Monitor](../src/services/system_performance_monitor.py)
- [End-to-End Testing](../tests/test_end_to_end_system_comparison.py)

### Scripts
- Migration: `scripts/migrate_to_refactored_system_v2.py`
- Validation: `scripts/validate_system_with_real_documents.py`
- Rollback: `scripts/rollback_migration_*.py` (auto-generated)

### Configuration Files
- OpenRouter: `config/settings/openrouter_config.yaml`
- Quality: `config/validation/quality_validation_config.yaml`
- Templates: `config/templates/assembly_config.yaml`

### Logs and Reports
- Migration logs: `logs/migration_*.log`
- Performance reports: `results/performance_reports/`
- Quality reports: `results/validation_reports/`

---

**Last Updated**: $(date)
**Migration Version**: 2.0
**Compatibility**: QME System Refactor v1.0+