"""Session management API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.schemas.session import (
    ErrorResponse,
    SessionCreateRequest,
    SessionResponse,
)
from app.services.session_service import (
    SessionNotFoundError,
    SessionOwnershipError,
    SessionService,
)

logger = get_logger(__name__)
router = APIRouter()


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Session created successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def create_session(
    request: SessionCreateRequest,
    service: SessionService = Depends(get_session_service),
):
    """Create a new learning session.
    
    Creates a new session with "analyzing" status. The system will use
    the provided prompt to identify the target concept and build a
    prerequisite graph.
    
    Requirements: 18.1, 18.6
    """
    try:
        logger.info(
            "create_session_request",
            user_id=str(request.user_id),
            prompt_length=len(request.prompt),
        )
        
        session = await service.create_session(
            user_id=request.user_id,
            prompt=request.prompt,
        )
        
        logger.info(
            "create_session_success",
            session_id=str(session.id),
            user_id=str(request.user_id),
        )
        
        return SessionResponse.model_validate(session)
        
    except Exception as e:
        logger.error(
            "create_session_error",
            user_id=str(request.user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="session_creation_failed",
                message="Failed to create session",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    responses={
        200: {"description": "Session retrieved successfully"},
        404: {"description": "Session not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    service: SessionService = Depends(get_session_service),
):
    """Get a learning session by ID.
    
    Retrieves session information including current status, prompt,
    and target concept if identified. Verifies session ownership.
    
    Args:
        session_id: UUID of the session to retrieve
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1, 18.6
    """
    try:
        logger.info(
            "get_session_request",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        
        session = await service.get_session(
            session_id=session_id,
            user_id=user_id,
        )
        
        logger.info(
            "get_session_success",
            session_id=str(session_id),
            user_id=str(user_id),
            status=session.status,
        )
        
        return SessionResponse.model_validate(session)
        
    except SessionNotFoundError as e:
        logger.warning(
            "get_session_not_found",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse.create(
                code="session_not_found",
                message=str(e),
                request_id=get_request_id(),
            ),
        )
        
    except SessionOwnershipError as e:
        logger.warning(
            "get_session_ownership_error",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        # Return 404 to avoid leaking information about session existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse.create(
                code="session_not_found",
                message="Session not found",
                request_id=get_request_id(),
            ),
        )
        
    except Exception as e:
        logger.error(
            "get_session_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="session_retrieval_failed",
                message="Failed to retrieve session",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Session deleted successfully"},
        404: {"description": "Session not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def delete_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    service: SessionService = Depends(get_session_service),
):
    """Delete a learning session.
    
    Permanently deletes a session and all associated data (concepts,
    edges, questions, attempts, etc.). Verifies session ownership
    before deletion.
    
    Args:
        session_id: UUID of the session to delete
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1, 18.6
    """
    try:
        logger.info(
            "delete_session_request",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        
        await service.delete_session(
            session_id=session_id,
            user_id=user_id,
        )
        
        logger.info(
            "delete_session_success",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        
        return None
        
    except SessionNotFoundError as e:
        logger.warning(
            "delete_session_not_found",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse.create(
                code="session_not_found",
                message=str(e),
                request_id=get_request_id(),
            ),
        )
        
    except SessionOwnershipError as e:
        logger.warning(
            "delete_session_ownership_error",
            session_id=str(session_id),
            user_id=str(user_id),
        )
        # Return 404 to avoid leaking information about session existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse.create(
                code="session_not_found",
                message="Session not found",
                request_id=get_request_id(),
            ),
        )
        
    except Exception as e:
        logger.error(
            "delete_session_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="session_deletion_failed",
                message="Failed to delete session",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
