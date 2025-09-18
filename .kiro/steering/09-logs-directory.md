---
inclusion: always
---

# Logs Directory (/logs)

## Purpose
Centralized logging for all system components with structured logging and audit trails.

## Log Files

### System Logs
- **`qme_system.log`**: Main system log with application-wide events
- **`document_qa_system.log`**: Document Q&A system specific logging
- **`errors.log`**: Centralized error logging across all components
- **`performance.log`**: Performance metrics and timing information

### Validation and Testing Logs
- **`comprehensive_validation_20250917_093712.log`**: System validation results
- **`comprehensive_validation_20250917_093805.log`**: Additional validation run
- **`real_document_validation.log`**: Real document processing validation
- **`migration.log`**: System migration and upgrade logs

## Log Categories

### Application Logs
- **System Events**: Startup, shutdown, configuration changes
- **User Actions**: Document uploads, template generations, Q&A interactions
- **Processing Events**: Document processing, field extraction, validation
- **API Calls**: External API interactions and responses

### Error Logs
- **System Errors**: Application crashes, configuration errors
- **Processing Errors**: Document processing failures, extraction errors
- **API Errors**: External service failures, timeout errors
- **Validation Errors**: Data validation failures, compliance issues

### Performance Logs
- **Processing Times**: Document processing duration, API response times
- **Resource Usage**: Memory usage, CPU utilization, disk I/O
- **Throughput Metrics**: Documents processed per hour, success rates
- **Bottleneck Analysis**: Performance bottlenecks and optimization opportunities

### Audit Logs
- **User Activities**: Complete audit trail of user actions
- **Data Access**: Document access, modification, deletion
- **System Changes**: Configuration changes, system updates
- **Compliance Events**: Regulatory compliance activities

## Log Format Standards

### Structured Logging
```json
{
  "timestamp": "2025-09-17T09:37:12.123Z",
  "level": "INFO",
  "component": "document_processor",
  "correlation_id": "req_12345",
  "message": "Document processing completed",
  "metadata": {
    "document_id": "doc_67890",
    "processing_time_ms": 1500,
    "fields_extracted": 25
  }
}
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General information about system operation
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error conditions that don't stop the application
- **CRITICAL**: Critical errors that may cause system failure

## Log Management

### Rotation Policy
- **Daily Rotation**: Logs rotate daily at midnight
- **Size Limits**: Maximum 100MB per log file
- **Retention**: Keep logs for 30 days (configurable)
- **Compression**: Older logs are compressed to save space

### Log Aggregation
- **Centralized Collection**: All logs collected in `/logs` directory
- **Correlation IDs**: Track requests across multiple components
- **Structured Format**: JSON format for easy parsing and analysis
- **Metadata Enrichment**: Include context and correlation information

## Monitoring and Alerting

### Log Monitoring
- **Error Rate Monitoring**: Alert on high error rates
- **Performance Monitoring**: Alert on slow processing times
- **System Health**: Monitor system health indicators
- **Compliance Monitoring**: Track compliance-related events

### Alert Conditions
- **Critical Errors**: Immediate alerts for critical system errors
- **Performance Degradation**: Alerts for performance issues
- **Security Events**: Alerts for security-related events
- **Compliance Issues**: Alerts for compliance violations

## Security and Privacy

### Log Security
- **Access Control**: Restricted access to log files
- **Encryption**: Sensitive logs encrypted at rest
- **Sanitization**: Remove sensitive data from logs
- **Audit Trail**: Log access is audited

### Privacy Compliance
- **Data Minimization**: Log only necessary information
- **Anonymization**: Remove or pseudonymize personal data
- **Retention Limits**: Automatic deletion after retention period
- **Access Logging**: Log all access to sensitive logs

## Development Guidelines

### Logging Best Practices
- **Consistent Format**: Use structured logging format
- **Appropriate Levels**: Use correct log levels for different events
- **Context Information**: Include relevant context and correlation IDs
- **Performance Impact**: Minimize logging performance impact
- **Error Details**: Include stack traces and error details for debugging

### Log Analysis
- **Search and Filter**: Easy searching and filtering of logs
- **Correlation**: Ability to correlate events across components
- **Visualization**: Dashboards and visualizations for log analysis
- **Alerting**: Automated alerting based on log patterns