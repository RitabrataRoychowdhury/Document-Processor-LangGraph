"""
Centralized exception hierarchy for the QME system.

This module defines the custom exception hierarchy used throughout the QME system
to provide clear error categorization and handling.
"""

import traceback
from typing import Optional, Dict, Any
from datetime import datetime


class QMESystemError(Exception):
    """Base exception for QME system errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc() if cause else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "traceback": self.traceback,
            "cause": str(self.cause) if self.cause else None
        }


class ExtractionError(QMESystemError):
    """Errors during document extraction."""
    pass


class ValidationError(QMESystemError):
    """Errors during evidence validation."""
    pass


class GenerationError(QMESystemError):
    """Errors during content generation."""
    pass


class ComplianceError(QMESystemError):
    """Errors during compliance validation."""
    pass


class CalculationError(QMESystemError):
    """Errors during programmatic calculations."""
    pass


class KnowledgeGraphError(QMESystemError):
    """Errors related to knowledge graph operations."""
    pass


class StorageError(QMESystemError):
    """Errors related to data storage operations."""
    pass


class ConfigurationError(QMESystemError):
    """Errors related to system configuration."""
    pass


class APIError(QMESystemError):
    """Errors related to external API calls."""
    pass


class WorkflowError(QMESystemError):
    """Errors related to workflow execution."""
    pass


# Specific error types for common scenarios
class DocumentNotFoundError(ExtractionError):
    """Document not found or inaccessible."""
    pass


class InvalidDocumentFormatError(ExtractionError):
    """Document format is not supported or invalid."""
    pass


class FieldExtractionError(ExtractionError):
    """Error extracting specific fields from document."""
    pass


class ConfidenceThresholdError(ValidationError):
    """Field confidence below required threshold."""
    pass


class ComplianceViolationError(ComplianceError):
    """Document violates compliance requirements."""
    pass


class TemplateGenerationError(GenerationError):
    """Error generating template."""
    pass


class ImpairmentCalculationError(CalculationError):
    """Error in impairment calculation."""
    pass


class DatabaseConnectionError(StorageError):
    """Database connection failed."""
    pass


class ExternalAPITimeoutError(APIError):
    """External API call timed out."""
    pass


class ExternalAPIRateLimitError(APIError):
    """External API rate limit exceeded."""
    pass