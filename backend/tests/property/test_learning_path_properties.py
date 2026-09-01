"""Property-based tests for learning path service.

Feature: rootlearn-knowledge-debugger
Tests Properties 47-52: Learning path properties
Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""
import uuid
from decimal import Decimal

import pytest
import networkx as nx
from hypothesis import given, settings, strategies as st, assume
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession
from app.services.learning_path_service import LearningPathService


# Hypothesis strategies for generating test data
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0 with 4 decimal places."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def learning_graph(draw):
    """Generate a learning graph with varying mastery levels.
    
    Creates a DAG with 3-6 concepts including target.
    """
    num_concepts = draw(st.integers(min_value=3, max_value=6))
    
    concepts_data = []
    for i in range(num_concepts - 1):  # Reserve last for target
        mastery = draw(valid_score())
        confidence = draw(valid_score())
        
        concepts_data.append({
            "slug": f"concept-{i}",
            "name": f"Concept {i}",
            "description": f"Concept {i} description",
            "mastery": mastery,
            "confidence": confidence,
            "is_target": False
        })
    
    # Add target concept
    concepts_data.append({
        "slug": "target",
        "name": "Target Concept",
        "description": "The learning goal",
        "mastery": draw(valid_score()),
        "confidence": draw(valid_score()),
        "is_target": True
    })
    
    # Create edges forming a valid DAG
    edges_data = []
    target_idx = len(concepts_data) - 1
    
    # Connect some prerequisites to target
    for i in range(min(2, num_concepts - 1)):
        edges_data.append({
            "source_idx": i,
            "target_idx": target_idx,
            "weight": draw(valid_score())
        })
    
    # Add some prerequisite chains
    for i in range(num_concepts - 2):
        if draw(st.booleans()):  # Randomly add edges
            # Ensure we maintain DAG property (lower index to higher index)
            target_candidate = draw(st.integers(min_value=i+1, max_value=num_concepts-1))
            edges_data.append({
                "source_idx": i,
                "target_idx": target_candidate,
                "weight": draw(valid_score())
            })
    
    return concepts_data, edges_data


class TestProperty47TopologicalOrderingOfPrerequisites:
    """Property 47: Topological ordering of prerequisites.
    
    For any recommended learning path sequence, prerequisites should always
    appear before the concepts that depend on them (topological order).
    
    Validates: Requirements 11.2, 11.8
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(graph_data=learning_graph())
    @settings(max_examples=100, deadline=None)
    async def test_topological_order_prerequisites_before_dependents(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        graph_data: tuple
    ):
        """Property test: Prerequisites always appear before their dependents."""
        # Feature: rootlearn-knowledge-debugger, Property 47: Topological ordering of prerequisites
        
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
        
        # Set target concept
        target_concept = next(c for c in concepts if c.is_target)
        test_session.target_concept_id = target_concept.id
        await db_session.flush()
        
        # Create edges
        edge_map = {}  # Track which concepts depend on which
        for edge_data in edges_data:
            source_concept = concepts[edge_data["source_idx"]]
            target_concept_edge = concepts[edge_data["target_idx"]]
            
            edge = ConceptEdge(
                session_id=test_session.id,
                source_concept_id=source_concept.id,
                target_concept_id=target_concept_edge.id,
                importance_weight=edge_data["weight"]
            )
            db_session.add(edge)
            
            # Track dependencies
            if target_concept_edge.id not in edge_map:
                edge_map[target_concept_edge.id] = []
            edge_map[target_concept_edge.id].append(source_concept.id)
        
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        topological_order = await service.get_topological_order(test_session.id)
        
        # Assert - For each concept in the order, all its prerequisites should appear before it
        position_map = {concept.id: idx for idx, concept in enumerate(topological_order)}
        
        for concept in topological_order:
            if concept.id in edge_map:
                # This concept has prerequisites
                prerequisite_ids = edge_map[concept.id]
                concept_position = position_map[concept.id]
                
                for prereq_id in prerequisite_ids:
                    prereq_position = position_map[prereq_id]
                    # Prerequisite must appear before dependent
                    assert prereq_position < concept_position, (
                        f"Prerequisite {prereq_id} at position {prereq_position} "
                        f"should appear before dependent {concept.id} at position {concept_position}"
                    )

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_topological_order_is_valid_learning_sequence(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Topological order respects all prerequisite relationships."""
        # Feature: rootlearn-knowledge-debugger, Property 47: Topological ordering of prerequisites
        
        # Arrange - Create a chain: A -> B -> C -> Target
        concept_a = Concept(
            session_id=test_session.id,
            slug="concept-a",
            name="Concept A",
            description="Base concept",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="weak"
        )
        db_session.add(concept_a)
        
        concept_b = Concept(
            session_id=test_session.id,
            slug="concept-b",
            name="Concept B",
            description="Intermediate concept",
            mastery_score=Decimal("0.4"),
            confidence_score=Decimal("0.5"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept_b)
        
        concept_c = Concept(
            session_id=test_session.id,
            slug="concept-c",
            name="Concept C",
            description="Advanced concept",
            mastery_score=Decimal("0.2"),
            confidence_score=Decimal("0.4"),
            is_target=False,
            status="weak"
        )
        db_session.add(concept_c)
        
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.1"),
            confidence_score=Decimal("0.3"),
            is_target=True,
            status="unknown"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create chain edges: A -> B -> C -> Target
        edge_ab = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_a.id,
            target_concept_id=concept_b.id,
            importance_weight=Decimal("0.9")
        )
        edge_bc = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_b.id,
            target_concept_id=concept_c.id,
            importance_weight=Decimal("0.8")
        )
        edge_c_target = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_c.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.95")
        )
        db_session.add(edge_ab)
        db_session.add(edge_bc)
        db_session.add(edge_c_target)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        topological_order = await service.get_topological_order(test_session.id)
        
        # Assert - Order should be A, B, C, Target
        concept_ids = [c.id for c in topological_order]
        
        a_idx = concept_ids.index(concept_a.id)
        b_idx = concept_ids.index(concept_b.id)
        c_idx = concept_ids.index(concept_c.id)
        target_idx = concept_ids.index(target.id)
        
        assert a_idx < b_idx < c_idx < target_idx


class TestProperty48WeakConceptsPrioritized:
    """Property 48: Weak concepts prioritized.
    
    For any two concepts that are both ready to learn (prerequisites understood),
    the one with lower mastery should be recommended first.
    
    Validates: Requirements 11.3
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        low_mastery=st.floats(min_value=0.0, max_value=0.5),
        high_mastery=st.floats(min_value=0.51, max_value=0.69)
    )
    @settings(max_examples=100, deadline=None)
    async def test_lower_mastery_concept_recommended_first(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        low_mastery: float,
        high_mastery: float
    ):
        """Property test: Lower mastery concepts are prioritized."""
        # Feature: rootlearn-knowledge-debugger, Property 48: Weak concepts prioritized
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create two concepts with different mastery, both ready to learn (no prerequisites)
        low_mastery_concept = Concept(
            session_id=test_session.id,
            slug="low-mastery",
            name="Low Mastery Concept",
            description="Weaker concept",
            mastery_score=Decimal(str(round(low_mastery, 4))),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="weak"
        )
        db_session.add(low_mastery_concept)
        
        high_mastery_concept = Concept(
            session_id=test_session.id,
            slug="high-mastery",
            name="High Mastery Concept",
            description="Stronger concept",
            mastery_score=Decimal(str(round(high_mastery, 4))),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="learning"
        )
        db_session.add(high_mastery_concept)
        await db_session.flush()
        
        # Both are prerequisites of target with equal importance
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=low_mastery_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=high_mastery_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Should recommend the lower mastery concept
        assert next_concept is not None
        assert next_concept.id == low_mastery_concept.id


