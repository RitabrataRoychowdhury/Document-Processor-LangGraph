"""
Error Message Formatter

Converts technical errors to user-friendly messages with contextual information
and actionable recovery suggestions.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Categories of errors for better user messaging."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    FILE_PROCESSING = "file_processing"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION = "validation"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class UserFriendlyError:
    """User-friendly error representation."""
    title: str
    message: str
    category: ErrorCategory
    severity: str
    recovery_suggestions: List[str]
    technical_details: Optional[str] = None
    help_url: Optional[str] = None


class ErrorMessageFormatter:
    """
    Formats technical errors into user-friendly messages with recovery suggestions.
    """
    
    def __init__(self):
        """Initialize the error message formatter."""
        self.error_patterns = self._initialize_error_patterns()
        self.recovery_suggestions = self._initialize_recovery_suggestions()
    
    def format_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
        """
        Format an error into a user-friendly message.
        
        Args:
            error: The exception to format
            context: Additional context about where the error occurred
            
        Returns:
            UserFriendlyError with formatted message and suggestions
        """
        error_str = str(error)
        error_type = type(error).__name__
        
        # Categorize the error
        category = self._categorize_error(error, error_str, context)
        
        # Get user-friendly message
        title, message = self._get_user_friendly_message(error, error_str, error_type, category, context)
        
        # Get recovery suggestions
        suggestions = self._get_recovery_suggestions(error, category, context)
        
        # Determine severity
        severity = self._determine_severity(error, category)
        
        # Get help URL if available
        help_url = self._get_help_url(category, error_type)
        
        return UserFriendlyError(
            title=title,
            message=message,
            category=category,
            severity=severity,
            recovery_suggestions=suggestions,
            technical_details=f"{error_type}: {error_str}",
            help_url=help_url
        )
    
    def _initialize_error_patterns(self) -> Dict[str, Tuple[ErrorCategory, str, str]]:
        """Initialize error patterns for categorization and messaging."""
        return {
            # Configuration errors
            r"(?i).*api.*key.*not.*found.*": (
                ErrorCategory.CONFIGURATION,
                "API Configuration Missing",
                "Your API key is not configured. Please set up your API credentials to use this feature."
            ),
            r"(?i).*environment.*variable.*not.*set.*": (
                ErrorCategory.CONFIGURATION,
                "Configuration Missing",
                "Required configuration is missing. Please check your environment settings."
            ),
            r"(?i).*config.*file.*not.*found.*": (
                ErrorCategory.CONFIGURATION,
                "Configuration File Missing",
                "The configuration file could not be found. Please ensure all required files are in place."
            ),
            
            # Network errors
            r"(?i).*connection.*refused.*": (
                ErrorCategory.NETWORK,
                "Connection Failed",
                "Unable to connect to the service. Please check your internet connection."
            ),
            r"(?i).*timeout.*": (
                ErrorCategory.NETWORK,
                "Request Timeout",
                "The request took too long to complete. This might be due to network issues or server load."
            ),
            r"(?i).*network.*error.*": (
                ErrorCategory.NETWORK,
                "Network Error",
                "A network error occurred. Please check your internet connection and try again."
            ),
            
            # Authentication errors
            r"(?i).*unauthorized.*": (
                ErrorCategory.AUTHENTICATION,
                "Authentication Failed",
                "Your credentials are invalid or have expired. Please check your API key or login credentials."
            ),
            r"(?i).*forbidden.*": (
                ErrorCategory.AUTHENTICATION,
                "Access Denied",
                "You don't have permission to access this resource. Please check your account permissions."
            ),
            r"(?i).*invalid.*api.*key.*": (
                ErrorCategory.AUTHENTICATION,
                "Invalid API Key",
                "The provided API key is invalid. Please check your API key configuration."
            ),
            
            # File processing errors
            r"(?i).*file.*not.*found.*": (
                ErrorCategory.FILE_PROCESSING,
                "File Not Found",
                "The requested file could not be found. Please check the file path and try again."
            ),
            r"(?i).*permission.*denied.*": (
                ErrorCategory.PERMISSION,
                "Permission Denied",
                "Unable to access the file due to permission restrictions. Please check file permissions."
            ),
            r"(?i).*unsupported.*file.*format.*": (
                ErrorCategory.FILE_PROCESSING,
                "Unsupported File Format",
                "The file format is not supported. Please use a supported file type (PDF, DOCX, TXT)."
            ),
            r"(?i).*file.*too.*large.*": (
                ErrorCategory.FILE_PROCESSING,
                "File Too Large",
                "The file is too large to process. Please use a smaller file or split large documents."
            ),
            
            # Service unavailable errors
            r"(?i).*service.*unavailable.*": (
                ErrorCategory.SERVICE_UNAVAILABLE,
                "Service Unavailable",
                "The service is temporarily unavailable. Please try again in a few moments."
            ),
            r"(?i).*import.*error.*": (
                ErrorCategory.SERVICE_UNAVAILABLE,
                "Service Not Available",
                "A required service component is not available. Some features may be limited."
            ),
            r"(?i).*module.*not.*found.*": (
                ErrorCategory.SERVICE_UNAVAILABLE,
                "Component Missing",
                "A required component is missing. Please ensure all dependencies are installed."
            ),
            
            # Validation errors
            r"(?i).*validation.*error.*": (
                ErrorCategory.VALIDATION,
                "Validation Failed",
                "The provided data did not pass validation. Please check your input and try again."
            ),
            r"(?i).*invalid.*input.*": (
                ErrorCategory.VALIDATION,
                "Invalid Input",
                "The input provided is not valid. Please check the format and requirements."
            ),
            
            # Resource errors
            r"(?i).*out.*of.*memory.*": (
                ErrorCategory.RESOURCE,
                "Memory Error",
                "The system is running low on memory. Please try processing smaller files or restart the application."
            ),
            r"(?i).*disk.*space.*": (
                ErrorCategory.RESOURCE,
                "Storage Error",
                "Insufficient disk space available. Please free up some space and try again."
            ),
        }
    
    def _initialize_recovery_suggestions(self) -> Dict[ErrorCategory, List[str]]:
        """Initialize recovery suggestions for each error category."""
        return {
            ErrorCategory.CONFIGURATION: [
                "Check your .env file for missing or incorrect configuration",
                "Verify that all required API keys are set",
                "Ensure configuration files are in the correct location",
                "Restart the application after making configuration changes",
                "Contact your administrator for configuration assistance"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a few moments",
                "Verify that the service is accessible",
                "Check if you're behind a firewall or proxy",
                "Contact your network administrator if the problem persists"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Verify your API key is correct and active",
                "Check if your credentials have expired",
                "Ensure you have the necessary permissions",
                "Try logging out and logging back in",
                "Contact support if you believe this is an error"
            ],
            ErrorCategory.FILE_PROCESSING: [
                "Check that the file exists and is accessible",
                "Verify the file format is supported (PDF, DOCX, TXT)",
                "Ensure the file is not corrupted",
                "Try uploading a smaller file",
                "Check file permissions and try again"
            ],
            ErrorCategory.SERVICE_UNAVAILABLE: [
                "Wait a few moments and try again",
                "Check if all required services are running",
                "Restart the application",
                "Verify that all dependencies are installed",
                "Contact support if the service remains unavailable"
            ],
            ErrorCategory.VALIDATION: [
                "Check that all required fields are filled",
                "Verify the input format matches requirements",
                "Review any validation error messages",
                "Try with different input data",
                "Consult the documentation for input requirements"
            ],
            ErrorCategory.PERMISSION: [
                "Check file and folder permissions",
                "Ensure you have the necessary access rights",
                "Try running as administrator if appropriate",
                "Contact your system administrator",
                "Verify the file is not locked by another process"
            ],
            ErrorCategory.RESOURCE: [
                "Close other applications to free up memory",
                "Try processing smaller files",
                "Restart the application",
                "Free up disk space",
                "Contact support if resource issues persist"
            ],
            ErrorCategory.UNKNOWN: [
                "Try refreshing the page",
                "Restart the application",
                "Check the system logs for more details",
                "Try the operation again",
                "Contact support with the error details"
            ]
        }
    
    def _categorize_error(self, error: Exception, error_str: str, context: Optional[Dict[str, Any]]) -> ErrorCategory:
        """Categorize an error based on its type and message."""
        # Check error patterns
        for pattern, (category, _, _) in self.error_patterns.items():
            if re.search(pattern, error_str):
                return category
        
        # Check error type
        error_type = type(error).__name__
        
        if error_type in ['ImportError', 'ModuleNotFoundError']:
            return ErrorCategory.SERVICE_UNAVAILABLE
        elif error_type in ['FileNotFoundError', 'IOError']:
            return ErrorCategory.FILE_PROCESSING
        elif error_type in ['PermissionError']:
            return ErrorCategory.PERMISSION
        elif error_type in ['ConnectionError', 'TimeoutError']:
            return ErrorCategory.NETWORK
        elif error_type in ['ValueError', 'TypeError']:
            return ErrorCategory.VALIDATION
        elif error_type in ['MemoryError']:
            return ErrorCategory.RESOURCE
        
        # Check context for additional clues
        if context:
            component = context.get('component', '').lower()
            if 'config' in component:
                return ErrorCategory.CONFIGURATION
            elif 'upload' in component or 'file' in component:
                return ErrorCategory.FILE_PROCESSING
            elif 'api' in component or 'service' in component:
                return ErrorCategory.SERVICE_UNAVAILABLE
        
        return ErrorCategory.UNKNOWN
    
    def _get_user_friendly_message(self, error: Exception, error_str: str, error_type: str, 
                                  category: ErrorCategory, context: Optional[Dict[str, Any]]) -> Tuple[str, str]:
        """Get user-friendly title and message for an error."""
        # Check if we have a specific pattern match
        for pattern, (cat, title, message) in self.error_patterns.items():
            if cat == category and re.search(pattern, error_str):
                return title, message
        
        # Default messages by category
        category_messages = {
            ErrorCategory.CONFIGURATION: (
                "Configuration Issue",
                "There's a problem with the system configuration. Please check your settings."
            ),
            ErrorCategory.NETWORK: (
                "Connection Problem",
                "Unable to connect to the required service. Please check your network connection."
            ),
            ErrorCategory.AUTHENTICATION: (
                "Authentication Problem",
                "There's an issue with your credentials or permissions."
            ),
            ErrorCategory.FILE_PROCESSING: (
                "File Processing Error",
                "There was a problem processing your file. Please check the file and try again."
            ),
            ErrorCategory.SERVICE_UNAVAILABLE: (
                "Service Unavailable",
                "A required service is not available. Some features may be limited."
            ),
            ErrorCategory.VALIDATION: (
                "Input Validation Error",
                "The provided input is not valid. Please check your data and try again."
            ),
            ErrorCategory.PERMISSION: (
                "Permission Error",
                "You don't have the necessary permissions to perform this action."
            ),
            ErrorCategory.RESOURCE: (
                "Resource Error",
                "The system is running low on resources. Please try again or contact support."
            ),
            ErrorCategory.UNKNOWN: (
                "Unexpected Error",
                "An unexpected error occurred. Please try again or contact support if the problem persists."
            )
        }
        
        return category_messages.get(category, category_messages[ErrorCategory.UNKNOWN])
    
    def _get_recovery_suggestions(self, error: Exception, category: ErrorCategory, 
                                context: Optional[Dict[str, Any]]) -> List[str]:
        """Get recovery suggestions for an error."""
        suggestions = self.recovery_suggestions.get(category, self.recovery_suggestions[ErrorCategory.UNKNOWN])
        
        # Add context-specific suggestions
        if context:
            page = context.get('page', '').lower()
            component = context.get('component', '').lower()
            
            if 'upload' in page or 'upload' in component:
                if category == ErrorCategory.FILE_PROCESSING:
                    suggestions = [
                        "Try uploading a different file",
                        "Check that the file is not corrupted",
                        "Ensure the file size is under the limit (10MB)"
                    ] + suggestions
            
            elif 'template' in page or 'template' in component:
                if category == ErrorCategory.SERVICE_UNAVAILABLE:
                    suggestions = [
                        "Try using the basic template generation instead",
                        "Check that all required services are configured"
                    ] + suggestions
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> str:
        """Determine the severity level of an error."""
        critical_categories = [ErrorCategory.RESOURCE, ErrorCategory.CONFIGURATION]
        error_categories = [ErrorCategory.SERVICE_UNAVAILABLE, ErrorCategory.AUTHENTICATION, ErrorCategory.PERMISSION]
        warning_categories = [ErrorCategory.NETWORK, ErrorCategory.FILE_PROCESSING, ErrorCategory.VALIDATION]
        
        if category in critical_categories:
            return "critical"
        elif category in error_categories:
            return "error"
        elif category in warning_categories:
            return "warning"
        else:
            return "info"
    
    def _get_help_url(self, category: ErrorCategory, error_type: str) -> Optional[str]:
        """Get help URL for specific error categories."""
        help_urls = {
            ErrorCategory.CONFIGURATION: "/docs/configuration",
            ErrorCategory.AUTHENTICATION: "/docs/authentication",
            ErrorCategory.FILE_PROCESSING: "/docs/file-formats",
            ErrorCategory.SERVICE_UNAVAILABLE: "/docs/troubleshooting"
        }
        
        return help_urls.get(category)


# Global error message formatter instance
error_message_formatter = ErrorMessageFormatter()


def format_user_friendly_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> UserFriendlyError:
    """Convenience function to format an error into a user-friendly message."""
    return error_message_formatter.format_error(error, context)