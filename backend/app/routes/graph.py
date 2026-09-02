"""Graph generation and retrieval API endpoints."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_service
from app.ai.schemas import PrerequisiteEdge, PrerequisiteNode
from app.ai.validated_ai_service import ValidatedAIService
from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.models import Concept, ConceptEdge
from app.schemas.session import ErrorResponse
from app.services.graph_service import GraphService
from app.services.session_service import SessionNotFoundError, SessionOwnershipError, SessionService

logger = get_logger(__name__)
router = APIRouter()


class GraphGenerateRequest(BaseModel):
    """Request schema for graph generation."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user requesting graph generation (for ownership verification)"
    )


class GraphResponse(BaseModel):
    """Response schema for prerequisite graph."""
    
    target_slug: str = Field(..., description="Slug of the target concept")
    nodes: list[PrerequisiteNode] = Field(..., description="All concepts in the graph")
    edges: list[PrerequisiteEdge] = Field(..., description="Prerequisite relationships")
    
    model_config = {
        "from_attributes": True
    }


class StoredConceptResponse(BaseModel):
    """A persisted concept with mastery data used by the frontend graph."""

    id: uuid.UUID
    slug: str
    name: str
    description: str
    is_target: bool
    mastery_score: float
    confidence_score: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoredEdgeResponse(BaseModel):
    """A persisted graph edge whose endpoints use concept UUIDs."""

    id: uuid.UUID
    source_concept_id: uuid.UUID
    target_concept_id: uuid.UUID
    importance_weight: float
    created_at: datetime

    model_config = {"from_attributes": True}


class StoredGraphResponse(BaseModel):
    """Stored graph representation consumed by the React Flow UI."""

    concepts: list[StoredConceptResponse]
    edges: list[StoredEdgeResponse]
    root_gap_id: uuid.UUID | None = None


def get_graph_service(
    db: AsyncSession = Depends(get_db),
    ai_service: ValidatedAIService = Depends(get_ai_service),
) -> GraphService:
    """Dependency to get graph service."""
    return GraphService(db, ai_service)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.post(
    "/sessions/{session_id}/graph/generate",
    response_model=GraphResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Graph generated successfully"},
        400: {"description": "Invalid request or validation failed", "model": ErrorResponse},
        404: {"description": "Session not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def generate_graph(
    session_id: uuid.UUID,
    request: GraphGenerateRequest,
    graph_service: GraphService = Depends(get_graph_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Generate prerequisite graph for a session's target concept.
    
    This endpoint generates a prerequisite graph showing all the foundational
    concepts needed to understand the target concept. The graph is a directed
    acyclic graph (DAG) with size and structural constraints enforced.
    
    This operation is idempotent - if a graph already exists for this session,
    the existing graph is returned.
    
    Args:
        session_id: UUID of the session to generate graph for
        request: Request containing user_id for ownership verification
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "generate_graph_request",
            session_id=str(session_id),
            user_id=str(request.user_id),
        )
        
        # Verify session ownership
        try:
            await session_service.get_session(
                session_id=session_id,
                user_id=request.user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "generate_graph_unauthorized",
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
        
        # Generate graph
        graph_output = await graph_service.generate_graph(session_id)
        
        logger.info(
            "generate_graph_success",
            session_id=str(session_id),
            user_id=str(request.user_id),
            node_count=len(graph_output.nodes),
            edge_count=len(graph_output.edges),
        )
        
        return GraphResponse(
            target_slug=graph_output.target_slug,
            nodes=graph_output.nodes,
            edges=graph_output.edges,
        )
        
    except HTTPException:
        raise
        
    except ValueError as e:
        # Graph validation errors or missing target concept
        logger.error(
            "generate_graph_validation_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse.create(
                code="graph_validation_failed",
                message=str(e),
                request_id=get_request_id(),
            ),
        )
        
    except Exception as e:
        logger.error(
            "generate_graph_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="graph_generation_failed",
                message="Failed to generate prerequisite graph",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.get(
    "/sessions/{session_id}/graph",
    response_model=StoredGraphResponse,
    responses={
        200: {"description": "Graph retrieved successfully"},
        404: {"description": "Session or graph not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_graph(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    graph_service: GraphService = Depends(get_graph_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get the prerequisite graph for a session.
    
    Retrieves the existing prerequisite graph for a session. Returns 404
    if no graph has been generated yet.
    
    Args:
        session_id: UUID of the session
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "get_graph_request",
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
                "get_graph_unauthorized",
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
        
        # Get graph
        graph_output = await graph_service.get_graph(session_id)
        
        if not graph_output:
            logger.info(
                "get_graph_not_found",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="graph_not_found",
                    message="No prerequisite graph exists for this session",
                    request_id=get_request_id(),
                ),
            )
        
        logger.info(
            "get_graph_success",
            session_id=str(session_id),
            user_id=str(user_id),
            node_count=len(graph_output.nodes),
            edge_count=len(graph_output.edges),
        )

        concept_result = await graph_service.db.execute(
            select(Concept)
            .where(Concept.session_id == session_id)
            .order_by(Concept.created_at.asc())
        )
        edge_result = await graph_service.db.execute(
            select(ConceptEdge)
            .where(ConceptEdge.session_id == session_id)
            .order_by(ConceptEdge.created_at.asc())
        )

        return StoredGraphResponse(
            concepts=[
                StoredConceptResponse.model_validate(concept)
                for concept in concept_result.scalars().all()
            ],
            edges=[
                StoredEdgeResponse.model_validate(edge)
                for edge in edge_result.scalars().all()
            ],
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "get_graph_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="graph_retrieval_failed",
                message="Failed to retrieve prerequisite graph",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
