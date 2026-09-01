"""AI Provider Factory.

This module handles provider selection and configuration based on
environment variables. Keeps provider instantiation centralized.
"""
from functools import lru_cache
from typing import Literal

from ..config import Settings, get_settings
from .exceptions import AIProviderError
from .protocol import AIProvider
from .providers.openai_provider import OpenAIProvider
from .validated_ai_service import ValidatedAIService


def create_ai_provider(
    settings: Settings | None = None,
    provider_override: Literal["openai", "anthropic", "gemini"] | None = None,
) -> AIProvider:
    """Create AI provider instance based on configuration.
    
    Reads configuration from Settings and instantiates the appropriate
    provider with credentials from environment variables.
    
    Args:
        settings: Application settings (defaults to global settings)
        provider_override: Override configured provider (for testing)
        
    Returns:
        Configured AI provider instance
        
    Raises:
        AIProviderError: If provider is not configured or credentials are missing
    """
    if settings is None:
        settings = get_settings()
    
    provider_name = provider_override or settings.ai_provider
    
    if provider_name == "openai":
        if not settings.openai_api_key:
            raise AIProviderError(
                "OpenAI provider selected but OPENAI_API_KEY not configured"
            )
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=getattr(settings, "openai_model", "gpt-4"),
            timeout=getattr(settings, "ai_timeout_seconds", 45.0),
            max_retries=getattr(settings, "ai_max_retries", 2),
        )
    
    elif provider_name == "anthropic":
        if not settings.anthropic_api_key:
            raise AIProviderError(
                "Anthropic provider selected but ANTHROPIC_API_KEY not configured"
            )
        # Anthropic provider would be imported and instantiated here
        # For now, raise not implemented
        raise AIProviderError("Anthropic provider not yet implemented")
    
    elif provider_name == "gemini":
        if not settings.google_api_key:
            raise AIProviderError(
                "Gemini provider selected but GOOGLE_API_KEY not configured"
            )
        # Gemini provider would be imported and instantiated here
        # For now, raise not implemented
        raise AIProviderError("Gemini provider not yet implemented")
    
    else:
        raise AIProviderError(
            f"Unknown AI provider: {provider_name}. "
            f"Must be one of: openai, anthropic, gemini"
        )


@lru_cache
def get_ai_provider() -> AIProvider:
    """Get cached AI provider instance.
    
    This function is cached to avoid recreating the provider on every call.
    The cache is cleared when the process restarts.
    
    Returns:
        Configured AI provider instance
    """
    return create_ai_provider()


def get_ai_service() -> ValidatedAIService:
    """Get ValidatedAIService instance for FastAPI dependency injection.
    
    This function creates a ValidatedAIService wrapping the configured
    AI provider. Used as a dependency in FastAPI route handlers.
    
    Returns:
        ValidatedAIService instance with retry logic and validation
    """
    provider = get_ai_provider()
    return ValidatedAIService(provider)
