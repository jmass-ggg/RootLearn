"""Root gap detection API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.schemas.session import ErrorResponse
from app.services.root_gap_service import RootGapService
from app.services.session_service import SessionNotFoundError, SessionOwnershipError, SessionService

logger = get_logger(__name__)
router = APIRouter()


class GapExplanationResponse(BaseModel):
    """Response schema for gap explanation."""
    
    concept_id: uuid.UUID = Field(..., description="ID of the root gap concept")
    concept_name: str = Field(..., description="Name of the root gap concept")
    mastery: float = Field(..., description="Current mastery score (0-1)")
    confidence: float = Field(..., description="Current confidence score (0-1)")
    gap_score: float = Field(..., description="Calculated gap score (higher = more critical)")
    reasons: list[str] = Field(..., description="Human-readable reasons for gap selection")


class RootGapResponse(BaseModel):
    """Response schema for root gap detection."""
    
    session_id: uuid.UUID = Field(..., description="ID of the learning session")
    root_gap: GapExplanationResponse = Field(..., description="Identified root gap")
    message: str = Field(..., description="Human-readable message")


def get_root_gap_service(db: AsyncSession = Depends(get_db)) -> RootGapService:
    """Dependency to get root gap service."""
    return RootGapService(db)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.get(
    "/sessions/{session_id}/root-gap",
    response_model=RootGapResponse,
    responses={
        200: {"description": "Root gap identified successfully"},
        404: {"description": "Session not found or no root gap available", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_root_gap(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    root_gap_service: RootGapService = Depends(get_root_gap_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get the root gap for a learning session.
    
    Identifies the most impactful knowledge gap by calculating gap scores
    based on mastery, confidence, path importance, and downstream impact.
    Returns the concept with the highest gap score along with an explanation.
    
    The root gap is the weakest prerequisite concept that is blocking
    understanding of the target concept. Only concepts with mastery < 0.70
    are considered as root gap candidates.
    
    Args:
        session_id: UUID of the session
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "get_root_gap_request",
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
                "get_root_gap_unauthorized",
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
        
        # Detect root gap
        try:
            root_gap_result = await root_gap_service.detect_root_gap(session_id)
        except ValueError as e:
            logger.error(
                "get_root_gap_invalid_session",
                session_id=str(session_id),
                user_id=str(user_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.create(
                    code="invalid_session",
                    message=str(e),
                    request_id=get_request_id(),
                ),
            )
        
        if not root_gap_result:
            logger.info(
                "no_root_gap_found",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="no_root_gap",
                    message="No root gap found. All prerequisites may already be understood.",
                    request_id=get_request_id(),
                ),
            )
        
        logger.info(
            "get_root_gap_success",
            session_id=str(session_id),
            user_id=str(user_id),
            concept_id=str(root_gap_result.concept.id),
            concept_name=root_gap_result.concept.name,
            gap_score=root_gap_result.gap_score,
        )
        
        return RootGapResponse(
            session_id=session_id,
            root_gap=GapExplanationResponse(
                concept_id=root_gap_result.explanation.concept_id,
                concept_name=root_gap_result.explanation.concept_name,
                mastery=root_gap_result.explanation.mastery,
                confidence=root_gap_result.explanation.confidence,
                gap_score=root_gap_result.explanation.gap_score,
                reasons=root_gap_result.explanation.reasons,
            ),
            message=f"Root gap identified: {root_gap_result.concept.name}",
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "get_root_gap_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="root_gap_detection_failed",
                message="Failed to detect root gap",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
