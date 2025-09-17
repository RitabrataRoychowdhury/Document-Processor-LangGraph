"""
Structured logging service with correlation IDs and request tracing.

This module provides comprehensive logging capabilities with structured format,
correlation IDs for request tracing, and integration with the error handling system.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.exceptions import QMESystemError


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context information for structured logging."""
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    workflow_id: Optional[str] = None
    document_id: Optional[str] = None
    service_name: Optional[str] = None
    operation: Optional[str] = None


# Context variable for storing log context across async calls
log_context: ContextVar[Optional[LogContext]] = ContextVar('log_context', default=None)


class StructuredLogger:
    """Structured logger with correlation ID support."""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        
        # Configure structured formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _create_log_entry(
        self,
        level: LogLevel,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Create structured log entry."""
        context = log_context.get()
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "logger": self.name,
            "message": message,
            "correlation_id": context.correlation_id if context else str(uuid.uuid4()),
        }
        
        # Add context information
        if context:
            entry.update({
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": context.request_id,
                "workflow_id": context.workflow_id,
                "document_id": context.document_id,
                "service_name": context.service_name,
                "operation": context.operation,
            })
        
        # Add extra data
        if extra_data:
            entry["data"] = extra_data
        
        # Add error information
        if error:
            if isinstance(error, QMESystemError):
                entry["error"] = error.to_dict()
            else:
                entry["error"] = {
                    "type": error.__class__.__name__,
                    "message": str(error),
                    "traceback": str(error.__traceback__) if error.__traceback__ else None
                }
        
        # Remove None values
        return {k: v for k, v in entry.items() if v is not None}
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        entry = self._create_log_entry(LogLevel.DEBUG, message, extra_data)
        self.logger.debug(json.dumps(entry))
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        entry = self._create_log_entry(LogLevel.INFO, message, extra_data)
        self.logger.info(json.dumps(entry))
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        entry = self._create_log_entry(LogLevel.WARNING, message, extra_data)
        self.logger.warning(json.dumps(entry))
    
    def error(self, message: str, error: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log error message."""
        entry = self._create_log_entry(LogLevel.ERROR, message, extra_data, error)
        self.logger.error(json.dumps(entry))
    
    def critical(self, message: str, error: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        entry = self._create_log_entry(LogLevel.CRITICAL, message, extra_data, error)
        self.logger.critical(json.dumps(entry))


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        # If the message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, ValueError):
            # If not JSON, create structured format
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "correlation_id": str(uuid.uuid4())
            })


def set_log_context(context: LogContext):
    """Set log context for current async context."""
    log_context.set(context)


def get_log_context() -> Optional[LogContext]:
    """Get current log context."""
    return log_context.get()


def create_correlation_id() -> str:
    """Create new correlation ID."""
    return str(uuid.uuid4())


def with_log_context(
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    document_id: Optional[str] = None,
    service_name: Optional[str] = None,
    operation: Optional[str] = None
):
    """Decorator to set log context for a function."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            context = LogContext(
                correlation_id=correlation_id or create_correlation_id(),
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                workflow_id=workflow_id,
                document_id=document_id,
                service_name=service_name,
                operation=operation
            )
            set_log_context(context)
            try:
                return await func(*args, **kwargs)
            finally:
                log_context.set(None)
        
        def sync_wrapper(*args, **kwargs):
            context = LogContext(
                correlation_id=correlation_id or create_correlation_id(),
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                workflow_id=workflow_id,
                document_id=document_id,
                service_name=service_name,
                operation=operation
            )
            set_log_context(context)
            try:
                return func(*args, **kwargs)
            finally:
                log_context.set(None)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Global logger instances
system_logger = StructuredLogger("qme.system")
extraction_logger = StructuredLogger("qme.extraction")
validation_logger = StructuredLogger("qme.validation")
generation_logger = StructuredLogger("qme.generation")
calculation_logger = StructuredLogger("qme.calculation")
workflow_logger = StructuredLogger("qme.workflow")
api_logger = StructuredLogger("qme.api")
storage_logger = StructuredLogger("qme.storage")
monitoring_logger = StructuredLogger("qme.monitoring")