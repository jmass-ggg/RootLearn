"""Pytest configuration and fixtures for tests."""
import asyncio
import os
from typing import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from app.models import User, LearningSession, Concept, ConceptEdge


# Use a separate test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable connection pooling for tests
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session() as session:
        async with session.begin():
            yield session
            # Rollback to ensure test isolation
            await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with unique email."""
    import uuid as uuid_module
    user = User(email=f"test-{uuid_module.uuid4()}@example.com", name="Test User")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_session(db_session: AsyncSession, test_user: User) -> LearningSession:
    """Create a test learning session."""
    session = LearningSession(
        user_id=test_user.id,
        original_prompt="I don't understand recursion",
        status="analyzing"
    )
    db_session.add(session)
    await db_session.flush()
    return session


@pytest_asyncio.fixture
async def test_concept(db_session: AsyncSession, test_session: LearningSession) -> Concept:
    """Create a test concept."""
    concept = Concept(
        session_id=test_session.id,
        slug="recursion",
        name="Recursion",
        description="A function calling itself",
        is_target=True,
        mastery_score=Decimal("0.5"),
        confidence_score=Decimal("0.7"),
        status="learning"
    )
    db_session.add(concept)
    await db_session.flush()
    return concept
