"""Property-based tests for teach-back evaluation.

Feature: rootlearn-knowledge-debugger
Property 40: Teach-back evaluation structure
Property 41: Teach-back evaluation details
Property 42: Teach-back feeds mastery engine
Property 43: Insufficient teach-back returns to tutoring
Property 44: Sufficient teach-back proceeds
Property 45: Teach-back persistence
Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, LearningSession, TeachBackAttempt, MasteryEvent
from app.services.teachback_service import TeachBackService
from tests.factories import add_learning_session


# Hypothesis strategies
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


def unique_concept_slug():
    """Generate a unique concept slug for each test run."""
    return st.uuids().map(lambda value: f"concept-{str(value)[:8]}")


@st.composite
def student_explanation_text(draw):
    """Generate realistic student explanation text."""
    templates = [
        "{} is a concept that involves {}",
        "I understand {} as {}",
        "{} works by {}",
        "The key idea of {} is that {}",
        "You use {} when you need to {}",
        "{} means {}",
    ]
    template = draw(st.sampled_from(templates))
    
    words = draw(st.lists(
        st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
        min_size=2,
        max_size=2
    ))
    
    try:
        return template.format(*words)
    except (IndexError, KeyError):
        return "This concept is about understanding the fundamental principles and applying them correctly."


class TestProperty40TeachBackEvaluationStructure:
    """Property 40: Teach-back evaluation structure.
    
    For any submitted teach-back explanation, the evaluation should return
    all three scores: coverage_score, reasoning_score, and clarity_score.
    
    Validates: Requirements 10.2
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        slug=unique_concept_slug(),
        explanation=student_explanation_text(),
        coverage=st.floats(min_value=0.0, max_value=1.0),
        reasoning=st.floats(min_value=0.0, max_value=1.0),
        clarity=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_evaluation_returns_all_three_scores(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        slug: str,
        explanation: str,
        coverage: float,
        reasoning: float,
        clarity: float
    ):
        """Property test: Teach-back evaluation returns coverage, reasoning, and clarity scores."""
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        # Feature: rootlearn-knowledge-debugger, Property 40: Teach-back evaluation structure
        
        # Arrange - Create concept with unique slug
        concept = Concept(
            session_id=test_session.id,
            slug=slug,
            name="Test Concept",
            description="A concept for testing teach-back",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Set session to teachback status
        test_session.status = "teachback"
        await db_session.flush()
        
        # Mock AI evaluation output
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = round(coverage, 4)
        mock_evaluation.reasoning_score = round(reasoning, 4)
        mock_evaluation.clarity_score = round(clarity, 4)
        mock_evaluation.demonstrated_points = ["Point 1", "Point 2"]
        mock_evaluation.missing_points = ["Point 3"]
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: round((coverage + reasoning + clarity) / 3, 4)
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            # Create service with mocked AI
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation=explanation
            )
            
            # Assert - All three scores present
            assert result.coverage_score is not None
            assert 0.0 <= result.coverage_score <= 1.0
            
            assert result.reasoning_score is not None
            assert 0.0 <= result.reasoning_score <= 1.0
            
            assert result.clarity_score is not None
            assert 0.0 <= result.clarity_score <= 1.0
            
            # Average should be calculated
            assert result.average_score is not None
            expected_avg = (result.coverage_score + result.reasoning_score + result.clarity_score) / 3
            assert abs(result.average_score - expected_avg) < 0.01

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        slug=unique_concept_slug(),
        explanation_length=st.integers(min_value=10, max_value=500)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_evaluation_accepts_various_explanation_lengths(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        slug: str,
        explanation_length: int
    ):
        """Property test: Evaluation works for explanations of various lengths."""
        # Feature: rootlearn-knowledge-debugger, Property 40: Teach-back evaluation structure
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=slug,
            name="Test Concept",
            description="A concept",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        explanation = "x" * explanation_length
        
        # Mock AI evaluation
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = 0.75
        mock_evaluation.reasoning_score = 0.80
        mock_evaluation.clarity_score = 0.70
        mock_evaluation.demonstrated_points = ["Point A"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: 0.75
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act & Assert - Should not raise exception
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation=explanation
            )
            
            assert result is not None
            assert result.coverage_score >= 0.0


