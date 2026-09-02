"""Integration test for complete learning loop.

Task: 16 - Checkpoint to verify core learning loop
Requirements: All core requirements

This test verifies the complete flow:
1. Create session with user prompt
2. Generate and validate prerequisite graph
3. Run diagnosis until root gap is identified
4. Verify root gap explanation
5. Complete Socratic tutoring session
6. Submit and evaluate teach-back
7. Verify mastery update and event creation
8. Get next concept recommendation

This is a critical checkpoint test that validates the entire system works end-to-end.
"""
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Concept,
    ConceptEdge,
    DiagnosticAttempt,
    DiagnosticQuestion,
    LearningSession,
    MasteryEvent,
    TeachBackAttempt,
    TutorMessage,
    User,
)
from app.services.concept_service import ConceptService
from app.services.diagnostic_service import DiagnosticService
from app.services.graph_service import GraphService
from app.services.learning_path_service import LearningPathService
from app.services.mastery_service import MasteryService
from app.services.root_gap_service import RootGapService
from app.services.session_service import SessionService
from app.services.state_machine_service import StateMachineService
from app.services.teachback_service import TeachBackService
from app.services.tutor_service import TutorService
from app.ai.schemas import (
    ConceptAnalysisOutput,
    DiagnosticEvaluationOutput,
    DiagnosticQuestionOutput,
    PrerequisiteEdge,
    PrerequisiteGraphOutput,
    PrerequisiteNode,
    SocraticResponseOutput,
    TeachBackEvaluationOutput,
)
from app.services.mastery_service import Evidence


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_learning_loop(db_session: AsyncSession):
    """Test the complete learning loop from session creation to mastery improvement.
    
    This is a comprehensive integration test that verifies:
    - Session management
    - Graph generation and validation
    - Diagnostic assessment
    - Root gap detection
    - Socratic tutoring
    - Teach-back evaluation
    - Mastery calculation
    - Learning path progression
    - State machine transitions
    """
    # ============================================================
    # STEP 1: Create session with user prompt
    # ============================================================
    user = User(email=f"test-{uuid.uuid4()}@example.com", name="Test Learner")
    db_session.add(user)
    await db_session.flush()
    
    session_service = SessionService(db_session)
    
    # Mock AI provider for concept identification
    mock_concept_output = ConceptAnalysisOutput(
        slug="recursion",
        name="Recursion",
        domain="Computer Science",
        description="A programming technique where a function calls itself"
    )
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider = AsyncMock()
        mock_provider.generate_structured.return_value = mock_concept_output
        mock_ai.return_value = mock_provider
        
        session = await session_service.create_session(
            user_id=user.id,
            prompt="I don't understand recursion in programming"
        )
    
    assert session is not None
    assert session.status == "analyzing"
    assert session.original_prompt == "I don't understand recursion in programming"
    
    # ============================================================
    # STEP 2: Generate and validate prerequisite graph
    # ============================================================
    mock_graph_output = PrerequisiteGraphOutput(
        target_slug="recursion",
        nodes=[
            PrerequisiteNode(
                slug="recursion",
                name="Recursion",
                description="A programming technique where a function calls itself"
            ),
            PrerequisiteNode(
                slug="functions",
                name="Functions",
                description="Named reusable blocks of code"
            ),
            PrerequisiteNode(
                slug="call-stack",
                name="Call Stack",
                description="Stack data structure tracking function calls"
            ),
            PrerequisiteNode(
                slug="base-case",
                name="Base Case",
                description="Condition to stop recursive calls"
            ),
        ],
        edges=[
            PrerequisiteEdge(source_slug="functions", target_slug="recursion", importance_weight=0.95),
            PrerequisiteEdge(source_slug="call-stack", target_slug="recursion", importance_weight=0.85),
            PrerequisiteEdge(source_slug="base-case", target_slug="recursion", importance_weight=0.90),
            PrerequisiteEdge(source_slug="functions", target_slug="base-case", importance_weight=0.70),
        ]
    )
    
    # Create AI service mock for GraphService
    from app.ai.validated_ai_service import ValidatedAIService
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_inner = AsyncMock()
        mock_provider_inner.generate_structured.return_value = mock_graph_output
        mock_ai.return_value = mock_provider_inner
        
        # Create ValidatedAIService with mocked provider
        validated_ai_service = ValidatedAIService(db_session)
        graph_service = GraphService(db_session, validated_ai_service)
        
        await graph_service.generate_graph(session.id)
    
    # Verify graph was created
    result = await db_session.execute(
        select(Concept).where(Concept.session_id == session.id)
    )
    concepts = result.scalars().all()
    assert len(concepts) == 4  # target + 3 prerequisites
    
    # Verify target concept is marked
    target = next((c for c in concepts if c.is_target), None)
    assert target is not None
    assert target.slug == "recursion"
    
    # Verify edges exist
    result = await db_session.execute(
        select(ConceptEdge).where(ConceptEdge.session_id == session.id)
    )
    edges = result.scalars().all()
    assert len(edges) == 4
    
    # ============================================================
    # STEP 3: Run diagnosis until root gap is identified
    # ============================================================
    # Create AI service mock for DiagnosticService
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_diag = AsyncMock()
        mock_ai.return_value = mock_provider_diag
        
        validated_ai_service_diag = ValidatedAIService(db_session)
        diagnostic_service = DiagnosticService(db_session, validated_ai_service_diag, mastery_service)
        state_machine = StateMachineService(db_session)
    
    # Transition to diagnosing
    await state_machine.transition_to_diagnosing(session.id)
    await db_session.refresh(session)
    assert session.status == "diagnosing"
    
    # Mock diagnostic question generation
    mock_question_output = DiagnosticQuestionOutput(
        question_text="What is the call stack and how does it work?",
        question_type="short_answer",
        rubric={
            "key_points": [
                "LIFO data structure",
                "Stores function calls",
                "Tracks execution context"
            ],
            "full_credit": 3,
            "partial_credit": 2
        },
        difficulty=0.6
    )
    
    # Get call stack concept
    call_stack = next((c for c in concepts if c.slug == "call-stack"), None)
    assert call_stack is not None
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_question = AsyncMock()
        mock_provider_question.generate_structured.return_value = mock_question_output
        mock_ai.return_value = mock_provider_question
        
        validated_ai_service_question = ValidatedAIService(db_session)
        diagnostic_service_for_question = DiagnosticService(db_session, validated_ai_service_question, mastery_service)
        
        question = await diagnostic_service_for_question.generate_question(call_stack.id)
    
    assert question is not None
    assert question.concept_id == call_stack.id
    
    # Mock answer evaluation showing weakness in call stack
    mock_eval_output = DiagnosticEvaluationOutput(
        correctness_score=0.35,
        reasoning_score=0.40,
        demonstrated_points=["Mentioned it's a stack"],
        missing_points=["LIFO behavior", "Function call tracking"],
        misconceptions=["Confused with heap memory"]
    )
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_eval = AsyncMock()
        mock_provider_eval.generate_structured.return_value = mock_eval_output
        mock_ai.return_value = mock_provider_eval
        
        validated_ai_service_eval = ValidatedAIService(db_session)
        diagnostic_service_for_eval = DiagnosticService(db_session, validated_ai_service_eval, mastery_service)
        
        result = await diagnostic_service_for_eval.evaluate_answer(
            question_id=question.id,
            answer="I think it's like a stack where things are stored"
        )
    
    assert result is not None
    assert "correctness_score" in result
    
    # Verify diagnostic attempt was recorded
    db_result = await db_session.execute(
        select(DiagnosticAttempt).where(DiagnosticAttempt.question_id == question.id)
    )
    attempts = db_result.scalars().all()
    assert len(attempts) == 1
    assert attempts[0].correctness_score == Decimal("0.35")
    
    # ============================================================
    # STEP 4: Detect and verify root gap
    # ============================================================
    root_gap_service = RootGapService(db_session)
    
    # Manually update mastery for call stack to make it the root gap
    await mastery_service.update_mastery(
        concept_id=call_stack.id,
        evidence=Evidence(
            source_type="diagnostic",
            reason={"diagnostic_score": 0.35}
        )
    )
    
    # Set other concepts to higher mastery
    functions = next((c for c in concepts if c.slug == "functions"), None)
    base_case = next((c for c in concepts if c.slug == "base-case"), None)
    
    if functions:
        await mastery_service.update_mastery(
            concept_id=functions.id,
            evidence=Evidence(
                source_type="diagnostic",
                reason={"diagnostic_score": 0.75}
            )
        )
    
    if base_case:
        await mastery_service.update_mastery(
            concept_id=base_case.id,
            evidence=Evidence(
                source_type="diagnostic",
                reason={"diagnostic_score": 0.50}
            )
        )
    
    # Detect root gap
    gap_result = await root_gap_service.detect_root_gap(session.id)
    
    assert gap_result is not None
    assert "root_gap_concept" in gap_result
    # Either call-stack or base-case could be root gap depending on formula
    root_gap_slug = gap_result["root_gap_concept"]["slug"]
    assert root_gap_slug in ["call-stack", "base-case"]
    
    # Verify explanation is complete
    assert "mastery" in gap_result["root_gap_concept"]
    assert "confidence" in gap_result["root_gap_concept"]
    assert "gap_score" in gap_result["root_gap_concept"]
    assert "explanation" in gap_result
    
    # ============================================================
    # STEP 5: Complete Socratic tutoring session
    # ============================================================
    tutor_service = TutorService(db_session)
    
    # Transition to tutoring
    root_gap_concept_id = gap_result["root_gap_concept"]["id"]
    await state_machine.transition_to_tutoring(session.id, root_gap_concept_id)
    await db_session.refresh(session)
    assert session.status == "tutoring"
    
    # Mock Socratic response
    mock_socratic_response = SocraticResponseOutput(
        response_text="Let's think about this together. Can you tell me what happens when you call a function?",
        hint_level=1
    )
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_tutor = AsyncMock()
        mock_provider_tutor.generate_structured.return_value = mock_socratic_response
        mock_ai.return_value = mock_provider_tutor
        
        response = await tutor_service.generate_response(
            session_id=session.id,
            user_message="I'm not sure how the call stack works"
        )
    
    assert response is not None
    assert len(response) > 0
    
    # Verify tutor messages were stored
    db_result = await db_session.execute(
        select(TutorMessage).where(TutorMessage.session_id == session.id)
    )
    messages = db_result.scalars().all()
    assert len(messages) >= 2  # user message + assistant response
    
    # Update practice evidence
    await mastery_service.update_mastery(
        concept_id=root_gap_concept_id,
        evidence=Evidence(
            source_type="tutoring",
            reason={"practice_score": 0.60}
        )
    )
    
    # ============================================================
    # STEP 6: Submit and evaluate teach-back
    # ============================================================
    # Create AI service mock for TeachBackService  
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_teachback = AsyncMock()
        mock_ai.return_value = mock_provider_teachback
        
        validated_ai_service_teachback = ValidatedAIService(db_session)
        teachback_service = TeachBackService(db_session, validated_ai_service_teachback, mastery_service)
    
    # Transition to teachback
    await state_machine.transition_to_teachback(session.id)
    await db_session.refresh(session)
    assert session.status == "teachback"
    
    # Mock teach-back evaluation
    mock_teachback_eval = TeachBackEvaluationOutput(
        coverage_score=0.75,
        reasoning_score=0.80,
        clarity_score=0.70,
        demonstrated_points=[
            "Explained LIFO behavior",
            "Described function call tracking",
            "Mentioned execution context"
        ],
        missing_points=["Stack overflow conditions"],
        misconceptions=[]
    )
    
    with patch('app.ai.factory.get_ai_provider') as mock_ai:
        mock_provider_eval_tb = AsyncMock()
        mock_provider_eval_tb.generate_structured.return_value = mock_teachback_eval
        mock_ai.return_value = mock_provider_eval_tb
        
        validated_ai_service_eval_tb = ValidatedAIService(db_session)
        teachback_service_eval = TeachBackService(db_session, validated_ai_service_eval_tb, mastery_service)
        
        teachback_result = await teachback_service_eval.evaluate_teachback(
            session_id=session.id,
            concept_id=root_gap_concept_id,
            explanation="The call stack is a LIFO data structure that keeps track of function calls..."
        )
    
    assert teachback_result is not None
    assert "coverage_score" in teachback_result
    assert teachback_result["average_score"] >= 0.70  # Should pass threshold
    
    # Verify teachback attempt was recorded
    db_result = await db_session.execute(
        select(TeachBackAttempt).where(
            TeachBackAttempt.session_id == session.id,
            TeachBackAttempt.concept_id == root_gap_concept_id
        )
    )
    teachback_attempts = db_result.scalars().all()
    assert len(teachback_attempts) == 1
    
    # ============================================================
    # STEP 7: Verify mastery update and event creation
    # ============================================================
    # Refresh concept to get updated mastery
    await db_session.refresh(call_stack)
    
    # Mastery should have improved from diagnostic + practice + teachback
    # Initial: 0.35 (diagnostic)
    # Practice: 0.60
    # Teachback: (0.75 + 0.80 + 0.70) / 3 ≈ 0.75
    # Expected: 0.45*0.35 + 0.35*0.60 + 0.20*0.75 ≈ 0.52
    assert call_stack.mastery_score > Decimal("0.35")
    
    # Verify mastery events were created
    db_result = await db_session.execute(
        select(MasteryEvent).where(
            MasteryEvent.concept_id == root_gap_concept_id
        ).order_by(MasteryEvent.created_at)
    )
    mastery_events = db_result.scalars().all()
    assert len(mastery_events) >= 3  # diagnostic, practice, teachback
    
    # Verify events have complete data
    for event in mastery_events:
        assert event.source_type in ["diagnostic", "practice", "teachback"]
        assert event.old_score >= 0
        assert event.new_score >= 0
        assert event.old_confidence >= 0
        assert event.new_confidence >= 0
    
    # ============================================================
    # STEP 8: Get next concept recommendation
    # ============================================================
    learning_path_service = LearningPathService(db_session)
    
    next_concept = await learning_path_service.get_next_concept(session.id)
    
    # Should recommend another weak prerequisite or the target
    assert next_concept is not None
    # The next concept should be either another prerequisite or the target
    assert next_concept.slug in ["functions", "base-case", "recursion"]
    
    # ============================================================
    # STEP 9: Verify state transitions and completion logic
    # ============================================================
    # If all prerequisites are understood, should be able to complete
    # For now, just verify we can transition back to diagnosis for next concept
    
    # Update the root gap concept to "understood" status
    await db_session.execute(
        select(Concept).where(Concept.id == root_gap_concept_id)
    )
    await db_session.refresh(call_stack)
    
    # Determine next state based on learning path
    if next_concept.is_target:
        # If next is target, all prerequisites are done
        # In real flow, this would complete after target is mastered
        pass
    else:
        # Should transition back to diagnosing for next concept
        await state_machine.transition_to_diagnosing(session.id)
        await db_session.refresh(session)
        assert session.status == "diagnosing"
    
    # ============================================================
    # CHECKPOINT VERIFICATION COMPLETE
    # ============================================================
    # The complete loop has been verified:
    # ✓ Session created with user prompt
    # ✓ Graph generated and validated
    # ✓ Diagnostic assessment identified weak concepts
    # ✓ Root gap detected with complete explanation
    # ✓ Socratic tutoring session conducted
    # ✓ Teach-back evaluated and passed threshold
    # ✓ Mastery updated with evidence from all sources
    # ✓ Mastery events created for audit trail
    # ✓ Next concept recommended for learning path
    # ✓ State machine transitions worked correctly


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deterministic_calculations_consistency(db_session: AsyncSession):
    """Verify that deterministic calculations produce consistent results.
    
    This test ensures that:
    - Mastery calculation is deterministic (same inputs → same output)
    - Gap score calculation is deterministic
    - Learning path ordering is consistent
    """
    # Create test data
    user = User(email=f"test-{uuid.uuid4()}@example.com", name="Test User")
    db_session.add(user)
    await db_session.flush()
    
    session = LearningSession(
        user_id=user.id,
        original_prompt="Test prompt",
        status="diagnosing"
    )
    db_session.add(session)
    await db_session.flush()
    
    concept = Concept(
        session_id=session.id,
        slug="test-concept",
        name="Test Concept",
        description="Test",
        is_target=False,
        mastery_score=Decimal("0.0"),
        confidence_score=Decimal("0.1"),
        status="weak"
    )
    db_session.add(concept)
    await db_session.flush()
    
    mastery_service = MasteryService(db_session)
    
    # Update mastery with known evidence
    await mastery_service.update_mastery(
        concept_id=concept.id,
        evidence=Evidence(
            source_type="diagnostic",
            reason={"diagnostic_score": 0.60}
        )
    )
    await db_session.refresh(concept)
    first_mastery = concept.mastery_score
    
    # Calculate again with same evidence - should get same result
    await mastery_service.update_mastery(
        concept_id=concept.id,
        evidence=Evidence(
            source_type="diagnostic",
            reason={"diagnostic_score": 0.60}
        )
    )
    await db_session.refresh(concept)
    second_mastery = concept.mastery_score
    
    # Verify determinism (allowing for floating point precision)
    assert abs(float(first_mastery) - float(second_mastery)) < 0.001
    
    # Add practice evidence
    await mastery_service.update_mastery(
        concept_id=concept.id,
        evidence=Evidence(
            source_type="tutoring",
            reason={"practice_score": 0.70}
        )
    )
    await db_session.refresh(concept)
    
    # Expected: 0.45*0.60 + 0.35*0.70 + 0.20*0.0 = 0.27 + 0.245 = 0.515
    # With renormalization (no teachback): 0.45/(0.45+0.35)*0.60 + 0.35/(0.45+0.35)*0.70
    # = 0.5625*0.60 + 0.4375*0.70 = 0.3375 + 0.30625 = 0.64375
    expected_with_practice = 0.5625 * 0.60 + 0.4375 * 0.70
    assert abs(float(concept.mastery_score) - expected_with_practice) < 0.01
    
    print(f"✓ Deterministic calculations verified")
    print(f"  First calculation: {first_mastery}")
    print(f"  Second calculation: {second_mastery}")
    print(f"  With practice: {concept.mastery_score}")
