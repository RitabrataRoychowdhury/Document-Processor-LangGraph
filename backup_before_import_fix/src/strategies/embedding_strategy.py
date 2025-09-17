"""
Embedding strategy implementations using the Strategy Pattern.
Supports both local (SentenceTransformers) and OpenAI embedding generation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
from src.utils.logging_config import get_logger

# Conditional import for requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = get_logger(__name__)


class EmbeddingStrategy(ABC):
    """Abstract base class for embedding generation strategies."""
    
    @abstractmethod
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of float values representing the text embedding
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this strategy.
        
        Returns:
            Integer representing embedding dimension
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Get the name of this embedding strategy.
        
        Returns:
            String name of the strategy
        """
        pass


class LocalEmbeddingStrategy(EmbeddingStrategy):
    """
    Local embedding strategy using SentenceTransformers.
    Note: This is a mock implementation since sentence-transformers is not in requirements.txt
    In a real implementation, you would install sentence-transformers and use it here.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding strategy.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self._model = None
        self._embedding_dim = 384  # Default dimension for all-MiniLM-L6-v2
        
        # In a real implementation, you would do:
        # from sentence_transformers import SentenceTransformer
        # self._model = SentenceTransformer(model_name)
        # self._embedding_dim = self._model.get_sentence_embedding_dimension()
        
        logger.info(f"Initialized LocalEmbeddingStrategy with model: {model_name}")
        logger.warning("LocalEmbeddingStrategy is using mock implementation. Install sentence-transformers for real embeddings.")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using local sentence transformer model.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of float values representing the text embedding
        """
        if not text or not text.strip():
            return [0.0] * self._embedding_dim
        
        # Mock implementation - generates deterministic "embeddings" based on text hash
        # In a real implementation, you would do:
        # embeddings = self._model.encode([text])
        # return embeddings[0].tolist()
        
        # Simple hash-based mock embedding for demonstration
        text_hash = hash(text.strip().lower())
        mock_embedding = []
        
        for i in range(self._embedding_dim):
            # Generate pseudo-random values based on text hash and position
            value = ((text_hash + i * 31) % 10000) / 10000.0 - 0.5
            mock_embedding.append(value)
        
        logger.debug(f"Generated mock embedding of dimension {len(mock_embedding)} for text length {len(text)}")
        return mock_embedding
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this strategy."""
        return self._embedding_dim
    
    def get_strategy_name(self) -> str:
        """Get the name of this embedding strategy."""
        return f"Local-{self.model_name}"


class OpenAIEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy using OpenAI's embedding API."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        Initialize OpenAI embedding strategy.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI embedding model to use
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/embeddings"
        self._embedding_dim = 1536  # Default dimension for text-embedding-ada-002
        
        if not api_key:
            raise ValueError("OpenAI API key is required for OpenAIEmbeddingStrategy")
        
        logger.info(f"Initialized OpenAIEmbeddingStrategy with model: {model}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            text: Input text to generate embeddings for
            
        Returns:
            List of float values representing the text embedding
        """
        if not text or not text.strip():
            return [0.0] * self._embedding_dim
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 8000  # Conservative limit
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding generation")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": self.model
        }
        
        if not REQUESTS_AVAILABLE:
            raise Exception("requests library is not available. Please install it to use OpenAI embeddings.")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            embeddings = result["data"][0]["embedding"]
            
            logger.debug(f"Generated OpenAI embedding of dimension {len(embeddings)} for text length {len(text)}")
            return embeddings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise Exception(f"Failed to generate OpenAI embeddings: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenAI API response format: {e}")
            raise Exception(f"Unexpected OpenAI API response format: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this strategy."""
        return self._embedding_dim
    
    def get_strategy_name(self) -> str:
        """Get the name of this embedding strategy."""
        return f"OpenAI-{self.model}"


class EmbeddingStrategyFactory:
    """Factory for creating embedding strategies."""
    
    @staticmethod
    def create_local_strategy(model_name: str = "all-MiniLM-L6-v2") -> LocalEmbeddingStrategy:
        """
        Create a local embedding strategy.
        
        Args:
            model_name: Name of the sentence transformer model
            
        Returns:
            LocalEmbeddingStrategy instance
        """
        return LocalEmbeddingStrategy(model_name)
    
    @staticmethod
    def create_openai_strategy(api_key: str, model: str = "text-embedding-ada-002") -> OpenAIEmbeddingStrategy:
        """
        Create an OpenAI embedding strategy.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI embedding model name
            
        Returns:
            OpenAIEmbeddingStrategy instance
        """
        return OpenAIEmbeddingStrategy(api_key, model)
    
    @staticmethod
    def create_strategy(strategy_type: str, **kwargs) -> EmbeddingStrategy:
        """
        Create an embedding strategy based on type.
        
        Args:
            strategy_type: Type of strategy ('local' or 'openai')
            **kwargs: Additional arguments for strategy initialization
            
        Returns:
            EmbeddingStrategy instance
            
        Raises:
            ValueError: If strategy_type is not supported
        """
        strategy_type = strategy_type.lower()
        
        if strategy_type == 'local':
            model_name = kwargs.get('model_name', 'all-MiniLM-L6-v2')
            return EmbeddingStrategyFactory.create_local_strategy(model_name)
        elif strategy_type == 'openai':
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("api_key is required for OpenAI embedding strategy")
            model = kwargs.get('model', 'text-embedding-ada-002')
            return EmbeddingStrategyFactory.create_openai_strategy(api_key, model)
        else:
            raise ValueError(f"Unsupported embedding strategy type: {strategy_type}. Supported types: 'local', 'openai'")