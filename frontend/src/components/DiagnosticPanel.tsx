'use client';

import { useState } from 'react';
import { DiagnosticQuestion, DiagnosticEvaluation } from '@/types/diagnostic';

interface DiagnosticPanelProps {
  question: DiagnosticQuestion | null;
  evaluation: DiagnosticEvaluation | null;
  isLoading: boolean;
  onSubmitAnswer: (answer: string) => Promise<void>;
}

/**
 * DiagnosticPanel component
 * Displays diagnostic questions and collects student answers
 */
export default function DiagnosticPanel({
  question,
  evaluation,
  isLoading,
  onSubmitAnswer,
}: DiagnosticPanelProps) {
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
    if (score >= 0.85) return 'text-green-600';
    if (score >= 0.70) return 'text-lime-600';
    if (score >= 0.40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMasteryBgColor = (score: number): string => {
    if (score >= 0.85) return 'bg-green-100';
    if (score >= 0.70) return 'bg-lime-100';
    if (score >= 0.40) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  // Loading State
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-3" aria-hidden="true"></div>
          <p className="text-gray-600 text-sm">Loading diagnostic question...</p>
          <span className="sr-only">Loading diagnostic question, please wait</span>
        </div>
      </div>
    );
  }

  // Empty State
  if (!question) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 p-6" role="status">
        <svg
          className="w-16 h-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-center">No diagnostic question available</p>
        <p className="text-sm text-gray-400 mt-2">Assessment will begin shortly</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Question Section - Responsive */}
      <div>
        <div className="mb-7">
          <div className="flex items-center justify-between gap-4">
            <span className="rounded-full bg-[#eaf1ff] px-3 py-1.5 text-sm font-semibold text-[#1463ff]">{question.concept_name}</span>
            <span className="text-sm text-[#718096]">Question in progress</span>
          </div>
          <div className="mt-3 flex gap-2" aria-hidden="true"><i className="h-1.5 flex-1 rounded-full bg-[#1463ff]" /><i className="h-1.5 flex-1 rounded-full bg-[#1463ff]" /><i className="h-1.5 flex-1 rounded-full bg-[#e2e8f0]" /><i className="h-1.5 flex-1 rounded-full bg-[#e2e8f0]" /></div>
          <h2 className="mt-7 text-2xl font-bold text-[#10213d]">Diagnostic Assessment</h2>
          <div className="mt-3 text-sm font-medium text-[#718096]"><span>Testing: {question.concept_name}</span><span className="ml-3 text-xs text-[#98a2b3]">Difficulty: {Math.round(question.difficulty * 100)}%</span></div>
        </div>

        <div className="prose max-w-none">
          <p className="whitespace-pre-wrap break-words text-lg font-medium leading-8 text-[#10213d]">
            {question.question_text}
          </p>
        </div>

        {/* Answer Input Form - Responsive */}
        {!evaluation && (
          <form onSubmit={handleSubmit} className="mt-6" aria-label="Answer diagnostic question">
            <div className="mb-4">
              <label
                htmlFor="answer"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Your Answer
              </label>
              {question.question_type === 'short_answer' ||
              question.question_type === 'reasoning' ||
              question.question_type === 'code' ? (
                <textarea
                  id="answer"
                  name="diagnostic-answer"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full resize-none rounded-xl border border-[#dce4ef] bg-[#fbfcfe] px-4 py-3 text-sm transition-shadow focus:border-[#1463ff] focus:bg-white sm:text-base"
                  rows={question.question_type === 'code' ? 10 : 5}
                  placeholder={
                    question.question_type === 'code'
                      ? 'Enter your code here...'
                      : 'Enter your answer here...'
                  }
                  disabled={isSubmitting}
                  required
                  aria-required="true"
                  autoFocus
                />
              ) : (
                <input
                  id="answer"
                  name="diagnostic-answer"
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full rounded-xl border border-[#dce4ef] bg-[#fbfcfe] px-4 py-3 text-sm transition-shadow focus:border-[#1463ff] focus:bg-white sm:text-base"
                  placeholder="Enter your answer here..."
                  disabled={isSubmitting}
                  required
                  aria-required="true"
                  autoFocus
                />
              )}
            </div>

            <div className="mb-5 rounded-xl bg-[#f4f7fb] p-4 text-sm leading-6 text-[#718096]"><span className="mr-2 font-bold text-[#1463ff]">ⓘ</span>Honest answers, even partial ones, help RootLearn pinpoint your real gap. There is no penalty for being unsure.</div>
            <button
              type="submit"
              disabled={isSubmitting || !answer.trim()}
              className="w-full rounded-xl bg-[#1463ff] px-6 py-3.5 font-semibold text-white transition hover:bg-[#0754e8] disabled:cursor-not-allowed disabled:bg-[#aebbd0]"
              aria-label={isSubmitting ? 'Submitting answer, please wait' : 'Submit answer'}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Submitting...
                </span>
              ) : (
                'Submit Answer'
              )}
            </button>
          </form>
        )}
      </div>

      {/* Evaluation Feedback - Responsive */}
      {evaluation && (
        <div 
          className="space-y-4 rounded-xl border border-[#dce5ef] bg-[#f8fafc] p-4 sm:p-6"
          role="region"
          aria-label="Evaluation results"
          aria-live="polite"
        >
          <h3 className="text-base sm:text-lg font-semibold text-gray-900">
            Evaluation Results
          </h3>

          {/* Scores - Responsive Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className={`p-3 sm:p-4 rounded-lg ${getMasteryBgColor(evaluation.correctness_score)}`}>
              <div className="text-xs sm:text-sm font-medium text-gray-600 mb-1">
                Correctness
              </div>
              <div className={`text-xl sm:text-2xl font-bold ${getMasteryColor(evaluation.correctness_score)}`}>
                {Math.round(evaluation.correctness_score * 100)}%
              </div>
            </div>

            <div className={`p-3 sm:p-4 rounded-lg ${getMasteryBgColor(evaluation.reasoning_score)}`}>
              <div className="text-xs sm:text-sm font-medium text-gray-600 mb-1">
                Reasoning
              </div>
              <div className={`text-xl sm:text-2xl font-bold ${getMasteryColor(evaluation.reasoning_score)}`}>
                {Math.round(evaluation.reasoning_score * 100)}%
              </div>
            </div>
          </div>

          {/* Demonstrated Points */}
          {evaluation.demonstrated_points.length > 0 && (
            <div>
              <h4 className="text-xs sm:text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
                <span aria-hidden="true">✓</span>
                <span>What you got right:</span>
              </h4>
              <ul className="space-y-1" role="list">
                {evaluation.demonstrated_points.map((point, index) => (
                  <li key={index} className="text-xs sm:text-sm text-gray-700 pl-4 break-words">
                    • {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Points */}
          {evaluation.missing_points.length > 0 && (
            <div>
              <h4 className="text-xs sm:text-sm font-semibold text-orange-700 mb-2 flex items-center gap-1">
                <span aria-hidden="true">⚠</span>
                <span>What was missing:</span>
              </h4>
              <ul className="space-y-1" role="list">
                {evaluation.missing_points.map((point, index) => (
                  <li key={index} className="text-xs sm:text-sm text-gray-700 pl-4 break-words">
                    • {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Misconceptions */}
          {evaluation.misconceptions.length > 0 && (
            <div>
              <h4 className="text-xs sm:text-sm font-semibold text-red-700 mb-2 flex items-center gap-1">
                <span aria-hidden="true">✗</span>
                <span>Misconceptions detected:</span>
              </h4>
              <ul className="space-y-1" role="list">
                {evaluation.misconceptions.map((misconception, index) => (
                  <li key={index} className="text-xs sm:text-sm text-gray-700 pl-4 break-words">
                    • {misconception}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Diagnosis Status */}
          {evaluation.should_stop && (
            <div className="mt-4 p-3 sm:p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs sm:text-sm text-blue-800 font-medium flex items-center gap-2">
                <span aria-hidden="true">✓</span>
                <span>Diagnostic assessment complete! Moving to root gap identification...</span>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
