"""
Main application integration layer for the Document Q&A System.
Coordinates all components and provides unified error handling.
"""

import os
import sys
import signal
import atexit
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config.app_config import app_config
# Import legacy config for backward compatibility
try:
    from config import config
except ImportError:
    # Create a minimal config for backward compatibility
    class LegacyConfig:
        def validate(self):
            return []
    config = LegacyConfig()
from src.config.app_config import app_config
from src.utils.logging_config import logging_manager, get_logger
from src.utils.error_handling import (
    DocumentQAError, ErrorType, handle_errors, format_error_for_ui
)
from src.storage.database import db_manager
from src.storage.document_storage import DocumentStorage
from src.repositories.document_repository import SQLiteDocumentRepository
from src.repositories.patient_repository import SQLitePatientRepository
from src.services.file_handler import FileUploadHandler
from src.services.qa_engine import QAEngine
from src.workflow.workflow_manager import WorkflowManager

logger = get_logger(__name__)


class DocumentQAApplication:
    """Main application class that integrates all components."""
    
    def __init__(self):
        self.initialized = False
        self.storage: Optional[DocumentStorage] = None
        self.document_repository: Optional[SQLiteDocumentRepository] = None
        self.patient_repository: Optional[SQLitePatientRepository] = None
        self.file_handler: Optional[FileUploadHandler] = None
        self.qa_engine: Optional[QAEngine] = None
        self.workflow_manager: Optional[WorkflowManager] = None
        self.app_config = app_config
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.shutdown()
            sys.exit(0)
        
        try:
            # Only set up signal handlers if we're in the main thread
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Signal handling not available (e.g., in Streamlit threads)
            logger.debug("Signal handling not available in this context")
        
        atexit.register(self.shutdown)
    
    @handle_errors(ErrorType.SYSTEM_ERROR)
    def initialize(self) -> bool:
        """Initialize the application and all components."""
        if self.initialized:
            logger.warning("Application already initialized")
            return True
        
        logger.info("Initializing Document Q&A Application...")
        
        # Log system information
        logging_manager.log_system_info()
        
        # Validate configuration (both legacy and new)
        config_errors = config.validate()
        app_config_errors = self.app_config.validate()
        
        all_errors = config_errors + app_config_errors
        if all_errors:
            error_msg = f"Configuration validation failed: {', '.join(all_errors)}"
            logger.error(error_msg)
            raise DocumentQAError(error_msg, ErrorType.VALIDATION_ERROR)
        
        # Create required directories
        self._create_directories()
        
        # Initialize database
        self._initialize_database()
        
        # Initialize components
        self._initialize_components()
        
        # Verify system health
        self._verify_system_health()
        
        self.initialized = True
        logger.info("✅ Application initialization complete")
        return True
    
    def _create_directories(self):
        """Create required directories."""
        directories = [
            self.app_config.documents_dir,
            self.app_config.database_dir,
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def _initialize_database(self):
        """Initialize the database."""
        try:
            # Database manager initializes automatically
            db_info = db_manager.get_database_info()
            logger.info(f"Database initialized: {db_info['database_path']}")
            logger.info(f"Database size: {db_info['database_size_bytes']} bytes")
            
            for table, count in db_info['tables'].items():
                logger.debug(f"Table {table}: {count} records")
                
        except Exception as e:
            raise DocumentQAError(
                "Failed to initialize database",
                ErrorType.DATABASE_ERROR,
                {"database_path": self.app_config.database_path},
                e
            )
    
    def _initialize_components(self):
        """Initialize all application components."""
        try:
            # Initialize storage (backward compatibility)
            self.storage = DocumentStorage()
            logger.debug("Document storage initialized")
            
            # Initialize repositories (new pattern)
            self.document_repository = SQLiteDocumentRepository()
            self.patient_repository = SQLitePatientRepository()
            logger.debug("Repositories initialized")
            
            # Initialize file handler
            self.file_handler = FileUploadHandler()
            logger.debug("File upload handler initialized")
            
            # Initialize Q&A engine with new configuration
            api_key = self.app_config.get_api_key_for_provider(self.app_config.qa_provider)
            if not api_key and self.app_config.qa_provider != "local":
                logger.warning(f"{self.app_config.qa_provider} API key not configured - Q&A functionality will be limited")
            
            self.qa_engine = QAEngine(self.storage, api_key)
            logger.debug("Q&A engine initialized")
            
            # Initialize workflow manager
            self.workflow_manager = WorkflowManager(self.storage)
            logger.debug("Workflow manager initialized")
            
        except Exception as e:
            raise DocumentQAError(
                "Failed to initialize application components",
                ErrorType.SYSTEM_ERROR,
                original_error=e
            )
    
    def _verify_system_health(self):
        """Verify system health and component connectivity."""
        health_checks = []
        
        # Check database connectivity
        try:
            stats = self.storage.get_storage_stats()
            health_checks.append(("Database", True, f"Connected - {stats['total_documents']} documents"))
        except Exception as e:
            health_checks.append(("Database", False, str(e)))
        
        # Check file handler
        try:
            # Test file validation with a mock file
            from unittest.mock import Mock
            mock_file = Mock()
            mock_file.name = "test.txt"
            mock_file.size = 1024
            result = self.file_handler.validate_file(mock_file)
            health_checks.append(("File Handler", True, "Validation working"))
        except Exception as e:
            health_checks.append(("File Handler", False, str(e)))
        
        # Check workflow manager
        try:
            status = self.workflow_manager.get_queue_status()
            health_checks.append(("Workflow Manager", True, f"Queue size: {status['queue_size']}"))
        except Exception as e:
            health_checks.append(("Workflow Manager", False, str(e)))
        
        # Log health check results
        logger.info("System Health Check:")
        for component, healthy, message in health_checks:
            status = "✅" if healthy else "❌"
            logger.info(f"  {status} {component}: {message}")
        
        # Check if any critical components failed
        failed_components = [name for name, healthy, _ in health_checks if not healthy]
        if failed_components:
            raise DocumentQAError(
                f"Critical components failed health check: {', '.join(failed_components)}",
                ErrorType.SYSTEM_ERROR,
                {"failed_components": failed_components}
            )
    
    @handle_errors(ErrorType.SYSTEM_ERROR)
    def shutdown(self):
        """Gracefully shutdown the application."""
        if not self.initialized:
            return
        
        logger.info("Shutting down Document Q&A Application...")
        
        try:
            # Stop workflow manager
            if self.workflow_manager:
                self.workflow_manager.shutdown()
                logger.debug("Workflow manager stopped")
            
            # Close database connections
            if hasattr(db_manager, 'close_all_connections'):
                db_manager.close_all_connections()
                logger.debug("Database connections closed")
            
            self.initialized = False
            logger.info("✅ Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    @contextmanager
    def error_context(self, operation: str, **context):
        """Context manager for error handling with additional context."""
        try:
            logger.debug(f"Starting operation: {operation}")
            yield
            logger.debug(f"Completed operation: {operation}")
        except DocumentQAError:
            raise
        except Exception as e:
            logger.error(f"Error in operation '{operation}': {str(e)}", exc_info=True)
            raise DocumentQAError(
                f"Error in {operation}: {str(e)}",
                ErrorType.SYSTEM_ERROR,
                context,
                e
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        if not self.initialized:
            return {"initialized": False, "error": "Application not initialized"}
        
        try:
            # Get storage stats
            storage_stats = self.storage.get_storage_stats()
            
            # Get workflow status
            workflow_status = self.workflow_manager.get_queue_status()
            
            # Get database info
            db_info = db_manager.get_database_info()
            
            return {
                "initialized": True,
                "storage": storage_stats,
                "workflow": workflow_status,
                "database": {
                    "path": db_info["database_path"],
                    "size_bytes": db_info["database_size_bytes"],
                    "tables": db_info["tables"]
                },
                "config": {
                    "max_file_size_mb": self.app_config.max_file_size_mb,
                    "allowed_file_types": self.app_config.allowed_file_types,
                    "debug_mode": self.app_config.debug_mode,
                    "api_key_configured": self.app_config.is_api_configured(),
                    "embedding_provider": self.app_config.embedding_provider,
                    "qa_provider": self.app_config.qa_provider,
                    "knowledge_graph_enabled": self.app_config.enable_knowledge_graph
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}", exc_info=True)
            return {
                "initialized": True,
                "error": str(e),
                "error_type": "system_status_error"
            }
    
    # Component access methods with error handling
    
    @handle_errors(ErrorType.STORAGE_ERROR)
    def get_storage(self) -> DocumentStorage:
        """Get document storage instance."""
        if not self.initialized or not self.storage:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.storage
    
    @handle_errors(ErrorType.FILE_PROCESSING)
    def get_file_handler(self) -> FileUploadHandler:
        """Get file upload handler instance."""
        if not self.initialized or not self.file_handler:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.file_handler
    
    @handle_errors(ErrorType.QA_ERROR)
    def get_qa_engine(self) -> QAEngine:
        """Get Q&A engine instance."""
        if not self.initialized or not self.qa_engine:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.qa_engine
    
    @handle_errors(ErrorType.WORKFLOW_ERROR)
    def get_workflow_manager(self) -> WorkflowManager:
        """Get workflow manager instance."""
        if not self.initialized or not self.workflow_manager:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.workflow_manager
    
    @handle_errors(ErrorType.STORAGE_ERROR)
    def get_document_repository(self) -> SQLiteDocumentRepository:
        """Get document repository instance."""
        if not self.initialized or not self.document_repository:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.document_repository
    
    @handle_errors(ErrorType.STORAGE_ERROR)
    def get_patient_repository(self) -> SQLitePatientRepository:
        """Get patient repository instance."""
        if not self.initialized or not self.patient_repository:
            raise DocumentQAError("Application not properly initialized", ErrorType.SYSTEM_ERROR)
        return self.patient_repository
    
    def get_app_config(self):
        """Get application configuration."""
        return self.app_config


# Global application instance
app = DocumentQAApplication()


def get_app() -> DocumentQAApplication:
    """Get the global application instance."""
    return app


def initialize_app() -> bool:
    """Initialize the global application instance."""
    return app.initialize()


def shutdown_app():
    """Shutdown the global application instance."""
    app.shutdown()