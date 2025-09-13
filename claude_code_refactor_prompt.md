# Document Management System - Complete Architecture Refactoring

## Context
You are refactoring a document processing system that handles medical documents, generates QME templates, builds knowledge graphs, and provides Q&A capabilities. The system currently uses LangGraph with Gemini but needs to be modular to support multiple LLM providers (Claude, OpenAI, local models).

## Current Structure Analysis
The existing codebase has basic layered architecture but lacks proper separation of concerns, design patterns, and modularity. It mixes UI, services, and storage concerns without clear boundaries.

## Architecture Requirements

### Design Patterns to Implement
1. **Domain-Driven Design (DDD)** with clear bounded contexts
2. **Hexagonal Architecture** (Ports & Adapters)
3. **Event-Driven Architecture** for decoupled components
4. **Strategy Pattern** for different processing approaches
5. **Factory Pattern** for object creation
6. **Builder Pattern** for complex object construction
7. **Chain of Responsibility** for processing pipelines
8. **Observer Pattern** for event handling
9. **Command Pattern** for operation encapsulation

### Target Folder Structure

Create the following complete folder structure:

```
src/
├── domain/                           # Domain Layer (Pure Business Logic)
│   ├── __init__.py
│   ├── entities/                     # Domain Entities
│   │   ├── __init__.py
│   │   ├── document.py              # Document entity with business rules
│   │   ├── qme_template.py          # QME template entity
│   │   ├── patient_report.py        # Patient report entity
│   │   ├── knowledge_node.py        # Knowledge graph node entity
│   │   ├── knowledge_edge.py        # Knowledge graph edge entity
│   │   └── qa_session.py            # Q&A session entity
│   │
│   ├── value_objects/               # Immutable domain objects
│   │   ├── __init__.py
│   │   ├── document_metadata.py     # Document metadata value object
│   │   ├── medical_codes.py         # Medical coding value objects
│   │   ├── template_fields.py       # Template field definitions
│   │   ├── extraction_results.py    # Entity extraction results
│   │   └── processing_status.py     # Processing status value object
│   │
│   ├── repositories/                # Repository interfaces (ports)
│   │   ├── __init__.py
│   │   ├── document_repository.py   # Document repository interface
│   │   ├── template_repository.py   # Template repository interface
│   │   ├── knowledge_graph_repository.py # Knowledge graph repository interface
│   │   ├── qa_session_repository.py # Q&A session repository interface
│   │   └── file_storage_repository.py # File storage repository interface
│   │
│   ├── services/                    # Domain services (business logic)
│   │   ├── __init__.py
│   │   ├── qme_generation_service.py # QME template generation logic
│   │   ├── knowledge_extraction_service.py # Knowledge extraction logic
│   │   ├── document_validation_service.py # Document validation logic
│   │   ├── template_validation_service.py # Template validation logic
│   │   └── medical_coding_service.py # Medical coding business logic
│   │
│   └── events/                      # Domain events
│       ├── __init__.py
│       ├── document_processed.py    # Document processed event
│       ├── template_generated.py    # Template generated event
│       ├── knowledge_updated.py     # Knowledge graph updated event
│       ├── qa_completed.py          # Q&A completed event
│       └── error_occurred.py        # Error occurred event
│
├── application/                     # Application Layer (Use Cases)
│   ├── __init__.py
│   ├── commands/                    # Command handlers (CQRS)
│   │   ├── __init__.py
│   │   ├── base_command.py          # Base command interface
│   │   ├── process_document_command.py # Process document use case
│   │   ├── generate_qme_command.py  # Generate QME template use case
│   │   ├── build_knowledge_graph_command.py # Build knowledge graph use case
│   │   ├── ask_question_command.py  # Ask question use case
│   │   └── update_template_command.py # Update template use case
│   │
│   ├── queries/                     # Query handlers (CQRS)
│   │   ├── __init__.py
│   │   ├── base_query.py            # Base query interface
│   │   ├── get_document_query.py    # Get document query
│   │   ├── search_documents_query.py # Search documents query
│   │   ├── get_template_query.py    # Get template query
│   │   ├── search_knowledge_query.py # Search knowledge graph query
│   │   └── get_qa_history_query.py  # Get Q&A history query
│   │
│   ├── dto/                         # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── document_dto.py          # Document data transfer objects
│   │   ├── qme_request_dto.py       # QME generation request DTO
│   │   ├── qme_response_dto.py      # QME generation response DTO
│   │   ├── qa_request_dto.py        # Q&A request DTO
│   │   ├── qa_response_dto.py       # Q&A response DTO
│   │   └── knowledge_graph_dto.py   # Knowledge graph DTOs
│   │
│   ├── orchestrators/               # Workflow orchestration
│   │   ├── __init__.py
│   │   ├── base_orchestrator.py     # Base orchestrator class
│   │   ├── document_processing_orchestrator.py # Document processing workflow
│   │   ├── qme_generation_orchestrator.py # QME generation workflow
│   │   ├── knowledge_graph_orchestrator.py # Knowledge graph construction workflow
│   │   └── qa_orchestrator.py       # Q&A processing workflow
│   │
│   └── interfaces/                  # Application service interfaces
│       ├── __init__.py
│       ├── document_processing_service.py # Document processing service interface
│       ├── qme_service.py           # QME service interface
│       ├── knowledge_service.py     # Knowledge service interface
│       ├── qa_service.py            # Q&A service interface
│       └── notification_service.py  # Notification service interface
│
├── infrastructure/                  # Infrastructure Layer (Adapters)
│   ├── __init__.py
│   ├── adapters/                    # External system adapters
│   │   ├── __init__.py
│   │   ├── storage/                 # Storage adapters
│   │   │   ├── __init__.py
│   │   │   ├── file_storage_adapter.py # File system storage adapter
│   │   │   ├── cloud_storage_adapter.py # Cloud storage adapter
│   │   │   ├── vector_db_adapter.py # Vector database adapter
│   │   │   ├── graph_db_adapter.py  # Graph database adapter
│   │   │   └── sql_db_adapter.py    # SQL database adapter
│   │   │
│   │   ├── parsers/                 # Document parser adapters
│   │   │   ├── __init__.py
│   │   │   ├── base_parser.py       # Base parser interface
│   │   │   ├── pdf_parser_adapter.py # PDF parser adapter
│   │   │   ├── docx_parser_adapter.py # DOCX parser adapter
│   │   │   ├── txt_parser_adapter.py # Text parser adapter
│   │   │   └── ocr_adapter.py       # OCR adapter
│   │   │
│   │   └── external_services/       # External service adapters
│   │       ├── __init__.py
│   │       ├── ama_guidelines_client.py # AMA guidelines API client
│   │       ├── medical_coding_client.py # Medical coding API client
│   │       └── notification_client.py # Notification service client
│   │
│   ├── factories/                   # Concrete factories
│   │   ├── __init__.py
│   │   ├── document_processor_factory.py # Document processor factory
│   │   ├── template_generator_factory.py # Template generator factory
│   │   ├── storage_factory.py       # Storage factory
│   │   ├── parser_factory.py        # Parser factory
│   │   └── llm_provider_factory.py  # LLM provider factory
│   │
│   ├── strategies/                  # Strategy implementations
│   │   ├── __init__.py
│   │   ├── processing_strategies/   # Document processing strategies
│   │   │   ├── __init__.py
│   │   │   ├── base_processing_strategy.py # Base processing strategy
│   │   │   ├── pdf_processing_strategy.py # PDF processing strategy
│   │   │   ├── docx_processing_strategy.py # DOCX processing strategy
│   │   │   └── multimodal_processing_strategy.py # Multimodal processing
│   │   │
│   │   ├── generation_strategies/   # Template generation strategies
│   │   │   ├── __init__.py
│   │   │   ├── base_generation_strategy.py # Base generation strategy
│   │   │   ├── orthopedic_qme_strategy.py # Orthopedic QME strategy
│   │   │   ├── neurological_qme_strategy.py # Neurological QME strategy
│   │   │   └── general_qme_strategy.py # General QME strategy
│   │   │
│   │   └── retrieval_strategies/    # Information retrieval strategies
│   │       ├── __init__.py
│   │       ├── base_retrieval_strategy.py # Base retrieval strategy
│   │       ├── vector_search_strategy.py # Vector search strategy
│   │       ├── graph_search_strategy.py # Graph search strategy
│   │       └── hybrid_search_strategy.py # Hybrid search strategy
│   │
│   ├── repositories/                # Repository implementations
│   │   ├── __init__.py
│   │   ├── sql_document_repository.py # SQL document repository
│   │   ├── nosql_document_repository.py # NoSQL document repository
│   │   ├── file_template_repository.py # File-based template repository
│   │   ├── graph_knowledge_repository.py # Graph-based knowledge repository
│   │   └── memory_qa_repository.py  # In-memory Q&A repository
│   │
│   └── config/                      # Configuration management
│       ├── __init__.py
│       ├── database_config.py       # Database configuration
│       ├── storage_config.py        # Storage configuration
│       ├── parser_config.py         # Parser configuration
│       └── external_service_config.py # External service configuration
│
├── langgraph/                       # LangGraph Module (Modular AI Workflows)
│   ├── __init__.py
│   ├── state/                       # Shared State Management
│   │   ├── __init__.py
│   │   ├── base_state.py           # Base state classes and enums
│   │   ├── document_state.py       # Document processing state
│   │   ├── qme_state.py           # QME generation state
│   │   ├── qa_state.py            # Q&A session state
│   │   ├── knowledge_graph_state.py # Knowledge graph construction state
│   │   ├── state_manager.py        # State persistence & recovery
│   │   └── state_serializer.py     # State serialization utilities
│   │
│   ├── nodes/                      # Reusable Node Components
│   │   ├── __init__.py
│   │   ├── base/                   # Base node implementations
│   │   │   ├── __init__.py
│   │   │   ├── base_node.py       # Abstract base node with common functionality
│   │   │   ├── conditional_node.py # Conditional routing node
│   │   │   ├── parallel_node.py   # Parallel execution node
│   │   │   ├── aggregation_node.py # Result aggregation node
│   │   │   └── validation_node.py # Input/output validation node
│   │   │
│   │   ├── document/              # Document processing nodes
│   │   │   ├── __init__.py
│   │   │   ├── ingestion_node.py  # Document ingestion and initial processing
│   │   │   ├── parsing_node.py    # Content parsing and extraction
│   │   │   ├── validation_node.py # Document validation and quality checks
│   │   │   ├── extraction_node.py # Information and entity extraction
│   │   │   ├── classification_node.py # Document classification
│   │   │   ├── indexing_node.py   # Document indexing and storage
│   │   │   └── metadata_node.py   # Metadata extraction and enrichment
│   │   │
│   │   ├── knowledge/             # Knowledge graph nodes
│   │   │   ├── __init__.py
│   │   │   ├── entity_extraction_node.py # Entity extraction from documents
│   │   │   ├── relationship_mapping_node.py # Relationship identification
│   │   │   ├── graph_construction_node.py # Graph structure building
│   │   │   ├── graph_validation_node.py # Graph consistency validation
│   │   │   ├── entity_resolution_node.py # Entity deduplication and linking
│   │   │   └── graph_enrichment_node.py # Graph enrichment with external data
│   │   │
│   │   ├── qme/                   # QME generation nodes
│   │   │   ├── __init__.py
│   │   │   ├── template_selection_node.py # Template type selection
│   │   │   ├── field_extraction_node.py # Required field identification
│   │   │   ├── data_mapping_node.py # Data mapping to template fields
│   │   │   ├── template_population_node.py # Template filling
│   │   │   ├── validation_node.py # Template validation
│   │   │   ├── formatting_node.py # Output formatting
│   │   │   └── finalization_node.py # Final review and approval
│   │   │
│   │   ├── qa/                    # Q&A processing nodes
│   │   │   ├── __init__.py
│   │   │   ├── query_analysis_node.py # Query understanding and parsing
│   │   │   ├── intent_classification_node.py # Intent classification
│   │   │   ├── context_retrieval_node.py # Relevant context retrieval
│   │   │   ├── answer_generation_node.py # Answer generation
│   │   │   ├── fact_checking_node.py # Answer fact checking
│   │   │   ├── citation_node.py   # Source citation and attribution
│   │   │   └── response_formatting_node.py # Response formatting
│   │   │
│   │   └── utility/               # Utility nodes
│   │       ├── __init__.py
│   │       ├── logging_node.py    # Logging and monitoring
│   │       ├── error_handling_node.py # Error handling and recovery
│   │       ├── notification_node.py # User notifications
│   │       ├── checkpoint_node.py # State checkpointing
│   │       ├── cache_node.py      # Caching operations
│   │       └── metrics_node.py    # Performance metrics collection
│   │
│   ├── graphs/                    # Graph Definitions
│   │   ├── __init__.py
│   │   ├── base/                  # Base graph components
│   │   │   ├── __init__.py
│   │   │   ├── base_graph.py     # Abstract base graph with common functionality
│   │   │   ├── graph_builder.py  # Graph construction utilities
│   │   │   ├── graph_registry.py # Graph registration and discovery system
│   │   │   ├── graph_validator.py # Graph structure validation
│   │   │   └── graph_optimizer.py # Graph optimization utilities
│   │   │
│   │   ├── workflows/            # Specific workflow graphs
│   │   │   ├── __init__.py
│   │   │   ├── document_processing_graph.py # Complete document processing workflow
│   │   │   ├── knowledge_graph_construction.py # Knowledge graph building workflow
│   │   │   ├── qme_generation_graph.py # QME template generation workflow
│   │   │   ├── qa_processing_graph.py # Q&A processing workflow
│   │   │   ├── hybrid_workflows.py # Combined multi-step workflows
│   │   │   └── batch_processing_graph.py # Batch processing workflows
│   │   │
│   │   └── routing/              # Graph routing logic
│   │       ├── __init__.py
│   │       ├── conditional_routing.py # Conditional flow routing
│   │       ├── parallel_routing.py # Parallel execution routing
│   │       ├── error_routing.py  # Error handling routing
│   │       └── dynamic_routing.py # Dynamic routing based on state
│   │
│   └── llm_providers/            # LLM Provider Abstraction Layer
│       ├── __init__.py
│       ├── base/                 # Base provider interfaces
│       │   ├── __init__.py
│       │   ├── base_provider.py  # Abstract LLM provider interface
│       │   ├── provider_config.py # Provider configuration schemas
│       │   ├── provider_factory.py # Provider factory and registry
│       │   ├── provider_manager.py # Provider lifecycle management
│       │   └── response_parser.py # Common response parsing utilities
│       │
│       ├── gemini/              # Gemini Implementation (Current)
│       │   ├── __init__.py
│       │   ├── nodes/           # Gemini-specific node implementations
│       │   │   ├── __init__.py
│       │   │   ├── gemini_extraction_node.py # Gemini entity extraction
│       │   │   ├── gemini_generation_node.py # Gemini text generation
│       │   │   ├── gemini_analysis_node.py # Gemini document analysis
│       │   │   ├── gemini_qa_node.py # Gemini Q&A processing
│       │   │   └── gemini_classification_node.py # Gemini classification
│       │   │
│       │   ├── graphs/          # Gemini-optimized graph implementations
│       │   │   ├── __init__.py
│       │   │   ├── gemini_document_graph.py # Gemini document processing
│       │   │   ├── gemini_qme_graph.py # Gemini QME generation
│       │   │   ├── gemini_qa_graph.py # Gemini Q&A processing
│       │   │   └── gemini_knowledge_graph.py # Gemini knowledge extraction
│       │   │
│       │   ├── config/          # Gemini configuration
│       │   │   ├── __init__.py
│       │   │   ├── model_config.py # Gemini model configurations
│       │   │   ├── prompt_templates.py # Gemini-specific prompts
│       │   │   └── fine_tuning_config.py # Fine-tuning configurations
│       │   │
│       │   └── utils/           # Gemini utilities
│       │       ├── __init__.py
│       │       ├── token_counter.py # Gemini token counting
│       │       ├── rate_limiter.py # Gemini rate limiting
│       │       ├── response_parser.py # Gemini response parsing
│       │       └── error_handler.py # Gemini error handling
│       │
│       ├── claude/              # Claude Implementation (Future)
│       │   ├── __init__.py
│       │   ├── nodes/           # Claude-specific node implementations
│       │   │   └── __init__.py
│       │   ├── graphs/          # Claude-optimized graph implementations
│       │   │   └── __init__.py
│       │   ├── config/          # Claude configuration
│       │   │   └── __init__.py
│       │   └── utils/           # Claude utilities
│       │       └── __init__.py
│       │
│       ├── openai/              # OpenAI Implementation (Future)
│       │   ├── __init__.py
│       │   ├── nodes/           # OpenAI-specific node implementations
│       │   │   └── __init__.py
│       │   ├── graphs/          # OpenAI-optimized graph implementations
│       │   │   └── __init__.py
│       │   ├── config/          # OpenAI configuration
│       │   │   └── __init__.py
│       │   └── utils/           # OpenAI utilities
│       │       └── __init__.py
│       │
│       └── local/               # Local Models Implementation (Future)
│           ├── __init__.py
│           ├── nodes/           # Local model node implementations
│           │   └── __init__.py
│           ├── graphs/          # Local model graph implementations
│           │   └── __init__.py
│           ├── config/          # Local model configuration
│           │   └── __init__.py
│           └── utils/           # Local model utilities
│               └── __init__.py
│
├── presentation/                # Presentation Layer
│   ├── __init__.py
│   ├── api/                    # REST API controllers
│   │   ├── __init__.py
│   │   ├── base_controller.py  # Base controller with common functionality
│   │   ├── document_controller.py # Document management endpoints
│   │   ├── qme_controller.py   # QME generation endpoints
│   │   ├── knowledge_controller.py # Knowledge graph endpoints
│   │   ├── qa_controller.py    # Q&A endpoints
│   │   └── health_controller.py # Health check endpoints
│   │
│   ├── web/                    # Web interface (Streamlit)
│   │   ├── __init__.py
│   │   ├── main_app.py        # Main Streamlit application
│   │   ├── components/        # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── document_uploader.py # Document upload component
│   │   │   ├── progress_tracker.py # Progress tracking component
│   │   │   ├── qa_interface.py # Q&A interface component
│   │   │   └── results_viewer.py # Results viewing component
│   │   │
│   │   ├── pages/             # Streamlit pages
│   │   │   ├── __init__.py
│   │   │   ├── document_management.py # Document management page
│   │   │   ├── qme_generation.py # QME generation page
│   │   │   ├── knowledge_explorer.py # Knowledge graph explorer
│   │   │   └── qa_chat.py     # Q&A chat interface
│   │   │
│   │   └── utils/             # Web UI utilities
│   │       ├── __init__.py
│   │       ├── session_manager.py # Session management
│   │       ├── file_handler.py # File handling utilities
│   │       └── display_utils.py # Display formatting utilities
│   │
│   └── cli/                   # Command line interface
│       ├── __init__.py
│       ├── main_cli.py        # Main CLI application
│       ├── commands/          # CLI command implementations
│       │   ├── __init__.py
│       │   ├── process_command.py # Document processing command
│       │   ├── generate_command.py # QME generation command
│       │   ├── query_command.py # Query command
│       │   └── config_command.py # Configuration command
│       │
│       └── utils/             # CLI utilities
│           ├── __init__.py
│           ├── output_formatter.py # Output formatting
│           └── progress_bar.py # Progress bar utilities
│
└── shared/                    # Shared utilities and cross-cutting concerns
    ├── __init__.py
    ├── exceptions/            # Custom exceptions
    │   ├── __init__.py
    │   ├── base_exceptions.py # Base exception classes
    │   ├── domain_exceptions.py # Domain-specific exceptions
    │   ├── infrastructure_exceptions.py # Infrastructure exceptions
    │   └── validation_exceptions.py # Validation exceptions
    │
    ├── logging/               # Logging configuration
    │   ├── __init__.py
    │   ├── logger_config.py   # Logger configuration
    │   ├── formatters.py      # Custom log formatters
    │   └── handlers.py        # Custom log handlers
    │
    ├── config/                # Configuration management
    │   ├── __init__.py
    │   ├── app_config.py      # Application configuration
    │   ├── environment_config.py # Environment-specific configuration
    │   ├── llm_config.py      # LLM provider configurations
    │   └── storage_config.py  # Storage configurations
    │
    ├── utils/                 # Utility functions
    │   ├── __init__.py
    │   ├── file_utils.py      # File handling utilities
    │   ├── text_utils.py      # Text processing utilities
    │   ├── validation_utils.py # Validation utilities
    │   ├── serialization_utils.py # Serialization utilities
    │   └── crypto_utils.py    # Cryptography utilities
    │
    ├── middleware/            # Cross-cutting concerns
    │   ├── __init__.py
    │   ├── authentication.py # Authentication middleware
    │   ├── authorization.py  # Authorization middleware
    │   ├── rate_limiting.py  # Rate limiting middleware
    │   ├── request_logging.py # Request logging middleware
    │   └── error_handling.py # Global error handling middleware
    │
    └── constants/             # Application constants
        ├── __init__.py
        ├── file_types.py      # Supported file types
        ├── medical_codes.py   # Medical coding constants
        ├── template_types.py  # QME template types
        └── processing_stages.py # Processing stage constants
```

