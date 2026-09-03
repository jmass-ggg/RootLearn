import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import DiagnosticAssessmentCard from '../DiagnosticAssessmentCard';
import type { DiagnosticQuestion } from '@/types/diagnostic';

const question: DiagnosticQuestion = {
  question_id: 'question-1',
  concept_id: 'concept-1',
  concept_name: 'Conditionals',
  question_text: 'How does an if-else statement work?',
  question_type: 'reasoning',
  difficulty: 0.5,
  should_stop: false,
};

describe('DiagnosticAssessmentCard', () => {
  it('shows the current concept mastery in the redesigned assessment panel', () => {
    render(
      <DiagnosticAssessmentCard
        question={question}
        evaluation={null}
        isLoading={false}
        masteryScore={0.62}
        onSubmitAnswer={vi.fn()}
      />
    );

    expect(screen.getByText('Conditionals mastery')).toBeInTheDocument();
    expect(screen.getByText('62%')).toBeInTheDocument();
    expect(screen.getByLabelText('Difficulty: Adaptive')).toBeInTheDocument();
  });

  it('allows an unsure answer to be submitted without typed text', async () => {
    const onSubmitAnswer = vi.fn().mockResolvedValue(undefined);
    render(
      <DiagnosticAssessmentCard
        question={question}
        evaluation={null}
        isLoading={false}
        onSubmitAnswer={onSubmitAnswer}
      />
    );

    fireEvent.click(screen.getByLabelText("I'm unsure about this one"));
    fireEvent.click(screen.getByRole('button', { name: 'Submit answer' }));

    await waitFor(() => {
      expect(onSubmitAnswer).toHaveBeenCalledWith('I am unsure about this question.');
    });
  });
});
