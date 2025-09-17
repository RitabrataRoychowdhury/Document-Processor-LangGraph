"""Configuration management for the Document Q&A System."""

import os
from typing import List, Optional

# Try to load dotenv if available, otherwise use environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables
    pass


class Config:
    """Configuration class for the Document Q&A System."""
    
    # API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/database/documents.db")
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES: List[str] = os.getenv("ALLOWED_FILE_TYPES", "pdf,txt,docx").split(",")
    
    # Processing Configuration
    MAX_PROCESSING_JOBS: int = int(os.getenv("MAX_PROCESSING_JOBS", "5"))
    PROCESSING_TIMEOUT_SECONDS: int = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "300"))
    
    # UI Configuration
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # Storage Paths
    DOCUMENTS_DIR: str = "data/documents"
    DATABASE_DIR: str = "data/database"
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if cls.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be positive")
        
        if cls.MAX_PROCESSING_JOBS <= 0:
            errors.append("MAX_PROCESSING_JOBS must be positive")
        
        if cls.PROCESSING_TIMEOUT_SECONDS <= 0:
            errors.append("PROCESSING_TIMEOUT_SECONDS must be positive")
        
        return errors
    
    @classmethod
    def get_max_file_size_bytes(cls) -> int:
        """Get maximum file size in bytes."""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @classmethod
    def is_allowed_file_type(cls, file_extension: str) -> bool:
        """Check if file type is allowed."""
        return file_extension.lower().lstrip('.') in cls.ALLOWED_FILE_TYPES
    
    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        """Get Gemini API key."""
        return cls.GEMINI_API_KEY if cls.GEMINI_API_KEY else None


# Global configuration instance
config = Config()