"""Property-based tests for AI validation and logging.

Feature: rootlearn-knowledge-debugger
Property 56: AI output validation occurs
Property 57: Validation failures trigger retries
Property 59: Only validated outputs are persisted
Validates: Requirements 13.1, 13.2, 13.5
"""
import json
import uuid
from typing import Any, AsyncIterator, Type, TypeVar
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.exceptions import AIProviderValidationError, AIProviderError
from app.ai.logging_service import AIRunLogger
from app.ai.protocol import AIProvider
from app.ai.schemas import ConceptAnalysisOutput, DiagnosticQuestionOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.models import AIRun, LearningSession


T = TypeVar("T", bound=BaseModel)


# Mock AI Provider for testing
class MockAIProvider:
    """Mock AI provider for testing validation logic."""
    
    def __init__(self, responses: list[Any] | None = None, should_fail: bool = False):
        """Initialize mock provider.
        
        Args:
            responses: List of responses to return on successive calls
            should_fail: Whether to always fail validation
        """
        self.responses = responses or []
        self.call_count = 0
        self.should_fail = should_fail
        self.model = "mock-model-v1"
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> T:
        """Generate structured output (mock)."""
        if self.should_fail:
            raise AIProviderValidationError("Mock validation failure")
        
        if self.call_count < len(self.responses):
            response_data = self.responses[self.call_count]
            self.call_count += 1
            
            # If response_data is already an instance, return it
            if isinstance(response_data, BaseModel):
                return response_data
            
            # If it's a dict, try to validate it
            if isinstance(response_data, dict):
                try:
                    return schema.model_validate(response_data)
                except ValidationError:
                    raise AIProviderValidationError("Mock validation failure")
            
            # If it's an exception, raise it
            if isinstance(response_data, Exception):
                raise response_data
        
        # Default: create a minimal valid instance
        raise AIProviderValidationError("No more mock responses")
    
    async def stream_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream text response (mock)."""
        yield "Mock response"


# Hypothesis strategies
@st.composite
def valid_concept_analysis(draw):
    """Generate valid ConceptAnalysisOutput data."""
    slug = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Ll", "Nd"),
        whitelist_characters="-_"
    ))).lower().strip("-_")
    
    if not slug:
        slug = "test-concept"
    
    return {
        "slug": slug,
        "name": draw(st.text(min_size=1, max_size=100)),
        "domain": draw(st.text(min_size=1, max_size=50)),
        "description": draw(st.text(min_size=10, max_size=500)),
    }


@st.composite
def invalid_concept_analysis(draw):
    """Generate invalid ConceptAnalysisOutput data (missing required fields)."""
    # Generate data with missing fields or invalid values
    strategy = draw(st.sampled_from([
        {},  # Empty
        {"slug": "test"},  # Missing required fields
        {"slug": "", "name": "Test", "domain": "CS", "description": "Desc"},  # Empty slug
        {"slug": "test", "name": "", "domain": "CS", "description": "Desc"},  # Empty name
        {"slug": "test", "name": "Test", "domain": "", "description": "Desc"},  # Empty domain
        {"slug": "test", "name": "Test", "domain": "CS", "description": ""},  # Empty description
        {"slug": "test", "name": "Test", "domain": "CS", "description": "Short"},  # Too short description
    ]))
    return strategy


class TestProperty56AIOutputValidationOccurs:
    """Property 56: AI output validation occurs.
    
    For any AI-generated structured output, it should be validated against
    its Pydantic schema before being used.
    
    Validates: Requirements 13.1
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_data=valid_concept_analysis())
    @settings(max_examples=100, deadline=None)
    async def test_valid_outputs_pass_validation(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_data: dict[str, Any]
    ):
        """Property test: Valid AI outputs pass validation and are returned."""
        # Arrange
        valid_output = ConceptAnalysisOutput(**concept_data)
        mock_provider = MockAIProvider(responses=[valid_output])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act
        result = await service.generate_structured(
            system_prompt="Test prompt",
            user_prompt="Analyze this",
            schema=ConceptAnalysisOutput,
            purpose="test_validation",
            prompt_version="v1.0",
            session_id=test_session.id,
        )
        
        # Assert
        assert isinstance(result, ConceptAnalysisOutput)
        assert result.slug == concept_data["slug"]
        assert result.name == concept_data["name"]
        assert result.domain == concept_data["domain"]
        assert result.description == concept_data["description"]
        
        # Verify AI run was logged
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(ai_runs) == 1
        assert ai_runs[0].success is True
        assert ai_runs[0].output_json is not None

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(invalid_data=invalid_concept_analysis())
    @settings(max_examples=50, deadline=None)
    async def test_invalid_outputs_fail_validation(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        invalid_data: dict[str, Any]
    ):
        """Property test: Invalid AI outputs fail validation and raise error."""
        # Arrange
        mock_provider = MockAIProvider(responses=[invalid_data, invalid_data, invalid_data])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act & Assert
        with pytest.raises(AIProviderValidationError):
            await service.generate_structured(
                system_prompt="Test prompt",
                user_prompt="Analyze this",
                schema=ConceptAnalysisOutput,
                purpose="test_validation_failure",
                prompt_version="v1.0",
                session_id=test_session.id,
            )
        
        # Verify AI runs were logged (3 attempts: initial + 2 retries)
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(ai_runs) == 3  # Initial attempt + 2 retries
        assert all(run.success is False for run in ai_runs)
        assert all(run.error_code in ["validation_error", "validation_error_exhausted"] for run in ai_runs)


