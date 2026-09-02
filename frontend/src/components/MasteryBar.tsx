/**
 * MasteryBar component
 * Visual progress bar showing mastery score (0-100%)
 * Color-coded by mastery band and includes confidence indicator
 * 
 * Requirements: 6.8, 6.9
 */

import React from 'react';
import { MasteryStatus } from '@/types';

export interface MasteryBarProps {
  masteryScore: number;
  confidenceScore: number;
  status: MasteryStatus;
  showLabel?: boolean;
  className?: string;
}

/**
 * Get color classes based on mastery status
 * Bands: weak (0-0.39), learning (0.40-0.69), understood (0.70-0.84), mastered (0.85-1.00)
 */
function getStatusColor(status: MasteryStatus): string {
  switch (status) {
    case 'weak':
      return 'bg-red-500';
    case 'learning':
      return 'bg-yellow-500';
    case 'understood':
      return 'bg-green-400';
    case 'mastered':
      return 'bg-green-600';
    case 'locked':
      return 'bg-gray-400';
    case 'unknown':
    default:
      return 'bg-gray-300';
  }
}

/**
 * Get confidence indicator color
 */
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.80) return 'text-green-600';
  if (confidence >= 0.60) return 'text-yellow-600';
  if (confidence >= 0.35) return 'text-orange-600';
  return 'text-red-600';
}

export function MasteryBar({
  masteryScore,
  confidenceScore,
  status,
  showLabel = true,
  className = '',
}: MasteryBarProps) {
  const percentage = Math.round(masteryScore * 100);
  const confidencePercentage = Math.round(confidenceScore * 100);
  const statusColor = getStatusColor(status);
  const confidenceColor = getConfidenceColor(confidenceScore);

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Mastery score and status label */}
      {showLabel && (
        <div className="flex justify-between items-center text-sm">
          <span className="font-medium text-gray-700">
            Mastery: {percentage}%
          </span>
          <span className="capitalize text-gray-600">
            {status}
          </span>
        </div>
      )}

      {/* Progress bar */}
      <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full ${statusColor} transition-all duration-300 ease-in-out`}
          style={{ width: `${percentage}%` }}
          aria-label={`${percentage}% mastery`}
        />
      </div>

      {/* Confidence indicator */}
      <div className="flex justify-between items-center text-xs">
        <span className="text-gray-500">
          Confidence:
        </span>
        <span className={`font-medium ${confidenceColor}`}>
          {confidencePercentage}%
        </span>
      </div>
    </div>
  );
}
