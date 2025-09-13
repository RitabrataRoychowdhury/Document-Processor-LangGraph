# Implementation Plan

- [x] 1. Implement Factory and Strategy Patterns for Document Processing

  - Create `src/factories/processor_factory.py` with ProcessorFactory class supporting PDF and DOCX processors
  - Refactor `src/services/file_handler.py` to use ProcessorFactory instead of direct processor instantiation
  - Implement EmbeddingStrategy interface with LocalEmbeddingStrategy (SentenceTransformers) and OpenAIEmbeddingStrategy classes
  - Create QAStrategy interface with HybridQAStrategy combining vector search and LLM generation
  - Add dependency injection configuration to inject strategies into qa_engine.py
  - _Requirements: 1.1, 1.2, 9.1, 9.2, 9.4_

- [x] 2. Implement Repository Pattern and Database Schema for Knowledge Graph

  - Create `src/repositories/document_repository.py` and `src/repositories/patient_repository.py` with abstract interfaces
  - Implement SQLiteDocumentRepository and SQLitePatientRepository as concrete implementations wrapping existing document_storage.py
  - Design and implement SQLite schema for knowledge graph nodes (Document, Section, Patient, Claim, Diagnosis, Finding, ImagingStudy, ImpairmentRating)
  - Create knowledge graph relationship tables with foreign keys and relationship types
  - Add database migration scripts to upgrade existing SQLite database to new schema
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 10.1_

- [x] 3. Implement Command Pattern Workflow with Retry Logic

  - Create `src/commands/` directory with base Command interface and concrete implementations: IngestCommand, NERCommand, KGPopulateCommand
  - Refactor `src/workflow/workflow_manager.py` to use command pattern instead of direct method calls
  - Implement retry decorator with exponential backoff for handling API failures and temporary errors
  - Add console logging for command execution, retries, and failures (no external logging services)
  - Create CommandResult class to standardize command return values and error handling
  - _Requirements: 1.4, 1.5, 6.3, 6.5_

- [x] 4. Build Knowledge Graph Ingestion Pipeline

  - Create `src/services/ingestion_pipeline.py` that orchestrates: text extraction → section segmentation → NER → embedding → KG population
  - Implement section segmentation logic to identify medical document sections (History, Examination, Diagnosis, etc.)
  - Add Named Entity Recognition using spaCy or similar library to extract Patient, Diagnosis, Finding, ImpairmentRating entities
  - Integrate embedding generation using LocalEmbeddingStrategy (SentenceTransformers) with Chroma or in-memory vector store
  - Create KnowledgeGraphService to populate SQLite tables with extracted entities and relationships
  - _Requirements: 2.4, 2.5, 6.1, 6.2, 6.4_

- [x] 5. Initialize Knowledge Base with Canonical Medical Documents

  - Create `src/services/knowledge_base_initializer.py` to automatically process the three canonical documents on system startup
  - Implement document processing for AMAGuides 5th Edition.pdf to extract impairment tables, rules, and medical guidelines
  - Process QME-Study-Guide.pdf to extract report-writing structure, legal requirements (§4062.3), and procedural guidelines
  - Ingest Sample3.pdf as reference QME report to extract sections, findings, diagnoses, and report structure patterns
  - Create specialized extractors for each document type to identify key medical concepts, AMA tables, and legal references
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6. Implement Hybrid Q&A System Over Knowledge Graph

  - Enhance `src/services/qa_engine.py` to use HybridQAStrategy combining vector similarity search and graph traversal
  - Implement context retrieval that searches both vector embeddings and follows knowledge graph relationships
  - Add source citation system that includes page numbers, document references, and provenance information
  - Create graph traversal logic to find connected entities (diagnosis → impairment rating → AMA table)
  - Integrate with Gemini API using configurable QA strategy pattern for answer generation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Build QME Template Generation System

  - Create `src/services/qme_template_generator.py` that generates DOCX templates following AI Example QME Report Template.docx format
  - Implement patient document processing to extract patient information, diagnoses, and medical findings using NER
  - Add knowledge graph matching logic to identify relevant impairment ratings and AMA guidelines for extracted diagnoses
  - Create template population system that fills QME report sections with extracted data and knowledge graph recommendations
  - Add missing information detection that highlights incomplete sections and suggests additional documentation needed
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Create Comprehensive Test Suite

  - Write unit tests for ProcessorFactory, EmbeddingStrategy, and QAStrategy implementations in `tests/test_factories.py` and `tests/test_strategies.py`
  - Create knowledge graph tests in `tests/test_knowledge_graph.py` to verify node creation, relationship establishment, and data integrity
  - Implement end-to-end integration test: ingest Sample3.pdf → verify KG nodes created → execute QA query → validate expected response with sources
  - Add QME template generation tests to verify output format matches AI Example QME Report Template.docx structure and contains expected content
  - Create repository pattern tests to ensure SQLite operations work correctly with new schema
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9. Maintain Backward Compatibility and Migration

  - Create data migration scripts in `scripts/migrate_existing_data.py` to convert existing processed documents to new knowledge graph schema
  - Update Streamlit web interface in `src/ui/main_app.py` to work with new repository pattern while maintaining same user experience
  - Ensure existing document upload, processing, and Q&A functionality continues to work with enhanced knowledge graph backend
  - Add configuration management in `src/config/app_config.py` using environment variables for API keys and provider selection
  - Test that previously processed documents can be accessed and queried through the new system
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 10. Deploy System with Health Checks and Performance Monitoring
  - Create `src/services/health_checker.py` with database connectivity checks and knowledge graph validation
  - Implement automatic knowledge base initialization on system startup using KnowledgeBaseInitializer
  - Add performance monitoring to track document processing times and ensure 50-page PDF processes within 30 seconds
  - Create deployment scripts that set up SQLite database, initialize canonical documents, and start the Streamlit interface
  - Add environment configuration validation to ensure required API keys and settings are properly configured
  - _Requirements: 10.2, 10.3, 10.4, 10.5_
