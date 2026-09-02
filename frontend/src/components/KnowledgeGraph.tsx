'use client';

import { useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  NodeTypes,
  MarkerType,
  OnNodesChange,
  OnEdgesChange,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { PrerequisiteGraph, Concept, MasteryStatus } from '@/types/graph';
import ConceptNode, { ConceptNodeData } from './ConceptNode';
import { StateDisplay } from './ui/StateDisplay';
import { colors } from '@/theme/tokens';

interface KnowledgeGraphProps {
  graph: PrerequisiteGraph | undefined;
  onNodeClick?: (concept: Concept) => void;
}

export interface GraphControlsRef {
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
}

interface KnowledgeGraphInternalProps {
  graph: PrerequisiteGraph;
  onNodeClick?: (concept: Concept) => void;
}

/**
 * Get color based on mastery status using design tokens
 */
function getNodeColor(status: MasteryStatus): string {
  switch (status) {
    case 'weak':
      return colors.mastery.weak;
    case 'learning':
      return colors.mastery.learning;
    case 'understood':
      return colors.mastery.understood;
    case 'mastered':
      return colors.mastery.mastered;
    case 'locked':
      return colors.mastery.locked;
    case 'unknown':
    default:
      return colors.mastery.unknown;
  }
}

/**
 * Calculate hierarchical layout for DAG
 */
function calculateHierarchicalLayout(
  concepts: Concept[],
  edges: PrerequisiteGraph['edges']
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  
  // Build adjacency list for incoming edges (prerequisites)
  const incomingEdges = new Map<string, string[]>();
  const outgoingEdges = new Map<string, string[]>();
  
  concepts.forEach(c => {
    incomingEdges.set(c.id, []);
    outgoingEdges.set(c.id, []);
  });
  
  edges.forEach(edge => {
    incomingEdges.get(edge.target_concept_id)?.push(edge.source_concept_id);
    outgoingEdges.get(edge.source_concept_id)?.push(edge.target_concept_id);
  });
  
  // Calculate levels using topological sort
  const levels = new Map<string, number>();
  const visited = new Set<string>();
  
  function calculateLevel(conceptId: string): number {
    if (levels.has(conceptId)) {
      return levels.get(conceptId)!;
    }
    
    if (visited.has(conceptId)) {
      return 0; // Cycle detection fallback
    }
    
    visited.add(conceptId);
    
    const prerequisites = incomingEdges.get(conceptId) || [];
    if (prerequisites.length === 0) {
      levels.set(conceptId, 0);
      return 0;
    }
    
    const maxPrereqLevel = Math.max(
      ...prerequisites.map(preReqId => calculateLevel(preReqId))
    );
    
    const level = maxPrereqLevel + 1;
    levels.set(conceptId, level);
    return level;
  }
  
  // Calculate levels for all concepts
  concepts.forEach(concept => calculateLevel(concept.id));
  
  // Group concepts by level
  const levelGroups = new Map<number, string[]>();
  concepts.forEach(concept => {
    const level = levels.get(concept.id) || 0;
    if (!levelGroups.has(level)) {
      levelGroups.set(level, []);
    }
    levelGroups.get(level)!.push(concept.id);
  });
  
  // Assign positions
  const horizontalSpacing = 280;
  const verticalSpacing = 180;
  
  levelGroups.forEach((conceptIds, level) => {
    const groupWidth = (conceptIds.length - 1) * horizontalSpacing;
    const startX = -groupWidth / 2;
    
    conceptIds.forEach((conceptId, index) => {
      positions.set(conceptId, {
        x: startX + index * horizontalSpacing,
        y: level * verticalSpacing,
      });
    });
  });
  
  return positions;
}

/**
 * Convert concepts to React Flow nodes
 */
function conceptsToNodes(
  concepts: Concept[],
  edges: PrerequisiteGraph['edges'],
  rootGapId?: string | null
): Node<ConceptNodeData>[] {
  const positions = calculateHierarchicalLayout(concepts, edges);
  
  return concepts.map((concept) => ({
    id: concept.id,
    type: 'conceptNode',
    position: positions.get(concept.id) || { x: 0, y: 0 },
    data: {
      concept,
      isRootGap: rootGapId === concept.id,
      color: getNodeColor(concept.status),
    },
  }));
}

/**
 * Convert edges to React Flow edges
 */
function edgesToFlowEdges(edges: PrerequisiteGraph['edges']): Edge[] {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source_concept_id,
    target: edge.target_concept_id,
    type: 'smoothstep',
    animated: false,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 20,
      height: 20,
    },
    label: edge.importance_weight < 1 ? `${Math.round(edge.importance_weight * 100)}%` : undefined,
    style: {
      stroke: '#94a3b8',
      strokeWidth: 2,
    },
  }));
}

