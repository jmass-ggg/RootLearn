"""Unit tests for state machine service."""
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession, User
from app.services.state_machine_service import (
    InvalidTransitionError,
    SessionStatus,
    StateMachineService,
)


@pytest.fixture
async def sample_session(db_session: AsyncSession) -> LearningSession:
    """Create a sample learning session for testing."""
    user = User(id=uuid.uuid4())
    db_session.add(user)
    await db_session.flush()
    
    session = LearningSession(
        user_id=user.id,
        original_prompt="I don't understand recursion",
        status="analyzing",
    )
    db_session.add(session)
    await db_session.flush()
    await db_session.refresh(session)
    
    return session


@pytest.fixture
async def session_with_graph(db_session: AsyncSession) -> tuple[LearningSession, Concept, list[Concept]]:
    """Create a session with a simple graph for testing."""
    user = User(id=uuid.uuid4())
    db_session.add(user)
    await db_session.flush()
    
    session = LearningSession(
        user_id=user.id,
        original_prompt="I don't understand recursion",
        status="diagnosing",
    )
    db_session.add(session)
    await db_session.flush()
    
    # Create target concept
    target = Concept(
        session_id=session.id,
        slug="recursion",
        name="Recursion",
        description="Recursive function calls",
        is_target=True,
        mastery_score=Decimal("0.30"),
        confidence_score=Decimal("0.60"),
        status="weak",
    )
    db_session.add(target)
    await db_session.flush()
    
    # Create prerequisite concepts
    prereq1 = Concept(
        session_id=session.id,
        slug="call-stack",
        name="Call Stack",
        description="How function calls are tracked",
        is_target=False,
        mastery_score=Decimal("0.50"),
        confidence_score=Decimal("0.70"),
        status="learning",
    )
    prereq2 = Concept(
        session_id=session.id,
        slug="base-case",
        name="Base Case",
        description="Termination condition for recursion",
        is_target=False,
        mastery_score=Decimal("0.40"),
        confidence_score=Decimal("0.60"),
        status="learning",
    )
    db_session.add(prereq1)
    db_session.add(prereq2)
    await db_session.flush()
    
    # Create edges
    edge1 = ConceptEdge(
        session_id=session.id,
        source_concept_id=prereq1.id,
        target_concept_id=target.id,
        importance_weight=Decimal("0.9"),
    )
    edge2 = ConceptEdge(
        session_id=session.id,
        source_concept_id=prereq2.id,
        target_concept_id=target.id,
        importance_weight=Decimal("0.8"),
    )
    db_session.add(edge1)
    db_session.add(edge2)
    await db_session.flush()
    
    # Set target_concept_id
    session.target_concept_id = target.id
    await db_session.flush()
    await db_session.refresh(session)
    
    return session, target, [prereq1, prereq2]


