"""Pydantic models for AI operations."""
from typing import Any

from pydantic import BaseModel, Field


class AIRunMetadata(BaseModel):
    """Metadata captured during AI operation execution."""

    purpose: str = Field(..., description="Purpose of this AI call")
    provider: str = Field(..., description="AI provider used (openai, anthropic, gemini)")
    model: str = Field(..., description="Model identifier")
    prompt_version: str = Field(..., description="Version of the prompt used")
    input_data: dict[str, Any] = Field(..., description="Input provided to AI")
    output_data: dict[str, Any] | None = Field(None, description="Output from AI")
    prompt_tokens: int | None = Field(None, description="Number of prompt tokens")
    completion_tokens: int | None = Field(None, description="Number of completion tokens")
    latency_ms: int = Field(..., description="Latency in milliseconds")
    success: bool = Field(..., description="Whether the operation succeeded")
    error_code: str | None = Field(None, description="Error code if failed")
    session_id: str | None = Field(None, description="Associated session ID")


class AIResponse(BaseModel):
    """Wrapper for AI responses with metadata."""

    content: Any = Field(..., description="The actual response content")
    metadata: AIRunMetadata = Field(..., description="Execution metadata")
