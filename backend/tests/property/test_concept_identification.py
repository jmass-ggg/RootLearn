"""Property-based tests for concept identification.

Feature: rootlearn-knowledge-debugger
Property 4: Target concept extraction produces valid structure
Property 5: Target concept is marked correctly
Validates: Requirements 2.1, 2.4, 2.5
"""
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, strategies as st
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.logging_service import AIRunLogger
from app.ai.schemas import ConceptAnalysisOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.models import Concept, LearningSession
from app.services.concept_service import ConceptService


# Mock AI Provider for testing
class MockAIProvider:
    """Mock AI provider for testing concept identification."""
    
    def __init__(self, concept_output: ConceptAnalysisOutput):
        """Initialize mock provider with a specific output."""
        self.concept_output = concept_output
        self.model = "mock-model-v1"
        self.call_count = 0
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type,
        temperature: float = 0.7,
    ):
        """Return the pre-configured concept output."""
        self.call_count += 1
        return self.concept_output
    
    async def stream_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7):
        """Mock stream text (not used in concept identification)."""
        yield "Mock response"


# Hypothesis strategies
@st.composite
def learner_prompt_strategy(draw):
    """Generate realistic learner prompts."""
    templates = [
        "I don't understand {}",
        "What is {}?",
        "How does {} work?",
        "{} is confusing me",
        "Can you explain {}?",
        "I'm struggling with {}",
        "Help me understand {}",
    ]
    
    topics = [
        "recursion",
        "React hooks",
        "async/await",
        "neural networks",
        "calculus",
        "pointers",
        "REST APIs",
        "blockchain",
        "inheritance",
        "closures"
    ]
    
    template = draw(st.sampled_from(templates))
    topic = draw(st.sampled_from(topics))
    
    return template.format(topic)


@st.composite
def valid_concept_output(draw):
    """Generate valid ConceptAnalysisOutput."""
    slugs = ["recursion", "react-hooks", "async-await", "neural-networks", 
             "calculus", "pointers", "rest-apis", "blockchain", "inheritance", "closures"]
    names = ["Recursion", "React Hooks", "Async/Await", "Neural Networks",
             "Calculus", "Pointers", "REST APIs", "Blockchain", "Inheritance", "Closures"]
    domains = ["Computer Science", "Web Development", "Programming", "Machine Learning",
               "Mathematics", "Systems Programming", "API Design", "Distributed Systems"]
    descriptions = [
        "A programming technique where a function calls itself to solve problems.",
        "Functions that let you use state and lifecycle features in React function components.",
        "JavaScript patterns for handling asynchronous operations.",
        "Computing systems inspired by biological neural networks.",
        "Mathematical study of continuous change.",
        "Variables that store memory addresses.",
        "Architectural style for designing networked applications.",
        "Distributed ledger technology for recording transactions.",
        "Object-oriented concept for deriving classes from parent classes.",
        "Functions that have access to outer scope variables.",
    ]
    
    idx = draw(st.integers(min_value=0, max_value=len(slugs) - 1))
    
    return ConceptAnalysisOutput(
        slug=slugs[idx],
        name=names[idx],
        domain=draw(st.sampled_from(domains)),
        description=descriptions[idx]
    )