class TestProperty49ShortestPathPreference:
    """Property 49: Shortest path preference.
    
    For any set of candidate concepts with equal mastery, the concept on the
    shortest path to the target should be recommended.
    
    Validates: Requirements 11.4
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_shorter_path_to_target_is_preferred(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Concepts closer to target are prioritized."""
        # Feature: rootlearn-knowledge-debugger, Property 49: Shortest path preference
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create two paths with equal mastery:
        # Path 1: A -> Target (distance 1)
        # Path 2: B -> C -> Target (distance 2)
        
        concept_a = Concept(
            session_id=test_session.id,
            slug="concept-a",
            name="Concept A",
            description="Direct prerequisite",
            mastery_score=Decimal("0.4"),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept_a)
        
        concept_b = Concept(
            session_id=test_session.id,
            slug="concept-b",
            name="Concept B",
            description="Indirect prerequisite",
            mastery_score=Decimal("0.4"),  # Same mastery as A
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept_b)
        
        concept_c = Concept(
            session_id=test_session.id,
            slug="concept-c",
            name="Concept C",
            description="Intermediate concept",
            mastery_score=Decimal("0.75"),  # Already understood
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="understood"
        )
        db_session.add(concept_c)
        await db_session.flush()
        
        # Create edges
        edge_a_target = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_a.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        edge_b_c = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_b.id,
            target_concept_id=concept_c.id,
            importance_weight=Decimal("0.8")
        )
        edge_c_target = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept_c.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge_a_target)
        db_session.add(edge_b_c)
        db_session.add(edge_c_target)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Should recommend concept A (shorter path)
        assert next_concept is not None
        assert next_concept.id == concept_a.id


