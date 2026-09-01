"""Unit tests for session service."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.models import LearningSession, User
from app.services.session_service import (
    SessionNotFoundError,
    SessionOwnershipError,
    SessionService,
)


@pytest.mark.asyncio
async def test_create_session(db_session):
    """Test creating a new learning session."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand recursion"
    
    session = await service.create_session(user_id=user_id, prompt=prompt)
    
    assert session.id is not None
    assert session.user_id == user_id
    assert session.original_prompt == prompt
    assert session.status == "analyzing"
    assert session.created_at is not None
    assert session.updated_at is not None
    assert session.completed_at is None


@pytest.mark.asyncio
async def test_get_session(db_session):
    """Test retrieving a session by ID."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand binary trees"
    
    # Create session
    created_session = await service.create_session(user_id=user_id, prompt=prompt)
    await db_session.commit()
    
    # Retrieve session
    retrieved_session = await service.get_session(
        session_id=created_session.id,
        user_id=user_id
    )
    
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_id == user_id
    assert retrieved_session.original_prompt == prompt
    assert retrieved_session.status == "analyzing"


@pytest.mark.asyncio
async def test_get_session_not_found(db_session):
    """Test retrieving a non-existent session raises error."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    fake_session_id = uuid.uuid4()
    
    with pytest.raises(SessionNotFoundError):
        await service.get_session(session_id=fake_session_id, user_id=user_id)


@pytest.mark.asyncio
async def test_get_session_ownership_violation(db_session):
    """Test retrieving another user's session raises error."""
    service = SessionService(db_session)
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    prompt = "I don't understand pointers"
    
    # Create session as owner
    session = await service.create_session(user_id=owner_id, prompt=prompt)
    await db_session.commit()
    
    # Try to access as different user
    with pytest.raises(SessionOwnershipError):
        await service.get_session(session_id=session.id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_update_session_status(db_session):
    """Test updating session status."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand graph algorithms"
    
    # Create session
    session = await service.create_session(user_id=user_id, prompt=prompt)
    await db_session.commit()
    
    # Update status
    updated_session = await service.update_session_status(
        session_id=session.id,
        status="diagnosing"
    )
    
    assert updated_session.status == "diagnosing"
    assert updated_session.completed_at is None


@pytest.mark.asyncio
async def test_update_session_status_to_completed(db_session):
    """Test updating session status to completed sets completed_at."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand lambdas"
    
    # Create session
    session = await service.create_session(user_id=user_id, prompt=prompt)
    await db_session.commit()
    
    # Update status to completed
    updated_session = await service.update_session_status(
        session_id=session.id,
        status="completed"
    )
    
    assert updated_session.status == "completed"
    assert updated_session.completed_at is not None
    assert isinstance(updated_session.completed_at, datetime)


@pytest.mark.asyncio
async def test_update_session_invalid_status(db_session):
    """Test updating session with invalid status raises error."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand async/await"
    
    # Create session
    session = await service.create_session(user_id=user_id, prompt=prompt)
    await db_session.commit()
    
    # Try to update with invalid status
    with pytest.raises(ValueError):
        await service.update_session_status(
            session_id=session.id,
            status="invalid_status"
        )


@pytest.mark.asyncio
async def test_delete_session(db_session):
    """Test deleting a session."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    prompt = "I don't understand closures"
    
    # Create session
    session = await service.create_session(user_id=user_id, prompt=prompt)
    session_id = session.id
    await db_session.commit()
    
    # Delete session
    await service.delete_session(session_id=session_id, user_id=user_id)
    await db_session.commit()
    
    # Verify session is deleted
    result = await db_session.execute(
        select(LearningSession).where(LearningSession.id == session_id)
    )
    deleted_session = result.scalar_one_or_none()
    assert deleted_session is None


@pytest.mark.asyncio
async def test_delete_session_ownership_violation(db_session):
    """Test deleting another user's session raises error."""
    service = SessionService(db_session)
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    prompt = "I don't understand generators"
    
    # Create session as owner
    session = await service.create_session(user_id=owner_id, prompt=prompt)
    await db_session.commit()
    
    # Try to delete as different user
    with pytest.raises(SessionOwnershipError):
        await service.delete_session(session_id=session.id, user_id=other_user_id)


@pytest.mark.asyncio
async def test_delete_session_not_found(db_session):
    """Test deleting a non-existent session raises error."""
    service = SessionService(db_session)
    user_id = uuid.uuid4()
    fake_session_id = uuid.uuid4()
    
    with pytest.raises(SessionNotFoundError):
        await service.delete_session(session_id=fake_session_id, user_id=user_id)
