"""Tests for the enhanced workflow system."""

import unittest
import tempfile
import os
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from src.models.document import Document, ProcessingJob
from src.storage.database import DatabaseManager
from src.storage.document_storage import DocumentStorage
from src.workflow.enhanced_workflow import EnhancedDocumentWorkflow
from src.workflow.workflow_manager import WorkflowManager


class TestEnhancedWorkflow(unittest.TestCase):
    """Test cases for enhanced workflow functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create test database manager and storage
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.storage = DocumentStorage()
        self.storage.db_manager = self.db_manager
        
        # Create test document
        self.test_document = Document(
            id=str(uuid.uuid4()),
            title="Test Document",
            file_type="txt",
            file_size=1000,
            upload_timestamp=datetime.now(),
            original_text="This is a test document for processing. It contains some sample text to analyze."
        )
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_document_storage_operations(self):
        """Test basic document storage operations."""
        # Create document
        doc_id = self.storage.create_document(self.test_document)
        self.assertEqual(doc_id, self.test_document.id)
        
        # Retrieve document
        retrieved_doc = self.storage.get_document(doc_id)
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc.title, self.test_document.title)
        
        # Update document
        updates = {
            'processing_status': 'completed',
            'document_type': 'Test Document Type'
        }
        updated = self.storage.update_document(doc_id, updates)
        self.assertTrue(updated)
        
        # Verify update
        updated_doc = self.storage.get_document(doc_id)
        self.assertEqual(updated_doc.processing_status, 'completed')
        self.assertEqual(updated_doc.document_type, 'Test Document Type')
        
        # List documents
        documents = self.storage.list_documents()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].id, doc_id)
        
        # Delete document
        deleted = self.storage.delete_document(doc_id)
        self.assertTrue(deleted)
        
        # Verify deletion
        deleted_doc = self.storage.get_document(doc_id)
        self.assertIsNone(deleted_doc)
    
    def test_processing_job_operations(self):
        """Test processing job operations."""
        # Create document first
        self.storage.create_document(self.test_document)
        
        # Create processing job
        job = ProcessingJob(
            job_id=str(uuid.uuid4()),
            document_id=self.test_document.id,
            status="pending"
        )
        
        job_id = self.storage.create_processing_job(job)
        self.assertEqual(job_id, job.job_id)
        
        # Retrieve job
        retrieved_job = self.storage.get_processing_job(job_id)
        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.document_id, self.test_document.id)
        
        # Update job
        updated = self.storage.update_processing_job(
            job_id,
            status="processing",
            current_step="analysis",
            progress_percentage=50
        )
        self.assertTrue(updated)
        
        # Verify update
        updated_job = self.storage.get_processing_job(job_id)
        self.assertEqual(updated_job.status, "processing")
        self.assertEqual(updated_job.current_step, "analysis")
        self.assertEqual(updated_job.progress_percentage, 50)
    
    @patch('src.workflow.enhanced_workflow.GeminiDocumentProcessor')
    def test_workflow_nodes(self, mock_processor_class):
        """Test individual workflow nodes."""
        # Mock the Gemini processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.call_gemini.return_value = "Test Classification Result"
        
        # Create workflow
        workflow = EnhancedDocumentWorkflow(self.storage)
        
        # Test document intake node
        state = {
            'document_id': self.test_document.id,
            'job_id': str(uuid.uuid4()),
            'api_key': 'test_key',
            'document': self.test_document.original_text,
            'processing_status': 'initialized'
        }
        
        # Create processing job for the test
        job = ProcessingJob(
            job_id=state['job_id'],
            document_id=state['document_id']
        )
        self.storage.create_processing_job(job)
        
        # Test intake node
        result_state = workflow.document_intake_node(state)
        self.assertEqual(result_state['next'], 'classification')
        self.assertIn('document_length', result_state)
        
        # Test classification node
        result_state = workflow.classification_node(result_state)
        self.assertEqual(result_state['next'], 'extraction')
        self.assertIn('document_type', result_state)
    
    def test_workflow_manager(self):
        """Test workflow manager functionality."""
        # Create workflow manager
        manager = WorkflowManager(self.storage)
        
        # Test queue status
        status = manager.get_queue_status()
        self.assertIn('queue_size', status)
        self.assertIn('active_jobs', status)
        self.assertIn('running', status)
        
        # Test job submission (without actually processing)
        with patch.object(manager.workflow, 'process_document') as mock_process:
            mock_process.return_value = 'test_job_id'
            
            job_id = manager.submit_document_for_processing(
                self.test_document, 
                'test_api_key'
            )
            
            self.assertIsNotNone(job_id)
            
            # Verify job was created
            job = manager.get_job_status(job_id)
            self.assertIsNotNone(job)
            self.assertEqual(job.document_id, self.test_document.id)
    
    def test_storage_stats(self):
        """Test storage statistics."""
        # Create some test data
        self.storage.create_document(self.test_document)
        
        job = ProcessingJob(
            job_id=str(uuid.uuid4()),
            document_id=self.test_document.id
        )
        self.storage.create_processing_job(job)
        
        # Get stats
        stats = self.storage.get_storage_stats()
        
        self.assertIn('total_documents', stats)
        self.assertIn('documents_by_status', stats)
        self.assertIn('jobs_by_status', stats)
        self.assertEqual(stats['total_documents'], 1)


if __name__ == '__main__':
    unittest.main()