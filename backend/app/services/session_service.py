"""Session management service."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.logging_config import get_logger
from app.models import LearningSession, User

logger = get_logger(__name__)


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""
    pass


class SessionOwnershipError(Exception):
    """Raised when user does not own the requested session."""
    pass


class SessionService:
    """Service for managing learning sessions."""

    def __init__(self, db: AsyncSession):
        """Initialize session service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def create_session(
        self, user_id: uuid.UUID, prompt: str
    ) -> LearningSession:
        """Create a new learning session.
        
        Creates a session with "analyzing" status and the user's original prompt.
        
        Args:
            user_id: ID of the user creating the session
            prompt: The user's learning prompt describing what they don't understand
            
        Returns:
            The created LearningSession with status "analyzing"
            
        Requirements: 1.1, 1.2
        """
        # Verify user exists
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Create user if doesn't exist (for MVP without authentication)
            user = User(id=user_id)
            self.db.add(user)
            await self.db.flush()
        
        # Create session with "analyzing" status
        session = LearningSession(
            user_id=user_id,
            original_prompt=prompt,
            status="analyzing",
        )
        
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        
        logger.info(
            "session_created",
            session_id=str(session.id),
            user_id=str(user_id),
            status=session.status,
        )
        
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> LearningSession:
        """Get a learning session by ID.
        
        Verifies session ownership before returning the session.
        
        Args:
            session_id: ID of the session to retrieve
            user_id: ID of the user requesting the session
            
        Returns:
            The LearningSession
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionOwnershipError: If user doesn't own the session
            
        Requirements: 1.3, 16.3, 16.4
        """
        result = await self.db.execute(
            select(LearningSession)
            .where(LearningSession.id == session_id)
            .options(
                selectinload(LearningSession.concepts),
                selectinload(LearningSession.target_concept),
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            logger.warning(
                "session_not_found",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Verify ownership
        if session.user_id != user_id:
            logger.warning(
                "session_ownership_violation",
                session_id=str(session_id),
                requested_by=str(user_id),
                owner=str(session.user_id),
            )
            raise SessionOwnershipError(
                f"User {user_id} does not own session {session_id}"
            )
        
        logger.debug(
            "session_retrieved",
            session_id=str(session_id),
            user_id=str(user_id),
            status=session.status,
        )
        
        return session

    async def update_session_status(
        self, session_id: uuid.UUID, status: str
    ) -> LearningSession:
        """Update a session's status.
        
        DEPRECATED: This method directly sets status without validation.
        Use StateMachineService for state transitions instead.
        
        This method is kept for backwards compatibility only.
        
        Args:
            session_id: ID of the session to update
            status: New status value (must be valid session status)
            
        Returns:
            The updated LearningSession
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            ValueError: If status is invalid
            
        Requirements: 1.4
        """
        # Validate status
        valid_statuses = {
            "analyzing",
            "diagnosing",
            "tutoring",
            "teachback",
            "completed",
            "abandoned",
        }
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )
        
        result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            logger.warning(
                "session_not_found_for_update",
                session_id=str(session_id),
            )
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        old_status = session.status
        session.status = status
        
        # Set completed_at if transitioning to completed
        if status == "completed" and not session.completed_at:
            session.completed_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(session)
        
        logger.info(
            "session_status_updated",
            session_id=str(session_id),
            old_status=old_status,
            new_status=status,
        )
        
        return session

    async def delete_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Delete a learning session.
        
        Verifies session ownership before deletion. All related data
        (concepts, edges, questions, etc.) are cascaded automatically.
        
        Args:
            session_id: ID of the session to delete
            user_id: ID of the user requesting deletion
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionOwnershipError: If user doesn't own the session
            
        Requirements: 1.4, 16.3
        """
        result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            logger.warning(
                "session_not_found_for_deletion",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Verify ownership
        if session.user_id != user_id:
            logger.warning(
                "session_deletion_ownership_violation",
                session_id=str(session_id),
                requested_by=str(user_id),
                owner=str(session.user_id),
            )
            raise SessionOwnershipError(
                f"User {user_id} does not own session {session_id}"
            )
        
        await self.db.delete(session)
        await self.db.flush()
        
        logger.info(
            "session_deleted",
            session_id=str(session_id),
            user_id=str(user_id),
        )
