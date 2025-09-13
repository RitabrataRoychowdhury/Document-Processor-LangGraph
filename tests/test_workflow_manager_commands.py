"""Integration tests for workflow manager with command pattern."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.workflow.workflow_manager import WorkflowManager
from src.commands.ingest_command import IngestCommand
from src.commands.ner_command import NERCommand
from src.commands.kg_populate_command import KGPopulateCommand


class TestWorkflowManagerCommands(unittest.TestCase):
    """Test workflow manager with command pattern integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage = Mock()
        self.mock_processor_factory = Mock()
        self.mock_kg_repository = Mock()
        
        self.workflow_manager = WorkflowManager(
            storage=self.mock_storage,
            processor_factory=self.mock_processor_factory,
            kg_repository=self.mock_kg_repository
        )
        
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        self.test_file.write("Test document content for workflow")
        self.test_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
    
    def test_create_ingest_command(self):
        """Test creating an ingest command."""
        command = self.workflow_manager._create_command('ingest', file_path=self.test_file.name)
        
        self.assertIsInstance(command, IngestCommand)
        self.assertEqual(command.file_path, self.test_file.name)
    
    def test_create_ner_command(self):
        """Test creating a NER command."""
        command = self.workflow_manager._create_command('ner', document_id='doc_123')
        
        self.assertIsInstance(command, NERCommand)
        self.assertEqual(command.document_id, 'doc_123')
    
    def test_create_kg_populate_command(self):
        """Test creating a KG populate command."""
        command = self.workflow_manager._create_command('kg_populate', document_id='doc_123')
        
        self.assertIsInstance(command, KGPopulateCommand)
        self.assertEqual(command.document_id, 'doc_123')
    
    def test_create_unknown_command(self):
        """Test creating an unknown command raises error."""
        with self.assertRaises(ValueError):
            self.workflow_manager._create_command('unknown_command')
    
    def test_execute_single_command(self):
        """Test executing a single command."""
        # Mock the command
        mock_command = Mock()
        mock_command.get_command_info.return_value = {
            'command_type': 'TestCommand',
            'command_id': 'test_123'
        }
        mock_command.execute_with_retry.return_value = Mock(
            success=True,
            message="Test success",
            execution_time=1.5,
            retry_count=0
        )
        
        result = self.workflow_manager.execute_single_command(mock_command)
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Test success")
        mock_command.execute_with_retry.assert_called_once()
    
    def test_command_history_tracking(self):
        """Test that command history is tracked."""
        # Execute a mock command
        mock_command = Mock()
        mock_command.get_command_info.return_value = {
            'command_type': 'TestCommand',
            'command_id': 'test_123'
        }
        mock_result = Mock(success=True, message="Test", execution_time=1.0, retry_count=0)
        mock_command.execute_with_retry.return_value = mock_result
        
        # Simulate adding to command history (this would happen in _process_job)
        job_id = "job_123"
        command_name = "test"
        self.workflow_manager.command_history[f"{job_id}_{command_name}"] = mock_result
        
        # Test retrieving command history
        history = self.workflow_manager.get_command_history(job_id)
        self.assertIn(f"{job_id}_{command_name}", history)
        self.assertEqual(history[f"{job_id}_{command_name}"], mock_result)
    
    def test_get_queue_status(self):
        """Test getting queue status."""
        status = self.workflow_manager.get_queue_status()
        
        self.assertIn('queue_size', status)
        self.assertIn('active_jobs', status)
        self.assertIn('running', status)
        self.assertIn('active_job_ids', status)
        
        self.assertEqual(status['queue_size'], 0)  # Empty queue initially
        self.assertEqual(status['active_jobs'], 0)  # No active jobs initially


if __name__ == '__main__':
    unittest.main()