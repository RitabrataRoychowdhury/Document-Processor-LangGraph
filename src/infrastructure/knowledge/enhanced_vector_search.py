"""
Enhanced Vector Search with Relevance Scoring and Multi-Modal Capabilities.

This module provides advanced vector search capabilities with:
- Relevance scoring algorithms
- Multi-modal search (text, semantic, contextual)
- Query expansion and refinement
- Result ranking and filtering
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..storage.vector_store import VectorDocument, InMemoryVectorStore
from src.strategies.embedding_strategy import EmbeddingStrategy
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SearchQuery:
    """Enhanced search query with multiple search modes."""
    text: str
    query_type: str = "semantic"  # semantic, keyword, hybrid
    filters: Dict[str, Any] = field(default_factory=dict)
    boost_factors: Dict[str, float] = field(default_factory=dict)
    max_results: int = 10
    min_relevance_score: float = 0.3
    enable_query_expansion: bool = True


@dataclass
class SearchResult:
    """Enhanced search result with detailed scoring."""
    document: VectorDocument
    relevance_score: float
    semantic_score: float
    keyword_score: float
    context_score: float
    boost_score: float
    final_score: float
    ranking_factors: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


class EnhancedVectorSearch:
    """
    Enhanced vector search engine with advanced relevance scoring.
    
    Features:
    - Multiple search algorithms (semantic, keyword, hybrid)
    - Advanced relevance scoring with multiple factors
    - Query expansion and refinement
    - Result ranking and filtering
    - Performance optimization
    """
    
    def __init__(self, 
                 vector_store: InMemoryVectorStore,
                 embedding_strategy: Optional[EmbeddingStrategy] = None):
        """
        Initialize enhanced vector search.
        
        Args:
            vector_store: Vector store for document storage
            embedding_strategy: Strategy for generating embeddings
        """
        self.vector_store = vector_store
        self.embedding_strategy = embedding_strategy
        
        # Search configuration
        self.config = {
            'semantic_weight': 0.4,
            'keyword_weight': 0.3,
            'context_weight': 0.2,
            'boost_weight': 0.1,
            'query_expansion_threshold': 0.7,
            'max_expanded_terms': 5
        }
        
        # Search statistics
        self.search_stats = {
            'total_searches': 0,
            'semantic_searches': 0,
            'keyword_searches': 0,
            'hybrid_searches': 0,
            'average_results_returned': 0.0,
            'average_search_time': 0.0
        }
        
        logger.info("Initialized EnhancedVectorSearch")
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform enhanced vector search with relevance scoring.
        
        Args:
            query: Enhanced search query
            
        Returns:
            List of search results with detailed scoring
        """
        start_time = datetime.now()
        
        try:
            logger.debug(f"Performing {query.query_type} search: {query.text}")
            
            # Update search statistics
            self.search_stats['total_searches'] += 1
            
            # Perform search based on query type
            if query.query_type == "semantic":
                results = self._semantic_search(query)
                self.search_stats['semantic_searches'] += 1
            elif query.query_type == "keyword":
                results = self._keyword_search(query)
                self.search_stats['keyword_searches'] += 1
            elif query.query_type == "hybrid":
                results = self._hybrid_search(query)
                self.search_stats['hybrid_searches'] += 1
            else:
                # Default to hybrid search
                results = self._hybrid_search(query)
                self.search_stats['hybrid_searches'] += 1
            
            # Apply filters
            filtered_results = self._apply_filters(results, query.filters)
            
            # Apply boost factors
            boosted_results = self._apply_boost_factors(filtered_results, query.boost_factors)
            
            # Calculate final scores and rank
            ranked_results = self._calculate_final_scores_and_rank(boosted_results)
            
            # Filter by minimum relevance score
            final_results = [
                result for result in ranked_results 
                if result.final_score >= query.min_relevance_score
            ]
            
            # Limit results
            final_results = final_results[:query.max_results]
            
            # Update statistics
            search_time = (datetime.now() - start_time).total_seconds()
            self._update_search_stats(len(final_results), search_time)
            
            logger.debug(f"Search completed: {len(final_results)} results in {search_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in enhanced vector search: {str(e)}")
            return []
    
    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic vector similarity search."""
        results = []
        
        try:
            if not self.embedding_strategy:
                logger.warning("No embedding strategy available for semantic search")
                return results
            
            # Generate query embeddings
            query_embeddings = self.embedding_strategy.generate_embeddings(query.text)
            
            # Perform vector similarity search
            vector_results = self.vector_store.search(
                query_embeddings, 
                top_k=query.max_results * 2,  # Get more results for better ranking
                min_similarity=0.1  # Lower threshold for initial search
            )
            
            # Convert to SearchResult objects
            for doc, similarity in vector_results:
                result = SearchResult(
                    document=doc,
                    relevance_score=similarity,
                    semantic_score=similarity,
                    keyword_score=0.0,
                    context_score=0.0,
                    boost_score=0.0,
                    final_score=similarity,
                    ranking_factors={'semantic_similarity': similarity},
                    explanation=f"Semantic similarity: {similarity:.3f}"
                )
                results.append(result)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
        
        return results
    
    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search."""
        results = []
        
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query.text)
            
            # Search through all documents
            for doc_id, doc in self.vector_store.documents.items():
                keyword_score = self._calculate_keyword_score(keywords, doc.text)
                
                if keyword_score > 0:
                    result = SearchResult(
                        document=doc,
                        relevance_score=keyword_score,
                        semantic_score=0.0,
                        keyword_score=keyword_score,
                        context_score=0.0,
                        boost_score=0.0,
                        final_score=keyword_score,
                        ranking_factors={'keyword_match': keyword_score},
                        explanation=f"Keyword match score: {keyword_score:.3f}"
                    )
                    results.append(result)
            
            # Sort by keyword score
            results.sort(key=lambda x: x.keyword_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
        
        return results
    
    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword approaches."""
        results = []
        
        try:
            # Get semantic search results
            semantic_results = self._semantic_search(query)
            
            # Get keyword search results
            keyword_results = self._keyword_search(query)
            
            # Combine results by document ID
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                doc_id = result.document.id
                combined_results[doc_id] = result
            
            # Merge keyword results
            for result in keyword_results:
                doc_id = result.document.id
                if doc_id in combined_results:
                    # Update existing result
                    existing = combined_results[doc_id]
                    existing.keyword_score = result.keyword_score
                    existing.ranking_factors['keyword_match'] = result.keyword_score
                else:
                    # Add new result
                    combined_results[doc_id] = result
            
            # Calculate context scores
            for result in combined_results.values():
                result.context_score = self._calculate_context_score(query, result.document)
                result.ranking_factors['context_relevance'] = result.context_score
            
            results = list(combined_results.values())
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
        
        return results
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results."""
        if not filters:
            return results
        
        filtered_results = []
        
        for result in results:
            include_result = True
            
            for filter_key, filter_value in filters.items():
                doc_value = result.document.metadata.get(filter_key)
                
                if filter_key == 'source' and doc_value != filter_value:
                    include_result = False
                    break
                elif filter_key == 'confidence_min' and (doc_value or 0) < filter_value:
                    include_result = False
                    break
                elif filter_key == 'document_type' and doc_value != filter_value:
                    include_result = False
                    break
                elif filter_key == 'date_range':
                    # Implement date range filtering if needed
                    pass
            
            if include_result:
                filtered_results.append(result)
        
        return filtered_results
    
    def _apply_boost_factors(self, results: List[SearchResult], boost_factors: Dict[str, float]) -> List[SearchResult]:
        """Apply boost factors to search results."""
        if not boost_factors:
            return results
        
        for result in results:
            boost_score = 0.0
            
            for boost_key, boost_value in boost_factors.items():
                if boost_key in result.document.metadata:
                    doc_value = result.document.metadata[boost_key]
                    
                    if boost_key == 'confidence':
                        boost_score += (doc_value or 0) * boost_value
                    elif boost_key == 'recency':
                        # Implement recency boost if needed
                        pass
                    elif boost_key == 'source_authority':
                        # Implement source authority boost if needed
                        pass
            
            result.boost_score = boost_score
            result.ranking_factors['boost_factors'] = boost_score
        
        return results
    
    def _calculate_final_scores_and_rank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Calculate final scores and rank results."""
        for result in results:
            # Calculate weighted final score
            final_score = (
                result.semantic_score * self.config['semantic_weight'] +
                result.keyword_score * self.config['keyword_weight'] +
                result.context_score * self.config['context_weight'] +
                result.boost_score * self.config['boost_weight']
            )
            
            result.final_score = min(1.0, final_score)  # Cap at 1.0
            result.relevance_score = result.final_score
            
            # Update explanation
            score_components = []
            if result.semantic_score > 0:
                score_components.append(f"semantic: {result.semantic_score:.3f}")
            if result.keyword_score > 0:
                score_components.append(f"keyword: {result.keyword_score:.3f}")
            if result.context_score > 0:
                score_components.append(f"context: {result.context_score:.3f}")
            if result.boost_score > 0:
                score_components.append(f"boost: {result.boost_score:.3f}")
            
            result.explanation = f"Final score: {result.final_score:.3f} ({', '.join(score_components)})"
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        return results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from query text."""
        # Simple keyword extraction - in production, use more sophisticated NLP
        import re
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
            'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_score(self, keywords: List[str], text: str) -> float:
        """Calculate keyword match score for a document."""
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword in text_lower:
                matches += 1
        
        return matches / total_keywords if total_keywords > 0 else 0.0
    
    def _calculate_context_score(self, query: SearchQuery, document: VectorDocument) -> float:
        """Calculate contextual relevance score."""
        context_score = 0.0
        
        try:
            # Document metadata relevance
            if 'extraction_method' in document.metadata:
                if 'openrouter' in document.metadata['extraction_method'].lower():
                    context_score += 0.2  # Boost for OpenRouter extraction
            
            # Document type relevance
            if 'document_type' in document.metadata:
                doc_type = document.metadata['document_type'].lower()
                if any(term in query.text.lower() for term in ['qme', 'medical', 'report']):
                    if 'medical' in doc_type or 'qme' in doc_type:
                        context_score += 0.3
            
            # Confidence score contribution
            if 'confidence' in document.metadata:
                confidence = document.metadata.get('confidence', 0)
                context_score += confidence * 0.2
            
            # Recency bonus (if timestamp available)
            if 'timestamp' in document.metadata:
                # Implement recency scoring if needed
                pass
            
        except Exception as e:
            logger.error(f"Error calculating context score: {str(e)}")
        
        return min(1.0, context_score)
    
    def _update_search_stats(self, num_results: int, search_time: float) -> None:
        """Update search statistics."""
        # Update average results returned
        total_searches = self.search_stats['total_searches']
        current_avg_results = self.search_stats['average_results_returned']
        self.search_stats['average_results_returned'] = (
            (current_avg_results * (total_searches - 1) + num_results) / total_searches
        )
        
        # Update average search time
        current_avg_time = self.search_stats['average_search_time']
        self.search_stats['average_search_time'] = (
            (current_avg_time * (total_searches - 1) + search_time) / total_searches
        )
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search performance statistics."""
        return {
            **self.search_stats,
            'semantic_search_ratio': (
                self.search_stats['semantic_searches'] / 
                max(1, self.search_stats['total_searches'])
            ),
            'keyword_search_ratio': (
                self.search_stats['keyword_searches'] / 
                max(1, self.search_stats['total_searches'])
            ),
            'hybrid_search_ratio': (
                self.search_stats['hybrid_searches'] / 
                max(1, self.search_stats['total_searches'])
            )
        }
    
    def update_search_config(self, config_updates: Dict[str, Any]) -> None:
        """Update search configuration."""
        for key, value in config_updates.items():
            if key in self.config:
                self.config[key] = value
                logger.info(f"Updated search config: {key} = {value}")
            else:
                logger.warning(f"Unknown config key: {key}")