"""Comprehensive error handling utilities for the Document Q&A System."""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, Tuple, Union
from enum import Enum

try:
    from src.utils.logging_config import get_logger
except ImportError:
    from utils.logging_config import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """Enumeration of error types in the system."""
    FILE_UPLOAD = "file_upload"
    FILE_PROCESSING = "file_processing"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    WORKFLOW_ERROR = "workflow_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    STORAGE_ERROR = "storage_error"
    QA_ERROR = "qa_error"
    SYSTEM_ERROR = "system_error"


class DocumentQAError(Exception):
    """Base exception class for Document Q&A System errors."""
    
    def __init__(self, message: str, error_type: ErrorType, 
                 details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "error": True,
            "message": self.message,
            "error_type": self.error_type.value,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class FileUploadError(DocumentQAError):
    """Error during file upload operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.FILE_UPLOAD, details, original_error)


class FileProcessingError(DocumentQAError):
    """Error during file processing operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.FILE_PROCESSING, details, original_error)


class APIError(DocumentQAError):
    """Error during API calls."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.API_ERROR, details, original_error)


class DatabaseError(DocumentQAError):
    """Error during database operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.DATABASE_ERROR, details, original_error)


class WorkflowError(DocumentQAError):
    """Error during workflow processing."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.WORKFLOW_ERROR, details, original_error)


class ValidationError(DocumentQAError):
    """Error during data validation."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.VALIDATION_ERROR, details, original_error)


class TimeoutError(DocumentQAError):
    """Error due to operation timeout."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.TIMEOUT_ERROR, details, original_error)


class StorageError(DocumentQAError):
    """Error during storage operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.STORAGE_ERROR, details, original_error)


class QAError(DocumentQAError):
    """Error during Q&A operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.QA_ERROR, details, original_error)


class RetryableException(DocumentQAError):
    """Exception that indicates the operation can be retried."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.SYSTEM_ERROR, details, original_error)


class NonRetryableException(DocumentQAError):
    """Exception that indicates the operation should not be retried."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message, ErrorType.SYSTEM_ERROR, details, original_error)


def handle_errors(error_type: ErrorType = ErrorType.SYSTEM_ERROR, 
                 return_error_dict: bool = False,
                 log_error: bool = True):
    """Decorator for handling errors in functions."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DocumentQAError:
                # Re-raise our custom errors
                raise
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                
                error = DocumentQAError(
                    message=f"Error in {func.__name__}: {str(e)}",
                    error_type=error_type,
                    details={"function": func.__name__, "args": str(args)},
                    original_error=e
                )
                
                if return_error_dict:
                    return error.to_dict()
                else:
                    raise error
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, **kwargs) -> Tuple[Any, Optional[Exception]]:
    """Safely execute a function and return result and error."""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}", exc_info=True)
        return None, e


def format_error_for_ui(error: Union[Exception, DocumentQAError, str]) -> Dict[str, Any]:
    """Format error for display in UI."""
    if isinstance(error, DocumentQAError):
        return {
            "error": True,
            "message": error.message,
            "type": error.error_type.value,
            "user_message": _get_user_friendly_message(error),
            "details": error.details
        }
    elif isinstance(error, Exception):
        return {
            "error": True,
            "message": str(error),
            "type": "system_error",
            "user_message": "An unexpected error occurred. Please try again.",
            "details": {"exception_type": type(error).__name__}
        }
    else:
        return {
            "error": True,
            "message": str(error),
            "type": "unknown_error",
            "user_message": str(error),
            "details": {}
        }


def _get_user_friendly_message(error: DocumentQAError) -> str:
    """Get user-friendly error message based on error type."""
    error_messages = {
        ErrorType.FILE_UPLOAD: "There was a problem uploading your file. Please check the file format and size.",
        ErrorType.FILE_PROCESSING: "We couldn't process your document. Please try uploading it again.",
        ErrorType.API_ERROR: "There was a problem connecting to our AI service. Please try again in a moment.",
        ErrorType.DATABASE_ERROR: "There was a problem saving your data. Please try again.",
        ErrorType.WORKFLOW_ERROR: "There was a problem processing your document. Please try again.",
        ErrorType.VALIDATION_ERROR: "The provided data is invalid. Please check your input.",
        ErrorType.TIMEOUT_ERROR: "The operation took too long to complete. Please try again.",
        ErrorType.STORAGE_ERROR: "There was a problem storing your document. Please try again.",
        ErrorType.QA_ERROR: "There was a problem answering your question. Please try rephrasing it.",
        ErrorType.SYSTEM_ERROR: "An unexpected error occurred. Please try again."
    }
    
    return error_messages.get(error.error_type, error.message)


class ErrorRecovery:
    """Utilities for error recovery and retry logic."""
    
    @staticmethod
    def retry_with_backoff(func: Callable, max_retries: int = 3, 
                          backoff_factor: float = 1.0) -> Tuple[Any, Optional[Exception]]:
        """Retry a function with exponential backoff."""
        import time
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = func()
                return result, None
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed: {str(e)}")
        
        return None, last_error
    
    @staticmethod
    def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
        """Circuit breaker pattern for preventing cascading failures."""
        def decorator(func: Callable) -> Callable:
            func._failure_count = 0
            func._last_failure_time = 0
            func._is_open = False
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                import time
                
                current_time = time.time()
                
                # Check if circuit is open and recovery time has passed
                if func._is_open:
                    if current_time - func._last_failure_time > recovery_timeout:
                        func._is_open = False
                        func._failure_count = 0
                        logger.info(f"Circuit breaker for {func.__name__} is now closed")
                    else:
                        raise DocumentQAError(
                            f"Circuit breaker is open for {func.__name__}",
                            ErrorType.SYSTEM_ERROR,
                            {"retry_after": recovery_timeout - (current_time - func._last_failure_time)}
                        )
                
                try:
                    result = func(*args, **kwargs)
                    # Reset failure count on success
                    func._failure_count = 0
                    return result
                except Exception as e:
                    func._failure_count += 1
                    func._last_failure_time = current_time
                    
                    if func._failure_count >= failure_threshold:
                        func._is_open = True
                        logger.error(f"Circuit breaker opened for {func.__name__} after {failure_threshold} failures")
                    
                    raise e
            
            return wrapper
        return decorator


# Global error recovery instance
error_recovery = ErrorRecovery()