## Specific Implementation Requirements

### 1. Domain Layer Implementation
- Create rich domain entities with business rules and invariants
- Implement value objects as immutable data containers
- Define repository interfaces as ports (hexagonal architecture)
- Create domain services for complex business logic
- Implement domain events for decoupled communication

### 2. Application Layer Implementation
- Implement CQRS pattern with separate command and query handlers
- Create DTOs for data transfer between layers
- Build orchestrators for complex multi-step workflows
- Define application service interfaces

### 3. Infrastructure Layer Implementation
- Create adapters for external systems (storage, parsers, APIs)
- Implement factory patterns for object creation
- Build strategy patterns for different processing approaches
- Create repository implementations
- Add configuration management

### 4. LangGraph Modular Implementation
- Create base state management system with serialization
- Build reusable node components with clear interfaces
- Implement graph definitions with dynamic construction
- Create LLM provider abstraction layer
- Add provider-specific implementations (start with Gemini)

### 5. Presentation Layer Implementation
- Build REST API controllers with proper error handling
- Create Streamlit web interface with reusable components
- Add CLI interface for batch operations
- Implement proper request/response handling

### 6. Shared Layer Implementation
- Create comprehensive exception hierarchy
- Implement structured logging system
- Add configuration management with environment support
- Create utility functions for common operations
- Add middleware for cross-cutting concerns

