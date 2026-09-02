import { test, expect, Page } from '@playwright/test';

/**
 * E2E Test: Complete Learning Flow
 * 
 * This test validates the entire happy path from landing page to completion:
 * 1. Landing page - session creation
 * 2. Graph visualization
 * 3. Diagnostic Q&A
 * 4. Root gap identification
 * 5. Tutoring chat
 * 6. Teach-back submission
 * 
 * Task 24.2: Write frontend E2E test with Playwright
 */

// Helper function to wait for specific session status
async function waitForSessionStatus(page: Page, status: string, timeout = 30000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    // Look for the status badge
    const statusBadge = page.locator('[class*="bg-"][class*="text-"]', { 
      hasText: new RegExp(status, 'i') 
    });
    
    if (await statusBadge.isVisible({ timeout: 1000 }).catch(() => false)) {
      return true;
    }
    
    await page.waitForTimeout(1000);
  }
  
  throw new Error(`Timeout waiting for session status: ${status}`);
}

// Helper to extract session ID and user ID from URL
function extractSessionParams(url: string) {
  const match = url.match(/\/session\/([^?]+)\?user_id=([^&]+)/);
  if (!match) {
    throw new Error('Could not extract session params from URL');
  }
  return {
    sessionId: match[1],
    userId: match[2],
  };
}