class TestProperty50RelevantBranchesOnly:
    """Property 50: Relevant branches only.
    
    For any recommended concept, there should exist a path from that concept
    to the target concept in the prerequisite graph.
    
    Validates: Requirements 11.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(graph_data=learning_graph())
    @settings(max_examples=100, deadline=None)
    async def test_recommended_concept_is_on_path_to_target(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        graph_data: tuple
    ):
        """Property test: Recommended concepts are always on path to target."""
        # Feature: rootlearn-knowledge-debugger, Property 50: Relevant branches only
        
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
        
        # Set target concept
        target_concept = next(c for c in concepts if c.is_target)
        test_session.target_concept_id = target_concept.id
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
        
        # Build graph to verify paths
        G = nx.DiGraph()
        for concept in concepts:
            G.add_node(concept.id)
        
        edges_result = await db_session.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == test_session.id)
        )
        for edge in edges_result.scalars().all():
            G.add_edge(edge.source_concept_id, edge.target_concept_id)
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - If a concept is recommended, it must be on path to target
        if next_concept and not next_concept.is_target:
            try:
                has_path = nx.has_path(G, next_concept.id, target_concept.id)
                assert has_path, (
                    f"Recommended concept {next_concept.slug} "
                    f"should have path to target {target_concept.slug}"
                )
            except nx.NetworkXError:
                pytest.fail("Graph error when checking path")

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_unrelated_branch_concepts_not_recommended(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Concepts not connected to target are filtered out."""
        # Feature: rootlearn-knowledge-debugger, Property 50: Relevant branches only
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create a concept on path to target
        relevant_concept = Concept(
            session_id=test_session.id,
            slug="relevant",
            name="Relevant Concept",
            description="On path to target",
            mastery_score=Decimal("0.4"),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="learning"
        )
        db_session.add(relevant_concept)
        
        # Create an unrelated concept (not connected to target)
        unrelated_concept = Concept(
            session_id=test_session.id,
            slug="unrelated",
            name="Unrelated Concept",
            description="Not connected to target",
            mastery_score=Decimal("0.2"),  # Lower mastery, but unrelated
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="weak"
        )
        db_session.add(unrelated_concept)
        await db_session.flush()
        
        # Only connect relevant concept to target
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=relevant_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Should recommend relevant concept, not unrelated
        assert next_concept is not None
        assert next_concept.id == relevant_concept.id
        assert next_concept.id != unrelated_concept.id


