"""
Q&A Engine for document question answering using processed document context.
Enhanced with knowledge graph support and hybrid retrieval strategies.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Conditional import for requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from src.models.document import Document, QASession
from src.storage.document_storage import DocumentStorage
from src.strategies.qa_strategy import QAStrategy, QAResponse, VectorGraphRetrievalStrategy, HybridQAStrategy
from src.repositories.knowledge_graph_repository import KnowledgeGraphRepository, SQLiteKnowledgeGraphRepository
from src.services.vector_store import vector_store_manager
from src.strategies.embedding_strategy import EmbeddingStrategy
from src.config.dependency_injection import get_container
from src.utils.logging_config import get_logger
from src.utils.error_handling import QAError, APIError, handle_errors

logger = get_logger(__name__)


class QAEngine:
    """Enhanced Q&A Engine with knowledge graph support and hybrid retrieval."""
    
    def __init__(self, 
                 storage: DocumentStorage, 
                 qa_strategy: Optional[QAStrategy] = None,
                 kg_repository: Optional[KnowledgeGraphRepository] = None,
                 embedding_strategy: Optional[EmbeddingStrategy] = None):
        """
        Initialize Q&A Engine with storage, strategy, and knowledge graph support.
        
        Args:
            storage: Document storage instance
            qa_strategy: Q&A strategy instance. If None, gets from dependency container.
            kg_repository: Knowledge graph repository for graph traversal
            embedding_strategy: Embedding strategy for vector search
        """
        self.storage = storage
        self.kg_repository = kg_repository or SQLiteKnowledgeGraphRepository()
        self.embedding_strategy = embedding_strategy
        
        # Initialize vector store
        self.vector_store = vector_store_manager.get_or_create_store("main")
        
        # Set up QA strategy - prefer hybrid if knowledge graph is available
        if qa_strategy:
            self.qa_strategy = qa_strategy
        else:
            try:
                self.qa_strategy = get_container().get_qa_strategy()
            except:
                # Fallback to creating a hybrid strategy if available
                if self.kg_repository and self.embedding_strategy:
                    self.qa_strategy = self._create_hybrid_strategy()
                else:
                    raise ValueError("No QA strategy provided and unable to create hybrid strategy")
        
        logger.info(f"Initialized QAEngine with {type(self.qa_strategy).__name__}")
    
    def _create_hybrid_strategy(self) -> HybridQAStrategy:
        """Create a hybrid QA strategy with knowledge graph support."""
        try:
            from src.strategies.qa_strategy import GeminiLLMStrategy
            import os
            
            # Create hybrid retrieval strategy
            retrieval_strategy = VectorGraphRetrievalStrategy(
                vector_store=self.vector_store,
                kg_repository=self.kg_repository,
                embedding_strategy=self.embedding_strategy
            )
            
            # Create LLM strategy (default to Gemini)
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable required for hybrid strategy")
            
            llm_strategy = GeminiLLMStrategy(api_key)
            
            return HybridQAStrategy(retrieval_strategy, llm_strategy)
            
        except Exception as e:
            logger.error(f"Error creating hybrid strategy: {e}")
            raise
    
    def answer_question(self, question: str, document_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a question using knowledge graph and document context.
        
        Args:
            question: The user's question
            document_id: Optional ID of specific document to query
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Prepare document content
            document_content = {}
            document_title = "Knowledge Base"
            document_type = "knowledge_graph"
            
            if document_id:
                # Get specific document if requested
                document = self.storage.get_document_with_embeddings(document_id)
                if document:
                    document_content = {
                        'original_text': document.original_text,
                        'extracted_info': document.extracted_info,
                        'analysis': document.analysis,
                        'summary': document.summary,
                        'document_type': document.document_type,
                        'title': document.title,
                        'document_id': document_id
                    }
                    document_title = document.title
                    document_type = document.document_type
                else:
                    return {
                        'answer': "Sorry, I couldn't find that document or it hasn't been processed yet.",
                        'sources': [],
                        'confidence': 0.0,
                        'error': 'Document not found or not processed'
                    }
            else:
                # Query across entire knowledge base
                document_content = {
                    'title': 'Knowledge Base Query',
                    'document_type': 'knowledge_graph',
                    'original_text': '',
                    'extracted_info': {},
                    'analysis': '',
                    'summary': ''
                }
            
            # Use strategy to answer question
            qa_response = self.qa_strategy.answer_question(question, document_content)
            
            # Store the Q&A interaction
            if session_id:
                self.storage.add_qa_interaction(session_id, question, qa_response.answer, qa_response.sources)
            
            # Convert QAResponse to dictionary format for backward compatibility
            return {
                'answer': qa_response.answer,
                'sources': qa_response.sources,
                'confidence': qa_response.confidence,
                'document_title': document_title,
                'document_type': document_type,
                'metadata': qa_response.metadata,
                'knowledge_graph_used': True
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': "I'm sorry, I encountered an error while processing your question. Please try again.",
                'sources': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def answer_question_with_graph_traversal(self, question: str, max_hops: int = 2) -> Dict[str, Any]:
        """
        Answer a question using deep knowledge graph traversal.
        
        Args:
            question: The user's question
            max_hops: Maximum number of relationship hops to traverse
            
        Returns:
            Dictionary containing answer, sources, and traversal path
        """
        try:
            # Find relevant starting nodes based on question keywords
            starting_nodes = self._find_relevant_nodes(question)
            
            if not starting_nodes:
                return self.answer_question(question)  # Fallback to regular search
            
            # Perform graph traversal
            traversal_results = []
            for node in starting_nodes[:3]:  # Limit to top 3 starting nodes
                paths = self._traverse_graph_paths(node.id, question, max_hops)
                traversal_results.extend(paths)
            
            # Create context from traversal results
            traversal_context = self._format_traversal_context(traversal_results)
            
            # Use LLM to generate answer from traversal context
            if hasattr(self.qa_strategy, 'llm_strategy'):
                answer = self.qa_strategy.llm_strategy.generate_answer(question, traversal_context)
            else:
                answer = "Based on the knowledge graph traversal, I found relevant information but cannot generate a comprehensive answer."
            
            # Extract sources from traversal
            sources = self._extract_traversal_sources(traversal_results)
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': 0.8,
                'document_title': 'Knowledge Graph Traversal',
                'document_type': 'graph_traversal',
                'metadata': {
                    'traversal_paths': len(traversal_results),
                    'max_hops': max_hops,
                    'starting_nodes': [node.id for node in starting_nodes]
                },
                'knowledge_graph_used': True
            }
            
        except Exception as e:
            logger.error(f"Error in graph traversal Q&A: {e}")
            return self.answer_question(question)  # Fallback to regular search
    
    def _find_relevant_nodes(self, question: str) -> List:
        """Find relevant starting nodes for graph traversal based on question."""
        relevant_nodes = []
        
        try:
            question_lower = question.lower()
            
            # Search for diagnosis nodes if question mentions medical conditions
            if any(term in question_lower for term in ['diagnosis', 'condition', 'disease', 'disorder']):
                diagnosis_nodes = self.kg_repository.find_nodes_by_type('diagnosis')
                for node in diagnosis_nodes:
                    if any(term in node.properties.get('description', '').lower() 
                          for term in question_lower.split() if len(term) > 3):
                        relevant_nodes.append(node)
            
            # Search for impairment rating nodes
            if any(term in question_lower for term in ['impairment', 'rating', 'disability', 'ama']):
                impairment_nodes = self.kg_repository.find_nodes_by_type('impairment_rating')
                relevant_nodes.extend(impairment_nodes[:3])
            
            # Search for finding nodes
            if any(term in question_lower for term in ['finding', 'examination', 'test']):
                finding_nodes = self.kg_repository.find_nodes_by_type('finding')
                relevant_nodes.extend(finding_nodes[:3])
            
        except Exception as e:
            logger.error(f"Error finding relevant nodes: {e}")
        
        return relevant_nodes[:5]  # Limit to top 5 nodes
    
    def _traverse_graph_paths(self, start_node_id: str, question: str, max_hops: int) -> List[Dict[str, Any]]:
        """Traverse graph paths from a starting node."""
        paths = []
        visited = set()
        
        def traverse(node_id: str, path: List[str], hop_count: int):
            if hop_count >= max_hops or node_id in visited:
                return
            
            visited.add(node_id)
            current_node = self.kg_repository.find_node_by_id(node_id)
            if not current_node:
                return
            
            # Add current path to results
            paths.append({
                'path': path + [node_id],
                'end_node': current_node,
                'hop_count': hop_count
            })
            
            # Continue traversal
            relationships = self.kg_repository.find_relationships_by_source(node_id)
            for rel in relationships:
                if rel.confidence > 0.5:  # Only follow high-confidence relationships
                    traverse(rel.target_node_id, path + [node_id], hop_count + 1)
        
        try:
            traverse(start_node_id, [], 0)
        except Exception as e:
            logger.error(f"Error in graph traversal: {e}")
        
        return paths
    
    def _format_traversal_context(self, traversal_results: List[Dict[str, Any]]) -> List:
        """Format traversal results into context for LLM."""
        from src.strategies.qa_strategy import RetrievalContext
        
        contexts = []
        for result in traversal_results:
            end_node = result['end_node']
            path_length = result['hop_count']
            
            # Create descriptive text for the traversal result
            context_text = f"Through {path_length} relationship hops: "
            context_text += f"{end_node.node_type.title()}: {end_node.properties.get('description', 'Unknown')}"
            
            if 'percentage' in end_node.properties:
                context_text += f" (Rating: {end_node.properties['percentage']}%)"
            
            if 'ama_table' in end_node.properties:
                context_text += f" [AMA Table: {end_node.properties['ama_table']}]"
            
            contexts.append(RetrievalContext(
                text=context_text,
                source=f"Graph Traversal - {end_node.node_type}",
                relevance_score=1.0 - (path_length * 0.2),  # Decrease relevance with distance
                metadata={
                    'node_id': end_node.id,
                    'node_type': end_node.node_type,
                    'hop_count': path_length,
                    'page_reference': end_node.properties.get('page_reference'),
                    'document_id': end_node.properties.get('document_id')
                }
            ))
        
        return contexts
    
    def _extract_traversal_sources(self, traversal_results: List[Dict[str, Any]]) -> List[str]:
        """Extract source information from traversal results."""
        sources = []
        for result in traversal_results:
            end_node = result['end_node']
            source_info = f"Graph Traversal - {end_node.node_type.title()}"
            
            if 'page_reference' in end_node.properties:
                source_info += f" (Page {end_node.properties['page_reference']})"
            
            if 'document_id' in end_node.properties:
                source_info += f" [Doc: {end_node.properties['document_id']}]"
            
            sources.append(source_info)
        
        return list(set(sources))
    

    
    def create_qa_session(self, document_id: str) -> str:
        """
        Create a new Q&A session for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Session ID
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        session = QASession(
            session_id=session_id,
            document_id=document_id
        )
        
        self.storage.create_qa_session(session)
        return session_id
    
    def get_qa_session(self, session_id: str) -> Optional[QASession]:
        """Get a Q&A session by ID."""
        return self.storage.get_qa_session(session_id)
    
    def get_document_qa_sessions(self, document_id: str) -> List[QASession]:
        """Get all Q&A sessions for a document."""
        return self.storage.list_qa_sessions(document_id)
    



