"""SQLAlchemy models for RootLearn."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    learning_sessions: Mapped[list["LearningSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class LearningSession(Base):
    """Learning session model."""

    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('analyzing', 'diagnosing', 'tutoring', 'teachback', 'completed', 'abandoned')",
            name="ck_learning_sessions_status",
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="learning_sessions")
    target_concept: Mapped[Optional["Concept"]] = relationship(
        foreign_keys=[target_concept_id], post_update=True
    )
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        foreign_keys="[Concept.session_id]",
    )
    concept_edges: Mapped[list["ConceptEdge"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    diagnostic_questions: Mapped[list["DiagnosticQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    diagnostic_attempts: Mapped[list["DiagnosticAttempt"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    tutor_messages: Mapped[list["TutorMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    teachback_attempts: Mapped[list["TeachBackAttempt"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    mastery_events: Mapped[list["MasteryEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    ai_runs: Mapped[list["AIRun"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Concept(Base):
    """Concept model."""

    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_target: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    mastery_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="0.0"
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="0.1"
    )
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="'unknown'")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "mastery_score >= 0 AND mastery_score <= 1",
            name="ck_concepts_mastery_score_bounds",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_concepts_confidence_score_bounds",
        ),
        CheckConstraint(
            "status IN ('unknown', 'weak', 'learning', 'understood', 'mastered', 'locked')",
            name="ck_concepts_status",
        ),
        UniqueConstraint("session_id", "slug", name="uq_concepts_session_slug"),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(
        back_populates="concepts", foreign_keys=[session_id]
    )
    outgoing_edges: Mapped[list["ConceptEdge"]] = relationship(
        back_populates="source_concept",
        foreign_keys="[ConceptEdge.source_concept_id]",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list["ConceptEdge"]] = relationship(
        back_populates="target_concept",
        foreign_keys="[ConceptEdge.target_concept_id]",
        cascade="all, delete-orphan",
    )
    diagnostic_questions: Mapped[list["DiagnosticQuestion"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    diagnostic_attempts: Mapped[list["DiagnosticAttempt"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    tutor_messages: Mapped[list["TutorMessage"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    teachback_attempts: Mapped[list["TeachBackAttempt"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    mastery_events: Mapped[list["MasteryEvent"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )


class ConceptEdge(Base):
    """Concept prerequisite edge model."""

    __tablename__ = "concept_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    importance_weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="1.0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "source_concept_id != target_concept_id",
            name="ck_concept_edges_no_self_loop",
        ),
        CheckConstraint(
            "importance_weight >= 0 AND importance_weight <= 1",
            name="ck_concept_edges_weight_bounds",
        ),
        UniqueConstraint(
            "source_concept_id", "target_concept_id", name="uq_concept_edges_source_target"
        ),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(back_populates="concept_edges")
    source_concept: Mapped["Concept"] = relationship(
        back_populates="outgoing_edges", foreign_keys=[source_concept_id]
    )
    target_concept: Mapped["Concept"] = relationship(
        back_populates="incoming_edges", foreign_keys=[target_concept_id]
    )


class AIRun(Base):
    """AI execution log model."""

    __tablename__ = "ai_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    purpose: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    input_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    session: Mapped[Optional["LearningSession"]] = relationship(back_populates="ai_runs")


class DiagnosticQuestion(Base):
    """Diagnostic question model."""

    __tablename__ = "diagnostic_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    rubric_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    difficulty: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, server_default="0.5")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('short_answer', 'multiple_choice', 'reasoning', 'code')",
            name="ck_diagnostic_questions_type",
        ),
        CheckConstraint(
            "difficulty >= 0 AND difficulty <= 1",
            name="ck_diagnostic_questions_difficulty_bounds",
        ),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(back_populates="diagnostic_questions")
    concept: Mapped["Concept"] = relationship(back_populates="diagnostic_questions")
    attempts: Mapped[list["DiagnosticAttempt"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class DiagnosticAttempt(Base):
    """Diagnostic attempt model."""

    __tablename__ = "diagnostic_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("diagnostic_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_answer: Mapped[str] = mapped_column(Text, nullable=False)
    correctness_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reasoning_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    misconceptions_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    missing_points_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "correctness_score >= 0 AND correctness_score <= 1",
            name="ck_diagnostic_attempts_correctness_bounds",
        ),
        CheckConstraint(
            "reasoning_score >= 0 AND reasoning_score <= 1",
            name="ck_diagnostic_attempts_reasoning_bounds",
        ),
    )

    # Relationships
    question: Mapped["DiagnosticQuestion"] = relationship(back_populates="attempts")
    session: Mapped["LearningSession"] = relationship(back_populates="diagnostic_attempts")
    concept: Mapped["Concept"] = relationship(back_populates="diagnostic_attempts")
    ai_run: Mapped[Optional["AIRun"]] = relationship()


class TutorMessage(Base):
    """Tutor message model."""

    __tablename__ = "tutor_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hint_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_tutor_messages_role",
        ),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(back_populates="tutor_messages")
    concept: Mapped["Concept"] = relationship(back_populates="tutor_messages")
    ai_run: Mapped[Optional["AIRun"]] = relationship()


class TeachBackAttempt(Base):
    """Teach-back attempt model."""

    __tablename__ = "teachback_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reasoning_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    clarity_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    misconceptions_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    missing_points_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "coverage_score >= 0 AND coverage_score <= 1",
            name="ck_teachback_attempts_coverage_bounds",
        ),
        CheckConstraint(
            "reasoning_score >= 0 AND reasoning_score <= 1",
            name="ck_teachback_attempts_reasoning_bounds",
        ),
        CheckConstraint(
            "clarity_score >= 0 AND clarity_score <= 1",
            name="ck_teachback_attempts_clarity_bounds",
        ),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(back_populates="teachback_attempts")
    concept: Mapped["Concept"] = relationship(back_populates="teachback_attempts")
    ai_run: Mapped[Optional["AIRun"]] = relationship()


class MasteryEvent(Base):
    """Mastery event model."""

    __tablename__ = "mastery_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    old_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    new_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    old_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    new_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reason_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('diagnostic', 'tutoring', 'teachback', 'manual')",
            name="ck_mastery_events_source_type",
        ),
        CheckConstraint(
            "old_score >= 0 AND old_score <= 1",
            name="ck_mastery_events_old_score_bounds",
        ),
        CheckConstraint(
            "new_score >= 0 AND new_score <= 1",
            name="ck_mastery_events_new_score_bounds",
        ),
        CheckConstraint(
            "old_confidence >= 0 AND old_confidence <= 1",
            name="ck_mastery_events_old_confidence_bounds",
        ),
        CheckConstraint(
            "new_confidence >= 0 AND new_confidence <= 1",
            name="ck_mastery_events_new_confidence_bounds",
        ),
    )

    # Relationships
    session: Mapped["LearningSession"] = relationship(back_populates="mastery_events")
    concept: Mapped["Concept"] = relationship(back_populates="mastery_events")
