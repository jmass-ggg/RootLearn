/**
 * Type definitions for knowledge graph
 */

export type MasteryStatus = 'weak' | 'learning' | 'understood' | 'mastered' | 'locked' | 'unknown';

export interface Concept {
  id: string;
  slug: string;
  name: string;
  description: string;
  is_target: boolean;
  mastery_score: number;
  confidence_score: number;
  status: MasteryStatus;
  created_at: string;
  updated_at: string;
}

export interface ConceptEdge {
  id: string;
  source_concept_id: string;
  target_concept_id: string;
  importance_weight: number;
  created_at: string;
}

export interface PrerequisiteGraph {
  concepts: Concept[];
  edges: ConceptEdge[];
  root_gap_id?: string | null;
}
