---
inclusion: always
---

# Results Directory (/results)

## Purpose
Storage for all system outputs, generated documents, validation reports, and processing results.

## Directory Structure

### `/results/audit_trails/` - Audit Trail Storage
- **Purpose**: Complete audit trails for compliance and traceability
- **Content**: Processing history, user actions, system decisions
- **Retention**: Long-term storage for regulatory compliance

### `/results/documents/` - Processed Documents
- **Purpose**: Storage for processed and analyzed documents
- **Content**: Extracted content, metadata, processing annotations
- **Lifecycle**: Archived after processing completion

### `/results/extraction_results/` - Field Extraction Results
- **Purpose**: Results from document field extraction processes
- **Content**: Extracted fields, confidence scores, evidence snippets
- **Format**: JSON files with structured extraction data

### `/results/generated_documents/` - Generated QME Templates
- **`2025/`**: Year-based organization for generated documents
- **Purpose**: Final QME templates and reports
- **Formats**: DOCX, PDF, and other output formats
- **Naming**: Includes timestamp and patient identifier

### `/results/metadata/` - Document Metadata
- **Purpose**: Metadata for all processed documents
- **Content**: Processing timestamps, file information, workflow status
- **Usage**: System tracking and audit purposes

### `/results/performance_reports/` - Performance Metrics
- **`system_performance_20250917_092935.json`**: System performance snapshot
- **`system_performance_20250917_094239.json`**: Performance metrics data
- **Purpose**: Performance monitoring and optimization
- **Content**: Processing times, resource usage, throughput metrics

### `/results/processing_logs/` - Processing Logs
- **`.gitkeep`**: Ensures directory exists in version control
- **Purpose**: Detailed processing logs for debugging
- **Content**: Step-by-step processing information

### `/results/quality_reports/` - Quality Assessment Reports
- **Purpose**: Quality validation and assessment results
- **Content**: Quality scores, validation results, improvement recommendations
- **Usage**: Continuous quality improvement

### `/results/template_results/` - Template Generation Results
- **Purpose**: Results from template generation processes
- **Content**: Generated templates, assembly logs, validation results
- **Format**: Structured data with template metadata

### `/results/templates_archive/` - Template Archive
- **`QME_Report_20250916_225531.docx`**: Archived QME report
- **`QME_Report_John Doe_20250916_221441.docx`**: Patient-specific report
- **`QME_Report_Unknown_20250916_221526.docx`**: Anonymous report
- **Purpose**: Long-term storage of generated templates
- **Organization**: Date-based archival system

### `/results/validation_reports/` - Validation Results
- **`comprehensive_system_validation_20250917_093806.json`**: System validation results
- **`final_comprehensive_test_report.md`**: Final test report
- **`performance_stability_report.json`**: Performance stability metrics
- **`quality_validation_*.json`**: Quality validation results
- **`session_state_fix_summary.md`**: Session state fix documentation
- **Purpose**: Validation and testing results storage

### `/results/validation_results/` - Validation Outcomes
- **Purpose**: Detailed validation outcomes and decisions
- **Content**: Pass/fail results, validation criteria, recommendations
- **Usage**: Quality assurance and compliance verification

## File Naming Conventions
- **Timestamps**: Use ISO format (YYYYMMDD_HHMMSS) for timestamps
- **Identifiers**: Include document/patient identifiers when appropriate
- **Types**: Clear indication of content type (validation, performance, quality)
- **Versions**: Version numbers for iterative results

## Data Management
- **Retention Policies**: Implement appropriate retention for different result types
- **Archival**: Automatic archival of older results
- **Cleanup**: Regular cleanup of temporary and intermediate results
- **Backup**: Regular backup of critical results and reports

## Security and Privacy
- **Anonymization**: Remove or pseudonymize patient identifiers
- **Access Control**: Restrict access to sensitive results
- **Encryption**: Encrypt sensitive results at rest
- **Audit Logging**: Log all access to results directories

## Result Categories
1. **Processing Results**: Direct outputs from document processing
2. **Validation Results**: Quality and compliance validation outcomes
3. **Performance Results**: System performance and metrics
4. **Generated Content**: Final templates and reports
5. **Audit Results**: Compliance and audit trail information

## Integration Points
- Results are referenced by the UI for display and download
- Validation results feed back into quality improvement processes
- Performance results inform system optimization
- Audit trails support compliance reporting
- Generated documents are delivered to end users