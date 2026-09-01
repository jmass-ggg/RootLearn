"""Teach-back evaluation API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_service
from app.ai.validated_ai_service import ValidatedAIService
from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.schemas.session import ErrorResponse
from app.services.mastery_service import MasteryService
from app.services.session_service import SessionNotFoundError, SessionOwnershipError, SessionService
from app.services.teachback_service import TeachBackService

logger = get_logger(__name__)
router = APIRouter()


class TeachBackRequest(BaseModel):
    """Request schema for submitting teach-back explanation."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user submitting teach-back (for ownership verification)"
    )
    concept_id: uuid.UUID = Field(
        ...,
        description="ID of the concept being explained"
    )
    explanation: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Learner's explanation of the concept in their own words"
    )


class TeachBackResponse(BaseModel):
    """Response schema for teach-back evaluation."""
    
    attempt_id: uuid.UUID = Field(..., description="ID of the teach-back attempt")
    concept_id: uuid.UUID = Field(..., description="ID of the concept that was explained")
    concept_name: str = Field(..., description="Name of the concept that was explained")
    coverage_score: float = Field(..., description="Coverage score (0-1): completeness of key ideas")
    reasoning_score: float = Field(..., description="Reasoning score (0-1): logical correctness")
    clarity_score: float = Field(..., description="Clarity score (0-1): communication effectiveness")
    average_score: float = Field(..., description="Average of all three scores")
    demonstrated_points: list[str] = Field(..., description="Key ideas correctly explained")
    missing_points: list[str] = Field(..., description="Important concepts missing from explanation")
    misconceptions: list[str] = Field(..., description="Detected misconceptions or errors")
    should_continue_tutoring: bool = Field(
        ...,
        description="Whether tutoring should continue (true if average < 0.70)"
    )
    new_mastery_score: float = Field(..., description="Updated mastery score after teach-back")
    new_confidence_score: float = Field(..., description="Updated confidence score after teach-back")


def get_teachback_service(
    db: AsyncSession = Depends(get_db),
    ai_service: ValidatedAIService = Depends(get_ai_service),
) -> TeachBackService:
    """Dependency to get teach-back service."""
    mastery_service = MasteryService(db)
    return TeachBackService(db, ai_service, mastery_service)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.post(
    "/sessions/{session_id}/teachback",
    response_model=TeachBackResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Teach-back evaluated successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Session or concept not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def submit_teachback(
    session_id: uuid.UUID,
    request: TeachBackRequest,
    teachback_service: TeachBackService = Depends(get_teachback_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Submit and evaluate a teach-back explanation.
    
    The learner explains a concept in their own words to verify understanding.
    AI evaluates the explanation across three dimensions:
    - Coverage: completeness of key ideas
    - Reasoning: logical correctness
    - Clarity: communication effectiveness
    
    If average score < 0.70, tutoring continues. If >= 0.70, proceed to next concept.
    
    Args:
        session_id: UUID of the session
        request: Request containing user_id, concept_id, and explanation
    
    Requirements: 18.1, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    try:
        logger.info(
            "submit_teachback_request",
            session_id=str(session_id),
            user_id=str(request.user_id),
            concept_id=str(request.concept_id),
            explanation_length=len(request.explanation),
        )
        
        # Verify session ownership
        try:
            session = await session_service.get_session(
                session_id=session_id,
                user_id=request.user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "submit_teachback_unauthorized",
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
        
        # Verify session is in teachback status
        if session.status != "teachback":
            logger.warning(
                "submit_teachback_wrong_status",
                session_id=str(session_id),
                user_id=str(request.user_id),
                status=session.status,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.create(
                    code="invalid_session_status",
                    message=f"Session status must be 'teachback', currently: {session.status}",
                    request_id=get_request_id(),
                    details={"current_status": session.status},
                ),
            )
        
        # Evaluate teach-back
        try:
            result = await teachback_service.evaluate_teachback(
                session_id=session_id,
                concept_id=request.concept_id,
                student_explanation=request.explanation,
            )
        except Exception as e:
            logger.error(
                "submit_teachback_evaluation_error",
                session_id=str(session_id),
                user_id=str(request.user_id),
                concept_id=str(request.concept_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.create(
                    code="teachback_evaluation_failed",
                    message="Failed to evaluate teach-back explanation",
                    request_id=get_request_id(),
                    details={"error": str(e)},
                ),
            )
        
        # Get updated concept to return mastery scores
        from sqlalchemy import select
        from app.models import Concept
        
        concept_result = await teachback_service.db.execute(
            select(Concept).where(Concept.id == request.concept_id)
        )
        concept = concept_result.scalar_one()
        
        logger.info(
            "submit_teachback_success",
            session_id=str(session_id),
            user_id=str(request.user_id),
            attempt_id=str(result.attempt_id),
            concept_id=str(result.concept_id),
            average_score=result.average_score,
            should_continue_tutoring=result.should_continue_tutoring,
            new_mastery=float(concept.mastery_score),
        )
        
        return TeachBackResponse(
            attempt_id=result.attempt_id,
            concept_id=result.concept_id,
            concept_name=concept.name,
            coverage_score=result.coverage_score,
            reasoning_score=result.reasoning_score,
            clarity_score=result.clarity_score,
            average_score=result.average_score,
            demonstrated_points=result.demonstrated_points,
            missing_points=result.missing_points,
            misconceptions=result.misconceptions,
            should_continue_tutoring=result.should_continue_tutoring,
            new_mastery_score=float(concept.mastery_score),
            new_confidence_score=float(concept.confidence_score),
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "submit_teachback_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="teachback_submission_failed",
                message="Failed to submit teach-back",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