class TestStateMachineService:
    """Test state machine service."""

    async def test_transition_analyzing_to_diagnosing(
        self, db_session: AsyncSession, sample_session: LearningSession
    ):
        """Test valid transition from analyzing to diagnosing."""
        service = StateMachineService(db_session)
        
        updated_session = await service.transition_to_diagnosing(sample_session.id)
        
        assert updated_session.status == "diagnosing"
        assert updated_session.id == sample_session.id

    async def test_transition_diagnosing_to_tutoring(
        self, db_session: AsyncSession, sample_session: LearningSession
    ):
        """Test valid transition from diagnosing to tutoring."""
        # Set session to diagnosing
        sample_session.status = "diagnosing"
        await db_session.flush()
        
        service = StateMachineService(db_session)
        root_gap_id = uuid.uuid4()
        
        updated_session = await service.transition_to_tutoring(
            sample_session.id, root_gap_id
        )
        
        assert updated_session.status == "tutoring"

    async def test_transition_tutoring_to_teachback(
        self, db_session: AsyncSession, sample_session: LearningSession
    ):
        """Test valid transition from tutoring to teachback."""
        # Set session to tutoring
        sample_session.status = "tutoring"
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        updated_session = await service.transition_to_teachback(sample_session.id)
        
        assert updated_session.status == "teachback"

    async def test_invalid_transition_raises_error(
        self, db_session: AsyncSession, sample_session: LearningSession
    ):
        """Test that invalid transitions raise InvalidTransitionError."""
        service = StateMachineService(db_session)
        
        # Cannot go from analyzing to tutoring directly
        with pytest.raises(InvalidTransitionError):
            await service.transition_to_tutoring(
                sample_session.id, uuid.uuid4()
            )

    async def test_transition_after_teachback_failed(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test transition after failed teach-back returns to tutoring."""
        session, target, prereqs = session_with_graph
        session.status = "teachback"
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=False,
            gap_resolved=False,
        )
        
        assert updated_session.status == "tutoring"

    async def test_transition_after_teachback_path_cleared(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test transition after teach-back when path is cleared."""
        session, target, prereqs = session_with_graph
        session.status = "teachback"
        
        # Set all prerequisites to understood
        for prereq in prereqs:
            prereq.mastery_score = Decimal("0.75")
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=True,
            gap_resolved=True,
        )
        
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None

    async def test_transition_after_teachback_more_gaps(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test transition after teach-back when more gaps remain."""
        session, target, prereqs = session_with_graph
        session.status = "teachback"
        
        # Set one prerequisite to understood, but not all
        prereqs[0].mastery_score = Decimal("0.75")
        prereqs[1].mastery_score = Decimal("0.40")
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=True,
            gap_resolved=True,
        )
        
        assert updated_session.status == "diagnosing"

    async def test_check_early_completion_high_mastery(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test early completion when target has high initial mastery."""
        session, target, prereqs = session_with_graph
        
        # Set target to high mastery and confidence
        target.mastery_score = Decimal("0.90")
        target.confidence_score = Decimal("0.85")
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        updated_session = await service.check_early_completion(session.id)
        
        assert updated_session is not None
        assert updated_session.status == "completed"
        assert updated_session.completed_at is not None

    async def test_check_early_completion_no_trigger(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test early completion not triggered when mastery is low."""
        session, target, prereqs = session_with_graph
        
        # Target has low mastery
        target.mastery_score = Decimal("0.30")
        target.confidence_score = Decimal("0.60")
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        result = await service.check_early_completion(session.id)
        
        assert result is None

    async def test_is_valid_transition(self, db_session: AsyncSession):
        """Test transition validation helper."""
        service = StateMachineService(db_session)
        
        # Valid transitions
        assert service.is_valid_transition("analyzing", "diagnosing") is True
        assert service.is_valid_transition("diagnosing", "tutoring") is True
        assert service.is_valid_transition("tutoring", "teachback") is True
        assert service.is_valid_transition("teachback", "tutoring") is True
        assert service.is_valid_transition("teachback", "diagnosing") is True
        assert service.is_valid_transition("teachback", "completed") is True
        
        # Invalid transitions
        assert service.is_valid_transition("analyzing", "tutoring") is False
        assert service.is_valid_transition("completed", "tutoring") is False
        assert service.is_valid_transition("diagnosing", "teachback") is False

    async def test_completed_at_timestamp_set(
        self, db_session: AsyncSession, session_with_graph
    ):
        """Test that completed_at timestamp is set on completion."""
        from datetime import timezone
        
        session, target, prereqs = session_with_graph
        session.status = "teachback"
        
        # Set all prerequisites to understood
        for prereq in prereqs:
            prereq.mastery_score = Decimal("0.75")
        await db_session.flush()
        
        service = StateMachineService(db_session)
        
        before_time = datetime.now(timezone.utc)
        updated_session = await service.transition_after_teachback(
            session_id=session.id,
            teachback_passed=True,
            gap_resolved=True,
        )
        after_time = datetime.now(timezone.utc)
        
        assert updated_session.completed_at is not None
        assert before_time <= updated_session.completed_at <= after_time
