"""
Q&A strategy implementations using the Strategy Pattern.
Supports hybrid approaches combining vector search and LLM generation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from dataclasses import dataclass
from src.utils.logging_config import get_logger

# Conditional import for requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class QAResponse:
    """Response object for Q&A operations."""
    answer: str
    sources: List[str]
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class RetrievalContext:
    """Context retrieved for Q&A."""
    text: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]


class RetrievalStrategy(ABC):
    """Abstract base class for context retrieval strategies."""
    
    @abstractmethod
    def retrieve_context(self, question: str, document_content: Dict[str, Any]) -> List[RetrievalContext]:
        """
        Retrieve relevant context for a question.
        
        Args:
            question: User's question
            document_content: Document content and metadata
            
        Returns:
            List of relevant context sections
        """
        pass


class LLMStrategy(ABC):
    """Abstract base class for LLM generation strategies."""
    
    @abstractmethod
    def generate_answer(self, question: str, context: List[RetrievalContext]) -> str:
        """
        Generate an answer using the provided context.
        
        Args:
            question: User's question
            context: Retrieved context sections
            
        Returns:
            Generated answer string
        """
        pass


class QAStrategy(ABC):
    """Abstract base class for Q&A strategies."""
    
    @abstractmethod
    def answer_question(self, question: str, document_content: Dict[str, Any]) -> QAResponse:
        """
        Answer a question using the document content.
        
        Args:
            question: User's question
            document_content: Document content and metadata
            
        Returns:
            QAResponse with answer, sources, and metadata
        """
        pass


class VectorGraphRetrievalStrategy(RetrievalStrategy):
    """Hybrid retrieval strategy combining vector search and knowledge graph traversal."""
    
    def __init__(self, vector_store, kg_repository, embedding_strategy):
        """
        Initialize hybrid retrieval strategy.
        
        Args:
            vector_store: Vector store for semantic search
            kg_repository: Knowledge graph repository for graph traversal
            embedding_strategy: Strategy for generating query embeddings
        """
        self.vector_store = vector_store
        self.kg_repository = kg_repository
        self.embedding_strategy = embedding_strategy
        logger.info("Initialized VectorGraphRetrievalStrategy")
    
    def retrieve_context(self, question: str, document_content: Dict[str, Any]) -> List[RetrievalContext]:
        """Retrieve context using both vector search and graph traversal."""
        context_sections = []
        
        try:
            # Step 1: Vector similarity search
            vector_contexts = self._vector_search(question)
            context_sections.extend(vector_contexts)
            
            # Step 2: Graph traversal for connected entities
            graph_contexts = self._graph_traversal_search(question, vector_contexts)
            context_sections.extend(graph_contexts)
            
            # Step 3: Fallback to keyword search if no results
            if not context_sections:
                keyword_contexts = self._keyword_fallback(question, document_content)
                context_sections.extend(keyword_contexts)
            
            # Remove duplicates and sort by relevance
            unique_contexts = self._deduplicate_contexts(context_sections)
            unique_contexts.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return unique_contexts[:10]  # Return top 10 most relevant sections
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            # Fallback to keyword search
            return self._keyword_fallback(question, document_content)
    
    def _vector_search(self, question: str) -> List[RetrievalContext]:
        """Perform vector similarity search."""
        try:
            # Search in the main vector store
            results = self.vector_store.search_by_text(
                question, 
                self.embedding_strategy, 
                top_k=5, 
                min_similarity=0.3
            )
            
            contexts = []
            for doc, similarity in results:
                contexts.append(RetrievalContext(
                    text=doc.text,
                    source=f"Vector Search - {doc.metadata.get('source', 'Unknown')}",
                    relevance_score=similarity,
                    metadata={
                        'search_type': 'vector',
                        'doc_id': doc.id,
                        'similarity': similarity,
                        **doc.metadata
                    }
                ))
            
            logger.debug(f"Vector search returned {len(contexts)} results")
            return contexts
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def _graph_traversal_search(self, question: str, vector_contexts: List[RetrievalContext]) -> List[RetrievalContext]:
        """Perform graph traversal to find connected entities."""
        try:
            graph_contexts = []
            
            # Extract entity IDs from vector search results
            entity_ids = []
            for ctx in vector_contexts:
                if 'node_id' in ctx.metadata:
                    entity_ids.append(ctx.metadata['node_id'])
            
            # Traverse graph for each entity
            for entity_id in entity_ids:
                connected_contexts = self._traverse_entity_relationships(entity_id, question)
                graph_contexts.extend(connected_contexts)
            
            # Also search for specific medical relationships
            medical_contexts = self._search_medical_relationships(question)
            graph_contexts.extend(medical_contexts)
            
            logger.debug(f"Graph traversal returned {len(graph_contexts)} results")
            return graph_contexts
            
        except Exception as e:
            logger.error(f"Error in graph traversal: {e}")
            return []
    
    def _traverse_entity_relationships(self, entity_id: str, question: str) -> List[RetrievalContext]:
        """Traverse relationships for a specific entity."""
        contexts = []
        
        try:
            # Get the source node
            source_node = self.kg_repository.find_node_by_id(entity_id)
            if not source_node:
                return contexts
            
            # Find outgoing relationships
            outgoing_rels = self.kg_repository.find_relationships_by_source(entity_id)
            
            for rel in outgoing_rels:
                target_node = self.kg_repository.find_node_by_id(rel.target_node_id)
                if target_node:
                    # Create context from relationship
                    relationship_text = self._format_relationship_context(source_node, rel, target_node)
                    
                    contexts.append(RetrievalContext(
                        text=relationship_text,
                        source=f"Knowledge Graph - {rel.relationship_type}",
                        relevance_score=rel.confidence * 0.8,  # Slightly lower than vector search
                        metadata={
                            'search_type': 'graph_traversal',
                            'relationship_type': rel.relationship_type,
                            'source_node_id': source_node.id,
                            'target_node_id': target_node.id,
                            'confidence': rel.confidence,
                            'page_reference': target_node.properties.get('page_reference'),
                            'document_id': target_node.properties.get('document_id')
                        }
                    ))
            
            # Also check incoming relationships
            incoming_rels = self.kg_repository.find_relationships_by_target(entity_id)
            
            for rel in incoming_rels:
                source_rel_node = self.kg_repository.find_node_by_id(rel.source_node_id)
                if source_rel_node:
                    relationship_text = self._format_relationship_context(source_rel_node, rel, source_node)
                    
                    contexts.append(RetrievalContext(
                        text=relationship_text,
                        source=f"Knowledge Graph - {rel.relationship_type} (Incoming)",
                        relevance_score=rel.confidence * 0.7,
                        metadata={
                            'search_type': 'graph_traversal',
                            'relationship_type': rel.relationship_type,
                            'source_node_id': source_rel_node.id,
                            'target_node_id': source_node.id,
                            'confidence': rel.confidence,
                            'page_reference': source_rel_node.properties.get('page_reference'),
                            'document_id': source_rel_node.properties.get('document_id')
                        }
                    ))
            
        except Exception as e:
            logger.error(f"Error traversing relationships for entity {entity_id}: {e}")
        
        return contexts
    
    def _search_medical_relationships(self, question: str) -> List[RetrievalContext]:
        """Search for specific medical relationships based on question content."""
        contexts = []
        
        try:
            # Look for diagnosis-related questions
            if any(term in question.lower() for term in ['diagnosis', 'diagnose', 'condition', 'disease']):
                diagnosis_contexts = self._get_diagnosis_relationships()
                contexts.extend(diagnosis_contexts)
            
            # Look for impairment rating questions
            if any(term in question.lower() for term in ['impairment', 'rating', 'disability', 'ama', 'table']):
                impairment_contexts = self._get_impairment_relationships()
                contexts.extend(impairment_contexts)
            
            # Look for finding-related questions
            if any(term in question.lower() for term in ['finding', 'examination', 'test', 'result']):
                finding_contexts = self._get_finding_relationships()
                contexts.extend(finding_contexts)
            
        except Exception as e:
            logger.error(f"Error searching medical relationships: {e}")
        
        return contexts
    
    def _get_diagnosis_relationships(self) -> List[RetrievalContext]:
        """Get diagnosis-related contexts from knowledge graph."""
        contexts = []
        
        try:
            # Find diagnosis nodes
            diagnosis_nodes = self.kg_repository.find_nodes_by_type('diagnosis')
            
            for diagnosis in diagnosis_nodes[:5]:  # Limit to top 5
                # Get related impairment ratings
                impairment_rels = self.kg_repository.find_relationships_by_source(diagnosis.id)
                
                for rel in impairment_rels:
                    if rel.relationship_type == 'HAS_RATING':
                        target_node = self.kg_repository.find_node_by_id(rel.target_node_id)
                        if target_node:
                            context_text = f"Diagnosis: {diagnosis.properties.get('description', 'Unknown')} " \
                                         f"has impairment rating: {target_node.properties.get('percentage', 'Unknown')}% " \
                                         f"based on AMA table {target_node.properties.get('ama_table', 'Unknown')}"
                            
                            contexts.append(RetrievalContext(
                                text=context_text,
                                source=f"Medical Knowledge - Diagnosis to Impairment",
                                relevance_score=0.8,
                                metadata={
                                    'search_type': 'medical_relationship',
                                    'relationship_type': 'diagnosis_impairment',
                                    'diagnosis_id': diagnosis.id,
                                    'impairment_id': target_node.id,
                                    'page_reference': target_node.properties.get('source_page'),
                                    'document_id': diagnosis.properties.get('document_id')
                                }
                            ))
            
        except Exception as e:
            logger.error(f"Error getting diagnosis relationships: {e}")
        
        return contexts
    
    def _get_impairment_relationships(self) -> List[RetrievalContext]:
        """Get impairment rating contexts from knowledge graph."""
        contexts = []
        
        try:
            # Find impairment rating nodes
            impairment_nodes = self.kg_repository.find_nodes_by_type('impairment_rating')
            
            for impairment in impairment_nodes[:5]:  # Limit to top 5
                context_text = f"Impairment Rating: {impairment.properties.get('percentage', 'Unknown')}% " \
                             f"from AMA Table {impairment.properties.get('ama_table', 'Unknown')}. " \
                             f"Rationale: {impairment.properties.get('rationale', 'Not specified')}"
                
                contexts.append(RetrievalContext(
                    text=context_text,
                    source="Medical Knowledge - Impairment Ratings",
                    relevance_score=0.8,
                    metadata={
                        'search_type': 'medical_relationship',
                        'relationship_type': 'impairment_rating',
                        'impairment_id': impairment.id,
                        'page_reference': impairment.properties.get('source_page'),
                        'document_id': impairment.properties.get('document_id'),
                        'ama_table': impairment.properties.get('ama_table')
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error getting impairment relationships: {e}")
        
        return contexts
    
    def _get_finding_relationships(self) -> List[RetrievalContext]:
        """Get medical finding contexts from knowledge graph."""
        contexts = []
        
        try:
            # Find finding nodes
            finding_nodes = self.kg_repository.find_nodes_by_type('finding')
            
            for finding in finding_nodes[:5]:  # Limit to top 5
                context_text = f"Medical Finding: {finding.properties.get('description', 'Unknown')} " \
                             f"(Type: {finding.properties.get('finding_type', 'Unknown')})"
                
                contexts.append(RetrievalContext(
                    text=context_text,
                    source="Medical Knowledge - Findings",
                    relevance_score=0.7,
                    metadata={
                        'search_type': 'medical_relationship',
                        'relationship_type': 'finding',
                        'finding_id': finding.id,
                        'page_reference': finding.properties.get('page_reference'),
                        'document_id': finding.properties.get('document_id')
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error getting finding relationships: {e}")
        
        return contexts
    
    def _format_relationship_context(self, source_node, relationship, target_node) -> str:
        """Format a relationship into readable context text."""
        source_desc = source_node.properties.get('description', source_node.properties.get('name', 'Unknown'))
        target_desc = target_node.properties.get('description', target_node.properties.get('name', 'Unknown'))
        
        relationship_text = f"{source_node.node_type.title()}: {source_desc} " \
                          f"{relationship.relationship_type.replace('_', ' ').lower()} " \
                          f"{target_node.node_type.title()}: {target_desc}"
        
        # Add additional context if available
        if 'rationale' in target_node.properties:
            relationship_text += f". Rationale: {target_node.properties['rationale']}"
        
        if 'percentage' in target_node.properties:
            relationship_text += f". Rating: {target_node.properties['percentage']}%"
        
        return relationship_text
    
    def _keyword_fallback(self, question: str, document_content: Dict[str, Any]) -> List[RetrievalContext]:
        """Fallback to keyword search when vector/graph search fails."""
        keyword_strategy = KeywordRetrievalStrategy()
        return keyword_strategy.retrieve_context(question, document_content)
    
    def _deduplicate_contexts(self, contexts: List[RetrievalContext]) -> List[RetrievalContext]:
        """Remove duplicate contexts based on text similarity."""
        if not contexts:
            return contexts
        
        unique_contexts = []
        seen_texts = set()
        
        for context in contexts:
            # Simple deduplication based on text content
            text_key = context.text.strip().lower()[:100]  # First 100 chars
            
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_contexts.append(context)
        
        return unique_contexts


class KeywordRetrievalStrategy(RetrievalStrategy):
    """Simple keyword-based retrieval strategy."""
    
    def retrieve_context(self, question: str, document_content: Dict[str, Any]) -> List[RetrievalContext]:
        """Retrieve context using keyword matching."""
        question_terms = self._extract_key_terms(question.lower())
        context_sections = []
        
        # Search in different parts of the document
        sections_to_search = [
            ('original_text', document_content.get('original_text', ''), 'Document Content'),
            ('extracted_info', json.dumps(document_content.get('extracted_info', {}), indent=2), 'Extracted Information'),
            ('analysis', document_content.get('analysis', ''), 'Analysis'),
            ('summary', document_content.get('summary', ''), 'Summary')
        ]
        
        for section_name, content, display_name in sections_to_search:
            if not content:
                continue
                
            # Find relevant passages
            relevant_passages = self._find_relevant_passages(question_terms, content, display_name)
            context_sections.extend(relevant_passages)
        
        # Sort by relevance score and return top sections
        context_sections.sort(key=lambda x: x.relevance_score, reverse=True)
        return context_sections[:5]  # Return top 5 most relevant sections
    
    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key terms from a question for context matching."""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'was', 'were',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'can', 'could', 'should', 'would', 'will',
            'shall', 'may', 'might', 'must', 'do', 'does', 'did', 'have', 'has', 'had'
        }
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', question.lower())
        
        # Filter out stop words and short words
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return key_terms
    
    def _find_relevant_passages(self, question_terms: List[str], content: str, source_name: str) -> List[RetrievalContext]:
        """Find relevant passages in content based on question terms."""
        if not content or not question_terms:
            return []
        
        content_lower = content.lower()
        passages = []
        
        # Split content into sentences/paragraphs
        sentences = re.split(r'[.!?]\s+', content)
        
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 20:  # Skip very short sentences
                continue
                
            sentence_lower = sentence.lower()
            
            # Calculate relevance score based on term matches
            matches = sum(1 for term in question_terms if term in sentence_lower)
            
            if matches > 0:
                # Calculate relevance score
                relevance_score = matches / len(question_terms)
                
                # Add context around the sentence
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 2)
                context_text = '. '.join(sentences[start_idx:end_idx]).strip()
                
                passages.append(RetrievalContext(
                    text=context_text,
                    source=source_name,
                    relevance_score=relevance_score,
                    metadata={'matches': matches, 'sentence_index': i}
                ))
        
        return passages


