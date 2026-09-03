"""Tests for the development AI quota fallback."""

from unittest.mock import AsyncMock

import pytest

from app.ai.exceptions import AIProviderRateLimitError
from app.ai.providers.local_fallback_provider import LocalFallbackProvider, ResilientAIProvider
from app.ai.schemas import (
    ConceptAnalysisOutput,
    DiagnosticEvaluationOutput,
    DiagnosticQuestionOutput,
    PrerequisiteGraphOutput,
)
from app.services.graph_service import GraphService


@pytest.mark.asyncio
async def test_recursion_prompt_builds_valid_local_graph():
    provider = LocalFallbackProvider()
    concept = await provider.generate_structured(
        system_prompt="",
        user_prompt='Learner input: "I understand functions, but recursion still confuses me."',
        schema=ConceptAnalysisOutput,
    )

    graph = await provider.generate_structured(
        system_prompt="",
        user_prompt=f"Target Concept: {concept.name}\n\nDescription: {concept.description}",
        schema=PrerequisiteGraphOutput,
    )

    assert concept.name == "Recursion"
    assert graph.target_slug == "recursion"
    assert {node.name for node in graph.nodes} >= {"Functions", "Base Case", "Call Stack", "Recursion"}
    assert GraphService(None, None).validate_graph_structure(graph).is_valid  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_local_fallback_supports_diagnostic_question_and_evaluation():
    provider = LocalFallbackProvider()
    question = await provider.generate_structured(
        system_prompt="",
        user_prompt="Concept to test: Base Case\n\nDescription: Stops recursion.",
        schema=DiagnosticQuestionOutput,
    )
    evaluation = await provider.generate_structured(
        system_prompt="",
        user_prompt=(
            f"Question: {question.question_text}\n\nRubric:\n"
            f"{{\"key_points\": [\"Defines a base case\", \"Explains why it stops\"]}}\n\n"
            "Student Answer: A base case is the condition that stops recursive calls, because otherwise the function would continue forever."
        ),
        schema=DiagnosticEvaluationOutput,
    )

    assert question.question_type == "reasoning"
    assert evaluation.correctness_score > 0
    assert evaluation.demonstrated_points


@pytest.mark.asyncio
async def test_resilient_provider_falls_back_on_rate_limit():
    primary = AsyncMock()
    primary.model = "rate-limited-model"
    primary.generate_structured.side_effect = AIProviderRateLimitError("quota exhausted")
    provider = ResilientAIProvider(primary)

    result = await provider.generate_structured(
        system_prompt="",
        user_prompt='Learner input: "Recursion confuses me"',
        schema=ConceptAnalysisOutput,
    )

    assert result.name == "Recursion"
