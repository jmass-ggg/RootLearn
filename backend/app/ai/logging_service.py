"""AI Run Logging Service.

This module handles logging of all AI operations to the ai_runs table.
Captures execution metadata, token usage, latency, and success/failure status.
"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIRun


class AIRunLogger:
    """Service for logging AI execution details to the database.
    
    Tracks all AI invocations for auditing, debugging, and cost analysis.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the AI run logger.
        
        Args:
            db: Database session for persisting logs
        """
        self.db = db

    async def log_ai_run(
        self,
        purpose: str,
        provider: str,
        model: str,
        prompt_version: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any] | None,
        latency_ms: int,
        success: bool,
        error_code: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        session_id: uuid.UUID | None = None,
    ) -> AIRun:
        """Log an AI execution to the database.
        
        Creates an ai_runs record capturing all execution details.
        
        Args:
            purpose: Description of why this AI call was made
            provider: AI provider name (openai, anthropic, gemini)
            model: Model identifier (gpt-4, claude-3, etc.)
            prompt_version: Version of the prompt template used
            input_data: Input provided to the AI
            output_data: Output from the AI (None if failed)
            latency_ms: Time taken in milliseconds
            success: Whether the operation succeeded
            error_code: Error code if operation failed
            prompt_tokens: Number of prompt tokens (if available)
            completion_tokens: Number of completion tokens (if available)
            session_id: Associated learning session ID (if applicable)
            
        Returns:
            Created AIRun database record
        """
        ai_run = AIRun(
            session_id=session_id,
            purpose=purpose,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            input_json=input_data,
            output_json=output_data,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            success=success,
            error_code=error_code,
        )
        
        self.db.add(ai_run)
        await self.db.commit()
        await self.db.refresh(ai_run)
        
        return ai_run

    async def log_success(
        self,
        purpose: str,
        provider: str,
        model: str,
        prompt_version: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        latency_ms: int,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        session_id: uuid.UUID | None = None,
    ) -> AIRun:
        """Log a successful AI execution.
        
        Convenience method for successful operations.
        
        Args:
            purpose: Description of why this AI call was made
            provider: AI provider name
            model: Model identifier
            prompt_version: Version of the prompt template used
            input_data: Input provided to the AI
            output_data: Output from the AI
            latency_ms: Time taken in milliseconds
            prompt_tokens: Number of prompt tokens (if available)
            completion_tokens: Number of completion tokens (if available)
            session_id: Associated learning session ID (if applicable)
            
        Returns:
            Created AIRun database record
        """
        return await self.log_ai_run(
            purpose=purpose,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            input_data=input_data,
            output_data=output_data,
            latency_ms=latency_ms,
            success=True,
            error_code=None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            session_id=session_id,
        )

    async def log_failure(
        self,
        purpose: str,
        provider: str,
        model: str,
        prompt_version: str,
        input_data: dict[str, Any],
        latency_ms: int,
        error_code: str,
        session_id: uuid.UUID | None = None,
    ) -> AIRun:
        """Log a failed AI execution.
        
        Convenience method for failed operations.
        
        Args:
            purpose: Description of why this AI call was made
            provider: AI provider name
            model: Model identifier
            prompt_version: Version of the prompt template used
            input_data: Input provided to the AI
            latency_ms: Time taken in milliseconds
            error_code: Error code describing the failure
            session_id: Associated learning session ID (if applicable)
            
        Returns:
            Created AIRun database record
        """
        return await self.log_ai_run(
            purpose=purpose,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            input_data=input_data,
            output_data=None,
            latency_ms=latency_ms,
            success=False,
            error_code=error_code,
            prompt_tokens=None,
            completion_tokens=None,
            session_id=session_id,
        )


def create_ai_run_logger(db: AsyncSession) -> AIRunLogger:
    """Factory function to create an AI run logger.
    
    Args:
        db: Database session
        
    Returns:
        Configured AIRunLogger instance
    """
    return AIRunLogger(db)

