"""Property-based tests for mastery engine.

Feature: rootlearn-knowledge-debugger
Tests Properties 19-25: Mastery calculation properties
Validates: Requirements 6.1, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10
"""
import uuid
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, TeachBackAttempt
from app.services.mastery_service import MasteryService, MasteryStatus, Evidence
from tests.factories import add_diagnostic_attempt


# Hypothesis strategies for generating test data
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0 with 4 decimal places."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def evidence_scores(draw):
    """Generate a set of evidence scores for diagnostic, practice, and teachback."""
    return {
        "diagnostic": draw(st.lists(valid_score(), min_size=0, max_size=5)),
        "teachback": draw(st.lists(valid_score(), min_size=0, max_size=5)),
    }


class TestProperty19MasteryCalculationIsDeterministic:
    """Property 19: Mastery calculation is deterministic.
    
    For any fixed set of evidence (diagnostic, tutoring, teach-back scores),
    calculating mastery multiple times should always return the same value.
    
    Validates: Requirements 6.1
    """

    @pytest.mark.asyncio
    @given(scores=evidence_scores())
    @settings(max_examples=100, deadline=None)
    async def test_mastery_calculation_is_deterministic(
        self,
        db_session: AsyncSession,
        test_session,
        scores: dict
    ):
        """Property test: Same evidence produces same mastery score every time."""
        # Arrange - Create a concept
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add diagnostic evidence
        for i, score in enumerate(scores["diagnostic"]):
            await add_diagnostic_attempt(
                db_session,
                session_id=test_session.id,
                concept_id=concept.id,
                student_answer=f"Answer {i}",
                correctness_score=score,
                reasoning_score=score,
            )
        
        # Add teachback evidence
        for i, score in enumerate(scores["teachback"]):
            attempt = TeachBackAttempt(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation=f"Explanation {i}",
                coverage_score=score,
                reasoning_score=score,
                clarity_score=score,
            )
            db_session.add(attempt)
        
        await db_session.flush()
        
        # Act - Calculate mastery multiple times
        service = MasteryService(db_session)
        mastery1 = await service.calculate_mastery(concept.id)
        mastery2 = await service.calculate_mastery(concept.id)
        mastery3 = await service.calculate_mastery(concept.id)
        
        # Assert - All calculations should produce the same result
        assert mastery1 == mastery2 == mastery3
        assert 0.0 <= mastery1 <= 1.0


