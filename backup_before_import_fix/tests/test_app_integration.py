"""Tests for the main application integration."""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app import DocumentQAApplication
from src.utils.error_handling import DocumentQAError, ErrorType
from src.config import Config


class TestDocumentQAApplication(unittest.TestCase):
    """Test cases for the main application integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = DocumentQAApplication()
        
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration
        self.original_config = {}
        config_attrs = ['DATABASE_PATH', 'DOCUMENTS_DIR', 'DATABASE_DIR']
        for attr in config_attrs:
            self.original_config[attr] = getattr(Config, attr)
            setattr(Config, attr, os.path.join(self.temp_dir, attr.lower()))
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original configuration
        for attr, value in self.original_config.items():
            setattr(Config, attr, value)
        
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Shutdown app if initialized
        if self.app.initialized:
            self.app.shutdown()
    
    @patch('src.app.config.validate')
    def test_initialization_success(self, mock_validate):
        """Test successful application initialization."""
        mock_validate.return_value = []  # No validation errors
        
        with patch('src.app.db_manager') as mock_db_manager:
            mock_db_manager.get_database_info.return_value = {
                'database_path': '/test/path',
                'database_size_bytes': 1024,
                'tables': {'documents': 0, 'processing_jobs': 0}
            }
            
            result = self.app.initialize()
            
            self.assertTrue(result)
            self.assertTrue(self.app.initialized)
            self.assertIsNotNone(self.app.storage)
            self.assertIsNotNone(self.app.file_handler)
            self.assertIsNotNone(self.app.qa_engine)
            self.assertIsNotNone(self.app.workflow_manager)
    
    @patch('src.app.config.validate')
    def test_initialization_config_error(self, mock_validate):
        """Test initialization failure due to configuration errors."""
        mock_validate.return_value = ['GEMINI_API_KEY is required']
        
        with self.assertRaises(DocumentQAError) as context:
            self.app.initialize()
        
        self.assertEqual(context.exception.error_type, ErrorType.VALIDATION_ERROR)
        self.assertFalse(self.app.initialized)
    
    @patch('src.app.config.validate')
    def test_initialization_database_error(self, mock_validate):
        """Test initialization failure due to database error."""
        mock_validate.return_value = []
        
        with patch('src.app.db_manager') as mock_db_manager:
            mock_db_manager.get_database_info.side_effect = Exception("Database connection failed")
            
            with self.assertRaises(DocumentQAError) as context:
                self.app.initialize()
            
            self.assertEqual(context.exception.error_type, ErrorType.DATABASE_ERROR)
            self.assertFalse(self.app.initialized)
    
    def test_double_initialization(self):
        """Test that double initialization is handled gracefully."""
        with patch('src.app.config.validate', return_value=[]):
            with patch('src.app.db_manager') as mock_db_manager:
                mock_db_manager.get_database_info.return_value = {
                    'database_path': '/test/path',
                    'database_size_bytes': 1024,
                    'tables': {'documents': 0}
                }
                
                # First initialization
                result1 = self.app.initialize()
                self.assertTrue(result1)
                
                # Second initialization should return True without re-initializing
                result2 = self.app.initialize()
                self.assertTrue(result2)
    
    def test_get_components_before_initialization(self):
        """Test that getting components before initialization raises errors."""
        with self.assertRaises(DocumentQAError):
            self.app.get_storage()
        
        with self.assertRaises(DocumentQAError):
            self.app.get_file_handler()
        
        with self.assertRaises(DocumentQAError):
            self.app.get_qa_engine()
        
        with self.assertRaises(DocumentQAError):
            self.app.get_workflow_manager()
    
    def test_get_components_after_initialization(self):
        """Test getting components after successful initialization."""
        with patch('src.app.config.validate', return_value=[]):
            with patch('src.app.db_manager') as mock_db_manager:
                mock_db_manager.get_database_info.return_value = {
                    'database_path': '/test/path',
                    'database_size_bytes': 1024,
                    'tables': {'documents': 0}
                }
                
                self.app.initialize()
                
                # Should not raise errors
                storage = self.app.get_storage()
                file_handler = self.app.get_file_handler()
                qa_engine = self.app.get_qa_engine()
                workflow_manager = self.app.get_workflow_manager()
                
                self.assertIsNotNone(storage)
                self.assertIsNotNone(file_handler)
                self.assertIsNotNone(qa_engine)
                self.assertIsNotNone(workflow_manager)
    
    def test_system_status_before_initialization(self):
        """Test getting system status before initialization."""
        status = self.app.get_system_status()
        
        self.assertFalse(status['initialized'])
        self.assertIn('error', status)
    
    def test_system_status_after_initialization(self):
        """Test getting system status after initialization."""
        with patch('src.app.config.validate', return_value=[]):
            with patch('src.app.db_manager') as mock_db_manager:
                mock_db_manager.get_database_info.return_value = {
                    'database_path': '/test/path',
                    'database_size_bytes': 1024,
                    'tables': {'documents': 5, 'processing_jobs': 2}
                }
                
                # Mock storage stats
                with patch.object(self.app, '_initialize_components'):
                    self.app._initialize_components()
                    mock_storage = Mock()
                    mock_storage.get_storage_stats.return_value = {
                        'total_documents': 5,
                        'documents_by_status': {'completed': 3, 'processing': 2},
                        'jobs_by_status': {'completed': 1, 'processing': 1}
                    }
                    self.app.storage = mock_storage
                    
                    # Mock workflow manager
                    mock_workflow = Mock()
                    mock_workflow.get_queue_status.return_value = {
                        'queue_size': 1,
                        'active_jobs': 1,
                        'running': True
                    }
                    self.app.workflow_manager = mock_workflow
                    
                    self.app.initialized = True
                    
                    status = self.app.get_system_status()
                    
                    self.assertTrue(status['initialized'])
                    self.assertEqual(status['storage']['total_documents'], 5)
                    self.assertEqual(status['workflow']['queue_size'], 1)
                    self.assertIn('database', status)
                    self.assertIn('config', status)
    
    def test_error_context_manager(self):
        """Test the error context manager."""
        with self.assertRaises(DocumentQAError) as context:
            with self.app.error_context("test_operation", test_param="test_value"):
                raise ValueError("Test error")
        
        self.assertEqual(context.exception.error_type, ErrorType.SYSTEM_ERROR)
        self.assertIn("test_operation", context.exception.message)
        self.assertEqual(context.exception.details['test_param'], "test_value")
    
    def test_shutdown_before_initialization(self):
        """Test shutdown before initialization."""
        # Should not raise errors
        self.app.shutdown()
        self.assertFalse(self.app.initialized)
    
    def test_shutdown_after_initialization(self):
        """Test shutdown after initialization."""
        with patch('src.app.config.validate', return_value=[]):
            with patch('src.app.db_manager') as mock_db_manager:
                mock_db_manager.get_database_info.return_value = {
                    'database_path': '/test/path',
                    'database_size_bytes': 1024,
                    'tables': {'documents': 0}
                }
                
                self.app.initialize()
                
                # Mock workflow manager shutdown
                self.app.workflow_manager.shutdown = Mock()
                
                self.app.shutdown()
                
                self.assertFalse(self.app.initialized)
                self.app.workflow_manager.shutdown.assert_called_once()


class TestApplicationGlobals(unittest.TestCase):
    """Test global application functions."""
    
    def test_get_app(self):
        """Test getting the global app instance."""
        from src.app import get_app
        
        app = get_app()
        self.assertIsInstance(app, DocumentQAApplication)
    
    @patch('src.app.app.initialize')
    def test_initialize_app(self, mock_initialize):
        """Test initializing the global app."""
        from src.app import initialize_app
        
        mock_initialize.return_value = True
        
        result = initialize_app()
        
        self.assertTrue(result)
        mock_initialize.assert_called_once()
    
    @patch('src.app.app.shutdown')
    def test_shutdown_app(self, mock_shutdown):
        """Test shutting down the global app."""
        from src.app import shutdown_app
        
        shutdown_app()
        
        mock_shutdown.assert_called_once()


if __name__ == '__main__':
    unittest.main()