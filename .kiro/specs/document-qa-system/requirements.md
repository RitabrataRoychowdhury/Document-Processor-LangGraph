# Requirements Document

## Introduction

This feature refactors the existing document Q&A system to implement a knowledge graph-based architecture with improved design patterns, better extensibility, and enhanced QME (Qualified Medical Evaluator) report generation capabilities. The system will process medical documents to build a comprehensive knowledge graph, enable intelligent Q&A over the knowledge base, and generate QME templates based on processed patient documents. The refactoring focuses on implementing clean architecture patterns while maintaining full functionality.

## Requirements

### Requirement 1

**User Story:** As a developer, I want the system to use proper design patterns and clean architecture, so that the codebase is maintainable, testable, and extensible.

#### Acceptance Criteria

1. WHEN the system is refactored THEN the system SHALL implement Factory Pattern for document processors (PDF, DOCX) with a centralized processor_factory.py
2. WHEN processing documents THEN the system SHALL use Strategy Pattern for embedding generation (OpenAI/Local) and QA strategies (retrieval + LLM)
3. WHEN accessing data THEN the system SHALL use Repository Pattern with DocumentRepository and PatientRepository wrapping SQLite storage
4. WHEN executing workflows THEN the system SHALL use Command Pattern with IngestCommand, NERCommand, and KGPopulateCommand in workflow_manager.py
5. IF any component fails THEN the system SHALL use proper error handling with retry decorators and console logging

### Requirement 2

**User Story:** As a medical professional, I want the system to build a comprehensive knowledge graph from medical documents, so that I can query relationships between diagnoses, treatments, and impairment ratings.

#### Acceptance Criteria

1. WHEN documents are processed THEN the system SHALL create knowledge graph nodes for Document, Section, Patient, Claim, Diagnosis, Finding, ImagingStudy, and ImpairmentRating
2. WHEN extracting entities THEN the system SHALL establish relationships: Document→Section, Section→Finding/Diagnosis, Diagnosis→ImpairmentRating, Diagnosis→Claim
3. WHEN storing knowledge THEN the system SHALL maintain provenance with page numbers, source_doc_id, and text_snippets for all extracted information
4. WHEN building the graph THEN the system SHALL use embeddings (Chroma or in-memory vector store) for semantic search capabilities
5. IF duplicate entities are found THEN the system SHALL merge them while preserving all source references

### Requirement 3

**User Story:** As a system user, I want to ingest a knowledge base from canonical medical documents, so that the system has foundational medical knowledge for QME report generation.

#### Acceptance Criteria

1. WHEN the system initializes THEN the system SHALL automatically ingest AMAGuides 5th Edition.pdf to extract impairment tables and rules
2. WHEN building knowledge base THEN the system SHALL process QME-Study-Guide.pdf to extract report-writing structure and legal requirements
3. WHEN creating reference data THEN the system SHALL ingest Sample3.pdf as a real-world QME report example for style and structure
4. WHEN extracting knowledge THEN the system SHALL create nodes for diagnoses, impairment ratings, legal rules (§4062.3), report sections, and AMA tables
5. IF knowledge base ingestion fails THEN the system SHALL log errors and continue with available knowledge

### Requirement 4

**User Story:** As a medical professional, I want to upload patient documents and have the system generate QME templates, so that I can create comprehensive medical evaluations efficiently.

#### Acceptance Criteria

1. WHEN a patient document is uploaded THEN the system SHALL extract patient information, diagnoses, and medical findings using NER
2. WHEN processing patient data THEN the system SHALL match findings against the knowledge graph to identify relevant impairment ratings
3. WHEN generating templates THEN the system SHALL create QME reports similar to the AI Example QME Report Template.docx format
4. WHEN populating templates THEN the system SHALL use knowledge graph relationships to suggest relevant AMA guidelines and legal requirements
5. IF insufficient information is available THEN the system SHALL highlight missing sections and suggest additional documentation needed

