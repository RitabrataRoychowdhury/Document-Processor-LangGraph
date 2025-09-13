"""
Tests for factory pattern implementations.
"""

import pytest
import io
import os
from unittest.mock import Mock, patch

from src.factories.processor_factory import ProcessorFactory, PDFProcessor, DOCXProcessor, TXTProcessor


class TestProcessorFactory:
    """Test cases for ProcessorFactory."""
    
    def test_create_pdf_processor(self):
        """Test creating PDF processor."""
        factory = ProcessorFactory()
        processor = factory.create_processor("pdf")
        assert isinstance(processor, PDFProcessor)
    
    def test_create_docx_processor(self):
        """Test creating DOCX processor."""
        factory = ProcessorFactory()
        processor = factory.create_processor("docx")
        assert isinstance(processor, DOCXProcessor)
    
    def test_create_txt_processor(self):
        """Test creating TXT processor."""
        factory = ProcessorFactory()
        processor = factory.create_processor("txt")
        assert isinstance(processor, TXTProcessor)
    
    def test_create_processor_with_dot_extension(self):
        """Test creating processor with dot extension."""
        factory = ProcessorFactory()
        processor = factory.create_processor(".pdf")
        assert isinstance(processor, PDFProcessor)
    
    def test_create_processor_case_insensitive(self):
        """Test creating processor with different cases."""
        factory = ProcessorFactory()
        processor = factory.create_processor("PDF")
        assert isinstance(processor, PDFProcessor)
    
    def test_unsupported_file_type(self):
        """Test error for unsupported file type."""
        factory = ProcessorFactory()
        with pytest.raises(ValueError, match="No processor registered"):
            factory.create_processor("xyz")
    
    def test_get_supported_types(self):
        """Test getting supported file types."""
        factory = ProcessorFactory()
        supported = factory.get_supported_types()
        assert ".pdf" in supported
        assert ".docx" in supported
        assert ".txt" in supported
    
    def test_is_supported(self):
        """Test checking if file type is supported."""
        factory = ProcessorFactory()
        assert factory.is_supported("pdf")
        assert factory.is_supported(".pdf")
        assert factory.is_supported("PDF")
        assert not factory.is_supported("xyz")
    
    def test_register_custom_processor(self):
        """Test registering custom processor."""
        factory = ProcessorFactory()
        
        class CustomProcessor(PDFProcessor):
            pass
        
        factory.register_processor(".custom", CustomProcessor)
        processor = factory.create_processor("custom")
        assert isinstance(processor, CustomProcessor)


class TestPDFProcessor:
    """Test cases for PDFProcessor."""
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        processor = PDFProcessor()
        extensions = processor.get_supported_extensions()
        assert extensions == ['.pdf']
    
    def test_extract_text_with_mock_pdf(self):
        """Test text extraction with mock PDF."""
        processor = PDFProcessor()
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # Mock PyPDF2.PdfReader
        with patch('src.factories.processor_factory.PyPDF2.PdfReader') as mock_reader_class:
            mock_reader = Mock()
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test PDF content"
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader
            
            result = processor.extract_text(mock_file)
            assert result == "Test PDF content"
    
    def test_extract_metadata_with_mock_pdf(self):
        """Test metadata extraction with mock PDF."""
        processor = PDFProcessor()
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # Mock PyPDF2.PdfReader
        with patch('src.factories.processor_factory.PyPDF2.PdfReader') as mock_reader_class:
            mock_reader = Mock()
            mock_reader.pages = [Mock(), Mock()]  # 2 pages
            mock_reader.metadata = {
                "/Title": "Test Document",
                "/Author": "Test Author"
            }
            mock_reader_class.return_value = mock_reader
            
            result = processor.extract_metadata(mock_file)
            assert result["page_count"] == 2
            assert result["processor_type"] == "PDF"
            assert result["title"] == "Test Document"
            assert result["author"] == "Test Author"


class TestTXTProcessor:
    """Test cases for TXTProcessor."""
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        processor = TXTProcessor()
        extensions = processor.get_supported_extensions()
        assert extensions == ['.txt']
    
    def test_extract_text_from_string_content(self):
        """Test text extraction from string content."""
        processor = TXTProcessor()
        
        # Create a mock file-like object with string content
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = "Test text content"
        
        result = processor.extract_text(mock_file)
        assert result == "Test text content"
    
    def test_extract_text_from_bytes_content(self):
        """Test text extraction from bytes content."""
        processor = TXTProcessor()
        
        # Create a mock file-like object with bytes content
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = b"Test text content"
        
        result = processor.extract_text(mock_file)
        assert result == "Test text content"
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        processor = TXTProcessor()
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.seek = Mock()
        mock_file.read.return_value = "Line 1\nLine 2\nLine 3"
        
        result = processor.extract_metadata(mock_file)
        assert result["processor_type"] == "TXT"
        assert result["line_count"] == 3
        assert result["word_count"] == 6  # "Line 1 Line 2 Line 3" = 6 words


