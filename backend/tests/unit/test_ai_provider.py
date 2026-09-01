"""Unit tests for AI provider abstraction layer.

Tests provider switching, retry logic, timeout handling, and error scenarios.
Requirements: 12.2, 12.4, 13.2
"""
import json
from typing import Type
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from openai import APIError, RateLimitError, APITimeoutError
from pydantic import BaseModel, Field

from app.ai import (
    OpenAIProvider,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    AIProviderAuthenticationError,
    AIProviderValidationError,
    create_ai_provider,
)
from app.config import Settings


# Test schema
class ConceptResponse(BaseModel):
    """Test schema for structured output."""
    
    message: str = Field(..., description="Test message")
    score: float = Field(..., ge=0.0, le=1.0, description="Test score")


class TestProviderSwitching:
    """Test provider configuration and selection.
    
    Requirements: 12.2, 12.4
    """

    def test_create_openai_provider_with_key(self):
        """Test creating OpenAI provider when API key is configured."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="openai",
            openai_api_key="sk-test-key",
        )
        
        provider = create_ai_provider(settings)
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4"

    def test_create_openai_provider_without_key_raises_error(self):
        """Test that missing API key raises appropriate error."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="openai",
            openai_api_key=None,
        )
        
        with pytest.raises(AIProviderError, match="OPENAI_API_KEY not configured"):
            create_ai_provider(settings)

    def test_anthropic_provider_not_implemented(self):
        """Test that Anthropic provider raises not implemented error."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="anthropic",
            anthropic_api_key="test-key",
        )
        
        with pytest.raises(AIProviderError, match="not yet implemented"):
            create_ai_provider(settings)

    def test_gemini_provider_not_implemented(self):
        """Test that Gemini provider raises not implemented error."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="gemini",
            google_api_key="test-key",
        )
        
        with pytest.raises(AIProviderError, match="not yet implemented"):
            create_ai_provider(settings)

    def test_unknown_provider_raises_error(self):
        """Test that unknown provider name raises error."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="openai",  # Valid, but we'll override
            openai_api_key="sk-test",
        )
        
        with pytest.raises(AIProviderError, match="Unknown AI provider"):
            create_ai_provider(settings, provider_override="unknown")  # type: ignore

    def test_provider_override(self):
        """Test provider override parameter."""
        settings = Settings(
            database_url="postgresql://test",
            ai_provider="anthropic",  # Configured for anthropic
            openai_api_key="sk-test",  # But has OpenAI key
        )
        
        # Override to use OpenAI despite config
        provider = create_ai_provider(settings, provider_override="openai")
        
        assert isinstance(provider, OpenAIProvider)


class TestOpenAIProviderRetry:
    """Test OpenAI provider retry logic on failures.
    
    Requirements: 13.2
    """

    @pytest.mark.asyncio
    async def test_retry_on_validation_failure(self):
        """Test that validation failures trigger retries up to max_retries."""
        provider = OpenAIProvider(
            api_key="sk-test",
            max_retries=2,
        )
        
        # Mock responses: first two invalid, third valid
        mock_responses = [
            Mock(
                choices=[Mock(message=Mock(content='{"invalid": "json"}'))],
                usage=Mock(prompt_tokens=10, completion_tokens=20),
            ),
            Mock(
                choices=[Mock(message=Mock(content='{"still": "invalid"}'))],
                usage=Mock(prompt_tokens=10, completion_tokens=20),
            ),
            Mock(
                choices=[Mock(message=Mock(content='{"message": "success", "score": 0.8}'))],
                usage=Mock(prompt_tokens=10, completion_tokens=20),
            ),
        ]
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            side_effect=[AsyncMock(return_value=r)() for r in mock_responses],
        ):
            result = await provider.generate_structured(
                system_prompt="Test",
                user_prompt="Generate",
                schema=ConceptResponse,
            )
            
            assert result.message == "success"
            assert result.score == 0.8

    @pytest.mark.asyncio
    async def test_validation_error_after_max_retries(self):
        """Test that validation error is raised after max retries exceeded."""
        provider = OpenAIProvider(
            api_key="sk-test",
            max_retries=2,
        )
        
        # Mock all responses as invalid
        mock_response = Mock(
            choices=[Mock(message=Mock(content='{"invalid": "response"}'))],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        )
        
        mock_create = AsyncMock(return_value=mock_response)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderValidationError, match="Failed to validate"):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test that rate limit errors are properly wrapped."""
        provider = OpenAIProvider(api_key="sk-test")
        
        mock_create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        )
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderRateLimitError, match="rate limit exceeded"):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self):
        """Test that authentication errors are properly wrapped."""
        provider = OpenAIProvider(api_key="sk-test")
        
        api_error = APIError(
            message="Invalid API key",
            request=Mock(),
            body=None,
        )
        api_error.status_code = 401
        
        mock_create = AsyncMock(side_effect=api_error)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderAuthenticationError, match="authentication failed"):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )


