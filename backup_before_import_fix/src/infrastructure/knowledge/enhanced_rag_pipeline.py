"""
Enhanced RAG Pipeline with OpenRouter Integration and Improved Context Retrieval.

This module implements an enhanced Retrieval-Augmented Generation pipeline that:
- Integrates OpenRouter-based extraction for superior document understanding
- Provides enhanced vector search with relevance scoring
- Implements processing metadata tracking and source reference management
- Supports multi-modal document processing with vision capabilities
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..models.extraction_models import (
    ExtractionResult, ExtractedField, QualityAssessment, 
    ProcessingMetadata, SourceReference, ExtractionConfig
)
from ..services.openrouter_extraction_service import OpenRouterExtractionService
from ..storage.vector_store import VectorDocument, InMemoryVectorStore
from ..strategies.embedding_strategy import EmbeddingStrategy
from ..repositories.knowledge_graph_repository import KnowledgeGraphRepository
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EnhancedRetrievalContext:
    """Enhanced context with OpenRouter-powered understanding."""
    text: str
    source: str
    relevance_score: float
    confidence_score: float
    extraction_method: str
    source_references: List[SourceReference]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult:
    """Result of enhanced document processing."""
    document_id: str
    extraction_result: ExtractionResult
    retrieval_contexts: List[EnhancedRetrievalContext]
    quality_assessment: QualityAssessment
    processing_metadata: ProcessingMetadata
    source_references: List[SourceReference]
    success: bool
    error_message: Optional[str] = None


@dataclass
class RAGGenerationRequest:
    """Request for RAG-based content generation."""
    query: str
    document_context: Dict[str, Any]
    extraction_data: Optional[ExtractionResult] = None
    context_filters: Optional[Dict[str, Any]] = None
    max_contexts: int = 10
    min_relevance_score: float = 0.3


@dataclass
class RAGGenerationResult:
    """Result of RAG-based content generation."""
    generated_content: str
    source_contexts: List[EnhancedRetrievalContext]
    confidence_score: float
    quality_metrics: Dict[str, float]
    generation_metadata: Dict[str, Any]
    citations: List[str]


class EnhancedRAGPipeline:
    """
    Enhanced RAG Pipeline with OpenRouter integration and improved context retrieval.
    
    Features:
    - OpenRouter-based document extraction with vision capabilities
    - Enhanced vector search with relevance scoring
    - Multi-source context retrieval (documents, knowledge graph, canonical sources)
    - Processing metadata tracking and source reference management
    - Quality validation and confidence scoring
    """
    
    def __init__(self,
                 openrouter_service: Optional[OpenRouterExtractionService] = None,
                 vector_store: Optional[InMemoryVectorStore] = None,
                 embedding_strategy: Optional[EmbeddingStrategy] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None):
        """
        Initialize the enhanced RAG pipeline.
        
        Args:
            openrouter_service: OpenRouter extraction service
            vector_store: Vector store for semantic search
            embedding_strategy: Strategy for generating embeddings
            kg_repository: Knowledge graph repository
        """
        self.openrouter_service = openrouter_service or OpenRouterExtractionService()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.embedding_strategy = embedding_strategy
        self.kg_repository = kg_repository
        
        # Processing statistics
        self.processing_stats = {
            'documents_processed': 0,
            'extraction_successes': 0,
            'extraction_failures': 0,
            'average_processing_time': 0.0,
            'total_contexts_generated': 0
        }
        
        logger.info("Initialized EnhancedRAGPipeline with OpenRouter integration")
    
    def process_document_with_enhanced_extraction(self, 
                                                document_path: str,
                                                extraction_config: ExtractionConfig) -> ProcessingResult:
        """
        Process document using enhanced OpenRouter extraction and RAG pipeline.
        
        Args:
            document_path: Path to the document file
            extraction_config: Configuration for extraction process
            
        Returns:
            ProcessingResult with extraction data and retrieval contexts
        """
        start_time = datetime.now()
        document_id = self._generate_document_id(document_path)
        
        try:
            logger.info(f"Processing document with enhanced extraction: {document_path}")
            
            # Step 1: Extract information using OpenRouter
            extraction_result = self.openrouter_service.extract_from_document(
                document_path, extraction_config
            )
            
            # Step 2: Validate extraction quality
            quality_assessment = self.openrouter_service.validate_extraction_quality(extraction_result)
            
            # Step 3: Generate enhanced retrieval contexts
            retrieval_contexts = self._generate_enhanced_contexts(
                extraction_result, document_path
            )
            
            # Step 4: Store in vector store for future retrieval
            self._store_in_vector_store(document_id, extraction_result, retrieval_contexts)
            
            # Step 5: Update knowledge graph if available
            if self.kg_repository:
                self._update_knowledge_graph(document_id, extraction_result, retrieval_contexts)
            
            # Calculate processing metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_metadata = ProcessingMetadata(
                extraction_method="enhanced_rag_openrouter",
                processing_time=processing_time,
                model_used=extraction_result.processing_metadata.model_used,
                prompt_template=extraction_config.prompt_template,
                api_version="v1"
            )
            
            # Update statistics
            self._update_processing_stats(processing_time, True, len(retrieval_contexts))
            
            result = ProcessingResult(
                document_id=document_id,
                extraction_result=extraction_result,
                retrieval_contexts=retrieval_contexts,
                quality_assessment=quality_assessment,
                processing_metadata=processing_metadata,
                source_references=extraction_result.source_references,
                success=True
            )
            
            logger.info(f"Successfully processed document {document_path} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_processing_stats(processing_time, False, 0)
            
            logger.error(f"Error processing document {document_path}: {str(e)}")
            
            return ProcessingResult(
                document_id=document_id,
                extraction_result=ExtractionResult(
                    document_id=document_id,
                    extraction_method="enhanced_rag_openrouter",
                    confidence_score=0.0,
                    extracted_fields={},
                    quality_assessment=QualityAssessment(
                        overall_score=0.0,
                        completeness_score=0.0,
                        accuracy_score=0.0,
                        consistency_score=0.0,
                        compliance_score=0.0,
                        identified_issues=[f"Processing failed: {str(e)}"],
                        improvement_suggestions=[],
                        confidence_intervals={}
                    ),
                    processing_metadata=ProcessingMetadata(
                        extraction_method="enhanced_rag_openrouter",
                        processing_time=processing_time,
                        model_used="unknown",
                        prompt_template="unknown",
                        api_version="v1"
                    ),
                    source_references=[],
                    validation_results=[]
                ),
                retrieval_contexts=[],
                quality_assessment=QualityAssessment(
                    overall_score=0.0,
                    completeness_score=0.0,
                    accuracy_score=0.0,
                    consistency_score=0.0,
                    compliance_score=0.0,
                    identified_issues=[f"Processing failed: {str(e)}"],
                    improvement_suggestions=[],
                    confidence_intervals={}
                ),
                processing_metadata=ProcessingMetadata(
                    extraction_method="enhanced_rag_openrouter",
                    processing_time=processing_time,
                    model_used="unknown",
                    prompt_template="unknown",
                    api_version="v1"
                ),
                source_references=[],
                success=False,
                error_message=str(e)
            )
    
    def retrieve_enhanced_context(self, 
                                query: str,
                                document_context: Dict[str, Any],
                                max_contexts: int = 10,
                                min_relevance_score: float = 0.3) -> List[EnhancedRetrievalContext]:
        """
        Retrieve enhanced context using multiple retrieval strategies.
        
        Args:
            query: Search query
            document_context: Document context information
            max_contexts: Maximum number of contexts to return
            min_relevance_score: Minimum relevance score threshold
            
        Returns:
            List of enhanced retrieval contexts
        """
        try:
            logger.debug(f"Retrieving enhanced context for query: {query}")
            
            contexts = []
            
            # Strategy 1: Vector similarity search
            if self.embedding_strategy:
                vector_contexts = self._vector_similarity_search(
                    query, max_contexts // 2, min_relevance_score
                )
                contexts.extend(vector_contexts)
            
            # Strategy 2: Knowledge graph traversal
            if self.kg_repository:
                graph_contexts = self._knowledge_graph_search(
                    query, document_context, max_contexts // 3
                )
                contexts.extend(graph_contexts)
            
            # Strategy 3: Semantic chunking search
            semantic_contexts = self._semantic_chunk_search(
                query, document_context, max_contexts // 3
            )
            contexts.extend(semantic_contexts)
            
            # Deduplicate and rank contexts
            unique_contexts = self._deduplicate_contexts(contexts)
            ranked_contexts = self._rank_contexts_by_relevance(unique_contexts, query)
            
            # Filter by minimum relevance score
            filtered_contexts = [
                ctx for ctx in ranked_contexts 
                if ctx.relevance_score >= min_relevance_score
            ]
            
            # Return top contexts
            result_contexts = filtered_contexts[:max_contexts]
            
            logger.debug(f"Retrieved {len(result_contexts)} enhanced contexts")
            return result_contexts
            
        except Exception as e:
            logger.error(f"Error retrieving enhanced context: {str(e)}")
            return []
    
    def generate_rag_content(self, request: RAGGenerationRequest) -> RAGGenerationResult:
        """
        Generate content using RAG with enhanced context retrieval.
        
        Args:
            request: RAG generation request
            
        Returns:
            RAG generation result with content and metadata
        """
        try:
            logger.info(f"Generating RAG content for query: {request.query}")
            
            # Retrieve enhanced contexts
            contexts = self.retrieve_enhanced_context(
                request.query,
                request.document_context,
                request.max_contexts,
                request.min_relevance_score
            )
            
            if not contexts:
                return RAGGenerationResult(
                    generated_content="No relevant context found for the query.",
                    source_contexts=[],
                    confidence_score=0.0,
                    quality_metrics={'context_coverage': 0.0, 'source_diversity': 0.0},
                    generation_metadata={'error': 'No contexts retrieved'},
                    citations=[]
                )
            
            # Generate content using OpenRouter if available
            if hasattr(self.openrouter_service, 'generate_content'):
                generated_content = self._generate_content_with_openrouter(
                    request.query, contexts
                )
            else:
                generated_content = self._generate_content_fallback(
                    request.query, contexts
                )
            
            # Calculate quality metrics
            quality_metrics = self._calculate_generation_quality_metrics(
                generated_content, contexts
            )
            
            # Extract citations
            citations = self._extract_citations_from_contexts(contexts)
            
            # Calculate overall confidence
            confidence_score = self._calculate_generation_confidence(
                contexts, quality_metrics
            )
            
            result = RAGGenerationResult(
                generated_content=generated_content,
                source_contexts=contexts,
                confidence_score=confidence_score,
                quality_metrics=quality_metrics,
                generation_metadata={
                    'num_contexts_used': len(contexts),
                    'generation_method': 'enhanced_rag_openrouter',
                    'timestamp': datetime.now().isoformat()
                },
                citations=citations
            )
            
            logger.info(f"Generated RAG content with {len(contexts)} contexts, confidence: {confidence_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating RAG content: {str(e)}")
            return RAGGenerationResult(
                generated_content=f"Error generating content: {str(e)}",
                source_contexts=[],
                confidence_score=0.0,
                quality_metrics={'error': 1.0},
                generation_metadata={'error': str(e)},
                citations=[]
            )
    
    def _generate_enhanced_contexts(self, 
                                  extraction_result: ExtractionResult,
                                  document_path: str) -> List[EnhancedRetrievalContext]:
        """Generate enhanced retrieval contexts from extraction result."""
        contexts = []
        
        try:
            # Create contexts from extracted fields
            for field_name, field in extraction_result.extracted_fields.items():
                if field.value and field.value != "NOT_FOUND":
                    context = EnhancedRetrievalContext(
                        text=f"{field_name}: {field.value}",
                        source=f"OpenRouter Extraction - {field_name}",
                        relevance_score=field.confidence,
                        confidence_score=field.confidence,
                        extraction_method="openrouter_claude_3_5_sonnet",
                        source_references=[
                            SourceReference(
                                field_name=field_name,
                                source_location=field.source_location or "openrouter_extraction",
                                confidence=field.confidence,
                                extraction_method="openrouter_claude_3_5_sonnet",
                                page_number=None,
                                section_name=field_name
                            )
                        ],
                        metadata={
                            'field_name': field_name,
                            'validation_status': field.validation_status,
                            'source_location': field.source_location,
                            'notes': field.notes,
                            'document_path': document_path
                        }
                    )
                    contexts.append(context)
            
            # Create context from overall document analysis
            if extraction_result.quality_assessment.overall_score > 0.5:
                document_context = EnhancedRetrievalContext(
                    text=f"Document analysis with {len(extraction_result.extracted_fields)} fields extracted. "
                         f"Overall quality score: {extraction_result.quality_assessment.overall_score:.2f}",
                    source="Document Analysis Summary",
                    relevance_score=extraction_result.quality_assessment.overall_score,
                    confidence_score=extraction_result.confidence_score,
                    extraction_method="openrouter_claude_3_5_sonnet",
                    source_references=extraction_result.source_references,
                    metadata={
                        'document_id': extraction_result.document_id,
                        'extraction_method': extraction_result.extraction_method,
                        'processing_time': extraction_result.processing_metadata.processing_time,
                        'model_used': extraction_result.processing_metadata.model_used,
                        'document_path': document_path
                    }
                )
                contexts.append(document_context)
            
            logger.debug(f"Generated {len(contexts)} enhanced contexts from extraction result")
            return contexts
            
        except Exception as e:
            logger.error(f"Error generating enhanced contexts: {str(e)}")
            return []
    
    def _vector_similarity_search(self, 
                                query: str,
                                max_results: int,
                                min_similarity: float) -> List[EnhancedRetrievalContext]:
        """Perform vector similarity search."""
        contexts = []
        
        try:
            if not self.embedding_strategy:
                return contexts
            
            # Search in vector store
            results = self.vector_store.search_by_text(
                query, self.embedding_strategy, max_results, min_similarity
            )
            
            for doc, similarity in results:
                context = EnhancedRetrievalContext(
                    text=doc.text,
                    source=f"Vector Search - {doc.metadata.get('source', 'Unknown')}",
                    relevance_score=similarity,
                    confidence_score=doc.metadata.get('confidence', 0.8),
                    extraction_method="vector_similarity",
                    source_references=[
                        SourceReference(
                            field_name="vector_search_result",
                            source_location=doc.metadata.get('source', 'vector_store'),
                            confidence=similarity,
                            extraction_method="vector_similarity",
                            page_number=doc.metadata.get('page_number'),
                            section_name=doc.metadata.get('section')
                        )
                    ],
                    metadata={
                        'similarity_score': similarity,
                        'doc_id': doc.id,
                        **doc.metadata
                    }
                )
                contexts.append(context)
            
            logger.debug(f"Vector search returned {len(contexts)} contexts")
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {str(e)}")
        
        return contexts
    
    def _knowledge_graph_search(self, 
                              query: str,
                              document_context: Dict[str, Any],
                              max_results: int) -> List[EnhancedRetrievalContext]:
        """Search knowledge graph for relevant contexts."""
        contexts = []
        
        try:
            if not self.kg_repository:
                return contexts
            
            # Search for relevant nodes based on query terms
            query_terms = query.lower().split()
            
            # Find nodes by type based on query content
            if any(term in query_terms for term in ['diagnosis', 'condition', 'disease']):
                diagnosis_nodes = self.kg_repository.find_nodes_by_type('diagnosis')
                for node in diagnosis_nodes[:max_results//3]:
                    context = self._create_context_from_kg_node(node, 'diagnosis')
                    if context:
                        contexts.append(context)
            
            if any(term in query_terms for term in ['impairment', 'rating', 'disability']):
                impairment_nodes = self.kg_repository.find_nodes_by_type('impairment_rating')
                for node in impairment_nodes[:max_results//3]:
                    context = self._create_context_from_kg_node(node, 'impairment_rating')
                    if context:
                        contexts.append(context)
            
            if any(term in query_terms for term in ['finding', 'examination', 'test']):
                finding_nodes = self.kg_repository.find_nodes_by_type('finding')
                for node in finding_nodes[:max_results//3]:
                    context = self._create_context_from_kg_node(node, 'finding')
                    if context:
                        contexts.append(context)
            
            logger.debug(f"Knowledge graph search returned {len(contexts)} contexts")
            
        except Exception as e:
            logger.error(f"Error in knowledge graph search: {str(e)}")
        
        return contexts
    
    def _semantic_chunk_search(self, 
                             query: str,
                             document_context: Dict[str, Any],
                             max_results: int) -> List[EnhancedRetrievalContext]:
        """Search semantic chunks for relevant contexts."""
        contexts = []
        
        try:
            # This is a placeholder for semantic chunk search
            # In a full implementation, this would search through
            # semantically chunked document content
            
            # For now, create contexts from document_context if available
            if 'original_text' in document_context:
                text = document_context['original_text']
                if text and len(text) > 100:
                    # Simple chunking by paragraphs
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    
                    query_terms = set(query.lower().split())
                    
                    for i, paragraph in enumerate(paragraphs[:max_results]):
                        paragraph_terms = set(paragraph.lower().split())
                        overlap = len(query_terms.intersection(paragraph_terms))
                        
                        if overlap > 0:
                            relevance_score = overlap / len(query_terms)
                            
                            context = EnhancedRetrievalContext(
                                text=paragraph,
                                source=f"Semantic Chunk {i+1}",
                                relevance_score=relevance_score,
                                confidence_score=0.7,
                                extraction_method="semantic_chunking",
                                source_references=[
                                    SourceReference(
                                        field_name="semantic_chunk",
                                        source_location=f"chunk_{i}",
                                        confidence=relevance_score,
                                        extraction_method="semantic_chunking",
                                        page_number=None,
                                        section_name=f"chunk_{i}"
                                    )
                                ],
                                metadata={
                                    'chunk_index': i,
                                    'term_overlap': overlap,
                                    'chunk_length': len(paragraph)
                                }
                            )
                            contexts.append(context)
            
            logger.debug(f"Semantic chunk search returned {len(contexts)} contexts")
            
        except Exception as e:
            logger.error(f"Error in semantic chunk search: {str(e)}")
        
        return contexts
    
    def _create_context_from_kg_node(self, node, node_type: str) -> Optional[EnhancedRetrievalContext]:
        """Create enhanced context from knowledge graph node."""
        try:
            description = node.properties.get('description', 'No description available')
            
            context_text = f"{node_type.title()}: {description}"
            
            # Add additional information based on node type
            if node_type == 'impairment_rating':
                if 'percentage' in node.properties:
                    context_text += f" (Rating: {node.properties['percentage']}%)"
                if 'ama_table' in node.properties:
                    context_text += f" [AMA Table: {node.properties['ama_table']}]"
            
            return EnhancedRetrievalContext(
                text=context_text,
                source=f"Knowledge Graph - {node_type}",
                relevance_score=0.8,
                confidence_score=node.properties.get('confidence', 0.9),
                extraction_method="knowledge_graph_traversal",
                source_references=[
                    SourceReference(
                        field_name="knowledge_graph_node",
                        source_location=node_type,
                        confidence=node.properties.get('confidence', 0.9),
                        extraction_method="knowledge_graph_traversal",
                        page_number=node.properties.get('page_reference'),
                        section_name=node_type
                    )
                ],
                metadata={
                    'node_id': node.id,
                    'node_type': node_type,
                    **node.properties
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating context from KG node: {str(e)}")
            return None
    
    def _store_in_vector_store(self, 
                             document_id: str,
                             extraction_result: ExtractionResult,
                             contexts: List[EnhancedRetrievalContext]) -> None:
        """Store extraction results and contexts in vector store."""
        try:
            if not self.embedding_strategy:
                return
            
            # Store each context as a vector document
            for i, context in enumerate(contexts):
                try:
                    # Generate embeddings for the context text
                    embeddings = self.embedding_strategy.generate_embeddings(context.text)
                    
                    # Create vector document
                    doc_id = f"{document_id}_context_{i}"
                    
                    self.vector_store.add_document(
                        doc_id=doc_id,
                        text=context.text,
                        embeddings=embeddings,
                        metadata={
                            'document_id': document_id,
                            'context_index': i,
                            'source': context.source,
                            'relevance_score': context.relevance_score,
                            'confidence_score': context.confidence_score,
                            'extraction_method': context.extraction_method,
                            **context.metadata
                        }
                    )
                    
                except Exception as e:
                    logger.warning(f"Error storing context {i} in vector store: {str(e)}")
            
            logger.debug(f"Stored {len(contexts)} contexts in vector store for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing in vector store: {str(e)}")
    
    def _update_knowledge_graph(self, 
                              document_id: str,
                              extraction_result: ExtractionResult,
                              contexts: List[EnhancedRetrievalContext]) -> None:
        """Update knowledge graph with extraction results."""
        try:
            # This is a placeholder for knowledge graph updates
            # In a full implementation, this would create nodes and relationships
            # based on the extraction results
            
            logger.debug(f"Updated knowledge graph for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {str(e)}")
    
    def _deduplicate_contexts(self, contexts: List[EnhancedRetrievalContext]) -> List[EnhancedRetrievalContext]:
        """Remove duplicate contexts based on text similarity."""
        if not contexts:
            return contexts
        
        unique_contexts = []
        seen_texts = set()
        
        for context in contexts:
            # Simple deduplication based on first 100 characters
            text_key = context.text.strip().lower()[:100]
            
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_contexts.append(context)
        
        return unique_contexts
    
    def _rank_contexts_by_relevance(self, 
                                  contexts: List[EnhancedRetrievalContext],
                                  query: str) -> List[EnhancedRetrievalContext]:
        """Rank contexts by relevance to query."""
        try:
            # Calculate enhanced relevance scores
            for context in contexts:
                # Combine multiple relevance factors
                base_score = context.relevance_score
                confidence_bonus = context.confidence_score * 0.2
                
                # Text overlap bonus
                query_terms = set(query.lower().split())
                context_terms = set(context.text.lower().split())
                overlap_ratio = len(query_terms.intersection(context_terms)) / len(query_terms) if query_terms else 0
                overlap_bonus = overlap_ratio * 0.3
                
                # Source quality bonus
                source_bonus = 0.1 if 'openrouter' in context.extraction_method.lower() else 0
                
                # Calculate final relevance score
                context.relevance_score = min(1.0, base_score + confidence_bonus + overlap_bonus + source_bonus)
            
            # Sort by relevance score
            contexts.sort(key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error ranking contexts: {str(e)}")
        
        return contexts
    
    def _generate_content_with_openrouter(self, 
                                        query: str,
                                        contexts: List[EnhancedRetrievalContext]) -> str:
        """Generate content using OpenRouter (placeholder)."""
        # This is a placeholder for OpenRouter content generation
        # In a full implementation, this would use OpenRouter's generation capabilities
        
        context_text = "\n\n".join([
            f"Source: {ctx.source}\nContent: {ctx.text}"
            for ctx in contexts[:5]  # Use top 5 contexts
        ])
        
        return f"Based on the available information:\n\n{context_text}\n\nQuery: {query}\n\n" \
               f"Generated response would be created here using OpenRouter's generation capabilities."
    
    def _generate_content_fallback(self, 
                                 query: str,
                                 contexts: List[EnhancedRetrievalContext]) -> str:
        """Fallback content generation method."""
        if not contexts:
            return "No relevant information found to answer the query."
        
        # Simple template-based generation
        context_summaries = []
        for ctx in contexts[:3]:  # Use top 3 contexts
            summary = f"From {ctx.source}: {ctx.text[:200]}..."
            context_summaries.append(summary)
        
        return f"Based on the available information:\n\n" + "\n\n".join(context_summaries)
    
    def _calculate_generation_quality_metrics(self, 
                                            content: str,
                                            contexts: List[EnhancedRetrievalContext]) -> Dict[str, float]:
        """Calculate quality metrics for generated content."""
        try:
            metrics = {}
            
            # Context coverage - how well the content uses available contexts
            if contexts:
                context_terms = set()
                for ctx in contexts:
                    context_terms.update(ctx.text.lower().split())
                
                content_terms = set(content.lower().split())
                coverage = len(context_terms.intersection(content_terms)) / len(context_terms) if context_terms else 0
                metrics['context_coverage'] = coverage
            else:
                metrics['context_coverage'] = 0.0
            
            # Source diversity - variety of sources used
            if contexts:
                unique_sources = len(set(ctx.source for ctx in contexts))
                metrics['source_diversity'] = min(1.0, unique_sources / 5.0)  # Normalize to max 5 sources
            else:
                metrics['source_diversity'] = 0.0
            
            # Content length appropriateness
            content_length = len(content.split())
            if 50 <= content_length <= 500:  # Appropriate length range
                metrics['length_appropriateness'] = 1.0
            elif content_length < 50:
                metrics['length_appropriateness'] = content_length / 50.0
            else:
                metrics['length_appropriateness'] = max(0.5, 500.0 / content_length)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {str(e)}")
            return {'error': 1.0}
    
    def _extract_citations_from_contexts(self, contexts: List[EnhancedRetrievalContext]) -> List[str]:
        """Extract citations from contexts."""
        citations = []
        
        for ctx in contexts:
            for ref in ctx.source_references:
                if ref.page_number:
                    citation = f"{ctx.source}, p. {ref.page_number}"
                else:
                    citation = ctx.source
                
                if citation not in citations:
                    citations.append(citation)
        
        return citations
    
    def _calculate_generation_confidence(self, 
                                       contexts: List[EnhancedRetrievalContext],
                                       quality_metrics: Dict[str, float]) -> float:
        """Calculate overall confidence for generated content."""
        try:
            if not contexts:
                return 0.0
            
            # Average context confidence
            avg_context_confidence = sum(ctx.confidence_score for ctx in contexts) / len(contexts)
            
            # Quality metrics contribution
            quality_score = sum(quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0.0
            
            # Number of contexts bonus (more contexts = higher confidence, up to a point)
            context_bonus = min(0.2, len(contexts) * 0.05)
            
            # Calculate final confidence
            confidence = (avg_context_confidence * 0.5 + quality_score * 0.3 + context_bonus)
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating generation confidence: {str(e)}")
            return 0.0
    
    def _generate_document_id(self, document_path: str) -> str:
        """Generate unique document ID."""
        import hashlib
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"doc_{timestamp}_{path_hash}"
    
    def _update_processing_stats(self, processing_time: float, success: bool, num_contexts: int) -> None:
        """Update processing statistics."""
        self.processing_stats['documents_processed'] += 1
        
        if success:
            self.processing_stats['extraction_successes'] += 1
        else:
            self.processing_stats['extraction_failures'] += 1
        
        # Update average processing time
        current_avg = self.processing_stats['average_processing_time']
        total_docs = self.processing_stats['documents_processed']
        self.processing_stats['average_processing_time'] = (
            (current_avg * (total_docs - 1) + processing_time) / total_docs
        )
        
        self.processing_stats['total_contexts_generated'] += num_contexts
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self.processing_stats,
            'success_rate': (
                self.processing_stats['extraction_successes'] / 
                max(1, self.processing_stats['documents_processed'])
            ),
            'average_contexts_per_document': (
                self.processing_stats['total_contexts_generated'] / 
                max(1, self.processing_stats['documents_processed'])
            )
        }