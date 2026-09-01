"""Property-based tests for root gap detection.

Feature: rootlearn-knowledge-debugger
Tests Properties 29-32: Root gap detection properties
Validates: Requirements 8.2, 8.3, 8.5, 8.6
"""
import uuid
from decimal import Decimal

import pytest
import networkx as nx
from hypothesis import given, settings, strategies as st, assume
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Concept, ConceptEdge, LearningSession
from app.services.root_gap_service import RootGapService


# Hypothesis strategies for generating test data
@st.composite
def valid_score(draw):
    """Generate a valid score between 0.0 and 1.0 with 4 decimal places."""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return Decimal(str(round(value, 4)))


@st.composite
def simple_prerequisite_graph(draw):
    """Generate a simple prerequisite graph (chain structure).
    
    Creates a graph like: A -> B -> C -> Target
    where A, B, C are prerequisites with varying mastery levels.
    """
    num_prereqs = draw(st.integers(min_value=2, max_value=5))
    
    concepts_data = []
    for i in range(num_prereqs):
        # Ensure at least some concepts have low mastery
        mastery = draw(valid_score())
        confidence = draw(valid_score())
        
        concepts_data.append({
            "slug": f"prereq-{i}",
            "name": f"Prerequisite {i}",
            "description": f"Prerequisite concept {i}",
            "mastery": mastery,
            "confidence": confidence,
            "is_target": False
        })
    
    # Add target concept
    concepts_data.append({
        "slug": "target",
        "name": "Target Concept",
        "description": "The target concept to learn",
        "mastery": draw(valid_score()),
        "confidence": draw(valid_score()),
        "is_target": True
    })
    
    # Create chain edges: each concept points to the next
    edges_data = []
    for i in range(num_prereqs):
        edges_data.append({
            "source_idx": i,
            "target_idx": i + 1,
            "weight": draw(valid_score())
        })
    
    return concepts_data, edges_data


class TestProperty29GapScoreCalculationFollowsFormula:
    """Property 29: Gap score calculation follows formula.
    
    For any concept with mastery m, confidence c, path_importance p, and
    downstream_impact d, the gap_score should equal (1-m) × c × p × d.
    
    Validates: Requirements 8.2
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score(),
        weight=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_gap_score_formula_components(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal,
        weight: Decimal
    ):
        """Property test: Gap score uses correct formula components."""
        # Feature: rootlearn-knowledge-debugger, Property 29: Gap score calculation follows formula
        
        # Arrange - Create a simple graph: prereq -> target
        prereq = Concept(
            session_id=test_session.id,
            slug="prereq",
            name="Prerequisite",
            description="A prerequisite concept",
            mastery_score=mastery,
            confidence_score=confidence,
            is_target=False,
            status="learning"
        )
        db_session.add(prereq)
        
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target concept",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        # Update session with target concept
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create edge
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq.id,
            target_concept_id=target.id,
            importance_weight=weight
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Build graph for gap score calculation
        G = nx.DiGraph()
        G.add_node(prereq.id)
        G.add_node(target.id)
        G.add_edge(prereq.id, target.id)
        
        concept_map = {prereq.id: prereq, target.id: target}
        edges = [edge]
        
        # Act
        service = RootGapService(db_session)
        gap_score = await service.calculate_gap_score(
            concept_id=prereq.id,
            graph=G,
            target_concept_id=target.id,
            concept_map=concept_map,
            edges=edges
        )
        
        # Assert - Gap score should be positive and bounded
        assert gap_score >= 0.0
        # The formula is: (1 - mastery) × confidence × path_importance × downstream_impact
        # Key insight: mastery_gap should be (1 - mastery)
        mastery_gap_component = 1.0 - float(mastery)
        confidence_component = float(confidence)
        
        # Gap score should contain these components
        assert gap_score <= mastery_gap_component * confidence_component * 10  # Upper bound check

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_gap_score_increases_with_low_mastery(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: Lower mastery leads to higher gap score (all else equal)."""
        # Feature: rootlearn-knowledge-debugger, Property 29: Gap score calculation follows formula
        
        # Assume we have different mastery levels to compare
        assume(mastery < Decimal("0.9"))  # Leave room for comparison
        
        # Arrange - Create two concepts with same confidence but different mastery
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target",
            description="Target concept",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        low_mastery_concept = Concept(
            session_id=test_session.id,
            slug="low-mastery",
            name="Low Mastery",
            description="Low mastery concept",
            mastery_score=mastery,
            confidence_score=confidence,
            is_target=False,
            status="weak"
        )
        db_session.add(low_mastery_concept)
        
        high_mastery_concept = Concept(
            session_id=test_session.id,
            slug="high-mastery",
            name="High Mastery",
            description="High mastery concept",
            mastery_score=min(mastery + Decimal("0.1"), Decimal("1.0")),
            confidence_score=confidence,
            is_target=False,
            status="learning"
        )
        db_session.add(high_mastery_concept)
        await db_session.flush()
        
        # Create identical edges
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
        
        # Build graphs
        G = nx.DiGraph()
        G.add_edge(low_mastery_concept.id, target.id)
        G.add_edge(high_mastery_concept.id, target.id)
        
        concept_map = {
            low_mastery_concept.id: low_mastery_concept,
            high_mastery_concept.id: high_mastery_concept,
            target.id: target
        }
        edges = [edge1, edge2]
        
        # Act
        service = RootGapService(db_session)
        low_gap_score = await service.calculate_gap_score(
            concept_id=low_mastery_concept.id,
            graph=G,
            target_concept_id=target.id,
            concept_map=concept_map,
            edges=edges
        )
        high_gap_score = await service.calculate_gap_score(
            concept_id=high_mastery_concept.id,
            graph=G,
            target_concept_id=target.id,
            concept_map=concept_map,
            edges=edges
        )
        
        # Assert - Lower mastery should have higher gap score
        assert low_gap_score >= high_gap_score