### Requirement 5

**User Story:** As a user, I want to perform intelligent Q&A over the knowledge graph, so that I can quickly find specific medical information and relationships.

#### Acceptance Criteria

1. WHEN asking questions THEN the system SHALL use hybrid search combining vector similarity and graph traversal
2. WHEN retrieving answers THEN the system SHALL provide responses with source citations including page numbers and document references
3. WHEN querying relationships THEN the system SHALL traverse the knowledge graph to find connected entities (e.g., diagnosis → impairment rating → AMA table)
4. WHEN generating answers THEN the system SHALL use the configured LLM strategy (Gemini by default) with retrieved context
5. IF no relevant information is found THEN the system SHALL suggest related topics or broader search terms

### Requirement 6

**User Story:** As a system administrator, I want the system to have a robust ingestion pipeline, so that documents are processed consistently and reliably.

#### Acceptance Criteria

1. WHEN documents are uploaded to /data folder THEN the system SHALL automatically detect and process PDF/DOCX files
2. WHEN processing documents THEN the system SHALL execute: OCR/text extraction → section segmentation → NER → embedding → KG population
3. WHEN running workflows THEN the system SHALL support retry mechanisms with exponential backoff for failed operations
4. WHEN processing completes THEN the system SHALL update document status and make content available for Q&A
5. IF processing fails THEN the system SHALL log detailed error information and allow manual retry

### Requirement 7

**User Story:** As a quality assurance tester, I want comprehensive testing coverage, so that the system reliability is ensured.

#### Acceptance Criteria

1. WHEN testing processors THEN the system SHALL have unit tests for processor factory and strategy patterns
2. WHEN testing knowledge graph THEN the system SHALL have tests verifying node creation and relationship establishment
3. WHEN testing end-to-end THEN the system SHALL have integration test: ingest Sample3.pdf → KG nodes created → QA query returns expected snippet
4. WHEN testing QME generation THEN the system SHALL verify template generation matches expected format and content
5. IF any test fails THEN the system SHALL provide clear error messages indicating the specific failure point

### Requirement 8

**User Story:** As a system user, I want the system to maintain backward compatibility, so that existing functionality continues to work during and after refactoring.

#### Acceptance Criteria

1. WHEN refactoring is complete THEN the system SHALL maintain all existing document upload and processing capabilities
2. WHEN using the web interface THEN the system SHALL provide the same user experience with enhanced functionality
3. WHEN accessing stored documents THEN the system SHALL continue to work with previously processed documents
4. WHEN performing Q&A THEN the system SHALL provide improved answers while maintaining the same interface
5. IF legacy data exists THEN the system SHALL migrate it to the new knowledge graph structure without data loss

### Requirement 9

**User Story:** As a developer, I want modular LLM provider support, so that the system can work with different AI models without code changes.

#### Acceptance Criteria

1. WHEN configuring the system THEN the system SHALL support pluggable embedding strategies (OpenAI, Local models)
2. WHEN generating answers THEN the system SHALL support configurable QA strategies with different retrieval and LLM combinations
3. WHEN processing documents THEN the system SHALL use dependency injection to select appropriate processors and strategies
4. WHEN switching providers THEN the system SHALL maintain consistent interfaces across different LLM implementations
5. IF a provider is unavailable THEN the system SHALL gracefully fallback to alternative providers or inform the user

### Requirement 10

**User Story:** As a system operator, I want simplified deployment and configuration, so that the system can be easily set up and maintained.

#### Acceptance Criteria

1. WHEN deploying the system THEN the system SHALL use SQLite as the only database backend for simplicity
2. WHEN configuring the system THEN the system SHALL use environment variables for API keys and configuration settings
3. WHEN starting the system THEN the system SHALL automatically initialize the knowledge base from the three canonical documents
4. WHEN running in production THEN the system SHALL provide health checks and basic monitoring capabilities
5. IF configuration is missing THEN the system SHALL provide clear error messages with setup instructions