## Key Design Principles

### Clean Architecture
- Dependencies point inward toward the domain
- No dependencies from inner layers to outer layers
- Business logic is independent of frameworks and external systems

### SOLID Principles
- Single Responsibility: Each class has one reason to change
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: Subtypes must be substitutable for base types
- Interface Segregation: Clients depend only on interfaces they use
- Dependency Inversion: Depend on abstractions, not concretions

### Domain-Driven Design
- Clear bounded contexts for different domains
- Rich domain models with business logic
- Ubiquitous language throughout the codebase
- Domain events for decoupled communication

## Implementation Strategy

### Phase 1: Foundation
1. Create the complete folder structure
2. Implement base classes and interfaces
3. Set up dependency injection container
4. Create configuration management system

### Phase 2: Domain Layer
1. Implement domain entities with business rules
2. Create value objects and domain services
3. Define repository interfaces
4. Implement domain events system

### Phase 3: Infrastructure Layer
1. Create adapters for external systems
2. Implement repository concrete classes
3. Build factory and strategy patterns
4. Add configuration implementations

### Phase 4: LangGraph Integration
1. Implement base state management
2. Create reusable node components
3. Build graph definitions and routing
4. Integrate Gemini provider implementation

### Phase 5: Application Layer
1. Implement command and query handlers
2. Create orchestrators for workflows
3. Build DTOs and service interfaces
4. Add application-level validation

