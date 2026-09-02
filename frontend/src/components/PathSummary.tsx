'use client';

import type { PrerequisiteGraph, RootGapResult } from '@/types';

interface PathSummaryProps {
  graph?: PrerequisiteGraph;
  rootGap: RootGapResult;
}

export default function PathSummary({ graph, rootGap }: PathSummaryProps) {
  // If no graph data, show unavailable state
  if (!graph || !graph.concepts || graph.concepts.length === 0) {
    return (
      <div className="soft-card mt-7 p-7 text-center sm:p-9">
        <p className="text-sm text-text-body">
          Learning path visualization unavailable
        </p>
      </div>
    );
  }

  // Find root gap concept and target concept
  const rootGapConcept = graph.concepts.find(
    c => c.id === rootGap.root_gap.concept_id
  );
  const targetConcept = graph.concepts.find(c => c.is_target);

  // Build a simple path from root gap to target
  // For now, show the first few concepts in the graph as a simple path
  const pathConcepts = graph.concepts.slice(0, 4);

  return (
    <div className="soft-card mt-7 p-7 sm:p-9">
      <h2 className="text-xl font-bold">
        <span className="mr-2 text-brand-blue">→</span>
        Learning path summary
      </h2>
      <p className="mt-2 text-sm text-text-body">
        From your root gap to the target concept
      </p>

      {/* Path visualization */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        {pathConcepts.map((concept, index) => (
          <div key={concept.id} className="flex items-center gap-3">
            <div
              className={`rounded-xl border-2 px-4 py-2 text-sm font-semibold ${
                concept.id === rootGap.root_gap.concept_id
                  ? 'border-brand-lime bg-[#fafce7] text-text-heading'
                  : concept.is_target
                  ? 'border-brand-blue bg-[#eaf1ff] text-brand-blue'
                  : 'border-border bg-bg-card text-text-body'
              }`}
            >
              {concept.name}
              {concept.id === rootGap.root_gap.concept_id && (
                <span className="ml-2 text-xs">(Root gap)</span>
              )}
              {concept.is_target && (
                <span className="ml-2 text-xs">(Target)</span>
              )}
            </div>
            {index < pathConcepts.length - 1 && (
              <span className="text-xl text-text-muted">→</span>
            )}
          </div>
        ))}
      </div>

      {/* Additional context */}
      <div className="mt-6 rounded-xl border border-border bg-bg-workspace p-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              Starting Point
            </p>
            <p className="mt-1 font-semibold text-text-heading">
              {rootGapConcept?.name || rootGap.root_gap.concept_name}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              Goal Concept
            </p>
            <p className="mt-1 font-semibold text-text-heading">
              {targetConcept?.name || 'Target concept'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