class TestProperty57ValidationFailuresTriggerRetries:
    """Property 57: Validation failures trigger retries.
    
    For any AI output that fails validation, the system should retry
    up to 2 times before giving up.
    
    Validates: Requirements 13.2
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_retries_on_validation_failure(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: Validation failures trigger exactly 2 retries."""
        # Arrange - Fail twice, then succeed
        invalid_data = {"slug": "test"}  # Missing required fields
        valid_data = {
            "slug": "recursion",
            "name": "Recursion",
            "domain": "Computer Science",
            "description": "A function that calls itself to solve problems."
        }
        
        mock_provider = MockAIProvider(responses=[
            invalid_data,  # First attempt fails
            invalid_data,  # First retry fails
            valid_data,    # Second retry succeeds
        ])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act
        result = await service.generate_structured(
            system_prompt="Test prompt",
            user_prompt="Analyze recursion",
            schema=ConceptAnalysisOutput,
            purpose="test_retry_logic",
            prompt_version="v1.0",
            session_id=test_session.id,
        )
        
        # Assert - Should succeed after retries
        assert isinstance(result, ConceptAnalysisOutput)
        assert result.slug == "recursion"
        
        # Verify exactly 3 AI runs (initial + 2 retries)
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(ai_runs) == 3
        
        # First two should fail, last should succeed
        assert ai_runs[0].success is False
        assert ai_runs[1].success is False
        assert ai_runs[2].success is True

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_stops_after_max_retries(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: System stops retrying after max_retries is exhausted."""
        # Arrange - Always fail
        invalid_data = {"slug": "test"}  # Missing required fields
        
        mock_provider = MockAIProvider(responses=[
            invalid_data,  # Initial attempt
            invalid_data,  # Retry 1
            invalid_data,  # Retry 2
        ])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act & Assert
        with pytest.raises(AIProviderValidationError) as exc_info:
            await service.generate_structured(
                system_prompt="Test prompt",
                user_prompt="Analyze this",
                schema=ConceptAnalysisOutput,
                purpose="test_max_retries",
                prompt_version="v1.0",
                session_id=test_session.id,
            )
        
        assert "3 attempts" in str(exc_info.value) or "after" in str(exc_info.value).lower()
        
        # Verify exactly 3 AI runs (no more retries after limit)
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(ai_runs) == 3
        assert all(run.success is False for run in ai_runs)

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_no_retry_on_provider_errors(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: Non-validation errors do not trigger retries."""
        # Arrange - Provider error (not validation error)
        mock_provider = MockAIProvider(responses=[
            AIProviderError("Network failure"),
        ])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act & Assert
        with pytest.raises(AIProviderError) as exc_info:
            await service.generate_structured(
                system_prompt="Test prompt",
                user_prompt="Analyze this",
                schema=ConceptAnalysisOutput,
                purpose="test_no_retry_on_provider_error",
                prompt_version="v1.0",
                session_id=test_session.id,
            )
        
        assert "Network failure" in str(exc_info.value)
        
        # Verify only 1 AI run (no retries for provider errors)
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        assert len(ai_runs) == 1
        assert ai_runs[0].success is False
        assert ai_runs[0].error_code == "provider_error"


class TestProperty59OnlyValidatedOutputsPersisted:
    """Property 59: Only validated outputs are persisted.
    
    For any AI output stored in the database (via ai_runs.output_json),
    it should have passed Pydantic validation.
    
    Validates: Requirements 13.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_data=valid_concept_analysis())
    @settings(max_examples=100, deadline=None)
    async def test_only_validated_outputs_in_database(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_data: dict[str, Any]
    ):
        """Property test: All persisted AI outputs can be revalidated successfully."""
        # Arrange
        valid_output = ConceptAnalysisOutput(**concept_data)
        mock_provider = MockAIProvider(responses=[valid_output])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act
        result = await service.generate_structured(
            system_prompt="Test prompt",
            user_prompt="Analyze this",
            schema=ConceptAnalysisOutput,
            purpose="test_persistence",
            prompt_version="v1.0",
            session_id=test_session.id,
        )
        
        # Assert - Retrieve from database and revalidate
        stmt = select(AIRun).where(
            AIRun.session_id == test_session.id,
            AIRun.success == True
        )
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        
        assert len(ai_runs) == 1
        assert ai_runs[0].output_json is not None
        
        # Revalidate the stored output
        stored_output = ConceptAnalysisOutput.model_validate(ai_runs[0].output_json)
        assert stored_output.slug == result.slug
        assert stored_output.name == result.name
        assert stored_output.domain == result.domain
        assert stored_output.description == result.description

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_failed_validations_have_no_output(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: Failed validation attempts have NULL output_json."""
        # Arrange
        invalid_data = {"slug": "test"}  # Missing required fields
        mock_provider = MockAIProvider(responses=[invalid_data, invalid_data, invalid_data])
        logger = AIRunLogger(db_session)
        service = ValidatedAIService(mock_provider, logger, max_retries=2)
        
        # Act
        with pytest.raises(AIProviderValidationError):
            await service.generate_structured(
                system_prompt="Test prompt",
                user_prompt="Analyze this",
                schema=ConceptAnalysisOutput,
                purpose="test_failed_validation_no_output",
                prompt_version="v1.0",
                session_id=test_session.id,
            )
        
        # Assert - All failed runs should have NULL output_json
        stmt = select(AIRun).where(AIRun.session_id == test_session.id)
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        
        assert len(ai_runs) == 3  # All attempts logged
        for run in ai_runs:
            assert run.success is False
            assert run.output_json is None  # No output persisted for failed validations

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_all_successful_outputs_are_valid(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: All successful AI runs have outputs that pass schema validation."""
        # Arrange - Create multiple successful AI runs
        valid_outputs = [
            ConceptAnalysisOutput(
                slug="recursion",
                name="Recursion",
                domain="Computer Science",
                description="A function that calls itself to solve problems."
            ),
            ConceptAnalysisOutput(
                slug="loops",
                name="Loops",
                domain="Programming",
                description="Repeated execution of a block of code until a condition is met."
            ),
        ]
        
        for output in valid_outputs:
            mock_provider = MockAIProvider(responses=[output])
            logger = AIRunLogger(db_session)
            service = ValidatedAIService(mock_provider, logger, max_retries=2)
            
            await service.generate_structured(
                system_prompt="Test prompt",
                user_prompt="Analyze this",
                schema=ConceptAnalysisOutput,
                purpose="test_multiple_outputs",
                prompt_version="v1.0",
                session_id=test_session.id,
            )
        
        # Assert - Retrieve all successful runs and verify outputs are valid
        stmt = select(AIRun).where(
            AIRun.session_id == test_session.id,
            AIRun.success == True
        )
        ai_runs = (await db_session.execute(stmt)).scalars().all()
        
        assert len(ai_runs) == len(valid_outputs)
        
        # Every successful run must have a valid output
        for run in ai_runs:
            assert run.output_json is not None
            # This should not raise ValidationError
            validated_output = ConceptAnalysisOutput.model_validate(run.output_json)
            assert isinstance(validated_output, ConceptAnalysisOutput)
            assert len(validated_output.slug) > 0
            assert len(validated_output.name) > 0
            assert len(validated_output.description) >= 10

