"""Diagnostic assessment API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_ai_service
from app.ai.validated_ai_service import ValidatedAIService
from app.database import get_db
from app.logging_config import get_logger, get_request_id
from app.schemas.session import ErrorResponse
from app.services.diagnostic_service import DiagnosticService
from app.services.mastery_service import MasteryService
from app.services.session_service import SessionNotFoundError, SessionOwnershipError, SessionService

logger = get_logger(__name__)
router = APIRouter()


class DiagnosisStartRequest(BaseModel):
    """Request schema for starting diagnosis."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user requesting diagnosis (for ownership verification)"
    )


class DiagnosisStartResponse(BaseModel):
    """Response schema for starting diagnosis."""
    
    session_id: uuid.UUID = Field(..., description="ID of the learning session")
    status: str = Field(..., description="Current session status")
    message: str = Field(..., description="Human-readable status message")


class DiagnosticQuestionResponse(BaseModel):
    """Response schema for current diagnostic question."""
    
    question_id: uuid.UUID = Field(..., description="ID of the diagnostic question")
    concept_id: uuid.UUID = Field(..., description="ID of the concept being tested")
    concept_name: str = Field(..., description="Name of the concept being tested")
    question_text: str = Field(..., description="Text of the diagnostic question")
    question_type: str = Field(..., description="Type of question (short_answer, multiple_choice, etc.)")
    difficulty: float = Field(..., description="Difficulty level of the question (0-1)")
    should_stop: bool = Field(..., description="Whether diagnosis should stop after this question")


class DiagnosisAnswerRequest(BaseModel):
    """Request schema for submitting diagnostic answer."""
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user submitting answer (for ownership verification)"
    )
    question_id: uuid.UUID = Field(..., description="ID of the question being answered")
    answer: str = Field(..., description="Student's answer to the question", min_length=1)


class DiagnosisAnswerResponse(BaseModel):
    """Response schema for diagnostic answer evaluation."""
    
    attempt_id: uuid.UUID = Field(..., description="ID of the diagnostic attempt")
    correctness_score: float = Field(..., description="Correctness score (0-1)")
    reasoning_score: float = Field(..., description="Reasoning quality score (0-1)")
    demonstrated_points: list[str] = Field(..., description="Points correctly demonstrated")
    missing_points: list[str] = Field(..., description="Points missing from answer")
    misconceptions: list[str] = Field(..., description="Detected misconceptions")
    should_stop: bool = Field(..., description="Whether diagnosis should stop")


