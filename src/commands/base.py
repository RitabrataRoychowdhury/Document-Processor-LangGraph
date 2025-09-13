"""Base command interface and result classes for the command pattern implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
import functools
import time
import logging

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status enumeration for command execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class CommandResult:
    """Standardized result class for command execution."""
    status: CommandStatus
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def success_result(cls, message: str, data: Dict[str, Any] = None) -> 'CommandResult':
        """Create a successful command result."""
        return cls(
            status=CommandStatus.COMPLETED,
            success=True,
            message=message,
            data=data or {},
            completed_at=datetime.now()
        )
    
    @classmethod
    def failure_result(cls, message: str, error: Exception = None, retry_count: int = 0) -> 'CommandResult':
        """Create a failed command result."""
        return cls(
            status=CommandStatus.FAILED,
            success=False,
            message=message,
            error=error,
            retry_count=retry_count,
            completed_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'status': self.status.value,
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error': str(self.error) if self.error else None,
            'execution_time': self.execution_time,
            'retry_count': self.retry_count,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class RetryableException(Exception):
    """Exception that indicates an operation can be retried."""
    pass


class NonRetryableException(Exception):
    """Exception that indicates an operation should not be retried."""
    pass


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0, 
                    retryable_exceptions: tuple = (RetryableException,)):
    """
    Decorator for implementing retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        retryable_exceptions: Tuple of exception types that should trigger retries
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    # Log attempt
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt + 1}/{max_attempts} for {func.__name__}")
                    
                    result = func(*args, **kwargs)
                    
                    # If we get here, the function succeeded
                    if attempt > 0:
                        logger.info(f"Function {func.__name__} succeeded after {attempt + 1} attempts")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable exception
                    if not isinstance(e, retryable_exceptions):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise e
                    
                    # If this is the last attempt, don't wait
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                        break
                    
                    # Calculate sleep time with exponential backoff
                    sleep_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {sleep_time}s: {e}")
                    time.sleep(sleep_time)
            
            # If we get here, all attempts failed
            raise last_exception
            
        return wrapper
    return decorator


class Command(ABC):
    """Abstract base class for all commands in the system."""
    
    def __init__(self, command_id: Optional[str] = None):
        self.command_id = command_id or self._generate_command_id()
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.retry_count = 0
    
    def _generate_command_id(self) -> str:
        """Generate a unique command ID."""
        import uuid
        return f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
    
    @abstractmethod
    def execute(self) -> CommandResult:
        """
        Execute the command and return a result.
        
        Returns:
            CommandResult: The result of command execution
        """
        pass
    
    @abstractmethod
    def can_retry(self) -> bool:
        """
        Check if this command can be retried on failure.
        
        Returns:
            bool: True if the command can be retried, False otherwise
        """
        pass
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get information about this command."""
        return {
            'command_id': self.command_id,
            'command_type': self.__class__.__name__,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count
        }
    
    def execute_with_retry(self, max_attempts: int = 3, backoff_factor: float = 2.0) -> CommandResult:
        """
        Execute the command with retry logic.
        
        Args:
            max_attempts: Maximum number of attempts
            backoff_factor: Exponential backoff factor
            
        Returns:
            CommandResult: The final result after all attempts
        """
        if not self.can_retry():
            max_attempts = 1
        
        last_result = None
        
        for attempt in range(max_attempts):
            try:
                self.started_at = datetime.now()
                self.retry_count = attempt
                
                logger.info(f"Executing command {self.command_id} (attempt {attempt + 1}/{max_attempts})")
                
                result = self.execute()
                result.retry_count = attempt
                result.started_at = self.started_at
                result.completed_at = datetime.now()
                result.execution_time = (result.completed_at - self.started_at).total_seconds()
                
                self.completed_at = result.completed_at
                
                if result.success:
                    if attempt > 0:
                        logger.info(f"Command {self.command_id} succeeded after {attempt + 1} attempts")
                    return result
                else:
                    last_result = result
                    if attempt == max_attempts - 1:
                        logger.error(f"Command {self.command_id} failed after {max_attempts} attempts")
                        break
                    
                    # Wait before retry
                    sleep_time = backoff_factor ** attempt
                    logger.warning(f"Command {self.command_id} failed (attempt {attempt + 1}), retrying in {sleep_time}s: {result.message}")
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Exception in command {self.command_id} (attempt {attempt + 1}): {e}")
                last_result = CommandResult.failure_result(
                    message=f"Command execution failed: {str(e)}",
                    error=e,
                    retry_count=attempt
                )
                
                if attempt == max_attempts - 1:
                    break
                
                # Wait before retry
                sleep_time = backoff_factor ** attempt
                logger.warning(f"Command {self.command_id} exception, retrying in {sleep_time}s")
                time.sleep(sleep_time)
        
        # Return the last result if all attempts failed
        return last_result or CommandResult.failure_result("Command execution failed with no result")