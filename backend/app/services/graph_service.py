"""Graph generation and validation service for RootLearn.

This service handles prerequisite graph generation and validation using NetworkX.
It ensures all graphs are valid DAGs with appropriate size constraints.
"""
import uuid
from dataclasses import dataclass
from decimal import Decimal

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import (
    PREREQUISITE_GRAPH_SYSTEM_PROMPT,
    PREREQUISITE_GRAPH_VERSION,
    get_prerequisite_graph_user_prompt,
)
from app.ai.schemas import PrerequisiteGraphOutput
from app.ai.validated_ai_service import ValidatedAIService
from app.models import Concept, ConceptEdge, LearningSession


@dataclass
class ValidationResult:
    """Result of graph validation."""

    is_valid: bool
    errors: list[str]


class GraphService:
    """Service for prerequisite graph generation and validation."""

    # Constraint constants from requirements
    MAX_NODES = 12  # Requirement 3.2
    MAX_DEPTH = 5  # Requirement 3.3
    MAX_PREDECESSORS = 4  # Requirement 3.4

    def __init__(self, db: AsyncSession, ai_service: ValidatedAIService):
        """Initialize the graph service.
        
        Args:
            db: Database session
            ai_service: Validated AI service with retry logic
        """
        self.db = db
        self.ai_service = ai_service

    def validate_graph_structure(
        self, graph_output: PrerequisiteGraphOutput
    ) -> ValidationResult:
        """Validate prerequisite graph structure using NetworkX.
        
        Checks all structural requirements:
        - Must be a DAG (no cycles)
        - Node count ≤ 12
        - Depth ≤ 5
        - Max predecessors per node ≤ 4
        - Importance weights in [0, 1]
        - Unique node IDs
        - No duplicate edges
        - All edge endpoints exist
        
        Args:
            graph_output: AI-generated graph to validate
            
        Returns:
            ValidationResult with is_valid flag and error messages
        """
        errors: list[str] = []

        # Build NetworkX graph for validation
        G = nx.DiGraph()
        
        # Add nodes
        node_slugs = {node.slug for node in graph_output.nodes}
        for node in graph_output.nodes:
            G.add_node(node.slug)

        # Add edges
        for edge in graph_output.edges:
            G.add_edge(edge.source_slug, edge.target_slug, weight=edge.importance_weight)

        # Requirement 3.5: Must be a DAG (no cycles)
        if not nx.is_directed_acyclic_graph(G):
            try:
                cycle = nx.find_cycle(G)
                cycle_path = " → ".join([str(u) for u, v in cycle] + [str(cycle[0][0])])
                errors.append(f"Graph contains cycle: {cycle_path}")
            except nx.NetworkXNoCycle:
                errors.append("Graph contains cycles")

        # Requirement 3.2: Node count ≤ 12
        if len(graph_output.nodes) > self.MAX_NODES:
            errors.append(
                f"Graph has {len(graph_output.nodes)} nodes, maximum is {self.MAX_NODES}"
            )

        # Requirement 3.3: Depth ≤ 5
        # Calculate depth as longest path in the DAG
        if nx.is_directed_acyclic_graph(G) and G.number_of_nodes() > 0:
            try:
                # Find all nodes with no incoming edges (roots)
                roots = [n for n in G.nodes() if G.in_degree(n) == 0]
                if roots:
                    max_depth = 0
                    for root in roots:
                        # Get longest path from this root
                        descendants = nx.descendants(G, root)
                        descendants.add(root)
                        subgraph = G.subgraph(descendants)
                        if subgraph.number_of_nodes() > 0:
                            depth = nx.dag_longest_path_length(subgraph)
                            max_depth = max(max_depth, depth)
                    
                    if max_depth > self.MAX_DEPTH:
                        errors.append(
                            f"Graph depth is {max_depth}, maximum is {self.MAX_DEPTH}"
                        )
            except Exception as e:
                errors.append(f"Error calculating graph depth: {str(e)}")

        # Requirement 3.4: Max predecessors per node ≤ 4
        for node_slug in G.nodes():
            in_degree = G.in_degree(node_slug)
            if in_degree > self.MAX_PREDECESSORS:
                errors.append(
                    f"Node '{node_slug}' has {in_degree} prerequisites, "
                    f"maximum is {self.MAX_PREDECESSORS}"
                )

        # Requirement 3.7: Importance weights in [0, 1]
        for edge in graph_output.edges:
            if not (0.0 <= edge.importance_weight <= 1.0):
                errors.append(
                    f"Edge {edge.source_slug}→{edge.target_slug} has weight "
                    f"{edge.importance_weight}, must be in [0.0, 1.0]"
                )

        # Requirement 3.8: Unique node IDs (checked by schema, but verify)
        if len(node_slugs) != len(graph_output.nodes):
            errors.append("Duplicate node slugs detected")

        # Requirement 3.9: All edge endpoints exist (checked by schema, but verify)
        for edge in graph_output.edges:
            if edge.source_slug not in node_slugs:
                errors.append(f"Edge references unknown source: {edge.source_slug}")
            if edge.target_slug not in node_slugs:
                errors.append(f"Edge references unknown target: {edge.target_slug}")

        # Requirement 3.10: No duplicate edges (checked by schema, but verify)
        edge_pairs = [(e.source_slug, e.target_slug) for e in graph_output.edges]
        if len(edge_pairs) != len(set(edge_pairs)):
            errors.append("Duplicate edges detected")

        # Additional validation: target concept should be in nodes
        if graph_output.target_slug not in node_slugs:
            errors.append(
                f"Target concept '{graph_output.target_slug}' not found in nodes"
            )

        # Additional validation: all nodes should be reachable from some path to target
        # (no completely disconnected components)
        if nx.is_directed_acyclic_graph(G) and G.number_of_nodes() > 0:
            if graph_output.target_slug in G.nodes():
                # Get all ancestors of target (nodes that lead to target)
                ancestors = nx.ancestors(G, graph_output.target_slug)
                ancestors.add(graph_output.target_slug)
                
                # Check if there are unreachable nodes
                unreachable = node_slugs - ancestors
                if unreachable:
                    errors.append(
                        f"Nodes not connected to target: {', '.join(unreachable)}"
                    )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    async def generate_graph(self, session_id: uuid.UUID) -> PrerequisiteGraphOutput:
        """Generate prerequisite graph for a session's target concept.
        
        This operation is idempotent - if a graph already exists for this session,
        it returns the existing graph instead of generating a new one.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            Validated PrerequisiteGraphOutput
            
        Raises:
            ValueError: If session or target concept not found
            AIProviderError: On AI provider failures
            ValidationError: If generated graph fails validation
        """
        # Check if graph already exists (idempotency)
        result = await self.db.execute(
            select(Concept)
            .where(Concept.session_id == session_id)
            .where(Concept.is_target == False)  # noqa: E712
            .limit(1)
        )
        if result.scalar_one_or_none():
            # Graph already exists, return it
            return await self._load_existing_graph(session_id)

        # Get session and target concept
        result = await self.db.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.target_concept_id:
            raise ValueError(f"Session {session_id} has no target concept")

        result = await self.db.execute(
            select(Concept).where(Concept.id == session.target_concept_id)
        )
        target_concept = result.scalar_one_or_none()
        if not target_concept:
            raise ValueError(f"Target concept {session.target_concept_id} not found")

        # Call AI to generate graph
        system_prompt = PREREQUISITE_GRAPH_SYSTEM_PROMPT
        user_prompt = get_prerequisite_graph_user_prompt(
            target_concept.name, target_concept.description
        )

        graph_output: PrerequisiteGraphOutput = await self.ai_service.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=PrerequisiteGraphOutput,
            purpose="prerequisite_graph_generation",
            prompt_version=PREREQUISITE_GRAPH_VERSION,
            temperature=0.7,
            session_id=session_id,
        )

        # Validate graph structure
        validation = self.validate_graph_structure(graph_output)
        if not validation.is_valid:
            error_msg = "; ".join(validation.errors)
            raise ValueError(f"Generated graph failed validation: {error_msg}")

        # Persist graph to database
        await self._save_graph(session_id, target_concept, graph_output)

        return graph_output

    async def _load_existing_graph(self, session_id: uuid.UUID) -> PrerequisiteGraphOutput:
        """Load existing graph from database.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            PrerequisiteGraphOutput reconstructed from database
        """
        # Get target concept
        result = await self.db.execute(
            select(Concept)
            .where(Concept.session_id == session_id)
            .where(Concept.is_target == True)  # noqa: E712
        )
        target_concept = result.scalar_one_or_none()
        if not target_concept:
            raise ValueError(f"No target concept found for session {session_id}")

        # Get all concepts for this session
        result = await self.db.execute(
            select(Concept).where(Concept.session_id == session_id)
        )
        concepts = result.scalars().all()

        # Get all edges for this session
        result = await self.db.execute(
            select(ConceptEdge).where(ConceptEdge.session_id == session_id)
        )
        edges = result.scalars().all()

        # Build PrerequisiteGraphOutput
        from app.ai.schemas import PrerequisiteNode, PrerequisiteEdge

        nodes = [
            PrerequisiteNode(
                slug=concept.slug,
                name=concept.name,
                description=concept.description,
            )
            for concept in concepts
        ]

        prerequisite_edges = [
            PrerequisiteEdge(
                source_slug=next(
                    c.slug for c in concepts if c.id == edge.source_concept_id
                ),
                target_slug=next(
                    c.slug for c in concepts if c.id == edge.target_concept_id
                ),
                importance_weight=float(edge.importance_weight),
            )
            for edge in edges
        ]

        return PrerequisiteGraphOutput(
            target_slug=target_concept.slug,
            nodes=nodes,
            edges=prerequisite_edges,
        )

    async def _save_graph(
        self,
        session_id: uuid.UUID,
        target_concept: Concept,
        graph_output: PrerequisiteGraphOutput,
    ) -> None:
        """Save validated graph to database.
        
        Args:
            session_id: ID of the learning session
            target_concept: The target concept for this session
            graph_output: Validated graph to save
        """
        # Create a mapping of slug -> concept for edges
        slug_to_concept: dict[str, Concept] = {}

        # Update target concept if it's in the graph with a different description
        target_node = next(
            (n for n in graph_output.nodes if n.slug == graph_output.target_slug), None
        )
        if target_node and target_node.description != target_concept.description:
            target_concept.description = target_node.description
            
        slug_to_concept[target_concept.slug] = target_concept

        # Create prerequisite concepts (excluding target)
        for node in graph_output.nodes:
            if node.slug == target_concept.slug:
                continue  # Skip target, already exists

            concept = Concept(
                session_id=session_id,
                slug=node.slug,
                name=node.name,
                description=node.description,
                is_target=False,
                mastery_score=Decimal("0.0"),
                confidence_score=Decimal("0.1"),
                status="unknown",
            )
            self.db.add(concept)
            slug_to_concept[node.slug] = concept

        # Flush to get IDs for concepts
        await self.db.flush()

        # Create edges
        for edge in graph_output.edges:
            source_concept = slug_to_concept[edge.source_slug]
            target_concept_edge = slug_to_concept[edge.target_slug]

            concept_edge = ConceptEdge(
                session_id=session_id,
                source_concept_id=source_concept.id,
                target_concept_id=target_concept_edge.id,
                importance_weight=Decimal(str(edge.importance_weight)),
            )
            self.db.add(concept_edge)

        await self.db.commit()

    async def get_graph(self, session_id: uuid.UUID) -> PrerequisiteGraphOutput | None:
        """Get the prerequisite graph for a session.
        
        Args:
            session_id: ID of the learning session
            
        Returns:
            PrerequisiteGraphOutput or None if no graph exists
        """
        # Check if any prerequisite concepts exist
        result = await self.db.execute(
            select(Concept)
            .where(Concept.session_id == session_id)
            .where(Concept.is_target == False)  # noqa: E712
            .limit(1)
        )
        if not result.scalar_one_or_none():
            return None

        return await self._load_existing_graph(session_id)
