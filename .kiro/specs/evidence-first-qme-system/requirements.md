# Requirements Document

## Introduction

This specification defines an evidence-first QME (Qualified Medical Evaluator) system enhancement that implements a two-pipeline architecture for high-precision medical-legal document processing. The system transforms the existing QME workflow into a deterministic, evidence-driven process that extracts structured data with confidence scoring, validates evidence completeness, and generates legally compliant QME reports with programmatic calculations and comprehensive audit trails.

## Requirements

### Requirement 1: Evidence-First Structured Extraction Pipeline

**User Story:** As a QME examiner, I want the system to extract medical data with deterministic confidence scoring and evidence provenance, so that every fact in the generated report can be traced to its source document with quantified reliability.

#### Acceptance Criteria

1. WHEN processing medical documents THEN the system SHALL extract fields using regex patterns with confidence scores ≥0.8 for critical fields (patient name, case number, injury date)
2. WHEN extraction confidence is below 0.8 THEN the system SHALL flag fields for human review and provide source snippets with page references
3. WHEN multiple extraction methods are used THEN the system SHALL combine regex, NER, and cross-document validation to maximize field coverage
4. WHEN fields are extracted THEN the system SHALL maintain evidence provenance linking each field to source document, page number, and text coordinates
5. WHEN knowledge graph is populated THEN the system SHALL only use validated fields with confidence ≥0.5 and maintain complete audit trails

### Requirement 2: Programmatic Impairment Calculation Engine

**User Story:** As a QME examiner, I want all numeric calculations performed programmatically using AMA Guidelines tables, so that impairment ratings are mathematically accurate and legally defensible without LLM involvement.

#### Acceptance Criteria

1. WHEN calculating impairment ratings THEN the system SHALL use only programmatic methods referencing AMA Guides 5th Edition tables with zero LLM involvement in numeric calculations
2. WHEN ROM measurements are available THEN the system SHALL require minimum 3 measurements per joint and calculate averages using AMA methodology
3. WHEN multiple impairments exist THEN the system SHALL apply Combined Values Chart calculations with step-by-step documentation and table citations
4. WHEN insufficient data exists for calculation THEN the system SHALL explicitly flag missing measurements and recommend specific additional testing
5. WHEN calculations are complete THEN the system SHALL provide complete audit trail with AMA table references, calculation steps, and source data validation

### Requirement 3: Knowledge Graph Complete Initialization and Validation

**User Story:** As a system administrator, I want the knowledge graph to be completely initialized with canonical documents whenever option 2 is selected, so that the system has full medical and legal context for evidence validation and report generation.

#### Acceptance Criteria

1. WHEN option 2 is selected from run script THEN the system SHALL automatically initialize knowledge graph with AMA Guides 5th Edition, QME Study Guide, Sample3.pdf, and all QME reference patterns
2. WHEN knowledge graph initialization occurs THEN the system SHALL validate completeness by verifying node counts ≥1000, relationship counts ≥500, and presence of all required entity types
3. WHEN canonical documents are processed THEN the system SHALL create structured entities for AMA tables, legal requirements, procedural patterns, and quality standards
4. WHEN initialization is complete THEN the system SHALL run validation tests confirming extraction patterns, impairment calculation tables, and legal compliance templates are accessible
5. WHEN knowledge graph is populated THEN the system SHALL provide initialization status report showing processed documents, entity counts, and validation results

### Requirement 4: Two-Pipeline Workflow Integration

**User Story:** As a QME examiner, I want the system to process documents through structured extraction then evidence-driven generation pipelines, so that reports are built only from validated evidence with complete traceability.

#### Acceptance Criteria

1. WHEN documents are uploaded THEN Pipeline 1 SHALL perform structured extraction, confidence scoring, evidence validation, and knowledge graph population with validated fields only
2. WHEN Pipeline 1 completes THEN the system SHALL generate validation report showing accepted fields (confidence ≥0.8), flagged fields (0.5-0.8), and missing critical fields
3. WHEN sufficient evidence exists THEN Pipeline 2 SHALL generate report content using only accepted fields, programmatic calculations, and canonical knowledge graph content
4. WHEN Pipeline 2 completes THEN the system SHALL validate legal compliance including Labor Code 4062.3 declaration, page count attestation, and mandatory signature blocks
5. WHEN workflows complete THEN the system SHALL provide comprehensive audit trail showing evidence sources, calculation methods, validation results, and compliance status

### Requirement 5: Enhanced Rules Engine and Legal Compliance

**User Story:** As a QME examiner, I want the system to enforce legal compliance requirements and quality standards automatically, so that all generated reports meet California workers' compensation law and QME regulatory standards.

#### Acceptance Criteria

1. WHEN generating reports THEN the system SHALL validate mandatory sections including patient demographics, records reviewed, physical examination, diagnosis, impairment rating, and legal attestation
2. WHEN legal compliance is checked THEN the system SHALL ensure Labor Code 4062.3 declaration, accurate page counts with MLPRR billing units, and required physician signature blocks are present
3. WHEN evidence validation occurs THEN the system SHALL apply confidence thresholds (critical fields ≥0.8, standard fields ≥0.5) and flag insufficient evidence for human review
4. WHEN post-generation validation runs THEN the system SHALL verify no placeholder text remains, all calculations are programmatic, and AMA table citations are accurate
5. WHEN compliance validation completes THEN the system SHALL generate detailed compliance report with pass/fail status for each requirement and actionable remediation steps
