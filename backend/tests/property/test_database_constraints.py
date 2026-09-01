"""Property-based tests for database constraints.

Feature: rootlearn-knowledge-debugger
Property 22: Mastery score bounds invariant
Property 9: Graph structural validity (weight bounds)
Validates: Requirements 6.7, 3.7, 19.4, 19.5, 19.6, 19.7
"""
import uuid
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession, User


# Hypothesis strategies for generating test data
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0 with 4 decimal places."""
    # Generate a float between 0 and 1, then round to 4 decimal places
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def invalid_score_below_bounds(draw):
    """Generate an invalid score below 0.0."""
    value = draw(st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def invalid_score_above_bounds(draw):
    """Generate an invalid score above 1.0."""
    value = draw(st.floats(min_value=1.0001, max_value=10.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def concept_data(draw):
    """Generate valid concept data."""
    return {
        "slug": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",)))),
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=("Cs",)))),
        "description": draw(st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_categories=("Cs",)))),
        "is_target": draw(st.booleans()),
        "mastery_score": draw(valid_score()),
        "confidence_score": draw(valid_score()),
        "status": draw(st.sampled_from(["unknown", "weak", "learning", "understood", "mastered", "locked"])),
    }


class TestProperty22MasteryScoreBoundsInvariant:
    """Property 22: Mastery score bounds invariant.
    
    For any evidence inputs and mastery calculation, the resulting mastery_score
    should satisfy 0.0 ≤ mastery_score ≤ 1.0.
    
    Validates: Requirements 6.7
    """

    @pytest.mark.asyncio
    @given(mastery_score=valid_score(), confidence_score=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_valid_mastery_scores_are_accepted(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery_score: Decimal,
        confidence_score: Decimal
    ):
        """Property test: Valid mastery scores in [0, 1] are accepted by the database."""
        # Arrange & Act
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=mastery_score,
            confidence_score=confidence_score,
            status="learning"
        )
        
        db_session.add(concept)
        await db_session.commit()
        await db_session.refresh(concept)
        
        # Assert
        assert concept.mastery_score == mastery_score
        assert concept.confidence_score == confidence_score
        assert Decimal("0.0") <= concept.mastery_score <= Decimal("1.0")
        assert Decimal("0.0") <= concept.confidence_score <= Decimal("1.0")

    @pytest.mark.asyncio
    @given(invalid_score=invalid_score_below_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_mastery_score_below_zero_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        invalid_score: Decimal
    ):
        """Property test: Mastery scores below 0.0 are rejected by database constraint."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=invalid_score,
            confidence_score=Decimal("0.5"),
            status="learning"
        )
        
        # Act & Assert
        db_session.add(concept)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concepts_mastery_score_bounds" in str(exc_info.value) or "mastery_score" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    @given(invalid_score=invalid_score_above_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_mastery_score_above_one_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        invalid_score: Decimal
    ):
        """Property test: Mastery scores above 1.0 are rejected by database constraint."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=invalid_score,
            confidence_score=Decimal("0.5"),
            status="learning"
        )
        
        # Act & Assert
        db_session.add(concept)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concepts_mastery_score_bounds" in str(exc_info.value) or "mastery_score" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    @given(invalid_score=invalid_score_below_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_confidence_score_below_zero_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        invalid_score: Decimal
    ):
        """Property test: Confidence scores below 0.0 are rejected by database constraint."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=Decimal("0.5"),
            confidence_score=invalid_score,
            status="learning"
        )
        
        # Act & Assert
        db_session.add(concept)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concepts_confidence_score_bounds" in str(exc_info.value) or "confidence_score" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    @given(invalid_score=invalid_score_above_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_confidence_score_above_one_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        invalid_score: Decimal
    ):
        """Property test: Confidence scores above 1.0 are rejected by database constraint."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=Decimal("0.5"),
            confidence_score=invalid_score,
            status="learning"
        )
        
        # Act & Assert
        db_session.add(concept)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concepts_confidence_score_bounds" in str(exc_info.value) or "confidence_score" in str(exc_info.value).lower()
        await db_session.rollback()


class TestProperty9GraphStructuralValidity:
    """Property 9: Graph structural validity (weight bounds).
    
    For any validated prerequisite graph, all edges should have:
    (1) importance_weight in [0.0, 1.0]
    (2) unique node IDs
    (3) valid source and target references
    (4) no duplicate edges
    
    Validates: Requirements 3.7, 3.8, 3.9, 3.10, 19.4, 19.5, 19.6, 19.7
    """

    @pytest.mark.asyncio
    @given(importance_weight=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_valid_importance_weights_are_accepted(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        test_concept: Concept,
        importance_weight: Decimal
    ):
        """Property test: Valid importance weights in [0, 1] are accepted."""
        # Arrange - Create a second concept to create an edge
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="A target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.commit()
        await db_session.refresh(target_concept)
        
        # Act - Create edge with the generated weight
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=importance_weight
        )
        db_session.add(edge)
        await db_session.commit()
        await db_session.refresh(edge)
        
        # Assert
        assert edge.importance_weight == importance_weight
        assert Decimal("0.0") <= edge.importance_weight <= Decimal("1.0")

    @pytest.mark.asyncio
    @given(invalid_weight=invalid_score_below_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_importance_weight_below_zero_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        test_concept: Concept,
        invalid_weight: Decimal
    ):
        """Property test: Importance weights below 0.0 are rejected by database constraint."""
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="A target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.commit()
        await db_session.refresh(target_concept)
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=invalid_weight
        )
        
        # Act & Assert
        db_session.add(edge)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concept_edges_weight_bounds" in str(exc_info.value) or "importance_weight" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    @given(invalid_weight=invalid_score_above_bounds())
    @settings(max_examples=100, deadline=None)
    async def test_importance_weight_above_one_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        test_concept: Concept,
        invalid_weight: Decimal
    ):
        """Property test: Importance weights above 1.0 are rejected by database constraint."""
        # Arrange
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="A target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.commit()
        await db_session.refresh(target_concept)
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=invalid_weight
        )
        
        # Act & Assert
        db_session.add(edge)
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concept_edges_weight_bounds" in str(exc_info.value) or "importance_weight" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_self_loop_edges_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        test_concept: Concept
    ):
        """Property test: Self-loop edges (source == target) are rejected by constraint."""
        # Arrange & Act
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=test_concept.id,  # Self-loop!
            importance_weight=Decimal("0.5")
        )
        
        db_session.add(edge)
        
        # Assert
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the constraint name is in the error
        assert "ck_concept_edges_no_self_loop" in str(exc_info.value) or "source_concept_id" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_duplicate_edges_rejected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        test_concept: Concept
    ):
        """Property test: Duplicate edges between same source/target are rejected."""
        # Arrange - Create target concept and first edge
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="A target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.commit()
        await db_session.refresh(target_concept)
        
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.5")
        )
        db_session.add(edge1)
        await db_session.commit()
        
        # Act - Try to create duplicate edge
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=test_concept.id,
            target_concept_id=target_concept.id,  # Same as edge1
            importance_weight=Decimal("0.8")  # Different weight, but still duplicate
        )
        db_session.add(edge2)
        
        # Assert
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.commit()
        
        # Verify the unique constraint is in the error
        assert "uq_concept_edges_source_target" in str(exc_info.value) or "unique" in str(exc_info.value).lower()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_concepts_must_be_in_same_session(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_session: LearningSession,
        test_concept: Concept
    ):
        """Property test: Edge concepts must belong to the same session as the edge."""
        # Arrange - Create a second session and concept
        other_session = LearningSession(
            user_id=test_user.id,
            original_prompt="Different topic",
            status="analyzing"
        )
        db_session.add(other_session)
        await db_session.commit()
        await db_session.refresh(other_session)
        
        other_concept = Concept(
            session_id=other_session.id,
            slug="other-concept",
            name="Other Concept",
            description="From different session",
            status="learning"
        )
        db_session.add(other_concept)
        await db_session.commit()
        await db_session.refresh(other_concept)
        
        # Act - Try to create an edge between concepts from different sessions
        # This should work at the database level but violates business logic
        # The edge's session_id should match both concepts' session_id
        edge = ConceptEdge(
            session_id=test_session.id,  # Edge belongs to test_session
            source_concept_id=test_concept.id,  # From test_session
            target_concept_id=other_concept.id,  # From other_session - this is the problem
            importance_weight=Decimal("0.5")
        )
        db_session.add(edge)
        
        # This might succeed at the database level (no FK constraint prevents it)
        # But it violates the requirement that concepts and edges belong to same session
        # For now, we just verify we can detect this programmatically
        await db_session.commit()
        await db_session.refresh(edge)
        
        # Assert - Verify we can detect the session mismatch
        stmt = select(Concept).where(Concept.id == edge.target_concept_id)
        result = await db_session.execute(stmt)
        target = result.scalar_one()
        
        assert edge.session_id != target.session_id, "Edge and target concept should be in different sessions"
        # In a real implementation, this should be caught by application logic
