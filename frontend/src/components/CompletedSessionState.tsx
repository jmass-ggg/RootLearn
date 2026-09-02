import React from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import type { MasteryEvent } from '@/types';

interface CompletedSessionStateProps {
  masteryEvents?: MasteryEvent[];
  onNewSession: () => void;
  onReviewHistory?: () => void;
}

export const CompletedSessionState: React.FC<CompletedSessionStateProps> = ({
  masteryEvents,
  onNewSession,
  onReviewHistory,
}) => {
  // Calculate summary stats from mastery events
  const conceptsMastered = masteryEvents?.filter(
    (event) => event.new_score >= 0.8 // Consider mastered if score >= 0.8
  ).length || 0;

  const totalEvents = masteryEvents?.length || 0;

  return (
    <div className="workspace-pattern flex min-h-[calc(100vh-76px)] items-center justify-center p-6">
      <Card variant="elevated" padding="xl" className="w-full max-w-2xl text-center">
        {/* Success Icon */}
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[#e2f7ef] text-4xl text-[#20a572] mb-6">
          ✓
        </div>

        {/* Heading */}
        <h1 className="text-3xl font-bold text-text-heading mb-3">
          Learning Complete!
        </h1>

        {/* Description */}
        <p className="text-lg text-text-body mb-8 max-w-lg mx-auto">
          You&apos;ve worked through your root knowledge gap and verified your understanding through teach-back.
        </p>

        {/* Mastery Achievements */}
        {totalEvents > 0 && (
          <div className="border-t border-border-default pt-6 mb-8">
            <h2 className="text-xl font-semibold text-text-heading mb-4">
              Your Progress
            </h2>
            <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
              <div className="bg-[#f8fafc] rounded-lg p-4 border border-border-default">
                <div className="text-3xl font-bold text-brand-blue mb-1">
                  {conceptsMastered}
                </div>
                <div className="text-sm text-text-body">
                  Concepts Mastered
                </div>
              </div>
              <div className="bg-[#f8fafc] rounded-lg p-4 border border-border-default">
                <div className="text-3xl font-bold text-brand-blue mb-1">
                  {totalEvents}
                </div>
                <div className="text-sm text-text-body">
                  Progress Updates
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
          <Button
            variant="primary"
            size="lg"
            onClick={onNewSession}
          >
            Start New Session
          </Button>
          {onReviewHistory && (
            <Button
              variant="ghost"
              size="lg"
              onClick={onReviewHistory}
            >
              Review Session History
            </Button>
          )}
        </div>

        {/* Optional: List key concepts mastered */}
        {masteryEvents && masteryEvents.length > 0 && (
          <div className="mt-8 pt-6 border-t border-border-default text-left">
            <h3 className="text-sm font-semibold text-text-heading mb-3">
              Concepts You&apos;ve Mastered
            </h3>
            <div className="space-y-2">
              {masteryEvents
                .filter((event) => event.new_score >= 0.8) // Mastered threshold
                .slice(0, 5)
                .map((event, index) => (
                  <div
                    key={`${event.concept_id}-${index}`}
                    className="flex items-center gap-2 text-sm text-text-body"
                  >
                    <span className="text-[#20a572]">✓</span>
                    <span className="capitalize">
                      {event.concept_id.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
