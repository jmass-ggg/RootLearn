"""Diagnostic assessment service for RootLearn.

This service handles adaptive diagnostic questioning:
- Select most informative concepts to test
- Generate diagnostic questions via AI
- Evaluate answers via AI
- Update mastery evidence
- Determine when diagnosis is sufficient

Requirements: 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal

import networkx as nx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import (
    DIAGNOSTIC_EVALUATION_SYSTEM_PROMPT,
    DIAGNOSTIC_EVALUATION_VERSION,
    DIAGNOSTIC_QUESTION_SYSTEM_PROMPT,
    DIAGNOSTIC_QUESTION_VERSION,
    get_diagnostic_evaluation_user_prompt,
    get_diagnostic_question_user_prompt,
)
from app.ai.schemas import DiagnosticEvaluationOutput, DiagnosticQuestionOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.logging_config import get_logger
from app.models import (
    Concept,
    ConceptEdge,
    DiagnosticAttempt,
    DiagnosticQuestion,
    LearningSession,
)
from app.services.mastery_service import Evidence, MasteryService

logger = get_logger(__name__)


@dataclass
class DiagnosticResult:
    """Result of diagnostic answer evaluation."""
    
    attempt_id: uuid.UUID
    correctness_score: float
    reasoning_score: float
    demonstrated_points: list[str]
    missing_points: list[str]
    misconceptions: list[str]


class DiagnosticService:
    """Service for adaptive diagnostic assessment.
    
    This service implements the concept selection algorithm that prioritizes
    concepts based on information value, then generates and evaluates
    diagnostic questions.
    """
    
    # Maximum diagnostic questions per session (Requirement 5.7)
    MAX_QUESTIONS_PER_SESSION = 6
    
    # Stopping conditions (Requirement 5.8)
    CONFIDENCE_THRESHOLD = Decimal("0.80")
    
    # High mastery filter (Requirement 5.10)
    HIGH_MASTERY_THRESHOLD = Decimal("0.70")
    HIGH_CONFIDENCE_THRESHOLD = Decimal("0.70")

    def __init__(
        self,
        db: AsyncSession,
        ai_service: ValidatedAIService,
        mastery_service: MasteryService,
    ):
        """Initialize diagnostic service.
        
        Args:
            db: Database session
            ai_service: Validated AI service with retry logic
            mastery_service: Mastery calculation service
        """
        self.db = db
        self.ai_service = ai_service
        self.mastery_service = mastery_service

    async def select_next_concept(self, session_id: uuid.UUID) -> Concept | None:
        """Select the most informative concept to test.
        
        Uses the information priority formula:
        priority = importance × (1 - confidence) × downstream_impact
        
        Filters out concepts with high mastery and high confidence.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            Concept to test, or None if no suitable concepts found
            
        Requirements: 5.1, 5.9, 5.10
        """
        # Get all concepts for this session
        result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        concepts = result.scalars().all()
        
        if not concepts:
            logger.warning("no_concepts_found", session_id=str(session_id))
            return None
        
        # Get all edges for downstream impact calculation
        result = await self.db.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == session_id)
        )
        edges = result.scalars().all()
        
        # Build NetworkX graph for downstream impact calculation
        G = nx.DiGraph()
        concept_map = {c.id: c for c in concepts}
        
        for concept in concepts:
            G.add_node(concept.id)
        
        for edge in edges:
            G.add_edge(
                edge.source_concept_id,
                edge.target_concept_id,
                weight=float(edge.importance_weight),
            )
        
        # Calculate priority for each concept
        concept_priorities: list[tuple[Concept, float]] = []
        
        for concept in concepts:
            # Filter out high-mastery, high-confidence concepts (Requirement 5.10)
            if (
                concept.mastery_score >= self.HIGH_MASTERY_THRESHOLD
                and concept.confidence_score >= self.HIGH_CONFIDENCE_THRESHOLD
            ):
                logger.debug(
                    "concept_filtered_high_mastery",
                    concept_id=str(concept.id),
                    mastery=float(concept.mastery_score),
                    confidence=float(concept.confidence_score),
                )
                continue
            
            # Calculate importance (average weight of outgoing edges)
            outgoing_edges = [e for e in edges if e.source_concept_id == concept.id]
            if outgoing_edges:
                importance = sum(float(e.importance_weight) for e in outgoing_edges) / len(
                    outgoing_edges
                )
            else:
                # If no outgoing edges, this might be the target concept
                # Give it moderate importance
                importance = 0.5
            
            # Calculate downstream impact (number of reachable concepts weighted by path importance)
            downstream_impact = self._calculate_downstream_impact(G, concept.id, edges)
            
            # Calculate information priority
            # priority = importance × (1 - confidence) × downstream_impact
            uncertainty = 1.0 - float(concept.confidence_score)
            priority = importance * uncertainty * downstream_impact
            
            concept_priorities.append((concept, priority))
            
            logger.debug(
                "concept_priority_calculated",
                concept_id=str(concept.id),
                concept_name=concept.name,
                importance=importance,
                confidence=float(concept.confidence_score),
                uncertainty=uncertainty,
                downstream_impact=downstream_impact,
                priority=priority,
            )
        
        # If no candidates, return None
        if not concept_priorities:
            logger.info("no_testable_concepts", session_id=str(session_id))
            return None
        
        # Select concept with highest priority
        selected_concept, selected_priority = max(
            concept_priorities, key=lambda x: x[1]
        )
        
        logger.info(
            "concept_selected_for_diagnosis",
            session_id=str(session_id),
            concept_id=str(selected_concept.id),
            concept_name=selected_concept.name,
            priority=selected_priority,
        )
        
        return selected_concept

    def _calculate_downstream_impact(
        self,
        graph: nx.DiGraph,
        concept_id: uuid.UUID,
        edges: list[ConceptEdge],
    ) -> float:
        """Calculate downstream impact of a concept.
        
        Downstream impact is the weighted count of concepts that depend on
        this concept (directly or transitively).
        
        Args:
            graph: NetworkX graph of prerequisite relationships
            concept_id: ID of the concept to calculate impact for
            edges: List of all edges in the graph
            
        Returns:
            Downstream impact score (higher = more concepts blocked)
        """
        try:
            # Get all descendants (concepts that transitively depend on this one)
            descendants = nx.descendants(graph, concept_id)
            
            if not descendants:
                # No downstream concepts
                return 0.1  # Small baseline impact
            
            # Calculate weighted impact based on edge importance
            # For each descendant, find the importance of edges leading to it
            impact = 0.0
            for descendant_id in descendants:
                # Find the path importance from concept to descendant
                try:
                    # Get shortest path (in terms of number of edges)
                    paths = list(nx.all_simple_paths(graph, concept_id, descendant_id))
                    if paths:
                        # Use the path with highest cumulative importance
                        max_path_importance = 0.0
                        for path in paths:
                            path_importance = 1.0
                            for i in range(len(path) - 1):
                                # Find edge weight
                                edge = next(
                                    (
                                        e
                                        for e in edges
                                        if e.source_concept_id == path[i]
                                        and e.target_concept_id == path[i + 1]
                                    ),
                                    None,
                                )
                                if edge:
                                    path_importance *= float(edge.importance_weight)
                            max_path_importance = max(max_path_importance, path_importance)
                        
                        impact += max_path_importance
                except nx.NetworkXNoPath:
                    pass
            
            # Normalize by number of descendants to keep impact bounded
            normalized_impact = impact / max(len(descendants), 1)
            
            # Add a bonus for having many descendants
            descendant_bonus = min(len(descendants) / 10.0, 1.0)
            
            final_impact = normalized_impact + descendant_bonus
            
            return final_impact
        
        except Exception as e:
            logger.warning(
                "downstream_impact_calculation_error",
                concept_id=str(concept_id),
                error=str(e),
            )
            # Return baseline impact on error
            return 0.5


    async def generate_question(self, concept_id: uuid.UUID) -> DiagnosticQuestion:
        """Generate a diagnostic question for a concept.
        
        Calls AI to generate a targeted question with grading rubric.
        Stores the question in the database.
        
        Args:
            concept_id: ID of the concept to generate question for
            
        Returns:
            Created DiagnosticQuestion model
            
        Raises:
            ValueError: If concept not found
            AIProviderError: On AI provider failures
            
        Requirements: 5.2, 5.4
        """
        # Get the concept
        result = await self.db.execute(
            select(Concept).where(Concept.id == concept_id)
        )
        concept = result.scalar_one_or_none()
        if not concept:
            raise ValueError(f"Concept {concept_id} not found")
        
        # Generate question using AI
        system_prompt = DIAGNOSTIC_QUESTION_SYSTEM_PROMPT
        user_prompt = get_diagnostic_question_user_prompt(
            concept_name=concept.name,
            concept_description=concept.description,
            current_mastery=float(concept.mastery_score),
            current_confidence=float(concept.confidence_score),
        )
        
        question_output: DiagnosticQuestionOutput = (
            await self.ai_service.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=DiagnosticQuestionOutput,
                purpose="diagnostic_question_generation",
                prompt_version=DIAGNOSTIC_QUESTION_VERSION,
                temperature=0.7,
                session_id=concept.session_id,
            )
        )
        
        # Create and store diagnostic question
        diagnostic_question = DiagnosticQuestion(
            session_id=concept.session_id,
            concept_id=concept_id,
            question_text=question_output.question_text,
            question_type=question_output.question_type,
            rubric_json=question_output.rubric,
            difficulty=Decimal(str(question_output.difficulty)),
        )
        
        self.db.add(diagnostic_question)
        await self.db.commit()
        await self.db.refresh(diagnostic_question)
        
        logger.info(
            "diagnostic_question_generated",
            session_id=str(concept.session_id),
            concept_id=str(concept_id),
            concept_name=concept.name,
            question_id=str(diagnostic_question.id),
            question_type=question_output.question_type,
            difficulty=float(question_output.difficulty),
        )
        
        return diagnostic_question

    async def evaluate_answer(
        self,
        question_id: uuid.UUID,
        answer: str,
    ) -> DiagnosticResult:
        """Evaluate a student's answer to a diagnostic question.
        
        Uses AI to evaluate the answer against the stored rubric,
        creates a diagnostic_attempts record, and updates mastery
        evidence for the concept.
        
        Args:
            question_id: ID of the diagnostic question
            answer: Student's submitted answer
            
        Returns:
            DiagnosticResult with evaluation scores and analysis
            
        Raises:
            ValueError: If question not found
            AIProviderError: On AI provider failures
            
        Requirements: 5.5, 5.6
        """
        # Get the diagnostic question
        result = await self.db.execute(
            select(DiagnosticQuestion).where(DiagnosticQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            raise ValueError(f"Diagnostic question {question_id} not found")
        
        # Get the concept for logging
        concept_result = await self.db.execute(
            select(Concept).where(Concept.id == question.concept_id)
        )
        concept = concept_result.scalar_one()
        
        # Evaluate answer using AI
        system_prompt = DIAGNOSTIC_EVALUATION_SYSTEM_PROMPT
        user_prompt = get_diagnostic_evaluation_user_prompt(
            question_text=question.question_text,
            rubric=question.rubric_json,
            student_answer=answer,
        )
        
        evaluation_output: DiagnosticEvaluationOutput = (
            await self.ai_service.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=DiagnosticEvaluationOutput,
                purpose="diagnostic_answer_evaluation",
                prompt_version=DIAGNOSTIC_EVALUATION_VERSION,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                session_id=question.session_id,
            )
        )
        
        # Create diagnostic attempt record
        diagnostic_attempt = DiagnosticAttempt(
            question_id=question_id,
            session_id=question.session_id,
            concept_id=question.concept_id,
            student_answer=answer,
            correctness_score=Decimal(str(evaluation_output.correctness_score)),
            reasoning_score=Decimal(str(evaluation_output.reasoning_score)),
            misconceptions_json=evaluation_output.misconceptions,
            missing_points_json=evaluation_output.missing_points,
        )
        
        self.db.add(diagnostic_attempt)
        await self.db.flush()
        await self.db.refresh(diagnostic_attempt)
        
        logger.info(
            "diagnostic_answer_evaluated",
            session_id=str(question.session_id),
            question_id=str(question_id),
            concept_id=str(question.concept_id),
            concept_name=concept.name,
            attempt_id=str(diagnostic_attempt.id),
            correctness_score=float(evaluation_output.correctness_score),
            reasoning_score=float(evaluation_output.reasoning_score),
            has_misconceptions=len(evaluation_output.misconceptions) > 0,
        )
        
        # Update mastery evidence
        # Calculate average of correctness and reasoning for diagnostic score
        diagnostic_score = (
            evaluation_output.correctness_score + evaluation_output.reasoning_score
        ) / 2.0
        
        evidence = Evidence(
            source_type="diagnostic",
            reason={
                "attempt_id": str(diagnostic_attempt.id),
                "question_id": str(question_id),
                "correctness_score": evaluation_output.correctness_score,
                "reasoning_score": evaluation_output.reasoning_score,
                "diagnostic_score": diagnostic_score,
                "demonstrated_points": evaluation_output.demonstrated_points,
                "missing_points": evaluation_output.missing_points,
                "misconceptions": evaluation_output.misconceptions,
            },
        )
        
        await self.mastery_service.update_mastery(
            concept_id=question.concept_id,
            evidence=evidence,
        )
        
        await self.db.commit()
        
        logger.info(
            "mastery_updated_from_diagnostic",
            session_id=str(question.session_id),
            concept_id=str(question.concept_id),
            concept_name=concept.name,
            diagnostic_score=diagnostic_score,
        )
        
        # Return result
        return DiagnosticResult(
            attempt_id=diagnostic_attempt.id,
            correctness_score=evaluation_output.correctness_score,
            reasoning_score=evaluation_output.reasoning_score,
            demonstrated_points=evaluation_output.demonstrated_points,
            missing_points=evaluation_output.missing_points,
            misconceptions=evaluation_output.misconceptions,
        )

    async def should_stop_diagnosis(self, session_id: uuid.UUID) -> bool:
        """Determine if diagnostic assessment should stop.
        
        Diagnosis stops when:
        1. Confidence ≥ 0.80 for key concepts, OR
        2. Question count has reached 6, OR
        3. Sufficient evidence has been gathered
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            True if diagnosis should stop, False otherwise
            
        Requirements: 5.7, 5.8
        """
        # Check question count limit (Requirement 5.7)
        question_count_result = await self.db.execute(
            select(func.count(DiagnosticQuestion.id)).where(
                DiagnosticQuestion.session_id == session_id
            )
        )
        question_count = question_count_result.scalar()
        
        if question_count >= self.MAX_QUESTIONS_PER_SESSION:
            logger.info(
                "diagnosis_stopping_max_questions",
                session_id=str(session_id),
                question_count=question_count,
            )
            return True
        
        # Check if key concepts have sufficient confidence (Requirement 5.8)
        # Key concepts are those with importance > 0.5 or on path to target
        
        # Get all concepts for this session
        concepts_result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        concepts = concepts_result.scalars().all()
        
        if not concepts:
            logger.warning("no_concepts_for_diagnosis_check", session_id=str(session_id))
            return False
        
        # Get edges to determine importance
        edges_result = await self.db.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == session_id)
        )
        edges = edges_result.scalars().all()
        
        # Find target concept
        target_concept = next((c for c in concepts if c.is_target), None)
        if not target_concept:
            logger.warning("no_target_concept_found", session_id=str(session_id))
            return False
        
        # Build graph to find concepts on path to target
        G = nx.DiGraph()
        for concept in concepts:
            G.add_node(concept.id)
        
        for edge in edges:
            G.add_edge(edge.source_concept_id, edge.target_concept_id)
        
        # Identify key concepts (those on path to target or with high importance)
        key_concept_ids = set()
        
        for concept in concepts:
            if concept.is_target:
                key_concept_ids.add(concept.id)
                continue
            
            # Check if on path to target
            try:
                if nx.has_path(G, concept.id, target_concept.id):
                    key_concept_ids.add(concept.id)
            except nx.NetworkXError:
                pass
            
            # Check importance based on outgoing edges
            outgoing_edges = [e for e in edges if e.source_concept_id == concept.id]
            if outgoing_edges:
                avg_importance = sum(float(e.importance_weight) for e in outgoing_edges) / len(
                    outgoing_edges
                )
                if avg_importance > 0.5:
                    key_concept_ids.add(concept.id)
        
        if not key_concept_ids:
            logger.info(
                "no_key_concepts_identified",
                session_id=str(session_id),
            )
            return False
        
        # Check if all key concepts have high confidence
        high_confidence_count = 0
        for concept in concepts:
            if concept.id in key_concept_ids:
                if concept.confidence_score >= self.CONFIDENCE_THRESHOLD:
                    high_confidence_count += 1
        
        # Stop if all key concepts have high confidence
        if high_confidence_count == len(key_concept_ids):
            logger.info(
                "diagnosis_stopping_high_confidence",
                session_id=str(session_id),
                key_concepts_count=len(key_concept_ids),
                high_confidence_count=high_confidence_count,
            )
            return True
        
        # Check if sufficient evidence gathered
        # At least 2 questions asked and at least 50% of key concepts have been tested
        if question_count >= 2:
            tested_concept_ids = set()
            questions_result = await self.db.execute(
                select(DiagnosticQuestion.concept_id).where(
                    DiagnosticQuestion.session_id == session_id
                )
            )
            for row in questions_result:
                tested_concept_ids.add(row[0])
            
            tested_key_concepts = tested_concept_ids.intersection(key_concept_ids)
            coverage_ratio = len(tested_key_concepts) / max(len(key_concept_ids), 1)
            
            if coverage_ratio >= 0.5 and high_confidence_count >= len(key_concept_ids) * 0.5:
                logger.info(
                    "diagnosis_stopping_sufficient_evidence",
                    session_id=str(session_id),
                    question_count=question_count,
                    coverage_ratio=coverage_ratio,
                    high_confidence_ratio=high_confidence_count / len(key_concept_ids),
                )
                return True
        
        logger.debug(
            "diagnosis_continuing",
            session_id=str(session_id),
            question_count=question_count,
            key_concepts_count=len(key_concept_ids),
            high_confidence_count=high_confidence_count,
        )
        
        return False