class TestDOCXProcessor:
    """Test cases for DOCXProcessor."""
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        processor = DOCXProcessor()
        extensions = processor.get_supported_extensions()
        assert extensions == ['.docx']
    
    def test_extract_text_with_mock_docx(self):
        """Test text extraction with mock DOCX."""
        processor = DOCXProcessor()
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # Mock docx.Document
        with patch('src.factories.processor_factory.DocxDocument') as mock_doc_class:
            mock_doc = Mock()
            mock_paragraph1 = Mock()
            mock_paragraph1.text = "Paragraph 1"
            mock_paragraph2 = Mock()
            mock_paragraph2.text = "Paragraph 2"
            mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
            mock_doc_class.return_value = mock_doc
            
            result = processor.extract_text(mock_file)
            assert result == "Paragraph 1\n\nParagraph 2"
    
    def test_extract_metadata_with_mock_docx(self):
        """Test metadata extraction with mock DOCX."""
        processor = DOCXProcessor()
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.seek = Mock()
        
        # Mock docx.Document
        with patch('src.factories.processor_factory.DocxDocument') as mock_doc_class:
            mock_doc = Mock()
            mock_doc.paragraphs = [Mock(), Mock()]  # 2 paragraphs
            
            # Mock core properties
            mock_core_props = Mock()
            mock_core_props.title = "Test Document"
            mock_core_props.author = "Test Author"
            mock_core_props.subject = None
            mock_core_props.keywords = None
            mock_core_props.comments = None
            mock_core_props.created = None
            mock_core_props.modified = None
            mock_core_props.last_modified_by = None
            mock_doc.core_properties = mock_core_props
            
            mock_doc_class.return_value = mock_doc
            
            result = processor.extract_metadata(mock_file)
            assert result["paragraph_count"] == 2
            assert result["processor_type"] == "DOCX"
            assert result["title"] == "Test Document"
            assert result["author"] == "Test Author"
    
    def test_error_handling(self):
        """Test error handling in DOCX processing."""
        processor = DOCXProcessor()
        
        # Test with invalid file
        with patch('src.factories.processor_factory.DocxDocument') as mock_doc_class:
            mock_doc_class.side_effect = Exception("Invalid DOCX file")
            
            mock_file = Mock()
            mock_file.seek = Mock()
            
            with pytest.raises(Exception):
                processor.extract_text(mock_file)


class TestProcessorFactoryIntegration:
    """Test processor factory integration scenarios."""
    
    def test_processor_factory_with_real_file_extensions(self):
        """Test factory with various real file extensions."""
        factory = ProcessorFactory()
        
        test_cases = [
            ("document.pdf", PDFProcessor),
            ("report.PDF", PDFProcessor),
            ("template.docx", DOCXProcessor),
            ("notes.DOCX", DOCXProcessor),
            ("readme.txt", TXTProcessor),
            ("log.TXT", TXTProcessor),
        ]
        
        for filename, expected_type in test_cases:
            # Extract extension from filename
            ext = os.path.splitext(filename)[1]
            processor = factory.create_processor(ext)
            assert isinstance(processor, expected_type)
    
    def test_processor_factory_error_scenarios(self):
        """Test processor factory error handling."""
        factory = ProcessorFactory()
        
        # Test with None
        with pytest.raises((ValueError, AttributeError)):
            factory.create_processor(None)
        
        # Test with empty string
        with pytest.raises(ValueError):
            factory.create_processor("")
        
        # Test with unsupported extension
        with pytest.raises(ValueError):
            factory.create_processor(".xyz")
    
    def test_processor_factory_registration_edge_cases(self):
        """Test edge cases in processor registration."""
        factory = ProcessorFactory()
        
        # Test registering with None processor class
        with pytest.raises((TypeError, AttributeError)):
            factory.register_processor(".test", None)
        
        # Test registering with invalid processor class
        class InvalidProcessor:
            pass
        
        # Note: The current implementation doesn't validate processor class inheritance
        # This test documents the current behavior
        factory.register_processor(".test", InvalidProcessor)
        # The factory accepts any class, validation happens at creation time