class GeminiLLMStrategy(LLMStrategy):
    """LLM strategy using Google Gemini API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini LLM strategy.
        
        Args:
            api_key: Gemini API key
        """
        self.api_key = api_key
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        if not api_key:
            raise ValueError("Gemini API key is required for GeminiLLMStrategy")
        
        logger.info("Initialized GeminiLLMStrategy")
    
    def generate_answer(self, question: str, context: List[RetrievalContext]) -> str:
        """Generate answer using Gemini API with provided context."""
        if not context:
            return "I couldn't find relevant information in the document to answer your question."
        
        # Prepare context for the prompt
        context_text = "\n\n".join([
            f"**{ctx.source}:**\n{ctx.text}"
            for ctx in context
        ])
        
        prompt = f"""
        You are a helpful assistant that answers questions about documents. Use only the provided context to answer the question. If the context doesn't contain enough information to answer the question, say so clearly.

        Context from the document:
        {context_text}

        Question: {question}

        Instructions:
        1. Answer based only on the provided context
        2. Be specific and cite relevant parts of the context
        3. If the context doesn't contain the answer, say "The document doesn't contain enough information to answer this question"
        4. Keep your answer concise but complete
        5. Use a helpful, professional tone

        Answer:
        """
        
        try:
            return self._call_gemini_api(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"Error generating answer with Gemini: {e}")
            return "I'm sorry, I encountered an error while generating the answer. Please try again."
    
    def _call_gemini_api(self, prompt: str, max_tokens: int = 500) -> str:
        """Make API call to Gemini."""
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3  # Lower temperature for more focused answers
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        if not REQUESTS_AVAILABLE:
            raise Exception("requests library is not available. Please install it to use Gemini API.")
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API request failed: {e}")
            raise Exception(f"Gemini API error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Gemini response format: {e}")
            raise Exception(f"Unexpected API response format: {str(e)}")


