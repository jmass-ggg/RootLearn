'use client';

import { useState } from 'react';
import { DiagnosticQuestion, DiagnosticEvaluation } from '@/types/diagnostic';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StateDisplay } from './ui/StateDisplay';
import { colors } from '@/theme/tokens';

interface DiagnosticAssessmentCardProps {
  question: DiagnosticQuestion | null;
  evaluation: DiagnosticEvaluation | null;
  isLoading: boolean;
  onSubmitAnswer: (answer: string) => Promise<void>;
}

/**
 * DiagnosticAssessmentCard component
 * Displays diagnostic questions and collects student answers with redesigned UI
 */
export default function DiagnosticAssessmentCard({
  question,
  evaluation,
  isLoading,
  onSubmitAnswer,
}: DiagnosticAssessmentCardProps) {
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!answer.trim() || !question) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmitAnswer(answer);
      setAnswer(''); // Clear answer after successful submission
    } catch (error) {
      console.error('Failed to submit answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getMasteryColor = (score: number): string => {
    if (score >= 0.85) return colors.mastery.mastered;
    if (score >= 0.70) return colors.mastery.understood;
    if (score >= 0.40) return colors.mastery.learning;
    return colors.mastery.weak;
  };

  // Loading State
  if (isLoading) {
    return (
      <Card variant="default" padding="xl">
        <StateDisplay
          variant="loading"
          title="Loading question..."
          description="Preparing your diagnostic assessment"
        />
      </Card>
    );
  }

  // Empty State
  if (!question) {
    return (
      <Card variant="default" padding="xl">
        <StateDisplay
          variant="empty"
          title="No question available"
          description="Assessment will begin shortly"
        />
      </Card>
    );
  }

  return (
    <Card variant="default" padding="xl" className="h-full">
      <div className="space-y-6">
        {/* Concept Badge with mastery color */}
        <div className="flex items-center justify-between">
          <span
            className="inline-block rounded-full px-4 py-2 text-sm font-semibold"
            style={{
              backgroundColor: `${colors.brand.blue}15`,
              color: colors.brand.blue,
            }}
          >
            {question.concept_name}
          </span>
          {/* Progress indicator - truthful wording when total unknown */}
          <span className="text-sm text-text-muted">
            Question in progress
          </span>
        </div>

        {/* Question text */}
        <div>
          <h2 className="text-2xl font-bold text-text-heading mb-4">
            Diagnostic Assessment
          </h2>
          <p className="text-lg text-text-heading whitespace-pre-wrap leading-relaxed">
            {question.question_text}
          </p>
        </div>

        {/* Answer Input Form */}
        {!evaluation && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="answer"
                className="block text-sm font-medium text-text-body mb-2"
              >
                Your Answer
              </label>
              {question.question_type === 'short_answer' ||
              question.question_type === 'reasoning' ||
              question.question_type === 'code' ? (
                <textarea
                  id="answer"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full resize-none rounded-lg border border-gray-300 bg-white px-4 py-3 text-base transition-colors focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/20"
                  rows={question.question_type === 'code' ? 10 : 5}
                  placeholder={
                    question.question_type === 'code'
                      ? 'Enter your code here...'
                      : 'Enter your answer here...'
                  }
                  disabled={isSubmitting}
                  required
                  autoFocus
                />
              ) : (
                <input
                  id="answer"
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-base transition-colors focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/20"
                  placeholder="Enter your answer here..."
                  disabled={isSubmitting}
                  required
                  autoFocus
                />
              )}
            </div>

            {/* Reassurance text */}
            <div className="rounded-lg bg-background-workspace p-4 text-sm text-text-body">
              <span className="font-semibold text-brand-blue">💡 </span>
              Honest answers, even partial ones, help us pinpoint your real gap. There&apos;s no penalty for being unsure.
            </div>

            {/* Submit button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              isDisabled={!answer.trim()}
              className="w-full"
            >
              {isSubmitting ? 'Submitting...' : 'Submit answer'}
            </Button>
          </form>
        )}

        {/* Evaluation Feedback */}
        {evaluation && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-text-heading">
              Evaluation Results
            </h3>

            {/* Scores */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-background-workspace p-4">
                <div className="text-sm font-medium text-text-muted mb-2">
                  Correctness
                </div>
                <div
                  className="text-2xl font-bold"
                  style={{ color: getMasteryColor(evaluation.correctness_score) }}
                >
                  {Math.round(evaluation.correctness_score * 100)}%
                </div>
              </div>

              <div className="rounded-lg bg-background-workspace p-4">
                <div className="text-sm font-medium text-text-muted mb-2">
                  Reasoning
                </div>
                <div
                  className="text-2xl font-bold"
                  style={{ color: getMasteryColor(evaluation.reasoning_score) }}
                >
                  {Math.round(evaluation.reasoning_score * 100)}%
                </div>
              </div>
            </div>

            {/* Demonstrated Points (green checkmarks) */}
            {evaluation.demonstrated_points.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: colors.mastery.mastered }}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>What you got right:</span>
                </h4>
                <ul className="space-y-2">
                  {evaluation.demonstrated_points.map((point, index) => (
                    <li key={index} className="text-sm text-text-body flex items-start gap-2">
                      <span className="text-green-600 flex-shrink-0 mt-0.5">✓</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Points (amber warnings) */}
            {evaluation.missing_points.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: colors.mastery.learning }}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>What was missing:</span>
                </h4>
                <ul className="space-y-2">
                  {evaluation.missing_points.map((point, index) => (
                    <li key={index} className="text-sm text-text-body flex items-start gap-2">
                      <span className="text-amber-600 flex-shrink-0 mt-0.5">⚠</span>
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Misconceptions (red alerts) */}
            {evaluation.misconceptions.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: colors.mastery.weak }}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span>Misconceptions detected:</span>
                </h4>
                <ul className="space-y-2">
                  {evaluation.misconceptions.map((misconception, index) => (
                    <li key={index} className="text-sm text-text-body flex items-start gap-2">
                      <span className="text-red-600 flex-shrink-0 mt-0.5">✗</span>
                      <span>{misconception}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