class TestOpenAIProviderTimeout:
    """Test OpenAI provider timeout handling.
    
    Requirements: 12.4
    """

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test that timeout errors are properly wrapped."""
        provider = OpenAIProvider(
            api_key="sk-test",
            timeout=1.0,
        )
        
        mock_create = AsyncMock(side_effect=APITimeoutError("Request timed out"))
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderTimeoutError, match="timed out"):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )

    @pytest.mark.asyncio
    async def test_timeout_configuration(self):
        """Test that timeout is properly configured."""
        provider = OpenAIProvider(
            api_key="sk-test",
            timeout=30.0,
        )
        
        # Verify timeout is set on the client
        assert provider.client.timeout == 30.0


class TestOpenAIProviderStreaming:
    """Test OpenAI provider text streaming."""

    @pytest.mark.asyncio
    async def test_stream_text_yields_chunks(self):
        """Test that stream_text yields text chunks."""
        provider = OpenAIProvider(api_key="sk-test")
        
        # Mock streaming response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" "))]),
            Mock(choices=[Mock(delta=Mock(content="world"))]),
            Mock(choices=[Mock(delta=Mock(content=None))]),  # End of stream
        ]
        
        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk
        
        mock_create = AsyncMock(return_value=mock_stream())
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            chunks = []
            async for chunk in provider.stream_text(
                system_prompt="Test",
                user_prompt="Generate",
            ):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " ", "world"]

    @pytest.mark.asyncio
    async def test_stream_text_handles_errors(self):
        """Test that streaming errors are properly wrapped."""
        provider = OpenAIProvider(api_key="sk-test")
        
        mock_create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        )
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderRateLimitError):
                async for _ in provider.stream_text(
                    system_prompt="Test",
                    user_prompt="Generate",
                ):
                    pass


class TestOpenAIProviderTokenTracking:
    """Test OpenAI provider token tracking and latency measurement.
    
    Requirements: 14.3, 14.4
    """

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test that token usage is tracked correctly."""
        provider = OpenAIProvider(api_key="sk-test")
        
        mock_response = Mock(
            choices=[Mock(message=Mock(content='{"message": "test", "score": 0.5}'))],
            usage=Mock(prompt_tokens=100, completion_tokens=50),
        )
        
        mock_create = AsyncMock(return_value=mock_response)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            result, prompt_tokens, completion_tokens = await provider.get_token_usage(
                system_prompt="Test",
                user_prompt="Generate",
                schema=ConceptResponse,
            )
            
            assert result.message == "test"
            assert result.score == 0.5
            assert prompt_tokens == 100
            assert completion_tokens == 50

    @pytest.mark.asyncio
    async def test_token_usage_with_no_usage_data(self):
        """Test token usage when provider doesn't return usage data."""
        provider = OpenAIProvider(api_key="sk-test")
        
        mock_response = Mock(
            choices=[Mock(message=Mock(content='{"message": "test", "score": 0.5}'))],
            usage=None,  # No usage data
        )
        
        mock_create = AsyncMock(return_value=mock_response)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            result, prompt_tokens, completion_tokens = await provider.get_token_usage(
                system_prompt="Test",
                user_prompt="Generate",
                schema=ConceptResponse,
            )
            
            assert result.message == "test"
            assert prompt_tokens == 0
            assert completion_tokens == 0


class TestOpenAIProviderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """Test handling of empty responses from provider."""
        provider = OpenAIProvider(api_key="sk-test")
        
        mock_response = Mock(
            choices=[Mock(message=Mock(content=None))],
            usage=Mock(prompt_tokens=10, completion_tokens=0),
        )
        
        mock_create = AsyncMock(return_value=mock_response)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderError, match="Empty response"):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )

    @pytest.mark.asyncio
    async def test_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        provider = OpenAIProvider(
            api_key="sk-test",
            max_retries=1,
        )
        
        mock_response = Mock(
            choices=[Mock(message=Mock(content='not valid json at all'))],
            usage=Mock(prompt_tokens=10, completion_tokens=20),
        )
        
        mock_create = AsyncMock(return_value=mock_response)
        
        with patch.object(
            provider.client.chat.completions,
            "create",
            mock_create,
        ):
            with pytest.raises(AIProviderValidationError):
                await provider.generate_structured(
                    system_prompt="Test",
                    user_prompt="Generate",
                    schema=ConceptResponse,
                )
