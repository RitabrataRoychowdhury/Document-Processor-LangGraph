# Implementation Plan

- [x] 1. Enhance Structured Extraction Pipeline with Confidence Scoring

  - Modify `src/services/qme_field_extractor.py` to implement regex pattern extraction with confidence scoring system
  - Update `data/qme_references/legal_patterns.json` with comprehensive extraction patterns for case numbers, patient names, dates, body parts, ROM measurements, and AMA table references
  - Create `src/services/structured_extractor.py` to orchestrate regex + NER extraction with evidence snippet collection and source coordinate tracking
  - Implement confidence calculation algorithm combining regex match confidence (0.6), NER probability (0.3), and cross-document consistency (0.1)
  - Add evidence provenance tracking linking each extracted field to source document, page number, and text coordinates
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Implement Evidence Validation Gateway and Threshold Management

  - Enhance `src/services/qme_field_validator.py` to implement evidence-first validation with configurable confidence thresholds
  - Create validation report generation showing accepted fields (≥0.8), flagged fields (0.5-0.8), and missing critical fields (<0.5)
  - Implement human-in-the-loop review queue for flagged fields with evidence snippet display and source context
  - Add cross-validation logic for consistency checking across multiple documents and entity disambiguation
  - Create validation status tracking and audit trail generation for complete evidence traceability
  - _Requirements: 1.2, 1.5, 5.3_

- [x] 3. Create Programmatic Impairment Calculation Engine

  - Create `src/services/impairment_calculator.py` implementing AMA Guides 5th Edition table-based calculations with zero LLM involvement
  - Load and structure AMA tables from `data/ama_guidelines/tables.json` for programmatic lookup and calculation
  - Implement ROM measurement averaging (minimum 3 measurements), impairment percentage calculation, and Combined Values Chart application
  - Add step-by-step calculation documentation with AMA table citations and source data validation
  - Create calculation validation system ensuring correct table usage, proper averaging, and valid percentage ranges
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. Enhance Knowledge Graph Complete Initialization System

  - Modify `src/services/knowledge_base_initializer.py` to ensure complete initialization when run script option 2 is selected
  - Add canonical document processing for AMA Guides 5th Edition, QME Study Guide, Sample3.pdf, and all QME reference patterns
  - Implement initialization validation requiring node counts ≥1000, relationship counts ≥500, and all required entity types present
  - Create structured entity creation for AMA tables, legal requirements, procedural patterns, and quality standards
  - Add initialization status reporting showing processed documents, entity counts, validation results, and system readiness confirmation
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Implement Two-Pipeline Workflow Integration

  - Create `src/workflow/evidence_first_workflow_manager.py` orchestrating Pipeline 1 (extraction/validation) and Pipeline 2 (generation/compliance)
  - Implement Pipeline 1 flow: document processing → structured extraction → confidence scoring → evidence validation → knowledge graph population
  - Implement Pipeline 2 flow: validated evidence → programmatic calculations → evidence-driven content generation → compliance validation
  - Add workflow state management tracking pipeline progress, validation results, and evidence completeness status
  - Create comprehensive audit trail generation showing evidence sources, calculation methods, validation results, and compliance status
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Enhance Evidence-Driven Content Generation

  - Modify `src/services/intelligent_content_generator.py` to implement evidence-constrained narrative generation using only validated fields
  - Create `src/services/evidence_rag_service.py` for canonical content retrieval from AMA Guides and QME Study Guide knowledge graph
  - Implement content generation with evidence snippet constraints, source citation management, and provenance tracking
  - Add narrative generation for QME sections (history, examination, diagnosis, impairment) using only accepted evidence fields
  - Create content validation ensuring no placeholder text remains and all statements have evidence backing with source references
  - _Requirements: 4.3, 5.4_

- [x] 7. Implement Enhanced Rules Engine and Legal Compliance Validation

  - Update `src/rules/rules.yaml` with evidence-first validation rules, confidence thresholds, and legal compliance requirements
  - Enhance `src/services/qme_rules_engine.py` to validate mandatory sections, Labor Code 4062.3 declaration, and signature blocks
  - Implement post-generation validation checking for placeholder text, programmatic calculations, and AMA table citation accuracy
  - Add legal compliance reporting with pass/fail status for each requirement and actionable remediation steps
  - Create compliance audit trail linking each requirement to evidence sources and validation results
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [x] 8. Update Professional Template Assembly with Evidence Integration

  - Enhance `src/services/professional_template_assembler.py` to integrate with evidence validation results and programmatic calculations
  - Modify template population to use only accepted fields from validation report and programmatic calculation results
  - Add evidence source citation insertion for all populated fields with page references and confidence scores
  - Implement template completeness validation ensuring all mandatory sections are populated with substantive evidence-based content
  - Create final quality assurance checking for professional formatting, legal compliance, and evidence traceability
  - _Requirements: 4.4, 5.4_

- [x] 9. Enhance Run Script Option 2 with Complete Knowledge Graph Initialization

  - Modify `scripts/run.sh` option 2 to trigger complete knowledge graph initialization with validation and status reporting
  - Add pre-initialization checks for canonical document availability and system readiness
  - Implement initialization progress tracking with real-time status updates and completion percentage reporting
  - Add post-initialization validation tests confirming extraction patterns, calculation tables, and legal templates are accessible
  - Create initialization failure handling with detailed error reporting and remediation recommendations
  - _Requirements: 3.1, 3.4, 3.5_

- [x] 10. Create Comprehensive Testing and Validation Framework
  - Create `tests/test_evidence_first_pipeline.py` for end-to-end pipeline testing using Sample3.pdf and PQME documents with known expected values
  - Implement confidence scoring validation tests ensuring ≥95% precision for critical fields and ≥90% overall field coverage
  - Add programmatic calculation testing validating AMA table accuracy, ROM calculations, and Combined Values Chart applications
  - Create knowledge graph initialization testing confirming canonical document processing and entity/relationship counts
  - Implement integration tests for complete workflow execution from document upload through final QME report generation with audit trail validation
  - _Requirements: 1.1, 2.5, 3.2, 4.5, 5.5_
