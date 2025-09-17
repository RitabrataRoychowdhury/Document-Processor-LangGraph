"""
API Provider Factory with fallback support.
Manages multiple API providers and automatic fallback when primary provider fails.
"""

import os
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from src.strategies.qa_strategy import LLMStrategy, QAStrategyFactory, RetrievalContext
from src.utils.logging_config import get_logger
from src.utils.error_handling import APIError

logger = get_logger(__name__)


class APIProviderType(Enum):
    """Supported API provider types."""
    GEMINI = "gemini"
    OPENAI = "openai"
    OPENROUTER = "openrouter"


@dataclass
class APIProviderConfig:
    """Configuration for an API provider."""
    provider_type: APIProviderType
    api_key: str
    model: Optional[str] = None
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True
    max_retries: int = 3
    timeout: int = 30
    retry_delay: float = 1.0


@dataclass
class APICallResult:
    """Result of an API call."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    provider_used: Optional[APIProviderType] = None
    attempt_count: int = 1
    total_time: float = 0.0


class APIProviderFactory:
    """Factory for managing multiple API providers with fallback support."""
    
    def __init__(self):
        """Initialize the API provider factory."""
        self.providers: Dict[APIProviderType, APIProviderConfig] = {}
        self.strategies: Dict[APIProviderType, LLMStrategy] = {}
        self.provider_stats: Dict[APIProviderType, Dict[str, Any]] = {}
        
        # Initialize from environment variables
        self._load_from_environment()
        
        logger.info(f"Initialized APIProviderFactory with {len(self.providers)} providers")
    
    def _load_from_environment(self):
        """Load API provider configurations from environment variables."""
        # Gemini configuration
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            self.add_provider(APIProviderConfig(
                provider_type=APIProviderType.GEMINI,
                api_key=gemini_key,
                priority=1,
                enabled=True
            ))
        
        # OpenRouter configuration
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            openrouter_model = os.getenv('OPENROUTER_MODEL', 'openrouter/sonoma-sky-alpha')
            self.add_provider(APIProviderConfig(
                provider_type=APIProviderType.OPENROUTER,
                api_key=openrouter_key,
                model=openrouter_model,
                priority=2,
                enabled=True
            ))
        
        # OpenAI configuration
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            self.add_provider(APIProviderConfig(
                provider_type=APIProviderType.OPENAI,
                api_key=openai_key,
                model=openai_model,
                priority=3,
                enabled=True
            ))
    
    def add_provider(self, config: APIProviderConfig):
        """Add an API provider configuration."""
        self.providers[config.provider_type] = config
        self.provider_stats[config.provider_type] = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_response_time': 0.0,
            'last_success': None,
            'last_failure': None
        }
        
        # Create the strategy instance
        try:
            self.strategies[config.provider_type] = QAStrategyFactory.create_llm_strategy(
                config.provider_type.value,
                config.api_key,
                config.model
            )
            logger.info(f"Added API provider: {config.provider_type.value}")
        except Exception as e:
            logger.error(f"Failed to create strategy for {config.provider_type.value}: {e}")
    
    def remove_provider(self, provider_type: APIProviderType):
        """Remove an API provider."""
        if provider_type in self.providers:
            del self.providers[provider_type]
            del self.strategies[provider_type]
            del self.provider_stats[provider_type]
            logger.info(f"Removed API provider: {provider_type.value}")
    
    def enable_provider(self, provider_type: APIProviderType):
        """Enable an API provider."""
        if provider_type in self.providers:
            self.providers[provider_type].enabled = True
            logger.info(f"Enabled API provider: {provider_type.value}")
    
    def disable_provider(self, provider_type: APIProviderType):
        """Disable an API provider."""
        if provider_type in self.providers:
            self.providers[provider_type].enabled = False
            logger.info(f"Disabled API provider: {provider_type.value}")
    
    def get_available_providers(self) -> List[APIProviderType]:
        """Get list of available (enabled) providers sorted by priority."""
        available = [
            provider_type for provider_type, config in self.providers.items()
            if config.enabled
        ]
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: self.providers[p].priority)
        return available
    
    def get_primary_provider(self) -> Optional[APIProviderType]:
        """Get the primary (highest priority) provider."""
        available = self.get_available_providers()
        return available[0] if available else None
    
    def get_fallback_providers(self) -> List[APIProviderType]:
        """Get fallback providers (all except primary)."""
        available = self.get_available_providers()
        return available[1:] if len(available) > 1 else []
    
    def call_with_fallback(self, 
                          operation: Callable[[LLMStrategy], Any],
                          max_total_attempts: int = None) -> APICallResult:
        """
        Execute an operation with automatic fallback between providers.
        
        Args:
            operation: Function that takes an LLMStrategy and returns a result
            max_total_attempts: Maximum total attempts across all providers
            
        Returns:
            APICallResult with success status and result or error
        """
        available_providers = self.get_available_providers()
        
        if not available_providers:
            return APICallResult(
                success=False,
                error="No API providers available",
                attempt_count=0
            )
        
        if max_total_attempts is None:
            max_total_attempts = sum(self.providers[p].max_retries for p in available_providers)
        
        total_attempts = 0
        start_time = time.time()
        
        for provider_type in available_providers:
            if total_attempts >= max_total_attempts:
                break
                
            config = self.providers[provider_type]
            strategy = self.strategies[provider_type]
            
            # Try this provider with retries
            for attempt in range(config.max_retries):
                if total_attempts >= max_total_attempts:
                    break
                
                total_attempts += 1
                
                try:
                    logger.debug(f"Attempting API call with {provider_type.value} (attempt {attempt + 1})")
                    
                    result = operation(strategy)
                    
                    # Success!
                    total_time = time.time() - start_time
                    self._update_stats(provider_type, True, total_time)
                    
                    return APICallResult(
                        success=True,
                        result=result,
                        provider_used=provider_type,
                        attempt_count=total_attempts,
                        total_time=total_time
                    )
                    
                except Exception as e:
                    logger.warning(f"API call failed with {provider_type.value}: {e}")
                    self._update_stats(provider_type, False, 0.0)
                    
                    # If this was the last attempt with this provider, continue to next provider
                    if attempt == config.max_retries - 1:
                        break
                    
                    # Wait before retry
                    if config.retry_delay > 0:
                        time.sleep(config.retry_delay)
        
        # All providers failed
        total_time = time.time() - start_time
        return APICallResult(
            success=False,
            error=f"All API providers failed after {total_attempts} attempts",
            attempt_count=total_attempts,
            total_time=total_time
        )
    
    def generate_answer_with_fallback(self, 
                                    question: str, 
                                    context: List[RetrievalContext]) -> APICallResult:
        """
        Generate an answer using the best available API provider with fallback.
        
        Args:
            question: The question to answer
            context: Retrieved context for the question
            
        Returns:
            APICallResult with the generated answer or error
        """
        def operation(strategy: LLMStrategy) -> str:
            return strategy.generate_answer(question, context)
        
        return self.call_with_fallback(operation)
    
    def test_provider(self, provider_type: APIProviderType) -> APICallResult:
        """
        Test a specific API provider with a simple query.
        
        Args:
            provider_type: The provider to test
            
        Returns:
            APICallResult indicating success or failure
        """
        if provider_type not in self.strategies:
            return APICallResult(
                success=False,
                error=f"Provider {provider_type.value} not configured"
            )
        
        strategy = self.strategies[provider_type]
        test_context = [
            RetrievalContext(
                text="This is a test context for API validation.",
                source="Test",
                relevance_score=1.0,
                metadata={}
            )
        ]
        
        def operation(strategy: LLMStrategy) -> str:
            return strategy.generate_answer("What is this test about?", test_context)
        
        start_time = time.time()
        try:
            result = operation(strategy)
            total_time = time.time() - start_time
            
            self._update_stats(provider_type, True, total_time)
            
            return APICallResult(
                success=True,
                result=result,
                provider_used=provider_type,
                total_time=total_time
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            self._update_stats(provider_type, False, total_time)
            
            return APICallResult(
                success=False,
                error=str(e),
                provider_used=provider_type,
                total_time=total_time
            )
    
    def test_all_providers(self) -> Dict[APIProviderType, APICallResult]:
        """Test all configured providers."""
        results = {}
        
        for provider_type in self.providers.keys():
            if self.providers[provider_type].enabled:
                results[provider_type] = self.test_provider(provider_type)
        
        return results
    
    def get_provider_stats(self) -> Dict[APIProviderType, Dict[str, Any]]:
        """Get statistics for all providers."""
        return self.provider_stats.copy()
    
    def get_provider_health(self) -> Dict[APIProviderType, str]:
        """Get health status for all providers."""
        health = {}
        
        for provider_type, stats in self.provider_stats.items():
            if not self.providers[provider_type].enabled:
                health[provider_type] = "disabled"
            elif stats['total_calls'] == 0:
                health[provider_type] = "untested"
            elif stats['failed_calls'] == 0:
                health[provider_type] = "healthy"
            elif stats['successful_calls'] / stats['total_calls'] > 0.8:
                health[provider_type] = "good"
            elif stats['successful_calls'] / stats['total_calls'] > 0.5:
                health[provider_type] = "degraded"
            else:
                health[provider_type] = "unhealthy"
        
        return health
    
    def _update_stats(self, provider_type: APIProviderType, success: bool, response_time: float):
        """Update statistics for a provider."""
        stats = self.provider_stats[provider_type]
        
        stats['total_calls'] += 1
        
        if success:
            stats['successful_calls'] += 1
            stats['last_success'] = time.time()
            
            # Update average response time
            if stats['avg_response_time'] == 0:
                stats['avg_response_time'] = response_time
            else:
                # Exponential moving average
                stats['avg_response_time'] = (stats['avg_response_time'] * 0.8) + (response_time * 0.2)
        else:
            stats['failed_calls'] += 1
            stats['last_failure'] = time.time()


# Global factory instance
_api_factory = None


def get_api_factory() -> APIProviderFactory:
    """Get the global API provider factory instance."""
    global _api_factory
    if _api_factory is None:
        _api_factory = APIProviderFactory()
    return _api_factory


def reset_api_factory():
    """Reset the global API provider factory (mainly for testing)."""
    global _api_factory
    _api_factory = None