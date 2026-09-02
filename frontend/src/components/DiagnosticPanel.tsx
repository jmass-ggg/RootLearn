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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!question) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No diagnostic question available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Question Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-4">
          <div className="text-sm font-medium text-gray-500 mb-1">
            Testing: {question.concept_name}
          </div>
          <div className="text-xs text-gray-400">
            Difficulty: {Math.round(question.difficulty * 100)}%
          </div>
        </div>

        <div className="prose max-w-none">
          <p className="text-lg text-gray-900 whitespace-pre-wrap">
            {question.question_text}
          </p>
        </div>

        {/* Answer Input Form */}
        {!evaluation && (
          <form onSubmit={handleSubmit} className="mt-6">
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
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={question.question_type === 'code' ? 10 : 5}
                  placeholder={
                    question.question_type === 'code'
                      ? 'Enter your code here...'
                      : 'Enter your answer here...'
                  }
                  disabled={isSubmitting}
                  required
                />
              ) : (
                <input
                  id="answer"
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your answer here..."
                  disabled={isSubmitting}
                  required
                />
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !answer.trim()}
              className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
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

      {/* Evaluation Feedback */}
      {evaluation && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Evaluation Results
          </h3>

          {/* Scores */}
          <div className="grid grid-cols-2 gap-4">
            <div className={`p-4 rounded-lg ${getMasteryBgColor(evaluation.correctness_score)}`}>
              <div className="text-sm font-medium text-gray-600 mb-1">
                Correctness
              </div>
              <div className={`text-2xl font-bold ${getMasteryColor(evaluation.correctness_score)}`}>
                {Math.round(evaluation.correctness_score * 100)}%
              </div>
            </div>

            <div className={`p-4 rounded-lg ${getMasteryBgColor(evaluation.reasoning_score)}`}>
              <div className="text-sm font-medium text-gray-600 mb-1">
                Reasoning
              </div>
              <div className={`text-2xl font-bold ${getMasteryColor(evaluation.reasoning_score)}`}>
                {Math.round(evaluation.reasoning_score * 100)}%
              </div>
            </div>
          </div>

          {/* Demonstrated Points */}
          {evaluation.demonstrated_points.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-green-700 mb-2">
                ✓ What you got right:
              </h4>
              <ul className="space-y-1">
                {evaluation.demonstrated_points.map((point, index) => (
                  <li key={index} className="text-sm text-gray-700 pl-4">
                    • {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Points */}
          {evaluation.missing_points.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-orange-700 mb-2">
                ⚠ What was missing:
              </h4>
              <ul className="space-y-1">
                {evaluation.missing_points.map((point, index) => (
                  <li key={index} className="text-sm text-gray-700 pl-4">
                    • {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Misconceptions */}
          {evaluation.misconceptions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 mb-2">
                ✗ Misconceptions detected:
              </h4>
              <ul className="space-y-1">
                {evaluation.misconceptions.map((misconception, index) => (
                  <li key={index} className="text-sm text-gray-700 pl-4">
                    • {misconception}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Diagnosis Status */}
          {evaluation.should_stop && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">
                ✓ Diagnostic assessment complete! Moving to root gap identification...
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
