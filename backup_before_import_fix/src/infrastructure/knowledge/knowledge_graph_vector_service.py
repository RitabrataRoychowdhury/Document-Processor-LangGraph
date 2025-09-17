"""
Service for managing vector embeddings of knowledge graph nodes.
Integrates knowledge graph with vector store for hybrid search.
"""

from typing import List, Dict, Any, Optional
import json

try:
    from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from src.infrastructure.storage.vector_store import vector_store_manager, VectorDocument
    from src.strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
    from src.utils.logging_config import get_logger
except ImportError:
    from repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
    from infrastructure.storage.vector_store import vector_store_manager, VectorDocument
    from strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeGraphVectorService:
    """Service for managing vector embeddings of knowledge graph nodes."""
    
    def __init__(self, 
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 embedding_strategy: Optional[EmbeddingStrategy] = None,
                 vector_store_name: str = "knowledge_graph"):
        """
        Initialize the service.
        
        Args:
            kg_repository: Knowledge graph repository
            embedding_strategy: Strategy for generating embeddings
            vector_store_name: Name of the vector store to use
        """
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        self.embedding_strategy = embedding_strategy or EmbeddingStrategyFactory.create_strategy('local')
        self.vector_store = vector_store_manager.get_or_create_store(vector_store_name)
        
        logger.info(f"Initialized KnowledgeGraphVectorService with {vector_store_name} vector store")
    
    def populate_vector_store_from_kg(self) -> Dict[str, int]:
        """
        Populate vector store with embeddings from all knowledge graph nodes.
        
        Returns:
            Dictionary with counts of processed nodes by type
        """
        stats = {}
        total_processed = 0
        
        try:
            # Process different node types
            node_types = ['document', 'section', 'diagnosis', 'finding', 'impairment_rating', 'patient']
            
            for node_type in node_types:
                try:
                    nodes = self.kg_repository.find_nodes_by_type(node_type)
                    processed_count = self._process_nodes_for_vector_store(nodes, node_type)
                    stats[node_type] = processed_count
                    total_processed += processed_count
                    
                    logger.info(f"Processed {processed_count} {node_type} nodes for vector store")
                    
                except Exception as e:
                    logger.error(f"Error processing {node_type} nodes: {e}")
                    stats[node_type] = 0
            
            stats['total'] = total_processed
            logger.info(f"Successfully populated vector store with {total_processed} node embeddings")
            
        except Exception as e:
            logger.error(f"Error populating vector store from knowledge graph: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def _process_nodes_for_vector_store(self, nodes: List, node_type: str) -> int:
        """Process a list of nodes and add them to vector store."""
        processed_count = 0
        
        for node in nodes:
            try:
                # Create text representation of the node
                node_text = self._create_node_text(node)
                
                if not node_text.strip():
                    continue
                
                # Generate embeddings if not already present
                embeddings = node.embeddings
                if not embeddings:
                    embeddings = self.embedding_strategy.generate_embeddings(node_text)
                    
                    # Update node with embeddings in knowledge graph
                    node.embeddings = embeddings
                    self.kg_repository.save_node(node)
                
                # Create metadata for vector store
                metadata = {
                    'node_id': node.id,
                    'node_type': node.node_type,
                    'source': f"Knowledge Graph - {node_type.title()}",
                    **node.properties
                }
                
                # Add to vector store
                self.vector_store.add_document(
                    doc_id=f"kg_{node.id}",
                    text=node_text,
                    embeddings=embeddings,
                    metadata=metadata
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing node {node.id}: {e}")
                continue
        
        return processed_count
    
    def _create_node_text(self, node) -> str:
        """Create a text representation of a knowledge graph node."""
        try:
            text_parts = []
            
            # Add node type
            text_parts.append(f"Type: {node.node_type.replace('_', ' ').title()}")
            
            # Add key properties based on node type
            if node.node_type == 'diagnosis':
                if 'description' in node.properties:
                    text_parts.append(f"Diagnosis: {node.properties['description']}")
                if 'icd_code' in node.properties:
                    text_parts.append(f"ICD Code: {node.properties['icd_code']}")
                if 'severity' in node.properties:
                    text_parts.append(f"Severity: {node.properties['severity']}")
            
            elif node.node_type == 'finding':
                if 'description' in node.properties:
                    text_parts.append(f"Finding: {node.properties['description']}")
                if 'finding_type' in node.properties:
                    text_parts.append(f"Type: {node.properties['finding_type']}")
            
            elif node.node_type == 'impairment_rating':
                if 'percentage' in node.properties:
                    text_parts.append(f"Impairment Rating: {node.properties['percentage']}%")
                if 'ama_table' in node.properties:
                    text_parts.append(f"AMA Table: {node.properties['ama_table']}")
                if 'rationale' in node.properties:
                    text_parts.append(f"Rationale: {node.properties['rationale']}")
            
            elif node.node_type == 'section':
                if 'section_type' in node.properties:
                    text_parts.append(f"Section: {node.properties['section_type']}")
                if 'text_content' in node.properties:
                    content = node.properties['text_content']
                    if len(content) > 500:
                        content = content[:500] + "..."
                    text_parts.append(f"Content: {content}")
            
            elif node.node_type == 'document':
                if 'title' in node.properties:
                    text_parts.append(f"Document: {node.properties['title']}")
                if 'document_type' in node.properties:
                    text_parts.append(f"Type: {node.properties['document_type']}")
            
            elif node.node_type == 'patient':
                if 'name' in node.properties:
                    text_parts.append(f"Patient: {node.properties['name']}")
                if 'case_number' in node.properties:
                    text_parts.append(f"Case: {node.properties['case_number']}")
            
            # Add common properties
            if 'page_reference' in node.properties:
                text_parts.append(f"Page: {node.properties['page_reference']}")
            
            if 'document_id' in node.properties:
                text_parts.append(f"Document ID: {node.properties['document_id']}")
            
            return ". ".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error creating text for node {node.id}: {e}")
            return f"Knowledge graph node: {node.node_type}"
    
    def add_node_to_vector_store(self, node) -> bool:
        """
        Add a single node to the vector store.
        
        Args:
            node: Knowledge graph node to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            node_text = self._create_node_text(node)
            
            if not node_text.strip():
                return False
            
            # Generate embeddings if not present
            embeddings = node.embeddings
            if not embeddings:
                embeddings = self.embedding_strategy.generate_embeddings(node_text)
                
                # Update node with embeddings
                node.embeddings = embeddings
                self.kg_repository.save_node(node)
            
            # Create metadata
            metadata = {
                'node_id': node.id,
                'node_type': node.node_type,
                'source': f"Knowledge Graph - {node.node_type.title()}",
                **node.properties
            }
            
            # Add to vector store
            self.vector_store.add_document(
                doc_id=f"kg_{node.id}",
                text=node_text,
                embeddings=embeddings,
                metadata=metadata
            )
            
            logger.debug(f"Added node {node.id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding node {node.id} to vector store: {e}")
            return False
    
    def search_similar_nodes(self, query: str, top_k: int = 5, min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for similar nodes using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar nodes with metadata
        """
        try:
            results = self.vector_store.search_by_text(
                query, 
                self.embedding_strategy, 
                top_k=top_k, 
                min_similarity=min_similarity
            )
            
            similar_nodes = []
            for doc, similarity in results:
                similar_nodes.append({
                    'node_id': doc.metadata.get('node_id'),
                    'node_type': doc.metadata.get('node_type'),
                    'text': doc.text,
                    'similarity': similarity,
                    'metadata': doc.metadata
                })
            
            logger.debug(f"Found {len(similar_nodes)} similar nodes for query: {query}")
            return similar_nodes
            
        except Exception as e:
            logger.error(f"Error searching similar nodes: {e}")
            return []
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            stats = self.vector_store.get_stats()
            
            # Add knowledge graph specific stats
            kg_docs = [doc for doc in self.vector_store.documents.values() 
                      if doc.id.startswith('kg_')]
            
            node_type_counts = {}
            for doc in kg_docs:
                node_type = doc.metadata.get('node_type', 'unknown')
                node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
            
            stats['knowledge_graph_documents'] = len(kg_docs)
            stats['node_type_counts'] = node_type_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {'error': str(e)}
    
    def clear_kg_vectors(self) -> bool:
        """Clear all knowledge graph vectors from the vector store."""
        try:
            kg_doc_ids = [doc_id for doc_id in self.vector_store.documents.keys() 
                         if doc_id.startswith('kg_')]
            
            removed_count = 0
            for doc_id in kg_doc_ids:
                if self.vector_store.remove_document(doc_id):
                    removed_count += 1
            
            logger.info(f"Removed {removed_count} knowledge graph documents from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing knowledge graph vectors: {e}")
            return False


def create_kg_vector_service(kg_repository: Optional[KnowledgeGraphRepository] = None,
                           embedding_strategy: Optional[EmbeddingStrategy] = None) -> KnowledgeGraphVectorService:
    """
    Factory function to create a knowledge graph vector service.
    
    Args:
        kg_repository: Knowledge graph repository
        embedding_strategy: Embedding strategy
        
    Returns:
        KnowledgeGraphVectorService instance
    """
    return KnowledgeGraphVectorService(kg_repository, embedding_strategy)