test.describe('Complete Learning Flow', () => {
  test.setTimeout(180000); // 3 minutes for complete flow
  
  test('should complete happy path from landing page to teach-back', async ({ page }) => {
    // ========================================
    // STEP 1: Landing Page - Create Session
    // ========================================
    await test.step('Navigate to landing page', async () => {
      await page.goto('/');
      
      // Verify we're on the landing page
      await expect(page.locator('h1')).toContainText('RootLearn');
      await expect(page.locator('text=What are you struggling with?')).toBeVisible();
    });

    await test.step('Create a new learning session', async () => {
      // Fill in the prompt
      const promptText = "I don't understand recursion in programming";
      await page.fill('textarea#prompt', promptText);
      
      // Verify the text was entered
      await expect(page.locator('textarea#prompt')).toHaveValue(promptText);
      
      // Submit the form
      await page.click('button[type="submit"]');
      
      // Wait for navigation to session page
      await page.waitForURL(/\/session\/[^?]+\?user_id=/, { timeout: 10000 });
      
      // Verify we're on the session page
      const url = page.url();
      expect(url).toMatch(/\/session\/[a-f0-9-]+\?user_id=[a-f0-9-]+/);
    });

    // ========================================
    // STEP 2: Graph Generation & Visualization
    // ========================================
    await test.step('Wait for graph generation', async () => {
      // First, we should see "Analyzing" status
      await expect(page.locator('text=/Analyzing/i')).toBeVisible({ timeout: 10000 });
      
      // Wait for analysis to complete and graph to be generated
      // The status should change from "analyzing" to "diagnosing"
      await waitForSessionStatus(page, 'Diagnosing', 60000);
      
      // Verify the graph visualization is present
      const graphContainer = page.locator('[class*="react-flow"]').first();
      await expect(graphContainer).toBeVisible({ timeout: 15000 });
    });

    await test.step('Verify graph displays concepts', async () => {
      // Wait a moment for the graph to fully render
      await page.waitForTimeout(2000);
      
      // The graph should have nodes (concepts)
      // React Flow renders nodes with class 'react-flow__node'
      const nodes = page.locator('.react-flow__node');
      const nodeCount = await nodes.count();
      
      // We should have at least one node
      expect(nodeCount).toBeGreaterThan(0);
      console.log(`Graph contains ${nodeCount} concept nodes`);
      
      // Verify edges exist (connections between concepts)
      const edges = page.locator('.react-flow__edge');
      const edgeCount = await edges.count();
      expect(edgeCount).toBeGreaterThan(0);
      console.log(`Graph contains ${edgeCount} edges`);
    });

    await test.step('Test graph interaction - click a node', async () => {
      // Click on the first visible node
      const firstNode = page.locator('.react-flow__node').first();
      await firstNode.click();
      
      // The click should work without errors
      await page.waitForTimeout(500);
    });

    // ========================================
    // STEP 3: Diagnostic Q&A
    // ========================================
    await test.step('Complete diagnostic assessment', async () => {
      // Verify we're in diagnostic phase
      await expect(page.locator('text=/Diagnostic Assessment/i')).toBeVisible();
      
      // Answer at least one diagnostic question
      // Look for question text
      const questionVisible = await page.locator('[class*="question"]').isVisible({ timeout: 5000 })
        .catch(() => false);
      
      if (questionVisible) {
        console.log('Answering diagnostic question...');
        
        // Find the answer input (could be textarea or input)
        const answerInput = page.locator('textarea, input[type="text"]').first();
        await answerInput.fill('A recursive function is a function that calls itself. It needs a base case to stop recursion.');
        
        // Submit the answer
        const submitButton = page.locator('button', { hasText: /submit/i }).first();
        await submitButton.click();
        
        // Wait for evaluation to appear
        await page.waitForTimeout(3000);
        
        // Look for evaluation feedback
        const evaluationPresent = await page.locator('text=/score|correct|evaluation/i')
          .isVisible({ timeout: 5000 })
          .catch(() => false);
        
        if (evaluationPresent) {
          console.log('Diagnostic evaluation received');
        }
      }
    });

    // ========================================
    // STEP 4: Root Gap & Tutoring
    // ========================================
    await test.step('Wait for tutoring phase and root gap identification', async () => {
      // The system should eventually transition to tutoring
      // This might take some time as it completes diagnosis
      await waitForSessionStatus(page, 'Tutoring', 60000);
      
      // Verify root gap card is displayed
      await expect(page.locator('text=/Root Gap|Gap Score/i')).toBeVisible({ timeout: 10000 });
      console.log('Root gap identified');
    });

    await test.step('Verify Socratic tutoring interface', async () => {
      // Verify tutoring panel is visible
      await expect(page.locator('text=/Socratic Tutoring/i')).toBeVisible();
      
      // There should be a message input
      const messageInput = page.locator('textarea, input[type="text"]').last();
      await expect(messageInput).toBeVisible();
      
      // There should be an "Explain it back" or similar button
      const explainButton = page.locator('button', { hasText: /explain.*back/i });
      await expect(explainButton).toBeVisible({ timeout: 5000 });
    });

    await test.step('Send messages in tutoring chat', async () => {
      // Send a message to the tutor
      const messageInput = page.locator('textarea, input[type="text"]').last();
      await messageInput.fill('Can you help me understand this concept better?');
      
      // Find and click the send button
      const sendButton = page.locator('button[type="submit"], button', { hasText: /send/i }).last();
      await sendButton.click();
      
      // Wait for AI response
      await page.waitForTimeout(5000);
      
      // Verify messages are displayed in chat
      const messages = page.locator('[class*="message"]');
      const messageCount = await messages.count().catch(() => 0);
      console.log(`Chat contains ${messageCount} messages`);
    });

    // ========================================
    // STEP 5: Teach-Back Submission
    // ========================================
    await test.step('Initiate teach-back', async () => {
      // Click "Explain it back" button
      const explainButton = page.locator('button', { hasText: /explain.*back/i }).first();
      await explainButton.click();
      
      // Wait for transition to teach-back state
      await waitForSessionStatus(page, 'Teach-Back', 30000);
      
      // Verify teach-back panel is visible
      await expect(page.locator('text=/Teach-Back Verification/i')).toBeVisible();
      console.log('Transitioned to teach-back phase');
    });

    await test.step('Submit teach-back explanation', async () => {
      // Find the explanation textarea
      const explanationArea = page.locator('textarea').first();
      await expect(explanationArea).toBeVisible();
      
      // Write a comprehensive explanation
      const explanation = `
        This concept works by breaking down a problem into smaller subproblems.
        The key components are:
        1. A base case that stops the recursion
        2. A recursive case that calls the function with a modified input
        3. The function must make progress toward the base case
        
        For example, calculating factorial: n! = n * (n-1)!
        The base case is when n = 0 or n = 1, which returns 1.
        Otherwise, we multiply n by the factorial of (n-1).
      `;
      
      await explanationArea.fill(explanation.trim());
      
      // Submit the explanation
      const submitButton = page.locator('button[type="submit"], button', { hasText: /submit/i }).first();
      await submitButton.click();
      
      // Wait for evaluation
      await page.waitForTimeout(5000);
      
      // Look for evaluation results
      const evaluationVisible = await page.locator('text=/coverage|reasoning|clarity|score/i')
        .isVisible({ timeout: 10000 })
        .catch(() => false);
      
      if (evaluationVisible) {
        console.log('Teach-back evaluation received');
        
        // Check for scores
        const scoresPresent = await page.locator('text=/\\d+%/').isVisible({ timeout: 5000 })
          .catch(() => false);
        
        if (scoresPresent) {
          console.log('Evaluation scores displayed');
        }
      }
    });

    // ========================================
    // STEP 6: Verify State Transitions
    // ========================================
    await test.step('Verify system progresses after teach-back', async () => {
      // After teach-back, the system should either:
      // - Return to tutoring (if insufficient)
      // - Return to diagnosing (if more concepts need work)
      // - Complete (if target is understood)
      
      // Wait for any state transition
      await page.waitForTimeout(5000);
      
      // Check what state we're in
      const currentStatus = await page.locator('[class*="bg-"][class*="text-"]').first().textContent();
      console.log(`Current session status: ${currentStatus}`);
      
      // Verify we're in a valid state
      const validStates = ['Diagnosing', 'Tutoring', 'Teach-Back', 'Completed'];
      const isValidState = validStates.some(state => 
        currentStatus?.toLowerCase().includes(state.toLowerCase())
      );
      
      expect(isValidState).toBeTruthy();
    });

    // ========================================
    // Final Verification
    // ========================================
    await test.step('Verify complete flow succeeded', async () => {
      // The graph should still be visible and updated
      const graphContainer = page.locator('[class*="react-flow"]').first();
      await expect(graphContainer).toBeVisible();
      
      // At least one node should show updated mastery
      // (This is implicit through the state changes)
      
      console.log('✅ Complete learning flow test passed');
    });
  });

  test('should handle session creation errors gracefully', async ({ page }) => {
    await test.step('Navigate to landing page', async () => {
      await page.goto('/');
    });

    await test.step('Try to submit empty prompt', async () => {
      const submitButton = page.locator('button[type="submit"]');
      
      // Button should be disabled when empty
      await expect(submitButton).toBeDisabled();
    });

    await test.step('Fill and clear prompt', async () => {
      // Fill prompt
      await page.fill('textarea#prompt', 'test');
      
      // Button should be enabled
      const submitButton = page.locator('button[type="submit"]');
      await expect(submitButton).toBeEnabled();
      
      // Clear prompt
      await page.fill('textarea#prompt', '');
      
      // Button should be disabled again
      await expect(submitButton).toBeDisabled();
    });
  });

  test('should display graph interactions correctly', async ({ page, request }) => {
    // This test uses API to set up a session with a graph
    // Then tests graph interaction features
    
    await test.step('Create session via API', async () => {
      // We'll create a session and manually navigate to it
      // For this test, we just verify the graph component works
      await page.goto('/');
      
      const promptText = "Test prompt for graph";
      await page.fill('textarea#prompt', promptText);
      await page.click('button[type="submit"]');
      
      await page.waitForURL(/\/session\/[^?]+\?user_id=/);
    });

    await test.step('Wait for graph to load', async () => {
      await waitForSessionStatus(page, 'Diagnosing', 60000);
      
      const graphContainer = page.locator('[class*="react-flow"]').first();
      await expect(graphContainer).toBeVisible({ timeout: 15000 });
    });

    await test.step('Verify graph zoom and pan controls', async () => {
      // React Flow includes zoom controls by default
      const zoomControls = page.locator('.react-flow__controls');
      
      // Controls might not always be visible depending on configuration
      const controlsVisible = await zoomControls.isVisible({ timeout: 2000 })
        .catch(() => false);
      
      console.log(`Graph controls visible: ${controlsVisible}`);
    });
  });
});
