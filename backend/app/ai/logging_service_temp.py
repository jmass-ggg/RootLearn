"""Temporary AILoggingService wrapper for tutor_service compatibility.

This is a compatibility layer until tutor_service can be refactored
to use AIRunLogger directly or ValidatedAIService.
"""
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIRun


class AILoggingService:
    """Compatibility wrapper for AI logging in tutor_service."""

    def __init__(self, db: AsyncSession):
        """Initialize the AI logging service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._start_times: dict[uuid.UUID, float] = {}

    async def log_ai_invocation(
        self,
        session_id: uuid.UUID | None,
        purpose: str,
        prompt_version: str,
        input_data: dict[str, Any],
    ) -> AIRun:
        """Log the start of an AI invocation.
        
        Creates a pending AI run record that will be updated on completion.
        
        Args:
            session_id: Associated learning session ID
            purpose: Description of why this AI call was made
            prompt_version: Version of the prompt template
            input_data: Input provided to the AI
            
        Returns:
            Created AIRun with pending status
        """
        from app.ai.factory import get_ai_provider
        
        provider = get_ai_provider()
        
        ai_run = AIRun(
            id=uuid.uuid4(),
            session_id=session_id,
            purpose=purpose,
            provider=provider.provider_name,
            model=provider.model_name,
            prompt_version=prompt_version,
            input_json=input_data,
            output_json=None,
            prompt_tokens=None,
            completion_tokens=None,
            latency_ms=None,
            success=False,  # Will be updated on completion
            error_code=None,
        )
        
        self.db.add(ai_run)
        await self.db.flush()
        
        # Store start time for latency calculation
        self._start_times[ai_run.id] = time.time()
        
        return ai_run

    async def log_ai_completion(
        self,
        ai_run_id: uuid.UUID,
        output_data: dict[str, Any] | None,
        success: bool,
        error_code: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        """Log the completion of an AI invocation.
        
        Updates the AI run record with results and latency.
        
        Args:
            ai_run_id: ID of the AI run to update
            output_data: Output from the AI (None if failed)
            success: Whether the operation succeeded
            error_code: Error code if operation failed
            prompt_tokens: Number of prompt tokens (if available)
            completion_tokens: Number of completion tokens (if available)
        """
        from sqlalchemy import select
        
        # Get the AI run
        result = await self.db.execute(
            select(AIRun).where(AIRun.id == ai_run_id)
        )
        ai_run = result.scalar_one()
        
        # Calculate latency if start time was recorded
        latency_ms = None
        if ai_run_id in self._start_times:
            start_time = self._start_times.pop(ai_run_id)
            latency_ms = int((time.time() - start_time) * 1000)
        
        # Update the AI run
        ai_run.output_json = output_data
        ai_run.success = success
        ai_run.error_code = error_code
        ai_run.prompt_tokens = prompt_tokens
        ai_run.completion_tokens = completion_tokens
        ai_run.latency_ms = latency_ms
        
        await self.db.flush()
