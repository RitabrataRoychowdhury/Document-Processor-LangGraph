"""Document text extraction workflow node."""

import os
from typing import Dict, Any, List

from src.workflow.base.workflow_node import WorkflowNode, NodeResult
from src.factories.processor_factory import ProcessorFactory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ExtractionNode(WorkflowNode):
    """Node for document text extraction.
    
    Implements Single Responsibility Principle - handles only text extraction.
    Follows Dependency Inversion - depends on ProcessorFactory abstraction.
    """
    
    def __init__(self, processor_factory: ProcessorFactory = None, node_id: str = None, 
                 correlation_id: str = None):
        super().__init__(node_id, correlation_id)
        # Use dependency injection - don't create default if not provided
        if processor_factory is None:
            raise ValueError("ProcessorFactory must be provided via dependency injection")
        self.processor_factory = processor_factory
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute text extraction from document."""
        try:
            file_path = state['file_path']
            
            logger.info(f"Starting text extraction for {file_path} [correlation_id: {self.correlation_id}]")
            
            # Check if file exists
            if not os.path.exists(file_path):
                return NodeResult.failure_result(
                    f"File not found: {file_path}",
                    error=FileNotFoundError(f"File not found: {file_path}")
                )
            
            # Get file size and type
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
            
            # Create appropriate processor
            try:
                processor = self.processor_factory.create_processor(file_extension)
            except ValueError as e:
                return NodeResult.failure_result(
                    f"Unsupported file type: {file_extension}",
                    error=e
                )
            
            # Extract text
            extracted_text = processor.extract_text(file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                return NodeResult.failure_result(
                    "Extracted text is too short or empty",
                    error=ValueError("Insufficient text content")
                )
            
            # Extract metadata
            try:
                metadata = processor.extract_metadata(file_path)
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}")
                metadata = {}
            
            # Prepare result data
            result_data = {
                'extracted_text': extracted_text,
                'text_length': len(extracted_text),
                'file_size': file_size,
                'file_type': file_extension,
                'document_metadata': metadata,
                'extraction_method': processor.__class__.__name__
            }
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from {file_path} "
                       f"[correlation_id: {self.correlation_id}]")
            
            return NodeResult.success_result(
                f"Text extraction completed: {len(extracted_text)} characters",
                data=result_data
            )
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e} [correlation_id: {self.correlation_id}]")
            return NodeResult.failure_result(
                f"Text extraction failed: {str(e)}",
                error=e
            )
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """Validate input state for text extraction."""
        required_keys = self.get_required_inputs()
        
        for key in required_keys:
            if key not in state:
                logger.error(f"Missing required input key: {key}")
                return False
        
        file_path = state.get('file_path')
        if not isinstance(file_path, str) or not file_path.strip():
            logger.error("Invalid file_path: must be a non-empty string")
            return False
        
        return True
    
    def get_required_inputs(self) -> List[str]:
        """Get required input keys."""
        return ['file_path']
    
    def get_output_keys(self) -> List[str]:
        """Get output keys this node adds to state."""
        return [
            'extracted_text',
            'text_length',
            'file_size',
            'file_type',
            'document_metadata',
            'extraction_method'
        ]
    
    def can_retry(self, error: Exception) -> bool:
        """Determine if extraction can be retried."""
        # Don't retry for file not found or unsupported file types
        non_retryable_errors = (FileNotFoundError, ValueError)
        if isinstance(error, non_retryable_errors):
            return False
        
        # Retry for other errors (IO errors, temporary issues, etc.)
        return True


class EnhancedExtractionNode(ExtractionNode):
    """Enhanced extraction node with additional features.
    
    Extends ExtractionNode with OCR fallback and content validation.
    """
    
    def __init__(self, processor_factory: ProcessorFactory = None, 
                 enable_ocr_fallback: bool = True,
                 min_text_length: int = 50,
                 node_id: str = None, correlation_id: str = None):
        super().__init__(processor_factory, node_id, correlation_id)
        self.enable_ocr_fallback = enable_ocr_fallback
        self.min_text_length = min_text_length
    
    def execute(self, state: Dict[str, Any]) -> NodeResult:
        """Execute enhanced text extraction with OCR fallback."""
        # First try standard extraction
        result = super().execute(state)
        
        if result.success:
            extracted_text = result.data.get('extracted_text', '')
            
            # Check if text meets minimum length requirement
            if len(extracted_text.strip()) < self.min_text_length:
                logger.warning(f"Extracted text is too short ({len(extracted_text)} chars), "
                             f"minimum required: {self.min_text_length}")
                
                if self.enable_ocr_fallback:
                    logger.info("Attempting OCR fallback extraction")
                    ocr_result = self._try_ocr_extraction(state['file_path'])
                    
                    if ocr_result.success:
                        # Use OCR result if it's better
                        ocr_text = ocr_result.data.get('extracted_text', '')
                        if len(ocr_text.strip()) > len(extracted_text.strip()):
                            logger.info("OCR extraction provided better results")
                            result.data.update(ocr_result.data)
                            result.data['extraction_method'] = 'OCR_fallback'
                            result.message = f"OCR extraction completed: {len(ocr_text)} characters"
                
                # If still too short, return failure
                final_text = result.data.get('extracted_text', '')
                if len(final_text.strip()) < self.min_text_length:
                    return NodeResult.failure_result(
                        f"Extracted text too short: {len(final_text)} chars (minimum: {self.min_text_length})",
                        error=ValueError("Insufficient text content after all extraction attempts")
                    )
        
        return result
    
    def _try_ocr_extraction(self, file_path: str) -> NodeResult:
        """Try OCR extraction as fallback."""
        try:
            # This is a placeholder for OCR functionality
            # In a real implementation, you would use libraries like pytesseract
            logger.info(f"OCR extraction not implemented for {file_path}")
            
            return NodeResult.failure_result(
                "OCR extraction not implemented",
                error=NotImplementedError("OCR functionality not available")
            )
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return NodeResult.failure_result(
                f"OCR extraction failed: {str(e)}",
                error=e
            )
    
    def get_output_keys(self) -> List[str]:
        """Get output keys including OCR-specific keys."""
        base_keys = super().get_output_keys()
        return base_keys + ['ocr_attempted', 'ocr_success']