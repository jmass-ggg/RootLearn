"""Unit tests for target concept persistence."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.ai.schemas import ConceptAnalysisOutput
from app.models import Concept
from app.services.concept_service import ConceptService


@pytest.mark.asyncio
async def test_analysis_flushes_concept_before_linking_it_to_session():
    """The generated concept UUID must be persisted on the learning session."""
    session_id = uuid.uuid4()
    session = SimpleNamespace(normalized_topic=None, target_concept_id=None)
    query_result = MagicMock()
    query_result.scalar_one_or_none.return_value = session

    db = MagicMock()
    db.execute = AsyncMock(return_value=query_result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    def assign_database_defaults():
        concept = db.add.call_args.args[0]
        if isinstance(concept, Concept) and concept.id is None:
            concept.id = uuid.uuid4()

    db.flush.side_effect = assign_database_defaults

    ai_service = MagicMock()
    ai_service.generate_structured = AsyncMock(
        return_value=ConceptAnalysisOutput(
            slug="recursion",
            name="Recursion",
            domain="Computer Science",
            description="A function solving a problem by calling itself.",
        )
    )

    concept = await ConceptService(db, ai_service).analyze_target_concept(
        session_id=session_id,
        prompt="I do not understand recursion",
    )

    assert concept.id is not None
    assert session.target_concept_id == concept.id
    assert session.normalized_topic == "Computer Science"
    db.commit.assert_awaited_once()
