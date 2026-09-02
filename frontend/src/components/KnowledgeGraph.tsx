'use client';

import { useCallback, useMemo } from 'react';
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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { PrerequisiteGraph, Concept, MasteryStatus } from '@/types/graph';
import ConceptNode, { ConceptNodeData } from './ConceptNode';

interface KnowledgeGraphProps {
  graph: PrerequisiteGraph;
  onNodeClick?: (concept: Concept) => void;
}

/**
 * Get color based on mastery status
 */
function getNodeColor(status: MasteryStatus): string {
  switch (status) {
    case 'weak':
      return '#ef4444'; // red
    case 'learning':
      return '#eab308'; // yellow
    case 'understood':
      return '#84cc16'; // light green
    case 'mastered':
      return '#22c55e'; // dark green
    case 'locked':
      return '#9ca3af'; // gray
    default:
      return '#6b7280'; // gray
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
 * KnowledgeGraph component
 * Renders a prerequisite graph using React Flow
 */
export default function KnowledgeGraph({
  graph,
  onNodeClick,
}: KnowledgeGraphProps) {
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
