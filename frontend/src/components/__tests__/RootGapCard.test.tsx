import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RootGapCard from '../RootGapCard';
import { RootGapResult } from '@/types/root-gap';

/**
 * Helper function to create a test root gap result
 */
function createTestRootGap(
  conceptName: string = 'Test Concept',
  mastery: number = 0.3,
  confidence: number = 0.8,
  gapScore: number = 0.56
): RootGapResult {
  return {
    session_id: 'session-1',
    root_gap: {
      concept_id: 'c1',
      concept_name: conceptName,
      mastery,
      confidence,
      gap_score: gapScore,
      reasons: [
        'Low diagnostic performance',
        'High confidence in assessment',
        'Direct prerequisite of target',
        'Blocks downstream concepts',
      ],
    },
    message: 'Root gap identified successfully',
  };
}

describe('RootGapCard Component', () => {
  describe('Display Root Gap Information', () => {
    it('should display the identified root gap concept name', () => {
      const rootGap = createTestRootGap('Call Stack');
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('Call Stack')).toBeInTheDocument();
    });

    it('should display mastery score as percentage', () => {
      const rootGap = createTestRootGap('Recursion', 0.31);
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('31%')).toBeInTheDocument();
    });

    it('should display confidence score as percentage', () => {
      const rootGap = createTestRootGap('Functions', 0.4, 0.85);
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should display gap score with two decimal places', () => {
      const rootGap = createTestRootGap('Variables', 0.3, 0.8, 0.612);
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('0.61')).toBeInTheDocument();
    });

    it('should show loading state when isLoading is true', () => {
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={null} isLoading={true} onFixGap={onFixGap} />);

      // Loading spinner should be present
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show appropriate message when no root gap is available', () => {
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={null} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('No root gap identified yet')).toBeInTheDocument();
    });
  });

  describe('Explanation Reasons', () => {
    it('should display all explanation reasons', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText(/Low diagnostic performance/i)).toBeInTheDocument();
      expect(screen.getByText(/High confidence in assessment/i)).toBeInTheDocument();
      expect(screen.getByText(/Direct prerequisite of target/i)).toBeInTheDocument();
      expect(screen.getByText(/Blocks downstream concepts/i)).toBeInTheDocument();
    });

    it('should display explanation section header', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText(/Why this gap matters:/i)).toBeInTheDocument();
    });

    it('should render custom reasons when provided', () => {
      const customRootGap: RootGapResult = {
        session_id: 'session-1',
        root_gap: {
          concept_id: 'c1',
          concept_name: 'Custom Concept',
          mastery: 0.2,
          confidence: 0.9,
          gap_score: 0.7,
          reasons: ['Custom reason 1', 'Custom reason 2'],
        },
        message: 'Custom message',
      };
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={customRootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('Custom reason 1')).toBeInTheDocument();
      expect(screen.getByText('Custom reason 2')).toBeInTheDocument();
    });
  });

  describe('Fix This Gap Button', () => {
    it('should render the "Fix This Gap" button', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      const button = screen.getByRole('button', { name: /fix this gap/i });
      expect(button).toBeInTheDocument();
    });

    it('should call onFixGap when button is clicked', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      const button = screen.getByRole('button', { name: /fix this gap/i });
      fireEvent.click(button);

      expect(onFixGap).toHaveBeenCalledTimes(1);
    });
  });

  describe('UI States and Styling', () => {
    it('should display "Root Gap Identified" header', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('Root Gap Identified')).toBeInTheDocument();
    });

    it('should display descriptive message from root gap result', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('Root gap identified successfully')).toBeInTheDocument();
    });

    it('should display helper text about Socratic guidance', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText(/work through this concept together using Socratic guidance/i)).toBeInTheDocument();
    });

    it('should display blocking message', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText(/This is blocking your understanding/i)).toBeInTheDocument();
    });
  });

  describe('Metrics Display', () => {
    it('should display all three metric labels', () => {
      const rootGap = createTestRootGap();
      const onFixGap = vi.fn();

      render(<RootGapCard rootGap={rootGap} isLoading={false} onFixGap={onFixGap} />);

      expect(screen.getByText('Mastery')).toBeInTheDocument();
      expect(screen.getByText('Confidence')).toBeInTheDocument();
      expect(screen.getByText('Gap Score')).toBeInTheDocument();
    });

    it('should handle edge case mastery values correctly', () => {
      // Test with 0% mastery
      const rootGap1 = createTestRootGap('Test', 0.0);
      const onFixGap = vi.fn();

      const { unmount } = render(<RootGapCard rootGap={rootGap1} isLoading={false} onFixGap={onFixGap} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
      unmount();

      // Test with 100% mastery (edge case)
      const rootGap2 = createTestRootGap('Test', 1.0);
      render(<RootGapCard rootGap={rootGap2} isLoading={false} onFixGap={onFixGap} />);
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });
});