def get_diagnostic_service(
    db: AsyncSession = Depends(get_db),
    ai_service: ValidatedAIService = Depends(get_ai_service),
) -> DiagnosticService:
    """Dependency to get diagnostic service."""
    mastery_service = MasteryService(db)
    return DiagnosticService(db, ai_service, mastery_service)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.post(
    "/sessions/{session_id}/diagnosis/start",
    response_model=DiagnosisStartResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Diagnosis started successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Session not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def start_diagnosis(
    session_id: uuid.UUID,
    request: DiagnosisStartRequest,
    session_service: SessionService = Depends(get_session_service),
):
    """Start diagnostic assessment for a session.
    
    Transitions the session to "diagnosing" status. The system will begin
    adaptive questioning to assess understanding of prerequisite concepts.
    
    Args:
        session_id: UUID of the session to start diagnosis for
        request: Request containing user_id for ownership verification
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "start_diagnosis_request",
            session_id=str(session_id),
            user_id=str(request.user_id),
        )
        
        # Verify session ownership
        try:
            session = await session_service.get_session(
                session_id=session_id,
                user_id=request.user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "start_diagnosis_unauthorized",
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
        
        # Update session status to "diagnosing"
        await session_service.update_session_status(
            session_id=session_id,
            status="diagnosing",
        )
        
        logger.info(
            "start_diagnosis_success",
            session_id=str(session_id),
            user_id=str(request.user_id),
        )
        
        return DiagnosisStartResponse(
            session_id=session_id,
            status="diagnosing",
            message="Diagnostic assessment started. Use GET /diagnosis/current to get the first question.",
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "start_diagnosis_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="diagnosis_start_failed",
                message="Failed to start diagnostic assessment",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.get(
    "/sessions/{session_id}/diagnosis/current",
    response_model=DiagnosticQuestionResponse,
    responses={
        200: {"description": "Current diagnostic question retrieved"},
        404: {"description": "Session not found or no question available", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def get_current_diagnostic_question(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Get the current diagnostic question for a session.
    
    Selects the most informative concept to test based on uncertainty,
    importance, and downstream impact, then generates a diagnostic question.
    
    If diagnosis should stop, returns the question with should_stop=true.
    
    Args:
        session_id: UUID of the session
        user_id: UUID of the requesting user (query parameter)
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "get_current_diagnostic_question_request",
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
                "get_current_diagnostic_question_unauthorized",
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
        
        # Check if diagnosis should stop
        should_stop = await diagnostic_service.should_stop_diagnosis(session_id)
        
        if should_stop:
            logger.info(
                "diagnosis_stopping",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="diagnosis_complete",
                    message="Diagnostic assessment is complete. No more questions needed.",
                    request_id=get_request_id(),
                ),
            )
        
        # Select next concept to test
        concept = await diagnostic_service.select_next_concept(session_id)
        
        if not concept:
            logger.warning(
                "no_concept_to_test",
                session_id=str(session_id),
                user_id=str(user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="no_concept_available",
                    message="No suitable concept found for testing",
                    request_id=get_request_id(),
                ),
            )
        
        # Generate diagnostic question
        question = await diagnostic_service.generate_question(concept.id)
        
        # Check again if we should stop after this question
        should_stop = await diagnostic_service.should_stop_diagnosis(session_id)
        
        logger.info(
            "get_current_diagnostic_question_success",
            session_id=str(session_id),
            user_id=str(user_id),
            question_id=str(question.id),
            concept_id=str(concept.id),
            concept_name=concept.name,
            should_stop=should_stop,
        )
        
        return DiagnosticQuestionResponse(
            question_id=question.id,
            concept_id=concept.id,
            concept_name=concept.name,
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=float(question.difficulty),
            should_stop=should_stop,
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "get_current_diagnostic_question_error",
            session_id=str(session_id),
            user_id=str(user_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="diagnostic_question_retrieval_failed",
                message="Failed to get diagnostic question",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )


@router.post(
    "/sessions/{session_id}/diagnosis/answer",
    response_model=DiagnosisAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Answer evaluated successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        404: {"description": "Session or question not found", "model": ErrorResponse},
        403: {"description": "Access forbidden", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def submit_diagnostic_answer(
    session_id: uuid.UUID,
    request: DiagnosisAnswerRequest,
    diagnostic_service: DiagnosticService = Depends(get_diagnostic_service),
    session_service: SessionService = Depends(get_session_service),
):
    """Submit and evaluate a diagnostic answer.
    
    Evaluates the student's answer against the question rubric using AI,
    creates a diagnostic attempt record, and updates mastery evidence.
    
    Args:
        session_id: UUID of the session
        request: Request containing user_id, question_id, and answer
    
    Requirements: 18.1
    """
    try:
        logger.info(
            "submit_diagnostic_answer_request",
            session_id=str(session_id),
            user_id=str(request.user_id),
            question_id=str(request.question_id),
            answer_length=len(request.answer),
        )
        
        # Verify session ownership
        try:
            await session_service.get_session(
                session_id=session_id,
                user_id=request.user_id,
            )
        except (SessionNotFoundError, SessionOwnershipError):
            logger.warning(
                "submit_diagnostic_answer_unauthorized",
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
        
        # Evaluate answer
        try:
            result = await diagnostic_service.evaluate_answer(
                question_id=request.question_id,
                answer=request.answer,
            )
        except ValueError as e:
            logger.warning(
                "submit_diagnostic_answer_invalid_question",
                session_id=str(session_id),
                user_id=str(request.user_id),
                question_id=str(request.question_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.create(
                    code="question_not_found",
                    message=str(e),
                    request_id=get_request_id(),
                ),
            )
        
        # Check if diagnosis should stop
        should_stop = await diagnostic_service.should_stop_diagnosis(session_id)
        
        logger.info(
            "submit_diagnostic_answer_success",
            session_id=str(session_id),
            user_id=str(request.user_id),
            question_id=str(request.question_id),
            attempt_id=str(result.attempt_id),
            correctness_score=result.correctness_score,
            reasoning_score=result.reasoning_score,
            should_stop=should_stop,
        )
        
        return DiagnosisAnswerResponse(
            attempt_id=result.attempt_id,
            correctness_score=result.correctness_score,
            reasoning_score=result.reasoning_score,
            demonstrated_points=result.demonstrated_points,
            missing_points=result.missing_points,
            misconceptions=result.misconceptions,
            should_stop=should_stop,
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            "submit_diagnostic_answer_error",
            session_id=str(session_id),
            user_id=str(request.user_id),
            question_id=str(request.question_id),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.create(
                code="answer_evaluation_failed",
                message="Failed to evaluate diagnostic answer",
                request_id=get_request_id(),
                details={"error": str(e)},
            ),
        )
