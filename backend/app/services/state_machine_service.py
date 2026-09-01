"""Session state machine service for RootLearn.

This service manages session state transitions with validation and conditional logic.
It enforces valid transition rules and implements business logic for when sessions
should progress, return to diagnosis, or complete.

Requirements: 15.1, 15.2, 15.3, 15.4
"""
import uuid
from enum import Enum
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import Concept, LearningSession

logger = get_logger(__name__)


class SessionStatus(str, Enum):
    """Session status values."""
    
    ANALYZING = "analyzing"
    DIAGNOSING = "diagnosing"
    TUTORING = "tutoring"
    TEACHBACK = "teachback"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateMachineService:
    """Service for managing session state transitions.
    
    This service enforces valid state transitions and implements conditional
    logic for determining the next state based on learning progress.
    
    Valid transitions:
    - analyzing → diagnosing
    - diagnosing → tutoring
    - diagnosing → completed (early completion)
    - tutoring → teachback
    - teachback → tutoring (insufficient mastery)
    - teachback → diagnosing (gap resolved, more gaps remain)
    - teachback → completed (path cleared)
    
    Requirements: 15.1, 15.2, 15.3, 15.4
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        SessionStatus.ANALYZING: {SessionStatus.DIAGNOSING},
        SessionStatus.DIAGNOSING: {SessionStatus.TUTORING, SessionStatus.COMPLETED},
        SessionStatus.TUTORING: {SessionStatus.TEACHBACK},
        SessionStatus.TEACHBACK: {
            SessionStatus.TUTORING,
            SessionStatus.DIAGNOSING,
            SessionStatus.COMPLETED,
        },
        SessionStatus.COMPLETED: set(),  # Terminal state
        SessionStatus.ABANDONED: set(),  # Terminal state
    }
    
    # Mastery thresholds
    UNDERSTOOD_THRESHOLD = 0.70
    HIGH_MASTERY_THRESHOLD = 0.85
    HIGH_CONFIDENCE_THRESHOLD = 0.80

    def __init__(self, db: AsyncSession):
        """Initialize state machine service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def transition_to_diagnosing(self, session_id: uuid.UUID) -> LearningSession:
        """Transition session to diagnosing state.
        
        Valid from: analyzing
        
        Args:
            session_id: ID of the session
            
        Returns:
            Updated LearningSession
            
        Raises:
            InvalidTransitionError: If current state doesn't allow this transition
            
        Requirements: 15.1
        """
        return await self._transition(
            session_id=session_id,
            to_status=SessionStatus.DIAGNOSING,
            reason="Starting diagnostic assessment",
        )

    async def transition_to_tutoring(
        self, session_id: uuid.UUID, root_gap_concept_id: uuid.UUID
    ) -> LearningSession:
        """Transition session to tutoring state.
        
        Valid from: diagnosing
        
        Args:
            session_id: ID of the session
            root_gap_concept_id: ID of the root gap concept to tutor
            
        Returns:
            Updated LearningSession
            
        Raises:
            InvalidTransitionError: If current state doesn't allow this transition
            
        Requirements: 15.1
        """
        return await self._transition(
            session_id=session_id,
            to_status=SessionStatus.TUTORING,
            reason=f"Starting tutoring for root gap concept {root_gap_concept_id}",
        )

    async def transition_to_teachback(self, session_id: uuid.UUID) -> LearningSession:
        """Transition session to teachback state.
        
        Valid from: tutoring
        
        Args:
            session_id: ID of the session
            
        Returns:
            Updated LearningSession
            
        Raises:
            InvalidTransitionError: If current state doesn't allow this transition
            
        Requirements: 15.1
        """
        return await self._transition(
            session_id=session_id,
            to_status=SessionStatus.TEACHBACK,
            reason="Requesting teach-back verification",
        )

    async def transition_after_teachback(
        self,
        session_id: uuid.UUID,
        teachback_passed: bool,
        gap_resolved: bool,
    ) -> LearningSession:
        """Transition session after teach-back evaluation.
        
        Implements conditional logic:
        - If teachback failed (average score < 0.70): return to tutoring
        - If teachback passed but gap resolved and more gaps remain: diagnosing
        - If teachback passed and path cleared: completed
        
        Valid from: teachback
        
        Args:
            session_id: ID of the session
            teachback_passed: Whether teach-back average score >= 0.70
            gap_resolved: Whether the current gap is now resolved
            
        Returns:
            Updated LearningSession
            
        Raises:
            InvalidTransitionError: If current state doesn't allow transition
            
        Requirements: 15.1, 15.2, 15.3
        """
        # Check if teach-back passed
        if not teachback_passed:
            # Return to tutoring
            logger.info(
                "teachback_failed_returning_to_tutoring",
                session_id=str(session_id),
            )
            return await self._transition(
                session_id=session_id,
                to_status=SessionStatus.TUTORING,
                reason="Teach-back insufficient, continuing tutoring",
            )
        
        # Teach-back passed, check if path is cleared
        from app.services.learning_path_service import LearningPathService
        
        learning_path_service = LearningPathService(self.db)
        path_cleared = await learning_path_service.is_path_cleared(session_id)
        
        if path_cleared:
            # All prerequisites understood, complete session
            logger.info(
                "path_cleared_completing_session",
                session_id=str(session_id),
            )
            return await self._transition(
                session_id=session_id,
                to_status=SessionStatus.COMPLETED,
                reason="All prerequisites understood, path cleared",
            )
        else:
            # More gaps remain, return to diagnosis
            logger.info(
                "gap_resolved_more_gaps_remain",
                session_id=str(session_id),
            )
            return await self._transition(
                session_id=session_id,
                to_status=SessionStatus.DIAGNOSING,
                reason="Current gap resolved, continuing diagnosis for remaining gaps",
            )

    async def check_early_completion(self, session_id: uuid.UUID) -> LearningSession | None:
        """Check if session can complete early due to high initial mastery.
        
        If diagnostic assessment reveals target concept already has mastery >= 0.85
        and confidence >= 0.80, transition directly to completed without tutoring.
        
        Valid from: diagnosing
        
        Args:
            session_id: ID of the session
            
        Returns:
            Updated LearningSession if early completion triggered, None otherwise
            
        Requirements: 15.4
        """
        # Get session
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Only check from diagnosing state
        if session.status != SessionStatus.DIAGNOSING.value:
            return None
        
        # Check if target concept exists
        if not session.target_concept_id:
            return None
        
        # Get target concept
        target_result = await self.db.execute(
            select(Concept).where(Concept.id == session.target_concept_id)
        )
        target_concept = target_result.scalar_one_or_none()
        
        if not target_concept:
            return None
        
        # Check if target has high mastery and confidence
        if (
            float(target_concept.mastery_score) >= self.HIGH_MASTERY_THRESHOLD
            and float(target_concept.confidence_score) >= self.HIGH_CONFIDENCE_THRESHOLD
        ):
            logger.info(
                "early_completion_high_initial_mastery",
                session_id=str(session_id),
                target_concept_id=str(target_concept.id),
                mastery=float(target_concept.mastery_score),
                confidence=float(target_concept.confidence_score),
            )
            
            return await self._transition(
                session_id=session_id,
                to_status=SessionStatus.COMPLETED,
                reason="Target concept already mastered with high confidence",
            )
        
        return None

    async def _transition(
        self,
        session_id: uuid.UUID,
        to_status: SessionStatus,
        reason: str,
    ) -> LearningSession:
        """Execute a state transition with validation.
        
        Validates the transition is allowed, updates the session status,
        and logs the transition.
        
        Args:
            session_id: ID of the session
            to_status: Target status
            reason: Human-readable reason for transition
            
        Returns:
            Updated LearningSession
            
        Raises:
            InvalidTransitionError: If transition is not valid
            ValueError: If session not found
            
        Requirements: 15.1
        """
        # Get current session
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        current_status = SessionStatus(session.status)
        
        # Validate transition
        if to_status not in self.VALID_TRANSITIONS.get(current_status, set()):
            logger.error(
                "invalid_state_transition",
                session_id=str(session_id),
                from_status=current_status.value,
                to_status=to_status.value,
            )
            raise InvalidTransitionError(
                f"Invalid transition from {current_status.value} to {to_status.value}"
            )
        
        # Perform transition
        old_status = session.status
        session.status = to_status.value
        
        # Set completed_at if transitioning to completed
        if to_status == SessionStatus.COMPLETED and not session.completed_at:
            from datetime import datetime, timezone
            session.completed_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        await self.db.refresh(session)
        
        logger.info(
            "state_transition",
            session_id=str(session_id),
            from_status=old_status,
            to_status=to_status.value,
            reason=reason,
        )
        
        return session

    def is_valid_transition(
        self, from_status: str, to_status: str
    ) -> bool:
        """Check if a state transition is valid.
        
        Args:
            from_status: Current status
            to_status: Target status
            
        Returns:
            True if transition is valid, False otherwise
        """
        try:
            from_enum = SessionStatus(from_status)
            to_enum = SessionStatus(to_status)
            return to_enum in self.VALID_TRANSITIONS.get(from_enum, set())
        except ValueError:
            return False
