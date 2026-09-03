'use client';

import { useState } from 'react';
import { TeachBackResponse } from '@/types/teachback';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StateDisplay } from '@/components/ui/StateDisplay';
import { FadeIn, FadeTransition } from '@/components/ui/FadeTransition';

interface TeachBackPanelProps {
  currentConcept: {
    id: string;
    name: string;
    description?: string;
  } | null;
  masteryScore: number;
  confidenceScore: number;
  evaluation: TeachBackResponse | null;
  isLoading: boolean;
  error?: Error | null;
  onSubmitExplanation: (explanation: string) => Promise<TeachBackResponse>;
  onContinue: () => void;
  onRetry?: () => void;
}

/**
 * TeachBackPanel component
 * Collects student explanation and displays evaluation results
 * Requirements: 9.2, 9.3, 9.4, 9.5, 9.6
 */
export default function TeachBackPanel({
  currentConcept,
  masteryScore,
  confidenceScore,
  evaluation,
  isLoading,
  error,
  onSubmitExplanation,
  onContinue,
  onRetry,
}: TeachBackPanelProps) {
  const [explanation, setExplanation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  // Minimum word count for valid explanation
  const MIN_WORDS = 8;
  
  const getWordCount = (text: string): number => {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  };

  const isExplanationValid = (): boolean => {
    return getWordCount(explanation) >= MIN_WORDS;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!explanation.trim() || !currentConcept) {
      return;
    }

    setIsSubmitting(true);
    setSubmissionError(null); // Clear previous errors
    try {
      await onSubmitExplanation(explanation);
      setExplanation(''); // Clear explanation after successful submission
    } catch (error) {
      console.error('Failed to submit explanation:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to submit explanation. Please try again.';
      setSubmissionError(errorMessage);
      // Don't clear on error so user can retry
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    // Clear the explanation and error to allow retry
    setExplanation('');
    setSubmissionError(null);
    // Call the onRetry callback if provided, otherwise just clear evaluation state
    if (onRetry) {
      onRetry();
    }
  };

  const getMasteryTextColor = (score: number): string => {
    if (score >= 0.85) return 'text-mastery-mastered';
    if (score >= 0.70) return 'text-mastery-understood';
    if (score >= 0.40) return 'text-mastery-learning';
    return 'text-mastery-weak';
  };

  const getMasteryBarColor = (score: number): string => {
    if (score >= 0.85) return 'bg-mastery-mastered';
    if (score >= 0.70) return 'bg-mastery-understood';
    if (score >= 0.40) return 'bg-mastery-learning';
    return 'bg-mastery-weak';
  };

  const getMasteryStrokeColor = (score: number): string => {
    if (score >= 0.85) return 'stroke-mastery-mastered';
    if (score >= 0.70) return 'stroke-mastery-understood';
    if (score >= 0.40) return 'stroke-mastery-learning';
    return 'stroke-mastery-weak';
  };

  // Loading state during evaluation
  if (isLoading) {
    return (
      <Card variant="elevated" padding="xl">
        <StateDisplay
          variant="loading"
          title="Evaluating your explanation..."
          description="We're analyzing your understanding. This will just take a moment."
        />
      </Card>
    );
  }

  // No concept state
  if (!currentConcept) {
    return (
      <Card variant="elevated" padding="xl">
        <StateDisplay
          variant="empty"
          title="No teach-back session active"
          description="Please start a tutoring session first."
        />
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Teach-Back Form */}
      {!evaluation && (
        <Card variant="elevated" padding="xl">
          {/* Header: Clearly identify concept being explained */}
          <div className="mb-6">
            <div className="inline-block px-3 py-1 bg-brand-blue/10 text-brand-blue rounded-full text-sm font-medium mb-3">
              {currentConcept.name}
            </div>
            <h2 className="text-2xl font-bold text-text-heading mb-2">
              Teach it back
            </h2>
            <p className="text-base text-text-body">
              Explain {currentConcept.name} in your own words. This helps verify your understanding and identify any remaining gaps.
            </p>
          </div>

          {/* Tips section */}
          <div className="bg-brand-blue/5 border-l-4 border-brand-blue rounded-r-lg p-4 mb-6">
            <div className="flex gap-3">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  className="h-5 w-5 text-brand-blue"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-brand-blue mb-2">
                  Tips for a great explanation:
                </p>
                <ul className="list-disc list-inside text-sm text-text-body space-y-1">
                  <li>Explain the core concept clearly</li>
                  <li>Include why it&apos;s important or how it works</li>
                  <li>Use your own words, not just what you memorized</li>
                  <li>Add an example if it helps</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Explanation Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error Display */}
            {submissionError && (
              <div className="bg-mastery-weak/10 border-l-4 border-mastery-weak rounded-r-lg p-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <svg
                      className="h-5 w-5 text-mastery-weak"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-mastery-weak">
                      {submissionError}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label
                htmlFor="explanation"
                className="block text-sm font-medium text-text-heading mb-2"
              >
                Your Explanation
              </label>
              <textarea
                id="explanation"
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                className="w-full px-4 py-3 border border-border-default rounded-lg focus:ring-2 focus:ring-brand-blue focus:border-transparent resize-none text-text-body bg-bg-card"
                rows={14}
                placeholder="Start typing your explanation here..."
                disabled={isSubmitting}
                required
              />
              <div className="mt-2 flex justify-between items-center">
                <p className="text-xs text-text-muted">
                  {getWordCount(explanation)} words (minimum {MIN_WORDS} words)
                </p>
                {explanation.trim() && !isExplanationValid() && (
                  <p className="text-xs text-mastery-learning">
                    Please write at least {MIN_WORDS} words
                  </p>
                )}
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              isDisabled={!isExplanationValid()}
              className="w-full"
            >
              {isSubmitting ? 'Evaluating your explanation...' : 'Submit explanation'}
            </Button>
          </form>
        </Card>
      )}

      {/* Evaluation Results */}
      {evaluation && (
        <Card variant="elevated" padding="xl">
          {/* Header */}
          <div className="border-b border-border-default pb-4 mb-6">
            <div className="inline-block px-3 py-1 bg-brand-blue/10 text-brand-blue rounded-full text-sm font-medium mb-3">
              {evaluation.concept_name}
            </div>
            <h2 className="text-2xl font-bold text-text-heading mb-2">
              Evaluation Results
            </h2>
            <p className="text-base text-text-body">
              Here&apos;s how well you explained the concept
            </p>
          </div>

          {/* Score Grid with visual indicators */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Coverage Score */}
            <div className="p-5 rounded-xl border-2 border-border-default bg-bg-workspace">
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
                Coverage
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className={`text-3xl font-bold ${getMasteryTextColor(evaluation.coverage_score)}`}>
                  {Math.round(evaluation.coverage_score * 100)}%
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-border-default rounded-full h-2 mb-1">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getMasteryBarColor(evaluation.coverage_score)}`}
                  style={{ width: `${evaluation.coverage_score * 100}%` }}
                />
              </div>
              <div className="text-xs text-text-muted">
                Completeness
              </div>
            </div>

            {/* Reasoning Score */}
            <div className="p-5 rounded-xl border-2 border-border-default bg-bg-workspace">
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
                Reasoning
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className={`text-3xl font-bold ${getMasteryTextColor(evaluation.reasoning_score)}`}>
                  {Math.round(evaluation.reasoning_score * 100)}%
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-border-default rounded-full h-2 mb-1">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getMasteryBarColor(evaluation.reasoning_score)}`}
                  style={{ width: `${evaluation.reasoning_score * 100}%` }}
                />
              </div>
              <div className="text-xs text-text-muted">
                Logic
              </div>
            </div>

            {/* Clarity Score */}
            <div className="p-5 rounded-xl border-2 border-border-default bg-bg-workspace">
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-2">
                Clarity
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className={`text-3xl font-bold ${getMasteryTextColor(evaluation.clarity_score)}`}>
                  {Math.round(evaluation.clarity_score * 100)}%
                </span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-border-default rounded-full h-2 mb-1">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getMasteryBarColor(evaluation.clarity_score)}`}
                  style={{ width: `${evaluation.clarity_score * 100}%` }}
                />
              </div>
              <div className="text-xs text-text-muted">
                Communication
              </div>
            </div>
          </div>

          {/* Average Score Highlight */}
          <div className="bg-brand-blue/5 border-2 border-brand-blue/20 rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-text-muted mb-1">
                  Average Score
                </div>
                <div className={`text-4xl font-bold ${getMasteryTextColor(evaluation.average_score)}`}>
                  {Math.round(evaluation.average_score * 100)}%
                </div>
              </div>
              <div className="w-24 h-24">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-border-default"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    strokeWidth="8"
                    strokeDasharray={`${evaluation.average_score * 251.2} 251.2`}
                    strokeLinecap="round"
                    className={`${getMasteryStrokeColor(evaluation.average_score)} transition-all duration-500`}
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Demonstrated Points (Strengths) */}
          {evaluation.demonstrated_points.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-mastery-mastered mb-3 flex items-center gap-2">
                <svg
                  className="h-5 w-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                What you explained well
              </h3>
              <ul className="space-y-2 bg-mastery-mastered/10 border border-mastery-mastered/20 rounded-lg p-4">
                {evaluation.demonstrated_points.map((point, index) => (
                  <li key={index} className="text-sm text-text-body flex items-start gap-2">
                    <span className="text-mastery-mastered mt-0.5 flex-shrink-0">✓</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Points (Gaps) */}
          {evaluation.missing_points.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-mastery-learning mb-3 flex items-center gap-2">
                <svg
                  className="h-5 w-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                What could be added
              </h3>
              <ul className="space-y-2 bg-mastery-learning/10 border border-mastery-learning/20 rounded-lg p-4">
                {evaluation.missing_points.map((point, index) => (
                  <li key={index} className="text-sm text-text-body flex items-start gap-2">
                    <span className="text-mastery-learning mt-0.5 flex-shrink-0">⚠</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Misconceptions */}
          {evaluation.misconceptions.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-mastery-weak mb-3 flex items-center gap-2">
                <svg
                  className="h-5 w-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                Misconceptions to address
              </h3>
              <ul className="space-y-2 bg-mastery-weak/10 border border-mastery-weak/20 rounded-lg p-4">
                {evaluation.misconceptions.map((misconception, index) => (
                  <li key={index} className="text-sm text-text-body flex items-start gap-2">
                    <span className="text-mastery-weak mt-0.5 flex-shrink-0">✗</span>
                    <span>{misconception}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-border-default">
            {evaluation.should_continue_tutoring ? (
              <div className="space-y-3">
                <div className="bg-mastery-learning/10 border border-mastery-learning/30 rounded-lg p-4">
                  <p className="text-sm text-text-heading font-medium">
                    <strong>Almost there! Let&apos;s strengthen your understanding.</strong>
                  </p>
                  <p className="text-sm text-text-body mt-1">
                    Your explanation shows you&apos;re making progress. You can try explaining again or continue with more tutoring.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Button
                    variant="secondary"
                    size="lg"
                    onClick={handleRetry}
                    className="w-full"
                  >
                    Try again
                  </Button>
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={onContinue}
                    className="w-full"
                  >
                    Continue tutoring
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-mastery-mastered/10 border border-mastery-mastered/30 rounded-lg p-4">
                  <p className="text-sm text-text-heading font-medium">
                    <strong>Great work! You&apos;ve mastered it.</strong>
                  </p>
                  <p className="text-sm text-text-body mt-1">
                    Your explanation shows solid understanding. Ready to move forward.
                  </p>
                </div>
                <Button
                  variant="lime"
                  size="lg"
                  onClick={onContinue}
                  className="w-full"
                >
                  Continue
                </Button>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
