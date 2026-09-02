/**
 * Type definitions for Socratic tutoring
 */

export interface TutorMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  hint_level: number | null;
  created_at: string;
}

export interface TutorMessageRequest {
  user_id: string;
  message: string;
}

export interface TutorMessageResponse {
  message_id: string;
  concept_id: string;
  concept_name: string;
  response: string;
  hint_level: number;
  mastery_score: number;
  confidence_score: number;
}

export interface TutorMessagesResponse {
  session_id: string;
  concept_id: string;
  concept_name: string;
  messages: TutorMessage[];
}
