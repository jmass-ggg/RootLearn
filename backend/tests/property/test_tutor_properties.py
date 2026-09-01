"""Property-based tests for Socratic tutoring.

Feature: rootlearn-knowledge-debugger
Property 33: Root gap triggers tutoring state
Property 34: Tutor response generation
Property 36: Tutor context completeness
Property 37: Tutor message persistence
Property 38: Tutoring updates practice evidence
Validates: Requirements 9.1, 9.2, 9.5, 9.6, 9.8
"""
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession, TutorMessage, MasteryEvent
from app.services.tutor_service import TutorService, TutorContext
from tests.factories import add_learning_session


# Hypothesis strategies
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def user_message_text(draw):
    """Generate realistic user message text."""
    # Generate meaningful messages (not just random strings)
    templates = [
        "I don't understand {}",
        "Can you explain {} again?",
        "What is {}?",
        "How does {} work?",
        "I'm confused about {}",
        "Is {} the same as {}?",
    ]
    template = draw(st.sampled_from(templates))
    
    if "{}" in template:
        placeholder_count = template.count("{}")
        words = draw(st.lists(
            st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
            min_size=placeholder_count,
            max_size=placeholder_count,
        ))
        return template.format(*words)
    return template


class TestProperty33RootGapTriggersTutoringState:
    """Property 33: Root gap triggers tutoring state.
    
    For any session where a root gap is identified, the session status
    should transition to "tutoring".
    
    Validates: Requirements 9.1
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=st.floats(min_value=0.0, max_value=0.69),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_start_tutoring_transitions_to_tutoring_status(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: float,
        confidence: Decimal
    ):
        """Property test: Starting tutoring transitions session to tutoring status."""
        # Feature: rootlearn-knowledge-debugger, Property 33: Root gap triggers tutoring state
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create root gap concept
        mastery_decimal = Decimal(str(round(mastery, 4)))
        
        root_gap_concept = Concept(
            session_id=test_session.id,
            slug="root-gap",
            name="Root Gap Concept",
            description="The identified root gap",
            mastery_score=mastery_decimal,
            confidence_score=confidence,
            is_target=False,
            status="weak"
        )
        db_session.add(root_gap_concept)
        await db_session.flush()
        
        # Ensure session starts in a non-tutoring state
        test_session.status = "diagnosing"
        await db_session.flush()
        
        # Act
        service = TutorService(db_session)
        await service.start_tutoring(
            session_id=test_session.id,
            concept_id=root_gap_concept.id
        )
        
        # Assert - Session status should be "tutoring"
        await db_session.refresh(test_session)
        assert test_session.status == "tutoring"

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_start_tutoring_requires_valid_concept(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Starting tutoring validates concept exists in session."""
        # Feature: rootlearn-knowledge-debugger, Property 33: Root gap triggers tutoring state
        
        # Arrange - Use non-existent concept ID
        fake_concept_id = uuid.uuid4()
        
        # Act & Assert - Should raise ValueError
        service = TutorService(db_session)
        
        with pytest.raises(ValueError, match="not found"):
            await service.start_tutoring(
                session_id=test_session.id,
                concept_id=fake_concept_id
            )

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(initial_status=st.sampled_from(["analyzing", "diagnosing", "teachback"]))
    @settings(max_examples=50, deadline=None)
    async def test_tutoring_state_transition_from_various_states(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        initial_status: str
    ):
        """Property test: Tutoring can be started from various valid states."""
        # Feature: rootlearn-knowledge-debugger, Property 33: Root gap triggers tutoring state
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status=initial_status
        )
        
        # Arrange - Create concept
        concept = Concept(
            session_id=test_session.id,
            slug="test-concept",
            name="Test Concept",
            description="A test concept",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.70"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Set initial status
        test_session.status = initial_status
        await db_session.flush()
        
        # Act
        service = TutorService(db_session)
        await service.start_tutoring(
            session_id=test_session.id,
            concept_id=concept.id
        )
        
        # Assert
        await db_session.refresh(test_session)
        assert test_session.status == "tutoring"


class TestProperty34TutorResponseGeneration:
    """Property 34: Tutor response generation.
    
    For any tutoring context with current concept and user message,
    the AI should generate a non-empty tutor response.
    
    Validates: Requirements 9.2
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        user_message=user_message_text(),
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_generate_response_produces_non_empty_response(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        user_message: str,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: Tutor response generation produces non-empty response."""
        # Feature: rootlearn-knowledge-debugger, Property 34: Tutor response generation
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange - Create target and current concept
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target concept",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current Concept",
            description="The concept being tutored",
            mastery_score=mastery,
            confidence_score=confidence,
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        # Update session with target
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        # Create edge
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial system message so get_tutor_context works
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting tutoring session",
            hint_level=0
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Mock AI provider
        mock_response = "Let me help you understand this concept. What specific part is confusing?"
        
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                for chunk in mock_response:
                    yield chunk
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            # Act
            service = TutorService(db_session)
            response = await service.generate_response(
                session_id=test_session.id,
                user_message=user_message
            )
            
            # Assert - Response should be non-empty
            assert response is not None
            assert isinstance(response, str)
            assert len(response) > 0
            
            # Verify AI provider was called
            mock_provider.stream_text.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(message_count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_response_generation_handles_multiple_interactions(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        message_count: int
    ):
        """Property test: Multiple response generations work correctly."""
        # Feature: rootlearn-knowledge-debugger, Property 34: Tutor response generation
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange - Create concepts and edge
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current Concept",
            description="Being tutored",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial message
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting tutoring",
            hint_level=0
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Mock AI provider
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                yield "Mock tutor response"
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            service = TutorService(db_session)
            
            # Act - Generate multiple responses
            responses = []
            for i in range(message_count):
                response = await service.generate_response(
                    session_id=test_session.id,
                    user_message=f"User question {i}"
                )
                responses.append(response)
            
            # Assert - All responses should be valid
            assert len(responses) == message_count
            for response in responses:
                assert response is not None
                assert len(response) > 0


class TestProperty36TutorContextCompleteness:
    """Property 36: Tutor context completeness.
    
    For any tutor AI invocation, the context should include: current_concept,
    root_gap, graph_neighborhood, recent_messages, known_misconceptions,
    mastery, confidence, and hint_level.
    
    Validates: Requirements 9.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score(),
        hint_level=st.integers(min_value=0, max_value=4)
    )
    @settings(max_examples=100, deadline=None)
    async def test_tutor_context_contains_all_required_fields(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal,
        hint_level: int
    ):
        """Property test: Tutor context has all required fields."""
        # Feature: rootlearn-knowledge-debugger, Property 36: Tutor context completeness
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange - Create full context
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target concept description",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current Concept",
            description="Current concept description",
            mastery_score=mastery,
            confidence_score=confidence,
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        
        # Add a related concept for graph neighborhood
        related_concept = Concept(
            session_id=test_session.id,
            slug="related",
            name="Related Concept",
            description="Related concept description",
            mastery_score=Decimal("0.60"),
            confidence_score=Decimal("0.70"),
            is_target=False,
            status="learning"
        )
        db_session.add(related_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        # Create edges (graph structure)
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=related_concept.id,
            target_concept_id=current_concept.id,
            importance_weight=Decimal("0.7")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Add tutor messages with hint level
        messages = [
            TutorMessage(
                session_id=test_session.id,
                concept_id=current_concept.id,
                role="system",
                content="Starting tutoring",
                hint_level=0
            ),
            TutorMessage(
                session_id=test_session.id,
                concept_id=current_concept.id,
                role="user",
                content="I don't understand",
                hint_level=None
            ),
            TutorMessage(
                session_id=test_session.id,
                concept_id=current_concept.id,
                role="assistant",
                content="Let me guide you",
                hint_level=hint_level
            )
        ]
        for msg in messages:
            db_session.add(msg)
        await db_session.flush()
        
        # Act
        service = TutorService(db_session)
        context = await service.get_tutor_context(test_session.id)
        
        # Assert - All required fields present
        assert isinstance(context, TutorContext)
        
        # Current concept
        assert context.current_concept is not None
        assert context.current_concept.id == current_concept.id
        assert context.current_concept.name == "Current Concept"
        
        # Target concept
        assert context.target_concept is not None
        assert context.target_concept.id == target_concept.id
        assert context.target_concept.name == "Target Concept"
        
        # Root gap explanation
        assert context.root_gap_explanation is not None
        assert isinstance(context.root_gap_explanation, str)
        assert len(context.root_gap_explanation) > 0
        
        # Recent messages
        assert context.recent_messages is not None
        assert isinstance(context.recent_messages, list)
        assert len(context.recent_messages) > 0
        
        # Misconceptions (may be empty list)
        assert context.misconceptions is not None
        assert isinstance(context.misconceptions, list)
        
        # Mastery and confidence
        assert context.mastery_score is not None
        assert 0.0 <= context.mastery_score <= 1.0
        assert context.confidence_score is not None
        assert 0.0 <= context.confidence_score <= 1.0
        
        # Hint level
        assert context.hint_level is not None
        assert context.hint_level >= 0
        assert context.hint_level <= 4
        
        # Graph neighborhood
        assert context.graph_neighborhood is not None
        assert isinstance(context.graph_neighborhood, list)
        # Should include related concept as neighbor
        assert len(context.graph_neighborhood) > 0

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(num_messages=st.integers(min_value=1, max_value=15))
    @settings(max_examples=50, deadline=None)
    async def test_context_includes_recent_messages_up_to_limit(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        num_messages: int
    ):
        """Property test: Context includes up to 10 most recent messages."""
        # Feature: rootlearn-knowledge-debugger, Property 36: Tutor context completeness
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current",
            description="Current",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add messages
        for i in range(num_messages):
            msg = TutorMessage(
                session_id=test_session.id,
                concept_id=current_concept.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                hint_level=0 if i % 2 == 1 else None
            )
            db_session.add(msg)
        await db_session.flush()
        
        # Act
        service = TutorService(db_session)
        context = await service.get_tutor_context(test_session.id)
        
        # Assert - Should have at most 10 messages
        assert len(context.recent_messages) <= 10
        # Should have all messages if num_messages <= 10
        if num_messages <= 10:
            assert len(context.recent_messages) == num_messages


class TestProperty37TutorMessagePersistence:
    """Property 37: Tutor message persistence.
    
    For any tutor interaction (user or assistant message), a tutor_messages
    record should be created with role, content, and timestamp.
    
    Validates: Requirements 9.6
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(user_message=user_message_text())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_user_and_assistant_messages_are_persisted(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        user_message: str
    ):
        """Property test: Both user and assistant messages are persisted."""
        # Feature: rootlearn-knowledge-debugger, Property 37: Tutor message persistence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current",
            description="Current",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial message
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting",
            hint_level=0
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Count messages before
        messages_before_result = await db_session.execute(
            select(TutorMessage).where(TutorMessage.session_id == test_session.id)
        )
        messages_before = len(list(messages_before_result.scalars().all()))
        
        # Mock AI provider
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                yield "Assistant response"
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            # Act
            service = TutorService(db_session)
            await service.generate_response(
                session_id=test_session.id,
                user_message=user_message
            )
            
            # Assert - Should have 2 new messages (user + assistant)
            messages_after_result = await db_session.execute(
                select(TutorMessage).where(TutorMessage.session_id == test_session.id)
            )
            messages_after = list(messages_after_result.scalars().all())
            
            assert len(messages_after) == messages_before + 2
            
            # Find the new messages
            new_messages = sorted(messages_after[-2:], key=lambda m: m.created_at)
            
            # First should be user message
            user_msg = new_messages[0]
            assert user_msg.role == "user"
            assert user_msg.content == user_message
            assert user_msg.concept_id == current_concept.id
            assert user_msg.hint_level is None
            
            # Second should be assistant message
            assistant_msg = new_messages[1]
            assert assistant_msg.role == "assistant"
            assert len(assistant_msg.content) > 0
            assert assistant_msg.concept_id == current_concept.id
            assert assistant_msg.hint_level is not None

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_interactions=st.integers(min_value=1, max_value=5),
        hint_level=st.integers(min_value=0, max_value=4)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_messages_have_required_fields(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        num_interactions: int,
        hint_level: int
    ):
        """Property test: All persisted messages have required fields."""
        # Feature: rootlearn-knowledge-debugger, Property 37: Tutor message persistence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current",
            description="Current",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial message
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting",
            hint_level=hint_level
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Mock AI provider
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                yield "Response"
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            service = TutorService(db_session)
            
            # Act - Generate multiple interactions
            for i in range(num_interactions):
                await service.generate_response(
                    session_id=test_session.id,
                    user_message=f"Question {i}"
                )
            
            # Assert - All messages have required fields
            messages_result = await db_session.execute(
                select(TutorMessage).where(TutorMessage.session_id == test_session.id)
            )
            all_messages = list(messages_result.scalars().all())
            
            for msg in all_messages:
                # Required fields
                assert msg.id is not None
                assert msg.session_id == test_session.id
                assert msg.concept_id is not None
                assert msg.role in ["user", "assistant", "system"]
                assert msg.content is not None
                assert len(msg.content) > 0
                assert msg.created_at is not None
                
                # Hint level only for assistant messages
                if msg.role == "assistant":
                    assert msg.hint_level is not None
                    assert 0 <= msg.hint_level <= 4
                elif msg.role == "user":
                    assert msg.hint_level is None


class TestProperty38TutoringUpdatesPracticeEvidence:
    """Property 38: Tutoring updates practice evidence.
    
    For any completed tutoring interaction, practice evidence scores
    should be updated for the concept being taught.
    
    Validates: Requirements 9.8
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(num_interactions=st.integers(min_value=3, max_value=12))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_practice_evidence_updated_after_interactions(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        num_interactions: int
    ):
        """Property test: Practice evidence is updated after tutoring interactions."""
        # Feature: rootlearn-knowledge-debugger, Property 38: Tutoring updates practice evidence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current",
            description="Current",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial message
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting",
            hint_level=0
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Record initial mastery
        initial_mastery = current_concept.mastery_score
        
        # Count mastery events before
        events_before_result = await db_session.execute(
            select(MasteryEvent).where(
                MasteryEvent.concept_id == current_concept.id,
                MasteryEvent.source_type == "tutoring"
            )
        )
        events_before_count = len(list(events_before_result.scalars().all()))
        
        # Mock AI provider
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                yield "Assistant response"
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            service = TutorService(db_session)
            
            # Act - Generate interactions (updates happen every 3 messages)
            for i in range(num_interactions):
                await service.generate_response(
                    session_id=test_session.id,
                    user_message=f"User message {i}"
                )
            
            # Assert - Practice evidence should be updated
            # Updates happen every 3 user messages
            expected_updates = num_interactions // 3
            
            if expected_updates > 0:
                # Should have mastery events for practice evidence
                events_after_result = await db_session.execute(
                    select(MasteryEvent).where(
                        MasteryEvent.concept_id == current_concept.id,
                        MasteryEvent.source_type == "tutoring"
                    )
                )
                events_after = list(events_after_result.scalars().all())
                
                # Should have at least one new mastery event
                assert len(events_after) > events_before_count
                
                # Verify mastery events have practice evidence
                for event in events_after:
                    assert event.source_type == "tutoring"
                    assert event.reason_json is not None
                    assert "interaction_count" in event.reason_json or "practice_score" in event.reason_json

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        message_length=st.integers(min_value=10, max_value=200),
        hint_level=st.integers(min_value=0, max_value=4)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_practice_score_influenced_by_interaction_quality(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        message_length: int,
        hint_level: int
    ):
        """Property test: Practice scoring considers interaction quality."""
        # Feature: rootlearn-knowledge-debugger, Property 38: Tutoring updates practice evidence
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="tutoring"
        )
        
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.50"),
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        current_concept = Concept(
            session_id=test_session.id,
            slug="current",
            name="Current",
            description="Current",
            mastery_score=Decimal("0.40"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(current_concept)
        await db_session.flush()
        
        test_session.target_concept_id = target_concept.id
        test_session.status = "tutoring"
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=current_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Add initial message with specific hint level
        initial_msg = TutorMessage(
            session_id=test_session.id,
            concept_id=current_concept.id,
            role="system",
            content="Starting",
            hint_level=hint_level
        )
        db_session.add(initial_msg)
        await db_session.flush()
        
        # Mock AI provider
        with patch('app.services.tutor_service.get_ai_provider') as mock_get_provider:
            mock_provider = MagicMock()
            
            async def mock_stream():
                yield "Response"
            
            mock_provider.stream_text.side_effect = lambda **_: mock_stream()
            mock_get_provider.return_value = mock_provider
            
            service = TutorService(db_session)
            
            # Act - Generate exactly 3 interactions to trigger mastery update
            for i in range(3):
                user_msg = "x" * message_length  # Message of specified length
                await service.generate_response(
                    session_id=test_session.id,
                    user_message=user_msg
                )
            
            # Assert - Should have created mastery event with practice evidence
            events_result = await db_session.execute(
                select(MasteryEvent).where(
                    MasteryEvent.concept_id == current_concept.id,
                    MasteryEvent.source_type == "tutoring"
                )
            )
            events = list(events_result.scalars().all())
            
            # Should have at least one event
            assert len(events) > 0
            
            # Latest event should have practice score info
            latest_event = events[-1]
            assert latest_event.source_type == "tutoring"
            assert latest_event.reason_json is not None
            
            # Practice score should be in valid range
            if "practice_score" in latest_event.reason_json:
                practice_score = latest_event.reason_json["practice_score"]
                assert 0.0 <= practice_score <= 1.0
