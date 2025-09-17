"""Tests for the error handling system."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.error_handling import (
    DocumentQAError, ErrorType, FileUploadError, APIError, DatabaseError,
    handle_errors, safe_execute, format_error_for_ui, ErrorRecovery
)


class TestDocumentQAError(unittest.TestCase):
    """Test cases for DocumentQAError and its subclasses."""
    
    def test_base_error_creation(self):
        """Test creating a base DocumentQAError."""
        error = DocumentQAError(
            "Test error message",
            ErrorType.SYSTEM_ERROR,
            {"key": "value"},
            ValueError("Original error")
        )
        
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.error_type, ErrorType.SYSTEM_ERROR)
        self.assertEqual(error.details["key"], "value")
        self.assertIsInstance(error.original_error, ValueError)
    
    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = DocumentQAError(
            "Test error",
            ErrorType.FILE_UPLOAD,
            {"filename": "test.pdf"}
        )
        
        error_dict = error.to_dict()
        
        self.assertTrue(error_dict["error"])
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["error_type"], "file_upload")
        self.assertEqual(error_dict["details"]["filename"], "test.pdf")
        self.assertIsNone(error_dict["original_error"])
    
    def test_file_upload_error(self):
        """Test FileUploadError creation."""
        error = FileUploadError("File too large", {"size": 15000000})
        
        self.assertEqual(error.error_type, ErrorType.FILE_UPLOAD)
        self.assertEqual(error.message, "File too large")
        self.assertEqual(error.details["size"], 15000000)
    
    def test_api_error(self):
        """Test APIError creation."""
        error = APIError("API rate limit exceeded", {"retry_after": 60})
        
        self.assertEqual(error.error_type, ErrorType.API_ERROR)
        self.assertEqual(error.message, "API rate limit exceeded")
        self.assertEqual(error.details["retry_after"], 60)
    
    def test_database_error(self):
        """Test DatabaseError creation."""
        error = DatabaseError("Connection failed", {"host": "localhost"})
        
        self.assertEqual(error.error_type, ErrorType.DATABASE_ERROR)
        self.assertEqual(error.message, "Connection failed")
        self.assertEqual(error.details["host"], "localhost")


class TestErrorDecorator(unittest.TestCase):
    """Test cases for the error handling decorator."""
    
    def test_handle_errors_success(self):
        """Test decorator with successful function execution."""
        @handle_errors(ErrorType.SYSTEM_ERROR)
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        self.assertEqual(result, 5)
    
    def test_handle_errors_with_exception(self):
        """Test decorator with function that raises exception."""
        @handle_errors(ErrorType.SYSTEM_ERROR)
        def failing_function():
            raise ValueError("Test error")
        
        with self.assertRaises(DocumentQAError) as context:
            failing_function()
        
        self.assertEqual(context.exception.error_type, ErrorType.SYSTEM_ERROR)
        self.assertIn("Test error", context.exception.message)
        self.assertIsInstance(context.exception.original_error, ValueError)
    
    def test_handle_errors_return_dict(self):
        """Test decorator returning error dictionary."""
        @handle_errors(ErrorType.SYSTEM_ERROR, return_error_dict=True)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        self.assertTrue(result["error"])
        self.assertIn("Test error", result["message"])
        self.assertEqual(result["error_type"], "system_error")
    
    def test_handle_errors_reraise_custom(self):
        """Test decorator re-raising custom errors."""
        @handle_errors(ErrorType.SYSTEM_ERROR)
        def function_with_custom_error():
            raise FileUploadError("Custom error")
        
        with self.assertRaises(FileUploadError):
            function_with_custom_error()


class TestSafeExecute(unittest.TestCase):
    """Test cases for safe_execute function."""
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def successful_function(x):
            return x * 2
        
        result, error = safe_execute(successful_function, 5)
        
        self.assertEqual(result, 10)
        self.assertIsNone(error)
    
    def test_safe_execute_failure(self):
        """Test safe_execute with failing function."""
        def failing_function():
            raise ValueError("Test error")
        
        result, error = safe_execute(failing_function)
        
        self.assertIsNone(result)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(str(error), "Test error")


class TestFormatErrorForUI(unittest.TestCase):
    """Test cases for format_error_for_ui function."""
    
    def test_format_document_qa_error(self):
        """Test formatting DocumentQAError for UI."""
        error = FileUploadError("File too large", {"size": 15000000})
        
        formatted = format_error_for_ui(error)
        
        self.assertTrue(formatted["error"])
        self.assertEqual(formatted["message"], "File too large")
        self.assertEqual(formatted["type"], "file_upload")
        self.assertIn("file", formatted["user_message"].lower())
        self.assertEqual(formatted["details"]["size"], 15000000)
    
    def test_format_standard_exception(self):
        """Test formatting standard exception for UI."""
        error = ValueError("Standard error")
        
        formatted = format_error_for_ui(error)
        
        self.assertTrue(formatted["error"])
        self.assertEqual(formatted["message"], "Standard error")
        self.assertEqual(formatted["type"], "system_error")
        self.assertEqual(formatted["user_message"], "An unexpected error occurred. Please try again.")
        self.assertEqual(formatted["details"]["exception_type"], "ValueError")
    
    def test_format_string_error(self):
        """Test formatting string error for UI."""
        error = "Simple error message"
        
        formatted = format_error_for_ui(error)
        
        self.assertTrue(formatted["error"])
        self.assertEqual(formatted["message"], "Simple error message")
        self.assertEqual(formatted["type"], "unknown_error")
        self.assertEqual(formatted["user_message"], "Simple error message")


class TestErrorRecovery(unittest.TestCase):
    """Test cases for ErrorRecovery utilities."""
    
    def test_retry_with_backoff_success(self):
        """Test retry with successful function."""
        call_count = 0
        
        def function_that_succeeds():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result, error = ErrorRecovery.retry_with_backoff(function_that_succeeds, max_retries=3)
        
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        self.assertEqual(call_count, 1)
    
    def test_retry_with_backoff_eventual_success(self):
        """Test retry with function that succeeds after failures."""
        call_count = 0
        
        def function_that_eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result, error = ErrorRecovery.retry_with_backoff(
                function_that_eventually_succeeds, 
                max_retries=3,
                backoff_factor=0.1
            )
        
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        self.assertEqual(call_count, 3)
    
    def test_retry_with_backoff_all_failures(self):
        """Test retry with function that always fails."""
        call_count = 0
        
        def function_that_always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result, error = ErrorRecovery.retry_with_backoff(
                function_that_always_fails, 
                max_retries=3,
                backoff_factor=0.1
            )
        
        self.assertIsNone(result)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(call_count, 3)
    
    def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker with normal operation."""
        @ErrorRecovery.circuit_breaker(failure_threshold=3, recovery_timeout=1)
        def normal_function(x):
            return x * 2
        
        # Should work normally
        result = normal_function(5)
        self.assertEqual(result, 10)
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        call_count = 0
        
        @ErrorRecovery.circuit_breaker(failure_threshold=3, recovery_timeout=1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")
        
        # First 3 calls should raise ValueError
        for i in range(3):
            with self.assertRaises(ValueError):
                failing_function()
        
        # 4th call should raise DocumentQAError (circuit open)
        with self.assertRaises(DocumentQAError) as context:
            failing_function()
        
        self.assertEqual(context.exception.error_type, ErrorType.SYSTEM_ERROR)
        self.assertIn("Circuit breaker is open", context.exception.message)
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        call_count = 0
        
        @ErrorRecovery.circuit_breaker(failure_threshold=2, recovery_timeout=0.1)  # Short timeout for testing
        def function_that_recovers():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError(f"Failure {call_count}")
            return "success"
        
        # First 2 calls fail
        for i in range(2):
            with self.assertRaises(ValueError):
                function_that_recovers()
        
        # 3rd call should open circuit
        with self.assertRaises(DocumentQAError):
            function_that_recovers()
        
        # Wait for recovery timeout
        import time
        time.sleep(0.2)
        
        # After recovery timeout, should work again
        result = function_that_recovers()
        self.assertEqual(result, "success")


if __name__ == '__main__':
    unittest.main()