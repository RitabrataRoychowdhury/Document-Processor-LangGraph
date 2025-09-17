"""
Consolidated Document Processing Service.

This module consolidates the functionality from document_processor.py, 
enhanced_document_processor.py, and refactored_document_processor.py into
a single, comprehensive document processing service with proper error handling,
dependency injection, and structured logging.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# Core imports
from src.core.exceptions import (
    ExtractionError, DocumentNotFoundError, InvalidDocumentFormatError,
    FieldExtractionError, StorageError
)
from src.infrastructure.monitoring.structured_logger import extraction_logger
from src.infrastructure.monitoring.circuit_breaker import circuit_breaker_registry
from src.infrastructure.monitoring.retry_handler import with_retry, BackoffStrategy

# Service imports (will be updated as we consolidate)
try:
    from src.core.extraction.openrouter_extraction_service import OpenRouterExtractionService
    from src.infrastructure.knowledge.enhanced_rag_pipeline import EnhancedRAGPipeline
    from src.infrastructure.storage.vector_store import InMemoryVectorStore
    from src.strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from src.storage.database import DatabaseManager
    from src.config.app_config import AppConfig
except ImportError as e:
    extraction_logger.warning(f"Some dependencies not available: {e}")


@dataclass
class DocumentProcessingConfig:
    """Configuration for document processing."""
    use_openrouter_extraction: bool = True
    use_vision_extraction: bool = False
    extraction_prompt_template: str = "patient_info"
    max_contexts_per_document: int = 20
    min_confidence_threshold: float = 0.5
    enable_knowledge_graph_updates: bool = True
    enable_vector_store_updates: bool = True
    quality_validation_enabled: bool = True
    supported_file_types: List[str] = field(default_factory=lambda: ['.pdf', '.docx', '.txt'])
    max_file_size_mb: int = 50


@dataclass
class ProcessingResult:
    """Result of document processing operation."""
    success: bool
    document_id: Optional[str] = None
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvenanceReference:
    """Tracks the source of extracted information."""
    doc_id: str
    page: Optional[int] = None
    offset: Optional[int] = None
    snippet: Optional[str] = None
    confidence: float = 1.0
    extraction_method: str = "rule_based"
    created_at: datetime = field(default_factory=datetime.now)


class IDocumentProcessor(ABC):
    """Interface for document processing services."""
    
    @abstractmethod
    async def process_document(self, file_path: str, **kwargs) -> ProcessingResult:
        """Process a document and extract information."""
        pass
    
    @abstractmethod
    async def get_document_status(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get processing status of a document."""
        pass
    
    @abstractmethod
    async def validate_document(self, file_path: str) -> bool:
        """Validate if document can be processed."""
        pass


