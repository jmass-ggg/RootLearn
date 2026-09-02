/**
 * Types for diagnostic assessment
 */

export interface DiagnosticQuestion {
  question_id: string;
  concept_id: string;
  concept_name: string;
  question_text: string;
  question_type: 'short_answer' | 'multiple_choice' | 'reasoning' | 'code';
  difficulty: number;
  should_stop: boolean;
}

export interface DiagnosticEvaluation {
  attempt_id: string;
  correctness_score: number;
  reasoning_score: number;
  demonstrated_points: string[];
  missing_points: string[];
  misconceptions: string[];
  should_stop: boolean;
}

export interface DiagnosisStartRequest {
  user_id: string;
}

export interface DiagnosisAnswerRequest {
  user_id: string;
  question_id: string;
  answer: string;
}
