"""
Application configuration management using environment variables for API keys and provider selection.
Supports backward compatibility with existing configuration while adding new knowledge graph features.

This module now integrates with the centralized configuration manager for consistent
environment variable loading across all components.
"""

import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Load environment variables using centralized configuration manager
try:
    from src.infrastructure.configuration.centralized_config_manager import config_manager
    _centralized_config_available = True
except ImportError:
    _centralized_config_available = False
    # Fallback to direct dotenv loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv not available, will use system environment variables
        pass


class EmbeddingProvider(Enum):
    """Supported embedding providers."""
    LOCAL = "local"
    OPENAI = "openai"


class QAProvider(Enum):
    """Supported QA providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    LOCAL = "local"


@dataclass
class AppConfig:
    """Application configuration with environment variable support."""
    
    # Database Configuration
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/database/documents.db"))
    
    # API Keys
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    
    # File Processing Configuration
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "10")))
    allowed_file_types: List[str] = field(default_factory=lambda: os.getenv("ALLOWED_FILE_TYPES", "pdf,docx,txt").split(","))
    
    # Processing Configuration
    max_processing_jobs: int = field(default_factory=lambda: int(os.getenv("MAX_PROCESSING_JOBS", "5")))
    processing_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "300")))
    
    # Provider Selection
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "local"))
    qa_provider: str = field(default_factory=lambda: os.getenv("QA_PROVIDER", "gemini"))
    
    # Knowledge Graph Configuration
    enable_knowledge_graph: bool = field(default_factory=lambda: os.getenv("ENABLE_KNOWLEDGE_GRAPH", "true").lower() == "true")
    kg_vector_store_type: str = field(default_factory=lambda: os.getenv("KG_VECTOR_STORE_TYPE", "chroma"))
    kg_embedding_model: str = field(default_factory=lambda: os.getenv("KG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    
    # UI Configuration
    streamlit_port: int = field(default_factory=lambda: int(os.getenv("STREAMLIT_PORT", "8501")))
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    
    # Storage Paths
    documents_dir: str = field(default_factory=lambda: os.getenv("DOCUMENTS_DIR", "data/documents"))
    database_dir: str = field(default_factory=lambda: os.getenv("DATABASE_DIR", "data/database"))
    
    # Backward Compatibility - Legacy Config Support
    _legacy_config_loaded: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """Post-initialization to handle legacy configuration."""
        self._load_legacy_config()
        self._normalize_file_types()
    
    def _load_legacy_config(self):
        """Load legacy configuration for backward compatibility."""
        try:
            # Try to import legacy config
            import sys
            import os as os_module
            
            # Add src directory to path
            src_dir = os_module.path.dirname(os_module.path.dirname(__file__))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            
            try:
                from config import config as legacy_config
                
                # Map legacy config values if they exist and current values are defaults
                if hasattr(legacy_config, 'GEMINI_API_KEY') and not self.gemini_api_key:
                    self.gemini_api_key = legacy_config.GEMINI_API_KEY
                
                if hasattr(legacy_config, 'DATABASE_PATH') and self.database_path == "data/database/documents.db":
                    self.database_path = legacy_config.DATABASE_PATH
                
                if hasattr(legacy_config, 'MAX_FILE_SIZE_MB') and self.max_file_size_mb == 10:
                    self.max_file_size_mb = legacy_config.MAX_FILE_SIZE_MB
                
                if hasattr(legacy_config, 'ALLOWED_FILE_TYPES') and self.allowed_file_types == ["pdf", "docx", "txt"]:
                    self.allowed_file_types = legacy_config.ALLOWED_FILE_TYPES
                
                if hasattr(legacy_config, 'MAX_PROCESSING_JOBS') and self.max_processing_jobs == 5:
                    self.max_processing_jobs = legacy_config.MAX_PROCESSING_JOBS
                
                if hasattr(legacy_config, 'PROCESSING_TIMEOUT_SECONDS') and self.processing_timeout_seconds == 300:
                    self.processing_timeout_seconds = legacy_config.PROCESSING_TIMEOUT_SECONDS
                
                if hasattr(legacy_config, 'STREAMLIT_PORT') and self.streamlit_port == 8501:
                    self.streamlit_port = legacy_config.STREAMLIT_PORT
                
                if hasattr(legacy_config, 'DEBUG_MODE') and not self.debug_mode:
                    self.debug_mode = legacy_config.DEBUG_MODE
                
                self._legacy_config_loaded = True
                
            except ImportError:
                # Legacy config not available, use environment variables only
                pass
                
        except Exception:
            # Ignore errors in legacy config loading
            pass
    
    def _normalize_file_types(self):
        """Normalize file types to lowercase without dots."""
        self.allowed_file_types = [ft.lower().lstrip('.') for ft in self.allowed_file_types]
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        return cls()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Use centralized validation if available
        if _centralized_config_available:
            try:
                validation_result = config_manager.validate_configuration()
                if not validation_result.is_valid:
                    errors.extend(validation_result.errors)
                return errors
            except Exception as e:
                errors.append(f"Centralized validation failed: {str(e)}")
        
        # Fallback to local validation
        # Validate API keys based on provider selection
        if self.qa_provider == QAProvider.GEMINI.value and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is required when using Gemini as QA provider")
        
        if self.qa_provider == QAProvider.OPENAI.value and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI as QA provider")
        
        if self.qa_provider == QAProvider.OPENROUTER.value and not self.openrouter_api_key:
            errors.append("OPENROUTER_API_KEY is required when using OpenRouter as QA provider")
        
        if self.embedding_provider == EmbeddingProvider.OPENAI.value and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when using OpenAI as embedding provider")
        
        # Validate numeric values
        if self.max_file_size_mb <= 0:
            errors.append("MAX_FILE_SIZE_MB must be positive")
        
        if self.max_processing_jobs <= 0:
            errors.append("MAX_PROCESSING_JOBS must be positive")
        
        if self.processing_timeout_seconds <= 0:
            errors.append("PROCESSING_TIMEOUT_SECONDS must be positive")
        
        # Validate provider values
        valid_embedding_providers = [p.value for p in EmbeddingProvider]
        if self.embedding_provider not in valid_embedding_providers:
            errors.append(f"EMBEDDING_PROVIDER must be one of: {', '.join(valid_embedding_providers)}")
        
        valid_qa_providers = [p.value for p in QAProvider]
        if self.qa_provider not in valid_qa_providers:
            errors.append(f"QA_PROVIDER must be one of: {', '.join(valid_qa_providers)}")
        
        # Validate file types
        if not self.allowed_file_types:
            errors.append("ALLOWED_FILE_TYPES cannot be empty")
        
        return errors
    
    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    def is_allowed_file_type(self, file_extension: str) -> bool:
        """Check if file type is allowed."""
        return file_extension.lower().lstrip('.') in self.allowed_file_types
    
    def get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for specified provider."""
        if provider == QAProvider.GEMINI.value:
            return self.gemini_api_key if self.gemini_api_key else None
        elif provider == QAProvider.OPENAI.value:
            return self.openai_api_key if self.openai_api_key else None
        elif provider == QAProvider.OPENROUTER.value:
            return self.openrouter_api_key if self.openrouter_api_key else None
        return None
    
    def is_api_configured(self) -> bool:
        """Check if required API keys are configured."""
        if self.qa_provider == QAProvider.GEMINI.value:
            return bool(self.gemini_api_key)
        elif self.qa_provider == QAProvider.OPENAI.value:
            return bool(self.openai_api_key)
        elif self.qa_provider == QAProvider.OPENROUTER.value:
            return bool(self.openrouter_api_key)
        elif self.qa_provider == QAProvider.LOCAL.value:
            return True  # Local provider doesn't need API key
        return False
    
    def get_embedding_strategy_config(self) -> Dict[str, Any]:
        """Get configuration for embedding strategy."""
        config = {
            'provider': self.embedding_provider,
            'model': self.kg_embedding_model
        }
        
        if self.embedding_provider == EmbeddingProvider.OPENAI.value:
            config['api_key'] = self.openai_api_key
        
        return config
    
    def get_qa_strategy_config(self) -> Dict[str, Any]:
        """Get configuration for QA strategy."""
        config = {
            'provider': self.qa_provider
        }
        
        if self.qa_provider == QAProvider.GEMINI.value:
            config['api_key'] = self.gemini_api_key
        elif self.qa_provider == QAProvider.OPENAI.value:
            config['api_key'] = self.openai_api_key
        elif self.qa_provider == QAProvider.OPENROUTER.value:
            config['api_key'] = self.openrouter_api_key
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database_path': self.database_path,
            'gemini_api_key': '***' if self.gemini_api_key else '',
            'openai_api_key': '***' if self.openai_api_key else '',
            'openrouter_api_key': '***' if self.openrouter_api_key else '',
            'max_file_size_mb': self.max_file_size_mb,
            'allowed_file_types': self.allowed_file_types,
            'max_processing_jobs': self.max_processing_jobs,
            'processing_timeout_seconds': self.processing_timeout_seconds,
            'embedding_provider': self.embedding_provider,
            'qa_provider': self.qa_provider,
            'enable_knowledge_graph': self.enable_knowledge_graph,
            'kg_vector_store_type': self.kg_vector_store_type,
            'kg_embedding_model': self.kg_embedding_model,
            'streamlit_port': self.streamlit_port,
            'debug_mode': self.debug_mode,
            'documents_dir': self.documents_dir,
            'database_dir': self.database_dir,
            'api_configured': self.is_api_configured(),
            'legacy_config_loaded': self._legacy_config_loaded
        }
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get configuration status information for system health checks."""
        status_info = {
            'api_key_configured': self.is_api_configured(),
            'embedding_provider': self.embedding_provider,
            'qa_provider': self.qa_provider,
            'knowledge_graph_enabled': self.enable_knowledge_graph,
            'max_file_size_mb': self.max_file_size_mb,
            'allowed_file_types': self.allowed_file_types,
            'debug_mode': self.debug_mode,
            'legacy_config_loaded': self._legacy_config_loaded
        }
        
        # Add centralized configuration status if available
        if _centralized_config_available:
            try:
                validation_result = config_manager.validate_configuration()
                status_info.update({
                    'centralized_config_available': True,
                    'configuration_valid': validation_result.is_valid,
                    'validation_errors': len(validation_result.errors),
                    'validation_warnings': len(validation_result.warnings),
                    'gemini_configured': config_manager.is_api_configured('gemini'),
                    'openrouter_configured': config_manager.is_api_configured('openrouter'),
                    'openai_configured': config_manager.is_api_configured('openai')
                })
            except Exception as e:
                status_info.update({
                    'centralized_config_available': False,
                    'centralized_config_error': str(e)
                })
        else:
            status_info['centralized_config_available'] = False
        
        return status_info


# Global configuration instance
app_config = AppConfig.from_env()