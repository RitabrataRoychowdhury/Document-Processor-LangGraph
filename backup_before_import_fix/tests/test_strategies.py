"""
Tests for strategy pattern implementations.
"""

import pytest
from unittest.mock import Mock, patch

from src.strategies.embedding_strategy import (
    LocalEmbeddingStrategy, 
    OpenAIEmbeddingStrategy, 
    EmbeddingStrategyFactory
)
from src.strategies.qa_strategy import (
    KeywordRetrievalStrategy,
    GeminiLLMStrategy,
    OpenAILLMStrategy,
    HybridQAStrategy,
    QAStrategyFactory,
    RetrievalContext
)


class TestLocalEmbeddingStrategy:
    """Test cases for LocalEmbeddingStrategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = LocalEmbeddingStrategy()
        assert strategy.model_name == "all-MiniLM-L6-v2"
        assert strategy.get_embedding_dimension() == 384
        assert strategy.get_strategy_name() == "Local-all-MiniLM-L6-v2"
    
    def test_generate_embeddings(self):
        """Test embedding generation."""
        strategy = LocalEmbeddingStrategy()
        embeddings = strategy.generate_embeddings("test text")
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 384
        assert all(isinstance(x, float) for x in embeddings)
    
    def test_generate_embeddings_empty_text(self):
        """Test embedding generation with empty text."""
        strategy = LocalEmbeddingStrategy()
        embeddings = strategy.generate_embeddings("")
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 384
        assert all(x == 0.0 for x in embeddings)
    
    def test_deterministic_embeddings(self):
        """Test that same text produces same embeddings."""
        strategy = LocalEmbeddingStrategy()
        embeddings1 = strategy.generate_embeddings("test text")
        embeddings2 = strategy.generate_embeddings("test text")
        
        assert embeddings1 == embeddings2


class TestOpenAIEmbeddingStrategy:
    """Test cases for OpenAIEmbeddingStrategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = OpenAIEmbeddingStrategy("test-api-key")
        assert strategy.api_key == "test-api-key"
        assert strategy.model == "text-embedding-ada-002"
        assert strategy.get_embedding_dimension() == 1536
        assert strategy.get_strategy_name() == "OpenAI-text-embedding-ada-002"
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key raises error."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            OpenAIEmbeddingStrategy("")
    
    @patch('src.strategies.embedding_strategy.requests.post')
    def test_generate_embeddings_success(self, mock_post):
        """Test successful embedding generation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_post.return_value = mock_response
        
        strategy = OpenAIEmbeddingStrategy("test-api-key")
        embeddings = strategy.generate_embeddings("test text")
        
        assert embeddings == [0.1, 0.2, 0.3]
        mock_post.assert_called_once()
    
    @patch('src.strategies.embedding_strategy.requests.post')
    def test_generate_embeddings_api_error(self, mock_post):
        """Test API error handling."""
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        strategy = OpenAIEmbeddingStrategy("test-api-key")
        
        with pytest.raises(Exception):
            strategy.generate_embeddings("test text")


class TestEmbeddingStrategyFactory:
    """Test cases for EmbeddingStrategyFactory."""
    
    def test_create_local_strategy(self):
        """Test creating local strategy."""
        strategy = EmbeddingStrategyFactory.create_local_strategy()
        assert isinstance(strategy, LocalEmbeddingStrategy)
        assert strategy.model_name == "all-MiniLM-L6-v2"
    
    def test_create_openai_strategy(self):
        """Test creating OpenAI strategy."""
        strategy = EmbeddingStrategyFactory.create_openai_strategy("test-key")
        assert isinstance(strategy, OpenAIEmbeddingStrategy)
        assert strategy.api_key == "test-key"
    
    def test_create_strategy_local(self):
        """Test creating strategy by type - local."""
        strategy = EmbeddingStrategyFactory.create_strategy("local")
        assert isinstance(strategy, LocalEmbeddingStrategy)
    
    def test_create_strategy_openai(self):
        """Test creating strategy by type - OpenAI."""
        strategy = EmbeddingStrategyFactory.create_strategy("openai", api_key="test-key")
        assert isinstance(strategy, OpenAIEmbeddingStrategy)
    
    def test_create_strategy_unsupported(self):
        """Test error for unsupported strategy type."""
        with pytest.raises(ValueError, match="Unsupported embedding strategy type"):
            EmbeddingStrategyFactory.create_strategy("unsupported")
    
    def test_create_strategy_openai_without_key(self):
        """Test error when creating OpenAI strategy without API key."""
        with pytest.raises(ValueError, match="api_key is required"):
            EmbeddingStrategyFactory.create_strategy("openai")


class TestKeywordRetrievalStrategy:
    """Test cases for KeywordRetrievalStrategy."""
    
    def test_retrieve_context(self):
        """Test context retrieval."""
        strategy = KeywordRetrievalStrategy()
        
        document_content = {
            'original_text': 'This is a test document about machine learning and AI.',
            'summary': 'A document discussing artificial intelligence topics.'
        }
        
        context = strategy.retrieve_context("What is machine learning?", document_content)
        
        assert isinstance(context, list)
        assert len(context) > 0
        assert all(isinstance(ctx, RetrievalContext) for ctx in context)
    
    def test_extract_key_terms(self):
        """Test key term extraction."""
        strategy = KeywordRetrievalStrategy()
        terms = strategy._extract_key_terms("What is machine learning and AI?")
        
        assert "machine" in terms
        assert "learning" in terms
        assert "what" not in terms  # Stop word should be filtered
        assert "is" not in terms    # Stop word should be filtered


class TestGeminiLLMStrategy:
    """Test cases for GeminiLLMStrategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = GeminiLLMStrategy("test-api-key")
        assert strategy.api_key == "test-api-key"
        assert "gemini" in strategy.api_url.lower()
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key raises error."""
        with pytest.raises(ValueError, match="Gemini API key is required"):
            GeminiLLMStrategy("")
    
    @patch('src.strategies.qa_strategy.requests.post')
    def test_generate_answer_success(self, mock_post):
        """Test successful answer generation."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Test answer"}]}}]
        }
        mock_post.return_value = mock_response
        
        strategy = GeminiLLMStrategy("test-api-key")
        context = [RetrievalContext("Test context", "Document", 0.8, {})]
        
        answer = strategy.generate_answer("Test question?", context)
        assert answer == "Test answer"
        mock_post.assert_called_once()
    
    def test_generate_answer_no_context(self):
        """Test answer generation with no context."""
        strategy = GeminiLLMStrategy("test-api-key")
        answer = strategy.generate_answer("Test question?", [])
        
        assert "couldn't find relevant information" in answer


