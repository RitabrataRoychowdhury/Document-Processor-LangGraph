"""
Refactored Document Processing Pipeline with Enhanced RAG Integration.

This module replaces the existing document processing logic with OpenRouter-based
extraction and enhanced RAG capabilities, providing superior accuracy and
comprehensive metadata tracking.
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..models.extraction_models import ExtractionConfig, ExtractionMethod
from ..services.enhanced_rag_pipeline import (
    EnhancedRAGPipeline, ProcessingResult, RAGGenerationRequest, RAGGenerationResult
)
from ..services.openrouter_extraction_service import OpenRouterExtractionService
from ..services.vector_store import InMemoryVectorStore
from ..strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
from ..storage.database import DatabaseManager
from ..config.app_config import AppConfig
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


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


@dataclass
class ProcessingMetrics:
    """Metrics for document processing performance."""
    total_documents: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    average_processing_time: float = 0.0
    average_confidence_score: float = 0.0
    total_contexts_generated: int = 0
    quality_issues_detected: int = 0


class RefactoredDocumentProcessor:
    """
    Refactored document processor with enhanced RAG integration.
    
    Features:
    - OpenRouter-based extraction replacing legacy extraction logic
    - Enhanced RAG pipeline with improved context retrieval
    - Comprehensive metadata tracking and source reference management
    - Quality validation and confidence scoring
    - Integration with vector store and knowledge graph
    """
    
    def __init__(self,
                 config: Optional[DocumentProcessingConfig] = None,
                 openrouter_service: Optional[OpenRouterExtractionService] = None,
                 vector_store: Optional[InMemoryVectorStore] = None,
                 embedding_strategy: Optional[EmbeddingStrategy] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 database_manager: Optional[DatabaseManager] = None):
        """
        Initialize the refactored document processor.
        
        Args:
            config: Processing configuration
            openrouter_service: OpenRouter extraction service
            vector_store: Vector store for semantic search
            embedding_strategy: Strategy for generating embeddings
            kg_repository: Knowledge graph repository
            database_manager: Database manager for persistence
        """
        self.config = config or DocumentProcessingConfig()
        
        # Initialize services
        self.openrouter_service = openrouter_service or OpenRouterExtractionService()
        self.vector_store = vector_store or InMemoryVectorStore()
        
        # Initialize embedding strategy
        if embedding_strategy:
            self.embedding_strategy = embedding_strategy
        else:
            try:
                self.embedding_strategy = EmbeddingStrategyFactory.create_strategy('local')
            except Exception as e:
                logger.warning(f"Could not create embedding strategy: {e}")
                self.embedding_strategy = None
        
        # Initialize knowledge graph repository
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        
        # Initialize database manager
        if database_manager:
            self.database_manager = database_manager
        else:
            try:
                app_config = AppConfig.from_env()
                self.database_manager = DatabaseManager(app_config.database_path)
            except Exception as e:
                logger.warning(f"Could not initialize database manager: {e}")
                self.database_manager = None
        
        # Initialize enhanced RAG pipeline
        self.rag_pipeline = EnhancedRAGPipeline(
            openrouter_service=self.openrouter_service,
            vector_store=self.vector_store,
            embedding_strategy=self.embedding_strategy,
            kg_repository=self.kg_repository
        )
        
        # Processing metrics
        self.metrics = ProcessingMetrics()
        
        logger.info("Initialized RefactoredDocumentProcessor with enhanced RAG integration")
    
    def process_document(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Process a document using the enhanced RAG pipeline.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional processing options
            
        Returns:
            Dictionary containing processing results and metadata
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing document with enhanced pipeline: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            # Create extraction configuration
            extraction_config = self._create_extraction_config(file_path, kwargs)
            
            # Process document with enhanced RAG pipeline
            processing_result = self.rag_pipeline.process_document_with_enhanced_extraction(
                file_path, extraction_config
            )
            
            # Store results in database if available
            if self.database_manager and processing_result.success:
                self._store_processing_result(file_path, processing_result)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(processing_result, processing_time)
            
            # Prepare response
            response = {
                'success': processing_result.success,
                'document_id': processing_result.document_id,
                'extraction_result': self._serialize_extraction_result(processing_result.extraction_result),
                'quality_assessment': self._serialize_quality_assessment(processing_result.quality_assessment),
                'processing_metadata': {
                    'processing_time': processing_time,
                    'extraction_method': processing_result.processing_metadata.extraction_method,
                    'model_used': processing_result.processing_metadata.model_used,
                    'contexts_generated': len(processing_result.retrieval_contexts),
                    'confidence_score': processing_result.extraction_result.confidence_score
                },
                'retrieval_contexts_count': len(processing_result.retrieval_contexts),
                'source_references_count': len(processing_result.source_references),
                'error_message': processing_result.error_message
            }
            
            if processing_result.success:
                logger.info(f"Successfully processed document {file_path} in {processing_time:.2f}s")
            else:
                logger.error(f"Failed to process document {file_path}: {processing_result.error_message}")
            
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            logger.error(f"Error processing document {file_path}: {error_message}")
            
            # Update metrics for failure
            self.metrics.total_documents += 1
            self.metrics.failed_extractions += 1
            
            return {
                'success': False,
                'document_id': None,
                'extraction_result': {},
                'quality_assessment': {},
                'processing_metadata': {
                    'processing_time': processing_time,
                    'extraction_method': 'enhanced_rag_openrouter',
                    'error': error_message
                },
                'retrieval_contexts_count': 0,
                'source_references_count': 0,
                'error_message': error_message
            }
    
    def process_multiple_documents(self, file_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of document file paths
            **kwargs: Additional processing options
            
        Returns:
            Dictionary containing batch processing results
        """
        start_time = datetime.now()
        
        logger.info(f"Processing {len(file_paths)} documents in batch")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for file_path in file_paths:
            try:
                result = self.process_document(file_path, **kwargs)
                results.append({
                    'file_path': file_path,
                    'result': result
                })
                
                if result['success']:
                    successful_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing document {file_path} in batch: {str(e)}")
                results.append({
                    'file_path': file_path,
                    'result': {
                        'success': False,
                        'error_message': str(e)
                    }
                })
                failed_count += 1
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        batch_result = {
            'total_documents': len(file_paths),
            'successful_count': successful_count,
            'failed_count': failed_count,
            'success_rate': successful_count / len(file_paths) if file_paths else 0,
            'total_processing_time': total_time,
            'average_time_per_document': total_time / len(file_paths) if file_paths else 0,
            'results': results,
            'processing_metrics': self.get_processing_metrics()
        }
        
        logger.info(f"Batch processing completed: {successful_count}/{len(file_paths)} successful")
        
        return batch_result
    
    def generate_content_with_rag(self, query: str, document_context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate content using RAG with enhanced context retrieval.
        
        Args:
            query: Content generation query
            document_context: Document context information
            **kwargs: Additional generation options
            
        Returns:
            Dictionary containing generated content and metadata
        """
        try:
            logger.info(f"Generating RAG content for query: {query}")
            
            # Create RAG generation request
            request = RAGGenerationRequest(
                query=query,
                document_context=document_context,
                max_contexts=kwargs.get('max_contexts', 10),
                min_relevance_score=kwargs.get('min_relevance_score', 0.3)
            )
            
            # Generate content using RAG pipeline
            rag_result = self.rag_pipeline.generate_rag_content(request)
            
            # Prepare response
            response = {
                'success': True,
                'generated_content': rag_result.generated_content,
                'confidence_score': rag_result.confidence_score,
                'source_contexts_count': len(rag_result.source_contexts),
                'quality_metrics': rag_result.quality_metrics,
                'citations': rag_result.citations,
                'generation_metadata': rag_result.generation_metadata,
                'source_contexts': [
                    {
                        'text': ctx.text[:200] + '...' if len(ctx.text) > 200 else ctx.text,
                        'source': ctx.source,
                        'relevance_score': ctx.relevance_score,
                        'confidence_score': ctx.confidence_score
                    }
                    for ctx in rag_result.source_contexts[:5]  # Include top 5 contexts
                ]
            }
            
            logger.info(f"Generated RAG content with confidence: {rag_result.confidence_score:.2f}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating RAG content: {str(e)}")
            return {
                'success': False,
                'generated_content': '',
                'confidence_score': 0.0,
                'error_message': str(e)
            }
    
    def extract_qme_fields(self, document_path: str) -> Dict[str, Any]:
        """
        Extract QME fields using enhanced extraction pipeline.
        
        Args:
            document_path: Path to the document file
            
        Returns:
            Dictionary containing extracted QME fields
        """
        try:
            logger.info(f"Extracting QME fields from: {document_path}")
            
            # Create QME-specific extraction configuration
            extraction_config = ExtractionConfig(
                prompt_template="patient_info",
                extraction_method=ExtractionMethod.OPENROUTER_CLAUDE,
                quality_threshold=self.config.min_confidence_threshold,
                enable_vision=self.config.use_vision_extraction
            )
            
            # Process document
            processing_result = self.rag_pipeline.process_document_with_enhanced_extraction(
                document_path, extraction_config
            )
            
            if not processing_result.success:
                return {
                    'success': False,
                    'qme_fields': {},
                    'error_message': processing_result.error_message
                }
            
            # Extract QME-specific fields
            qme_fields = {}
            for field_name, field in processing_result.extraction_result.extracted_fields.items():
                if field.value and field.value != "NOT_FOUND":
                    qme_fields[field_name] = {
                        'value': field.value,
                        'confidence': field.confidence,
                        'source_location': field.source_location,
                        'validation_status': field.validation_status
                    }
            
            return {
                'success': True,
                'qme_fields': qme_fields,
                'extraction_metadata': {
                    'document_id': processing_result.document_id,
                    'extraction_method': processing_result.extraction_result.extraction_method,
                    'overall_confidence': processing_result.extraction_result.confidence_score,
                    'quality_score': processing_result.quality_assessment.overall_score,
                    'fields_extracted': len(qme_fields),
                    'processing_time': processing_result.processing_metadata.processing_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting QME fields: {str(e)}")
            return {
                'success': False,
                'qme_fields': {},
                'error_message': str(e)
            }
    
    def get_document_status(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get processing status of a document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document status or None if not found
        """
        try:
            if not self.database_manager:
                return None
            
            file_name = os.path.basename(file_path)
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, processing_status, upload_timestamp, 
                           updated_at, extracted_info
                    FROM documents 
                    WHERE title = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (file_name,))
                
                row = cursor.fetchone()
                if row:
                    extracted_info = {}
                    if row[5]:
                        try:
                            extracted_info = json.loads(row[5])
                        except:
                            pass
                    
                    return {
                        'id': row[0],
                        'title': row[1],
                        'status': row[2],
                        'uploaded': row[3],
                        'updated': row[4],
                        'extracted_info': extracted_info,
                        'processing_method': extracted_info.get('processing_method', 'unknown')
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting document status: {str(e)}")
            return None
    
    def list_processed_documents(self) -> List[Dict[str, Any]]:
        """
        List all processed documents.
        
        Returns:
            List of document information dictionaries
        """
        try:
            if not self.database_manager:
                return []
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, file_type, file_size, processing_status,
                           upload_timestamp, updated_at, extracted_info
                    FROM documents 
                    ORDER BY updated_at DESC
                """)
                
                documents = []
                for row in cursor.fetchall():
                    extracted_info = {}
                    if row[7]:
                        try:
                            extracted_info = json.loads(row[7])
                        except:
                            pass
                    
                    documents.append({
                        'id': row[0],
                        'title': row[1],
                        'file_type': row[2],
                        'file_size': row[3],
                        'status': row[4],
                        'uploaded': row[5],
                        'updated': row[6],
                        'processing_method': extracted_info.get('processing_method', 'unknown'),
                        'confidence_score': extracted_info.get('confidence_score', 0.0),
                        'contexts_generated': extracted_info.get('contexts_generated', 0)
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing performance metrics."""
        pipeline_stats = self.rag_pipeline.get_processing_statistics()
        
        return {
            'processor_metrics': {
                'total_documents': self.metrics.total_documents,
                'successful_extractions': self.metrics.successful_extractions,
                'failed_extractions': self.metrics.failed_extractions,
                'success_rate': (
                    self.metrics.successful_extractions / max(1, self.metrics.total_documents)
                ),
                'average_processing_time': self.metrics.average_processing_time,
                'average_confidence_score': self.metrics.average_confidence_score,
                'total_contexts_generated': self.metrics.total_contexts_generated,
                'quality_issues_detected': self.metrics.quality_issues_detected
            },
            'pipeline_metrics': pipeline_stats,
            'configuration': {
                'use_openrouter_extraction': self.config.use_openrouter_extraction,
                'use_vision_extraction': self.config.use_vision_extraction,
                'min_confidence_threshold': self.config.min_confidence_threshold,
                'max_contexts_per_document': self.config.max_contexts_per_document
            }
        }
    
    def _create_extraction_config(self, file_path: str, kwargs: Dict[str, Any]) -> ExtractionConfig:
        """Create extraction configuration for document processing."""
        return ExtractionConfig(
            prompt_template=kwargs.get('prompt_template', self.config.extraction_prompt_template),
            extraction_method=ExtractionMethod.OPENROUTER_CLAUDE,
            quality_threshold=kwargs.get('quality_threshold', self.config.min_confidence_threshold),
            enable_vision=kwargs.get('enable_vision', self.config.use_vision_extraction),
            max_retries=kwargs.get('max_retries', 3),
            timeout=kwargs.get('timeout', 60)
        )
    
    def _store_processing_result(self, file_path: str, processing_result: ProcessingResult) -> None:
        """Store processing result in database."""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_ext = Path(file_path).suffix.lower()[1:]  # Remove the dot
            
            # Prepare extracted info
            extracted_info = {
                'processing_method': 'enhanced_rag_openrouter',
                'confidence_score': processing_result.extraction_result.confidence_score,
                'quality_score': processing_result.quality_assessment.overall_score,
                'contexts_generated': len(processing_result.retrieval_contexts),
                'extraction_fields': {
                    name: {
                        'value': field.value,
                        'confidence': field.confidence,
                        'validation_status': field.validation_status
                    }
                    for name, field in processing_result.extraction_result.extracted_fields.items()
                },
                'processing_time': processing_result.processing_metadata.processing_time,
                'model_used': processing_result.processing_metadata.model_used,
                'file_path': file_path
            }
            
            with self.database_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if document already exists
                cursor.execute("SELECT id FROM documents WHERE title = ?", (file_name,))
                existing = cursor.fetchone()
                
                now = datetime.now()
                
                if existing:
                    # Update existing document
                    cursor.execute("""
                        UPDATE documents 
                        SET processing_status = ?, updated_at = ?, extracted_info = ?
                        WHERE id = ?
                    """, ('completed', now, json.dumps(extracted_info), existing[0]))
                else:
                    # Insert new document
                    cursor.execute("""
                        INSERT INTO documents (
                            id, title, file_type, file_size, processing_status,
                            upload_timestamp, created_at, updated_at, extracted_info
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        processing_result.document_id, file_name, file_ext, file_size,
                        'completed', now, now, now, json.dumps(extracted_info)
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing processing result: {str(e)}")
    
    def _update_metrics(self, processing_result: ProcessingResult, processing_time: float) -> None:
        """Update processing metrics."""
        self.metrics.total_documents += 1
        
        if processing_result.success:
            self.metrics.successful_extractions += 1
            
            # Update average confidence score
            current_avg = self.metrics.average_confidence_score
            total_successful = self.metrics.successful_extractions
            self.metrics.average_confidence_score = (
                (current_avg * (total_successful - 1) + processing_result.extraction_result.confidence_score) 
                / total_successful
            )
        else:
            self.metrics.failed_extractions += 1
        
        # Update average processing time
        current_avg_time = self.metrics.average_processing_time
        total_docs = self.metrics.total_documents
        self.metrics.average_processing_time = (
            (current_avg_time * (total_docs - 1) + processing_time) / total_docs
        )
        
        # Update contexts generated
        self.metrics.total_contexts_generated += len(processing_result.retrieval_contexts)
        
        # Count quality issues
        if processing_result.quality_assessment.identified_issues:
            self.metrics.quality_issues_detected += len(processing_result.quality_assessment.identified_issues)
    
    def _serialize_extraction_result(self, extraction_result) -> Dict[str, Any]:
        """Serialize extraction result for JSON response."""
        return {
            'document_id': extraction_result.document_id,
            'extraction_method': extraction_result.extraction_method,
            'confidence_score': extraction_result.confidence_score,
            'extracted_fields': {
                name: {
                    'value': field.value,
                    'confidence': field.confidence,
                    'source_location': field.source_location,
                    'validation_status': field.validation_status,
                    'notes': field.notes
                }
                for name, field in extraction_result.extracted_fields.items()
            },
            'processing_metadata': {
                'extraction_method': extraction_result.processing_metadata.extraction_method,
                'processing_time': extraction_result.processing_metadata.processing_time,
                'model_used': extraction_result.processing_metadata.model_used,
                'prompt_template': extraction_result.processing_metadata.prompt_template
            }
        }
    
    def _serialize_quality_assessment(self, quality_assessment) -> Dict[str, Any]:
        """Serialize quality assessment for JSON response."""
        return {
            'overall_score': quality_assessment.overall_score,
            'completeness_score': quality_assessment.completeness_score,
            'accuracy_score': quality_assessment.accuracy_score,
            'consistency_score': quality_assessment.consistency_score,
            'compliance_score': quality_assessment.compliance_score,
            'identified_issues': quality_assessment.identified_issues,
            'improvement_suggestions': quality_assessment.improvement_suggestions
        }


# Factory function for creating processor instances
def create_refactored_processor(config: Optional[DocumentProcessingConfig] = None) -> RefactoredDocumentProcessor:
    """
    Factory function to create a refactored document processor.
    
    Args:
        config: Processing configuration
        
    Returns:
        RefactoredDocumentProcessor instance
    """
    return RefactoredDocumentProcessor(config=config)


# Backward compatibility function
def process_document_simple(file_path: str) -> bool:
    """
    Backward compatibility function for simple document processing.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        processor = create_refactored_processor()
        result = processor.process_document(file_path)
        return result['success']
    except Exception as e:
        logger.error(f"Error in backward compatibility processing: {str(e)}")
        return False