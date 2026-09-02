import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TeachBackPanel from '../TeachBackPanel';
import { TeachBackResponse } from '@/types/teachback';

/**
 * Helper function to create a test concept
 */
function createTestConcept(
  id: string = 'c1',
  name: string = 'Test Concept',
  description: string = 'Test concept description'
) {
  return {
    id,
    name,
    description,
  };
}

/**
 * Helper function to create a test evaluation response
 */
function createTestEvaluation(
  coverage: number = 0.8,
  reasoning: number = 0.75,
  clarity: number = 0.85,
  shouldContinue: boolean = false
): TeachBackResponse {
  return {
    attempt_id: 'attempt1',
    concept_id: 'c1',
    concept_name: 'Test Concept',
    coverage_score: coverage,
    reasoning_score: reasoning,
    clarity_score: clarity,
    average_score: (coverage + reasoning + clarity) / 3,
    demonstrated_points: ['Key point 1', 'Key point 2'],
    missing_points: ['Missing idea 1'],
    misconceptions: ['Misconception 1'],
    should_continue_tutoring: shouldContinue,
    new_mastery_score: 0.75,
    new_confidence_score: 0.80,
  };
}

describe('TeachBackPanel Component', () => {
  describe('Header and Mastery Display', () => {
    it('should display the concept name', () => {
      const concept = createTestConcept('c1', 'Recursion');
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Teach-Back: Recursion/i)).toBeInTheDocument();
    });

    it('should display current mastery score', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText('65%')).toBeInTheDocument();
    });

    it('should display confidence score', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.80}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Confidence: 80%/i)).toBeInTheDocument();
    });

    it('should show loading state when isLoading is true', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={true}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show appropriate message when no concept is active', () => {
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={null}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText('No teach-back session active')).toBeInTheDocument();
    });
  });

  describe('Explanation Input Form', () => {
    it('should display the instruction message', () => {
      const concept = createTestConcept('c1', 'Recursion');
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Time to teach back!/i)).toBeInTheDocument();
      expect(screen.getByText(/Explain Recursion in your own words/i)).toBeInTheDocument();
    });

    it('should render a large textarea for explanation', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const textarea = screen.getByLabelText('Your Explanation') as HTMLTextAreaElement;
      expect(textarea.tagName).toBe('TEXTAREA');
      expect(textarea.rows).toBe(12);
    });

    it('should allow user to type explanation', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const textarea = screen.getByLabelText('Your Explanation');
      fireEvent.change(textarea, {
        target: { value: 'This is my detailed explanation of the concept.' },
      });

      expect(textarea).toHaveValue('This is my detailed explanation of the concept.');
    });

    it('should disable submit button when explanation is too short', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const textarea = screen.getByLabelText('Your Explanation');
      fireEvent.change(textarea, { target: { value: 'Too short' } });

      const submitButton = screen.getByRole('button', { name: /submit my explanation/i });
      expect(submitButton).toBeDisabled();
    });

    it('should call onSubmitExplanation when form is submitted', async () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn().mockResolvedValue(evaluation);
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const textarea = screen.getByLabelText('Your Explanation');
      const explanation = 'This is a detailed explanation of the concept with sufficient length.';
      fireEvent.change(textarea, { target: { value: explanation } });

      const submitButton = screen.getByRole('button', { name: /submit my explanation/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(explanation);
      });
    });

    it('should show loading state while submitting', async () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn().mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const textarea = screen.getByLabelText('Your Explanation');
      fireEvent.change(textarea, {
        target: { value: 'This is a detailed explanation with sufficient length.' },
      });

      const submitButton = screen.getByRole('button', { name: /submit my explanation/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/evaluating your explanation/i)).toBeInTheDocument();
      });
    });
  });

  describe('Evaluation Results Display', () => {
    it('should display all three evaluation scores', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.85, 0.75, 0.90);
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText('Coverage')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('Reasoning')).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('Clarity')).toBeInTheDocument();
      expect(screen.getByText('90%')).toBeInTheDocument();
    });

    it('should display average score', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.80, 0.80, 0.80);
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText('Average Score')).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument();
    });

    it('should display demonstrated points', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/What you explained well/i)).toBeInTheDocument();
      expect(screen.getByText(/Key point 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Key point 2/i)).toBeInTheDocument();
    });

    it('should display missing points', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/What could be added/i)).toBeInTheDocument();
      expect(screen.getByText(/Missing idea 1/i)).toBeInTheDocument();
    });

    it('should display misconceptions', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Misconceptions to address/i)).toBeInTheDocument();
      expect(screen.getByText(/Misconception 1/i)).toBeInTheDocument();
    });

    it('should display mastery update section', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Mastery Update/i)).toBeInTheDocument();
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Updated')).toBeInTheDocument();
      expect(screen.getByText('Change')).toBeInTheDocument();
    });

    it('should show positive feedback when mastery improves', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.80, 0.80, 0.80, false);
      evaluation.new_mastery_score = 0.80;
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Great work! You've mastered it/i)).toBeInTheDocument();
    });

    it('should show encouragement when should_continue_tutoring is true', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.60, 0.60, 0.60, true);
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByText(/Almost there! Let's practice more/i)).toBeInTheDocument();
    });

    it('should hide explanation form when evaluation is shown', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.queryByLabelText('Your Explanation')).not.toBeInTheDocument();
    });
  });

  describe('Continue Button', () => {
    it('should show continue button after evaluation', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const continueButton = screen.getByRole('button', { name: /continue/i });
      expect(continueButton).toBeInTheDocument();
    });

    it('should call onContinue when continue button is clicked', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      const continueButton = screen.getByRole('button', { name: /continue/i });
      fireEvent.click(continueButton);

      expect(onContinue).toHaveBeenCalledTimes(1);
    });

    it('should show "Continue Tutoring" when should_continue_tutoring is true', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.60, 0.60, 0.60, true);
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByRole('button', { name: /continue tutoring/i })).toBeInTheDocument();
    });

    it('should show "Continue Learning" when mastery is sufficient', () => {
      const concept = createTestConcept();
      const evaluation = createTestEvaluation(0.80, 0.80, 0.80, false);
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={evaluation}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.getByRole('button', { name: /continue learning/i })).toBeInTheDocument();
    });

    it('should not show continue button before evaluation', () => {
      const concept = createTestConcept();
      const onSubmit = vi.fn();
      const onContinue = vi.fn();

      render(
        <TeachBackPanel
          currentConcept={concept}
          masteryScore={0.65}
          confidenceScore={0.70}
          evaluation={null}
          isLoading={false}
          onSubmitExplanation={onSubmit}
          onContinue={onContinue}
        />
      );

      expect(screen.queryByRole('button', { name: /continue/i })).not.toBeInTheDocument();
    });
  });
});
