"""AI Provider Protocol Interface.

This module defines the provider-neutral interface for AI operations.
All AI providers must implement this protocol to work with RootLearn.
"""
from typing import AsyncIterator, Protocol, Type, TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class AIProvider(Protocol):
    """Protocol defining the interface all AI providers must implement.
    
    This protocol ensures provider-neutral AI operations throughout the
    application. Providers can be switched without changing service code.
    """

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> T:
        """Generate structured output validated against a Pydantic schema.
        
        Args:
            system_prompt: System-level instructions for the AI
            user_prompt: User-provided prompt or context
            schema: Pydantic model class defining expected output structure
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Validated instance of the schema type
            
        Raises:
            AIProviderError: On provider-specific failures
            ValidationError: When output doesn't match schema after retries
        """
        ...

    async def stream_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream text response token by token.
        
        Args:
            system_prompt: System-level instructions for the AI
            user_prompt: User-provided prompt or context
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Yields:
            Text chunks as they become available
            
        Raises:
            AIProviderError: On provider-specific failures
        """
        ...
