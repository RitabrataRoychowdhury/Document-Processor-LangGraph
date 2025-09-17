"""
Unit tests for the FileUploadHandler class.
Tests file validation, text extraction, and error handling.
"""

import unittest
import io
import os
import sys
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.file_handler import FileUploadHandler, FileMetadata

class TestFileUploadHandler(unittest.TestCase):
    """Test cases for FileUploadHandler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = FileUploadHandler()
    
    def test_init(self):
        """Test FileUploadHandler initialization"""
        self.assertEqual(self.handler.MAX_FILE_SIZE, 10 * 1024 * 1024)
        self.assertEqual(self.handler.supported_extensions, ['.pdf', '.txt', '.docx'])
    
    def test_validate_file_none(self):
        """Test validation with None file"""
        result = self.handler.validate_file(None)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "No file uploaded")
    
    def test_validate_file_too_large(self):
        """Test validation with oversized file"""
        mock_file = Mock()
        mock_file.name = "large_file.pdf"
        mock_file.size = 15 * 1024 * 1024  # 15MB
        
        result = self.handler.validate_file(mock_file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("exceeds maximum limit", result.error_message)
    
    def test_validate_file_unsupported_format(self):
        """Test validation with unsupported file format"""
        mock_file = Mock()
        mock_file.name = "document.xlsx"
        mock_file.size = 1024  # 1KB
        
        result = self.handler.validate_file(mock_file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported file format", result.error_message)
    
    def test_validate_file_valid_pdf(self):
        """Test validation with valid PDF file"""
        mock_file = Mock()
        mock_file.name = "document.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        
        result = self.handler.validate_file(mock_file)
        
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.file_type, ".pdf")
    
    def test_validate_file_valid_txt(self):
        """Test validation with valid TXT file"""
        mock_file = Mock()
        mock_file.name = "document.txt"
        mock_file.size = 512 * 1024  # 512KB
        
        result = self.handler.validate_file(mock_file)
        
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.file_type, ".txt")
    
    def test_validate_file_valid_docx(self):
        """Test validation with valid DOCX file"""
        mock_file = Mock()
        mock_file.name = "document.docx"
        mock_file.size = 2 * 1024 * 1024  # 2MB
        
        result = self.handler.validate_file(mock_file)
        
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.file_type, ".docx")
    
    def test_extract_txt_text_success(self):
        """Test successful text extraction from TXT file"""
        test_content = "This is a test document with some content."
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.size = len(test_content)
        mock_file.seek = Mock()
        mock_file.read = Mock(return_value=test_content.encode('utf-8'))
        
        text, error = self.handler.extract_text(mock_file)
        
        self.assertEqual(text, test_content)
        self.assertIsNone(error)
    
    def test_extract_text_invalid_file(self):
        """Test text extraction with invalid file"""
        mock_file = Mock()
        mock_file.name = "test.xyz"
        mock_file.size = 1024
        
        text, error = self.handler.extract_text(mock_file)
        
        self.assertEqual(text, "")
        self.assertIn("Unsupported file format", error)
    
    def test_get_file_metadata(self):
        """Test getting file metadata"""
        mock_file = Mock()
        mock_file.name = "test_document.pdf"
        mock_file.size = 1024 * 1024  # 1MB
        
        metadata = self.handler.get_file_metadata(mock_file)
        
        self.assertEqual(metadata['filename'], "test_document.pdf")
        self.assertEqual(metadata['file_type'], ".pdf")
        self.assertEqual(metadata['file_size'], 1024 * 1024)
        self.assertEqual(metadata['file_size_mb'], 1.0)
        self.assertTrue(metadata['is_valid'])
        self.assertIsNone(metadata['error_message'])

if __name__ == '__main__':
    unittest.main()