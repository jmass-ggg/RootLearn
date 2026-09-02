'use client';

import { RootGapResult } from '@/types/root-gap';

interface RootGapCardProps {
  rootGap: RootGapResult | null;
  isLoading: boolean;
  onFixGap: () => void;
}

/**
 * RootGapCard component
 * Displays identified root gap concept with explanation and action button
 */
export default function RootGapCard({
  rootGap,
  isLoading,
  onFixGap,
}: RootGapCardProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!rootGap) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-32 text-gray-500">
          <p>No root gap identified yet</p>
        </div>
      </div>
    );
  }

  const { root_gap: gap, message } = rootGap;

  const getMasteryColor = (score: number): string => {
    if (score >= 0.85) return 'text-green-600';
    if (score >= 0.70) return 'text-lime-600';
    if (score >= 0.40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMasteryBgColor = (score: number): string => {
    if (score >= 0.85) return 'bg-green-100 border-green-300';
    if (score >= 0.70) return 'bg-lime-100 border-lime-300';
    if (score >= 0.40) return 'bg-yellow-100 border-yellow-300';
    return 'bg-red-100 border-red-300';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.80) return 'text-blue-600';
    if (confidence >= 0.60) return 'text-indigo-600';
    return 'text-purple-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border-2 border-orange-300">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center mb-2">
          <div className="w-3 h-3 bg-orange-500 rounded-full mr-2 animate-pulse"></div>
          <h3 className="text-lg font-semibold text-gray-900">
            Root Gap Identified
          </h3>
        </div>
        <p className="text-sm text-gray-600">{message}</p>
      </div>

      {/* Concept Name */}
      <div className="mb-6">
        <div className="text-2xl font-bold text-gray-900 mb-2">
          {gap.concept_name}
        </div>
        <div className="text-sm text-gray-500">
          This is blocking your understanding
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Mastery */}
        <div className={`p-3 rounded-lg border ${getMasteryBgColor(gap.mastery)}`}>
          <div className="text-xs font-medium text-gray-600 mb-1">
            Mastery
          </div>
          <div className={`text-xl font-bold ${getMasteryColor(gap.mastery)}`}>
            {Math.round(gap.mastery * 100)}%
          </div>
        </div>

        {/* Confidence */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs font-medium text-gray-600 mb-1">
            Confidence
          </div>
          <div className={`text-xl font-bold ${getConfidenceColor(gap.confidence)}`}>
            {Math.round(gap.confidence * 100)}%
          </div>
        </div>

        {/* Gap Score */}
        <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="text-xs font-medium text-gray-600 mb-1">
            Gap Score
          </div>
          <div className="text-xl font-bold text-orange-600">
            {gap.gap_score.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Explanation Reasons */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          Why this gap matters:
        </h4>
        <ul className="space-y-2">
          {gap.reasons.map((reason, index) => (
            <li
              key={index}
              className="flex items-start text-sm text-gray-700"
            >
              <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Action Button */}
      <button
        onClick={onFixGap}
        className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-orange-600 hover:to-red-600 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
      >
        Fix This Gap
      </button>

      {/* Helper Text */}
      <p className="text-xs text-center text-gray-500 mt-3">
        Let&apos;s work through this concept together using Socratic guidance
      </p>
    </div>
  );
}
