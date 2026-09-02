"""
Mastery event routes.

Requirements: 7.1, 7.2, 7.4
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import MasteryEvent, LearningSession

router = APIRouter()


@router.get("/sessions/{session_id}/mastery-events")
async def get_mastery_events(
    session_id: UUID,
    user_id: UUID = Query(..., description="User ID for session ownership verification"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get mastery events for a session.
    
    Returns chronologically ordered mastery events showing before/after scores
    and reasons for changes.
    
    Requirements: 7.1, 7.2, 7.4
    """
    # Verify session ownership
    session_result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get mastery events ordered by creation time
    result = await db.execute(
        select(MasteryEvent)
        .where(MasteryEvent.session_id == session_id)
        .order_by(MasteryEvent.created_at.asc())
    )
    events = result.scalars().all()
    
    # Format response
    return [
        {
            "id": str(event.id),
            "concept_id": str(event.concept_id),
            "source_type": event.source_type,
            "old_score": float(event.old_score),
            "new_score": float(event.new_score),
            "old_confidence": float(event.old_confidence),
            "new_confidence": float(event.new_confidence),
            "reason": event.reason_json,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


@router.get("/sessions/{session_id}/concepts/{concept_id}/mastery-events")
async def get_concept_mastery_events(
    session_id: UUID,
    concept_id: UUID,
    user_id: UUID = Query(..., description="User ID for session ownership verification"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get mastery events for a specific concept within a session.
    
    Returns chronologically ordered mastery events for a single concept.
    
    Requirements: 7.1, 7.2, 7.4
    """
    # Verify session ownership
    session_result = await db.execute(
        select(LearningSession).where(
            LearningSession.id == session_id,
            LearningSession.user_id == user_id
        )
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get mastery events for the specific concept
    result = await db.execute(
        select(MasteryEvent)
        .where(
            MasteryEvent.session_id == session_id,
            MasteryEvent.concept_id == concept_id
        )
        .order_by(MasteryEvent.created_at.asc())
    )
    events = result.scalars().all()
    
    # Format response
    return [
        {
            "id": str(event.id),
            "concept_id": str(event.concept_id),
            "source_type": event.source_type,
            "old_score": float(event.old_score),
            "new_score": float(event.new_score),
            "old_confidence": float(event.old_confidence),
            "new_confidence": float(event.new_confidence),
            "reason": event.reason_json,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]
