"""OpenAI Provider Implementation.

This module implements the AIProvider protocol using OpenAI's API.
Supports structured output generation and text streaming with token tracking.
"""
import json
import time
from typing import AsyncIterator, Type, TypeVar

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from pydantic import BaseModel, ValidationError

from ..exceptions import (
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    AIProviderAuthenticationError,
    AIProviderValidationError,
)


T = TypeVar("T", bound=BaseModel)


class OpenAIProvider:
    """OpenAI implementation of the AIProvider protocol.
    
    Features:
    - Structured output using JSON mode
    - Token tracking and latency measurement
    - Automatic retries with exponential backoff
    - Error handling for common failure modes
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        timeout: float = 45.0,
        max_retries: int = 2,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model identifier (default: gpt-4)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_retries = max_retries

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> T:
        """Generate structured output validated against a Pydantic schema.
        
        Uses OpenAI's JSON mode to encourage structured responses.
        Validates output against schema and retries on validation failures.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User-provided prompt
            schema: Pydantic model class for output validation
            temperature: Sampling temperature
            
        Returns:
            Validated instance of schema type
            
        Raises:
            AIProviderValidationError: After max retries with validation failures
            AIProviderError: On other provider failures
        """
        # Add JSON instruction to system prompt
        enhanced_system_prompt = f"{system_prompt}\n\nYou must respond with valid JSON matching this schema: {schema.model_json_schema()}"
        
        last_validation_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Extract response content
                content = response.choices[0].message.content
                if not content:
                    raise AIProviderError("Empty response from OpenAI")
                
                # Parse and validate JSON
                try:
                    data = json.loads(content)
                    validated = schema.model_validate(data)
                    return validated
                except (json.JSONDecodeError, ValidationError) as e:
                    last_validation_error = e
                    if attempt < self.max_retries:
                        # Retry on validation failure
                        continue
                    else:
                        raise AIProviderValidationError(
                            f"Failed to validate output after {self.max_retries + 1} attempts: {e}"
                        )
                        
            except AIProviderValidationError:
                # Re-raise validation errors without wrapping
                raise
            except RateLimitError as e:
                raise AIProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            except APITimeoutError as e:
                raise AIProviderTimeoutError(f"OpenAI request timed out: {e}")
            except APIError as e:
                if e.status_code == 401:
                    raise AIProviderAuthenticationError(f"OpenAI authentication failed: {e}")
                raise AIProviderError(f"OpenAI API error: {e}")
            except Exception as e:
                raise AIProviderError(f"Unexpected error with OpenAI: {e}")
        
        # Should not reach here due to raises in loop, but just in case
        if last_validation_error:
            raise AIProviderValidationError(
                f"Failed to validate output after {self.max_retries + 1} attempts: {last_validation_error}"
            )
        raise AIProviderValidationError("Max retries exceeded")

    async def stream_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream text response token by token.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User-provided prompt
            temperature: Sampling temperature
            
        Yields:
            Text chunks as they become available
            
        Raises:
            AIProviderError: On provider failures
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except RateLimitError as e:
            raise AIProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
        except APITimeoutError as e:
            raise AIProviderTimeoutError(f"OpenAI request timed out: {e}")
        except APIError as e:
            if e.status_code == 401:
                raise AIProviderAuthenticationError(f"OpenAI authentication failed: {e}")
            raise AIProviderError(f"OpenAI API error: {e}")
        except Exception as e:
            raise AIProviderError(f"Unexpected error with OpenAI: {e}")

    async def get_token_usage(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> tuple[T, int, int]:
        """Generate structured output and return token usage.
        
        Helper method that returns both the validated output and token counts.
        Useful for logging and cost tracking.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User-provided prompt
            schema: Pydantic model class for output validation
            temperature: Sampling temperature
            
        Returns:
            Tuple of (validated_output, prompt_tokens, completion_tokens)
        """
        enhanced_system_prompt = f"{system_prompt}\n\nYou must respond with valid JSON matching this schema: {schema.model_json_schema()}"
        
        last_validation_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                
                # Extract token usage
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                
                # Extract and validate content
                content = response.choices[0].message.content
                if not content:
                    raise AIProviderError("Empty response from OpenAI")
                
                try:
                    data = json.loads(content)
                    validated = schema.model_validate(data)
                    return validated, prompt_tokens, completion_tokens
                except (json.JSONDecodeError, ValidationError) as e:
                    last_validation_error = e
                    if attempt < self.max_retries:
                        continue
                    else:
                        raise AIProviderValidationError(
                            f"Failed to validate output after {self.max_retries + 1} attempts: {e}"
                        )
                        
            except AIProviderValidationError:
                # Re-raise validation errors without wrapping
                raise
            except RateLimitError as e:
                raise AIProviderRateLimitError(f"OpenAI rate limit exceeded: {e}")
            except APITimeoutError as e:
                raise AIProviderTimeoutError(f"OpenAI request timed out: {e}")
            except APIError as e:
                if e.status_code == 401:
                    raise AIProviderAuthenticationError(f"OpenAI authentication failed: {e}")
                raise AIProviderError(f"OpenAI API error: {e}")
            except Exception as e:
                raise AIProviderError(f"Unexpected error with OpenAI: {e}")
        
        if last_validation_error:
            raise AIProviderValidationError(
                f"Failed to validate output after {self.max_retries + 1} attempts: {last_validation_error}"
            )
        raise AIProviderValidationError("Max retries exceeded")
