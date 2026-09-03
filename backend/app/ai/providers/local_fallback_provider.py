"""Deterministic development fallback for temporary AI-provider failures.

The fallback keeps the complete learning loop usable when a development API
key is rate-limited. It deliberately favors predictable, conservative output
over pretending to provide the same semantic quality as the primary model.
"""

from __future__ import annotations

import json
import logging
import re
from typing import AsyncIterator, Type, TypeVar

from pydantic import BaseModel

from app.ai.exceptions import AIProviderError
from app.ai.schemas import (
    ConceptAnalysisOutput,
    DiagnosticEvaluationOutput,
    DiagnosticQuestionOutput,
    PrerequisiteEdge,
    PrerequisiteGraphOutput,
    PrerequisiteNode,
    TeachBackEvaluationOutput,
)


T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "learning-topic"


def _match_value(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default


def _identify_topic(learner_prompt: str) -> tuple[str, str]:
    normalized = learner_prompt.lower()
    known_topics = (
        ("sql join", "SQL Joins", "Databases"),
        ("neural network", "Neural Networks", "Machine Learning"),
        ("recursion", "Recursion", "Computer Science"),
        ("calculus", "Calculus", "Mathematics"),
        ("probability", "Probability", "Mathematics"),
        ("derivative", "Derivatives", "Calculus"),
        ("integration", "Integration", "Calculus"),
    )
    for keyword, name, domain in known_topics:
        if keyword in normalized:
            return name, domain

    cleaned = re.sub(
        r"\b(i|do not|don't|dont|understand|confused|confuses|about|how|why|please|help|me|still)\b",
        " ",
        learner_prompt,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[A-Za-z0-9+#.-]+", cleaned)
    name = " ".join(words[-4:]).strip().title() or "Learning Topic"
    return name, "General Studies"


GRAPH_TEMPLATES: dict[str, tuple[list[str], list[tuple[str, str, float]]]] = {
    "recursion": (
        ["Variables", "Control Flow", "Functions", "Conditionals", "Function Calls", "Base Case", "Call Stack", "Recursion"],
        [
            ("Variables", "Functions", 0.8),
            ("Control Flow", "Conditionals", 0.8),
            ("Functions", "Function Calls", 0.9),
            ("Conditionals", "Base Case", 0.9),
            ("Function Calls", "Call Stack", 0.9),
            ("Base Case", "Recursion", 1.0),
            ("Call Stack", "Recursion", 1.0),
        ],
    ),
    "sql-joins": (
        ["Tables and Rows", "Primary Keys", "Foreign Keys", "SELECT Queries", "Join Conditions", "SQL Joins"],
        [
            ("Tables and Rows", "Primary Keys", 0.8),
            ("Tables and Rows", "SELECT Queries", 0.8),
            ("Primary Keys", "Foreign Keys", 0.9),
            ("Foreign Keys", "Join Conditions", 1.0),
            ("SELECT Queries", "Join Conditions", 0.8),
            ("Join Conditions", "SQL Joins", 1.0),
        ],
    ),
    "neural-networks": (
        ["Linear Algebra", "Functions", "Probability", "Python", "Machine Learning Basics", "Activation Functions", "Gradient Descent", "Backpropagation", "Neural Networks"],
        [
            ("Linear Algebra", "Machine Learning Basics", 0.9),
            ("Functions", "Activation Functions", 0.8),
            ("Probability", "Machine Learning Basics", 0.7),
            ("Python", "Machine Learning Basics", 0.6),
            ("Machine Learning Basics", "Gradient Descent", 0.9),
            ("Activation Functions", "Backpropagation", 0.8),
            ("Gradient Descent", "Backpropagation", 1.0),
            ("Backpropagation", "Neural Networks", 1.0),
        ],
    ),
    "probability": (
        ["Fractions", "Sets", "Counting", "Sample Spaces", "Events", "Conditional Probability", "Probability"],
        [
            ("Fractions", "Probability", 0.7),
            ("Sets", "Sample Spaces", 0.8),
            ("Counting", "Sample Spaces", 0.8),
            ("Sample Spaces", "Events", 1.0),
            ("Events", "Conditional Probability", 0.9),
            ("Conditional Probability", "Probability", 0.8),
        ],
    ),
    "calculus": (
        ["Algebra", "Functions", "Graphs", "Limits", "Rates of Change", "Derivatives", "Integrals", "Calculus"],
        [
            ("Algebra", "Functions", 0.9),
            ("Functions", "Graphs", 0.8),
            ("Graphs", "Limits", 0.9),
            ("Limits", "Derivatives", 1.0),
            ("Rates of Change", "Derivatives", 0.9),
            ("Derivatives", "Integrals", 0.8),
            ("Integrals", "Calculus", 0.9),
        ],
    ),
}


class LocalFallbackProvider:
    """Generate schema-valid educational content without a network call."""

    model = "rootlearn-local-fallback-v1"

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> T:
        del system_prompt, temperature

        if schema is ConceptAnalysisOutput:
            learner_input = _match_value(r'Learner input:\s*"(.*?)"', user_prompt, user_prompt)
            name, domain = _identify_topic(learner_input)
            result = ConceptAnalysisOutput(
                slug=_slugify(name),
                name=name,
                domain=domain,
                description=f"{name} is the learner's target concept. Understanding its foundations and how its parts interact supports accurate practical use.",
            )
            return result  # type: ignore[return-value]

        if schema is PrerequisiteGraphOutput:
            target_name = _match_value(r"Target Concept:\s*([^\n]+)", user_prompt, "Learning Topic")
            target_slug = _slugify(target_name)
            names, relationships = GRAPH_TEMPLATES.get(
                target_slug,
                (
                    ["Core Terminology", "Foundational Ideas", "Worked Examples", target_name],
                    [
                        ("Core Terminology", "Foundational Ideas", 0.9),
                        ("Foundational Ideas", "Worked Examples", 0.8),
                        ("Worked Examples", target_name, 1.0),
                    ],
                ),
            )
            nodes = [
                PrerequisiteNode(
                    slug=_slugify(name),
                    name=name,
                    description=f"{name} provides an important conceptual foundation for understanding {target_name}.",
                )
                for name in names
            ]
            edges = [
                PrerequisiteEdge(
                    source_slug=_slugify(source),
                    target_slug=_slugify(target),
                    importance_weight=weight,
                )
                for source, target, weight in relationships
            ]
            result = PrerequisiteGraphOutput(target_slug=target_slug, nodes=nodes, edges=edges)
            return result  # type: ignore[return-value]

        if schema is DiagnosticQuestionOutput:
            concept_name = _match_value(r"Concept to test:\s*([^\n]+)", user_prompt, "this concept")
            result = DiagnosticQuestionOutput(
                question_text=f"Explain {concept_name} in your own words, describe why it matters, and give one concrete example of how it is used.",
                question_type="reasoning",
                rubric={
                    "key_points": [
                        f"Defines {concept_name} accurately",
                        "Explains its purpose or effect",
                        "Provides a relevant concrete example",
                    ],
                    "correctness_criteria": "The explanation should be conceptually accurate and internally consistent.",
                    "common_misconceptions": ["Confusing the concept with a related mechanism"],
                    "scoring_guide": "Give partial credit for correct ideas even when the explanation is incomplete.",
                },
                difficulty=0.5,
            )
            return result  # type: ignore[return-value]

        if schema is DiagnosticEvaluationOutput:
            answer = _match_value(r"Student Answer:\s*(.*)$", user_prompt, "")
            rubric_text = _match_value(r"Rubric:\s*(.*?)\n\nStudent Answer:", user_prompt, "{}")
            try:
                key_points = json.loads(rubric_text).get("key_points", [])
            except (json.JSONDecodeError, AttributeError):
                key_points = []
            score = self._answer_score(answer)
            demonstrated_count = min(len(key_points), round(score * len(key_points)))
            result = DiagnosticEvaluationOutput(
                correctness_score=score,
                reasoning_score=max(0.0, min(1.0, score + (0.1 if self._shows_reasoning(answer) else -0.05))),
                demonstrated_points=key_points[:demonstrated_count],
                missing_points=key_points[demonstrated_count:],
                misconceptions=[] if score >= 0.4 else ["The answer does not yet show a clear conceptual model."],
            )
            return result  # type: ignore[return-value]

        if schema is TeachBackEvaluationOutput:
            answer = _match_value(r"Student's Explanation:\s*\"(.*?)\"", user_prompt, "")
            score = self._answer_score(answer)
            result = TeachBackEvaluationOutput(
                coverage_score=score,
                reasoning_score=max(0.0, min(1.0, score + (0.1 if self._shows_reasoning(answer) else 0))),
                clarity_score=max(0.1, min(1.0, score + 0.05)),
                demonstrated_points=["Explains the concept in the learner's own words"] if score >= 0.4 else [],
                missing_points=[] if score >= 0.7 else ["Add the core mechanism and a concrete example."],
                misconceptions=[] if score >= 0.4 else ["The explanation needs a clearer connection between cause and effect."],
            )
            return result  # type: ignore[return-value]

        raise AIProviderError(f"Local fallback does not support schema {schema.__name__}")

    async def stream_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        del system_prompt, temperature
        concept = _match_value(r"Current Concept \(Root Gap\):\s*([^\n]+)", user_prompt, "this concept")
        yield (
            f"Let’s connect {concept} to something concrete. What do you think changes step by step, "
            "and what condition tells the process when to stop or move on?"
        )

    @staticmethod
    def _answer_score(answer: str) -> float:
        normalized = answer.strip().lower()
        if not normalized or "unsure" in normalized or "don't know" in normalized or "do not know" in normalized:
            return 0.1
        word_count = len(re.findall(r"\b\w+\b", normalized))
        if word_count >= 45:
            return 0.8
        if word_count >= 25:
            return 0.65
        if word_count >= 12:
            return 0.45
        return 0.25

    @staticmethod
    def _shows_reasoning(answer: str) -> bool:
        normalized = answer.lower()
        return any(marker in normalized for marker in ("because", "therefore", "for example", "so that", "which means"))


class ResilientAIProvider:
    """Use a local provider only when the configured provider is unavailable."""

    def __init__(self, primary, fallback: LocalFallbackProvider | None = None):
        self.primary = primary
        self.fallback = fallback or LocalFallbackProvider()
        self.model = getattr(primary, "model", "unknown")

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[T],
        temperature: float = 0.7,
    ) -> T:
        try:
            return await self.primary.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                temperature=temperature,
            )
        except AIProviderError as exc:
            logger.warning("Primary AI unavailable; using local fallback: %s", type(exc).__name__)
            return await self.fallback.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema,
                temperature=temperature,
            )

    async def stream_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        yielded_primary_content = False
        try:
            async for chunk in self.primary.stream_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            ):
                yielded_primary_content = True
                yield chunk
        except AIProviderError as exc:
            if yielded_primary_content:
                raise
            logger.warning("Primary AI stream unavailable; using local fallback: %s", type(exc).__name__)
            async for chunk in self.fallback.stream_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            ):
                yield chunk
