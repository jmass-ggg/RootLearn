"""Small persistence helpers shared by database-backed tests."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiagnosticAttempt, DiagnosticQuestion, LearningSession


async def add_learning_session(
    db: AsyncSession,
    *,
    user_id: UUID,
    status: str = "analyzing",
) -> LearningSession:
    """Create a distinct session for one generated property-test example."""
    session = LearningSession(
        user_id=user_id,
        original_prompt="Property-test learning session",
        status=status,
    )
    db.add(session)
    await db.flush()
    return session


async def add_diagnostic_attempt(
    db: AsyncSession,
    *,
    session_id: UUID,
    concept_id: UUID,
    student_answer: str,
    correctness_score: Decimal,
    reasoning_score: Decimal,
) -> DiagnosticAttempt:
    """Create a valid diagnostic question and its associated attempt."""
    question = DiagnosticQuestion(
        session_id=session_id,
        concept_id=concept_id,
        question_text="Test diagnostic question",
        question_type="short_answer",
        rubric_json={"required_points": ["test point"]},
        difficulty=Decimal("0.5"),
    )
    db.add(question)
    await db.flush()

    attempt = DiagnosticAttempt(
        question_id=question.id,
        session_id=session_id,
        concept_id=concept_id,
        student_answer=student_answer,
        correctness_score=correctness_score,
        reasoning_score=reasoning_score,
    )
    db.add(attempt)
    return attempt