class TestProperty20EvidenceBasedMasteryFormula:
    """Property 20: Evidence-based mastery formula.
    
    For any concept with all three evidence types (diagnostic_score=d, practice_score=p,
    teachback_score=t), mastery should equal 0.45×d + 0.35×p + 0.20×t.
    
    Validates: Requirements 6.5
    """

    @pytest.mark.asyncio
    @given(
        diagnostic_score=valid_score(),
        teachback_score=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_mastery_formula_with_all_evidence(
        self,
        db_session: AsyncSession,
        test_session,
        diagnostic_score: Decimal,
        teachback_score: Decimal
    ):
        """Property test: Mastery formula is applied correctly with all evidence types."""
        # Arrange - Create concept with all three evidence types
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add diagnostic evidence
        await add_diagnostic_attempt(
            db_session,
            session_id=test_session.id,
            concept_id=concept.id,
            student_answer="Diagnostic answer",
            correctness_score=diagnostic_score,
            reasoning_score=diagnostic_score,
        )
        
        # Add teachback evidence
        teachback_attempt = TeachBackAttempt(
            session_id=test_session.id,
            concept_id=concept.id,
            student_explanation="Teachback explanation",
            coverage_score=teachback_score,
            reasoning_score=teachback_score,
            clarity_score=teachback_score,
        )
        db_session.add(teachback_attempt)
        
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        calculated_mastery = await service.calculate_mastery(concept.id)
        
        # Assert - Calculate expected mastery manually
        # Note: Practice weight is currently 0 in MVP, so we only test diagnostic + teachback
        # The formula should renormalize: 0.45/(0.45+0.20) for diagnostic, 0.20/(0.45+0.20) for teachback
        diagnostic_weight_normalized = Decimal("0.45") / (Decimal("0.45") + Decimal("0.20"))
        teachback_weight_normalized = Decimal("0.20") / (Decimal("0.45") + Decimal("0.20"))
        
        expected_mastery = (
            diagnostic_weight_normalized * diagnostic_score +
            teachback_weight_normalized * teachback_score
        )
        
        # Allow small floating point difference
        assert abs(calculated_mastery - float(expected_mastery)) < 0.0001
        assert 0.0 <= calculated_mastery <= 1.0


class TestProperty21PartialEvidenceWeightRenormalization:
    """Property 21: Partial evidence weight renormalization.
    
    For any concept with only a subset of evidence types available,
    the weights used should sum to 1.0.
    
    Validates: Requirements 6.6
    """

    @pytest.mark.asyncio
    @given(diagnostic_score=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_partial_evidence_weights_sum_to_one_diagnostic_only(
        self,
        db_session: AsyncSession,
        test_session,
        diagnostic_score: Decimal
    ):
        """Property test: With only diagnostic evidence, weight should be 1.0."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add only diagnostic evidence
        await add_diagnostic_attempt(
            db_session,
            session_id=test_session.id,
            concept_id=concept.id,
            student_answer="Answer",
            correctness_score=diagnostic_score,
            reasoning_score=diagnostic_score,
        )
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        calculated_mastery = await service.calculate_mastery(concept.id)
        
        # Assert - With only diagnostic evidence, mastery should equal diagnostic score
        # (weight = 1.0 after renormalization)
        expected_mastery = diagnostic_score
        assert abs(calculated_mastery - float(expected_mastery)) < 0.0001
        assert 0.0 <= calculated_mastery <= 1.0

    @pytest.mark.asyncio
    @given(teachback_score=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_partial_evidence_weights_sum_to_one_teachback_only(
        self,
        db_session: AsyncSession,
        test_session,
        teachback_score: Decimal
    ):
        """Property test: With only teachback evidence, weight should be 1.0."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add only teachback evidence
        teachback_attempt = TeachBackAttempt(
            session_id=test_session.id,
            concept_id=concept.id,
            student_explanation="Explanation",
            coverage_score=teachback_score,
            reasoning_score=teachback_score,
            clarity_score=teachback_score,
        )
        db_session.add(teachback_attempt)
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        calculated_mastery = await service.calculate_mastery(concept.id)
        
        # Assert - With only teachback evidence, mastery should equal teachback score
        expected_mastery = teachback_score
        assert abs(calculated_mastery - float(expected_mastery)) < 0.0001
        assert 0.0 <= calculated_mastery <= 1.0


class TestProperty22MasteryScoreBoundsInvariant:
    """Property 22: Mastery score bounds invariant.
    
    For any evidence inputs and mastery calculation, the resulting mastery_score
    should satisfy 0.0 ≤ mastery_score ≤ 1.0.
    
    Note: This property is also tested in test_database_constraints.py for database enforcement.
    Here we test the calculation logic itself.
    
    Validates: Requirements 6.7
    """

    @pytest.mark.asyncio
    @given(scores=evidence_scores())
    @settings(max_examples=100, deadline=None)
    async def test_mastery_score_always_in_bounds(
        self,
        db_session: AsyncSession,
        test_session,
        scores: dict
    ):
        """Property test: Calculated mastery is always between 0.0 and 1.0."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add all evidence
        for score in scores["diagnostic"]:
            await add_diagnostic_attempt(
                db_session,
                session_id=test_session.id,
                concept_id=concept.id,
                student_answer="Answer",
                correctness_score=score,
                reasoning_score=score,
            )
        
        for score in scores["teachback"]:
            attempt = TeachBackAttempt(
                session_id=test_session.id,
                concept_id=concept.id,
                student_explanation="Explanation",
                coverage_score=score,
                reasoning_score=score,
                clarity_score=score,
            )
            db_session.add(attempt)
        
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        calculated_mastery = await service.calculate_mastery(concept.id)
        
        # Assert
        assert 0.0 <= calculated_mastery <= 1.0


class TestProperty23ConfidenceFromEvidenceQuantity:
    """Property 23: Confidence from evidence quantity.
    
    For any concept with n diagnostic attempts, confidence should match:
    n=0→0.10, n=1→0.35, n=2→0.60, n=3→0.80, n≥4→0.90.
    
    Validates: Requirements 6.8
    """

    @pytest.mark.asyncio
    @given(num_attempts=st.integers(min_value=0, max_value=10))
    @settings(max_examples=50, deadline=None)
    async def test_confidence_maps_to_evidence_count(
        self,
        db_session: AsyncSession,
        test_session,
        num_attempts: int
    ):
        """Property test: Confidence score matches evidence count mapping."""
        # Arrange
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Add diagnostic attempts
        for i in range(num_attempts):
            await add_diagnostic_attempt(
                db_session,
                session_id=test_session.id,
                concept_id=concept.id,
                student_answer=f"Answer {i}",
                correctness_score=Decimal("0.5"),
                reasoning_score=Decimal("0.5"),
            )
        
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        calculated_confidence = await service.calculate_confidence(concept.id)
        
        # Assert - Map to expected confidence
        expected_confidence_map = {
            0: 0.10,
            1: 0.35,
            2: 0.60,
            3: 0.80,
        }
        expected_confidence = expected_confidence_map.get(num_attempts, 0.90)
        
        assert calculated_confidence == expected_confidence


class TestProperty24MasteryStatusBandMapping:
    """Property 24: Mastery status band mapping.
    
    For any mastery score m, status should be:
    - weak if m<0.40
    - learning if 0.40≤m<0.70
    - understood if 0.70≤m<0.85
    - mastered if m≥0.85
    
    Validates: Requirements 6.9
    """

    @pytest.mark.asyncio
    @given(mastery_score=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_mastery_status_band_mapping(
        self,
        mastery_score: Decimal
    ):
        """Property test: Mastery score maps correctly to status bands."""
        # Arrange
        service = MasteryService(None)  # No db needed for this pure function
        
        # Act
        status = service.get_mastery_status(float(mastery_score))
        
        # Assert - Check status matches expected band
        if mastery_score < Decimal("0.40"):
            assert status == MasteryStatus.WEAK
        elif mastery_score < Decimal("0.70"):
            assert status == MasteryStatus.LEARNING
        elif mastery_score < Decimal("0.85"):
            assert status == MasteryStatus.UNDERSTOOD
        else:
            assert status == MasteryStatus.MASTERED


class TestProperty25PrerequisiteBasedLocking:
    """Property 25: Prerequisite-based locking.
    
    For any concept with one or more prerequisites having mastery < 0.70,
    the concept should have status "locked".
    
    Validates: Requirements 6.10
    """

    @pytest.mark.asyncio
    @given(
        prereq_mastery=valid_score(),
        has_prerequisite=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    async def test_concept_locked_when_prerequisite_not_met(
        self,
        db_session: AsyncSession,
        test_session,
        prereq_mastery: Decimal,
        has_prerequisite: bool
    ):
        """Property test: Concepts are locked when prerequisites have low mastery."""
        # Arrange - Create target concept
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="Target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.flush()
        
        # Optionally create prerequisite
        if has_prerequisite:
            prereq_concept = Concept(
                session_id=test_session.id,
                slug=f"prereq-{uuid.uuid4()}",
                name="Prerequisite Concept",
                description="Prerequisite",
                mastery_score=prereq_mastery,
                confidence_score=Decimal("0.8"),
                status="learning"
            )
            db_session.add(prereq_concept)
            await db_session.flush()
            
            # Create edge from prerequisite to target
            edge = ConceptEdge(
                session_id=test_session.id,
                source_concept_id=prereq_concept.id,
                target_concept_id=target_concept.id,
                importance_weight=Decimal("0.8")
            )
            db_session.add(edge)
            await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        is_locked = await service.is_concept_locked(target_concept.id)
        
        # Assert
        if has_prerequisite:
            # Locked if prerequisite mastery < 0.70
            expected_locked = prereq_mastery < Decimal("0.70")
            assert is_locked == expected_locked
        else:
            # Not locked if no prerequisites
            assert is_locked is False

    @pytest.mark.asyncio
    async def test_concept_with_multiple_prerequisites_any_below_threshold(
        self,
        db_session: AsyncSession,
        test_session
    ):
        """Property test: Concept is locked if ANY prerequisite is below threshold."""
        # Arrange - Create target concept
        target_concept = Concept(
            session_id=test_session.id,
            slug=f"target-{uuid.uuid4()}",
            name="Target Concept",
            description="Target concept",
            status="learning"
        )
        db_session.add(target_concept)
        await db_session.flush()
        
        # Create first prerequisite with high mastery
        prereq1 = Concept(
            session_id=test_session.id,
            slug=f"prereq1-{uuid.uuid4()}",
            name="Prereq 1",
            description="First prerequisite",
            mastery_score=Decimal("0.85"),
            confidence_score=Decimal("0.9"),
            status="mastered"
        )
        db_session.add(prereq1)
        
        # Create second prerequisite with low mastery
        prereq2 = Concept(
            session_id=test_session.id,
            slug=f"prereq2-{uuid.uuid4()}",
            name="Prereq 2",
            description="Second prerequisite",
            mastery_score=Decimal("0.30"),
            confidence_score=Decimal("0.8"),
            status="weak"
        )
        db_session.add(prereq2)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq1.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.8")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq2.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.9")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = MasteryService(db_session)
        is_locked = await service.is_concept_locked(target_concept.id)
        
        # Assert - Should be locked because prereq2 has mastery < 0.70
        assert is_locked is True