class TestProperty41TeachBackEvaluationDetails:
    """Property 41: Teach-back evaluation details.
    
    For any teach-back evaluation, it should identify: demonstrated_points,
    missing_points, and misconceptions_detected.
    
    Validates: Requirements 10.3
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        slug=unique_concept_slug(),
        num_demonstrated=st.integers(min_value=0, max_value=5),
        num_missing=st.integers(min_value=0, max_value=5),
        num_misconceptions=st.integers(min_value=0, max_value=3)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_evaluation_identifies_all_detail_categories(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        slug: str,
        num_demonstrated: int,
        num_missing: int,
        num_misconceptions: int
    ):
        """Property test: Evaluation identifies demonstrated points, missing points, and misconceptions."""
        # Feature: rootlearn-knowledge-debugger, Property 41: Teach-back evaluation details
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=slug,
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Create mock evaluation with variable numbers of each detail type
        demonstrated_points = [f"Demonstrated {i}" for i in range(num_demonstrated)]
        missing_points = [f"Missing {i}" for i in range(num_missing)]
        misconceptions = [f"Misconception {i}" for i in range(num_misconceptions)]
        
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = 0.70
        mock_evaluation.reasoning_score = 0.75
        mock_evaluation.clarity_score = 0.80
        mock_evaluation.demonstrated_points = demonstrated_points
        mock_evaluation.missing_points = missing_points
        mock_evaluation.misconceptions = misconceptions
        mock_evaluation.average_score = lambda: 0.75
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Student explanation"
            )
            
            # Assert - All detail categories present
            assert result.demonstrated_points is not None
            assert isinstance(result.demonstrated_points, list)
            assert len(result.demonstrated_points) == num_demonstrated
            
            assert result.missing_points is not None
            assert isinstance(result.missing_points, list)
            assert len(result.missing_points) == num_missing
            
            assert result.misconceptions is not None
            assert isinstance(result.misconceptions, list)
            assert len(result.misconceptions) == num_misconceptions


class TestProperty42TeachBackFeedsMasteryEngine:
    """Property 42: Teach-back feeds mastery engine.
    
    For any completed teach-back evaluation, the scores should be
    incorporated into the mastery calculation for that concept.
    
    Validates: Requirements 10.4
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        slug=unique_concept_slug(),
        coverage=st.floats(min_value=0.0, max_value=1.0),
        reasoning=st.floats(min_value=0.0, max_value=1.0),
        clarity=st.floats(min_value=0.0, max_value=1.0),
        initial_mastery=valid_score()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_teachback_creates_mastery_event(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        slug: str,
        coverage: float,
        reasoning: float,
        clarity: float,
        initial_mastery: Decimal
    ):
        """Property test: Teach-back evaluation creates mastery event with teachback source."""
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        # Feature: rootlearn-knowledge-debugger, Property 42: Teach-back feeds mastery engine
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=slug,
            name="Concept",
            description="Description",
            mastery_score=initial_mastery,
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Count mastery events before
        events_before_result = await db_session.execute(
            select(MasteryEvent).where(
                MasteryEvent.concept_id == concept.id,
                MasteryEvent.source_type == "teachback"
            )
        )
        events_before_count = len(list(events_before_result.scalars().all()))
        
        # Mock evaluation
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = round(coverage, 4)
        mock_evaluation.reasoning_score = round(reasoning, 4)
        mock_evaluation.clarity_score = round(clarity, 4)
        mock_evaluation.demonstrated_points = ["Point"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: round((coverage + reasoning + clarity) / 3, 4)
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Explanation"
            )
            
            # Assert - Should have new mastery event
            events_after_result = await db_session.execute(
                select(MasteryEvent).where(
                    MasteryEvent.concept_id == concept.id,
                    MasteryEvent.source_type == "teachback"
                )
            )
            events_after = list(events_after_result.scalars().all())
            
            assert len(events_after) == events_before_count + 1
            
            # Verify latest event has correct source and data
            latest_event = events_after[-1]
            assert latest_event.source_type == "teachback"
            assert latest_event.reason_json is not None
            assert "average_score" in latest_event.reason_json
            assert "coverage_score" in latest_event.reason_json
            assert "reasoning_score" in latest_event.reason_json
            assert "clarity_score" in latest_event.reason_json

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        slug=unique_concept_slug(),
        avg_score=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_teachback_updates_concept_mastery(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        slug: str,
        avg_score: float
    ):
        """Property test: Teach-back evaluation updates concept mastery score."""
        # Feature: rootlearn-knowledge-debugger, Property 42: Teach-back feeds mastery engine
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        initial_mastery = Decimal("0.50")
        concept = Concept(
            session_id=test_session.id,
            slug=slug,
            name="Concept",
            description="Description",
            mastery_score=initial_mastery,
            confidence_score=Decimal("0.35"),  # Low confidence, only 1 evidence
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Mock evaluation with specific average score
        mock_evaluation = AsyncMock()
        avg_rounded = round(avg_score, 4)
        mock_evaluation.coverage_score = avg_rounded
        mock_evaluation.reasoning_score = avg_rounded
        mock_evaluation.clarity_score = avg_rounded
        mock_evaluation.demonstrated_points = ["Point"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: avg_rounded
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Explanation"
            )
            
            # Assert - Mastery should be updated
            await db_session.refresh(concept)
            
            # New mastery should be different from initial (unless teach-back score exactly equals initial)
            # With only teach-back evidence, mastery should equal teach-back average
            assert concept.mastery_score != initial_mastery or abs(float(initial_mastery) - avg_rounded) < 0.01
            
            # Mastery should be in valid range
            assert 0.0 <= float(concept.mastery_score) <= 1.0


class TestProperty43InsufficientTeachBackReturnsTutoring:
    """Property 43: Insufficient teach-back returns to tutoring.
    
    For any teach-back with average_score < 0.70, the session should
    transition back to "tutoring" status.
    
    Validates: Requirements 10.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(avg_score=st.floats(min_value=0.0, max_value=0.69))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_low_score_indicates_continue_tutoring(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        avg_score: float
    ):
        """Property test: Teach-back with score < 0.70 signals to continue tutoring."""
        # Feature: rootlearn-knowledge-debugger, Property 43: Insufficient teach-back returns to tutoring
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug="concept",
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Mock evaluation with low scores
        avg_rounded = round(avg_score, 4)
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = avg_rounded
        mock_evaluation.reasoning_score = avg_rounded
        mock_evaluation.clarity_score = avg_rounded
        mock_evaluation.demonstrated_points = ["Partial"]
        mock_evaluation.missing_points = ["Key concept"]
        mock_evaluation.misconceptions = ["Some confusion"]
        mock_evaluation.average_score = lambda: avg_rounded
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Incomplete explanation"
            )
            
            # Assert - Should indicate tutoring should continue
            assert result.should_continue_tutoring is True
            assert result.average_score < 0.70

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        coverage=st.floats(min_value=0.0, max_value=0.69),
        reasoning=st.floats(min_value=0.0, max_value=0.69),
        clarity=st.floats(min_value=0.0, max_value=0.69)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_any_low_component_score_may_trigger_continuation(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        coverage: float,
        reasoning: float,
        clarity: float
    ):
        """Property test: Low scores in any dimension can result in continuing tutoring."""
        # Feature: rootlearn-knowledge-debugger, Property 43: Insufficient teach-back returns to tutoring
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug="concept",
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = round(coverage, 4)
        mock_evaluation.reasoning_score = round(reasoning, 4)
        mock_evaluation.clarity_score = round(clarity, 4)
        mock_evaluation.demonstrated_points = []
        mock_evaluation.missing_points = ["Something"]
        mock_evaluation.misconceptions = []
        avg = (coverage + reasoning + clarity) / 3
        mock_evaluation.average_score = lambda: round(avg, 4)
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Explanation"
            )
            
            # Assert - Decision based on average
            if avg < 0.70:
                assert result.should_continue_tutoring is True


class TestProperty44SufficientTeachBackProceeds:
    """Property 44: Sufficient teach-back proceeds.
    
    For any teach-back with average_score >= 0.70, mastery should be updated
    and the system should select the next concept or complete.
    
    Validates: Requirements 10.6
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(avg_score=st.floats(min_value=0.70, max_value=1.0))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_high_score_indicates_proceed(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        avg_score: float
    ):
        """Property test: Teach-back with score >= 0.70 signals to proceed."""
        # Feature: rootlearn-knowledge-debugger, Property 44: Sufficient teach-back proceeds
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug="concept",
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Mock evaluation with high scores
        avg_rounded = round(avg_score, 4)
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = avg_rounded
        mock_evaluation.reasoning_score = avg_rounded
        mock_evaluation.clarity_score = avg_rounded
        mock_evaluation.demonstrated_points = ["Key concept", "Details"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: avg_rounded
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Complete explanation"
            )
            
            # Assert - Should indicate ready to proceed
            assert result.should_continue_tutoring is False
            assert result.average_score >= 0.70
            
            # Mastery should have been updated
            await db_session.refresh(concept)
            # With high teach-back score, mastery should reflect it
            assert float(concept.mastery_score) > 0.0


class TestProperty45TeachBackPersistence:
    """Property 45: Teach-back persistence.
    
    For any submitted teach-back explanation, a teachback_attempts record
    should be created with student_explanation and all evaluation scores.
    
    Validates: Requirements 10.7
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        explanation=student_explanation_text(),
        coverage=st.floats(min_value=0.0, max_value=1.0),
        reasoning=st.floats(min_value=0.0, max_value=1.0),
        clarity=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_teachback_attempt_is_persisted(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        explanation: str,
        coverage: float,
        reasoning: float,
        clarity: float
    ):
        """Property test: Teach-back creates persistent attempt record with all scores."""
        # Feature: rootlearn-knowledge-debugger, Property 45: Teach-back persistence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug="concept",
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Count attempts before
        attempts_before_result = await db_session.execute(
            select(TeachBackAttempt).where(
                TeachBackAttempt.session_id == test_session.id,
                TeachBackAttempt.concept_id == concept.id
            )
        )
        attempts_before_count = len(list(attempts_before_result.scalars().all()))
        
        # Mock evaluation
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = round(coverage, 4)
        mock_evaluation.reasoning_score = round(reasoning, 4)
        mock_evaluation.clarity_score = round(clarity, 4)
        mock_evaluation.demonstrated_points = ["Point"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: round((coverage + reasoning + clarity) / 3, 4)
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act
            result = await service.evaluate_teachback(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation=explanation
            )
            
            # Assert - New attempt should be created
            attempts_after_result = await db_session.execute(
                select(TeachBackAttempt).where(
                    TeachBackAttempt.session_id == test_session.id,
                    TeachBackAttempt.concept_id == concept.id
                )
            )
            attempts_after = list(attempts_after_result.scalars().all())
            
            assert len(attempts_after) == attempts_before_count + 1
            
            # Verify latest attempt has all required fields
            latest_attempt = attempts_after[-1]
            assert latest_attempt.id == result.attempt_id
            assert latest_attempt.session_id == test_session.id
            assert latest_attempt.concept_id == concept.id
            assert latest_attempt.student_explanation == explanation
            assert 0.0 <= float(latest_attempt.coverage_score) <= 1.0
            assert 0.0 <= float(latest_attempt.reasoning_score) <= 1.0
            assert 0.0 <= float(latest_attempt.clarity_score) <= 1.0
            assert latest_attempt.created_at is not None

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(num_attempts=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_multiple_teachback_attempts_all_persisted(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        num_attempts: int
    ):
        """Property test: Multiple teach-back attempts are all persisted separately."""
        # Feature: rootlearn-knowledge-debugger, Property 45: Teach-back persistence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="teachback"
        )
        
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug="concept",
            name="Concept",
            description="Description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        test_session.status = "teachback"
        await db_session.flush()
        
        # Mock evaluation
        mock_evaluation = AsyncMock()
        mock_evaluation.coverage_score = 0.75
        mock_evaluation.reasoning_score = 0.80
        mock_evaluation.clarity_score = 0.70
        mock_evaluation.demonstrated_points = ["Point"]
        mock_evaluation.missing_points = []
        mock_evaluation.misconceptions = []
        mock_evaluation.average_score = lambda: 0.75
        
        with patch('app.services.teachback_service.ValidatedAIService') as mock_ai_class:
            mock_ai_instance = AsyncMock()
            mock_ai_instance.generate_structured = AsyncMock(return_value=mock_evaluation)
            
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(db_session)
            service = TeachBackService(db_session, mock_ai_instance, mastery_service)
            
            # Act - Submit multiple attempts
            for i in range(num_attempts):
                await service.evaluate_teachback(
                    session_id=test_session.id,
                    concept_id=concept.id,
                    student_explanation=f"Attempt {i}"
                )
            
            # Assert - All attempts should be persisted
            attempts_result = await db_session.execute(
                select(TeachBackAttempt).where(
                    TeachBackAttempt.session_id == test_session.id,
                    TeachBackAttempt.concept_id == concept.id
                )
            )
            attempts = list(attempts_result.scalars().all())
            
            assert len(attempts) == num_attempts
            
            # Each should have unique explanation
            explanations = [att.student_explanation for att in attempts]
            for i in range(num_attempts):
                assert f"Attempt {i}" in explanations
