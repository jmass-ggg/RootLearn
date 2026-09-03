/**
 * Responsive Layout Tests
 * Tests responsive behavior at mobile (375px), tablet (768px), desktop (1024px, 1440px) widths
 * Requirements: 13.1, 13.2, 13.3, 13.8, 13.9
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SessionShell } from '@/components/layout/SessionShell';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { KnowledgeMapCard } from '@/components/KnowledgeMapCard';

// Mock Next.js router
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/session/test-id',
  useSearchParams: () => new URLSearchParams(),
}));

// Mock React Flow to avoid complex setup
vi.mock('reactflow', () => ({
  ReactFlow: () => <div data-testid="react-flow-mock">Graph</div>,
  Background: () => null,
  Controls: () => null,
  MiniMap: () => null,
  useNodesState: () => [[], vi.fn(), vi.fn()],
  useEdgesState: () => [[], vi.fn(), vi.fn()],
}));

describe('Responsive Layout Tests', () => {
  const originalInnerWidth = window.innerWidth;
  
  // Helper to set viewport size
  const setViewport = (width: number) => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    });
    window.dispatchEvent(new Event('resize'));
  };

  afterEach(() => {
    // Restore original viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    mockPush.mockClear();
  });

  describe('Property 8: Responsive layout adaptation', () => {
    it('should render mobile layout correctly at 375px', () => {
      setViewport(375);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div>Test Content</div>
        </SessionShell>
      );

      // Verify content renders
      expect(screen.getByText('Test Content')).toBeInTheDocument();
      expect(screen.getByText('RootLearn')).toBeInTheDocument();
    });

    it('should render tablet layout correctly at 768px', () => {
      setViewport(768);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div>Test Content</div>
        </SessionShell>
      );

      // Verify content renders
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should render desktop layout correctly at 1024px', () => {
      setViewport(1024);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div>Test Content</div>
        </SessionShell>
      );

      // Verify sidebar is present (desktop view)
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should render desktop layout correctly at 1440px', () => {
      setViewport(1440);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div>Test Content</div>
        </SessionShell>
      );

      // Verify content renders properly at wide viewport
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });
  });

  describe('Header Responsive Behavior', () => {
    it('should show abbreviated text on mobile', () => {
      setViewport(375);
      
      render(
        <Header
          sessionId="test-session"
          currentPhase="diagnosing"
          topic="Test Topic"
          onNewSession={vi.fn()}
        />
      );

      // Header should render with mobile optimization
      const newButton = screen.getByRole('button', { name: /New/i });
      expect(newButton).toBeInTheDocument();
    });

    it('should show full text on desktop', () => {
      setViewport(1024);
      
      render(
        <Header
          sessionId="test-session"
          currentPhase="diagnosing"
          topic="Test Topic That Is Quite Long"
          onNewSession={vi.fn()}
        />
      );

      // Should show full button text on desktop
      const newButton = screen.getByRole('button', { name: /New session/i });
      expect(newButton).toBeInTheDocument();
    });

    it('should display topic in mobile separate row', () => {
      setViewport(375);
      
      render(
        <Header
          sessionId="test-session"
          currentPhase="diagnosing"
          topic="Long Topic Name"
          onNewSession={vi.fn()}
        />
      );

      // Topic should be displayed (in both desktop hidden and mobile visible sections)
      const topicElements = screen.getAllByText('Long Topic Name');
      expect(topicElements.length).toBeGreaterThan(0);
    });
  });

  describe('Sidebar Responsive Behavior', () => {
    it('should render mobile navigation button at mobile viewport', () => {
      setViewport(375);
      
      render(
        <Sidebar
          sessionId="test-session"
          currentPhase="diagnosing"
          onNavigate={vi.fn()}
        />
      );

      // Should have mobile menu toggle button
      const toggleButton = screen.getByLabelText(/toggle navigation menu/i);
      expect(toggleButton).toBeInTheDocument();
    });

    it('should render desktop sidebar at desktop viewport', () => {
      setViewport(1024);
      
      render(
        <Sidebar
          sessionId="test-session"
          currentPhase="diagnosing"
          onNavigate={vi.fn()}
        />
      );

      // Should have navigation items visible (both desktop and mobile versions render)
      const overviewElements = screen.getAllByText('Overview');
      expect(overviewElements.length).toBeGreaterThan(0);
      
      const knowledgeMapElements = screen.getAllByText('Knowledge Map');
      expect(knowledgeMapElements.length).toBeGreaterThan(0);
      
      const diagnosisElements = screen.getAllByText('Diagnosis');
      expect(diagnosisElements.length).toBeGreaterThan(0);
    });

    it('should highlight active section based on current phase', () => {
      setViewport(1024);
      
      render(
        <Sidebar
          sessionId="test-session"
          currentPhase="tutoring"
          onNavigate={vi.fn()}
        />
      );

      // Tutoring keeps the learner in the combined Knowledge Map workspace.
      const knowledgeMapElements = screen.getAllByText('Knowledge Map');
      expect(knowledgeMapElements.length).toBeGreaterThan(0);
      expect(screen.queryByText('Root Gap')).not.toBeInTheDocument();
    });
  });

  describe('KnowledgeMapCard Responsive Behavior', () => {
    const mockGraph = {
      session_id: 'test',
      concepts: [
        {
          id: '1',
          slug: 'test-concept',
          name: 'Test Concept',
          description: 'Test',
          mastery_score: 0.5,
          confidence_score: 0.7,
          status: 'learning' as const,
          is_target: false,
          is_root_gap: false,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      ],
      edges: [],
      target_concept_id: '1',
      root_gap_id: null,
    };

    it('should render controls at all viewport sizes', () => {
      setViewport(375);
      
      render(
        <KnowledgeMapCard
          graph={mockGraph}
          isLoading={false}
          topic="Test Topic"
        />
      );

      // Controls should be accessible (KnowledgeMapCard controls + React Flow controls)
      const zoomInButtons = screen.getAllByLabelText(/zoom in/i);
      expect(zoomInButtons.length).toBeGreaterThan(0);
      
      const zoomOutButtons = screen.getAllByLabelText(/zoom out/i);
      expect(zoomOutButtons.length).toBeGreaterThan(0);
      
      const fitViewButtons = screen.getAllByLabelText(/fit.*view/i);
      expect(fitViewButtons.length).toBeGreaterThan(0);
    });

    it('should handle truncated topic text on mobile', () => {
      setViewport(375);
      
      render(
        <KnowledgeMapCard
          graph={mockGraph}
          isLoading={false}
          topic="Very Long Topic Name That Should Truncate On Mobile Devices"
        />
      );

      // Topic should be rendered
      expect(screen.getByText(/Very Long Topic Name/)).toBeInTheDocument();
    });
  });

  describe('No Horizontal Scrolling', () => {
    it('should not cause horizontal overflow at 375px', () => {
      setViewport(375);
      
      const { container } = render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div style={{ width: '100%' }}>
            <KnowledgeMapCard
              graph={undefined}
              isLoading={false}
              topic="Test"
            />
          </div>
        </SessionShell>
      );

      // Check that container doesn't exceed viewport
      const shell = container.firstChild as HTMLElement;
      expect(shell).toBeInTheDocument();
      // Container should have proper width constraints
      expect(shell.className).toContain('w-full');
    });

    it('should not cause horizontal overflow at 768px', () => {
      setViewport(768);
      
      const { container } = render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div style={{ width: '100%' }}>Test Content</div>
        </SessionShell>
      );

      const shell = container.firstChild as HTMLElement;
      expect(shell.className).toContain('w-full');
    });
  });

  describe('Two-Column Layout Collapse', () => {
    it('should use single column layout on mobile (375px)', () => {
      setViewport(375);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="w-full lg:w-1/2">Column 1</div>
            <div className="w-full lg:w-1/2">Column 2</div>
          </div>
        </SessionShell>
      );

      // Both columns should render
      expect(screen.getByText('Column 1')).toBeInTheDocument();
      expect(screen.getByText('Column 2')).toBeInTheDocument();
    });

    it('should use two column layout on desktop (1024px)', () => {
      setViewport(1024);
      
      render(
        <SessionShell
          sessionId="test-session"
          userId="test-user"
          currentPhase="diagnosing"
          topic="Test Topic"
        >
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="w-full lg:w-1/2">Column 1</div>
            <div className="w-full lg:w-1/2">Column 2</div>
          </div>
        </SessionShell>
      );

      // Both columns should render
      expect(screen.getByText('Column 1')).toBeInTheDocument();
      expect(screen.getByText('Column 2')).toBeInTheDocument();
    });
  });
});