def create_qa_engine(storage: Optional[DocumentStorage] = None, 
                    qa_strategy: Optional[QAStrategy] = None,
                    kg_repository: Optional[KnowledgeGraphRepository] = None,
                    embedding_strategy: Optional[EmbeddingStrategy] = None) -> QAEngine:
    """
    Factory function to create a Q&A engine with knowledge graph support.
    
    Args:
        storage: Document storage instance. If None, creates default.
        qa_strategy: Q&A strategy instance. If None, creates hybrid strategy.
        kg_repository: Knowledge graph repository. If None, creates default.
        embedding_strategy: Embedding strategy. If None, creates default.
        
    Returns:
        QAEngine instance
    """
    if storage is None:
        storage = DocumentStorage()
    
    if kg_repository is None:
        kg_repository = SQLiteKnowledgeGraphRepository()
    
    if embedding_strategy is None:
        try:
            from src.strategies.embedding_strategy import EmbeddingStrategyFactory
            embedding_strategy = EmbeddingStrategyFactory.create_strategy('local')
        except Exception as e:
            logger.warning(f"Could not create default embedding strategy: {e}")
    
    return QAEngine(storage, qa_strategy, kg_repository, embedding_strategy)


def create_hybrid_qa_engine(gemini_api_key: str, 
                           storage: Optional[DocumentStorage] = None,
                           kg_repository: Optional[KnowledgeGraphRepository] = None) -> QAEngine:
    """
    Factory function to create a Q&A engine with hybrid strategy.
    
    Args:
        gemini_api_key: Gemini API key for LLM strategy
        storage: Document storage instance. If None, creates default.
        kg_repository: Knowledge graph repository. If None, creates default.
        
    Returns:
        QAEngine instance with hybrid strategy
    """
    from src.strategies.embedding_strategy import EmbeddingStrategyFactory
    from src.strategies.qa_strategy import GeminiLLMStrategy, HybridQAStrategy, VectorGraphRetrievalStrategy
    
    if storage is None:
        storage = DocumentStorage()
    
    if kg_repository is None:
        kg_repository = SQLiteKnowledgeGraphRepository()
    
    # Create embedding strategy
    embedding_strategy = EmbeddingStrategyFactory.create_strategy('local')
    
    # Create vector store
    vector_store = vector_store_manager.get_or_create_store("main")
    
    # Create hybrid retrieval strategy
    retrieval_strategy = VectorGraphRetrievalStrategy(
        vector_store=vector_store,
        kg_repository=kg_repository,
        embedding_strategy=embedding_strategy
    )
    
    # Create LLM strategy
    llm_strategy = GeminiLLMStrategy(gemini_api_key)
    
    # Create hybrid QA strategy
    qa_strategy = HybridQAStrategy(retrieval_strategy, llm_strategy)
    
    return QAEngine(storage, qa_strategy, kg_repository, embedding_strategy)