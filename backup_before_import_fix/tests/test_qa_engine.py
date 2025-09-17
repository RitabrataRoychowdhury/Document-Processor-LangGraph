"""Tests for the Q&A Engine functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from src.services.qa_engine import QAEngine
from src.models.document import Document
from src.storage.document_storage import DocumentStorage


class TestQAEngine(unittest.TestCase):
    """Test cases for QA Engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_storage = Mock(spec=DocumentStorage)
        self.api_key = "test_api_key"
        self.qa_engine = QAEngine(self.mock_storage, self.api_key)
        
        # Create a test document
        self.test_document = Document(
            id="test_doc_1",
            title="Test Document",
            file_type="txt",
            file_size=1000,
            upload_timestamp=datetime.now(),
            processing_status="completed",
            original_text="This is a test document about artificial intelligence and machine learning. It discusses various algorithms and their applications in modern technology.",
            document_type="Technical Documentation",
            extracted_info={
                "Main Topic": "Artificial Intelligence and Machine Learning",
                "Key Entities": ["AI", "ML", "algorithms", "technology"],
                "Summary": "Document about AI/ML algorithms and applications"
            },
            analysis="This document provides an overview of AI and ML technologies with focus on practical applications.",
            summary="A comprehensive guide to AI and ML algorithms and their real-world applications."
        )
    
    def test_extract_key_terms(self):
        """Test key term extraction from questions."""
        question = "What are the main algorithms discussed in artificial intelligence?"
        key_terms = self.qa_engine._extract_key_terms(question)
        
        # Should extract meaningful terms and filter out stop words
        self.assertIn("algorithms", key_terms)
        self.assertIn("artificial", key_terms)
        self.assertIn("intelligence", key_terms)
        self.assertNotIn("what", key_terms)
        self.assertNotIn("are", key_terms)
        self.assertNotIn("the", key_terms)
    
    def test_find_relevant_passages(self):
        """Test finding relevant passages in content."""
        question_terms = ["artificial", "intelligence", "algorithms"]
        content = self.test_document.original_text
        
        passages = self.qa_engine._find_relevant_passages(question_terms, content, "Test Content")
        
        # Should find relevant passages
        self.assertGreater(len(passages), 0)
        
        # Check passage structure
        passage = passages[0]
        self.assertIn("text", passage)
        self.assertIn("source", passage)
        self.assertIn("relevance_score", passage)
        self.assertIn("matches", passage)
        
        # Should have positive relevance score
        self.assertGreater(passage["relevance_score"], 0)
    
    def test_get_relevant_context(self):
        """Test getting relevant context from document."""
        question = "What is artificial intelligence?"
        
        context_sections = self.qa_engine.get_relevant_context(question, self.test_document)
        
        # Should return context sections
        self.assertIsInstance(context_sections, list)
        
        if context_sections:
            # Check context section structure
            section = context_sections[0]
            self.assertIn("text", section)
            self.assertIn("source", section)
            self.assertIn("relevance_score", section)
    
    @patch('requests.post')
    def test_generate_answer_success(self, mock_post):
        """Test successful answer generation."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Artificial intelligence refers to machine learning algorithms that can process data and make decisions."
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        question = "What is artificial intelligence?"
        context_sections = [
            {
                "text": "This document discusses artificial intelligence and machine learning algorithms.",
                "source": "Document Content",
                "relevance_score": 0.8
            }
        ]
        
        answer = self.qa_engine.generate_answer(question, context_sections, self.test_document)
        
        # Should return the generated answer
        self.assertIn("artificial intelligence", answer.lower())
        
        # Verify API call was made
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_generate_answer_api_error(self, mock_post):
        """Test answer generation with API error."""
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        question = "What is artificial intelligence?"
        context_sections = [
            {
                "text": "Test content",
                "source": "Test Source",
                "relevance_score": 0.5
            }
        ]
        
        answer = self.qa_engine.generate_answer(question, context_sections, self.test_document)
        
        # Should return error message
        self.assertIn("error", answer.lower())
    
    def test_answer_question_document_not_found(self):
        """Test answering question when document is not found."""
        # Mock storage to return None
        self.mock_storage.get_document_with_embeddings.return_value = None
        
        result = self.qa_engine.answer_question("Test question", "nonexistent_doc")
        
        # Should return error response
        self.assertIn("error", result)
        self.assertIn("couldn't find", result["answer"].lower())
        self.assertEqual(result["confidence"], 0.0)
    
    @patch('requests.post')
    def test_answer_question_success(self, mock_post):
        """Test successful question answering."""
        # Mock storage to return test document
        self.mock_storage.get_document_with_embeddings.return_value = self.test_document
        
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "The document discusses artificial intelligence and machine learning algorithms."
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.qa_engine.answer_question("What does this document discuss?", "test_doc_1")
        
        # Should return successful response
        self.assertIn("answer", result)
        self.assertIn("sources", result)
        self.assertIn("confidence", result)
        self.assertGreater(result["confidence"], 0)
        self.assertEqual(result["document_title"], "Test Document")
    
    def test_create_qa_session(self):
        """Test creating a Q&A session."""
        # Mock storage
        self.mock_storage.create_qa_session.return_value = "session_123"
        
        session_id = self.qa_engine.create_qa_session("test_doc_1")
        
        # Should return a valid session ID (UUID format)
        self.assertIsInstance(session_id, str)
        self.assertGreater(len(session_id), 0)
        
        # Should call storage
        self.mock_storage.create_qa_session.assert_called_once()
    
    def test_extract_sources(self):
        """Test extracting sources from context sections."""
        context_sections = [
            {
                "text": "Test content 1",
                "source": "Document Content",
                "relevance_score": 0.8,
                "matches": 2
            },
            {
                "text": "Test content 2",
                "source": "Analysis",
                "relevance_score": 0.6,
                "matches": 1
            }
        ]
        
        sources = self.qa_engine._extract_sources(context_sections)
        
        # Should extract source information
        self.assertIsInstance(sources, list)
        self.assertGreater(len(sources), 0)
        
        # Should include relevance information
        for source in sources:
            self.assertIn("relevance:", source)


if __name__ == '__main__':
    unittest.main()