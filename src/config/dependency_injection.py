"""
Dependency injection configuration for the document Q&A system.
Provides centralized configuration and creation of strategy instances.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.strategies.embedding_strategy import EmbeddingStrategy, EmbeddingStrategyFactory
from src.strategies.qa_strategy import QAStrategy, QAStrategyFactory
from src.factories.processor_factory import ProcessorFactory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Database
    database_path: str = "data/database/documents.db"
    
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    
    # Processing
    max_file_size_mb: int = 10
    allowed_file_types: list = None
    
    # Embedding Strategy
    embedding_provider: str = "local"  # "openai" or "local"
    embedding_model: str = "all-MiniLM-L6-v2"  # For local, or "text-embedding-ada-002" for OpenAI
    
    # QA Strategy
    qa_provider: str = "gemini"  # "gemini", "openai"
    qa_model: str = "gemini-2.0-flash"  # For Gemini, or "gpt-3.5-turbo" for OpenAI
    retrieval_strategy: str = "keyword"  # "keyword" (more strategies can be added later)
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.allowed_file_types is None:
            self.allowed_file_types = [".pdf", ".docx", ".txt"]
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            AppConfig instance with values from environment
        """
        return cls(
            database_path=os.getenv("DATABASE_PATH", "data/database/documents.db"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            qa_provider=os.getenv("QA_PROVIDER", "gemini"),
            qa_model=os.getenv("QA_MODEL", "gemini-2.0-flash"),
            retrieval_strategy=os.getenv("RETRIEVAL_STRATEGY", "keyword")
        )


class DependencyContainer:
    """Container for managing application dependencies."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize dependency container.
        
        Args:
            config: Application configuration. If None, loads from environment.
        """
        self.config = config or AppConfig.from_env()
        self._processor_factory = None
        self._embedding_strategy = None
        self._qa_strategy = None
        
        logger.info(f"Initialized DependencyContainer with config: "
                   f"embedding_provider={self.config.embedding_provider}, "
                   f"qa_provider={self.config.qa_provider}")
    
    def get_processor_factory(self) -> ProcessorFactory:
        """
        Get processor factory instance.
        
        Returns:
            ProcessorFactory instance
        """
        if self._processor_factory is None:
            self._processor_factory = ProcessorFactory()
            logger.info("Created ProcessorFactory instance")
        
        return self._processor_factory
    
    def get_embedding_strategy(self) -> EmbeddingStrategy:
        """
        Get embedding strategy instance based on configuration.
        
        Returns:
            EmbeddingStrategy instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        if self._embedding_strategy is None:
            try:
                if self.config.embedding_provider.lower() == "local":
                    self._embedding_strategy = EmbeddingStrategyFactory.create_local_strategy(
                        model_name=self.config.embedding_model
                    )
                elif self.config.embedding_provider.lower() == "openai":
                    if not self.config.openai_api_key:
                        raise ValueError("OpenAI API key is required for OpenAI embedding strategy")
                    
                    self._embedding_strategy = EmbeddingStrategyFactory.create_openai_strategy(
                        api_key=self.config.openai_api_key,
                        model=self.config.embedding_model
                    )
                else:
                    raise ValueError(f"Unsupported embedding provider: {self.config.embedding_provider}")
                
                logger.info(f"Created {type(self._embedding_strategy).__name__} instance")
                
            except Exception as e:
                logger.error(f"Failed to create embedding strategy: {e}")
                # Fallback to local strategy
                logger.info("Falling back to local embedding strategy")
                self._embedding_strategy = EmbeddingStrategyFactory.create_local_strategy()
        
        return self._embedding_strategy
    
    def get_qa_strategy(self) -> QAStrategy:
        """
        Get Q&A strategy instance based on configuration.
        
        Returns:
            QAStrategy instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        if self._qa_strategy is None:
            try:
                if self.config.qa_provider.lower() == "gemini":
                    if not self.config.gemini_api_key:
                        raise ValueError("Gemini API key is required for Gemini Q&A strategy")
                    
                    self._qa_strategy = QAStrategyFactory.create_hybrid_strategy(
                        retrieval_type=self.config.retrieval_strategy,
                        llm_type="gemini",
                        api_key=self.config.gemini_api_key
                    )
                elif self.config.qa_provider.lower() == "openai":
                    if not self.config.openai_api_key:
                        raise ValueError("OpenAI API key is required for OpenAI Q&A strategy")
                    
                    self._qa_strategy = QAStrategyFactory.create_hybrid_strategy(
                        retrieval_type=self.config.retrieval_strategy,
                        llm_type="openai",
                        api_key=self.config.openai_api_key,
                        model=self.config.qa_model
                    )
                else:
                    raise ValueError(f"Unsupported Q&A provider: {self.config.qa_provider}")
                
                logger.info(f"Created {type(self._qa_strategy).__name__} instance")
                
            except Exception as e:
                logger.error(f"Failed to create Q&A strategy: {e}")
                raise
        
        return self._qa_strategy
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check API keys based on configured providers
        if self.config.embedding_provider.lower() == "openai" and not self.config.openai_api_key:
            validation_results["errors"].append("OpenAI API key is required for OpenAI embedding provider")
            validation_results["valid"] = False
        
        if self.config.qa_provider.lower() == "gemini" and not self.config.gemini_api_key:
            validation_results["errors"].append("Gemini API key is required for Gemini Q&A provider")
            validation_results["valid"] = False
        
        if self.config.qa_provider.lower() == "openai" and not self.config.openai_api_key:
            validation_results["errors"].append("OpenAI API key is required for OpenAI Q&A provider")
            validation_results["valid"] = False
        
        # Check file size limits
        if self.config.max_file_size_mb <= 0:
            validation_results["errors"].append("Max file size must be greater than 0")
            validation_results["valid"] = False
        
        # Check database path
        database_dir = os.path.dirname(self.config.database_path)
        if database_dir and not os.path.exists(database_dir):
            validation_results["warnings"].append(f"Database directory does not exist: {database_dir}")
        
        # Warnings for missing optional API keys
        if not self.config.gemini_api_key and not self.config.openai_api_key:
            validation_results["warnings"].append("No API keys configured. Some features may not work.")
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "database_path": self.config.database_path,
            "max_file_size_mb": self.config.max_file_size_mb,
            "allowed_file_types": self.config.allowed_file_types,
            "embedding_provider": self.config.embedding_provider,
            "embedding_model": self.config.embedding_model,
            "qa_provider": self.config.qa_provider,
            "qa_model": self.config.qa_model,
            "retrieval_strategy": self.config.retrieval_strategy,
            "has_gemini_key": bool(self.config.gemini_api_key),
            "has_openai_key": bool(self.config.openai_api_key)
        }


# Global dependency container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """
    Get the global dependency container instance.
    
    Returns:
        DependencyContainer instance
    """
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def set_container(container: DependencyContainer) -> None:
    """
    Set the global dependency container instance.
    
    Args:
        container: DependencyContainer instance to set as global
    """
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global dependency container (useful for testing)."""
    global _container
    _container = None