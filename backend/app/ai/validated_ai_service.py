"""Validated AI Service with retry logic and logging.

This module wraps the AI provider with validation, retry logic, and
comprehensive logging. All AI calls should go through this service
to ensure consistency and auditability.
"""
import time
import uuid
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import (
    AIProviderError,
    AIProviderValidationError,
    AIProviderTimeoutError,
    AIProviderRateLimitError,
)
from .logging_service import AIRunLogger
from .protocol import AIProvider


T = TypeVar("T", bound=BaseModel)


class ValidatedAIService:
    """AI service with validation, retry logic, and logging.
    
    This service wraps an AI provider and ensures:
    - All outputs are validated against Pydantic schemas
    - Failed validations trigger retries (up to max_retries)
    - All executions are logged to ai_runs table
    - Safe fallbacks after retry exhaustion
    """

    def __init__(
        self,
        provider: AIProvider,
        logger: AIRunLogger,
        max_retries: int = 2,
    ):
        """Initialize the validated AI service.
        
        Args:
            provider: AI provider implementation
            logger: AI run logger for database logging
            max_retries: Maximum number of retries on validation failures
        """
        self.provider = provider
        self.logger = logger
        self.max_retries = max_retries

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        purpose: str,
        prompt_version: str,
        temperature: float = 0.7,
        session_id: uuid.UUID | None = None,
    ) -> T:
        """Generate and validate structured output with retry logic.
        
        Calls the AI provider, validates output against schema, retries on
        validation failures, and logs all attempts.
        
        Args:
            system_prompt: System-level instructions for the AI
            user_prompt: User-provided prompt or context
            schema: Pydantic model class defining expected output structure
            purpose: Description of why this AI call is being made
            prompt_version: Version identifier for the prompt template
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            session_id: Associated learning session ID (if applicable)
            
        Returns:
            Validated instance of the schema type
            
        Raises:
            AIProviderValidationError: After max retries with validation failures
            AIProviderError: On other provider failures
        """
        provider_name = type(self.provider).__name__.replace("Provider", "").lower()
        model = getattr(self.provider, "model", "unknown")
        
        input_data = {
            "system_prompt": system_prompt[:500],  # Truncate for storage
            "user_prompt": user_prompt[:500],
            "schema": schema.__name__,
            "temperature": temperature,
        }
        
        last_error: Exception | None = None
        
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            
            try:
                # Call the AI provider
                result = await self.provider.generate_structured(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    temperature=temperature,
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Validation succeeded (provider already validates)
                output_data = result.model_dump()
                
                # Log successful execution
                await self.logger.log_success(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt_version,
                    input_data=input_data,
                    output_data=output_data,
                    latency_ms=latency_ms,
                    session_id=session_id,
                )
                
                return result
                
            except AIProviderValidationError as e:
                # Validation failed - retry if we have attempts left
                latency_ms = int((time.time() - start_time) * 1000)
                last_error = e
                
                if attempt < self.max_retries:
                    # Log the failed attempt but continue retrying
                    await self.logger.log_failure(
                        purpose=f"{purpose} (attempt {attempt + 1})",
                        provider=provider_name,
                        model=model,
                        prompt_version=prompt_version,
                        input_data=input_data,
                        latency_ms=latency_ms,
                        error_code="validation_error",
                        session_id=session_id,
                    )
                    continue
                else:
                    # Max retries exhausted - log final failure
                    await self.logger.log_failure(
                        purpose=f"{purpose} (final attempt)",
                        provider=provider_name,
                        model=model,
                        prompt_version=prompt_version,
                        input_data=input_data,
                        latency_ms=latency_ms,
                        error_code="validation_error_exhausted",
                        session_id=session_id,
                    )
                    raise AIProviderValidationError(
                        f"Validation failed after {self.max_retries + 1} attempts: {e}"
                    ) from e
                    
            except (AIProviderTimeoutError, AIProviderRateLimitError) as e:
                # Don't retry on timeout or rate limit errors
                latency_ms = int((time.time() - start_time) * 1000)
                
                error_code = "timeout" if isinstance(e, AIProviderTimeoutError) else "rate_limit"
                
                await self.logger.log_failure(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt_version,
                    input_data=input_data,
                    latency_ms=latency_ms,
                    error_code=error_code,
                    session_id=session_id,
                )
                raise
                
            except AIProviderError as e:
                # General provider error - don't retry
                latency_ms = int((time.time() - start_time) * 1000)
                
                await self.logger.log_failure(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt_version,
                    input_data=input_data,
                    latency_ms=latency_ms,
                    error_code="provider_error",
                    session_id=session_id,
                )
                raise
                
            except Exception as e:
                # Unexpected error - don't retry
                latency_ms = int((time.time() - start_time) * 1000)
                
                await self.logger.log_failure(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt_version,
                    input_data=input_data,
                    latency_ms=latency_ms,
                    error_code="unexpected_error",
                    session_id=session_id,
                )
                raise AIProviderError(f"Unexpected error: {e}") from e
        
        # Should not reach here due to raises in loop, but just in case
        if last_error:
            raise AIProviderValidationError(
                f"Validation failed after {self.max_retries + 1} attempts"
            ) from last_error
        raise AIProviderValidationError("Max retries exceeded")

    async def generate_structured_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        fallback: T,
        purpose: str,
        prompt_version: str,
        temperature: float = 0.7,
        session_id: uuid.UUID | None = None,
    ) -> T:
        """Generate structured output with a safe fallback value.
        
        If all retries are exhausted, returns the fallback value instead
        of raising an exception. Use this for non-critical AI calls where
        a safe default is acceptable.
        
        Args:
            system_prompt: System-level instructions for the AI
            user_prompt: User-provided prompt or context
            schema: Pydantic model class defining expected output structure
            fallback: Safe fallback value to return on failure
            purpose: Description of why this AI call is being made
            prompt_version: Version identifier for the prompt template
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            session_id: Associated learning session ID (if applicable)
            
        Returns:
            Validated instance of schema type, or fallback on failure
        """
        try:
            return await self.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                purpose=purpose,
                prompt_version=prompt_version,
                temperature=temperature,
                session_id=session_id,
            )
        except (AIProviderError, AIProviderValidationError):
            # Log that we're using fallback
            # (The error was already logged by generate_structured)
            return fallback


def create_validated_ai_service(
    provider: AIProvider,
    db: AsyncSession,
    max_retries: int = 2,
) -> ValidatedAIService:
    """Factory function to create a validated AI service.
    
    Args:
        provider: AI provider implementation
        db: Database session for logging
        max_retries: Maximum number of retries on validation failures
        
    Returns:
        Configured ValidatedAIService instance
    """
    logger = AIRunLogger(db)
    return ValidatedAIService(
        provider=provider,
        logger=logger,
        max_retries=max_retries,
    )

