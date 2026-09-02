"""Service for tracking application metrics and statistics."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import (
    AIRun,
    DiagnosticQuestion,
    LearningSession,
    MasteryEvent,
)

logger = get_logger(__name__)


class MetricsService:
    """Service for tracking and logging application metrics."""
    
    def __init__(self, db: AsyncSession):
        """Initialize metrics service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def log_session_completion(
        self,
        session_id: UUID,
        success: bool = True,
    ) -> None:
        """Log session completion metrics.
        
        Args:
            session_id: Session ID
            success: Whether session completed successfully
        """
        try:
            # Get session details
            result = await self.db.execute(
                select(LearningSession).where(LearningSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return
            
            # Calculate session duration
            if session.completed_at and session.created_at:
                duration_seconds = (
                    session.completed_at - session.created_at
                ).total_seconds()
            else:
                duration_seconds = None
            
            # Get diagnostic question count
            result = await self.db.execute(
                select(func.count(DiagnosticQuestion.id))
                .where(DiagnosticQuestion.session_id == session_id)
            )
            question_count = result.scalar() or 0
            
            # Get average mastery change
            result = await self.db.execute(
                select(
                    func.avg(MasteryEvent.new_score - MasteryEvent.old_score)
                )
                .where(MasteryEvent.session_id == session_id)
            )
            avg_mastery_change = result.scalar() or 0.0
            
            logger.info(
                "session_completed",
                session_id=str(session_id),
                status=session.status,
                success=success,
                duration_seconds=duration_seconds,
                diagnostic_questions=question_count,
                avg_mastery_change=float(avg_mastery_change),
            )
            
        except Exception as e:
            # Don't fail on metrics logging errors
            logger.error(
                "metrics_logging_error",
                error=str(e),
                session_id=str(session_id),
            )
    
    async def log_ai_metrics(
        self,
        session_id: Optional[UUID] = None,
        time_window_minutes: int = 5,
    ) -> None:
        """Log AI provider metrics.
        
        Args:
            session_id: Optional session ID to filter by
            time_window_minutes: Time window for metrics
        """
        try:
            # Calculate time window
            since = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            # Build query
            query = select(AIRun).where(AIRun.created_at >= since)
            if session_id:
                query = query.where(AIRun.session_id == session_id)
            
            result = await self.db.execute(query)
            ai_runs = result.scalars().all()
            
            if not ai_runs:
                return
            
            # Calculate metrics
            total_runs = len(ai_runs)
            successful_runs = sum(1 for run in ai_runs if run.success)
            failed_runs = total_runs - successful_runs
            failure_rate = failed_runs / total_runs if total_runs > 0 else 0
            
            # Calculate latency metrics
            latencies = [run.latency_ms for run in ai_runs if run.latency_ms]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            max_latency = max(latencies) if latencies else 0
            
            # Calculate token usage
            total_prompt_tokens = sum(
                run.prompt_tokens for run in ai_runs if run.prompt_tokens
            )
            total_completion_tokens = sum(
                run.completion_tokens for run in ai_runs if run.completion_tokens
            )
            
            # Calculate costs (approximate, would need provider-specific pricing)
            # These are rough estimates and should be updated based on actual pricing
            estimated_cost = (
                (total_prompt_tokens * 0.00001) +  # ~$0.01 per 1K tokens
                (total_completion_tokens * 0.00003)  # ~$0.03 per 1K tokens
            )
            
            logger.info(
                "ai_metrics",
                time_window_minutes=time_window_minutes,
                total_runs=total_runs,
                successful_runs=successful_runs,
                failed_runs=failed_runs,
                failure_rate=failure_rate,
                avg_latency_ms=avg_latency,
                max_latency_ms=max_latency,
                total_prompt_tokens=total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                estimated_cost_usd=estimated_cost,
                session_id=str(session_id) if session_id else None,
            )
            
        except Exception as e:
            # Don't fail on metrics logging errors
            logger.error(
                "ai_metrics_logging_error",
                error=str(e),
            )
    
    async def log_session_statistics(
        self,
        time_window_hours: int = 24,
    ) -> None:
        """Log session statistics.
        
        Args:
            time_window_hours: Time window for statistics
        """
        try:
            # Calculate time window
            since = datetime.utcnow() - timedelta(hours=time_window_hours)
            
            # Get total sessions
            result = await self.db.execute(
                select(func.count(LearningSession.id))
                .where(LearningSession.created_at >= since)
            )
            total_sessions = result.scalar() or 0
            
            # Get completed sessions
            result = await self.db.execute(
                select(func.count(LearningSession.id))
                .where(
                    LearningSession.created_at >= since,
                    LearningSession.status == "completed",
                )
            )
            completed_sessions = result.scalar() or 0
            
            # Calculate completion rate
            completion_rate = (
                completed_sessions / total_sessions
                if total_sessions > 0
                else 0
            )
            
            # Get average mastery change across all sessions
            result = await self.db.execute(
                select(
                    func.avg(MasteryEvent.new_score - MasteryEvent.old_score)
                )
                .join(LearningSession)
                .where(LearningSession.created_at >= since)
            )
            avg_mastery_change = result.scalar() or 0.0
            
            # Get average diagnostic questions per session
            result = await self.db.execute(
                select(func.avg(func.count(DiagnosticQuestion.id)))
                .join(LearningSession)
                .where(LearningSession.created_at >= since)
                .group_by(LearningSession.id)
            )
            avg_questions = result.scalar() or 0.0
            
            logger.info(
                "session_statistics",
                time_window_hours=time_window_hours,
                total_sessions=total_sessions,
                completed_sessions=completed_sessions,
                completion_rate=completion_rate,
                avg_mastery_change=float(avg_mastery_change),
                avg_diagnostic_questions=float(avg_questions),
            )
            
        except Exception as e:
            # Don't fail on metrics logging errors
            logger.error(
                "session_statistics_error",
                error=str(e),
            )


async def log_session_completion_metric(
    db: AsyncSession,
    session_id: UUID,
    success: bool = True,
) -> None:
    """Helper function to log session completion metrics.
    
    Args:
        db: Database session
        session_id: Session ID
        success: Whether session completed successfully
    """
    metrics_service = MetricsService(db)
    await metrics_service.log_session_completion(session_id, success)


async def log_ai_metrics(
    db: AsyncSession,
    session_id: Optional[UUID] = None,
    time_window_minutes: int = 5,
) -> None:
    """Helper function to log AI metrics.
    
    Args:
        db: Database session
        session_id: Optional session ID
        time_window_minutes: Time window for metrics
    """
    metrics_service = MetricsService(db)
    await metrics_service.log_ai_metrics(session_id, time_window_minutes)
