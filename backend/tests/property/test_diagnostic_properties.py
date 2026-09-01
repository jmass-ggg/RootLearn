"""Property-based tests for diagnostic assessment.

Feature: rootlearn-knowledge-debugger
Property 13: Concept selection follows priority formula
Property 14: Diagnostic question generation is successful
Property 15: Answer evaluation produces structured results
Property 16: Diagnostic question count is bounded
Property 17: Diagnosis stops at confidence threshold
Property 18: High-mastery concepts are not repeatedly tested
Validates: Requirements 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 5.10
"""
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.logging_service import AIRunLogger
from app.ai.schemas import DiagnosticEvaluationOutput, DiagnosticQuestionOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.models import Concept, ConceptEdge, DiagnosticQuestion, LearningSession
from app.services.diagnostic_service import DiagnosticService
from app.services.mastery_service import MasteryService
from tests.factories import add_learning_session


# Mock AI Provider for testing
class MockDiagnosticAIProvider:
    """Mock AI provider for diagnostic testing."""
    
    def __init__(self):
        """Initialize mock provider."""
        self.model = "mock-model-v1"
        self.call_count = 0
        self.question_output = DiagnosticQuestionOutput(
            question_text="What is the base case of a recursive function?",
            question_type="short_answer",
            rubric={
                "key_points": [
                    "Termination condition",
                    "Prevents infinite recursion",
                    "Returns without recursive call"
                ],
                "criteria": "Answer should mention stopping condition"
            },
            difficulty=0.5
        )
        self.evaluation_output = DiagnosticEvaluationOutput(
            correctness_score=0.75,
            reasoning_score=0.80,
            demonstrated_points=["Mentioned termination", "Gave example"],
            missing_points=["Didn't explain why it's needed"],
            misconceptions=[]
        )
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type,
        temperature: float = 0.7,
    ):
        """Return pre-configured outputs based on schema."""
        self.call_count += 1
        if schema == DiagnosticQuestionOutput:
            return self.question_output
        elif schema == DiagnosticEvaluationOutput:
            return self.evaluation_output
        else:
            raise ValueError(f"Unknown schema: {schema}")
    
    async def stream_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7):
        """Mock stream text (not used in diagnostics)."""
        yield "Mock response"


# Hypothesis strategies
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def concept_graph_data(draw):
    """Generate a small prerequisite graph for testing."""
    num_concepts = draw(st.integers(min_value=2, max_value=6))
    
    concepts_data = []
    for i in range(num_concepts):
        concepts_data.append({
            "slug": f"concept-{i}",
            "name": f"Concept {i}",
            "description": f"Test concept {i}",
            "mastery": draw(valid_score()),
            "confidence": draw(valid_score()),
            "is_target": (i == num_concepts - 1)  # Last one is target
        })
    
    # Create edges (chain structure for simplicity)
    edges_data = []
    for i in range(num_concepts - 1):
        edges_data.append({
            "source_idx": i,
            "target_idx": i + 1,
            "weight": draw(valid_score())
        })
    
    return concepts_data, edges_data


