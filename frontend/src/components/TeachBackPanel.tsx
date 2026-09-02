'use client';

import { useState } from 'react';
import { TeachBackResponse } from '@/types/teachback';

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
  onSubmitExplanation: (explanation: string) => Promise<TeachBackResponse>;
  onContinue: () => void;
}

/**
 * TeachBackPanel component
 * Collects student explanation and displays evaluation results
 * Requirements: 10.2, 10.3
 */
export default function TeachBackPanel({
  currentConcept,
  masteryScore,
  confidenceScore,
  evaluation,
  isLoading,
  onSubmitExplanation,
  onContinue,
}: TeachBackPanelProps) {
  const [explanation, setExplanation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    try {
      await onSubmitExplanation(explanation);
      setExplanation(''); // Clear explanation after successful submission
    } catch (error) {
      console.error('Failed to submit explanation:', error);
      // Don't clear on error so user can retry
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

  const getMasteryBarColor = (score: number): string => {
    if (score >= 0.85) return 'bg-green-500';
    if (score >= 0.70) return 'bg-lime-500';
    if (score >= 0.40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!currentConcept) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No teach-back session active</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Instruction Section */}
      {!evaluation && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Teach-Back: {currentConcept.name}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              Time to teach back! Explain {currentConcept.name} in your own words to demonstrate your understanding.
            </p>
            
            {/* Current mastery display */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="text-xs font-medium text-gray-500">Current Mastery</div>
                <div className={`text-xl font-bold ${getMasteryColor(masteryScore)}`}>
                  {Math.round(masteryScore * 100)}%
                </div>
              </div>
              <div className="text-xl font-bold text-blue-600">Confidence: {Math.round(confidenceScore * 100)}%</div>
            </div>
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-blue-400"
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
              <div className="ml-3 flex-1">
                <p className="text-sm text-blue-700">
                  <strong>Tips for a great explanation:</strong>
                </p>
                <ul className="list-disc list-inside text-sm text-blue-700 mt-2 space-y-1">
                  <li>Explain the core concept clearly</li>
                  <li>Include why it&apos;s important or how it works</li>
                  <li>Use your own words, not just what you memorized</li>
                  <li>Add an example if it helps</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Explanation Form */}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="explanation"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Your Explanation
              </label>
              <textarea
                id="explanation"
                value={explanation}
                onChange={(e) => setExplanation(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                rows={12}
                placeholder="Start typing your explanation here..."
                disabled={isSubmitting}
                required
              />
              <div className="mt-2 flex justify-between items-center">
                <p className="text-xs text-gray-500">
                  {getWordCount(explanation)} words (minimum {MIN_WORDS} words)
                </p>
                {explanation.trim() && !isExplanationValid() && (
                  <p className="text-xs text-orange-600">
                    Please write at least {MIN_WORDS} words
                  </p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !isExplanationValid()}
              className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
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
                  Evaluating your explanation...
                </span>
              ) : (
                'Submit My Explanation'
              )}
            </button>
          </form>
        </div>
      )}

      {/* Evaluation Results */}
      {evaluation && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Evaluation Results
            </h3>
            <p className="text-sm text-gray-600">
              Here&apos;s how well you explained: {evaluation.concept_name}
            </p>
          </div>

          {/* Score Grid */}
          <div className="grid grid-cols-3 gap-4">
            {/* Coverage Score */}
            <div className={`p-4 rounded-lg ${getMasteryBgColor(evaluation.coverage_score)}`}>
              <div className="text-xs font-medium text-gray-600 mb-1">
                Coverage
              </div>
              <div className={`text-2xl font-bold ${getMasteryColor(evaluation.coverage_score)}`}>
                {Math.abs(evaluation.coverage_score - evaluation.average_score) < 0.0001 ? `${Math.round(evaluation.coverage_score * 100)}% coverage` : `${Math.round(evaluation.coverage_score * 100)}%`}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Completeness
              </div>
            </div>

            {/* Reasoning Score */}
            <div className={`p-4 rounded-lg ${getMasteryBgColor(evaluation.reasoning_score)}`}>
              <div className="text-xs font-medium text-gray-600 mb-1">
                Reasoning
              </div>
              <div className={`text-2xl font-bold ${getMasteryColor(evaluation.reasoning_score)}`}>
                {Math.abs(evaluation.reasoning_score - evaluation.average_score) < 0.0001 ? `${Math.round(evaluation.reasoning_score * 100)}% reasoning` : `${Math.round(evaluation.reasoning_score * 100)}%`}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Logic
              </div>
            </div>

            {/* Clarity Score */}
            <div className={`p-4 rounded-lg ${getMasteryBgColor(evaluation.clarity_score)}`}>
              <div className="text-xs font-medium text-gray-600 mb-1">
                Clarity
              </div>
              <div className={`text-2xl font-bold ${getMasteryColor(evaluation.clarity_score)}`}>
                {Math.abs(evaluation.clarity_score - evaluation.average_score) < 0.0001 ? `${Math.round(evaluation.clarity_score * 100)}% clarity` : `${Math.round(evaluation.clarity_score * 100)}%`}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Communication
              </div>
            </div>
          </div>

          {/* Average Score */}
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-sm font-medium text-gray-600 mb-1">
                  Average Score
                </div>
                <div className={`text-3xl font-bold ${getMasteryColor(evaluation.average_score)}`}>
                  {Math.round(evaluation.average_score * 100)}%
                </div>
              </div>
            </div>
          </div>

          {/* Mastery Update Section */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              Mastery Update
            </h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Previous</div>
                <div className={`text-xl font-bold ${getMasteryColor(masteryScore)}`}>
                  {Math.round(masteryScore * 100)}%
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Updated</div>
                <div className={`text-xl font-bold ${getMasteryColor(evaluation.new_mastery_score)}`}>
                  Updated to {Math.round(evaluation.new_mastery_score * 100)}%
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Change</div>
                <div className={`text-xl font-bold ${
                  evaluation.new_mastery_score > masteryScore ? 'text-green-600' : 
                  evaluation.new_mastery_score < masteryScore ? 'text-red-600' : 
                  'text-gray-600'
                }`}>
                  {evaluation.new_mastery_score > masteryScore ? '+' : ''}
                  {Math.round((evaluation.new_mastery_score - masteryScore) * 100)}%
                </div>
              </div>
            </div>

            {/* Mastery Progress Bar */}
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getMasteryBarColor(
                    evaluation.new_mastery_score
                  )}`}
                  style={{ width: `${evaluation.new_mastery_score * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Demonstrated Points */}
          {evaluation.demonstrated_points.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-green-700 mb-3 flex items-center">
                <svg
                  className="h-5 w-5 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                What you explained well:
              </h4>
              <ul className="space-y-2 bg-green-50 rounded-lg p-4">
                {evaluation.demonstrated_points.map((point, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-green-600 mr-2">✓</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Points */}
          {evaluation.missing_points.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-orange-700 mb-3 flex items-center">
                <svg
                  className="h-5 w-5 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                What could be added:
              </h4>
              <ul className="space-y-2 bg-orange-50 rounded-lg p-4">
                {evaluation.missing_points.map((point, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-orange-600 mr-2">⚠</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Misconceptions */}
          {evaluation.misconceptions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-red-700 mb-3 flex items-center">
                <svg
                  className="h-5 w-5 mr-2"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                Misconceptions to address:
              </h4>
              <ul className="space-y-2 bg-red-50 rounded-lg p-4">
                {evaluation.misconceptions.map((misconception, index) => (
                  <li key={index} className="text-sm text-gray-700 flex items-start">
                    <span className="text-red-600 mr-2">✗</span>
                    <span>{misconception}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-gray-200">
            {evaluation.should_continue_tutoring ? (
              <div className="space-y-3">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800 font-medium">
                    <strong>Almost there! Let&apos;s practice more.</strong>
                  </p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Your explanation shows you&apos;re making progress, but we should work through this a bit more to strengthen your understanding.
                  </p>
                </div>
                <button
                  onClick={onContinue}
                  className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all shadow-md hover:shadow-lg"
                >
                  Continue Tutoring
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-sm text-green-800 font-medium">
                    <strong>Great work! You&apos;ve mastered it.</strong>
                  </p>
                  <p className="text-sm text-green-700 mt-1">
                    Your explanation shows solid understanding. Let&apos;s move forward in your learning journey.
                  </p>
                </div>
                <button
                  onClick={onContinue}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-600 hover:to-emerald-600 transition-all shadow-md hover:shadow-lg"
                >
                  Continue Learning
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
