'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Concept } from '@/types/graph';

export interface ConceptNodeData extends Record<string, unknown> {
  concept: Concept;
  isRootGap: boolean;
  color: string;
}

/**
 * Custom node component for displaying concepts in the knowledge graph
 */
function ConceptNode({ data }: { data: ConceptNodeData }) {
  const { concept, isRootGap, color } = data;
  const masteryPercentage = Math.round(concept.mastery_score * 100);

  return (
    <div
      className={`
        px-4 py-3 rounded-lg border-2 shadow-md bg-white
        transition-all duration-200
        hover:shadow-lg hover:scale-105
        ${isRootGap ? 'border-red-500 ring-2 ring-red-300' : 'border-gray-300'}
      `}
      style={{
        minWidth: '180px',
        maxWidth: '220px',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3"
        style={{ background: color }}
      />

      {/* Concept Name */}
      <div className="font-semibold text-sm mb-2 text-gray-900 break-words">
        {concept.name}
      </div>

      {/* Mastery Bar */}
      <div className="space-y-1">
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${masteryPercentage}%`,
              backgroundColor: color,
            }}
          />
        </div>
        <div className="text-xs text-gray-600 flex justify-between items-center">
          <span>{concept.status}</span>
          <span className="font-medium">{masteryPercentage}%</span>
        </div>
      </div>

      {/* Root Gap Indicator */}
      {isRootGap && (
        <div className="mt-2 text-xs font-medium text-red-600 text-center">
          Root Gap
        </div>
      )}

      {/* Target Indicator */}
      {concept.is_target && (
        <div className="mt-2 text-xs font-medium text-blue-600 text-center">
          Target
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3"
        style={{ background: color }}
      />
    </div>
  );
}

export default memo(ConceptNode);
