---
inclusion: always
---

# Data Directory (/data)

## Purpose
Centralized data storage for documents, databases, reference materials, and cached content.

## Directory Structure

### `/data/ama_guidelines/` - AMA Guidelines Reference Data
- **`chapters.json`**: AMA Guidelines 5th Edition chapter structure and content
- **`tables.json`**: AMA impairment rating tables and calculation data
- **Purpose**: Programmatic access to AMA guidelines for zero-LLM calculations

### `/data/cache/` - Temporary Cache Storage
- **Purpose**: Temporary storage for processed data, API responses, and computed results
- **Lifecycle**: Automatically cleaned based on retention policies
- **Usage**: Performance optimization and reducing API calls

### `/data/canonical/` - Canonical Reference Documents
- **`documents/`**: Master reference documents (AMA Guides, QME Study Guide, Sample reports)
- **`templates/`**: Master template files and formatting standards
- **Purpose**: Source of truth for knowledge base initialization and validation

### `/data/database/` - Database Files
- **`documents.db`**: SQLite database for document metadata and processing history
- **`.gitkeep`**: Ensures directory exists in version control
- **Purpose**: Persistent storage for application data

### `/data/documents/` - Uploaded Documents
- **Purpose**: Storage for user-uploaded documents during processing
- **Lifecycle**: Cleaned after processing completion or retention period
- **Security**: Temporary storage with automatic cleanup

### `/data/exports/` - Generated Exports
- **Purpose**: Storage for generated QME templates, reports, and export files
- **Format**: DOCX, PDF, and other output formats
- **Lifecycle**: Archived based on retention policies

### `/data/qme_references/` - QME Reference Patterns
- **`integrated_patterns.json`**: Integrated QME report patterns and structures
- **`legal_patterns.json`**: Legal compliance patterns and requirements
- **`procedural_requirements.json`**: QME procedural requirements and standards
- **`quality_standards.json`**: Quality standards and validation criteria
- **`reasoning_examples.json`**: Medical reasoning examples and patterns
- **`structure_patterns.json`**: Report structure patterns and templates

### `/data/sample_documents/` - Sample Documents for Testing
- **`Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf`**: Sample PQME document
- **`Injured worker-PQME-(09.08.2025)-DA CL-09.09.2025.p4.pdf`**: Sample PQME document
- **`Sample3.pdf`**: Reference sample document
- **Purpose**: Testing, validation, and demonstration

## Data Management Guidelines
- **Security**: No sensitive patient data in version control
- **Retention**: Implement data retention policies for temporary files
- **Backup**: Regular backup of database and canonical documents
- **Access Control**: Proper file permissions and access restrictions
- **Cleanup**: Automated cleanup of temporary and cache files

## File Naming Conventions
- Use descriptive names with timestamps for generated files
- Include document type and processing date in filenames
- Use consistent extensions (.json, .pdf, .docx, .db)
- Avoid spaces and special characters in filenames

## Data Privacy and Compliance
- Patient data must be anonymized or pseudonymized
- Implement secure deletion for sensitive documents
- Maintain audit trails for data access and modifications
- Comply with HIPAA and California privacy regulations