### Phase 6: Presentation Layer
1. Build REST API controllers
2. Create web interface components
3. Add CLI interface
4. Implement proper error handling

## Migration Instructions

1. **Preserve existing functionality** during refactoring
2. **Move existing code** to appropriate layers in the new structure
3. **Create adapter classes** to wrap existing implementations initially
4. **Implement interfaces** for all external dependencies
5. **Add comprehensive logging** throughout the system
6. **Create unit tests** for each component as you refactor
7. **Update configuration files** to match new structure
8. **Maintain backward compatibility** for existing APIs

## Files to Create or Refactor

### Critical Files to Implement First:
1. `domain/entities/document.py` - Core document entity
2. `shared/config/app_config.py` - Application configuration
3. `infrastructure/factories/llm_provider_factory.py` - LLM provider factory
4. `langgraph/state/base_state.py` - Base state management
5. `langgraph/nodes/base/base_node.py` - Base node implementation
6. `application/orchestrators/document_processing_orchestrator.py` - Main workflow

### Configuration Files to Update:
- Update `requirements.txt` with new dependencies
- Create `config/` directory with YAML configuration files
- Update Docker configurations if needed
- Create environment-specific configuration files

## Testing Strategy

Create comprehensive tests for each layer:
- **Unit tests** for domain entities and value objects
- **Integration tests** for infrastructure adapters
- **Workflow tests** for LangGraph implementations
- **API tests** for presentation layer
- **End-to-end tests** for complete workflows

