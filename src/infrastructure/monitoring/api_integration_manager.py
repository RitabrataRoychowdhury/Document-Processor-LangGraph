"""
API Integration Manager with Circuit Breaker and Retry Logic.

This module provides robust API integration capabilities with circuit breaker pattern,
exponential backoff retry logic, and comprehensive error handling for external API calls.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json

from src.core.exceptions import (
    APIError, ExternalAPITimeoutError, ExternalAPIRateLimitError,
    ConfigurationError
)
from src.infrastructure.monitoring.structured_logger import api_logger
from src.infrastructure.monitoring.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, circuit_breaker_registry
)
from src.infrastructure.monitoring.retry_handler import (
    RetryHandler, RetryConfig, BackoffStrategy
)


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class APIEndpointConfig:
    """Configuration for API endpoint."""
    name: str
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL_JITTER
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    headers: Dict[str, str] = field(default_factory=dict)
    auth_config: Optional[Dict[str, Any]] = None


@dataclass
class APIRequest:
    """API request configuration."""
    method: HTTPMethod
    endpoint: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None
    data: Optional[Union[str, bytes]] = None
    timeout: Optional[int] = None


@dataclass
class APIResponse:
    """API response wrapper."""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]] = None
    response_time: float = 0.0
    success: bool = False
    error_message: Optional[str] = None


class APIIntegrationManager:
    """
    API Integration Manager with comprehensive error handling and resilience patterns.
    
    Features:
    - Circuit breaker pattern for fault tolerance
    - Exponential backoff retry logic
    - Request/response logging and monitoring
    - Rate limiting and timeout handling
    - Authentication management
    - Connection pooling and session management
    """
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpointConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handlers: Dict[str, RetryHandler] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        api_logger.info("Initialized APIIntegrationManager")
    
    def register_endpoint(self, config: APIEndpointConfig):
        """Register API endpoint configuration."""
        self.endpoints[config.name] = config
        
        # Create circuit breaker
        cb_config = config.circuit_breaker_config or CircuitBreakerConfig()
        self.circuit_breakers[config.name] = CircuitBreaker(config.name, cb_config)
        
        # Create retry handler
        retry_config = RetryConfig(
            max_attempts=config.max_retries,
            backoff_strategy=config.retry_backoff,
            retryable_exceptions=[
                APIError,
                ExternalAPITimeoutError,
                aiohttp.ClientError,
                asyncio.TimeoutError
            ]
        )
        self.retry_handlers[config.name] = RetryHandler(retry_config)
        
        api_logger.info(
            f"Registered API endpoint: {config.name}",
            extra_data={
                "base_url": config.base_url,
                "timeout": config.timeout,
                "max_retries": config.max_retries
            }
        )
    
    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'QME-System/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            )
    
    async def make_request(
        self,
        endpoint_name: str,
        request: APIRequest,
        **kwargs
    ) -> APIResponse:
        """Make API request with circuit breaker and retry logic."""
        if endpoint_name not in self.endpoints:
            raise ConfigurationError(
                f"API endpoint '{endpoint_name}' not registered",
                context={"endpoint_name": endpoint_name}
            )
        
        config = self.endpoints[endpoint_name]
        circuit_breaker = self.circuit_breakers[endpoint_name]
        retry_handler = self.retry_handlers[endpoint_name]
        
        api_logger.debug(
            f"Making API request to {endpoint_name}",
            extra_data={
                "endpoint": request.endpoint,
                "method": request.method.value,
                "has_json_data": request.json_data is not None
            }
        )
        
        # Execute request with circuit breaker and retry
        try:
            response = await retry_handler.execute_with_retry(
                self._execute_request,
                config,
                request,
                circuit_breaker,
                **kwargs
            )
            
            api_logger.info(
                f"API request successful: {endpoint_name}",
                extra_data={
                    "status_code": response.status_code,
                    "response_time": response.response_time,
                    "endpoint": request.endpoint
                }
            )
            
            return response
            
        except Exception as e:
            api_logger.error(
                f"API request failed: {endpoint_name}",
                error=e,
                extra_data={
                    "endpoint": request.endpoint,
                    "method": request.method.value
                }
            )
            raise
    
    async def _execute_request(
        self,
        config: APIEndpointConfig,
        request: APIRequest,
        circuit_breaker: CircuitBreaker,
        **kwargs
    ) -> APIResponse:
        """Execute HTTP request with circuit breaker protection."""
        start_time = time.time()
        
        # Use circuit breaker for the actual HTTP call
        response = await circuit_breaker.call(
            self._make_http_request,
            config,
            request,
            **kwargs
        )
        
        response.response_time = time.time() - start_time
        return response
    
    async def _make_http_request(
        self,
        config: APIEndpointConfig,
        request: APIRequest,
        **kwargs
    ) -> APIResponse:
        """Make actual HTTP request."""
        await self._ensure_session()
        
        # Build URL
        url = f"{config.base_url.rstrip('/')}/{request.endpoint.lstrip('/')}"
        
        # Merge headers
        headers = config.headers.copy()
        if request.headers:
            headers.update(request.headers)
        
        # Add authentication if configured
        if config.auth_config:
            headers.update(self._build_auth_headers(config.auth_config))
        
        # Set timeout
        timeout = request.timeout or config.timeout
        
        try:
            async with self.session.request(
                method=request.method.value,
                url=url,
                headers=headers,
                params=request.params,
                json=request.json_data,
                data=request.data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                # Read response content
                content = await response.read()
                text = content.decode('utf-8', errors='ignore')
                
                # Try to parse JSON
                json_data = None
                if response.content_type == 'application/json':
                    try:
                        json_data = json.loads(text)
                    except json.JSONDecodeError:
                        pass
                
                # Check for HTTP errors
                success = 200 <= response.status < 300
                error_message = None
                
                if not success:
                    error_message = f"HTTP {response.status}: {response.reason}"
                    
                    # Handle specific error cases
                    if response.status == 429:
                        raise ExternalAPIRateLimitError(
                            f"Rate limit exceeded for {config.name}",
                            context={
                                "endpoint": url,
                                "status_code": response.status,
                                "retry_after": response.headers.get('Retry-After')
                            }
                        )
                    elif response.status >= 500:
                        raise APIError(
                            f"Server error from {config.name}: {error_message}",
                            context={
                                "endpoint": url,
                                "status_code": response.status
                            }
                        )
                
                return APIResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    content=content,
                    text=text,
                    json_data=json_data,
                    success=success,
                    error_message=error_message
                )
                
        except asyncio.TimeoutError:
            raise ExternalAPITimeoutError(
                f"Request to {config.name} timed out after {timeout}s",
                context={"endpoint": url, "timeout": timeout}
            )
        except aiohttp.ClientError as e:
            raise APIError(
                f"Client error for {config.name}: {str(e)}",
                context={"endpoint": url},
                cause=e
            )
    
    def _build_auth_headers(self, auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Build authentication headers."""
        headers = {}
        
        auth_type = auth_config.get('type', '').lower()
        
        if auth_type == 'bearer':
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f"Bearer {token}"
        elif auth_type == 'api_key':
            key = auth_config.get('key')
            header_name = auth_config.get('header', 'X-API-Key')
            if key:
                headers[header_name] = key
        elif auth_type == 'basic':
            username = auth_config.get('username')
            password = auth_config.get('password')
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers['Authorization'] = f"Basic {credentials}"
        
        return headers
    
    async def health_check(self, endpoint_name: str) -> Dict[str, Any]:
        """Perform health check for API endpoint."""
        if endpoint_name not in self.endpoints:
            return {
                "status": "error",
                "message": f"Endpoint '{endpoint_name}' not registered"
            }
        
        config = self.endpoints[endpoint_name]
        circuit_breaker = self.circuit_breakers[endpoint_name]
        
        try:
            # Simple health check request
            health_request = APIRequest(
                method=HTTPMethod.GET,
                endpoint="",  # Base URL health check
                timeout=5
            )
            
            start_time = time.time()
            response = await self._make_http_request(config, health_request)
            response_time = time.time() - start_time
            
            return {
                "status": "healthy" if response.success else "degraded",
                "endpoint": config.base_url,
                "response_time": response_time,
                "status_code": response.status_code,
                "circuit_breaker": circuit_breaker.get_stats()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": config.base_url,
                "error": str(e),
                "circuit_breaker": circuit_breaker.get_stats()
            }
    
    def get_endpoint_stats(self, endpoint_name: str) -> Dict[str, Any]:
        """Get statistics for API endpoint."""
        if endpoint_name not in self.endpoints:
            return {"error": f"Endpoint '{endpoint_name}' not registered"}
        
        circuit_breaker = self.circuit_breakers[endpoint_name]
        return circuit_breaker.get_stats()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered endpoints."""
        return {
            name: self.get_endpoint_stats(name)
            for name in self.endpoints.keys()
        }
    
    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        
        api_logger.info("Closed APIIntegrationManager")


# Global API integration manager instance
api_integration_manager = APIIntegrationManager()


# Convenience functions for common API operations
async def register_openrouter_endpoint(api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
    """Register OpenRouter API endpoint."""
    config = APIEndpointConfig(
        name="openrouter",
        base_url=base_url,
        timeout=60,
        max_retries=3,
        headers={"Content-Type": "application/json"},
        auth_config={
            "type": "bearer",
            "token": api_key
        },
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=120,
            timeout=60
        )
    )
    
    api_integration_manager.register_endpoint(config)


async def make_openrouter_request(
    endpoint: str,
    json_data: Dict[str, Any],
    **kwargs
) -> APIResponse:
    """Make request to OpenRouter API."""
    request = APIRequest(
        method=HTTPMethod.POST,
        endpoint=endpoint,
        json_data=json_data
    )
    
    return await api_integration_manager.make_request("openrouter", request, **kwargs)