class DocumentProcessor(IDocumentProcessor):
    """
    Consolidated document processor with enhanced capabilities.
    
    Features:
    - Multiple extraction methods (simple, enhanced, OpenRouter-based)
    - Comprehensive error handling with circuit breaker pattern
    - Structured logging with correlation IDs
    - Knowledge graph integration
    - Vector store integration for semantic search
    - Provenance tracking and metadata management
    """
    
    def __init__(
        self,
        config: Optional[DocumentProcessingConfig] = None,
        openrouter_service: Optional[OpenRouterExtractionService] = None,
        vector_store: Optional[InMemoryVectorStore] = None,
        embedding_strategy: Optional[EmbeddingStrategy] = None,
        kg_repository: Optional[KnowledgeGraphRepository] = None,
        database_manager: Optional[DatabaseManager] = None
    ):
        """Initialize the document processor with dependencies."""
        self.config = config or DocumentProcessingConfig()
        
        # Initialize services with graceful degradation
        self.openrouter_service = openrouter_service
        self.vector_store = vector_store
        self.embedding_strategy = embedding_strategy
        self.kg_repository = kg_repository
        self.database_manager = database_manager
        
        # Initialize RAG pipeline if dependencies are available
        self.rag_pipeline = None
        if self.openrouter_service and self.vector_store:
            try:
                self.rag_pipeline = EnhancedRAGPipeline(
                    openrouter_service=self.openrouter_service,
                    vector_store=self.vector_store,
                    embedding_strategy=self.embedding_strategy,
                    kg_repository=self.kg_repository
                )
            except Exception as e:
                extraction_logger.warning(f"Could not initialize RAG pipeline: {e}")
        
        # Get circuit breaker for external API calls
        self.circuit_breaker = circuit_breaker_registry.get_breaker("document_processor")
        
        extraction_logger.info(
            "Initialized DocumentProcessor",
            extra_data={
                "config": {
                    "use_openrouter_extraction": self.config.use_openrouter_extraction,
                    "min_confidence_threshold": self.config.min_confidence_threshold,
                    "supported_file_types": self.config.supported_file_types
                },
                "services_available": {
                    "openrouter_service": self.openrouter_service is not None,
                    "vector_store": self.vector_store is not None,
                    "embedding_strategy": self.embedding_strategy is not None,
                    "kg_repository": self.kg_repository is not None,
                    "database_manager": self.database_manager is not None,
                    "rag_pipeline": self.rag_pipeline is not None
                }
            }
        )
    
    async def validate_document(self, file_path: str) -> bool:
        """Validate if document can be processed."""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise DocumentNotFoundError(f"Document not found: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = self.config.max_file_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise InvalidDocumentFormatError(
                    f"File size {file_size} bytes exceeds maximum {max_size_bytes} bytes"
                )
            
            # Check file type
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.config.supported_file_types:
                raise InvalidDocumentFormatError(
                    f"Unsupported file type: {file_ext}. Supported types: {self.config.supported_file_types}"
                )
            
            extraction_logger.debug(
                f"Document validation passed: {file_path}",
                extra_data={
                    "file_size": file_size,
                    "file_type": file_ext,
                    "file_name": os.path.basename(file_path)
                }
            )
            
            return True
            
        except Exception as e:
            extraction_logger.error(
                f"Document validation failed: {file_path}",
                error=e,
                extra_data={"file_path": file_path}
            )
            raise
    
    @with_retry(
        max_attempts=3,
        base_delay=1.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_JITTER
    )
    async def process_document(self, file_path: str, **kwargs) -> ProcessingResult:
        """Process a document and extract information."""
        start_time = datetime.now()
        
        try:
            extraction_logger.info(
                f"Starting document processing: {file_path}",
                extra_data={
                    "file_path": file_path,
                    "processing_method": "enhanced" if self.rag_pipeline else "simple",
                    "kwargs": kwargs
                }
            )
            
            # Validate document
            await self.validate_document(file_path)
            
            # Check if document already exists
            existing_status = await self.get_document_status(file_path)
            if existing_status and existing_status.get('status') == 'completed':
                extraction_logger.info(
                    f"Document already processed: {file_path}",
                    extra_data={"existing_document_id": existing_status.get('id')}
                )
                return ProcessingResult(
                    success=True,
                    document_id=existing_status.get('id'),
                    metadata={"already_processed": True}
                )
            
            # Process document based on available services
            if self.rag_pipeline and self.config.use_openrouter_extraction:
                result = await self._process_with_rag_pipeline(file_path, **kwargs)
            else:
                result = await self._process_simple(file_path, **kwargs)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            extraction_logger.info(
                f"Document processing completed: {file_path}",
                extra_data={
                    "success": result.success,
                    "document_id": result.document_id,
                    "processing_time": processing_time,
                    "extracted_fields_count": len(result.extracted_fields),
                    "average_confidence": sum(result.confidence_scores.values()) / len(result.confidence_scores) if result.confidence_scores else 0
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            extraction_logger.error(
                f"Document processing failed: {file_path}",
                error=e,
                extra_data={
                    "file_path": file_path,
                    "processing_time": processing_time,
                    "error_type": type(e).__name__
                }
            )
            
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time,
                metadata={"error_type": type(e).__name__}
            )
    
    async def _process_with_rag_pipeline(self, file_path: str, **kwargs) -> ProcessingResult:
        """Process document using enhanced RAG pipeline."""
        try:
            # Use circuit breaker for external API calls
            processing_result = await self.circuit_breaker.call(
                self.rag_pipeline.process_document,
                file_path,
                **kwargs
            )
            
            # Store in database if available
            document_id = None
            if self.database_manager:
                document_id = await self._store_document_record(file_path, processing_result)
            
            return ProcessingResult(
                success=True,
                document_id=document_id,
                extracted_fields=processing_result.extracted_data,
                confidence_scores=processing_result.confidence_scores,
                metadata={
                    "extraction_method": "rag_pipeline",
                    "contexts_generated": len(processing_result.contexts),
                    "quality_score": processing_result.quality_score
                }
            )
            
        except Exception as e:
            raise ExtractionError(
                f"RAG pipeline processing failed: {str(e)}",
                context={"file_path": file_path, "method": "rag_pipeline"},
                cause=e
            )
    
    async def _process_simple(self, file_path: str, **kwargs) -> ProcessingResult:
        """Process document using simple method."""
        try:
            # Get file info
            file_path_obj = Path(file_path)
            file_name = file_path_obj.name
            file_size = file_path_obj.stat().st_size
            file_ext = file_path_obj.suffix.lower()
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Basic extracted info
            extracted_fields = {
                "file_name": file_name,
                "file_size": file_size,
                "file_type": file_ext[1:],
                "file_path": file_path
            }
            
            # Store in database if available
            if self.database_manager:
                await self._store_simple_document_record(document_id, file_path, extracted_fields)
            
            return ProcessingResult(
                success=True,
                document_id=document_id,
                extracted_fields=extracted_fields,
                confidence_scores={"file_info": 1.0},
                metadata={"extraction_method": "simple"}
            )
            
        except Exception as e:
            raise ExtractionError(
                f"Simple processing failed: {str(e)}",
                context={"file_path": file_path, "method": "simple"},
                cause=e
            )
    
    async def _store_document_record(self, file_path: str, processing_result: Any) -> str:
        """Store document record in database."""
        try:
            document_id = str(uuid.uuid4())
            now = datetime.now()
            
            file_path_obj = Path(file_path)
            extracted_info = json.dumps({
                "file_path": file_path,
                "extracted_data": processing_result.extracted_data,
                "confidence_scores": processing_result.confidence_scores,
                "quality_score": processing_result.quality_score
            })
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (
                        id, title, file_type, file_size, processing_status,
                        upload_timestamp, created_at, updated_at, extracted_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id, file_path_obj.name, file_path_obj.suffix[1:],
                    file_path_obj.stat().st_size, 'completed',
                    now, now, now, extracted_info
                ))
                conn.commit()
            
            return document_id
            
        except Exception as e:
            raise StorageError(
                f"Failed to store document record: {str(e)}",
                context={"file_path": file_path},
                cause=e
            )
    
    async def _store_simple_document_record(self, document_id: str, file_path: str, extracted_fields: Dict[str, Any]) -> None:
        """Store simple document record in database."""
        try:
            now = datetime.now()
            file_path_obj = Path(file_path)
            
            extracted_info = json.dumps(extracted_fields)
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (
                        id, title, file_type, file_size, processing_status,
                        upload_timestamp, created_at, updated_at, extracted_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id, file_path_obj.name, file_path_obj.suffix[1:],
                    file_path_obj.stat().st_size, 'completed',
                    now, now, now, extracted_info
                ))
                conn.commit()
                
        except Exception as e:
            raise StorageError(
                f"Failed to store simple document record: {str(e)}",
                context={"file_path": file_path, "document_id": document_id},
                cause=e
            )
    
    async def get_document_status(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get processing status of a document."""
        if not self.database_manager:
            return None
        
        try:
            file_name = os.path.basename(file_path)
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, processing_status, upload_timestamp, updated_at, extracted_info
                    FROM documents 
                    WHERE title = ?
                """, (file_name,))
                
                row = cursor.fetchone()
                if row:
                    # Check if the extracted_info contains the file path
                    extracted_info = row[5]
                    if extracted_info:
                        try:
                            info = json.loads(extracted_info)
                            if info.get('file_path') == file_path:
                                return {
                                    'id': row[0],
                                    'title': row[1],
                                    'status': row[2],
                                    'uploaded': row[3],
                                    'updated': row[4]
                                }
                        except json.JSONDecodeError:
                            pass
                    
                    # Fallback: match by title only
                    return {
                        'id': row[0],
                        'title': row[1],
                        'status': row[2],
                        'uploaded': row[3],
                        'updated': row[4]
                    }
                
                return None
                
        except Exception as e:
            extraction_logger.error(
                f"Error getting document status: {file_path}",
                error=e,
                extra_data={"file_path": file_path}
            )
            return None


# Factory function for creating document processor instances
def create_document_processor(
    config: Optional[DocumentProcessingConfig] = None,
    **dependencies
) -> DocumentProcessor:
    """Factory function to create document processor with dependencies."""
    return DocumentProcessor(config=config, **dependencies)