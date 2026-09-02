"""Property-based tests for session state machine.

Feature: rootlearn-knowledge-debugger
Tests Properties 66-69: State machine properties
Validates: Requirements 15.1, 15.2, 15.3, 15.4
"""
import uuid
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st, assume
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession, User
from app.services.state_machine_service import (
    InvalidTransitionError,
    SessionStatus,
    StateMachineService,
)
from tests.factories import add_learning_session


# Hypothesis strategies for generating test data
@st.composite
def valid_status_pair(draw):
    """Generate a pair of (from_status, to_status) for testing transitions."""
    all_statuses = [
        "analyzing",
        "diagnosing",
        "tutoring",
        "teachback",
        "completed",
        "abandoned",
    ]
    from_status = draw(st.sampled_from(all_statuses))
    to_status = draw(st.sampled_from(all_statuses))
    return from_status, to_status


@st.composite
def valid_mastery_score(draw):
    """Generate a valid mastery score between 0.0 and 1.0."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


class TestProperty66StateMachineTransitionsAreValid:
    """Property 66: State machine transitions are valid.
    
    For any session status update, the transition should be one of the allowed
    transitions: analyzing→diagnosing, diagnosing→tutoring, tutoring→teachback,
    teachback→tutoring, teachback→diagnosing, teachback→completed, diagnosing→completed
    
    Validates: Requirements 15.1
    """

    @pytest.mark.asyncio
    @given(status_pair=valid_status_pair())
    @settings(max_examples=100, deadline=None)
    async def test_valid_transitions_succeed_invalid_fail(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        status_pair: tuple[str, str]
    ):
        """Property test: Valid transitions succeed, invalid transitions are rejected."""
        # Feature: rootlearn-knowledge-debugger, Property 66: State machine transitions are valid
        from_status, to_status = status_pair
        
        # Create a fresh session for this test
        user = User(id=uuid.uuid4())
        db_session.add(user)
        await db_session.flush()
        
        session = LearningSession(
            user_id=user.id,
            original_prompt="Test transition",
            status=from_status,
        )
        db_session.add(session)
        await db_session.flush()
        
        # Define valid transitions
        valid_transitions = {
            "analyzing": {"diagnosing"},
            "diagnosing": {"tutoring", "completed"},
            "tutoring": {"teachback"},
            "teachback": {"tutoring", "diagnosing", "completed"},
            "completed": set(),
            "abandoned": set(),
        }
        
        service = StateMachineService(db_session)
        
        # Check if this transition is valid
        is_valid = to_status in valid_transitions.get(from_status, set())
        
        if is_valid:
            # Valid transition should succeed
            result = service.is_valid_transition(from_status, to_status)
            assert result is True, f"Expected {from_status}→{to_status} to be valid"
        else:
            # Invalid transition should be rejected
            result = service.is_valid_transition(from_status, to_status)
            assert result is False, f"Expected {from_status}→{to_status} to be invalid"


class TestProperty67UnresolvedPrerequisitesTriggerContinuedDiagnosis:
    """Property 67: Unresolved prerequisites trigger continued diagnosis.
    
    For any session in teachback where gap is resolved but other prerequisites
    remain weak, status should transition to "diagnosing"
    
    Validates: Requirements 15.2
    """

    @pytest.mark.asyncio
    @given(
        resolved_mastery=st.floats(min_value=0.70, max_value=1.0, allow_nan=False, allow_infinity=False),
        weak_mastery=st.floats(min_value=0.0, max_value=0.69, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    async def test_unresolved_prerequisites_return_to_diagnosing(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        resolved_mastery: float,
        weak_mastery: float
    ):
        """Property test: Resolved gap + weak prerequisites → diagnosing."""
        # Feature: rootlearn-knowledge-debugger, Property 67: Unresolved prerequisites trigger continued diagnosis
        
        # Create a fresh session with graph
        user = User(id=uuid.uuid4())
        db_session.add(user)
        await db_session.flush()
        
        session = LearningSession(
            user_id=user.id,
            original_prompt="Test prerequisite diagnosis",
            status="teachback",
        )
        db_session.add(session)
        await db_session.flush()
        
        # Create target concept
        target = Concept(
            session_id=session.id,
            slug="target",
            name="Target Concept",
            description="The learning goal",
            is_target=True,
            mastery_score=Decimal(str(round(weak_mastery, 4))),
            confidence_score=Decimal("0.60"),
            status="weak",
        )
        db_session.add(target)
        await db_session.flush()
        
        # Create resolved prerequisite (gap that was just fixed)
        resolved_prereq = Concept(
            session_id=session.id,
            slug="resolved",
            name="Resolved Prereq",
            description="Gap that was resolved",
            is_target=False,
            mastery_score=Decimal(str(round(resolved_mastery, 4))),
            confidence_score=Decimal("0.80"),
            status="understood",
        )
        db_session.add(resolved_prereq)
        await db_session.flush()
        
        # Create weak prerequisite (still needs work)
        weak_prereq = Concept(
            session_id=session.id,
            slug="weak",
            name="Weak Prereq",
            description="Still weak",
            is_target=False,
            mastery_score=Decimal(str(round(weak_mastery, 4))),
            confidence_score=Decimal("0.70"),
            status="weak",
        )
        db_session.add(weak_prereq)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=session.id,
            source_concept_id=resolved_prereq.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8"),
        )
        edge2 = ConceptEdge(
            session_id=session.id,
            source_concept_id=weak_prereq.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9"),
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        session.target_concept_id = target.id
        await db_session.flush()
        
        # Act - Transition after teachback with gap resolved
        service = StateMachineService(db_session)
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=True,
            gap_resolved=True,
        )
        
        # Assert - Should return to diagnosing since weak prerequisite remains
        assert updated_session.status == "diagnosing"


class TestProperty68ClearedPathTriggersCompletion:
    """Property 68: Cleared path triggers completion.
    
    For any session where all prerequisites of the target concept have
    mastery ≥ 0.70, status should transition to "completed"
    
    Validates: Requirements 15.3
    """

    @pytest.mark.asyncio
    @given(
        prereq1_mastery=st.floats(min_value=0.70, max_value=1.0, allow_nan=False, allow_infinity=False),
        prereq2_mastery=st.floats(min_value=0.70, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    async def test_cleared_path_completes_session(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        prereq1_mastery: float,
        prereq2_mastery: float
    ):
        """Property test: All prerequisites understood → completed."""
        # Feature: rootlearn-knowledge-debugger, Property 68: Cleared path triggers completion
        
        # Create a fresh session with graph
        user = User(id=uuid.uuid4())
        db_session.add(user)
        await db_session.flush()
        
        session = LearningSession(
            user_id=user.id,
            original_prompt="Test path cleared",
            status="teachback",
        )
        db_session.add(session)
        await db_session.flush()
        
        # Create target concept
        target = Concept(
            session_id=session.id,
            slug="target",
            name="Target Concept",
            description="The learning goal",
            is_target=True,
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            status="learning",
        )
        db_session.add(target)
        await db_session.flush()
        
        # Create prerequisites - all understood
        prereq1 = Concept(
            session_id=session.id,
            slug="prereq1",
            name="Prereq 1",
            description="First prerequisite",
            is_target=False,
            mastery_score=Decimal(str(round(prereq1_mastery, 4))),
            confidence_score=Decimal("0.80"),
            status="understood",
        )
        prereq2 = Concept(
            session_id=session.id,
            slug="prereq2",
            name="Prereq 2",
            description="Second prerequisite",
            is_target=False,
            mastery_score=Decimal(str(round(prereq2_mastery, 4))),
            confidence_score=Decimal("0.80"),
            status="understood",
        )
        db_session.add(prereq1)
        db_session.add(prereq2)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=session.id,
            source_concept_id=prereq1.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8"),
        )
        edge2 = ConceptEdge(
            session_id=session.id,
            source_concept_id=prereq2.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9"),
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        session.target_concept_id = target.id
        await db_session.flush()
        
        # Act - Transition after successful teachback
        service = StateMachineService(db_session)
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=True,
            gap_resolved=True,
        )
        
        # Assert - Should complete since all prerequisites are understood
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None


class TestProperty69HighInitialMasteryTriggersEarlyCompletion:
    """Property 69: High initial mastery triggers early completion.
    
    For any session where diagnostic assessment reveals target concept
    already has mastery ≥ 0.85, status should transition to "completed"
    without tutoring
    
    Validates: Requirements 15.4
    """

    @pytest.mark.asyncio
    @given(
        target_mastery=st.floats(min_value=0.85, max_value=1.0, allow_nan=False, allow_infinity=False),
        target_confidence=st.floats(min_value=0.80, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    async def test_high_initial_mastery_early_completion(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        target_mastery: float,
        target_confidence: float
    ):
        """Property test: High initial mastery → early completion."""
        # Feature: rootlearn-knowledge-debugger, Property 69: High initial mastery triggers early completion
        
        # Create a fresh session
        user = User(id=uuid.uuid4())
        db_session.add(user)
        await db_session.flush()
        
        session = LearningSession(
            user_id=user.id,
            original_prompt="Test early completion",
            status="diagnosing",
        )
        db_session.add(session)
        await db_session.flush()
        
        # Create target concept with high mastery and confidence
        target = Concept(
            session_id=session.id,
            slug="target",
            name="Target Concept",
            description="Already mastered",
            is_target=True,
            mastery_score=Decimal(str(round(target_mastery, 4))),
            confidence_score=Decimal(str(round(target_confidence, 4))),
            status="mastered",
        )
        db_session.add(target)
        await db_session.flush()
        
        session.target_concept_id = target.id
        await db_session.flush()
        
        # Act - Check for early completion
        service = StateMachineService(db_session)
        updated_session = await service.check_early_completion(session.id)
        
        # Assert - Should complete early
        assert updated_session is not None
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None

    @pytest.mark.asyncio
    @given(
        target_mastery=st.floats(min_value=0.0, max_value=0.84, allow_nan=False, allow_infinity=False),
        target_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    async def test_low_mastery_no_early_completion(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        target_mastery: float,
        target_confidence: float
    ):
        """Property test: Low mastery → no early completion."""
        # Feature: rootlearn-knowledge-debugger, Property 69: High initial mastery triggers early completion
        
        # Create a fresh session
        user = User(id=uuid.uuid4())
        db_session.add(user)
        await db_session.flush()
        
        session = LearningSession(
            user_id=user.id,
            original_prompt="Test no early completion",
            status="diagnosing",
        )
        db_session.add(session)
        await db_session.flush()
        
        # Create target concept with low mastery
        target = Concept(
            session_id=session.id,
            slug="target",
            name="Target Concept",
            description="Not yet mastered",
            is_target=True,
            mastery_score=Decimal(str(round(target_mastery, 4))),
            confidence_score=Decimal(str(round(target_confidence, 4))),
            status="weak",
        )
        db_session.add(target)
        await db_session.flush()
        
        session.target_concept_id = target.id
        await db_session.flush()
        
        # Act - Check for early completion
        service = StateMachineService(db_session)
        result = await service.check_early_completion(session.id)
        
        # Assert - Should NOT complete early
        assert result is None
