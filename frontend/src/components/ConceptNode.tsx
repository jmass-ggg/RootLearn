'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Concept } from '@/types/graph';
import { colors } from '@/theme/tokens';

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
  const isTarget = concept.is_target;
  const isLocked = concept.status === 'locked';

  // Determine border and background styling
  let borderClass = 'border-gray-300';
  let bgClass = 'bg-white';
  let ringClass = '';
  
  if (isRootGap) {
    // Lime highlight for root gap with readable labels
    bgClass = 'bg-[#D2E90D]';
    borderClass = 'border-[#D2E90D]';
    ringClass = 'ring-4 ring-[#D2E90D]/20';
  } else if (isTarget) {
    // Blue border for target
    borderClass = 'border-[#1463FF]';
    ringClass = 'ring-4 ring-[#1463FF]/10';
  }

  return (
    <div
      className={`
        px-3 py-2 sm:px-4 sm:py-3 rounded-xl sm:rounded-2xl border-2 shadow-md text-center
        transition-all duration-200
        hover:shadow-lg hover:scale-105
        touch-manipulation
        ${bgClass} ${borderClass} ${ringClass}
      `}
      style={{
        minWidth: '140px',
        maxWidth: '180px',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3"
        style={{ background: color }}
      />

      {/* Badge for target or root gap */}
      {isTarget && (
        <div className="mb-1 sm:mb-2 text-[10px] sm:text-xs font-bold uppercase tracking-wide text-[#1463FF]">
          Target
        </div>
      )}
      {isRootGap && (
        <div className="mb-1 sm:mb-2 text-[10px] sm:text-xs font-bold uppercase tracking-wide text-[#839300]">
          Root Gap
        </div>
      )}

      {/* Concept name with lock icon if locked */}
      <div className="mb-2 sm:mb-3 break-words text-xs sm:text-sm font-semibold text-[#10213d] flex items-center justify-center gap-1">
        {isLocked && (
          <svg 
            className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" 
            />
          </svg>
        )}
        <span className="leading-tight">{concept.name}</span>
      </div>

      {/* Mastery Bar */}
      <div className="space-y-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${masteryPercentage}%`,
              backgroundColor: color,
            }}
          />
        </div>
        <div className="flex items-center justify-between text-[10px] sm:text-xs text-gray-600">
          <span className="capitalize truncate">{concept.status}</span>
          <span className="font-medium flex-shrink-0 ml-1">{masteryPercentage}%</span>
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