class OpenAILLMStrategy(LLMStrategy):
    """LLM strategy using OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI LLM strategy.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if not api_key:
            raise ValueError("OpenAI API key is required for OpenAILLMStrategy")
        
        logger.info(f"Initialized OpenAILLMStrategy with model: {model}")
    
    def generate_answer(self, question: str, context: List[RetrievalContext]) -> str:
        """Generate answer using OpenAI API with provided context."""
        if not context:
            return "I couldn't find relevant information in the document to answer your question."
        
        # Prepare context for the prompt
        context_text = "\n\n".join([
            f"**{ctx.source}:**\n{ctx.text}"
            for ctx in context
        ])
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions about documents. Use only the provided context to answer questions. If the context doesn't contain enough information, say so clearly."
            },
            {
                "role": "user",
                "content": f"""Context from the document:
{context_text}

Question: {question}

Please answer based only on the provided context. Be specific and cite relevant parts of the context."""
            }
        ]
        
        try:
            return self._call_openai_api(messages)
        except Exception as e:
            logger.error(f"Error generating answer with OpenAI: {e}")
            return "I'm sorry, I encountered an error while generating the answer. Please try again."
    
    def _call_openai_api(self, messages: List[Dict[str, str]]) -> str:
        """Make API call to OpenAI."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        if not REQUESTS_AVAILABLE:
            raise Exception("requests library is not available. Please install it to use OpenAI API.")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenAI response format: {e}")
            raise Exception(f"Unexpected API response format: {str(e)}")


