/**
 * Types for root gap detection
 */

export interface GapExplanation {
  concept_id: string;
  concept_name: string;
  mastery: number;
  confidence: number;
  gap_score: number;
  reasons: string[];
}

export interface RootGapResult {
  session_id: string;
  root_gap: GapExplanation;
  message: string;
}
