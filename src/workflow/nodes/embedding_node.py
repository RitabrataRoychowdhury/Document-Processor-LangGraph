"""Vector embedding generation workflow node."""

import hashlib
from typing import Dict, Any, List, Optional

from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.strategies.embedding_strategy import EmbeddingStrategy, LocalEmbeddingStrategy
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingNode(WorkflowNode):
    """Node for vector embedding generation.
    
    Implements Single Responsibility Principle - handles only embedding generation.
    Follows Dependency Inversion - depends on EmbeddingStrategy abstraction.
    """
    
    def __init__(self, embedding_strategy: EmbeddingStrategy = None,
                 chunk_size: int = 1000, chunk_overlap: int = 200,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        # Use dependency injection - don't create default if not provided
        if embedding_strategy is None:
            raise ValueError("EmbeddingStrategy must be provided via dependency injection")
        self.embedding_strategy = embedding_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute embedding generation."""
        try:
            extracted_text = state['extracted_text']
            entities = state.get('entities_extracted', [])
            
            logger.info(f"Starting embedding generation for {len(extracted_text)} characters "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Chunk the text for better embedding quality
            text_chunks = self._chunk_text(extracted_text)
            
            # Generate embeddings for text chunks
            chunk_embeddings = []
            for i, chunk in enumerate(text_chunks):
                try:
                    embedding = self.embedding_strategy.generate_embeddings(chunk)
                    chunk_embeddings.append({
                        'chunk_id': i,
                        'text': chunk,
                        'embedding': embedding,
                        'start_pos': self._get_chunk_start_position(extracted_text, chunk, i),
                        'length': len(chunk)
                    })
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {i}: {e}")
                    continue
            
            # Generate embeddings for entities
            entity_embeddings = []
            for entity in entities:
                try:
                    entity_text = entity.get('text', '')
                    if len(entity_text.strip()) > 3:  # Only embed meaningful entities
                        embedding = self.embedding_strategy.generate_embeddings(entity_text)
                        entity_embeddings.append({
                            'entity_type': entity.get('type'),
                            'entity_text': entity_text,
                            'embedding': embedding,
                            'confidence': entity.get('confidence', 0.0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for entity '{entity_text}': {e}")
                    continue
            
            # Generate document-level embedding (average of chunk embeddings)
            document_embedding = self._generate_document_embedding(chunk_embeddings)
            
            # Calculate embedding statistics
            embedding_stats = {
                'total_chunks': len(text_chunks),
                'successful_chunk_embeddings': len(chunk_embeddings),
                'total_entities': len(entities),
                'successful_entity_embeddings': len(entity_embeddings),
                'embedding_dimension': len(document_embedding) if document_embedding else 0,
                'average_chunk_size': sum(len(chunk) for chunk in text_chunks) / len(text_chunks) if text_chunks else 0
            }
            
            result_data = {
                'document_embedding': document_embedding,
                'chunk_embeddings': chunk_embeddings,
                'entity_embeddings': entity_embeddings,
                'embedding_statistics': embedding_stats,
                'embedding_strategy': self.embedding_strategy.__class__.__name__,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
            
            logger.info(f"Embedding generation completed: {len(chunk_embeddings)} chunk embeddings, "
                       f"{len(entity_embeddings)} entity embeddings "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Embedding generation completed: {len(chunk_embeddings)} chunks, {len(entity_embeddings)} entities",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Embedding generation failed: {str(e)}",
                error=e
            )
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the overlap region
                sentence_end = text.rfind('.', end - self.chunk_overlap, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _get_chunk_start_position(self, full_text: str, chunk: str, chunk_index: int) -> int:
        """Get the start position of a chunk in the full text."""
        try:
            # Simple approach: find the chunk in the text
            # This might not be perfect for overlapping chunks, but gives an approximation
            return full_text.find(chunk[:50])  # Use first 50 chars to find position
        except:
            # Fallback: estimate based on chunk index
            return chunk_index * (self.chunk_size - self.chunk_overlap)
    
    def _generate_document_embedding(self, chunk_embeddings: List[Dict[str, Any]]) -> Optional[List[float]]:
        """Generate document-level embedding by averaging chunk embeddings."""
        if not chunk_embeddings:
            return None
        
        try:
            # Get embedding dimension from first chunk
            first_embedding = chunk_embeddings[0]['embedding']
            if not first_embedding:
                return None
            
            embedding_dim = len(first_embedding)
            
            # Average all chunk embeddings
            document_embedding = [0.0] * embedding_dim
            valid_chunks = 0
            
            for chunk_data in chunk_embeddings:
                embedding = chunk_data.get('embedding')
                if embedding and len(embedding) == embedding_dim:
                    for i, value in enumerate(embedding):
                        document_embedding[i] += value
                    valid_chunks += 1
            
            if valid_chunks > 0:
                # Normalize by number of chunks
                document_embedding = [value / valid_chunks for value in document_embedding]
                return document_embedding
            
        except Exception as e:
            logger.warning(f"Failed to generate document embedding: {e}")
        
        return None
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state for embedding generation."""
        required_keys = self.get_required_inputs()
        
        for key in required_keys:
            if key not in state:
                logger.error(f"Missing required input key: {key}")
                return False
        
        extracted_text = state.get('extracted_text')
        if not isinstance(extracted_text, str) or len(extracted_text.strip()) < 10:
            logger.error("Invalid extracted_text: must be a string with at least 10 characters")
            return False
        
        return True
    
    def get_required_inputs(self) -> List[str]:
        """Get required input keys."""
        return ['extracted_text']
    
    def get_output_keys(self) -> List[str]:
        """Get output keys this node adds to state."""
        return [
            'document_embedding',
            'chunk_embeddings',
            'entity_embeddings',
            'embedding_statistics',
            'embedding_strategy',
            'chunk_size',
            'chunk_overlap'
        ]
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if embedding generation can be retried."""
        # Embedding generation is generally retryable for network/API errors
        non_retryable_errors = (ValueError, TypeError)
        return not isinstance(error, non_retryable_errors)


class CachedEmbeddingNode(EmbeddingNode):
    """Embedding node with caching capabilities.
    
    Extends EmbeddingNode with caching to avoid regenerating embeddings for the same content.
    """
    
    def __init__(self, embedding_strategy: EmbeddingStrategy = None,
                 chunk_size: int = 1000, chunk_overlap: int = 200,
                 enable_cache: bool = True,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(embedding_strategy, chunk_size, chunk_overlap, node_id, correlation_id)
        self.enable_cache = enable_cache
        self._embedding_cache: Dict[str, List[float]] = {}
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute embedding generation with caching."""
        if not self.enable_cache:
            return super().execute(state)
        
        try:
            extracted_text = state['extracted_text']
            
            # Check if we have cached embeddings for this text
            text_hash = self._get_text_hash(extracted_text)
            
            if text_hash in self._embedding_cache:
                logger.info(f"Using cached embeddings for text hash {text_hash[:8]}... "
                           f"[correlation_id: {self.correlation_id}]")
                
                cached_embedding = self._embedding_cache[text_hash]
                
                result_data = {
                    'document_embedding': cached_embedding,
                    'chunk_embeddings': [],  # Not cached for simplicity
                    'entity_embeddings': [],  # Not cached for simplicity
                    'embedding_statistics': {
                        'total_chunks': 1,
                        'successful_chunk_embeddings': 1,
                        'embedding_dimension': len(cached_embedding),
                        'cache_hit': True
                    },
                    'embedding_strategy': f"Cached_{self.embedding_strategy.__class__.__name__}",
                    'chunk_size': self.chunk_size,
                    'chunk_overlap': self.chunk_overlap
                }
                
                return NodeResult.success_result(
                    "Embedding generation completed using cache",
                    data=result_data
                )
            
            # Generate embeddings normally
            result = super().execute(state)
            
            # Cache the document embedding if successful
            if result.success and 'document_embedding' in result.data:
                document_embedding = result.data['document_embedding']
                if document_embedding:
                    self._embedding_cache[text_hash] = document_embedding
                    logger.debug(f"Cached embedding for text hash {text_hash[:8]}...")
                    
                    # Update statistics to indicate caching
                    if 'embedding_statistics' in result.data:
                        result.data['embedding_statistics']['cache_hit'] = False
                        result.data['embedding_statistics']['cached'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Cached embedding generation failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Cached embedding generation failed: {str(e)}",
                error=e
            )
    
    def _get_text_hash(self, text: str) -> str:
        """Generate a hash for the text content."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Cleared embedding cache")
    
    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._embedding_cache)
    
    def get_output_keys(self) -> List[str]:
        """Get output keys including cache-specific keys."""
        base_keys = super().get_output_keys()
        return base_keys + ['cache_hit', 'cached']


class BatchEmbeddingNode(EmbeddingNode):
    """Embedding node optimized for batch processing.
    
    Extends EmbeddingNode with batch processing capabilities for better performance.
    """
    
    def __init__(self, embedding_strategy: EmbeddingStrategy = None,
                 chunk_size: int = 1000, chunk_overlap: int = 200,
                 batch_size: int = 10,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(embedding_strategy, chunk_size, chunk_overlap, node_id, correlation_id)
        self.batch_size = batch_size
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute batch embedding generation."""
        try:
            extracted_text = state['extracted_text']
            entities = state.get('entities_extracted', [])
            
            logger.info(f"Starting batch embedding generation for {len(extracted_text)} characters "
                       f"[correlation_id: {self.correlation_id}]")
            
            # Chunk the text
            text_chunks = self._chunk_text(extracted_text)
            
            # Process chunks in batches
            chunk_embeddings = []
            for i in range(0, len(text_chunks), self.batch_size):
                batch_chunks = text_chunks[i:i + self.batch_size]
                batch_embeddings = self._process_chunk_batch(batch_chunks, i)
                chunk_embeddings.extend(batch_embeddings)
            
            # Process entities in batches
            entity_embeddings = []
            entity_texts = [entity.get('text', '') for entity in entities if len(entity.get('text', '').strip()) > 3]
            
            for i in range(0, len(entity_texts), self.batch_size):
                batch_entities = entity_texts[i:i + self.batch_size]
                batch_entity_data = entities[i:i + self.batch_size]
                batch_embeddings = self._process_entity_batch(batch_entities, batch_entity_data)
                entity_embeddings.extend(batch_embeddings)
            
            # Generate document-level embedding
            document_embedding = self._generate_document_embedding(chunk_embeddings)
            
            # Calculate statistics
            embedding_stats = {
                'total_chunks': len(text_chunks),
                'successful_chunk_embeddings': len(chunk_embeddings),
                'total_entities': len(entities),
                'successful_entity_embeddings': len(entity_embeddings),
                'embedding_dimension': len(document_embedding) if document_embedding else 0,
                'batch_size': self.batch_size,
                'batches_processed': (len(text_chunks) + self.batch_size - 1) // self.batch_size
            }
            
            result_data = {
                'document_embedding': document_embedding,
                'chunk_embeddings': chunk_embeddings,
                'entity_embeddings': entity_embeddings,
                'embedding_statistics': embedding_stats,
                'embedding_strategy': f"Batch_{self.embedding_strategy.__class__.__name__}",
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'batch_size': self.batch_size
            }
            
            logger.info(f"Batch embedding generation completed: {len(chunk_embeddings)} chunk embeddings, "
                       f"{len(entity_embeddings)} entity embeddings "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Batch embedding generation completed: {len(chunk_embeddings)} chunks, {len(entity_embeddings)} entities",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Batch embedding generation failed: {str(e)}",
                error=e
            )
    
    def _process_chunk_batch(self, chunks: List[str], start_index: int) -> List[Dict[str, Any]]:
        """Process a batch of text chunks."""
        batch_embeddings = []
        
        try:
            # If the embedding strategy supports batch processing, use it
            if hasattr(self.embedding_strategy, 'generate_batch_embeddings'):
                embeddings = self.embedding_strategy.generate_batch_embeddings(chunks)
                
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    batch_embeddings.append({
                        'chunk_id': start_index + i,
                        'text': chunk,
                        'embedding': embedding,
                        'length': len(chunk)
                    })
            else:
                # Fallback to individual processing
                for i, chunk in enumerate(chunks):
                    try:
                        embedding = self.embedding_strategy.generate_embeddings(chunk)
                        batch_embeddings.append({
                            'chunk_id': start_index + i,
                            'text': chunk,
                            'embedding': embedding,
                            'length': len(chunk)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for chunk {start_index + i}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Batch chunk processing failed: {e}")
        
        return batch_embeddings
    
    def _process_entity_batch(self, entity_texts: List[str], entity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of entities."""
        batch_embeddings = []
        
        try:
            # If the embedding strategy supports batch processing, use it
            if hasattr(self.embedding_strategy, 'generate_batch_embeddings'):
                embeddings = self.embedding_strategy.generate_batch_embeddings(entity_texts)
                
                for entity_text, entity, embedding in zip(entity_texts, entity_data, embeddings):
                    batch_embeddings.append({
                        'entity_type': entity.get('type'),
                        'entity_text': entity_text,
                        'embedding': embedding,
                        'confidence': entity.get('confidence', 0.0)
                    })
            else:
                # Fallback to individual processing
                for entity_text, entity in zip(entity_texts, entity_data):
                    try:
                        embedding = self.embedding_strategy.generate_embeddings(entity_text)
                        batch_embeddings.append({
                            'entity_type': entity.get('type'),
                            'entity_text': entity_text,
                            'embedding': embedding,
                            'confidence': entity.get('confidence', 0.0)
                        })
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for entity '{entity_text}': {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Batch entity processing failed: {e}")
        
        return batch_embeddings
    
    def get_output_keys(self) -> List[str]:
        """Get output keys including batch-specific keys."""
        base_keys = super().get_output_keys()
        return base_keys + ['batch_size', 'batches_processed']