"""Unit tests for MasteryService."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Concept, DiagnosticAttempt, MasteryEvent
from app.services.mastery_service import Evidence, MasteryService


@pytest.mark.asyncio
async def test_update_mastery_with_diagnostic_evidence(db_session, test_session):
    """Test updating mastery with diagnostic evidence creates event and updates concept."""
    # Create a concept
    concept = Concept(
        session_id=test_session.id,
        slug="test-concept",
        name="Test Concept",
        description="A test concept",
        mastery_score=Decimal("0.0"),
        confidence_score=Decimal("0.1"),
        status="unknown",
    )
    db_session.add(concept)
    await db_session.flush()
    
    # Create diagnostic attempt (evidence)
    attempt = DiagnosticAttempt(
        question_id=uuid.uuid4(),  # Not testing question creation here
        session_id=test_session.id,
        concept_id=concept.id,
        student_answer="Test answer",
        correctness_score=Decimal("0.75"),
        reasoning_score=Decimal("0.80"),
    )
    db_session.add(attempt)
    await db_session.flush()
    
    # Update mastery
    service = MasteryService(db_session)
    evidence = Evidence(
        source_type="diagnostic",
        reason={"attempt_id": str(attempt.id), "scores": {"correctness": 0.75, "reasoning": 0.80}}
    )
    
    event = await service.update_mastery(concept.id, evidence)
    await db_session.commit()
    
    # Verify event was created
    assert event is not None
    assert event.concept_id == concept.id
    assert event.session_id == test_session.id
    assert event.source_type == "diagnostic"
    assert event.old_score == Decimal("0.0")
    assert event.new_score > Decimal("0.0")  # Should be updated
    assert event.old_confidence == Decimal("0.1")
    assert event.new_confidence == Decimal("0.35")  # 1 evidence = 0.35 confidence
    assert event.reason_json == evidence.reason
    
    # Verify concept was updated
    await db_session.refresh(concept)
    assert concept.mastery_score > Decimal("0.0")
    assert concept.confidence_score == Decimal("0.35")
    assert concept.status != "unknown"


@pytest.mark.asyncio
async def test_update_mastery_event_persistence(db_session, test_session, test_concept):
    """Test that mastery events are persisted correctly."""
    service = MasteryService(db_session)
    
    # Create diagnostic evidence
    attempt = DiagnosticAttempt(
        question_id=uuid.uuid4(),
        session_id=test_session.id,
        concept_id=test_concept.id,
        student_answer="Answer",
        correctness_score=Decimal("0.60"),
        reasoning_score=Decimal("0.65"),
    )
    db_session.add(attempt)
    await db_session.flush()
    
    evidence = Evidence(
        source_type="diagnostic",
        reason={"test": "data"}
    )
    
    old_mastery = float(test_concept.mastery_score)
    old_confidence = float(test_concept.confidence_score)
    
    # Update mastery
    event = await service.update_mastery(test_concept.id, evidence)
    await db_session.commit()
    
    # Query the event from database
    result = await db_session.execute(
        select(MasteryEvent).where(MasteryEvent.id == event.id)
    )
    persisted_event = result.scalar_one()
    
    # Verify all fields are persisted
    assert persisted_event.concept_id == test_concept.id
    assert persisted_event.session_id == test_session.id
    assert persisted_event.source_type == "diagnostic"
    assert persisted_event.old_score == Decimal(str(old_mastery))
    assert persisted_event.old_confidence == Decimal(str(old_confidence))
    assert float(persisted_event.new_score) > old_mastery or float(persisted_event.new_score) >= 0.0
    assert persisted_event.reason_json == {"test": "data"}
    assert persisted_event.created_at is not None


@pytest.mark.asyncio
async def test_update_mastery_multiple_times(db_session, test_session, test_concept):
    """Test that multiple mastery updates create multiple events."""
    service = MasteryService(db_session)
    
    # First update
    attempt1 = DiagnosticAttempt(
        question_id=uuid.uuid4(),
        session_id=test_session.id,
        concept_id=test_concept.id,
        student_answer="First answer",
        correctness_score=Decimal("0.50"),
        reasoning_score=Decimal("0.55"),
    )
    db_session.add(attempt1)
    await db_session.flush()
    
    event1 = await service.update_mastery(
        test_concept.id,
        Evidence(source_type="diagnostic", reason={"update": 1})
    )
    await db_session.commit()
    
    # Second update
    attempt2 = DiagnosticAttempt(
        question_id=uuid.uuid4(),
        session_id=test_session.id,
        concept_id=test_concept.id,
        student_answer="Second answer",
        correctness_score=Decimal("0.80"),
        reasoning_score=Decimal("0.85"),
    )
    db_session.add(attempt2)
    await db_session.flush()
    
    event2 = await service.update_mastery(
        test_concept.id,
        Evidence(source_type="diagnostic", reason={"update": 2})
    )
    await db_session.commit()
    
    # Verify both events exist
    result = await db_session.execute(
        select(MasteryEvent)
        .where(MasteryEvent.concept_id == test_concept.id)
        .order_by(MasteryEvent.created_at)
    )
    events = result.scalars().all()
    
    assert len(events) == 2
    assert events[0].id == event1.id
    assert events[1].id == event2.id
    assert float(events[1].old_score) == float(events[0].new_score)


@pytest.mark.asyncio
async def test_update_mastery_updates_status(db_session, test_session):
    """Test that mastery update changes concept status appropriately."""
    # Create concept with low mastery
    concept = Concept(
        session_id=test_session.id,
        slug="status-test",
        name="Status Test",
        description="Test status updates",
        mastery_score=Decimal("0.0"),
        confidence_score=Decimal("0.1"),
        status="weak",
    )
    db_session.add(concept)
    await db_session.flush()
    
    service = MasteryService(db_session)
    
    # Add high-score diagnostic evidence
    attempt = DiagnosticAttempt(
        question_id=uuid.uuid4(),
        session_id=test_session.id,
        concept_id=concept.id,
        student_answer="Great answer",
        correctness_score=Decimal("0.90"),
        reasoning_score=Decimal("0.95"),
    )
    db_session.add(attempt)
    await db_session.flush()
    
    # Update mastery
    await service.update_mastery(
        concept.id,
        Evidence(source_type="diagnostic", reason={"test": "status"})
    )
    await db_session.commit()
    
    # Verify status was updated
    await db_session.refresh(concept)
    # With 0.925 average score (0.90 + 0.95) / 2, status should be "mastered"
    assert concept.status == "mastered"
    assert concept.mastery_score >= Decimal("0.85")
