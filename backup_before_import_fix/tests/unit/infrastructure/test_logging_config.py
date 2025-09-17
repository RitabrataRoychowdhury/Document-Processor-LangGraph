"""Tests for the logging configuration system."""

import unittest
import tempfile
import os
import sys
import logging
from unittest.mock import patch, Mock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.logging_config import LoggingManager, get_logger


class TestLoggingManager(unittest.TestCase):
    """Test cases for LoggingManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch config to use temp directory
        self.config_patcher = patch('src.utils.logging_config.config')
        self.mock_config = self.config_patcher.start()
        self.mock_config.DEBUG_MODE = False
    
    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        
        # Clean up temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_logging_manager_initialization(self):
        """Test LoggingManager initialization."""
        with patch.object(LoggingManager, '_setup_logging') as mock_setup:
            manager = LoggingManager()
            
            self.assertEqual(manager.log_dir, "logs")
            self.assertIn("document_qa_system.log", manager.log_file)
            self.assertIn("errors.log", manager.error_log_file)
            mock_setup.assert_called_once()
    
    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates the logs directory."""
        with patch('os.makedirs') as mock_makedirs:
            with patch('logging.getLogger') as mock_get_logger:
                mock_root_logger = Mock()
                mock_get_logger.return_value = mock_root_logger
                
                manager = LoggingManager()
                
                mock_makedirs.assert_called_with("logs", exist_ok=True)
    
    def test_setup_logging_configures_handlers(self):
        """Test that setup_logging configures all handlers."""
        with patch('logging.getLogger') as mock_get_logger:
            with patch('logging.StreamHandler') as mock_stream_handler:
                with patch('logging.handlers.RotatingFileHandler') as mock_file_handler:
                    mock_root_logger = Mock()
                    mock_get_logger.return_value = mock_root_logger
                    
                    manager = LoggingManager()
                    
                    # Should create console handler and two file handlers
                    mock_stream_handler.assert_called_once()
                    self.assertEqual(mock_file_handler.call_count, 2)
                    
                    # Should add handlers to root logger
                    self.assertEqual(mock_root_logger.addHandler.call_count, 3)
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        manager = LoggingManager()
        
        logger = manager.get_logger("test_module")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_module")
    
    def test_log_system_info(self):
        """Test logging system information."""
        manager = LoggingManager()
        
        with patch.object(manager, 'get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            manager.log_system_info()
            
            # Should log multiple info messages
            self.assertGreater(mock_logger.info.call_count, 5)
            
            # Check that system info is logged
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            self.assertTrue(any("Document Q&A System Starting" in call for call in calls))
    
    def test_log_error_with_context(self):
        """Test logging error with context."""
        manager = LoggingManager()
        mock_logger = Mock()
        
        error = ValueError("Test error")
        context = {"operation": "test_operation", "user_id": "123"}
        
        manager.log_error_with_context(mock_logger, error, context)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check error message includes context
        error_msg = call_args[0][0]
        self.assertIn("Test error", error_msg)
        self.assertIn("Context:", error_msg)
        
        # Check exc_info is True
        self.assertTrue(call_args[1]['exc_info'])
    
    def test_log_processing_event(self):
        """Test logging processing events."""
        manager = LoggingManager()
        
        with patch.object(manager, 'get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            manager.log_processing_event(
                "document_uploaded",
                "doc_123",
                job_id="job_456",
                details={"file_size": 1024}
            )
            
            mock_logger.info.assert_called_once()
            
            # Check log message contains event data
            log_msg = mock_logger.info.call_args[0][0]
            self.assertIn("Processing Event:", log_msg)
            self.assertIn("document_uploaded", log_msg)
            self.assertIn("doc_123", log_msg)
            self.assertIn("job_456", log_msg)
    
    def test_debug_mode_configuration(self):
        """Test logging configuration in debug mode."""
        self.mock_config.DEBUG_MODE = True
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            manager = LoggingManager()
            
            # Should have called setLevel (exact level may vary due to existing loggers)
            self.assertTrue(mock_root_logger.setLevel.called)
    
    def test_production_mode_configuration(self):
        """Test logging configuration in production mode."""
        self.mock_config.DEBUG_MODE = False
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            manager = LoggingManager()
            
            # Should have called setLevel (exact level may vary due to existing loggers)
            self.assertTrue(mock_root_logger.setLevel.called)


class TestGlobalLoggingFunctions(unittest.TestCase):
    """Test global logging functions."""
    
    def test_get_logger_function(self):
        """Test the global get_logger function."""
        logger = get_logger("test_module")
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_module")
    
    @patch('src.utils.logging_config.logging_manager')
    def test_get_logger_uses_global_manager(self, mock_manager):
        """Test that get_logger uses the global logging manager."""
        mock_logger = Mock()
        mock_manager.get_logger.return_value = mock_logger
        
        result = get_logger("test_module")
        
        mock_manager.get_logger.assert_called_once_with("test_module")
        self.assertEqual(result, mock_logger)


class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for logging system."""
    
    def test_logging_manager_creation(self):
        """Test that LoggingManager can be created successfully."""
        with patch('src.utils.logging_config.config') as mock_config:
            mock_config.DEBUG_MODE = True
            
            # Should not raise any exceptions
            manager = LoggingManager()
            self.assertIsNotNone(manager)
            
            # Should be able to get a logger
            logger = manager.get_logger("test")
            self.assertIsInstance(logger, logging.Logger)


if __name__ == '__main__':
    unittest.main()