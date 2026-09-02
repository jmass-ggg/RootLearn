import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DiagnosticPanel from '../DiagnosticPanel';
import { DiagnosticQuestion, DiagnosticEvaluation } from '@/types/diagnostic';

/**
 * Helper function to create a test diagnostic question
 */
function createTestQuestion(
  questionId: string = 'q1',
  conceptName: string = 'Test Concept',
  questionType: DiagnosticQuestion['question_type'] = 'short_answer'
): DiagnosticQuestion {
  return {
    question_id: questionId,
    concept_id: 'c1',
    concept_name: conceptName,
    question_text: 'What is a test question?',
    question_type: questionType,
    difficulty: 0.5,
    should_stop: false,
  };
}

/**
 * Helper function to create a test evaluation
 */
function createTestEvaluation(
  correctness: number = 0.8,
  reasoning: number = 0.7
): DiagnosticEvaluation {
  return {
    attempt_id: 'a1',
    correctness_score: correctness,
    reasoning_score: reasoning,
    demonstrated_points: ['Point 1', 'Point 2'],
    missing_points: ['Missing point'],
    misconceptions: ['Misconception 1'],
    should_stop: false,
  };
}

describe('DiagnosticPanel Component', () => {
  describe('Question Display', () => {
    it('should display the current question text', () => {
      const question = createTestQuestion('q1', 'Variables');
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText('What is a test question?')).toBeInTheDocument();
    });

    it('should display the concept being tested', () => {
      const question = createTestQuestion('q1', 'Recursion');
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText(/Testing: Recursion/i)).toBeInTheDocument();
    });

    it('should show loading state when isLoading is true', () => {
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={null}
          evaluation={null}
          isLoading={true}
          onSubmitAnswer={onSubmit}
        />
      );

      // Loading spinner should be present (check for animate-spin class or aria-label)
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show appropriate message when no question is available', () => {
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={null}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText('No diagnostic question available')).toBeInTheDocument();
    });
  });

  describe('Answer Input', () => {
    it('should render textarea for short_answer question type', () => {
      const question = createTestQuestion('q1', 'Test', 'short_answer');
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const textarea = screen.getByLabelText('Your Answer');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('should render textarea for reasoning question type', () => {
      const question = createTestQuestion('q1', 'Test', 'reasoning');
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const textarea = screen.getByLabelText('Your Answer');
      expect(textarea.tagName).toBe('TEXTAREA');
    });

    it('should render larger textarea for code question type', () => {
      const question = createTestQuestion('q1', 'Test', 'code');
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const textarea = screen.getByLabelText('Your Answer') as HTMLTextAreaElement;
      expect(textarea.tagName).toBe('TEXTAREA');
      expect(textarea.rows).toBe(10);
    });

    it('should allow user to type answer', async () => {
      const question = createTestQuestion();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const input = screen.getByLabelText('Your Answer');
      fireEvent.change(input, { target: { value: 'My answer' } });

      expect(input).toHaveValue('My answer');
    });
  });

  describe('Submit Button', () => {
    it('should call onSubmitAnswer when submit button is clicked', async () => {
      const question = createTestQuestion();
      const onSubmit = vi.fn().mockResolvedValue(undefined);

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const input = screen.getByLabelText('Your Answer');
      fireEvent.change(input, { target: { value: 'Test answer' } });

      const submitButton = screen.getByRole('button', { name: /submit answer/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith('Test answer');
      });
    });

    it('should disable submit button when answer is empty', () => {
      const question = createTestQuestion();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const submitButton = screen.getByRole('button', { name: /submit answer/i });
      expect(submitButton).toBeDisabled();
    });

    it('should show loading state while submitting', async () => {
      const question = createTestQuestion();
      const onSubmit = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(
        <DiagnosticPanel
          question={question}
          evaluation={null}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      const input = screen.getByLabelText('Your Answer');
      fireEvent.change(input, { target: { value: 'Test answer' } });

      const submitButton = screen.getByRole('button', { name: /submit answer/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submitting...')).toBeInTheDocument();
      });
    });
  });

  describe('Evaluation Feedback Display', () => {
    it('should display evaluation scores when evaluation is provided', () => {
      const question = createTestQuestion();
      const evaluation = createTestEvaluation(0.85, 0.75);
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should display demonstrated points', () => {
      const question = createTestQuestion();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText(/what you got right/i)).toBeInTheDocument();
      expect(screen.getByText(/Point 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Point 2/i)).toBeInTheDocument();
    });

    it('should display missing points', () => {
      const question = createTestQuestion();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText(/what was missing/i)).toBeInTheDocument();
      expect(screen.getByText(/Missing point/i)).toBeInTheDocument();
    });

    it('should display misconceptions', () => {
      const question = createTestQuestion();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText(/misconceptions detected/i)).toBeInTheDocument();
      expect(screen.getByText(/Misconception 1/i)).toBeInTheDocument();
    });

    it('should hide answer input form when evaluation is shown', () => {
      const question = createTestQuestion();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.queryByLabelText('Your Answer')).not.toBeInTheDocument();
    });

    it('should show completion message when should_stop is true', () => {
      const question = createTestQuestion();
      const evaluation = { ...createTestEvaluation(), should_stop: true };
      const onSubmit = vi.fn();

      render(
        <DiagnosticPanel
          question={question}
          evaluation={evaluation}
          isLoading={false}
          onSubmitAnswer={onSubmit}
        />
      );

      expect(screen.getByText(/diagnostic assessment complete/i)).toBeInTheDocument();
    });
  });
});