class TestProperty4TargetConceptExtractionProducesValidStructure:
    """Property 4: Target concept extraction produces valid structure.
    
    For any valid user prompt submitted to the concept analyzer, the returned
    concept should have all required fields (slug, name, domain, description)
    populated with non-empty values.
    
    Validates: Requirements 2.1, 2.3, 2.4
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        prompt=learner_prompt_strategy(),
        concept_output=valid_concept_output()
    )
    @settings(max_examples=100, deadline=None)
    async def test_extracted_concept_has_all_required_fields(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        prompt: str,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Extracted concepts have all required non-empty fields."""
        # Feature: rootlearn-knowledge-debugger, Property 4: Target concept extraction produces valid structure
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt=prompt
        )
        
        # Assert - All required fields must be non-empty
        assert result.slug is not None and len(result.slug) > 0
        assert result.name is not None and len(result.name) > 0
        assert result.description is not None and len(result.description) > 0
        
        # Assert - Fields match the AI output
        assert result.slug == concept_output.slug
        assert result.name == concept_output.name
        assert result.description == concept_output.description
        
        # Assert - Concept is stored in database
        stmt = select(Concept).where(Concept.id == result.id)
        db_concept = (await db_session.execute(stmt)).scalar_one_or_none()
        assert db_concept is not None
        assert db_concept.slug == concept_output.slug

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_output=valid_concept_output())
    @settings(max_examples=100, deadline=None)
    async def test_slug_is_url_safe(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Concept slugs are URL-safe (lowercase, hyphenated)."""
        # Feature: rootlearn-knowledge-debugger, Property 4: Target concept extraction produces valid structure
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Slug must be URL-safe
        assert result.slug == result.slug.lower()  # Lowercase
        assert all(c.isalnum() or c in ['-', '_'] for c in result.slug)  # Only alphanumeric, hyphens, underscores
        assert not result.slug.startswith('-')  # No leading hyphen
        assert not result.slug.endswith('-')  # No trailing hyphen

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_output=valid_concept_output())
    @settings(max_examples=100, deadline=None)
    async def test_description_is_meaningful(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Concept descriptions are meaningful (at least 10 characters)."""
        # Feature: rootlearn-knowledge-debugger, Property 4: Target concept extraction produces valid structure
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Description must be meaningful (validated by schema, but double-check)
        assert len(result.description) >= 10


class TestProperty5TargetConceptIsMarkedCorrectly:
    """Property 5: Target concept is marked correctly.
    
    For any identified target concept stored in the database, the is_target
    flag should be true.
    
    Validates: Requirements 2.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        prompt=learner_prompt_strategy(),
        concept_output=valid_concept_output()
    )
    @settings(max_examples=100, deadline=None)
    async def test_target_concept_has_is_target_true(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        prompt: str,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: All target concepts have is_target=True."""
        # Feature: rootlearn-knowledge-debugger, Property 5: Target concept is marked correctly
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt=prompt
        )
        
        # Assert - is_target must be True
        assert result.is_target is True
        
        # Assert - Verify in database
        stmt = select(Concept).where(Concept.id == result.id)
        db_concept = (await db_session.execute(stmt)).scalar_one_or_none()
        assert db_concept is not None
        assert db_concept.is_target is True

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_output=valid_concept_output())
    @settings(max_examples=100, deadline=None)
    async def test_session_updated_with_target_concept(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Session is updated with target_concept_id."""
        # Feature: rootlearn-knowledge-debugger, Property 5: Target concept is marked correctly
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Initially session should have no target concept
        assert test_session.target_concept_id is None
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Session should now reference this concept
        await db_session.refresh(test_session)
        assert test_session.target_concept_id == result.id
        
        # Assert - Can retrieve target concept via service
        target = await concept_service.get_target_concept(test_session.id)
        assert target is not None
        assert target.id == result.id
        assert target.is_target is True

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_output=valid_concept_output())
    @settings(max_examples=100, deadline=None)
    async def test_session_normalized_topic_is_set(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Session normalized_topic is set to the concept domain."""
        # Feature: rootlearn-knowledge-debugger, Property 5: Target concept is marked correctly
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Initially session should have no normalized topic
        assert test_session.normalized_topic is None
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Session normalized_topic should be set to domain
        await db_session.refresh(test_session)
        assert test_session.normalized_topic is not None
        assert test_session.normalized_topic == concept_output.domain

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_only_one_target_concept_per_session(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
    ):
        """Property test: Each session should have exactly one target concept."""
        # Feature: rootlearn-knowledge-debugger, Property 5: Target concept is marked correctly
        
        # Arrange
        concept1 = ConceptAnalysisOutput(
            slug="recursion",
            name="Recursion",
            domain="Computer Science",
            description="A function that calls itself."
        )
        
        mock_provider = MockAIProvider(concept1)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act - Create target concept
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Only one concept should be marked as target
        stmt = select(Concept).where(
            Concept.session_id == test_session.id,
            Concept.is_target == True
        )
        target_concepts = (await db_session.execute(stmt)).scalars().all()
        assert len(target_concepts) == 1
        assert target_concepts[0].id == result.id

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_output=valid_concept_output())
    @settings(max_examples=100, deadline=None)
    async def test_target_concept_has_initial_mastery_state(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_output: ConceptAnalysisOutput
    ):
        """Property test: Target concepts are initialized with default mastery values."""
        # Feature: rootlearn-knowledge-debugger, Property 5: Target concept is marked correctly
        
        # Arrange
        mock_provider = MockAIProvider(concept_output)
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        concept_service = ConceptService(db_session, ai_service)
        
        # Act
        result = await concept_service.analyze_target_concept(
            session_id=test_session.id,
            prompt="Test prompt"
        )
        
        # Assert - Initial mastery state
        assert float(result.mastery_score) == 0.0
        assert float(result.confidence_score) == 0.1
        assert result.status == "unknown"
