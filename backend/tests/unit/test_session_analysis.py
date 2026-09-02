"""Tests for the session analysis background workflow."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from app.routes.sessions import analyze_session_background


@pytest.mark.asyncio
async def test_background_analysis_advances_session_to_diagnosing():
    """A completed concept and graph analysis must leave the polling state."""
    session_id = uuid.uuid4()
    db = AsyncMock()

    @asynccontextmanager
    async def db_context():
        yield db

    concept = SimpleNamespace(slug="recursion")
    graph = SimpleNamespace(nodes=[object(), object()], edges=[object()])

    with (
        patch("app.routes.sessions.get_db_context", db_context),
        patch("app.routes.sessions.get_ai_provider", return_value=MagicMock()),
        patch("app.routes.sessions.ConceptService") as concept_service_class,
        patch("app.routes.sessions.GraphService") as graph_service_class,
        patch("app.routes.sessions.StateMachineService") as state_machine_class,
    ):
        concept_service_class.return_value.analyze_target_concept = AsyncMock(
            return_value=concept
        )
        graph_service_class.return_value.generate_graph = AsyncMock(return_value=graph)
        state_machine_class.return_value.transition_to_diagnosing = AsyncMock()

        await analyze_session_background(session_id, "Explain recursion")

        concept_service_class.return_value.analyze_target_concept.assert_awaited_once_with(
            session_id=session_id,
            prompt="Explain recursion",
        )
        graph_service_class.return_value.generate_graph.assert_awaited_once_with(session_id)
        state_machine_class.return_value.transition_to_diagnosing.assert_awaited_once_with(
            session_id
        )


@pytest.mark.asyncio
async def test_background_analysis_marks_failed_session_abandoned():
    """An analysis error must not leave the frontend polling indefinitely."""
    session_id = uuid.uuid4()
    analysis_db = AsyncMock()
    failure_db = AsyncMock()
    session = SimpleNamespace(status="analyzing")
    result = MagicMock()
    result.scalar_one_or_none.return_value = session
    failure_db.execute.return_value = result
    databases = iter((analysis_db, failure_db))

    @asynccontextmanager
    async def db_context():
        yield next(databases)

    with (
        patch("app.routes.sessions.get_db_context", db_context),
        patch("app.routes.sessions.get_ai_provider", side_effect=RuntimeError("AI unavailable")),
    ):
        await analyze_session_background(session_id, "Explain recursion")

    assert session.status == "abandoned"
    failure_db.flush.assert_awaited_once()
