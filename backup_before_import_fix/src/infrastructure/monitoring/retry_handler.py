"""
Retry mechanism with exponential backoff and fallback strategies.

This module provides retry functionality for handling transient failures
with configurable backoff strategies and fallback mechanisms.
"""

import asyncio
import random
import time
from typing import Callable, Any, Optional, List, Type, Union
from dataclasses import dataclass
from enum import Enum

from src.core.exceptions import QMESystemError, APIError, ExternalAPITimeoutError
from src.infrastructure.monitoring.structured_logger import api_logger


class BackoffStrategy(Enum):
    """Backoff strategies for retry attempts."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    jitter_range: float = 0.1  # Jitter range (0.0 to 1.0)
    retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                APIError,
                ExternalAPITimeoutError,
                ConnectionError,
                TimeoutError
            ]


class RetryHandler:
    """Handles retry logic with various backoff strategies."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if self.config.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * attempt
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (2 ** (attempt - 1))
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL_JITTER:
            base_delay = self.config.base_delay * (2 ** (attempt - 1))
            jitter = base_delay * self.config.jitter_range * random.random()
            delay = base_delay + jitter
        else:
            delay = self.config.base_delay
        
        return min(delay, self.config.max_delay)
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable."""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        fallback_func: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                api_logger.debug(
                    f"Executing function with retry, attempt {attempt}/{self.config.max_attempts}",
                    extra_data={
                        "function": func.__name__,
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts
                    }
                )
                
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                if attempt > 1:
                    api_logger.info(
                        f"Function succeeded on attempt {attempt}",
                        extra_data={
                            "function": func.__name__,
                            "attempt": attempt,
                            "success_after_retry": True
                        }
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                api_logger.warning(
                    f"Function failed on attempt {attempt}: {str(e)}",
                    error=e,
                    extra_data={
                        "function": func.__name__,
                        "attempt": attempt,
                        "max_attempts": self.config.max_attempts,
                        "is_retryable": self._is_retryable(e)
                    }
                )
                
                # Check if we should retry
                if attempt >= self.config.max_attempts or not self._is_retryable(e):
                    break
                
                # Calculate and apply delay
                delay = self._calculate_delay(attempt)
                api_logger.debug(
                    f"Retrying after {delay:.2f} seconds",
                    extra_data={
                        "function": func.__name__,
                        "attempt": attempt,
                        "delay": delay,
                        "backoff_strategy": self.config.backoff_strategy.value
                    }
                )
                
                await asyncio.sleep(delay)
        
        # All attempts failed, try fallback if available
        if fallback_func:
            try:
                api_logger.info(
                    f"Executing fallback function after {self.config.max_attempts} failed attempts",
                    extra_data={
                        "original_function": func.__name__,
                        "fallback_function": fallback_func.__name__,
                        "last_error": str(last_exception)
                    }
                )
                
                if asyncio.iscoroutinefunction(fallback_func):
                    return await fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
                    
            except Exception as fallback_error:
                api_logger.error(
                    f"Fallback function also failed",
                    error=fallback_error,
                    extra_data={
                        "original_function": func.__name__,
                        "fallback_function": fallback_func.__name__,
                        "original_error": str(last_exception),
                        "fallback_error": str(fallback_error)
                    }
                )
                raise fallback_error
        
        # No fallback or fallback failed, raise the last exception
        api_logger.error(
            f"All retry attempts failed for function {func.__name__}",
            error=last_exception,
            extra_data={
                "function": func.__name__,
                "total_attempts": self.config.max_attempts,
                "final_error": str(last_exception)
            }
        )
        
        raise last_exception


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    fallback_func: Optional[Callable] = None
):
    """Decorator for adding retry logic to functions."""
    def decorator(func):
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            backoff_strategy=backoff_strategy,
            retryable_exceptions=retryable_exceptions
        )
        retry_handler = RetryHandler(config)
        
        async def async_wrapper(*args, **kwargs):
            return await retry_handler.execute_with_retry(
                func, *args, fallback_func=fallback_func, **kwargs
            )
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run in event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(
                retry_handler.execute_with_retry(
                    func, *args, fallback_func=fallback_func, **kwargs
                )
            )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global retry handler with default configuration
default_retry_handler = RetryHandler()