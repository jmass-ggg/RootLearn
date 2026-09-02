/**
 * Type definitions for teach-back evaluation
 */

export interface TeachBackRequest {
  user_id: string;
  concept_id: string;
  explanation: string;
}

export interface TeachBackResponse {
  attempt_id: string;
  concept_id: string;
  concept_name: string;
  coverage_score: number;
  reasoning_score: number;
  clarity_score: number;
  average_score: number;
  demonstrated_points: string[];
  missing_points: string[];
  misconceptions: string[];
  should_continue_tutoring: boolean;
  new_mastery_score: number;
  new_confidence_score: number;
}
