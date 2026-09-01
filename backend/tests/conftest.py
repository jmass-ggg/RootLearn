"""Pytest configuration and fixtures for tests."""
import os
from typing import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from hypothesis import HealthCheck, settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from app.models import User, LearningSession, Concept, ConceptEdge


# Database-backed property tests intentionally share their function-scoped
# fixture across generated examples.  The tests create unique rows for each
# example, and the database is recreated for every test function.
settings.register_profile(
    "database",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
settings.load_profile("database")


# Use a separate test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn_test"
)


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
        try:
            yield session
        finally:
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
