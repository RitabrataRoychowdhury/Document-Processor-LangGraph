"""
In-memory vector store for semantic search capabilities.
Provides vector similarity search for knowledge graph embeddings.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import json

try:
    from src.utils.logging_config import get_logger
except ImportError:
    from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class VectorDocument:
    """Document stored in vector store."""
    id: str
    text: str
    embeddings: List[float]
    metadata: Dict[str, Any]


class InMemoryVectorStore:
    """In-memory vector store with cosine similarity search."""
    
    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}
        self._embeddings_matrix: Optional[np.ndarray] = None
        self._doc_ids: List[str] = []
        self._needs_rebuild = True
    
    def add_document(self, doc_id: str, text: str, embeddings: List[float], metadata: Dict[str, Any] = None) -> None:
        """
        Add document to vector store.
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            embeddings: Vector embeddings for the document
            metadata: Additional metadata
        """
        if metadata is None:
            metadata = {}
        
        doc = VectorDocument(
            id=doc_id,
            text=text,
            embeddings=embeddings,
            metadata=metadata
        )
        
        self.documents[doc_id] = doc
        self._needs_rebuild = True
        
        logger.debug(f"Added document {doc_id} to vector store")
    
    def add_documents(self, documents: List[Tuple[str, str, List[float], Dict[str, Any]]]) -> None:
        """
        Add multiple documents to vector store.
        
        Args:
            documents: List of (doc_id, text, embeddings, metadata) tuples
        """
        for doc_id, text, embeddings, metadata in documents:
            self.add_document(doc_id, text, embeddings, metadata or {})
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(self, query_embeddings: List[float], top_k: int = 5, min_similarity: float = 0.0) -> List[Tuple[VectorDocument, float]]:
        """
        Search for similar documents using cosine similarity.
        
        Args:
            query_embeddings: Query vector embeddings
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents:
            return []
        
        self._rebuild_matrix_if_needed()
        
        if self._embeddings_matrix is None:
            return []
        
        # Convert query to numpy array
        query_vector = np.array(query_embeddings)
        
        # Calculate cosine similarities
        similarities = self._cosine_similarity(query_vector, self._embeddings_matrix)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            similarity = similarities[idx]
            if similarity >= min_similarity:
                doc_id = self._doc_ids[idx]
                document = self.documents[doc_id]
                results.append((document, float(similarity)))
        
        logger.debug(f"Vector search returned {len(results)} results")
        return results
    
    def search_by_text(self, query_text: str, embedding_strategy, top_k: int = 5, min_similarity: float = 0.0) -> List[Tuple[VectorDocument, float]]:
        """
        Search using text query (generates embeddings first).
        
        Args:
            query_text: Text query
            embedding_strategy: Strategy to generate query embeddings
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            query_embeddings = embedding_strategy.generate_embeddings(query_text)
            return self.search(query_embeddings, top_k, min_similarity)
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Get document by ID."""
        return self.documents.get(doc_id)
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove document from vector store."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._needs_rebuild = True
            logger.debug(f"Removed document {doc_id} from vector store")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all documents from vector store."""
        self.documents.clear()
        self._embeddings_matrix = None
        self._doc_ids.clear()
        self._needs_rebuild = False
        logger.info("Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "document_count": len(self.documents),
            "embedding_dimension": len(next(iter(self.documents.values())).embeddings) if self.documents else 0,
            "needs_rebuild": self._needs_rebuild
        }
    
    def _rebuild_matrix_if_needed(self) -> None:
        """Rebuild embeddings matrix if needed."""
        if not self._needs_rebuild:
            return
        
        if not self.documents:
            self._embeddings_matrix = None
            self._doc_ids = []
            return
        
        # Build embeddings matrix and doc ID list
        embeddings_list = []
        doc_ids = []
        
        for doc_id, doc in self.documents.items():
            embeddings_list.append(doc.embeddings)
            doc_ids.append(doc_id)
        
        self._embeddings_matrix = np.array(embeddings_list)
        self._doc_ids = doc_ids
        self._needs_rebuild = False
        
        logger.debug(f"Rebuilt embeddings matrix: {self._embeddings_matrix.shape}")
    
    def _cosine_similarity(self, query_vector: np.ndarray, embeddings_matrix: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and all documents."""
        # Normalize vectors
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        embeddings_norm = embeddings_matrix / (np.linalg.norm(embeddings_matrix, axis=1, keepdims=True) + 1e-8)
        
        # Calculate cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities
    
    def save_to_file(self, file_path: str) -> None:
        """Save vector store to file."""
        try:
            data = {
                "documents": {
                    doc_id: {
                        "id": doc.id,
                        "text": doc.text,
                        "embeddings": doc.embeddings,
                        "metadata": doc.metadata
                    }
                    for doc_id, doc in self.documents.items()
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved vector store to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    def load_from_file(self, file_path: str) -> None:
        """Load vector store from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.documents.clear()
            
            for doc_id, doc_data in data.get("documents", {}).items():
                doc = VectorDocument(
                    id=doc_data["id"],
                    text=doc_data["text"],
                    embeddings=doc_data["embeddings"],
                    metadata=doc_data.get("metadata", {})
                )
                self.documents[doc_id] = doc
            
            self._needs_rebuild = True
            logger.info(f"Loaded vector store from {file_path}: {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise


class VectorStoreManager:
    """Manager for multiple vector stores."""
    
    def __init__(self):
        self.stores: Dict[str, InMemoryVectorStore] = {}
    
    def create_store(self, store_name: str) -> InMemoryVectorStore:
        """Create a new vector store."""
        store = InMemoryVectorStore()
        self.stores[store_name] = store
        logger.info(f"Created vector store: {store_name}")
        return store
    
    def get_store(self, store_name: str) -> Optional[InMemoryVectorStore]:
        """Get vector store by name."""
        return self.stores.get(store_name)
    
    def get_or_create_store(self, store_name: str) -> InMemoryVectorStore:
        """Get existing store or create new one."""
        if store_name not in self.stores:
            return self.create_store(store_name)
        return self.stores[store_name]
    
    def remove_store(self, store_name: str) -> bool:
        """Remove vector store."""
        if store_name in self.stores:
            del self.stores[store_name]
            logger.info(f"Removed vector store: {store_name}")
            return True
        return False
    
    def list_stores(self) -> List[str]:
        """List all vector store names."""
        return list(self.stores.keys())
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all stores."""
        return {
            store_name: store.get_stats()
            for store_name, store in self.stores.items()
        }


# Global vector store manager instance
vector_store_manager = VectorStoreManager()