class OpenRouterLLMStrategy(LLMStrategy):
    """LLM strategy using OpenRouter API for Sonoma Sky."""
    
    def __init__(self, api_key: str, model: str = "openrouter/sonoma-sky-alpha"):
        """
        Initialize OpenRouter LLM strategy.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (default: Sonoma Sky Alpha)
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not api_key:
            raise ValueError("OpenRouter API key is required for OpenRouterLLMStrategy")
        
        logger.info(f"Initialized OpenRouterLLMStrategy with model: {model}")
    
    def generate_answer(self, question: str, context: List[RetrievalContext]) -> str:
        """Generate answer using OpenRouter API with provided context."""
        if not context:
            return "I couldn't find relevant information in the document to answer your question."
        
        # Prepare context for the prompt
        context_text = "\n\n".join([
            f"**{ctx.source}:**\n{ctx.text}"
            for ctx in context
        ])
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions about documents. Use only the provided context to answer questions. If the context doesn't contain enough information, say so clearly. Be precise and professional in your responses."
            },
            {
                "role": "user",
                "content": f"""Context from the document:
{context_text}

Question: {question}

Please answer based only on the provided context. Be specific and cite relevant parts of the context. If the context doesn't contain sufficient information to answer the question, clearly state that."""
            }
        ]
        
        try:
            return self._call_openrouter_api(messages)
        except Exception as e:
            logger.error(f"Error generating answer with OpenRouter: {e}")
            return "I'm sorry, I encountered an error while generating the answer. Please try again."
    
    def _call_openrouter_api(self, messages: List[Dict[str, str]]) -> str:
        """Make API call to OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8501",  # Required by OpenRouter
            "X-Title": "QME Document Analysis System"  # Optional but recommended
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        if not REQUESTS_AVAILABLE:
            raise Exception("requests library is not available. Please install it to use OpenRouter API.")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"OpenRouter API error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenRouter response format: {e}")
            raise Exception(f"Unexpected API response format: {str(e)}")


class HybridQAStrategy(QAStrategy):
    """
    Hybrid Q&A strategy that combines vector search and LLM generation.
    Uses retrieval strategy to find relevant context and LLM strategy to generate answers.
    """
    
    def __init__(self, retrieval_strategy: RetrievalStrategy, llm_strategy: LLMStrategy):
        """
        Initialize hybrid Q&A strategy.
        
        Args:
            retrieval_strategy: Strategy for retrieving relevant context
            llm_strategy: Strategy for generating answers with LLM
        """
        self.retrieval_strategy = retrieval_strategy
        self.llm_strategy = llm_strategy
        
        logger.info(f"Initialized HybridQAStrategy with {type(retrieval_strategy).__name__} and {type(llm_strategy).__name__}")
    
    def answer_question(self, question: str, document_content: Dict[str, Any]) -> QAResponse:
        """
        Answer a question using hybrid retrieval and generation.
        
        Args:
            question: User's question
            document_content: Document content and metadata
            
        Returns:
            QAResponse with answer, sources, and metadata
        """
        try:
            # Step 1: Retrieve relevant context
            context = self.retrieval_strategy.retrieve_context(question, document_content)
            
            if not context:
                return QAResponse(
                    answer="I couldn't find relevant information in the document to answer your question.",
                    sources=[],
                    confidence=0.2,
                    metadata={'error': 'No relevant context found'}
                )
            
            # Step 2: Generate answer using LLM
            answer = self.llm_strategy.generate_answer(question, context)
            
            # Step 3: Extract sources and calculate confidence
            sources = self._extract_sources(context)
            confidence = self._calculate_confidence(context, answer)
            
            # Step 4: Prepare metadata
            metadata = {
                'context_count': len(context),
                'retrieval_strategy': type(self.retrieval_strategy).__name__,
                'llm_strategy': type(self.llm_strategy).__name__,
                'avg_relevance_score': sum(ctx.relevance_score for ctx in context) / len(context) if context else 0.0
            }
            
            return QAResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error in hybrid Q&A strategy: {e}")
            return QAResponse(
                answer="I'm sorry, I encountered an error while processing your question. Please try again.",
                sources=[],
                confidence=0.0,
                metadata={'error': str(e)}
            )
    
    def _extract_sources(self, context: List[RetrievalContext]) -> List[str]:
        """Extract source references with page numbers and provenance information."""
        sources = []
        for ctx in context:
            source_info = f"{ctx.source}"
            
            # Add page reference if available
            if 'page_reference' in ctx.metadata and ctx.metadata['page_reference']:
                source_info += f" (Page {ctx.metadata['page_reference']})"
            
            # Add document reference if available
            if 'document_id' in ctx.metadata and ctx.metadata['document_id']:
                doc_id = ctx.metadata['document_id']
                source_info += f" [Doc: {doc_id}]"
            
            # Add AMA table reference for impairment ratings
            if 'ama_table' in ctx.metadata and ctx.metadata['ama_table']:
                source_info += f" [AMA Table: {ctx.metadata['ama_table']}]"
            
            # Add confidence/relevance score
            if ctx.relevance_score > 0:
                source_info += f" (Confidence: {ctx.relevance_score:.2f})"
            
            sources.append(source_info)
        
        return list(set(sources))  # Remove duplicates
    
    def _calculate_confidence(self, context: List[RetrievalContext], answer: str) -> float:
        """Calculate confidence score based on context quality and answer."""
        if not context:
            return 0.0
        
        # Base confidence on average relevance score
        avg_relevance = sum(ctx.relevance_score for ctx in context) / len(context)
        
        # Adjust based on answer quality indicators
        confidence = avg_relevance * 0.8  # Start with 80% of relevance score
        
        # Boost confidence if answer doesn't indicate uncertainty
        uncertainty_phrases = [
            "don't contain enough information",
            "couldn't find",
            "not mentioned",
            "unclear",
            "uncertain"
        ]
        
        if not any(phrase in answer.lower() for phrase in uncertainty_phrases):
            confidence += 0.2
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)


class QAStrategyFactory:
    """Factory for creating Q&A strategies."""
    
    @staticmethod
    def create_hybrid_strategy(retrieval_type: str = "keyword", 
                             llm_type: str = "gemini", 
                             **kwargs) -> HybridQAStrategy:
        """
        Create a hybrid Q&A strategy.
        
        Args:
            retrieval_type: Type of retrieval strategy ('keyword', 'vector_graph')
            llm_type: Type of LLM strategy ('gemini', 'openai', or 'openrouter')
            **kwargs: Additional arguments for strategy initialization
            
        Returns:
            HybridQAStrategy instance
        """
        # Create retrieval strategy
        if retrieval_type.lower() == "keyword":
            retrieval_strategy = KeywordRetrievalStrategy()
        elif retrieval_type.lower() == "vector_graph":
            # Vector graph retrieval requires additional dependencies
            vector_store = kwargs.get('vector_store')
            kg_repository = kwargs.get('kg_repository')
            embedding_strategy = kwargs.get('embedding_strategy')
            
            if not all([vector_store, kg_repository, embedding_strategy]):
                raise ValueError("vector_store, kg_repository, and embedding_strategy are required for vector_graph retrieval")
            
            retrieval_strategy = VectorGraphRetrievalStrategy(
                vector_store=vector_store,
                kg_repository=kg_repository,
                embedding_strategy=embedding_strategy
            )
        else:
            raise ValueError(f"Unsupported retrieval strategy: {retrieval_type}")
        
        # Create LLM strategy
        if llm_type.lower() == "gemini":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("api_key is required for Gemini LLM strategy")
            llm_strategy = GeminiLLMStrategy(api_key)
        elif llm_type.lower() == "openai":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("api_key is required for OpenAI LLM strategy")
            model = kwargs.get('model', 'gpt-3.5-turbo')
            llm_strategy = OpenAILLMStrategy(api_key, model)
        elif llm_type.lower() == "openrouter":
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("api_key is required for OpenRouter LLM strategy")
            model = kwargs.get('model', 'openrouter/sonoma-sky-alpha')
            llm_strategy = OpenRouterLLMStrategy(api_key, model)
        else:
            raise ValueError(f"Unsupported LLM strategy: {llm_type}")
        
        return HybridQAStrategy(retrieval_strategy, llm_strategy)
    
    @staticmethod
    def create_llm_strategy(llm_type: str, api_key: str, model: str = None) -> LLMStrategy:
        """
        Create an LLM strategy instance.
        
        Args:
            llm_type: Type of LLM strategy ('gemini', 'openai', or 'openrouter')
            api_key: API key for the LLM service
            model: Optional model name (uses defaults if not provided)
            
        Returns:
            LLMStrategy instance
        """
        if llm_type.lower() == "gemini":
            return GeminiLLMStrategy(api_key)
        elif llm_type.lower() == "openai":
            model = model or 'gpt-3.5-turbo'
            return OpenAILLMStrategy(api_key, model)
        elif llm_type.lower() == "openrouter":
            model = model or 'openrouter/sonoma-sky-alpha'
            return OpenRouterLLMStrategy(api_key, model)
        else:
            raise ValueError(f"Unsupported LLM strategy: {llm_type}")
    
    @staticmethod
    def get_supported_llm_types() -> List[str]:
        """Get list of supported LLM types."""
        return ['gemini', 'openai', 'openrouter']
    
    @staticmethod
    def get_supported_retrieval_types() -> List[str]:
        """Get list of supported retrieval types."""
        return ['keyword', 'vector_graph']