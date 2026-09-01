"""Pydantic schemas for session endpoints."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SessionCreateRequest(BaseModel):
    """Request schema for creating a new session."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user creating the session"
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The learning prompt describing what the user doesn't understand"
    )
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt_not_empty(cls, v: str) -> str:
        """Validate that prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()


class SessionResponse(BaseModel):
    """Response schema for session data."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    original_prompt: str
    normalized_topic: Optional[str] = None
    target_concept_id: Optional[uuid.UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standardized error response schema."""
    
    error: dict = Field(
        ...,
        description="Error information"
    )
    
    @staticmethod
    def create(
        code: str,
        message: str,
        request_id: str,
        details: Optional[dict] = None
    ) -> dict:
        """Create a standardized error response.
        
        Args:
            code: Error code (e.g., "session_not_found", "validation_error")
            message: Human-readable error message
            request_id: Request correlation ID
            details: Optional additional error details
            
        Returns:
            Formatted error response dictionary
        """
        return {
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details or {},
            }
        }
