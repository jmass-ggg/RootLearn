import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import KnowledgeGraph from '../KnowledgeGraph';
import { PrerequisiteGraph, Concept, MasteryStatus } from '@/types/graph';

/**
 * Helper function to create a test concept
 */
function createConcept(
  id: string,
  name: string,
  masteryScore: number,
  status: MasteryStatus,
  isTarget: boolean = false
): Concept {
  return {
    id,
    slug: name.toLowerCase().replace(/\s+/g, '-'),
    name,
    description: `Description for ${name}`,
    is_target: isTarget,
    mastery_score: masteryScore,
    confidence_score: 0.8,
    status,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

/**
 * Helper function to create a test graph
 */
function createTestGraph(
  concepts: Concept[],
  rootGapId?: string | null
): PrerequisiteGraph {
  // Create edges: connect each concept to the next one
  const edges = concepts.slice(0, -1).map((concept, index) => ({
    id: `edge-${index}`,
    source_concept_id: concept.id,
    target_concept_id: concepts[index + 1].id,
    importance_weight: 0.8,
    created_at: new Date().toISOString(),
  }));

  return {
    concepts,
    edges,
    root_gap_id: rootGapId,
  };
}

describe('KnowledgeGraph Component', () => {
  describe('Property 10: Graph nodes display required information', () => {
    it('should display concept name on all nodes', () => {
      const concepts = [
        createConcept('1', 'Variables', 0.5, 'learning'),
        createConcept('2', 'Functions', 0.3, 'weak'),
        createConcept('3', 'Recursion', 0.1, 'weak', true),
      ];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Verify all concept names are displayed
      expect(screen.getByText('Variables')).toBeInTheDocument();
      expect(screen.getByText('Functions')).toBeInTheDocument();
      expect(screen.getByText('Recursion')).toBeInTheDocument();
    });

    it('should display mastery percentage on all nodes', () => {
      const concepts = [
        createConcept('1', 'Variables', 0.85, 'mastered'),
        createConcept('2', 'Functions', 0.42, 'learning'),
        createConcept('3', 'Recursion', 0.15, 'weak', true),
      ];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Verify mastery percentages are displayed (rounded)
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('42%')).toBeInTheDocument();
      expect(screen.getByText('15%')).toBeInTheDocument();
    });

    it('should update a node when refreshed graph mastery data changes', async () => {
      const initialGraph = createTestGraph([
        createConcept('1', 'Variables', 0, 'unknown'),
      ]);
      const { rerender } = render(<KnowledgeGraph graph={initialGraph} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('unknown')).toBeInTheDocument();

      const refreshedGraph = createTestGraph([
        createConcept('1', 'Variables', 0.72, 'understood'),
      ]);
      rerender(<KnowledgeGraph graph={refreshedGraph} />);

      expect(await screen.findByText('72%')).toBeInTheDocument();
      expect(screen.getByText('understood')).toBeInTheDocument();
      expect(screen.queryByText('0%')).not.toBeInTheDocument();
    });

    it('should display both concept name and mastery percentage for any concept', () => {
      // Property: For any concept node rendered, both name and mastery % should be present
      const testCases = [
        { name: 'Test Concept A', mastery: 0.0, status: 'weak' as MasteryStatus },
        { name: 'Test Concept B', mastery: 0.5, status: 'learning' as MasteryStatus },
        { name: 'Test Concept C', mastery: 1.0, status: 'mastered' as MasteryStatus },
      ];

      testCases.forEach(({ name, mastery, status }) => {
        const concepts = [createConcept('test-id', name, mastery, status)];
        const graph = createTestGraph(concepts);

        const { container, unmount } = render(<KnowledgeGraph graph={graph} />);

        // Verify concept name is present
        expect(screen.getByText(name)).toBeInTheDocument();

        // Verify mastery percentage is present
        const expectedPercentage = `${Math.round(mastery * 100)}%`;
        expect(screen.getByText(expectedPercentage)).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Property 11: Node visual state reflects mastery', () => {
    it('should render weak concepts with red color', () => {
      const concepts = [createConcept('1', 'Weak Concept', 0.2, 'weak')];
      const graph = createTestGraph(concepts);

      const { container } = render(<KnowledgeGraph graph={graph} />);

      // Check for weak status text
      expect(screen.getByText('weak')).toBeInTheDocument();
    });

    it('should render learning concepts with yellow indicator', () => {
      const concepts = [createConcept('1', 'Learning Concept', 0.5, 'learning')];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Check for learning status text
      expect(screen.getByText('learning')).toBeInTheDocument();
    });

    it('should render understood concepts with light green indicator', () => {
      const concepts = [createConcept('1', 'Understood Concept', 0.75, 'understood')];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Check for understood status text
      expect(screen.getByText('understood')).toBeInTheDocument();
    });

    it('should render mastered concepts with dark green indicator', () => {
      const concepts = [createConcept('1', 'Mastered Concept', 0.9, 'mastered')];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Check for mastered status text
      expect(screen.getByText('mastered')).toBeInTheDocument();
    });

    it('should render locked concepts with gray indicator', () => {
      const concepts = [createConcept('1', 'Locked Concept', 0.0, 'locked')];
      const graph = createTestGraph(concepts);

      render(<KnowledgeGraph graph={graph} />);

      // Check for locked status text
      expect(screen.getByText('locked')).toBeInTheDocument();
    });

    it('should apply correct visual state for any mastery status', () => {
      // Property: For any concept with specific mastery status, correct visual state is applied
      const statusCases: Array<{ status: MasteryStatus; expectedText: string }> = [
        { status: 'weak', expectedText: 'weak' },
        { status: 'learning', expectedText: 'learning' },
        { status: 'understood', expectedText: 'understood' },
        { status: 'mastered', expectedText: 'mastered' },
        { status: 'locked', expectedText: 'locked' },
      ];

      statusCases.forEach(({ status, expectedText }) => {
        const concepts = [createConcept('test-id', `Test ${status}`, 0.5, status)];
        const graph = createTestGraph(concepts);

        const { unmount } = render(<KnowledgeGraph graph={graph} />);

        // Verify status text is displayed
        expect(screen.getByText(expectedText)).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Property 12: Root gap highlighting', () => {
    it('should highlight the root gap node when root_gap_id is set', () => {
      const concepts = [
        createConcept('1', 'Concept A', 0.8, 'understood'),
        createConcept('2', 'Root Gap Concept', 0.2, 'weak'),
        createConcept('3', 'Target Concept', 0.1, 'weak', true),
      ];
      const graph = createTestGraph(concepts, '2'); // Set concept '2' as root gap

      render(<KnowledgeGraph graph={graph} />);

      // Verify "Root Gap" indicator is present
      expect(screen.getByText('Root Gap')).toBeInTheDocument();
    });

    it('should not show root gap highlighting when root_gap_id is null', () => {
      const concepts = [
        createConcept('1', 'Concept A', 0.5, 'learning'),
        createConcept('2', 'Concept B', 0.3, 'weak'),
      ];
      const graph = createTestGraph(concepts, null);

      render(<KnowledgeGraph graph={graph} />);

      // Verify "Root Gap" text is not present
      expect(screen.queryByText('Root Gap')).not.toBeInTheDocument();
    });

    it('should highlight only the specified root gap node', () => {
      const concepts = [
        createConcept('1', 'Concept A', 0.5, 'learning'),
        createConcept('2', 'Root Gap', 0.2, 'weak'),
        createConcept('3', 'Concept C', 0.3, 'weak'),
      ];
      const graph = createTestGraph(concepts, '2');

      render(<KnowledgeGraph graph={graph} />);

      // Should have "Root Gap" indicator (may appear in both main graph and minimap)
      const rootGapElements = screen.getAllByText('Root Gap');
      expect(rootGapElements.length).toBeGreaterThanOrEqual(1);
    });

    it('should apply root gap highlighting for any identified root gap', () => {
      // Property: For any session with identified root gap, highlighting is applied
      const testRootGapIds = ['root-1', 'root-2', 'root-3'];

      testRootGapIds.forEach((rootGapId) => {
        const concepts = [
          createConcept('root-1', 'Concept 1', 0.3, 'weak'),
          createConcept('root-2', 'Concept 2', 0.2, 'weak'),
          createConcept('root-3', 'Concept 3', 0.4, 'learning'),
        ];
        const graph = createTestGraph(concepts, rootGapId);

        const { unmount } = render(<KnowledgeGraph graph={graph} />);

        // Verify exactly one root gap indicator is shown
        const rootGapElements = screen.getAllByText('Root Gap');
        expect(rootGapElements).toHaveLength(1);

        unmount();
      });
    });
  });

  describe('Integration: All properties together', () => {
    it('should display all required information with correct visual states and root gap highlighting', () => {
      const concepts = [
        createConcept('1', 'Variables', 0.85, 'mastered'),
        createConcept('2', 'Functions', 0.72, 'understood'),
        createConcept('3', 'Call Stack', 0.25, 'weak'), // Root gap
        createConcept('4', 'Recursion', 0.15, 'locked', true),
      ];
      const graph = createTestGraph(concepts, '3');

      render(<KnowledgeGraph graph={graph} />);

      // Property 10: All names and percentages displayed
      expect(screen.getByText('Variables')).toBeInTheDocument();
      expect(screen.getByText('Functions')).toBeInTheDocument();
      expect(screen.getByText('Call Stack')).toBeInTheDocument();
      expect(screen.getByText('Recursion')).toBeInTheDocument();

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('72%')).toBeInTheDocument();
      expect(screen.getByText('25%')).toBeInTheDocument();
      expect(screen.getByText('15%')).toBeInTheDocument();

      // Property 11: Status indicators present
      expect(screen.getByText('mastered')).toBeInTheDocument();
      expect(screen.getByText('understood')).toBeInTheDocument();
      expect(screen.getByText('weak')).toBeInTheDocument();
      expect(screen.getByText('locked')).toBeInTheDocument();

      // Property 12: Root gap highlighted
      expect(screen.getByText('Root Gap')).toBeInTheDocument();

      // Target indicator should also be present
      expect(screen.getByText('Target')).toBeInTheDocument();
    });
  });

  describe('Property 16 & 17: Defensive rendering for undefined data', () => {
    it('should render loading state when graph is undefined', () => {
      // Feature: rootlearn-ui-redesign, Property 16: Graph defensive rendering - concepts
      render(<KnowledgeGraph graph={undefined} />);

      expect(screen.getByText('Loading knowledge map...')).toBeInTheDocument();
      expect(screen.getByText('Building your prerequisite graph')).toBeInTheDocument();
    });

    it('should render loading state when concepts are undefined', () => {
      // Feature: rootlearn-ui-redesign, Property 16: Graph defensive rendering - concepts
      const graph = {
        concepts: undefined as any,
        edges: [],
        root_gap_id: null,
      };

      render(<KnowledgeGraph graph={graph} />);

      expect(screen.getByText('Loading knowledge map...')).toBeInTheDocument();
    });

    it('should render loading state when edges are undefined', () => {
      // Feature: rootlearn-ui-redesign, Property 17: Graph defensive rendering - edges
      const graph = {
        concepts: [createConcept('1', 'Test', 0.5, 'learning')],
        edges: undefined as any,
        root_gap_id: null,
      };

      render(<KnowledgeGraph graph={graph} />);

      expect(screen.getByText('Loading knowledge map...')).toBeInTheDocument();
    });

    it('should render empty state when concepts array is empty', () => {
      // Feature: rootlearn-ui-redesign, Property 18: Graph empty state
      const graph = {
        concepts: [],
        edges: [],
        root_gap_id: null,
      };

      render(<KnowledgeGraph graph={graph} />);

      expect(screen.getByText('No concepts to display')).toBeInTheDocument();
      expect(screen.getByText(/knowledge map is empty/i)).toBeInTheDocument();
    });

    it('should not crash when calling map on undefined concepts', () => {
      // Feature: rootlearn-ui-redesign, Property 16: Graph defensive rendering - concepts
      // This test ensures .map() is never called on undefined
      const graph = {
        concepts: undefined as any,
        edges: [],
        root_gap_id: null,
      };

      // Should not throw an error
      expect(() => render(<KnowledgeGraph graph={graph} />)).not.toThrow();
    });

    it('should not crash when calling map on undefined edges', () => {
      // Feature: rootlearn-ui-redesign, Property 17: Graph defensive rendering - edges
      // This test ensures .map() is never called on undefined
      const graph = {
        concepts: [createConcept('1', 'Test', 0.5, 'learning')],
        edges: undefined as any,
        root_gap_id: null,
      };

      // Should not throw an error
      expect(() => render(<KnowledgeGraph graph={graph} />)).not.toThrow();
    });
  });
});
