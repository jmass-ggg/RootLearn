"""Root gap detection service for RootLearn.

This service identifies the most impactful knowledge gap (root gap) by
calculating gap scores based on mastery, confidence, path importance, and
downstream impact. It provides explainable reasoning for why a particular
gap was selected.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import Concept, ConceptEdge, LearningSession

logger = get_logger(__name__)


@dataclass
class GapExplanation:
    """Human-readable explanation of why a gap was selected."""
    
    concept_id: uuid.UUID
    concept_name: str
    mastery: float
    confidence: float
    gap_score: float
    reasons: list[str]


@dataclass
class RootGapResult:
    """Result of root gap detection."""
    
    concept: Concept
    gap_score: float
    explanation: GapExplanation


class RootGapService:
    """Service for root gap detection.
    
    This service uses deterministic formulas to identify the most
    impactful knowledge gap that is blocking a learner's understanding.
    """
    
    # Mastery threshold for filtering (Requirement 8.6)
    HIGH_MASTERY_THRESHOLD = Decimal("0.70")

    def __init__(self, db: AsyncSession):
        """Initialize root gap service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def calculate_gap_score(
        self,
        concept_id: uuid.UUID,
        graph: nx.DiGraph,
        target_concept_id: uuid.UUID,
        concept_map: dict[uuid.UUID, Concept],
        edges: list[ConceptEdge],
    ) -> float:
        """Calculate gap score for a concept.
        
        Uses the formula:
        gap_score = (1 - mastery) × confidence × path_importance × downstream_impact
        
        Args:
            concept_id: ID of the concept to calculate gap score for
            graph: NetworkX graph of prerequisite relationships
            target_concept_id: ID of the target concept
            concept_map: Dictionary mapping concept IDs to Concept models
            edges: List of all concept edges in the session
            
        Returns:
            Gap score (higher = more critical gap)
            
        Requirements: 8.1, 8.2, 8.4, 8.7
        """
        concept = concept_map[concept_id]
        
        # Component 1: (1 - mastery) - measures gap size
        mastery_gap = float(Decimal("1.0") - concept.mastery_score)
        
        # Component 2: confidence - measures certainty of assessment
        confidence = float(concept.confidence_score)
        
        # Component 3: path_importance - measures importance to target
        path_importance = self._calculate_path_importance(
            graph, concept_id, target_concept_id, edges
        )
        
        # Component 4: downstream_impact - measures how many concepts are blocked
        downstream_impact = self._calculate_downstream_impact(
            graph, concept_id, edges
        )
        
        # Calculate final gap score
        gap_score = mastery_gap * confidence * path_importance * downstream_impact
        
        logger.debug(
            "gap_score_calculated",
            concept_id=str(concept_id),
            concept_name=concept.name,
            mastery_gap=mastery_gap,
            confidence=confidence,
            path_importance=path_importance,
            downstream_impact=downstream_impact,
            gap_score=gap_score,
        )
        
        return gap_score

    def _calculate_path_importance(
        self,
        graph: nx.DiGraph,
        concept_id: uuid.UUID,
        target_concept_id: uuid.UUID,
        edges: list[ConceptEdge],
    ) -> float:
        """Calculate path importance from concept to target.
        
        Path importance is the cumulative edge weights along the path
        from this concept to the target concept. Higher values indicate
        more direct prerequisite relationships.
        
        Args:
            graph: NetworkX graph of prerequisite relationships
            concept_id: ID of the concept to calculate path importance for
            target_concept_id: ID of the target concept
            edges: List of all concept edges
            
        Returns:
            Path importance score [0, 1]
        """
        # Check if concept is on a path to target
        try:
            if not nx.has_path(graph, concept_id, target_concept_id):
                # Not on path to target, return low importance
                return 0.1
        except nx.NetworkXError:
            return 0.1
        
        # Find all paths from concept to target
        try:
            paths = list(nx.all_simple_paths(graph, concept_id, target_concept_id))
            
            if not paths:
                return 0.1
            
            # Calculate the importance of each path (product of edge weights)
            max_path_importance = 0.0
            
            for path in paths:
                path_importance = 1.0
                
                # Multiply edge weights along the path
                for i in range(len(path) - 1):
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
                
                # Keep track of the highest importance path
                max_path_importance = max(max_path_importance, path_importance)
            
            # Bonus for being a direct prerequisite (path length = 1)
            if len(paths[0]) == 2:  # Direct edge (only 2 nodes in path)
                max_path_importance = min(max_path_importance * 1.5, 1.0)
            
            return max_path_importance
        
        except Exception as e:
            logger.warning(
                "path_importance_calculation_error",
                concept_id=str(concept_id),
                target_concept_id=str(target_concept_id),
                error=str(e),
            )
            return 0.5  # Return moderate importance on error

    def _calculate_downstream_impact(
        self,
        graph: nx.DiGraph,
        concept_id: uuid.UUID,
        edges: list[ConceptEdge],
    ) -> float:
        """Calculate downstream impact of a concept.
        
        Downstream impact measures how many concepts depend on this concept
        (directly or transitively), weighted by edge importance.
        
        Args:
            graph: NetworkX graph of prerequisite relationships
            concept_id: ID of the concept to calculate impact for
            edges: List of all concept edges
            
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
            impact = 0.0
            
            for descendant_id in descendants:
                # Find paths from concept to descendant
                try:
                    paths = list(nx.all_simple_paths(graph, concept_id, descendant_id))
                    
                    if paths:
                        # Use the path with highest cumulative importance
                        max_path_importance = 0.0
                        
                        for path in paths:
                            path_importance = 1.0
                            
                            for i in range(len(path) - 1):
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
            # This captures the "breadth" of impact
            descendant_bonus = min(len(descendants) / 10.0, 1.0)
            
            final_impact = normalized_impact + descendant_bonus
            
            # Ensure impact stays in a reasonable range
            return min(final_impact, 2.0)
        
        except Exception as e:
            logger.warning(
                "downstream_impact_calculation_error",
                concept_id=str(concept_id),
                error=str(e),
            )
            return 0.5  # Return moderate impact on error

    async def detect_root_gap(self, session_id: uuid.UUID) -> RootGapResult | None:
        """Detect the root gap for a learning session.
        
        Identifies the weak prerequisite concept with the highest gap score.
        Filters out concepts with mastery > 0.70.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            RootGapResult with identified gap and explanation, or None if no gap found
            
        Raises:
            ValueError: If session or target concept not found
            
        Requirements: 8.1, 8.3, 8.6
        """
        # Get session and verify it exists
        session_result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not session.target_concept_id:
            raise ValueError(f"Session {session_id} has no target concept")
        
        # Get all concepts for this session
        concepts_result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        concepts = concepts_result.scalars().all()
        
        if not concepts:
            logger.warning("no_concepts_found", session_id=str(session_id))
            return None
        
        # Get all edges
        edges_result = await self.db.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == session_id)
        )
        edges = edges_result.scalars().all()
        
        # Build NetworkX graph
        G = nx.DiGraph()
        concept_map = {c.id: c for c in concepts}
        
        for concept in concepts:
            G.add_node(concept.id)
        
        for edge in edges:
            G.add_edge(edge.source_concept_id, edge.target_concept_id)
        
        # Filter concepts: only consider weak concepts (mastery < 0.70)
        # and exclude target concept from being selected as root gap
        candidate_concepts: list[tuple[Concept, float]] = []
        
        for concept in concepts:
            # Skip target concept
            if concept.is_target:
                logger.debug(
                    "concept_skipped_is_target",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                )
                continue
            
            # Filter out high-mastery concepts (Requirement 8.6)
            if concept.mastery_score >= self.HIGH_MASTERY_THRESHOLD:
                logger.debug(
                    "concept_skipped_high_mastery",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                    mastery=float(concept.mastery_score),
                )
                continue
            
            # Calculate gap score for this concept
            gap_score = await self.calculate_gap_score(
                concept_id=concept.id,
                graph=G,
                target_concept_id=session.target_concept_id,
                concept_map=concept_map,
                edges=edges,
            )
            
            candidate_concepts.append((concept, gap_score))
        
        # If no candidates, return None
        if not candidate_concepts:
            logger.info(
                "no_root_gap_candidates",
                session_id=str(session_id),
            )
            return None
        
        # Select concept with maximum gap score (Requirement 8.3)
        root_gap_concept, max_gap_score = max(
            candidate_concepts, key=lambda x: x[1]
        )
        
        # Generate explanation
        explanation = await self.explain_gap(
            concept_id=root_gap_concept.id,
            gap_score=max_gap_score,
            graph=G,
            target_concept_id=session.target_concept_id,
            concept_map=concept_map,
            edges=edges,
        )
        
        logger.info(
            "root_gap_detected",
            session_id=str(session_id),
            concept_id=str(root_gap_concept.id),
            concept_name=root_gap_concept.name,
            gap_score=max_gap_score,
            mastery=float(root_gap_concept.mastery_score),
            confidence=float(root_gap_concept.confidence_score),
        )
        
        return RootGapResult(
            concept=root_gap_concept,
            gap_score=max_gap_score,
            explanation=explanation,
        )

    async def explain_gap(
        self,
        concept_id: uuid.UUID,
        gap_score: float,
        graph: nx.DiGraph,
        target_concept_id: uuid.UUID,
        concept_map: dict[uuid.UUID, Concept],
        edges: list[ConceptEdge],
    ) -> GapExplanation:
        """Generate human-readable explanation for why a gap was selected.
        
        Provides reasons including:
        - Low mastery performance
        - High confidence in assessment
        - Prerequisite relationship to target
        - Number of blocked concepts
        
        Args:
            concept_id: ID of the root gap concept
            gap_score: Calculated gap score
            graph: NetworkX graph of prerequisite relationships
            target_concept_id: ID of the target concept
            concept_map: Dictionary mapping concept IDs to Concept models
            edges: List of all concept edges
            
        Returns:
            GapExplanation with human-readable reasons
            
        Requirements: 8.5
        """
        concept = concept_map[concept_id]
        target_concept = concept_map[target_concept_id]
        
        reasons: list[str] = []
        
        # Reason 1: Low mastery
        mastery_percent = int(float(concept.mastery_score) * 100)
        reasons.append(f"Low mastery score ({mastery_percent}%)")
        
        # Reason 2: Confidence level
        confidence_percent = int(float(concept.confidence_score) * 100)
        if concept.confidence_score >= Decimal("0.70"):
            reasons.append(f"High confidence in assessment ({confidence_percent}%)")
        elif concept.confidence_score >= Decimal("0.50"):
            reasons.append(f"Moderate confidence in assessment ({confidence_percent}%)")
        else:
            reasons.append(f"Low confidence in assessment ({confidence_percent}%)")
        
        # Reason 3: Relationship to target
        try:
            if nx.has_path(graph, concept_id, target_concept_id):
                # Check if direct prerequisite
                if graph.has_edge(concept_id, target_concept_id):
                    reasons.append(f"Direct prerequisite of {target_concept.name}")
                else:
                    # Count path length
                    try:
                        path = nx.shortest_path(graph, concept_id, target_concept_id)
                        distance = len(path) - 1
                        if distance == 2:
                            reasons.append(f"One step away from {target_concept.name}")
                        else:
                            reasons.append(
                                f"On path to {target_concept.name} ({distance} steps away)"
                            )
                    except nx.NetworkXNoPath:
                        pass
        except nx.NetworkXError:
            pass
        
        # Reason 4: Downstream impact
        try:
            descendants = nx.descendants(graph, concept_id)
            if descendants:
                blocked_count = len(descendants)
                
                if blocked_count == 1:
                    reasons.append("Blocks 1 downstream concept")
                else:
                    reasons.append(f"Blocks {blocked_count} downstream concepts")
        except Exception:
            pass
        
        # Reason 5: Evidence-based assessment
        # Count diagnostic attempts to show evidence basis
        from app.models import DiagnosticAttempt
        
        attempts_result = await self.db.execute(
            select(DiagnosticAttempt).where(DiagnosticAttempt.concept_id == concept_id)
        )
        attempt_count = len(attempts_result.scalars().all())
        
        if attempt_count > 0:
            reasons.append(f"Based on {attempt_count} diagnostic assessment(s)")
        
        explanation = GapExplanation(
            concept_id=concept_id,
            concept_name=concept.name,
            mastery=float(concept.mastery_score),
            confidence=float(concept.confidence_score),
            gap_score=gap_score,
            reasons=reasons,
        )
        
        logger.debug(
            "gap_explanation_generated",
            concept_id=str(concept_id),
            concept_name=concept.name,
            gap_score=gap_score,
            reasons=reasons,
        )
        
        return explanation
