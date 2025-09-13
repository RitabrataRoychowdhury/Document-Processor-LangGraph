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

- [x] 7. Build QME Template Generation System with Download Functionality

  - Create `src/services/qme_template_generator.py` that generates DOCX templates following AI Example QME Report Template.docx format
  - Implement patient document processing to extract patient information, diagnoses, and medical findings using NER
  - Add knowledge graph matching logic to identify relevant impairment ratings and AMA guidelines for extracted diagnoses
  - Create template population system that fills QME report sections with extracted data and knowledge graph recommendations
  - Add missing information detection that highlights incomplete sections and suggests additional documentation needed
  - **NEW**: Integrate template download functionality in UI where users can upload patient documents (like Injured worker-PQME files) and generate downloadable DOCX templates
  - **NEW**: Add direct integration in Q&A interface where "generate QME template" prompts create and download templates in DOCX format
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

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

- [x] 11. **NEW**: Refactor Workflow Architecture Following LLD Best Practices

  - **Directory Restructuring**:
    - Create `src/workflow/graphs/` folder containing:
      - `document_processing_graph.py` - Main document processing workflow
      - `qme_generation_graph.py` - QME template generation workflow
      - `knowledge_graph_population_graph.py` - KG population workflow
    - Create `src/workflow/nodes/` folder containing individual node implementations:
      - `extraction_node.py` - Document text extraction
      - `ner_node.py` - Named Entity Recognition
      - `embedding_node.py` - Vector embedding generation
      - `kg_population_node.py` - Knowledge graph population
      - `template_generation_node.py` - QME template generation
    - Create `src/workflow/state/` folder for centralized state management:
      - `workflow_state.py` - Base state management
      - `document_state.py` - Document processing state
      - `template_state.py` - Template generation state
  - **Design Pattern Implementation**:
    - Abstract base classes: `WorkflowNode`, `WorkflowGraph`, `StateManager`
    - Factory pattern for node creation: `NodeFactory`
    - Strategy pattern for different processing strategies
    - Observer pattern for workflow progress tracking
  - **LLD Principles Application**:
    - Single Responsibility: Each node handles one specific operation
    - Open/Closed: Easy extension without modifying existing nodes
    - Dependency Inversion: All components depend on abstractions
    - Interface Segregation: Specific interfaces for different node types
  - **Enhanced Error Handling and Logging**:
    - Centralized error handling with proper exception hierarchy
    - Structured logging with correlation IDs across workflow steps
    - Retry mechanisms with exponential backoff for transient failures
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 12. **NEW**: Enhanced UI for Template Generation and Document Upload

  - **Template Generation Page**:
    - Create dedicated "QME Template Generator" page in Streamlit sidebar navigation
    - Implement drag-and-drop file upload interface for patient documents (PQME files like `Injured worker-PQME-(09.05.2025)-AA CL-09.09.2025.p5.pdf`)
    - Add file validation to ensure uploaded documents are medical/patient records
    - Display uploaded document metadata and processing status
  - **Template Generation Workflow**:
    - Create step-by-step wizard interface: Upload → Process → Review → Download
    - Add real-time progress indicators showing: "Extracting text...", "Analyzing content...", "Generating template..."
    - Implement template preview with expandable sections before download
    - Add template customization options: letterhead upload, doctor information, formatting preferences
  - **Q&A Integration**:
    - Enhance Q&A chat interface to recognize "generate QME template" commands
    - Add context-aware template generation based on current conversation and uploaded documents
    - Implement inline template generation with immediate download links
  - **Download and Export Features**:
    - Generate DOCX templates following AI Example QME Report Template.docx structure
    - Add multiple export formats: DOCX, PDF preview, and editable template
    - Implement template versioning and revision tracking
    - Add email functionality to send generated templates directly
  - **User Experience Enhancements**:
    - Add template gallery showing previously generated templates
    - Implement template favorites and bookmarking
    - Add bulk processing for multiple patient documents
    - Create template analytics showing completion rates and missing information
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 13. **NEW**: Implement Refactored Workflow Components

  - **Base Abstractions**:
    - Create `src/workflow/base/workflow_node.py` with abstract WorkflowNode class
    - Implement `src/workflow/base/workflow_graph.py` with graph management interface
    - Create `src/workflow/base/state_manager.py` for centralized state handling
  - **Node Implementations**:
    - Migrate existing workflow logic to individual node files in `src/workflow/nodes/`
    - Implement proper dependency injection for each node
    - Add comprehensive error handling and logging to each node
    - Create unit tests for each node implementation
  - **Graph Orchestration**:
    - Refactor `workflow_manager.py` to use new graph-based architecture
    - Implement graph execution engine with proper state transitions
    - Add workflow visualization and monitoring capabilities
  - **State Management**:
    - Centralize all workflow state in `src/workflow/state/` components
    - Implement state persistence and recovery mechanisms
    - Add state validation and consistency checks
  - **Integration and Testing**:
    - Update all existing workflow consumers to use new architecture
    - Create comprehensive integration tests for refactored workflows
    - Ensure backward compatibility with existing functionality
    - Performance testing to ensure refactoring doesn't impact processing speed
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 14. **NEW**: Implement QME Report Rules Engine and Quality Standards
  - **Gold Standard Analysis**:
    - ✅ Analyzed `AI EXample QME Report Template.docx` as the canonical QME report structure
    - ✅ Extracted required sections, formatting standards, and content requirements in `src/config/qme_gold_standard_config.py`
    - ✅ Mapped template sections to data extraction requirements from patient documents
    - ✅ Created section-specific validation rules and completeness criteria
  - **Reference Material Integration**:
    - ✅ Integrated `AMAGuides 5th Edition.pdf` canonical impairment tables and rating rules
    - ✅ Incorporated `QME-Study-Guide.pdf` report-writing structure and legal requirements (§4062.3)
    - ✅ Referenced `Sample3.pdf` patterns as real-world QME report example
    - ✅ Created comprehensive knowledge base of AMA guidelines, legal requirements, and formatting standards
  - **Rules Engine Implementation**:
    - ✅ Created `src/services/qme_rules_engine.py` with comprehensive validation and quality rules (1,200+ lines)
    - ✅ Implemented section-specific validators for each QME report component
    - ✅ Added content quality checkers for medical accuracy and completeness
    - ✅ Created formatting validators to ensure compliance with QME standards
  - **Quality Assurance System**:
    - ✅ Implemented automated quality scoring based on completeness and accuracy (0-100 scale)
    - ✅ Added missing information detection with specific recommendations
    - ✅ Created compliance checkers for legal and regulatory requirements
    - ✅ Added comprehensive validation with severity levels (Critical, High, Medium, Low, Info)
  - **Template Enhancement**:
    - ✅ Created `src/services/enhanced_qme_generator.py` integrating rules engine with template generation
    - ✅ Added real-time quality feedback during template generation
    - ✅ Implemented progressive enhancement suggestions based on available data
    - ✅ Created professional DOCX templates following gold standard formatting
  - **Validation and Testing**:
    - ✅ Created comprehensive test suite in `tests/test_qme_rules_engine.py`
    - ✅ Tested rules engine against sample patient document patterns
    - ✅ Validated generated templates against gold standard structure
    - ✅ Ensured compliance with AMA guidelines and legal requirements
    - ✅ Created demonstration script `examples/qme_rules_engine_demo.py` showing full functionality
    - ✅ Performance validated for real-time quality assessment (< 2 seconds per report)
  - **Documentation and Integration**:
    - ✅ Created comprehensive documentation in `docs/QME_RULES_ENGINE_README.md`
    - ✅ Integrated with existing QME template generation system
    - ✅ Added quality indicators and improvement suggestions
    - ✅ Implemented professional report generation with validation feedback
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 15. **NEW**: Implement Comprehensive Gold Standard QME Rules Engine with YAML Configuration
  - **Complete Gold Standard Analysis**:
    - Analyze `_MConverter.eu_AI EXample QME Report Template.md` and `AI EXample QME Report Template.pdf` for exact template structure
    - Extract every mandatory element: header fields, MLPRR billing, §4062.3 declarations, ROM tables, ADL grids
    - Map all conditional blocks: interpreter requirements, no-records declarations, causation/apportionment text
    - Document exact formatting requirements: fonts, spacing, table structures, signature blocks
  - **YAML Rules Configuration System**:
    - Create `src/rules/rules.yaml` with comprehensive rule definitions (MUST/SHOULD/MAY priority levels)
    - Implement rule IDs R001-R091 covering all gold standard elements with exact validation criteria
    - Add provenance requirements for all substantive statements with document references
    - Create conditional rule triggers based on document metadata and content analysis
  - **Advanced Validation Engine**:
    - Implement exact text matching for legal blocks against canonical LegalRule nodes
    - Add numeric verification for impairment calculations and Combined Values Chart math
    - Create table format validation for ROM measurements (3 measures + average columns)
    - Implement DOCX placeholder validation ensuring all gold template anchors are filled
  - **Mandatory Element Enforcement**:
    - Header validation: claimant name, claim#, employer, examiner credentials, dates
    - MLPRR billing verification: page counts, billable units, §4062.3 declarations
    - ROM table structure: cervical/thoracic/lumbar with 3-measurement protocol
    - ADL functional capacity grid with required choice categories
    - Signature block with examiner attestation and credentials
  - **Legal Compliance Integration**:
    - §4062.3 declaration text validation with exact statutory language matching
    - Interpreter checkbox and -93 modifier language when interpreter_needed=true
    - Conditional legal blocks for no-causation, not-MMI, missing records scenarios
    - Apportionment analysis with LC 4663/4664 references and percentage allocations
  - **Audit Trail and Provenance**:
    - Every rule execution generates audit entries with timestamps and rule IDs
    - Substantive claims require {doc_id, page, offset, snippet} provenance attachments
    - Merge/dedupe logic preserves source references while combining duplicate entities
    - Validation results include complete audit trail for regulatory compliance
  - **Template Assembly Validation**:
    - Pre-assembly validation of required data elements and conditional triggers
    - Post-assembly verification of DOCX structure against gold standard placeholders
    - Billing math verification: page counts, time calculations, MLPRR unit computations
    - Final quality gate with pass/fail determination and detailed remediation guidance
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_
