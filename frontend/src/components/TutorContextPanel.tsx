'use client';

import { Card } from './ui/Card';
import { FadeIn } from './ui/FadeTransition';
import type { PrerequisiteGraph, RootGapResult } from '@/types';

interface TutorContextPanelProps {
  currentConcept: {
    id: string;
    name: string;
  } | null;
  masteryScore: number;
  confidenceScore: number;
  rootGap: RootGapResult | null;
  graph?: PrerequisiteGraph;
}

/**
 * TutorContextPanel - Compact left sidebar showing learning context
 * Requirements: 8.3, 8.4
 * 
 * Displays:
 * - Current objective/learning goal
 * - Concept being learned
 * - Mastery bar with real mastery value
 * - Confidence indicator
 * - Learning path visualization
 * 
 * Made compact to maximize conversation space
 */
export default function TutorContextPanel({
  currentConcept,
  masteryScore,
  confidenceScore,
  rootGap,
  graph,
}: TutorContextPanelProps) {
  // Get mastery color classes based on score
  const getMasteryColor = (score: number): string => {
    if (score >= 0.85) return 'text-mastery-mastered';
    if (score >= 0.70) return 'text-mastery-understood';
    if (score >= 0.40) return 'text-mastery-learning';
    return 'text-mastery-weak';
  };

  const getMasteryBgColor = (score: number): string => {
    if (score >= 0.85) return 'bg-mastery-mastered';
    if (score >= 0.70) return 'bg-mastery-understood';
    if (score >= 0.40) return 'bg-mastery-learning';
    return 'bg-mastery-weak';
  };

  // Get learning path from root gap to target
  const learningPath = graph?.concepts.slice(0, 5) || [];
  const isConceptInPath = (conceptId: string) =>
    learningPath.some((c) => c.id === conceptId);

  return (
    <FadeIn duration={300}>
      <div className="space-y-6">
      {/* Current objective card */}
      <Card variant="default" padding="lg">
        <div className="space-y-4">
          {/* Objective header */}
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-text-muted mb-2">
              Current Objective
            </p>
            {currentConcept ? (
              <h2 className="text-xl font-semibold text-text-heading">
                <span className="text-brand-blue mr-2">◎</span>
                Understand {currentConcept.name}
              </h2>
            ) : (
              <p className="text-text-body">Loading concept...</p>
            )}
          </div>

          {/* Mastery score */}
          <div>
            <div className="flex items-baseline justify-between mb-2">
              <span className="text-sm font-medium text-text-body">
                Mastery
              </span>
              <span
                className={`text-2xl font-bold ${getMasteryColor(masteryScore)}`}
                aria-label={`Mastery: ${Math.round(masteryScore * 100)} percent`}
              >
                {Math.round(masteryScore * 100)}%
              </span>
            </div>
            {/* Mastery progress bar */}
            <div
              className="h-2 w-full rounded-full bg-gray-200"
              role="progressbar"
              aria-valuenow={masteryScore * 100}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Mastery progress"
            >
              <div
                className={`h-2 rounded-full transition-all duration-500 ${getMasteryBgColor(
                  masteryScore
                )}`}
                style={{ width: `${masteryScore * 100}%` }}
              />
            </div>
          </div>

          {/* Confidence indicator */}
          <div className="flex items-center justify-between pt-2 border-t border-border">
            <span className="text-sm font-medium text-text-body">
              Confidence
            </span>
            <span className="text-sm font-semibold text-text-heading">
              {Math.round(confidenceScore * 100)}%
            </span>
          </div>
        </div>
      </Card>

      {/* Learning path visualization */}
      {learningPath.length > 0 && (
        <Card variant="default" padding="lg">
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-bold text-text-heading mb-1">
                Learning Path
              </h3>
              <p className="text-xs text-text-muted">
                Root gap → Target concept
              </p>
            </div>

            {/* Path steps */}
            <ol className="space-y-3">
              {learningPath.map((concept, index) => {
                const isRootGap = concept.id === rootGap?.root_gap.concept_id;
                const isCurrent = concept.id === currentConcept?.id;
                const isMastered = concept.status === 'mastered';

                return (
                  <li key={concept.id} className="flex gap-3 items-start">
                    {/* Step indicator */}
                    <span
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold ${
                        isMastered
                          ? 'border-mastery-mastered bg-mastery-mastered text-white'
                          : isCurrent
                          ? 'border-brand-blue bg-brand-blue text-white'
                          : isRootGap
                          ? 'border-brand-lime bg-brand-lime text-text-heading'
                          : 'border-mastery-learning bg-bg-workspace text-mastery-learning'
                      }`}
                      aria-label={
                        isMastered
                          ? 'Mastered'
                          : isCurrent
                          ? 'Current'
                          : isRootGap
                          ? 'Root gap'
                          : 'Not started'
                      }
                    >
                      {isMastered ? '✓' : isCurrent ? '▷' : index + 1}
                    </span>

                    {/* Concept info */}
                    <div className="flex-1 min-w-0 pt-1">
                      <p
                        className={`font-semibold text-sm truncate ${
                          isCurrent ? 'text-brand-blue' : 'text-text-heading'
                        }`}
                      >
                        {concept.name}
                      </p>
                      <p className="text-xs text-text-muted capitalize">
                        {isCurrent
                          ? 'Current concept'
                          : isRootGap
                          ? 'Root gap'
                          : concept.status}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </Card>
      )}

      {/* Mastery legend */}
      <Card variant="default" padding="md">
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-text-heading">
            Mastery Legend
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-mastery-mastered">●</span>
              <span className="text-text-body">Mastered</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-brand-blue">●</span>
              <span className="text-text-body">Currently learning</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-brand-lime">●</span>
              <span className="text-text-body">Root gap</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-mastery-learning">●</span>
              <span className="text-text-body">Learning</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-mastery-unknown">○</span>
              <span className="text-text-body">Not reached</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
    </FadeIn>
  );
}
