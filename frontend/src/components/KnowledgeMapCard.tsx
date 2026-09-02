'use client';

import React, { useRef, useCallback } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import KnowledgeGraph from './KnowledgeGraph';
import { PrerequisiteGraph } from '@/types/graph';
import { StateDisplay } from './ui/StateDisplay';

export interface KnowledgeMapCardProps {
  graph?: PrerequisiteGraph;
  isLoading: boolean;
  error?: Error | null;
  topic: string;
  onRetry?: () => void;
}

// Controls interface for KnowledgeGraph to expose
export interface GraphControlsRef {
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
}

export const KnowledgeMapCard: React.FC<KnowledgeMapCardProps> = ({
  graph,
  isLoading,
  error,
  topic,
  onRetry,
}) => {
  const graphControlsRef = useRef<GraphControlsRef>(null);

  const handleZoomIn = useCallback(() => {
    graphControlsRef.current?.zoomIn();
  }, []);

  const handleZoomOut = useCallback(() => {
    graphControlsRef.current?.zoomOut();
  }, []);

  const handleFitView = useCallback(() => {
    graphControlsRef.current?.fitView();
  }, []);

  return (
    <Card variant="elevated" padding="lg" className="h-full flex flex-col">
      {/* Header with title and controls */}
      <div className="flex items-start justify-between gap-4 mb-4 pb-4 border-b border-border-default">
        <div>
          <h2 className="text-2xl font-bold text-text-heading flex items-center gap-2">
            <span className="text-brand-blue">⌘</span>
            Knowledge Map
          </h2>
          <p className="text-text-body mt-1">Prerequisites for {topic}</p>
        </div>
        
        {/* Controls: fit view, zoom in/out */}
        <div className="flex gap-2" aria-label="Graph controls">
          <button
            onClick={handleZoomIn}
            className="h-10 w-10 flex items-center justify-center rounded-lg border border-border-default text-text-body hover:bg-bg-workspace transition disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Zoom in"
            title="Zoom in"
            disabled={!graph}
          >
            <span className="text-lg">⊕</span>
          </button>
          <button
            onClick={handleZoomOut}
            className="h-10 w-10 flex items-center justify-center rounded-lg border border-border-default text-text-body hover:bg-bg-workspace transition disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Zoom out"
            title="Zoom out"
            disabled={!graph}
          >
            <span className="text-lg">⊖</span>
          </button>
          <button
            onClick={handleFitView}
            className="h-10 w-10 flex items-center justify-center rounded-lg border border-border-default text-text-body hover:bg-bg-workspace transition disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Fit view"
            title="Fit to view"
            disabled={!graph}
          >
            <span className="text-lg">↶</span>
          </button>
        </div>
      </div>

      {/* Mastery Legend */}
      <div className="flex flex-wrap gap-x-5 gap-y-2 py-3 mb-4 border-b border-border-default text-sm text-text-body">
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-unknown" aria-hidden="true" />
          Unknown
        </span>
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-weak" aria-hidden="true" />
          Weak
        </span>
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-learning" aria-hidden="true" />
          Learning
        </span>
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-understood" aria-hidden="true" />
          Understood
        </span>
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-mastered" aria-hidden="true" />
          Mastered
        </span>
        <span className="flex items-center gap-2">
          <i className="h-3 w-3 rounded-full bg-mastery-rootGap" aria-hidden="true" />
          Root gap
        </span>
      </div>

      {/* Graph content area */}
      <div className="flex-1 min-h-[500px] relative">
        {isLoading ? (
          <StateDisplay
            variant="loading"
            title="Building knowledge map"
            description="Analyzing prerequisite relationships..."
          />
        ) : error ? (
          <StateDisplay
            variant="error"
            title="Failed to load knowledge map"
            description={error.message || 'An error occurred while loading the graph'}
            action={onRetry ? {
              label: 'Retry',
              onClick: onRetry,
            } : undefined}
          />
        ) : !graph ? (
          <StateDisplay
            variant="empty"
            title="No knowledge map available"
            description="The knowledge map is being generated"
          />
        ) : (
          <KnowledgeGraph graph={graph} ref={graphControlsRef} />
        )}
      </div>
    </Card>
  );
};
