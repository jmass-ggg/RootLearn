"""Teach-back evaluation service for RootLearn.

This service implements teach-back verification where learners explain concepts
in their own words to verify understanding. AI evaluates the explanations for
coverage, reasoning, and clarity.
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import (
    TEACHBACK_EVALUATION_SYSTEM_PROMPT,
    TEACHBACK_EVALUATION_VERSION,
    get_teachback_evaluation_user_prompt,
)
from app.ai.schemas import TeachBackEvaluationOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.logging_config import get_logger
from app.models import Concept, LearningSession, TeachBackAttempt
from app.services.mastery_service import Evidence, MasteryService

logger = get_logger(__name__)


@dataclass
class TeachBackResult:
    """Result of teach-back evaluation."""
    
    attempt_id: uuid.UUID
    concept_id: uuid.UUID
    coverage_score: float
    reasoning_score: float
    clarity_score: float
    average_score: float
    demonstrated_points: list[str]
    missing_points: list[str]
    misconceptions: list[str]
    should_continue_tutoring: bool


class TeachBackService:
    """Service for teach-back evaluation and verification.
    
    Implements teach-back assessment where learners explain concepts in their
    own words. AI evaluates explanations across three dimensions:
    - Coverage: completeness of key ideas
    - Reasoning: logical correctness
    - Clarity: communication effectiveness
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    
    # Threshold for sufficient understanding
    SUFFICIENT_MASTERY_THRESHOLD = 0.70

    def __init__(
        self,
        db: AsyncSession,
        ai_service: ValidatedAIService,
        mastery_service: MasteryService,
    ):
        """Initialize teach-back service.
        
        Args:
            db: Database session
            ai_service: Validated AI service for structured output
            mastery_service: Mastery service for updating evidence
        """
        self.db = db
        self.ai_service = ai_service
        self.mastery_service = mastery_service

    async def request_teachback(
        self,
        session_id: uuid.UUID,
        concept_id: uuid.UUID,
    ) -> None:
        """Request teach-back from the learner.
        
        Transitions session to "teachback" status and prepares for evaluation.
        This is called when tutoring concludes.
        
        Args:
            session_id: Learning session ID
            concept_id: Concept to be explained
            
        Requirements: 10.1
        """
        # Get session
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one()
        
        # Transition to teachback status
        old_status = session.status
        session.status = "teachback"
        await self.db.flush()
        
        logger.info(
            "teachback_requested",
            session_id=str(session_id),
            concept_id=str(concept_id),
            old_status=old_status,
            new_status=session.status,
        )

    async def evaluate_teachback(
        self,
        session_id: uuid.UUID,
        concept_id: uuid.UUID,
        student_explanation: str,
    ) -> TeachBackResult:
        """Evaluate teach-back explanation and update mastery.
        
        Uses AI to evaluate the learner's explanation across three dimensions:
        coverage, reasoning, and clarity. Creates teach-back attempt record
        and updates mastery engine with evidence.
        
        Args:
            session_id: Learning session ID
            concept_id: Concept being explained
            student_explanation: Learner's explanation in their own words
            
        Returns:
            TeachBackResult with scores and decision
            
        Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
        """
        # Get concept details
        concept_result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = concept_result.scalar_one()
        
        logger.info(
            "evaluating_teachback",
            session_id=str(session_id),
            concept_id=str(concept_id),
            concept_name=concept.name,
            explanation_length=len(student_explanation),
        )
        
        # Generate AI evaluation prompt
        system_prompt = TEACHBACK_EVALUATION_SYSTEM_PROMPT
        user_prompt = get_teachback_evaluation_user_prompt(
            concept_name=concept.name,
            concept_description=concept.description,
            student_explanation=student_explanation,
        )
        
        # Call AI for evaluation
        evaluation: TeachBackEvaluationOutput = await self.ai_service.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=TeachBackEvaluationOutput,
            purpose="teachback_evaluation",
            prompt_version=TEACHBACK_EVALUATION_VERSION,
            temperature=0.3,  # Lower temperature for consistent evaluation
            session_id=session_id,
        )
        
        logger.info(
            "teachback_evaluated",
            session_id=str(session_id),
            concept_id=str(concept_id),
            coverage_score=evaluation.coverage_score,
            reasoning_score=evaluation.reasoning_score,
            clarity_score=evaluation.clarity_score,
            average_score=evaluation.average_score(),
        )
        
        # Create teach-back attempt record
        attempt = TeachBackAttempt(
            session_id=session_id,
            concept_id=concept_id,
            student_explanation=student_explanation,
            coverage_score=Decimal(str(evaluation.coverage_score)),
            reasoning_score=Decimal(str(evaluation.reasoning_score)),
            clarity_score=Decimal(str(evaluation.clarity_score)),
            misconceptions_json={"misconceptions": evaluation.misconceptions} if evaluation.misconceptions else None,
            missing_points_json={"missing_points": evaluation.missing_points} if evaluation.missing_points else None,
            ai_run_id=None,  # Will be populated by logging service
        )
        
        self.db.add(attempt)
        await self.db.flush()
        await self.db.refresh(attempt)
        
        logger.info(
            "teachback_attempt_stored",
            attempt_id=str(attempt.id),
            session_id=str(session_id),
            concept_id=str(concept_id),
        )
        
        # Update mastery engine with teach-back evidence
        evidence = Evidence(
            source_type="teachback",
            reason={
                "attempt_id": str(attempt.id),
                "coverage_score": evaluation.coverage_score,
                "reasoning_score": evaluation.reasoning_score,
                "clarity_score": evaluation.clarity_score,
                "average_score": evaluation.average_score(),
                "demonstrated_points": evaluation.demonstrated_points,
                "missing_points": evaluation.missing_points,
                "misconceptions": evaluation.misconceptions,
            }
        )
        
        mastery_event = await self.mastery_service.update_mastery(
            concept_id=concept_id,
            evidence=evidence,
        )
        
        logger.info(
            "teachback_mastery_updated",
            concept_id=str(concept_id),
            old_mastery=float(mastery_event.old_score),
            new_mastery=float(mastery_event.new_score),
        )
        
        # Determine if tutoring should continue
        average_score = evaluation.average_score()
        should_continue = self.should_continue_tutoring(average_score)
        
        # Build result
        result = TeachBackResult(
            attempt_id=attempt.id,
            concept_id=concept_id,
            coverage_score=evaluation.coverage_score,
            reasoning_score=evaluation.reasoning_score,
            clarity_score=evaluation.clarity_score,
            average_score=average_score,
            demonstrated_points=evaluation.demonstrated_points,
            missing_points=evaluation.missing_points,
            misconceptions=evaluation.misconceptions,
            should_continue_tutoring=should_continue,
        )
        
        logger.info(
            "teachback_result",
            attempt_id=str(attempt.id),
            average_score=average_score,
            should_continue_tutoring=should_continue,
        )
        
        return result

    def should_continue_tutoring(self, average_score: float) -> bool:
        """Determine if tutoring should continue based on teach-back scores.
        
        If average score < 0.70, tutoring should continue.
        If average score >= 0.70, proceed to next concept or completion.
        
        Args:
            average_score: Average of coverage, reasoning, and clarity scores
            
        Returns:
            True if tutoring should continue, False if ready to proceed
            
        Requirements: 10.5, 10.6
        """
        should_continue = average_score < self.SUFFICIENT_MASTERY_THRESHOLD
        
        logger.debug(
            "teachback_decision",
            average_score=average_score,
            threshold=self.SUFFICIENT_MASTERY_THRESHOLD,
            should_continue_tutoring=should_continue,
        )
        
        return should_continue
