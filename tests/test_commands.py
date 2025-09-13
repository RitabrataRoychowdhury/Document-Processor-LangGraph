"""Tests for command pattern implementation."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

from src.commands.base import Command, CommandResult, CommandStatus, retry_on_failure, RetryableException
from src.commands.ingest_command import IngestCommand
from src.commands.ner_command import NERCommand
from src.commands.kg_populate_command import KGPopulateCommand
from src.models.document import Document


class TestCommandBase(unittest.TestCase):
    """Test base command functionality."""
    
    def test_command_result_success(self):
        """Test creating successful command result."""
        result = CommandResult.success_result("Test success", {"key": "value"})
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, CommandStatus.COMPLETED)
        self.assertEqual(result.message, "Test success")
        self.assertEqual(result.data["key"], "value")
    
    def test_command_result_failure(self):
        """Test creating failed command result."""
        error = Exception("Test error")
        result = CommandResult.failure_result("Test failure", error, retry_count=2)
        
        self.assertFalse(result.success)
        self.assertEqual(result.status, CommandStatus.FAILED)
        self.assertEqual(result.message, "Test failure")
        self.assertEqual(result.error, error)
        self.assertEqual(result.retry_count, 2)
    
    def test_command_result_to_dict(self):
        """Test converting command result to dictionary."""
        result = CommandResult.success_result("Test", {"data": "value"})
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["status"], "completed")
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["message"], "Test")
        self.assertEqual(result_dict["data"]["data"], "value")


class TestRetryDecorator(unittest.TestCase):
    """Test retry decorator functionality."""
    
    def test_retry_success_first_attempt(self):
        """Test function succeeds on first attempt."""
        @retry_on_failure(max_attempts=3)
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_retry_success_after_failures(self):
        """Test function succeeds after some failures."""
        call_count = 0
        
        @retry_on_failure(max_attempts=3, backoff_factor=0.1)  # Fast backoff for testing
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableException("Temporary failure")
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_all_attempts_fail(self):
        """Test all retry attempts fail."""
        @retry_on_failure(max_attempts=2, backoff_factor=0.1)
        def test_function():
            raise RetryableException("Always fails")
        
        with self.assertRaises(RetryableException):
            test_function()


class TestIngestCommand(unittest.TestCase):
    """Test ingest command functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_processor_factory = Mock()
        self.mock_storage = Mock()
        self.mock_processor = Mock()
        
        # Create a temporary test file
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        self.test_file.write("Test document content")
        self.test_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
    
    def test_ingest_command_success(self):
        """Test successful document ingestion."""
        # Setup mocks
        self.mock_processor_factory.create_processor.return_value = self.mock_processor
        self.mock_processor.extract_text.return_value = "Extracted text content"
        self.mock_processor.extract_metadata.return_value = {"pages": 1}
        self.mock_storage.create_document.return_value = "doc_123"
        
        # Create and execute command
        command = IngestCommand(
            file_path=self.test_file.name,
            processor_factory=self.mock_processor_factory,
            storage=self.mock_storage
        )
        
        result = command.execute()
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, CommandStatus.COMPLETED)
        self.assertIn("document_id", result.data)
        self.assertEqual(result.data["document_id"], "doc_123")
        
        # Verify mocks were called
        self.mock_processor_factory.create_processor.assert_called_once_with('txt')
        self.mock_processor.extract_text.assert_called_once_with(self.test_file.name)
        self.mock_storage.create_document.assert_called_once()
    
    def test_ingest_command_file_not_found(self):
        """Test ingest command with non-existent file."""
        with self.assertRaises(Exception):  # Should raise NonRetryableException
            IngestCommand(
                file_path="/nonexistent/file.txt",
                processor_factory=self.mock_processor_factory,
                storage=self.mock_storage
            )
    
    def test_ingest_command_can_retry(self):
        """Test that ingest command can be retried."""
        command = IngestCommand(
            file_path=self.test_file.name,
            processor_factory=self.mock_processor_factory,
            storage=self.mock_storage
        )
        
        self.assertTrue(command.can_retry())