class TestHybridQAStrategy:
    """Test cases for HybridQAStrategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        retrieval_strategy = KeywordRetrievalStrategy()
        llm_strategy = GeminiLLMStrategy("test-key")
        
        qa_strategy = HybridQAStrategy(retrieval_strategy, llm_strategy)
        
        assert qa_strategy.retrieval_strategy == retrieval_strategy
        assert qa_strategy.llm_strategy == llm_strategy
    
    @patch('src.strategies.qa_strategy.requests.post')
    def test_answer_question_success(self, mock_post):
        """Test successful question answering."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Test answer"}]}}]
        }
        mock_post.return_value = mock_response
        
        retrieval_strategy = KeywordRetrievalStrategy()
        llm_strategy = GeminiLLMStrategy("test-key")
        qa_strategy = HybridQAStrategy(retrieval_strategy, llm_strategy)
        
        document_content = {
            'original_text': 'This document contains information about machine learning.',
            'summary': 'ML document'
        }
        
        response = qa_strategy.answer_question("What is machine learning?", document_content)
        
        assert response.answer == "Test answer"
        assert isinstance(response.sources, list)
        assert isinstance(response.confidence, float)
        assert isinstance(response.metadata, dict)
    
    def test_answer_question_no_context(self):
        """Test question answering with no relevant context."""
        retrieval_strategy = KeywordRetrievalStrategy()
        llm_strategy = GeminiLLMStrategy("test-key")
        qa_strategy = HybridQAStrategy(retrieval_strategy, llm_strategy)
        
        document_content = {
            'original_text': 'This document is about cooking recipes.',
            'summary': 'Cooking document'
        }
        
        response = qa_strategy.answer_question("What is quantum physics?", document_content)
        
        assert "couldn't find relevant information" in response.answer
        assert response.confidence == 0.2


class TestQAStrategyFactory:
    """Test cases for QAStrategyFactory."""
    
    def test_create_hybrid_strategy_gemini(self):
        """Test creating hybrid strategy with Gemini."""
        strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type="keyword",
            llm_type="gemini",
            api_key="test-key"
        )
        
        assert isinstance(strategy, HybridQAStrategy)
        assert isinstance(strategy.retrieval_strategy, KeywordRetrievalStrategy)
        assert isinstance(strategy.llm_strategy, GeminiLLMStrategy)
    
    def test_create_hybrid_strategy_openai(self):
        """Test creating hybrid strategy with OpenAI."""
        strategy = QAStrategyFactory.create_hybrid_strategy(
            retrieval_type="keyword",
            llm_type="openai",
            api_key="test-key"
        )
        
        assert isinstance(strategy, HybridQAStrategy)
        assert isinstance(strategy.retrieval_strategy, KeywordRetrievalStrategy)
        assert isinstance(strategy.llm_strategy, OpenAILLMStrategy)
    
    def test_create_hybrid_strategy_unsupported_retrieval(self):
        """Test error for unsupported retrieval strategy."""
        with pytest.raises(ValueError, match="Unsupported retrieval strategy"):
            QAStrategyFactory.create_hybrid_strategy(
                retrieval_type="unsupported",
                llm_type="gemini",
                api_key="test-key"
            )
    
    def test_create_hybrid_strategy_unsupported_llm(self):
        """Test error for unsupported LLM strategy."""
        with pytest.raises(ValueError, match="Unsupported LLM strategy"):
            QAStrategyFactory.create_hybrid_strategy(
                retrieval_type="keyword",
                llm_type="unsupported",
                api_key="test-key"
            )
    
    def test_create_hybrid_strategy_missing_api_key(self):
        """Test error when API key is missing."""
        with pytest.raises(ValueError, match="api_key is required"):
            QAStrategyFactory.create_hybrid_strategy(
                retrieval_type="keyword",
                llm_type="gemini"
            )