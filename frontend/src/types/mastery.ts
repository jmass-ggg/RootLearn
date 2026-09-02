/**
 * Mastery event types
 * Requirements: 7.1, 7.2, 7.4
 */

export type MasterySourceType = 'diagnostic' | 'tutoring' | 'teachback' | 'manual';

export interface MasteryEvent {
  id: string;
  concept_id: string;
  source_type: MasterySourceType;
  old_score: number;
  new_score: number;
  old_confidence: number;
  new_confidence: number;
  reason: Record<string, any>;
  created_at: string;
}

export interface MasteryHistoryProps {
  events: MasteryEvent[];
  conceptNames?: Record<string, string>; // Map concept_id to concept name
  className?: string;
}
