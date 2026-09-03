import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MasteryHistory } from '../MasteryHistory';
import type { MasteryEvent } from '@/types';

describe('MasteryHistory', () => {
  it('turns diagnostic evidence into learner-friendly text without exposing raw API fields', () => {
    const event: MasteryEvent = {
      id: 'event-1',
      concept_id: 'iteration',
      source_type: 'diagnostic',
      old_score: 0,
      new_score: 1,
      old_confidence: 0.1,
      new_confidence: 0.35,
      reason: {
        attempt_id: 'internal-attempt-id',
        question_id: 'internal-question-id',
        demonstrated_points: ['Explained how iteration repeats instructions.'],
        missing_points: ['Compare a while loop with a for loop.'],
        misconceptions: [],
      },
      created_at: '2026-09-03T08:56:00.000Z',
    };

    render(<MasteryHistory events={[event]} conceptNames={{ iteration: 'Iteration' }} />);

    expect(screen.getByText(/Demonstrated: Explained how iteration repeats instructions/)).toBeInTheDocument();
    expect(screen.getByText(/Still to strengthen: Compare a while loop with a for loop/)).toBeInTheDocument();
    expect(screen.queryByText(/attempt_id/)).not.toBeInTheDocument();
    expect(screen.queryByText(/internal-attempt-id/)).not.toBeInTheDocument();
  });
});
