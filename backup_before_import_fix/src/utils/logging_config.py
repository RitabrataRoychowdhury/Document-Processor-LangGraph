"""Centralized logging configuration for the Document Q&A System."""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

import sys
import os

# Add the src directory to path to import config.py
src_dir = os.path.dirname(os.path.dirname(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import from the config.py file (not the config directory)
try:
    from config import config
except ImportError:
    # Fallback: create a minimal config for testing
    class MinimalConfig:
        DEBUG_MODE = False
        MAX_FILE_SIZE_MB = 10
        ALLOWED_FILE_TYPES = ['pdf', 'txt', 'docx']
        DATABASE_PATH = 'data/database/documents.db'
        PROCESSING_TIMEOUT_SECONDS = 300
    
    config = MinimalConfig()


class LoggingManager:
    """Manages logging configuration and setup for the application."""
    
    def __init__(self):
        self.log_dir = "logs"
        self.log_file = os.path.join(self.log_dir, "document_qa_system.log")
        self.error_log_file = os.path.join(self.log_dir, "errors.log")
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if config.DEBUG_MODE else logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs (rotating)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Suppress verbose third-party logs
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(name)
    
    def log_system_info(self):
        """Log system startup information."""
        logger = self.get_logger(__name__)
        logger.info("=" * 50)
        logger.info("Document Q&A System Starting")
        logger.info(f"Debug Mode: {config.DEBUG_MODE}")
        logger.info(f"Max File Size: {config.MAX_FILE_SIZE_MB}MB")
        logger.info(f"Allowed File Types: {config.ALLOWED_FILE_TYPES}")
        logger.info(f"Database Path: {config.DATABASE_PATH}")
        logger.info(f"Processing Timeout: {config.PROCESSING_TIMEOUT_SECONDS}s")
        logger.info("=" * 50)
    
    def log_error_with_context(self, logger: logging.Logger, error: Exception, 
                              context: Optional[dict] = None):
        """Log an error with additional context information."""
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        logger.error(error_msg, exc_info=True)
    
    def log_processing_event(self, event_type: str, document_id: str, 
                           job_id: Optional[str] = None, details: Optional[dict] = None):
        """Log processing events for monitoring."""
        logger = self.get_logger("processing")
        
        log_data = {
            "event": event_type,
            "document_id": document_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if job_id:
            log_data["job_id"] = job_id
        
        if details:
            log_data.update(details)
        
        logger.info(f"Processing Event: {log_data}")


# Global logging manager instance
logging_manager = LoggingManager()

# Convenience function to get logger
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging_manager.get_logger(name)