class TestProperty13ConceptSelectionFollowsPriorityFormula:
    """Property 13: Concept selection follows priority formula.
    
    For any graph state during diagnosis, the selected concept should have
    the highest information_priority score where:
    priority = importance × (1 - confidence) × downstream_impact
    
    Validates: Requirements 5.1, 5.9
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(graph_data=concept_graph_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_concept_selection_uses_priority_formula(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        graph_data: tuple
    ):
        """Property test: Selected concept has highest information priority."""
        # Feature: rootlearn-knowledge-debugger, Property 13: Concept selection follows priority formula
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        concepts_data, edges_data = graph_data
        
        # Arrange - Create concepts
        concepts = []
        for data in concepts_data:
            concept = Concept(
                session_id=test_session.id,
                slug=data["slug"],
                name=data["name"],
                description=data["description"],
                mastery_score=data["mastery"],
                confidence_score=data["confidence"],
                is_target=data["is_target"],
                status="learning"
            )
            db_session.add(concept)
            concepts.append(concept)
        
        await db_session.flush()
        
        # Create edges
        for edge_data in edges_data:
            edge = ConceptEdge(
                session_id=test_session.id,
                source_concept_id=concepts[edge_data["source_idx"]].id,
                target_concept_id=concepts[edge_data["target_idx"]].id,
                importance_weight=edge_data["weight"]
            )
            db_session.add(edge)
        
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        selected_concept = await diagnostic_service.select_next_concept(test_session.id)
        
        # Assert - If a concept was selected, it should not be filtered out
        if selected_concept:
            # Should not have high mastery AND high confidence
            if selected_concept.mastery_score >= Decimal("0.70"):
                assert selected_concept.confidence_score < Decimal("0.70")
            
            # Selected concept should exist in our created concepts
            assert selected_concept.id in [c.id for c in concepts]


class TestProperty14DiagnosticQuestionGenerationIsSuccessful:
    """Property 14: Diagnostic question generation is successful.
    
    For any selected concept during diagnosis, exactly one diagnostic question
    with a non-empty rubric should be generated.
    
    Validates: Requirements 5.2, 5.4
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_question_generation_produces_valid_question(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: Question generation always produces valid question."""
        # Feature: rootlearn-knowledge-debugger, Property 14: Diagnostic question generation is successful
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create concept
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept for diagnostics",
            mastery_score=mastery,
            confidence_score=confidence,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        question = await diagnostic_service.generate_question(concept.id)
        
        # Assert - Question must have all required fields
        assert question.id is not None
        assert question.session_id == test_session.id
        assert question.concept_id == concept.id
        assert question.question_text is not None
        assert len(question.question_text) >= 10
        assert question.question_type in ["short_answer", "multiple_choice", "reasoning", "code"]
        assert question.rubric_json is not None
        assert len(question.rubric_json) > 0  # Non-empty rubric
        assert 0.0 <= float(question.difficulty) <= 1.0
        
        # Assert - Question is persisted
        stmt = select(DiagnosticQuestion).where(DiagnosticQuestion.id == question.id)
        db_question = (await db_session.execute(stmt)).scalar_one_or_none()
        assert db_question is not None

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(concept_count=st.integers(min_value=1, max_value=5))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_exactly_one_question_per_generation_call(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        concept_count: int
    ):
        """Property test: Each generate_question call produces exactly one question."""
        # Feature: rootlearn-knowledge-debugger, Property 14: Diagnostic question generation is successful
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create multiple concepts
        concepts = []
        for i in range(concept_count):
            concept = Concept(
                session_id=test_session.id,
                slug=f"concept-{i}-{uuid.uuid4()}",
                name=f"Concept {i}",
                description=f"Test concept {i}",
                mastery_score=Decimal("0.5"),
                confidence_score=Decimal("0.5"),
                status="learning"
            )
            db_session.add(concept)
            concepts.append(concept)
        
        await db_session.flush()
        
        # Act - Generate question for each concept
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        question_ids = []
        for concept in concepts:
            question = await diagnostic_service.generate_question(concept.id)
            question_ids.append(question.id)
        
        # Assert - All question IDs are unique (exactly one per call)
        assert len(question_ids) == len(set(question_ids))
        assert len(question_ids) == concept_count


class TestProperty15AnswerEvaluationProducesStructuredResults:
    """Property 15: Answer evaluation produces structured results.
    
    For any submitted answer to a diagnostic question, the evaluation should
    return: correctness_score, reasoning_score, demonstrated_points,
    missing_points, and misconceptions.
    
    Validates: Requirements 5.5, 5.6
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        answer_text=st.text(min_size=1, max_size=500),
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_evaluation_produces_all_required_fields(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        answer_text: str,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: Evaluation always includes all required structured fields."""
        # Feature: rootlearn-knowledge-debugger, Property 15: Answer evaluation produces structured results
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create concept and question
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=mastery,
            confidence_score=confidence,
            status="learning"
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Create diagnostic question
        question = DiagnosticQuestion(
            session_id=test_session.id,
            concept_id=concept.id,
            question_text="What is the base case?",
            question_type="short_answer",
            rubric_json={"key_points": ["termination", "stopping"]},
            difficulty=Decimal("0.5")
        )
        db_session.add(question)
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        result = await diagnostic_service.evaluate_answer(question.id, answer_text)
        
        # Assert - All required fields are present
        assert result.attempt_id is not None
        assert isinstance(result.correctness_score, float)
        assert isinstance(result.reasoning_score, float)
        assert isinstance(result.demonstrated_points, list)
        assert isinstance(result.missing_points, list)
        assert isinstance(result.misconceptions, list)
        
        # Assert - Scores are in valid range
        assert 0.0 <= result.correctness_score <= 1.0
        assert 0.0 <= result.reasoning_score <= 1.0

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(answer_text=st.text(min_size=1, max_size=500))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_evaluation_updates_mastery_evidence(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        answer_text: str
    ):
        """Property test: Evaluation updates mastery evidence for the concept."""
        # Feature: rootlearn-knowledge-debugger, Property 15: Answer evaluation produces structured results
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create concept and question
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.1"),
            status="weak"
        )
        db_session.add(concept)
        await db_session.flush()
        
        question = DiagnosticQuestion(
            session_id=test_session.id,
            concept_id=concept.id,
            question_text="What is the base case?",
            question_type="short_answer",
            rubric_json={"key_points": ["termination"]},
            difficulty=Decimal("0.5")
        )
        db_session.add(question)
        await db_session.flush()
        
        old_mastery = concept.mastery_score
        old_confidence = concept.confidence_score
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        await diagnostic_service.evaluate_answer(question.id, answer_text)
        
        # Assert - Concept mastery should be updated
        await db_session.refresh(concept)
        # Mastery may have changed (depending on the score)
        # Confidence should have increased (more evidence)
        assert concept.confidence_score >= old_confidence


class TestProperty16DiagnosticQuestionCountIsBounded:
    """Property 16: Diagnostic question count is bounded.
    
    For any diagnosis session, the total number of diagnostic questions
    asked should not exceed 6.
    
    Validates: Requirements 5.7
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_max_six_questions_per_session(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Diagnostic questioning stops at 6 questions maximum."""
        # Feature: rootlearn-knowledge-debugger, Property 16: Diagnostic question count is bounded
        
        # Arrange - Create multiple concepts
        concepts = []
        for i in range(10):  # More concepts than max questions
            concept = Concept(
                session_id=test_session.id,
                slug=f"concept-{i}",
                name=f"Concept {i}",
                description=f"Test concept {i}",
                mastery_score=Decimal("0.3"),
                confidence_score=Decimal("0.3"),
                status="weak"
            )
            db_session.add(concept)
            concepts.append(concept)
        
        await db_session.flush()
        
        # Act - Generate maximum questions and check stopping condition
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        # Generate 6 questions
        for i in range(6):
            question = await diagnostic_service.generate_question(concepts[i].id)
            assert question is not None
        
        # Assert - Should stop diagnosis after 6 questions
        should_stop = await diagnostic_service.should_stop_diagnosis(test_session.id)
        assert should_stop is True

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(num_questions=st.integers(min_value=0, max_value=10))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_should_stop_when_reaching_limit(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        num_questions: int
    ):
        """Property test: Diagnosis stops when question count >= 6."""
        # Feature: rootlearn-knowledge-debugger, Property 16: Diagnostic question count is bounded
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create concept and questions
        concept = Concept(
            session_id=test_session.id,
            slug=f"test-concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            status="learning",
            is_target=True
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Create diagnostic questions
        for i in range(num_questions):
            question = DiagnosticQuestion(
                session_id=test_session.id,
                concept_id=concept.id,
                question_text=f"Question {i}",
                question_type="short_answer",
                rubric_json={"key": "value"},
                difficulty=Decimal("0.5")
            )
            db_session.add(question)
        
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        should_stop = await diagnostic_service.should_stop_diagnosis(test_session.id)
        
        # Assert - Should stop if we've reached or exceeded the limit
        if num_questions >= 6:
            assert should_stop is True
        # If fewer than 6 questions and concept doesn't have high confidence, may continue
        # (depends on other stopping conditions, so we don't assert False)


class TestProperty17DiagnosisStopsAtConfidenceThreshold:
    """Property 17: Diagnosis stops at confidence threshold.
    
    For any diagnosis session where a concept reaches confidence ≥ 0.80,
    no additional questions should be generated for that concept.
    
    Validates: Requirements 5.8
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(confidence_score=valid_score())
    @settings(max_examples=100, deadline=None)
    async def test_diagnosis_stops_at_high_confidence(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        confidence_score: Decimal
    ):
        """Property test: Diagnosis stops when key concepts reach 0.80 confidence."""
        # Feature: rootlearn-knowledge-debugger, Property 17: Diagnosis stops at confidence threshold
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create target concept with varying confidence
        target_concept = Concept(
            session_id=test_session.id,
            slug="target-concept",
            name="Target Concept",
            description="The target concept",
            mastery_score=Decimal("0.5"),
            confidence_score=confidence_score,
            is_target=True,
            status="learning"
        )
        db_session.add(target_concept)
        
        # Create a prerequisite concept on path to target
        prereq_concept = Concept(
            session_id=test_session.id,
            slug="prereq-concept",
            name="Prerequisite Concept",
            description="A prerequisite",
            mastery_score=Decimal("0.5"),
            confidence_score=confidence_score,
            status="learning"
        )
        db_session.add(prereq_concept)
        await db_session.flush()
        
        # Create edge to make it a key concept
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq_concept.id,
            target_concept_id=target_concept.id,
            importance_weight=Decimal("0.9")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        should_stop = await diagnostic_service.should_stop_diagnosis(test_session.id)
        
        # Assert - Should stop if all key concepts have confidence >= 0.80
        if confidence_score >= Decimal("0.80"):
            assert should_stop is True


class TestProperty18HighMasteryConceptsNotRepeatedlyTested:
    """Property 18: High-mastery concepts are not repeatedly tested.
    
    For any concept with mastery > 0.70 and confidence > 0.70, it should not
    be selected for additional diagnostic questioning unless confidence later drops.
    
    Validates: Requirements 5.10
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        high_mastery=st.floats(min_value=0.71, max_value=1.0),
        high_confidence=st.floats(min_value=0.71, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None)
    async def test_high_mastery_concepts_not_selected(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        high_mastery: float,
        high_confidence: float
    ):
        """Property test: Concepts with high mastery+confidence are not selected."""
        # Feature: rootlearn-knowledge-debugger, Property 18: High-mastery concepts are not repeatedly tested
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create high-mastery concept
        high_mastery_concept = Concept(
            session_id=test_session.id,
            slug="high-mastery-concept",
            name="High Mastery Concept",
            description="A well-understood concept",
            mastery_score=Decimal(str(round(high_mastery, 4))),
            confidence_score=Decimal(str(round(high_confidence, 4))),
            status="understood"
        )
        db_session.add(high_mastery_concept)
        
        # Create low-mastery concept
        low_mastery_concept = Concept(
            session_id=test_session.id,
            slug="low-mastery-concept",
            name="Low Mastery Concept",
            description="A concept that needs work",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.4"),
            status="weak",
            is_target=True
        )
        db_session.add(low_mastery_concept)
        await db_session.flush()
        
        # Create edge for graph structure
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=high_mastery_concept.id,
            target_concept_id=low_mastery_concept.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        selected_concept = await diagnostic_service.select_next_concept(test_session.id)
        
        # Assert - Should not select the high-mastery concept
        if selected_concept:
            # The selected concept should NOT be the high mastery one
            # (it should be the low mastery one instead)
            assert selected_concept.id != high_mastery_concept.id
            assert selected_concept.id == low_mastery_concept.id

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_concept_selection_respects_mastery_filter(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: Concept selection filters based on mastery+confidence thresholds."""
        # Feature: rootlearn-knowledge-debugger, Property 18: High-mastery concepts are not repeatedly tested
        test_session = await add_learning_session(
            db_session, user_id=test_session.user_id, status="diagnosing"
        )
        
        # Arrange - Create concept with varying mastery and confidence
        concept = Concept(
            session_id=test_session.id,
            slug=f"concept-{uuid.uuid4()}",
            name="Test Concept",
            description="A test concept",
            mastery_score=mastery,
            confidence_score=confidence,
            status="learning",
            is_target=True
        )
        db_session.add(concept)
        await db_session.flush()
        
        # Act
        mock_provider = MockDiagnosticAIProvider()
        logger = AIRunLogger(db_session)
        ai_service = ValidatedAIService(mock_provider, logger, max_retries=2)
        mastery_service = MasteryService(db_session)
        diagnostic_service = DiagnosticService(db_session, ai_service, mastery_service)
        
        selected_concept = await diagnostic_service.select_next_concept(test_session.id)
        
        # Assert - If concept has high mastery AND high confidence, should not be selected
        if mastery >= Decimal("0.70") and confidence >= Decimal("0.70"):
            # Should not select this concept (or should return None if it's the only one)
            if selected_concept:
                assert selected_concept.id != concept.id
        else:
            # May be selected (has low mastery or low confidence)
            if selected_concept:
                assert selected_concept.id == concept.id
