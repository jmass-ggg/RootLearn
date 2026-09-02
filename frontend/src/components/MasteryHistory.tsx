/**
 * MasteryHistory component
 * Display mastery events timeline showing before/after scores and reasons
 * 
 * Requirements: 7.1, 7.2, 7.4
 */

import React from 'react';
import { MasteryEvent, MasterySourceType } from '@/types';

export interface MasteryHistoryProps {
  events: MasteryEvent[];
  conceptNames?: Record<string, string>; // Map concept_id to concept name
  className?: string;
}

/**
 * Get color for source type badge
 */
function getSourceColor(sourceType: MasterySourceType): string {
  switch (sourceType) {
    case 'diagnostic':
      return 'bg-blue-100 text-blue-800';
    case 'tutoring':
      return 'bg-purple-100 text-purple-800';
    case 'teachback':
      return 'bg-green-100 text-green-800';
    case 'manual':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Get color for score change
 */
function getChangeColor(change: number): string {
  if (change > 0) return 'text-green-600';
  if (change < 0) return 'text-red-600';
  return 'text-gray-600';
}

/**
 * Format score as percentage
 */
function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Extract reason text from reason JSON
 */
function formatReason(reasonJson: Record<string, any>): string {
  if (typeof reasonJson === 'string') {
    return reasonJson;
  }
  
  // Try common fields
  if (reasonJson.description) {
    return reasonJson.description;
  }
  if (reasonJson.message) {
    return reasonJson.message;
  }
  if (reasonJson.reason) {
    return reasonJson.reason;
  }
  
  // Fallback to JSON stringify (pretty format)
  try {
    return JSON.stringify(reasonJson, null, 2);
  } catch {
    return 'Reason details unavailable';
  }
}

export function MasteryHistory({
  events,
  conceptNames = {},
  className = '',
}: MasteryHistoryProps) {
  if (events.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        No mastery events yet. Complete diagnostic questions, tutoring, or teach-back to track progress.
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900">Mastery History</h3>
      
      {/* Timeline */}
      <div className="space-y-4">
        {events.map((event, index) => {
          const masteryChange = event.new_score - event.old_score;
          const confidenceChange = event.new_confidence - event.old_confidence;
          const conceptName = conceptNames[event.concept_id] || event.concept_id;
          
          return (
            <div
              key={event.id}
              className="relative pl-8 pb-4 border-l-2 border-gray-300 last:border-l-0"
            >
              {/* Timeline dot */}
              <div className="absolute left-0 top-0 -translate-x-1/2 w-4 h-4 rounded-full bg-blue-500 border-2 border-white" />
              
              <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                {/* Header with source type and timestamp */}
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getSourceColor(
                        event.source_type
                      )}`}
                    >
                      {event.source_type}
                    </span>
                    <span className="text-sm text-gray-600 font-medium">
                      {conceptName}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(event.created_at)}
                  </span>
                </div>
                
                {/* Score changes */}
                <div className="grid grid-cols-2 gap-4 mb-3">
                  {/* Mastery change */}
                  <div className="space-y-1">
                    <div className="text-xs text-gray-500 uppercase">Mastery</div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-700">
                        {formatScore(event.old_score)}
                      </span>
                      <span className="text-gray-400">→</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatScore(event.new_score)}
                      </span>
                      <span
                        className={`text-xs font-medium ${getChangeColor(masteryChange)}`}
                      >
                        {masteryChange > 0 ? '+' : ''}
                        {formatScore(masteryChange)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Confidence change */}
                  <div className="space-y-1">
                    <div className="text-xs text-gray-500 uppercase">Confidence</div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-700">
                        {formatScore(event.old_confidence)}
                      </span>
                      <span className="text-gray-400">→</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {formatScore(event.new_confidence)}
                      </span>
                      <span
                        className={`text-xs font-medium ${getChangeColor(
                          confidenceChange
                        )}`}
                      >
                        {confidenceChange > 0 ? '+' : ''}
                        {formatScore(confidenceChange)}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Reason */}
                <div className="pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-500 uppercase mb-1">Reason</div>
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {formatReason(event.reason)}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
