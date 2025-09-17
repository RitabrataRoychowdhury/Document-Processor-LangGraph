"""
File upload and text extraction service for the document Q&A system.
Handles file validation, text extraction from various formats, and error handling.
Refactored to use Factory Pattern for document processing.
"""

import os
import io
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Conditional import for streamlit
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from src.factories.processor_factory import ProcessorFactory
    from src.utils.logging_config import get_logger
    from src.utils.error_handling import FileUploadError, FileProcessingError, handle_errors
except ImportError:
    from factories.processor_factory import ProcessorFactory
    from utils.logging_config import get_logger
    from utils.error_handling import FileUploadError, FileProcessingError, handle_errors

logger = get_logger(__name__)

@dataclass
class FileMetadata:
    """Metadata for uploaded files"""
    filename: str
    file_type: str
    file_size: int
    is_valid: bool
    error_message: Optional[str] = None

class FileUploadHandler:
    """Handles file uploads, validation, and text extraction using Factory Pattern"""
    
    # Supported file formats and their MIME types
    SUPPORTED_FORMATS = {
        'pdf': ['application/pdf'],
        'txt': ['text/plain'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    def __init__(self, processor_factory: Optional[ProcessorFactory] = None):
        """
        Initialize the file upload handler with processor factory.
        
        Args:
            processor_factory: Factory for creating document processors. 
                             If None, uses the global factory instance.
        """
        self.processor_factory = processor_factory or ProcessorFactory()
        self.supported_extensions = self.processor_factory.get_supported_types()
        logger.info(f"Initialized FileUploadHandler with supported types: {self.supported_extensions}")
    
    def validate_file(self, uploaded_file) -> FileMetadata:
        """
        Validate uploaded file format and size
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            FileMetadata: Validation results and metadata
        """
        try:
            if uploaded_file is None:
                return FileMetadata(
                    filename="",
                    file_type="",
                    file_size=0,
                    is_valid=False,
                    error_message="No file uploaded"
                )
            
            filename = uploaded_file.name
            file_size = uploaded_file.size
            
            # Check file size
            if file_size > self.MAX_FILE_SIZE:
                return FileMetadata(
                    filename=filename,
                    file_type="",
                    file_size=file_size,
                    is_valid=False,
                    error_message=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of 10MB"
                )
            
            # Check file extension
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension not in self.supported_extensions:
                return FileMetadata(
                    filename=filename,
                    file_type=file_extension,
                    file_size=file_size,
                    is_valid=False,
                    error_message=f"Unsupported file format '{file_extension}'. Supported formats: {', '.join(self.supported_extensions)}"
                )
            
            return FileMetadata(
                filename=filename,
                file_type=file_extension,
                file_size=file_size,
                is_valid=True
            )
            
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return FileMetadata(
                filename=getattr(uploaded_file, 'name', 'unknown'),
                file_type="",
                file_size=0,
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def extract_text(self, uploaded_file) -> Tuple[str, Optional[str]]:
        """
        Extract text content from uploaded file using processor factory.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Tuple[str, Optional[str]]: (extracted_text, error_message)
        """
        try:
            # Validate file first
            metadata = self.validate_file(uploaded_file)
            if not metadata.is_valid:
                return "", metadata.error_message
            
            file_extension = metadata.file_type
            
            # Use processor factory to get appropriate processor
            try:
                processor = self.processor_factory.create_processor(file_extension)
                extracted_text = processor.extract_text(uploaded_file)
                return extracted_text, None
            except ValueError as e:
                logger.error(f"No processor available for file type {file_extension}: {e}")
                return "", f"Unsupported file format: {file_extension}"
            except Exception as e:
                logger.error(f"Processor failed to extract text: {e}")
                return "", f"Text extraction failed: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            return "", f"Text extraction failed: {str(e)}"
    
    def extract_metadata(self, uploaded_file) -> Dict[str, Any]:
        """
        Extract metadata from uploaded file using processor factory.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Dict[str, Any]: File metadata including processor-specific metadata
        """
        try:
            # Get basic file metadata
            basic_metadata = self.get_file_metadata(uploaded_file)
            
            if not basic_metadata['is_valid']:
                return basic_metadata
            
            file_extension = basic_metadata['file_type']
            
            # Use processor factory to get detailed metadata
            try:
                processor = self.processor_factory.create_processor(file_extension)
                processor_metadata = processor.extract_metadata(uploaded_file)
                
                # Combine basic and processor metadata
                combined_metadata = {**basic_metadata, **processor_metadata}
                return combined_metadata
                
            except ValueError as e:
                logger.error(f"No processor available for metadata extraction: {e}")
                basic_metadata['metadata_error'] = str(e)
                return basic_metadata
            except Exception as e:
                logger.error(f"Processor failed to extract metadata: {e}")
                basic_metadata['metadata_error'] = str(e)
                return basic_metadata
                
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                'filename': getattr(uploaded_file, 'name', 'unknown'),
                'error': str(e),
                'is_valid': False
            }
    
    def get_file_metadata(self, uploaded_file) -> Dict[str, Any]:
        """
        Get comprehensive metadata for uploaded file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Dict[str, Any]: File metadata dictionary
        """
        metadata = self.validate_file(uploaded_file)
        
        return {
            'filename': metadata.filename,
            'file_type': metadata.file_type,
            'file_size': metadata.file_size,
            'file_size_mb': round(metadata.file_size / (1024 * 1024), 2),
            'is_valid': metadata.is_valid,
            'error_message': metadata.error_message,
            'supported_formats': self.supported_extensions
        }