/**
 * KnowledgeGraph component (internal)
 * Renders a prerequisite graph using React Flow
 */
const KnowledgeGraphInternal = forwardRef<GraphControlsRef, KnowledgeGraphInternalProps>(
  ({ graph, onNodeClick }, ref) => {
    const reactFlowInstance = useReactFlow();

    const initialNodes = useMemo(
      () => conceptsToNodes(graph.concepts, graph.edges, graph.root_gap_id),
      [graph.concepts, graph.edges, graph.root_gap_id]
    );

    const initialEdges = useMemo(
      () => edgesToFlowEdges(graph.edges),
      [graph.edges]
    );

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    const nodeTypes = useMemo<NodeTypes>(() => ({
      conceptNode: ConceptNode,
    }), []);

    const handleNodeClick = useCallback(
      (_event: React.MouseEvent, node: Node) => {
        const nodeData = node.data as ConceptNodeData;
        if (onNodeClick && nodeData?.concept) {
          onNodeClick(nodeData.concept);
        }
      },
      [onNodeClick]
    );

    // Expose control methods via ref
    useImperativeHandle(ref, () => ({
      fitView: () => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
      },
      zoomIn: () => {
        reactFlowInstance.zoomIn({ duration: 300 });
      },
      zoomOut: () => {
        reactFlowInstance.zoomOut({ duration: 300 });
      },
    }), [reactFlowInstance]);

    return (
      <div className="w-full h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={2}
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as ConceptNodeData;
              return data?.color || '#6b7280';
            }}
            nodeStrokeWidth={3}
            zoomable
            pannable
          />
        </ReactFlow>
      </div>
    );
  }
);

KnowledgeGraphInternal.displayName = 'KnowledgeGraphInternal';

/**
 * KnowledgeGraph component with ReactFlowProvider wrapper
 */
const KnowledgeGraph = forwardRef<GraphControlsRef, KnowledgeGraphProps>(
  (props, ref) => {
    const { graph } = props;

    // Defensive rendering: check for undefined before accessing properties
    if (graph === undefined) {
      return (
        <StateDisplay
          variant="loading"
          title="Loading knowledge map..."
          description="Building your prerequisite graph"
        />
      );
    }

    // Check if concepts or edges are undefined
    if (graph.concepts === undefined || graph.edges === undefined) {
      return (
        <StateDisplay
          variant="loading"
          title="Loading knowledge map..."
          description="Building your prerequisite graph"
        />
      );
    }

    // Check if concepts array is empty
    if (graph.concepts.length === 0) {
      return (
        <StateDisplay
          variant="empty"
          title="No concepts to display"
          description="The knowledge map is empty. This might indicate an issue with graph generation."
        />
      );
    }

    // Safe to render - all data is present
    return (
      <ReactFlowProvider>
        <KnowledgeGraphInternal {...props} graph={graph} ref={ref} />
      </ReactFlowProvider>
    );
  }
);

KnowledgeGraph.displayName = 'KnowledgeGraph';

export default KnowledgeGraph;