## Documentation Requirements

Create documentation for:
- **Architecture overview** with diagrams
- **API documentation** with examples
- **Configuration guide** for different environments
- **Developer guide** for extending the system
- **User guide** for operating the system

## Specific Code Generation Tasks

### 1. Create Base Domain Entities

Generate the following domain entities with proper business logic:

**Document Entity** (`domain/entities/document.py`):
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(Enum):
    MEDICAL_REPORT = "medical_report"
    ATTORNEY_DOCUMENT = "attorney_document"
    AMA_GUIDELINE = "ama_guideline"
    QME_TEMPLATE = "qme_template"

class DocumentStatus(Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

@dataclass
class Document:
    # Entity properties with business rules
    # Methods for business operations
    # Validation methods
    # Domain events
```

**QME Template Entity** (`domain/entities/qme_template.py`):
```python
# Complete QME template entity with validation rules
# Template field management
# Medical specialty handling
# Completion tracking
```

### 2. Create LangGraph Base Components

**Base State** (`langgraph/state/base_state.py`):
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class StateStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BaseState(ABC):
    # Common state properties
    # Serialization methods
    # State transition methods
    # Validation methods
```

**Base Node** (`langgraph/nodes/base/base_node.py`):
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class BaseNode(ABC):
    # Node interface definition
    # Common node functionality
    # Error handling
    # Logging integration
    # Performance monitoring
```

### 3. Create Infrastructure Adapters

**LLM Provider Factory** (`infrastructure/factories/llm_provider_factory.py`):
```python
from typing import Dict, Any, Type
from ..adapters.base_llm_provider import BaseLLMProvider

class LLMProviderFactory:
    # Provider registration system
    # Dynamic provider creation
    # Configuration management
    # Provider switching logic
```

**Storage Factory** (`infrastructure/factories/storage_factory.py`):
```python
# Storage adapter creation
# Configuration-based storage selection
# Connection management
# Storage strategy implementation
```

### 4. Create Application Services

**Document Processing Orchestrator** (`application/orchestrators/document_processing_orchestrator.py`):
```python
from typing import Dict, Any, List
from ..commands.process_document_command import ProcessDocumentCommand
from ...domain.entities.document import Document
from ...langgraph.graphs.workflows.document_processing_graph import DocumentProcessingGraph

class DocumentProcessingOrchestrator:
    # Workflow coordination
    # State management
    # Error handling and recovery
    # Progress tracking
    # Event publishing
```

### 5. Create Configuration Management

**Application Configuration** (`shared/config/app_config.py`):
```python
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import yaml

@dataclass
class DatabaseConfig:
    # Database connection settings

@dataclass
class LLMConfig:
    # LLM provider configurations

@dataclass
class StorageConfig:
    # Storage settings

@dataclass
class AppConfig:
    # Main application configuration
    # Environment-specific settings
    # Configuration loading methods
```

### 6. Create API Controllers

**Document Controller** (`presentation/api/document_controller.py`):
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import List, Optional
from ...application.dto.document_dto import DocumentDTO, DocumentCreateDTO

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Document upload endpoint
# Document retrieval endpoints
# Document processing status endpoints
# Document search endpoints
```

### 7. Create Web Interface Components

**Main Streamlit App** (`presentation/web/main_app.py`):
```python
import streamlit as st
from typing import Dict, Any
import asyncio

# Main application layout
# Navigation system
# Session management
# Error handling
# Progress tracking
```

**Document Upload Component** (`presentation/web/components/document_uploader.py`):
```python
import streamlit as st
from typing import List, Optional
import tempfile
import os

class DocumentUploader:
    # File upload interface
    # File validation
    # Progress tracking
    # Error handling
```

### 8. Create Gemini Provider Implementation

**Gemini Provider** (`langgraph/llm_providers/gemini/gemini_provider.py`):
```python
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from ..base.base_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    # Gemini client initialization
    # Text generation methods
    # Entity extraction methods
    # Document analysis methods
    # Rate limiting and error handling
```

**Gemini Nodes** (`langgraph/llm_providers/gemini/nodes/`):
```python
# gemini_extraction_node.py - Entity extraction with Gemini
# gemini_generation_node.py - Text generation with Gemini
# gemini_analysis_node.py - Document analysis with Gemini
# gemini_qa_node.py - Q&A processing with Gemini
```

### 9. Create Workflow Graphs

**Document Processing Graph** (`langgraph/graphs/workflows/document_processing_graph.py`):
```python
from langgraph.graph import Graph, END
from typing import Dict, Any
from ...nodes.document import *
from ...state.document_state import DocumentState

class DocumentProcessingGraph:
    # Graph construction
    # Node wiring
    # Conditional routing
    # Error handling paths
```

### 10. Create Repository Implementations

**SQL Document Repository** (`infrastructure/repositories/sql_document_repository.py`):
```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ...domain.repositories.document_repository import DocumentRepository
from ...domain.entities.document import Document

class SQLDocumentRepository(DocumentRepository):
    # CRUD operations
    # Query methods
    # Transaction management
    # Error handling
```

## Configuration Files to Generate

### 1. LLM Provider Configuration (`config/llm_providers.yaml`)
```yaml
providers:
  gemini:
    model: "gemini-1.5-flash"
    api_key: "${GEMINI_API_KEY}"
    rate_limit: 60
    max_tokens: 8192
    temperature: 0.1
    safety_settings:
      harassment: "block_none"
      hate_speech: "block_none"
  
  claude:
    model: "claude-3-sonnet-20240229"
    api_key: "${ANTHROPIC_API_KEY}"
    rate_limit: 50
    max_tokens: 4096
    temperature: 0.1
  
  openai:
    model: "gpt-4-turbo"
    api_key: "${OPENAI_API_KEY}"
    rate_limit: 100
    max_tokens: 4096
    temperature: 0.1
```

### 2. Application Configuration (`config/app_config.yaml`)
```yaml
application:
  name: "Document Management System"
  version: "2.0.0"
  debug: false
  
database:
  type: "postgresql"
  host: "${DB_HOST:localhost}"
  port: "${DB_PORT:5432}"
  database: "${DB_NAME:dms}"
  username: "${DB_USER:dms_user}"
  password: "${DB_PASSWORD}"
  
storage:
  type: "local"  # local, s3, gcs
  local_path: "./data/documents"
  vector_db:
    type: "chroma"  # chroma, pinecone, weaviate
    connection_string: "${VECTOR_DB_URL}"
  
workflows:
  default_llm_provider: "gemini"
  max_concurrent_jobs: 5
  timeout_seconds: 3600
```

### 3. Logging Configuration (`config/logging.yaml`)
```yaml
version: 1
disable_existing_loggers: false

formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  structured:
    format: '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: structured
    filename: logs/app.log

loggers:
  domain:
    level: DEBUG
    handlers: [console, file]
  langgraph:
    level: DEBUG
    handlers: [console, file]
  infrastructure:
    level: INFO
    handlers: [console, file]

root:
  level: INFO
  handlers: [console]
```

## Dependency Updates

### Requirements.txt Updates
Add the following dependencies:
```
# Core dependencies
fastapi>=0.104.0
uvicorn>=0.24.0
streamlit>=1.28.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.0.0
dependency-injector>=4.41.0

# LangGraph and AI
langgraph>=0.0.40
langchain>=0.1.0
google-generativeai>=0.3.0
anthropic>=0.7.0  # For future Claude integration
openai>=1.0.0     # For future OpenAI integration

# Storage and databases
chromadb>=0.4.0
psycopg2-binary>=2.9.0
redis>=5.0.0

# Document processing
pypdf2>=3.0.0
python-docx>=0.8.0
pillow>=10.0.0
pytesseract>=0.3.0  # For OCR

# Utilities
pyyaml>=6.0
python-dotenv>=1.0.0
tenacity>=8.2.0  # For retries
httpx>=0.25.0
```

## Migration Scripts

### 1. Data Migration Script (`scripts/migrate_existing_data.py`)
```python
#!/usr/bin/env python3
"""
Migration script to move existing data to new structure
"""
import os
import shutil
from pathlib import Path
import logging

def migrate_documents():
    # Migrate existing documents to new structure
    pass

def migrate_configurations():
    # Migrate existing configurations
    pass

def migrate_database():
    # Migrate database schema if needed
    pass

if __name__ == "__main__":
    migrate_documents()
    migrate_configurations()
    migrate_database()
```

### 2. Refactoring Script (`scripts/refactor_codebase.py`)
```python
#!/usr/bin/env python3
"""
Automated refactoring script to move existing code
"""
import ast
import os
from pathlib import Path

def move_existing_files():
    # Map old file locations to new structure
    pass

def update_imports():
    # Update import statements in existing files
    pass

def create_adapter_wrappers():
    # Create adapters for existing implementations
    pass

if __name__ == "__main__":
    move_existing_files()
    update_imports()
    create_adapter_wrappers()
```

## Testing Framework Setup

### 1. Test Configuration (`tests/conftest.py`)
```python
import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    # Async test support
    pass

@pytest.fixture
def test_database():
    # Test database setup
    pass

@pytest.fixture
def mock_llm_provider():
    # Mock LLM provider for testing
    pass
```

### 2. Domain Tests (`tests/domain/`)
```python
# test_document_entity.py - Test document business logic
# test_qme_template.py - Test QME template validation
# test_domain_services.py - Test domain services
```

### 3. LangGraph Tests (`tests/langgraph/`)
```python
# test_base_state.py - Test state management
# test_nodes.py - Test individual nodes
# test_graphs.py - Test workflow graphs
# test_providers.py - Test LLM providers
```

## Docker Configuration Updates

### 1. Multi-stage Dockerfile
```dockerfile
# Update existing Dockerfile to support new structure
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Production stage
FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY config/ /app/config/
WORKDIR /app

CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Docker Compose Updates
```yaml
# Update docker-compose.yml to include new services
version: '3.8'

services:
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dms
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dms
      - POSTGRES_USER=dms_user
      - POSTGRES_PASSWORD=dms_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## Implementation Notes

### Critical Success Factors:
1. **Maintain backwards compatibility** during refactoring
2. **Implement comprehensive error handling** throughout
3. **Add extensive logging** for debugging and monitoring
4. **Create thorough tests** for all components
5. **Use dependency injection** for loose coupling
6. **Implement proper configuration management**
7. **Add health checks** and monitoring endpoints
8. **Create clear documentation** for each component

### Performance Considerations:
1. **Async/await** for I/O operations
2. **Connection pooling** for databases
3. **Caching strategies** for frequently accessed data
4. **Batch processing** for large document sets
5. **Rate limiting** for external API calls
6. **Memory management** for large files
7. **Background task processing** for long-running operations

### Security Requirements:
1. **Input validation** for all user inputs
2. **Authentication and authorization** for API endpoints
3. **Secure file handling** for uploaded documents
4. **API key management** for external services
5. **Data encryption** for sensitive information
6. **Audit logging** for security events
7. **Rate limiting** to prevent abuse

This comprehensive refactoring will transform your current codebase into a maintainable, scalable, and extensible system following best practices and design patterns. The modular LangGraph implementation will make it easy to switch between different LLM providers and extend functionality as needed.