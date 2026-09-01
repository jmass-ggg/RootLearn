"""Learning path service for RootLearn.

This service provides recommendations for the next concept to learn based on
prerequisite relationships, mastery scores, and path optimization. It uses
topological sorting to ensure prerequisites are learned before dependents.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8
"""
import uuid
from decimal import Decimal

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import get_logger
from app.models import Concept, ConceptEdge, LearningSession

logger = get_logger(__name__)


class LearningPathService:
    """Service for learning path recommendation.
    
    This service uses deterministic algorithms to recommend the next concept
    to learn based on:
    - Topological ordering (prerequisites before dependents)
    - Mastery scores (weak before understood)
    - Path optimization (shortest path to target)
    - Filtering (mastered concepts, unrelated branches)
    """
    
    # Mastery thresholds
    UNDERSTOOD_THRESHOLD = Decimal("0.70")  # Prerequisites must reach this level
    MASTERED_THRESHOLD = Decimal("0.85")  # Don't repeat unless confidence drops
    CONFIDENCE_THRESHOLD = Decimal("0.80")  # Threshold for re-testing mastered concepts

    def __init__(self, db: AsyncSession):
        """Initialize learning path service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def get_next_concept(self, session_id: uuid.UUID) -> Concept | None:
        """Get the next concept to learn in this session.
        
        Selects the next concept based on:
        1. Prerequisites before dependents (topological order)
        2. Weak concepts before understood concepts
        3. Shortest path to target concept
        4. Filter out mastered concepts
        5. Filter out unrelated branches
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            Next Concept to learn, or None if path is complete
            
        Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
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
        
        # Check if path is cleared (all prerequisites understood)
        if await self.is_path_cleared(session_id):
            logger.info(
                "path_cleared_target_recommended",
                session_id=str(session_id),
                target_concept_id=str(session.target_concept_id),
            )
            # Return target concept
            target_result = await self.db.execute(
                select(Concept).where(Concept.id == session.target_concept_id)
            )
            return target_result.scalar_one()
        
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
        
        # Get topological order
        topological_concepts = await self.get_topological_order(session_id)
        
        # Filter candidates:
        # 1. Exclude mastered concepts (unless confidence dropped)
        # 2. Exclude target concept (will be returned when path is cleared)
        # 3. Include only concepts on path to target (relevant branches)
        # 4. Ensure prerequisites are understood
        
        candidate_concepts: list[tuple[Concept, int, float]] = []
        
        for concept in topological_concepts:
            # Skip target concept
            if concept.is_target:
                logger.debug(
                    "candidate_skipped_is_target",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                )
                continue
            
            # Filter out mastered concepts (Requirement 11.6)
            if (
                concept.mastery_score >= self.MASTERED_THRESHOLD
                and concept.confidence_score >= self.CONFIDENCE_THRESHOLD
            ):
                logger.debug(
                    "candidate_skipped_mastered",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                    mastery=float(concept.mastery_score),
                    confidence=float(concept.confidence_score),
                )
                continue
            
            # Check if concept is on path to target (Requirement 11.5)
            try:
                if not nx.has_path(G, concept.id, session.target_concept_id):
                    logger.debug(
                        "candidate_skipped_not_on_path",
                        concept_id=str(concept.id),
                        concept_name=concept.name,
                    )
                    continue
            except nx.NetworkXError:
                logger.debug(
                    "candidate_skipped_path_error",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                )
                continue
            
            # Check if prerequisites are understood (Requirement 11.2)
            prerequisites_met = await self._are_prerequisites_understood(concept.id)
            
            if not prerequisites_met:
                logger.debug(
                    "candidate_skipped_prerequisites_not_met",
                    concept_id=str(concept.id),
                    concept_name=concept.name,
                )
                continue
            
            # Calculate path distance to target for priority
            try:
                path_length = nx.shortest_path_length(
                    G, concept.id, session.target_concept_id
                )
            except (nx.NetworkXNoPath, nx.NetworkXError):
                path_length = 999  # Very high value for unreachable
            
            # Add to candidates with (concept, path_length, mastery)
            candidate_concepts.append(
                (concept, path_length, float(concept.mastery_score))
            )
        
        # If no candidates, return None
        if not candidate_concepts:
            logger.info(
                "no_next_concept_candidates",
                session_id=str(session_id),
            )
            return None
        
        # Sort candidates by:
        # 1. Shortest path to target (Requirement 11.4)
        # 2. Lowest mastery score (Requirement 11.3)
        # 3. Topological order (already ordered by get_topological_order)
        candidate_concepts.sort(key=lambda x: (x[1], x[2]))
        
        next_concept = candidate_concepts[0][0]
        
        logger.info(
            "next_concept_selected",
            session_id=str(session_id),
            concept_id=str(next_concept.id),
            concept_name=next_concept.name,
            mastery=float(next_concept.mastery_score),
            path_length=candidate_concepts[0][1],
        )
        
        return next_concept

    async def get_topological_order(self, session_id: uuid.UUID) -> list[Concept]:
        """Get concepts in topological order (prerequisites before dependents).
        
        Uses NetworkX topological sort to ensure valid learning sequence where
        all prerequisites of a concept are learned before the concept itself.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            List of Concepts in topological order
            
        Requirements: 11.2, 11.8
        """
        # Get all concepts for this session
        concepts_result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        concepts = concepts_result.scalars().all()
        
        if not concepts:
            return []
        
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
        
        # Get topological order
        try:
            ordered_ids = list(nx.topological_sort(G))
        except nx.NetworkXError as e:
            logger.error(
                "topological_sort_failed",
                session_id=str(session_id),
                error=str(e),
            )
            # Fallback: return concepts in any order
            return list(concepts)
        
        # Map IDs back to Concept objects
        ordered_concepts = [concept_map[concept_id] for concept_id in ordered_ids]
        
        logger.debug(
            "topological_order_calculated",
            session_id=str(session_id),
            order=[c.name for c in ordered_concepts],
        )
        
        return ordered_concepts

    async def is_path_cleared(self, session_id: uuid.UUID) -> bool:
        """Check if the path to the target concept is cleared.
        
        A path is cleared when all prerequisites of the target concept
        have mastery >= 0.70.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            True if path is cleared, False otherwise
            
        Requirements: 11.7
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
            return False
        
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
        
        # Get all ancestors (prerequisites) of the target concept
        try:
            prerequisites = nx.ancestors(G, session.target_concept_id)
        except nx.NetworkXError:
            # Target has no prerequisites or error occurred
            prerequisites = set()
        
        # Check if all prerequisites have mastery >= 0.70
        for prereq_id in prerequisites:
            prereq_concept = concept_map[prereq_id]
            
            if prereq_concept.mastery_score < self.UNDERSTOOD_THRESHOLD:
                logger.debug(
                    "path_not_cleared_prerequisite_weak",
                    session_id=str(session_id),
                    prerequisite_id=str(prereq_id),
                    prerequisite_name=prereq_concept.name,
                    mastery=float(prereq_concept.mastery_score),
                )
                return False
        
        logger.info(
            "path_cleared",
            session_id=str(session_id),
            target_concept_id=str(session.target_concept_id),
            prerequisite_count=len(prerequisites),
        )
        
        return True

    async def _are_prerequisites_understood(self, concept_id: uuid.UUID) -> bool:
        """Check if all direct prerequisites of a concept are understood.
        
        A prerequisite is considered understood if mastery >= 0.70.
        
        Args:
            concept_id: ID of the concept to check
            
        Returns:
            True if all prerequisites are understood, False otherwise
        """
        # Get all incoming edges (prerequisites) for this concept
        edges_result = await self.db.execute(
            select(ConceptEdge)
            .where(ConceptEdge.target_concept_id == concept_id)
        )
        prerequisite_edges = edges_result.scalars().all()
        
        # If no prerequisites, return True
        if not prerequisite_edges:
            return True
        
        # Check each prerequisite's mastery
        for edge in prerequisite_edges:
            prereq_result = await self.db.execute(
                select(Concept).where(Concept.id == edge.source_concept_id)
            )
            prerequisite = prereq_result.scalar_one()
            
            if prerequisite.mastery_score < self.UNDERSTOOD_THRESHOLD:
                return False
        
        return True