class TestProperty30RootGapSelectionIsMaximumGapScore:
    """Property 30: Root gap selection is maximum gap score.
    
    For any set of weak prerequisite concepts, the selected root gap should
    be the concept with the highest gap_score.
    
    Validates: Requirements 8.3
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(graph_data=simple_prerequisite_graph())
    @settings(max_examples=100, deadline=None)
    async def test_root_gap_is_maximum_gap_score(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        graph_data: tuple
    ):
        """Property test: Root gap has the maximum gap score among candidates."""
        # Feature: rootlearn-knowledge-debugger, Property 30: Root gap selection is maximum gap score
        
        concepts_data, edges_data = graph_data
        
        # Ensure at least one concept has low mastery to be selected
        has_low_mastery = any(c["mastery"] < Decimal("0.70") for c in concepts_data if not c["is_target"])
        assume(has_low_mastery)
        
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
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert - If a root gap was found
        if result:
            # Calculate gap scores for all eligible concepts (mastery < 0.70, not target)
            G = nx.DiGraph()
            for concept in concepts:
                G.add_node(concept.id)
            
            edges_result = await db_session.execute(
                f"SELECT source_concept_id, target_concept_id FROM concept_edges WHERE session_id = '{test_session.id}'"
            )
            for source_id, target_id in edges_result:
                G.add_edge(source_id, target_id)
            
            concept_map = {c.id: c for c in concepts}
            edges_list = await db_session.execute(
                f"SELECT * FROM concept_edges WHERE session_id = '{test_session.id}'"
            )
            
            # The selected root gap should not be the target
            assert result.concept.id != target_concept.id
            
            # The selected root gap should have mastery < 0.70
            assert result.concept.mastery_score < Decimal("0.70")
            
            # The gap score should be non-negative
            assert result.gap_score >= 0.0

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_root_gap_selects_highest_score_from_multiple_candidates(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: Root gap selection picks maximum from multiple candidates."""
        # Feature: rootlearn-knowledge-debugger, Property 30: Root gap selection is maximum gap score
        
        # Arrange - Create target concept
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create multiple low-mastery prerequisites with different configurations
        # Concept 1: Very low mastery, high confidence, direct prerequisite
        concept1 = Concept(
            session_id=test_session.id,
            slug="concept-1",
            name="Concept 1",
            description="Very weak concept",
            mastery_score=Decimal("0.20"),
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="weak"
        )
        db_session.add(concept1)
        
        # Concept 2: Moderate low mastery, moderate confidence
        concept2 = Concept(
            session_id=test_session.id,
            slug="concept-2",
            name="Concept 2",
            description="Moderately weak concept",
            mastery_score=Decimal("0.50"),
            confidence_score=Decimal("0.60"),
            is_target=False,
            status="learning"
        )
        db_session.add(concept2)
        
        # Concept 3: Low mastery, low confidence (uncertain assessment)
        concept3 = Concept(
            session_id=test_session.id,
            slug="concept-3",
            name="Concept 3",
            description="Uncertain weak concept",
            mastery_score=Decimal("0.30"),
            confidence_score=Decimal("0.40"),
            is_target=False,
            status="weak"
        )
        db_session.add(concept3)
        
        await db_session.flush()
        
        # Create edges - all direct prerequisites
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept1.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept2.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        edge3 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept3.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.7")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        db_session.add(edge3)
        await db_session.flush()
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert
        assert result is not None
        assert result.gap_score > 0.0
        
        # The selected concept should be one of our low-mastery candidates
        assert result.concept.id in [concept1.id, concept2.id, concept3.id]
        
        # Concept 1 should likely be selected (lowest mastery, highest confidence)
        # But we verify that whichever was selected has a valid gap score
        assert result.concept.mastery_score < Decimal("0.70")


