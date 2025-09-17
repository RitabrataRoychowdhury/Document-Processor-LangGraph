"""Ingest command for document ingestion and text extraction."""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from .base import Command, CommandResult, RetryableException, NonRetryableException
from src.factories.processor_factory import ProcessorFactory
from src.models.document import Document
from src.storage.document_storage import DocumentStorage

logger = logging.getLogger(__name__)


class IngestCommand(Command):
    """Command for ingesting documents and extracting text content."""
    
    def __init__(self, file_path: str, document_id: Optional[str] = None, 
                 processor_factory: Optional[ProcessorFactory] = None,
                 storage: Optional[DocumentStorage] = None):
        super().__init__()
        self.file_path = file_path
        self.document_id = document_id
        self.processor_factory = processor_factory or ProcessorFactory()
        self.storage = storage or DocumentStorage()
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise NonRetryableException(f"File not found: {file_path}")
    
    def execute(self) -> CommandResult:
        """Execute document ingestion."""
        try:
            logger.info(f"Starting document ingestion for: {self.file_path}")
            
            # Get file extension to determine processor type
            file_ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
            
            # Create appropriate processor
            try:
                processor = self.processor_factory.create_processor(file_ext)
            except ValueError as e:
                return CommandResult.failure_result(
                    message=f"Unsupported file type: {file_ext}",
                    error=NonRetryableException(str(e))
                )
            
            # Extract text from document
            try:
                extracted_text = processor.extract_text(self.file_path)
                if not extracted_text or not extracted_text.strip():
                    return CommandResult.failure_result(
                        message="No text content extracted from document",
                        error=NonRetryableException("Empty document content")
                    )
            except Exception as e:
                # Text extraction failures might be retryable (e.g., temporary file locks)
                logger.warning(f"Text extraction failed: {e}")
                raise RetryableException(f"Failed to extract text: {str(e)}")
            
            # Extract metadata
            try:
                metadata = processor.extract_metadata(self.file_path)
            except Exception as e:
                logger.warning(f"Metadata extraction failed, continuing with basic metadata: {e}")
                metadata = {
                    'file_name': os.path.basename(self.file_path),
                    'file_size': os.path.getsize(self.file_path),
                    'file_type': file_ext
                }
            
            # Create or update document
            if self.document_id:
                # Update existing document
                document_data = {
                    'original_text': extracted_text,
                    'extracted_info': metadata,
                    'processing_status': 'ingested'
                }
                self.storage.update_document(self.document_id, document_data)
                document_id = self.document_id
            else:
                # Create new document
                import uuid
                document = Document(
                    id=str(uuid.uuid4()),
                    title=os.path.basename(self.file_path),
                    file_type=file_ext,
                    file_size=os.path.getsize(self.file_path),
                    upload_timestamp=datetime.now(),
                    original_text=extracted_text,
                    extracted_info=metadata,
                    processing_status='ingested'
                )
                document_id = self.storage.create_document(document)
            
            result_data = {
                'document_id': document_id,
                'file_path': self.file_path,
                'text_length': len(extracted_text),
                'metadata': metadata
            }
            
            logger.info(f"Successfully ingested document {document_id} from {self.file_path}")
            
            return CommandResult.success_result(
                message=f"Successfully ingested document from {self.file_path}",
                data=result_data
            )
            
        except RetryableException:
            # Re-raise retryable exceptions
            raise
        except NonRetryableException as e:
            return CommandResult.failure_result(
                message=f"Non-retryable error during ingestion: {str(e)}",
                error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error during document ingestion: {e}")
            # Treat unexpected errors as retryable
            raise RetryableException(f"Unexpected ingestion error: {str(e)}")
    
    def can_retry(self) -> bool:
        """Ingest operations can be retried for certain types of failures."""
        return True
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get information about this ingest command."""
        info = super().get_command_info()
        info.update({
            'file_path': self.file_path,
            'document_id': self.document_id,
            'file_exists': os.path.exists(self.file_path) if self.file_path else False
        })
        return info