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
        px-5 py-4 rounded-2xl border-2 shadow-md bg-white text-center
        transition-all duration-200
        hover:shadow-lg hover:scale-105
        ${isRootGap ? 'border-[#d2e90d] ring-4 ring-[#d2e90d]/20' : concept.is_target ? 'border-[#1463ff] ring-4 ring-[#1463ff]/10' : 'border-[#dfe6ef]'}
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

      {concept.is_target && <div className="mb-2 text-xs font-bold uppercase tracking-wide text-[#1463ff]">Target</div>}
      {isRootGap && <div className="mb-2 text-xs font-bold uppercase tracking-wide text-[#839300]">Root Gap</div>}
      <div className="mb-3 break-words text-base font-semibold text-[#10213d]">
        {concept.name}
      </div>

      {/* Mastery Bar */}
      <div className="space-y-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#e8edf3]">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${masteryPercentage}%`,
              backgroundColor: color,
            }}
          />
        </div>
        <div className="flex items-center justify-between text-xs text-[#718096]">
          <span className="capitalize">{concept.status}</span>
          <span className="font-medium">{masteryPercentage}%</span>
        </div>
      </div>

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