class TestNERCommand(unittest.TestCase):
    """Test NER command functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage = Mock()
        self.mock_embedding_strategy = Mock()
        
        # Mock document
        self.mock_document = Mock()
        self.mock_document.original_text = "Patient John Doe has diabetes and hypertension. Impairment rating is 15%."
        self.mock_document.extracted_info = {}
        self.mock_document.title = "Test Document"
        
    def test_ner_command_success(self):
        """Test successful NER processing."""
        # Setup mocks
        self.mock_storage.get_document.return_value = self.mock_document
        self.mock_embedding_strategy.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        
        # Create and execute command
        command = NERCommand(
            document_id="doc_123",
            embedding_strategy=self.mock_embedding_strategy,
            storage=self.mock_storage
        )
        
        result = command.execute()
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, CommandStatus.COMPLETED)
        self.assertIn("entities_count", result.data)
        self.assertGreater(result.data["entities_count"], 0)
        
        # Verify mocks were called
        self.mock_storage.get_document.assert_called_once_with("doc_123")
        self.mock_embedding_strategy.generate_embeddings.assert_called_once()
        self.mock_storage.update_document.assert_called_once()
    
    def test_ner_command_document_not_found(self):
        """Test NER command with non-existent document."""
        self.mock_storage.get_document.return_value = None
        
        command = NERCommand(
            document_id="nonexistent_doc",
            embedding_strategy=self.mock_embedding_strategy,
            storage=self.mock_storage
        )
        
        result = command.execute()
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.message)
    
    def test_ner_command_can_retry(self):
        """Test that NER command can be retried."""
        command = NERCommand(
            document_id="doc_123",
            embedding_strategy=self.mock_embedding_strategy,
            storage=self.mock_storage
        )
        
        self.assertTrue(command.can_retry())


class TestKGPopulateCommand(unittest.TestCase):
    """Test KG populate command functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage = Mock()
        self.mock_kg_repository = Mock()
        
        # Mock document with NER results
        self.mock_document = Mock()
        self.mock_document.title = "Test Document"
        self.mock_document.extracted_info = {
            'ner_processed': True,
            'entities': [
                {'text': 'John Doe', 'type': 'PATIENT', 'start': 0, 'end': 8, 'confidence': 0.9},
                {'text': 'diabetes', 'type': 'DIAGNOSIS', 'start': 20, 'end': 28, 'confidence': 0.8}
            ]
        }
    
    def test_kg_populate_command_success(self):
        """Test successful KG population."""
        # Setup mocks
        self.mock_storage.get_document.return_value = self.mock_document
        self.mock_kg_repository.create_document_node.return_value = "doc_node_123"
        self.mock_kg_repository.create_patient_node.return_value = "patient_node_123"
        self.mock_kg_repository.create_diagnosis_node.return_value = "diagnosis_node_123"
        
        # Create and execute command
        command = KGPopulateCommand(
            document_id="doc_123",
            kg_repository=self.mock_kg_repository,
            storage=self.mock_storage
        )
        
        result = command.execute()
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, CommandStatus.COMPLETED)
        self.assertIn("nodes_created", result.data)
        self.assertIn("relationships_created", result.data)
        
        # Verify mocks were called
        self.mock_storage.get_document.assert_called_once_with("doc_123")
        self.mock_kg_repository.create_document_node.assert_called_once()
        self.mock_kg_repository.create_patient_node.assert_called_once()
        self.mock_kg_repository.create_diagnosis_node.assert_called_once()
    
    def test_kg_populate_command_no_ner_data(self):
        """Test KG populate command with document that hasn't been processed with NER."""
        self.mock_document.extracted_info = {}  # No NER data
        self.mock_storage.get_document.return_value = self.mock_document
        
        command = KGPopulateCommand(
            document_id="doc_123",
            kg_repository=self.mock_kg_repository,
            storage=self.mock_storage
        )
        
        result = command.execute()
        
        self.assertFalse(result.success)
        self.assertIn("not been processed with NER", result.message)
    
    def test_kg_populate_command_can_retry(self):
        """Test that KG populate command can be retried."""
        command = KGPopulateCommand(
            document_id="doc_123",
            kg_repository=self.mock_kg_repository,
            storage=self.mock_storage
        )
        
        self.assertTrue(command.can_retry())


if __name__ == '__main__':
    unittest.main()