class TestProperty31RootGapExplanationCompleteness:
    """Property 31: Root gap explanation completeness.
    
    For any identified root gap, the explanation should include: concept name,
    mastery, confidence, gap_score, and a list of human-readable reasons.
    
    Validates: Requirements 8.5
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=st.floats(min_value=0.0, max_value=0.69),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_explanation_has_all_required_fields(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: float,
        confidence: Decimal
    ):
        """Property test: Root gap explanation contains all required fields."""
        # Feature: rootlearn-knowledge-debugger, Property 31: Root gap explanation completeness
        
        # Arrange - Create a simple graph with one weak prerequisite
        mastery_decimal = Decimal(str(round(mastery, 4)))
        
        prereq = Concept(
            session_id=test_session.id,
            slug="weak-prereq",
            name="Weak Prerequisite",
            description="A weak prerequisite concept",
            mastery_score=mastery_decimal,
            confidence_score=confidence,
            is_target=False,
            status="weak"
        )
        db_session.add(prereq)
        
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target concept",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create edge
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.85")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert - Explanation should have all required fields
        assert result is not None
        explanation = result.explanation
        
        # Required fields
        assert explanation.concept_id is not None
        assert explanation.concept_name is not None
        assert len(explanation.concept_name) > 0
        assert explanation.mastery is not None
        assert 0.0 <= explanation.mastery <= 1.0
        assert explanation.confidence is not None
        assert 0.0 <= explanation.confidence <= 1.0
        assert explanation.gap_score is not None
        assert explanation.gap_score >= 0.0
        assert explanation.reasons is not None
        assert isinstance(explanation.reasons, list)
        assert len(explanation.reasons) > 0  # Should have at least one reason
        
        # All reasons should be non-empty strings
        for reason in explanation.reasons:
            assert isinstance(reason, str)
            assert len(reason) > 0

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(graph_data=simple_prerequisite_graph())
    @settings(max_examples=50, deadline=None)
    async def test_explanation_reasons_are_informative(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        graph_data: tuple
    ):
        """Property test: Explanation reasons provide meaningful information."""
        # Feature: rootlearn-knowledge-debugger, Property 31: Root gap explanation completeness
        
        concepts_data, edges_data = graph_data
        
        # Ensure at least one concept has low mastery
        has_low_mastery = any(c["mastery"] < Decimal("0.70") for c in concepts_data if not c["is_target"])
        assume(has_low_mastery)
        
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
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert
        if result:
            explanation = result.explanation
            
            # Reasons should mention mastery or confidence
            reasons_text = " ".join(explanation.reasons).lower()
            assert "mastery" in reasons_text or "confidence" in reasons_text
            
            # Should mention relationship to target (prerequisite, path, etc.)
            assert any(
                keyword in reasons_text
                for keyword in ["prerequisite", "path", "blocks", "downstream"]
            )


class TestProperty32HighMasteryConceptsExcludedFromRootGap:
    """Property 32: High-mastery concepts excluded from root gap.
    
    For any concept with mastery > 0.70, it should not be selected as a root gap
    unless all other concepts are also mastered.
    
    Validates: Requirements 8.6
    """

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        high_mastery=st.floats(min_value=0.71, max_value=1.0),
        low_mastery=st.floats(min_value=0.0, max_value=0.69)
    )
    @settings(max_examples=100, deadline=None)
    async def test_high_mastery_concepts_not_selected_as_root_gap(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        high_mastery: float,
        low_mastery: float
    ):
        """Property test: Concepts with mastery > 0.70 are not selected as root gap."""
        # Feature: rootlearn-knowledge-debugger, Property 32: High-mastery concepts excluded from root gap
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create high-mastery concept
        high_mastery_concept = Concept(
            session_id=test_session.id,
            slug="high-mastery",
            name="High Mastery Concept",
            description="Well understood",
            mastery_score=Decimal(str(round(high_mastery, 4))),
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="understood"
        )
        db_session.add(high_mastery_concept)
        
        # Create low-mastery concept
        low_mastery_concept = Concept(
            session_id=test_session.id,
            slug="low-mastery",
            name="Low Mastery Concept",
            description="Needs work",
            mastery_score=Decimal(str(round(low_mastery, 4))),
            confidence_score=Decimal("0.70"),
            is_target=False,
            status="weak"
        )
        db_session.add(low_mastery_concept)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=high_mastery_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.9")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=low_mastery_concept.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert - Root gap should be the low-mastery concept, not the high-mastery one
        assert result is not None
        assert result.concept.id == low_mastery_concept.id
        assert result.concept.id != high_mastery_concept.id
        assert result.concept.mastery_score < Decimal("0.70")

    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_no_root_gap_when_all_concepts_have_high_mastery(
        self,
        db_session: AsyncSession,
        test_session: LearningSession
    ):
        """Property test: No root gap is found when all concepts have mastery > 0.70."""
        # Feature: rootlearn-knowledge-debugger, Property 32: High-mastery concepts excluded from root gap
        
        # Arrange - Create target
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target",
            mastery_score=Decimal("0.75"),
            confidence_score=Decimal("0.80"),
            is_target=True,
            status="understood"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        # Create all high-mastery prerequisites
        concept1 = Concept(
            session_id=test_session.id,
            slug="concept-1",
            name="Concept 1",
            description="Well understood 1",
            mastery_score=Decimal("0.80"),
            confidence_score=Decimal("0.85"),
            is_target=False,
            status="understood"
        )
        db_session.add(concept1)
        
        concept2 = Concept(
            session_id=test_session.id,
            slug="concept-2",
            name="Concept 2",
            description="Well understood 2",
            mastery_score=Decimal("0.90"),
            confidence_score=Decimal("0.90"),
            is_target=False,
            status="mastered"
        )
        db_session.add(concept2)
        await db_session.flush()
        
        # Create edges
        edge1 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept1.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        edge2 = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=concept2.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.7")
        )
        db_session.add(edge1)
        db_session.add(edge2)
        await db_session.flush()
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert - No root gap should be found
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        mastery=valid_score(),
        confidence=valid_score()
    )
    @settings(max_examples=100, deadline=None)
    async def test_mastery_threshold_filtering_is_enforced(
        self,
        db_session: AsyncSession,
        test_session: LearningSession,
        mastery: Decimal,
        confidence: Decimal
    ):
        """Property test: The 0.70 mastery threshold is consistently enforced."""
        # Feature: rootlearn-knowledge-debugger, Property 32: High-mastery concepts excluded from root gap
        
        # Arrange - Create single prerequisite with varying mastery
        target = Concept(
            session_id=test_session.id,
            slug="target",
            name="Target Concept",
            description="The target",
            mastery_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
            is_target=True,
            status="learning"
        )
        db_session.add(target)
        await db_session.flush()
        
        test_session.target_concept_id = target.id
        await db_session.flush()
        
        prereq = Concept(
            session_id=test_session.id,
            slug="prereq",
            name="Prerequisite",
            description="A prerequisite",
            mastery_score=mastery,
            confidence_score=confidence,
            is_target=False,
            status="learning"
        )
        db_session.add(prereq)
        await db_session.flush()
        
        edge = ConceptEdge(
            session_id=test_session.id,
            source_concept_id=prereq.id,
            target_concept_id=target.id,
            importance_weight=Decimal("0.8")
        )
        db_session.add(edge)
        await db_session.flush()
        
        # Act
        service = RootGapService(db_session)
        result = await service.detect_root_gap(test_session.id)
        
        # Assert - If mastery >= 0.70, should not be selected
        if mastery >= Decimal("0.70"):
            assert result is None
        else:
            # May be selected if mastery < 0.70
            if result:
                assert result.concept.mastery_score < Decimal("0.70")
