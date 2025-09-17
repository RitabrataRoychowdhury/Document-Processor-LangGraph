"""
Circuit breaker pattern implementation for external API calls.

This module implements the circuit breaker pattern to prevent cascade failures
by temporarily disabling failing services.
"""

import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from src.core.exceptions import APIError, ExternalAPITimeoutError


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: int = 30  # Request timeout in seconds


class CircuitBreaker:
    """Circuit breaker implementation for external service calls."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "circuit_opens": 0
        }
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        self.stats["total_calls"] += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise APIError(
                    f"Circuit breaker {self.name} is OPEN",
                    error_code="CIRCUIT_BREAKER_OPEN",
                    context={"circuit_name": self.name, "state": self.state.value}
                )
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            error = ExternalAPITimeoutError(
                f"Call to {self.name} timed out after {self.config.timeout}s",
                context={"circuit_name": self.name, "timeout": self.config.timeout}
            )
            self._on_failure(error)
            raise error
            
        except Exception as e:
            api_error = APIError(
                f"Call to {self.name} failed: {str(e)}",
                context={"circuit_name": self.name, "original_error": str(e)},
                cause=e
            )
            self._on_failure(api_error)
            raise api_error
    
    def _on_success(self):
        """Handle successful call."""
        self.stats["successful_calls"] += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
    
    def _on_failure(self, error: Exception):
        """Handle failed call."""
        self.stats["failed_calls"] += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.stats["circuit_opens"] += 1
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "stats": self.stats.copy(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Manually reset circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()