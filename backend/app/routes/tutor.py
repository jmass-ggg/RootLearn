"""Socratic tutoring API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.schemas.session import ErrorResponse
from app.services.session_service import SessionNotFoundError, SessionOwnershipError, SessionService
from app.services.tutor_service import TutorService

logger = get_logger(__name__)
router = APIRouter()


class TutorMessageRequest(BaseModel):
    """Request schema for submitting a tutor message."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user submitting message (for ownership verification)"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The learner's message/question to the tutor"
    )


class TutorMessageResponse(BaseModel):
    """Response schema for tutor response."""
    
    message_id: uuid.UUID = Field(..., description="ID of the assistant message")
    concept_id: uuid.UUID = Field(..., description="ID of the concept being taught")
    concept_name: str = Field(..., description="Name of the concept being taught")
    response: str = Field(..., description="Tutor's response to the learner")
    hint_level: int = Field(..., description="Current hint level (0-4)")
    mastery_score: float = Field(..., description="Current mastery score for concept")
    confidence_score: float = Field(..., description="Current confidence score for concept")


class TutorMessagesResponse(BaseModel):
    """Response schema for tutor message history."""
    
    session_id: uuid.UUID = Field(..., description="ID of the learning session")
    concept_id: uuid.UUID = Field(..., description="ID of the concept being taught")
    concept_name: str = Field(..., description="Name of the concept being taught")
    messages: list[dict] = Field(..., description="List of conversation messages")


def get_tutor_service(db: AsyncSession = Depends(get_db)) -> TutorService:
    """Dependency to get tutor service."""
    return TutorService(db)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.post(
    "/sessions/{session_id}/tutor/messages",
    response_model=TutorMessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Tutor response generated successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Session not found or not in tutoring state", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def send_tutor_message(
    session_id: uuid.UUID,
    request: TutorMessageRequest,
    tutor_service: TutorService = Depends(get_tutor_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Send a message to the Socratic tutor and get a response.
    
    The tutor uses progressive hint escalation to guide the learner
    toward understanding without directly explaining. Context includes
    the current concept, conversation history, known misconceptions,
    and mastery levels.
    
    Args:
        session_id: UUID of the session
        request: Request containing user_id and message
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "send_tutor_message_request",
            session_id=str(session_id),
            user_id=str(request.user_id),
            message_length=len(request.message),
        )
        
        # Verify session ownership
        try:
            session = await session_service.get_session(
                session_id=session_id,
                user_id=request.user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "send_tutor_message_unauthorized",
                session_id=str(session_id),
                user_id=str(request.user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="session_not_found",
                    message="Session not found",
                    request_id=get_request_id(),
                ),
            )
        
        # Verify session is in tutoring status
        if session.status != "tutoring":
            logger.warning(
                "send_tutor_message_wrong_status",
                session_id=str(session_id),
                user_id=str(request.user_id),
                status=session.status,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.create(
                    code="invalid_session_status",
                    message=f"Session status must be 'tutoring', currently: {session.status}",
                    request_id=get_request_id(),
                    details={"current_status": session.status},
                ),
            )
        
        # Generate tutor response
        try:
            response = await tutor_service.generate_response(
                session_id=session_id,
                user_message=request.message,
            )
        except ValueError as e:
            logger.warning(
                "send_tutor_message_invalid",
                session_id=str(session_id),
                user_id=str(request.user_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="tutoring_not_started",
                    message=str(e),
                    request_id=get_request_id(),
                ),
            )
        
        # Get context for response metadata
        context = await tutor_service.get_tutor_context(session_id)
        
        # Get the message ID (most recent assistant message)
        from sqlalchemy import select
        from app.models import TutorMessage
        
        result = await tutor_service.db.execute(
            select(TutorMessage)
            .where(
                TutorMessage.session_id == session_id,
                TutorMessage.role == "assistant",
            )
            .order_by(TutorMessage.created_at.desc())
            .limit(1)
        )
        assistant_message = result.scalar_one()
        
        logger.info(
            "send_tutor_message_success",
            session_id=str(session_id),
            user_id=str(request.user_id),
            message_id=str(assistant_message.id),
            concept_id=str(context.current_concept.id),
            hint_level=context.hint_level,
            response_length=len(response),
        )
        
        return TutorMessageResponse(
            message_id=assistant_message.id,
            concept_id=context.current_concept.id,
            concept_name=context.current_concept.name,
            response=response,
            hint_level=context.hint_level,
            mastery_score=context.mastery_score,
            confidence_score=context.confidence_score,
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "send_tutor_message_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="tutor_response_failed",
                message="Failed to generate tutor response",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.get(
    "/sessions/{session_id}/tutor/messages",
    response_model=TutorMessagesResponse,
    responses={
        200: {"description": "Tutor messages retrieved successfully"},
        404: {"description": "Session not found or no tutoring messages", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_tutor_messages(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    tutor_service: TutorService = Depends(get_tutor_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get the conversation history for tutoring session.
    
    Returns all tutor messages for the current concept being taught,
    including both user messages and assistant responses.
    
    Args:
        session_id: UUID of the session
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "get_tutor_messages_request",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        
        # Verify session ownership
        try:
            await session_service.get_session(
                session_id=session_id,
                user_id=user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "get_tutor_messages_unauthorized",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="session_not_found",
                    message="Session not found",
                    request_id=get_request_id(),
                ),
            )
        
        # Get tutor context to find current concept
        try:
            context = await tutor_service.get_tutor_context(session_id)
        except ValueError as e:
            logger.warning(
                "get_tutor_messages_no_context",
                session_id=str(session_id),
                user_id=str(user_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="no_tutoring_messages",
                    message=str(e),
                    request_id=get_request_id(),
                ),
            )
        
        # Get all messages for current concept
        from sqlalchemy import select
        from app.models import TutorMessage
        
        result = await tutor_service.db.execute(
            select(TutorMessage)
            .where(
                TutorMessage.session_id == session_id,
                TutorMessage.concept_id == context.current_concept.id,
            )
            .order_by(TutorMessage.created_at.asc())
        )
        messages = result.scalars().all()
        
        # Format messages
        formatted_messages = [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "hint_level": msg.hint_level,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
        
        logger.info(
            "get_tutor_messages_success",
            session_id=str(session_id),
            user_id=str(user_id),
            concept_id=str(context.current_concept.id),
            message_count=len(formatted_messages),
        )
        
        return TutorMessagesResponse(
            session_id=session_id,
            concept_id=context.current_concept.id,
            concept_name=context.current_concept.name,
            messages=formatted_messages,
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "get_tutor_messages_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="tutor_messages_retrieval_failed",
                message="Failed to retrieve tutor messages",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
