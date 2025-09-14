# Requirements Document

## Introduction

This specification defines an enhanced QME (Qualified Medical Evaluator) template generation system that produces gold-standard compliant medical reports using knowledge graph-driven reasoning, advanced rules engines, and comprehensive medical/legal context analysis. The system will process patient medical records (PQME files) and generate complete, professionally formatted QME reports that match the quality and structure of the provided gold-standard template, incorporating AMA Guides 5th Edition impairment ratings and legal compliance requirements.

## Requirements

### Requirement 1: Knowledge Graph-Driven Document Processing

**User Story:** As a QME examiner, I want the system to intelligently extract and connect medical information from patient documents using a knowledge graph, so that the generated reports contain comprehensive, contextually relevant medical findings with proper relationships between diagnoses, treatments, and impairments.

#### Acceptance Criteria

1. WHEN patient documents (PQME PDFs) are uploaded THEN the system SHALL extract entities including Patient, Diagnosis, ImagingStudy, Findings, Claim, Treatment, and ImpairmentRating nodes
2. WHEN entities are extracted THEN the system SHALL establish relationships between connected medical concepts (diagnosis → impairment rating → AMA table)
3. WHEN processing medical records THEN the system SHALL perform proper document chunking with semantic boundaries preserving medical context
4. WHEN building the knowledge graph THEN the system SHALL maintain provenance information linking each fact to its source document, page, and location
5. WHEN multiple documents reference the same entity THEN the system SHALL merge and deduplicate entities while preserving all source references

### Requirement 2: AMA Guidelines Integration and Impairment Rating

**User Story:** As a QME examiner, I want the system to automatically apply AMA Guides 5th Edition rules and calculations, so that impairment ratings are accurate, properly documented, and include the correct table references and calculation steps.

#### Acceptance Criteria

1. WHEN generating impairment ratings THEN the system SHALL reference the AMA Guides 5th Edition PDF as the canonical source for impairment tables and calculation methods
2. WHEN calculating impairments THEN the system SHALL select the appropriate AMA chapter and method (Table vs ROM vs DRE) based on the diagnosis
3. WHEN multiple impairments exist THEN the system SHALL apply the Combined Values Chart correctly with step-by-step calculation documentation
4. WHEN impairment calculations are performed THEN the system SHALL include specific table citations and page references from the AMA Guides
5. WHEN insufficient data exists for rating THEN the system SHALL explicitly flag missing measurements and recommend specific additional testing

### Requirement 3: Legal Compliance and Regulatory Requirements

**User Story:** As a QME examiner, I want the system to ensure all generated reports meet legal and regulatory requirements, so that reports are compliant with California workers' compensation law and QME standards.

#### Acceptance Criteria

1. WHEN generating any QME report THEN the system SHALL include the mandatory §4062.3 declaration with exact statutory language
2. WHEN calculating billing THEN the system SHALL include accurate page counts, MLPRR billing units, and required attestations
3. WHEN an interpreter was used THEN the system SHALL include interpreter checkbox and -93 modifier language
4. WHEN no medical records are available THEN the system SHALL insert the appropriate "no records available" legal block
5. WHEN apportionment is required THEN the system SHALL include LC 4663/4664 references and percentage allocations with legal reasoning

### Requirement 4: Gold Standard Template Compliance

**User Story:** As a QME examiner, I want generated reports to exactly match the structure and quality of the gold standard template, so that all reports maintain professional consistency and include all required sections and elements.

#### Acceptance Criteria

1. WHEN generating a report THEN the system SHALL follow the exact section order and headings from the AI Example QME Report Template
2. WHEN populating sections THEN the system SHALL ensure all mandatory elements are present including header fields, ROM tables, ADL grids, and signature blocks
3. WHEN formatting the report THEN the system SHALL maintain professional medical language and proper clinical terminology
4. WHEN tables are required THEN the system SHALL include properly formatted ROM measurements (3 measurements + average), ADL functional capacity grids, and impairment calculation tables
5. WHEN the report is complete THEN the system SHALL validate that no placeholder text remains and all sections contain substantive content

### Requirement 5: Intelligent Content Generation and Reasoning

**User Story:** As a QME examiner, I want the system to generate coherent, medically accurate narrative content based on extracted facts and medical knowledge, so that reports read naturally and demonstrate proper medical reasoning rather than just filling templates with data.

#### Acceptance Criteria

1. WHEN generating the history section THEN the system SHALL create a coherent narrative of injury mechanism, treatment course, and current complaints using knowledge graph timeline data
2. WHEN writing examination findings THEN the system SHALL generate detailed descriptions including general appearance, joint inspection, palpation, ROM measurements, and neurological tests
3. WHEN discussing causation THEN the system SHALL analyze industrial causation versus pre-existing conditions with medical reasoning
4. WHEN recommending future care THEN the system SHALL suggest appropriate treatments (PT, injections, surgery) based on diagnosis and current status
5. WHEN generating any content THEN the system SHALL include proper medical citations and source references for all substantive statements