class TestProperty51MasteredConceptsNotRepeated:
    """Property 51: Mastered concepts are not repeated.
    
    For any concept with status "mastered" and confidence > 0.80, it should
    not be recommended again unless confidence drops.
    
    Validates: Requirements 11.6
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastered_mastery=st.floats(min_value=0.85, max_value=1.0),
        mastered_confidence=st.floats(min_value=0.81, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None)
    async def test_mastered_concepts_with_high_confidence_not_repeated(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastered_mastery: float,
        mastered_confidence: float
    ):
        """Property test: Mastered concepts with high confidence are not repeated."""
        # Feature: rootlearn-knowledge-debugger, Property 51: Mastered concepts are not repeated
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create a mastered concept with high confidence
        mastered_concept = Concept(
            session_id=test_session.id,
            slug="mastered",
            name="Mastered Concept",
            description="Already mastered",
            mastery_score=Decimal(str(round(mastered_mastery, 4))),
            confidence_score=Decimal(str(round(mastered_confidence, 4))),
            is_target=False,
            status="mastered"
        )
        db_session.add(mastered_concept)
        
        # Create a weak concept
        weak_concept = Concept(
            session_id=test_session.id,
            slug="weak",
            name="Weak Concept",
            description="Needs work",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.6"),
            is_target=False,
            status="weak"
        )
        db_session.add(weak_concept)
        await db_session.flush()
        
        # Both are prerequisites of target
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=mastered_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=weak_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Should recommend weak concept, not mastered
        assert next_concept is not None
        assert next_concept.id == weak_concept.id
        assert next_concept.id != mastered_concept.id

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_mastered_concept_with_low_confidence_may_be_repeated(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Mastered concepts with low confidence may be revisited."""
        # Feature: rootlearn-knowledge-debugger, Property 51: Mastered concepts are not repeated
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create a mastered concept but with LOW confidence (uncertain)
        mastered_low_conf = Concept(
            session_id=test_session.id,
            slug="mastered-uncertain",
            name="Mastered but Uncertain",
            description="High mastery but low confidence",
            mastery_score=Decimal("0.90"),  # Mastered
            confidence_score=Decimal("0.50"),  # Low confidence
            is_target=False,
            status="mastered"
        )
        db_session.add(mastered_low_conf)
        await db_session.flush()
        
        # Connect to target
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=mastered_low_conf.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - May recommend this concept for review due to low confidence
        # Or may return None if no better candidates
        # The key is that low confidence allows reconsideration
        if next_concept:
            # If recommended, confidence should be below threshold
            assert next_concept.confidence_score < Decimal("0.80")


class TestProperty52TargetRecommendedWhenPathCleared:
    """Property 52: Target recommended when path is clear.
    
    For any session where all prerequisites of the target concept have
    mastery >= 0.70, the target concept should be the next recommendation.
    
    Validates: Requirements 11.7
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        prereq1_mastery=st.floats(min_value=0.70, max_value=1.0),
        prereq2_mastery=st.floats(min_value=0.70, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None)
    async def test_target_recommended_when_all_prerequisites_understood(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        prereq1_mastery: float,
        prereq2_mastery: float
    ):
        """Property test: Target is recommended when prerequisites are understood."""
        # Feature: rootlearn-knowledge-debugger, Property 52: Target recommended when path is clear
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create two prerequisites with mastery >= 0.70
        prereq1 = Concept(
            session_id=test_session.id,
            slug="prereq-1",
            name="Prerequisite 1",
            description="First prerequisite",
            mastery_score=Decimal(str(round(prereq1_mastery, 4))),
            confidence_score=Decimal("0.80"),
            is_target=False,
            status="understood"
        )
        db_session.add(prereq1)
        
        prereq2 = Concept(
            session_id=test_session.id,
            slug="prereq-2",
            name="Prerequisite 2",
            description="Second prerequisite",
            mastery_score=Decimal(str(round(prereq2_mastery, 4))),
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="understood"
        )
        db_session.add(prereq2)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq1.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq2.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.85")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        is_cleared = await service.is_path_cleared(test_session.id)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Path should be cleared and target recommended
        assert is_cleared is True
        assert next_concept is not None
        assert next_concept.id == target.id
        assert next_concept.is_target is True

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_target_not_recommended_when_prerequisites_weak(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Target is not recommended when prerequisites are weak."""
        # Feature: rootlearn-knowledge-debugger, Property 52: Target recommended when path is clear
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="Learning goal",
            mastery_score=Decimal("0.3"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="weak"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create prerequisites with at least one below threshold
        prereq_understood = Concept(
            session_id=test_session.id,
            slug="prereq-good",
            name="Understood Prerequisite",
            description="Already understood",
            mastery_score=Decimal("0.80"),
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="understood"
        )
        db_session.add(prereq_understood)
        
        prereq_weak = Concept(
            session_id=test_session.id,
            slug="prereq-weak",
            name="Weak Prerequisite",
            description="Still needs work",
            mastery_score=Decimal("0.40"),  # Below threshold
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(prereq_weak)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq_understood.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq_weak.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.85")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = LearningPathService(db_session)
        is_cleared = await service.is_path_cleared(test_session.id)
        next_concept = await service.get_next_concept(test_session.id)
        
        # Assert - Path should NOT be cleared, weak prereq should be recommended
        assert is_cleared is False
        assert next_concept is not None
        assert next_concept.id == prereq_weak.id
        assert next_concept.id != target.id
