'use client';

import { useState } from 'react';
import { DiagnosticQuestion, DiagnosticEvaluation } from '@/types/diagnostic';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { StateDisplay } from './ui/StateDisplay';
import { FadeIn, FadeTransition } from './ui/FadeTransition';
import { colors } from '@/theme/tokens';

interface DiagnosticAssessmentCardProps {
  question: DiagnosticQuestion | null;
  evaluation: DiagnosticEvaluation | null;
  isLoading: boolean;
  onSubmitAnswer: (answer: string) => Promise<void>;
  masteryScore?: number;
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
  masteryScore = 0,
}: DiagnosticAssessmentCardProps) {
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUnsure, setIsUnsure] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if ((!answer.trim() && !isUnsure) || !question) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmitAnswer(isUnsure ? 'I am unsure about this question.' : answer);
      setAnswer(''); // Clear answer after successful submission
      setIsUnsure(false);
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
    <Card variant="default" padding="xl" className="h-full shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
      <FadeTransition transitionKey={question?.question_id || 'no-question'} duration={250}>
        <div className="space-y-7">
        {/* Concept Badge with mastery color */}
        <div className="flex items-center justify-between gap-4">
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
          <span className="flex items-center gap-2 text-sm text-[#777c86]">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[#cbd0d7] border-t-[#737a85]" aria-hidden="true" />
            Question in progress
          </span>
        </div>

        {/* Question text */}
        <div>
          <h2 className="mb-5 text-2xl font-bold tracking-tight text-[#111827] sm:text-[28px]">
            Diagnostic Assessment
          </h2>
          <p className="whitespace-pre-wrap text-[17px] leading-8 text-[#656a74]">
            {question.question_text}
          </p>
        </div>

        {/* Answer Input Form */}
        {!evaluation && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="answer"
                className="mb-3 block text-base font-semibold text-[#20242b]"
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
                  className="w-full resize-none rounded-xl border border-[#d9dde3] bg-white px-4 py-4 text-base text-[#20242b] shadow-sm transition-colors placeholder:text-[#9ba0aa] focus:border-[#4b98f9] focus:outline-none focus:ring-2 focus:ring-[#4b98f9]/15"
                  rows={question.question_type === 'code' ? 10 : 7}
                  placeholder={
                    question.question_type === 'code'
                      ? 'Enter your code here...'
                      : 'Enter your answer here...'
                  }
                  disabled={isSubmitting}
                  required={!isUnsure}
                  autoFocus
                  aria-required={!isUnsure}
                />
              ) : (
                <input
                  id="answer"
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full rounded-xl border border-[#d9dde3] bg-white px-4 py-4 text-base text-[#20242b] shadow-sm transition-colors placeholder:text-[#9ba0aa] focus:border-[#4b98f9] focus:outline-none focus:ring-2 focus:ring-[#4b98f9]/15"
                  placeholder="Enter your answer here..."
                  disabled={isSubmitting}
                  required={!isUnsure}
                  autoFocus
                  aria-required={!isUnsure}
                />
              )}
            </div>

            <label className="flex cursor-pointer items-center gap-3 text-base text-[#747983]">
              <input
                type="checkbox"
                checked={isUnsure}
                onChange={(event) => setIsUnsure(event.target.checked)}
                disabled={isSubmitting}
                className="h-5 w-5 rounded border-[#cfd4db] text-[#4b98f9] focus:ring-[#4b98f9]"
              />
              I&apos;m unsure about this one
            </label>

            <div>
              <p className="mb-3 text-base font-semibold text-[#20242b]">Difficulty</p>
              <div className="flex h-12 items-center justify-between rounded-xl border border-[#d9dde3] bg-white px-4 text-base text-[#20242b] shadow-sm" aria-label="Difficulty: Adaptive">
                <span>Adaptive</span>
                <svg className="h-5 w-5 text-[#777c86]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
              </div>
            </div>

            {/* Reassurance text */}
            <div className="flex gap-3 rounded-xl bg-[#f4f4f5] p-4 text-sm leading-6 text-[#747983]">
              <svg className="mt-0.5 h-5 w-5 shrink-0 text-[#f59e0b]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d="M9 18h6M10 22h4M8.5 15.5A7 7 0 1 1 15.5 15.5c-.9.7-1.5 1.5-1.5 2.5h-4c0-1-.6-1.8-1.5-2.5Z" /></svg>
              <span>Honest answers, even partial ones, help us pinpoint your real gap. There&apos;s no penalty for being unsure.</span>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between text-sm text-[#777c86]">
                <span>{question.concept_name} mastery</span>
                <span>{Math.round(masteryScore * 100)}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[#eeeeef]">
                <div className="h-full rounded-full bg-[#dce7f7] transition-all duration-500" style={{ width: `${Math.round(masteryScore * 100)}%` }} />
              </div>
            </div>

            {/* Submit button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              isLoading={isSubmitting}
              isDisabled={!answer.trim() && !isUnsure}
              className="w-full !rounded-lg !bg-[#6daaf7] hover:!bg-[#4b98f9]"
            >
              {isSubmitting ? 'Submitting...' : 'Submit answer'}
            </Button>
          </form>
        )}

        {/* Evaluation Feedback */}
        {evaluation && (
          <FadeIn duration={300}>
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
          </FadeIn>
        )}
      </div>
      </FadeTransition>
    </Card>
  );
}
