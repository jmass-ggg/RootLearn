import { Page, expect } from '@playwright/test';

/**
 * Test Helper Utilities for E2E Tests
 * 
 * Reusable functions for common test operations
 */

/**
 * Wait for a specific session status to appear
 * @param page - Playwright page object
 * @param status - Expected status (e.g., 'Diagnosing', 'Tutoring')
 * @param timeout - Maximum time to wait in milliseconds
 * @returns Promise<boolean> - Returns true when status is found
 */
export async function waitForSessionStatus(
  page: Page, 
  status: string, 
  timeout = 30000
): Promise<boolean> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    // Look for the status badge
    const statusBadge = page.locator('[class*="bg-"][class*="text-"]', { 
      hasText: new RegExp(status, 'i') 
    });
    
    const isVisible = await statusBadge.isVisible({ timeout: 1000 }).catch(() => false);
    if (isVisible) {
      return true;
    }
    
    await page.waitForTimeout(1000);
  }
  
  throw new Error(`Timeout waiting for session status: ${status}`);
}

/**
 * Extract session ID and user ID from the current URL
 * @param url - Current page URL
 * @returns Object with sessionId and userId
 */
export function extractSessionParams(url: string): { sessionId: string; userId: string } {
  const match = url.match(/\/session\/([^?]+)\?user_id=([^&]+)/);
  if (!match) {
    throw new Error(`Could not extract session params from URL: ${url}`);
  }
  return {
    sessionId: match[1],
    userId: match[2],
  };
}

/**
 * Wait for graph to be fully loaded and rendered
 * @param page - Playwright page object
 * @param timeout - Maximum time to wait
 */
export async function waitForGraphLoaded(page: Page, timeout = 15000): Promise<void> {
  const graphContainer = page.locator('[class*="react-flow"]').first();
  await expect(graphContainer).toBeVisible({ timeout });
  
  // Wait for at least one node to be rendered
  const nodes = page.locator('.react-flow__node');
  await expect(nodes.first()).toBeVisible({ timeout: 5000 });
}

/**
 * Count the number of graph nodes
 * @param page - Playwright page object
 * @returns Number of nodes in the graph
 */
export async function countGraphNodes(page: Page): Promise<number> {
  const nodes = page.locator('.react-flow__node');
  return await nodes.count();
}

/**
 * Count the number of graph edges
 * @param page - Playwright page object
 * @returns Number of edges in the graph
 */
export async function countGraphEdges(page: Page): Promise<number> {
  const edges = page.locator('.react-flow__edge');
  return await edges.count();
}

/**
 * Fill and submit diagnostic answer
 * @param page - Playwright page object
 * @param answer - Answer text to submit
 */
export async function submitDiagnosticAnswer(page: Page, answer: string): Promise<void> {
  const answerInput = page.locator('textarea, input[type="text"]').first();
  await answerInput.fill(answer);
  
  const submitButton = page.locator('button', { hasText: /submit/i }).first();
  await submitButton.click();
}

/**
 * Send a message in the tutor chat
 * @param page - Playwright page object
 * @param message - Message text to send
 */
export async function sendTutorMessage(page: Page, message: string): Promise<void> {
  const messageInput = page.locator('textarea, input[type="text"]').last();
  await messageInput.fill(message);
  
  const sendButton = page.locator('button[type="submit"], button', { hasText: /send/i }).last();
  await sendButton.click();
}

/**
 * Click the "Explain it back" button to transition to teach-back
 * @param page - Playwright page object
 */
export async function clickExplainBack(page: Page): Promise<void> {
  const explainButton = page.locator('button', { hasText: /explain.*back/i }).first();
  await explainButton.click();
}

/**
 * Submit a teach-back explanation
 * @param page - Playwright page object
 * @param explanation - Explanation text to submit
 */
export async function submitTeachBack(page: Page, explanation: string): Promise<void> {
  const explanationArea = page.locator('textarea').first();
  await explanationArea.fill(explanation);
  
  const submitButton = page.locator('button[type="submit"], button', { hasText: /submit/i }).first();
  await submitButton.click();
}

/**
 * Create a new session from landing page
 * @param page - Playwright page object
 * @param prompt - Learning prompt text
 * @returns Promise that resolves when navigated to session page
 */
export async function createSession(page: Page, prompt: string): Promise<void> {
  await page.goto('/');
  
  await page.fill('textarea#prompt', prompt);
  await page.click('button[type="submit"]');
  
  // Wait for navigation to session page
  await page.waitForURL(/\/session\/[^?]+\?user_id=/, { timeout: 10000 });
}

/**
 * Wait for a specific element to contain text
 * @param page - Playwright page object
 * @param selector - CSS selector or text pattern
 * @param text - Text to wait for
 * @param timeout - Maximum time to wait
 */
export async function waitForText(
  page: Page, 
  selector: string, 
  text: string | RegExp, 
  timeout = 10000
): Promise<void> {
  const element = typeof text === 'string' 
    ? page.locator(selector, { hasText: text })
    : page.locator(selector, { hasText: text });
  
  await expect(element).toBeVisible({ timeout });
}

/**
 * Check if element exists (without waiting)
 * @param page - Playwright page object
 * @param selector - CSS selector
 * @returns Promise<boolean> - True if element exists
 */
export async function elementExists(page: Page, selector: string): Promise<boolean> {
  return await page.locator(selector).count() > 0;
}

/**
 * Get the current session status from the badge
 * @param page - Playwright page object
 * @returns Promise<string> - Current status text
 */
export async function getCurrentStatus(page: Page): Promise<string> {
  const statusBadge = page.locator('[class*="bg-"][class*="text-"]').first();
  const statusText = await statusBadge.textContent();
  return statusText?.trim() || '';
}

/**
 * Wait for any loading indicators to disappear
 * @param page - Playwright page object
 * @param timeout - Maximum time to wait
 */
export async function waitForLoadingComplete(page: Page, timeout = 30000): Promise<void> {
  const loadingIndicators = [
    page.locator('text=/loading/i'),
    page.locator('[class*="animate-spin"]'),
    page.locator('text=/please wait/i'),
  ];
  
  for (const indicator of loadingIndicators) {
    const exists = await indicator.isVisible({ timeout: 1000 }).catch(() => false);
    if (exists) {
      await indicator.waitFor({ state: 'hidden', timeout });
    }
  }
}

/**
 * Take a screenshot with a descriptive name
 * @param page - Playwright page object
 * @param name - Screenshot name
 */
export async function takeScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ 
    path: `test-results/screenshots/${name}.png`,
    fullPage: true 
  });
}

/**
 * Log test information to console
 * @param message - Message to log
 * @param data - Optional data object
 */
export function logTestInfo(message: string, data?: any): void {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`, data ? JSON.stringify(data, null, 2) : '');
}

/**
 * Verify graph node has specific visual state
 * @param page - Playwright page object
 * @param nodeName - Name of the concept node
 * @param expectedClass - Expected CSS class (e.g., 'weak', 'mastered')
 */
export async function verifyNodeVisualState(
  page: Page, 
  nodeName: string, 
  expectedClass: string
): Promise<void> {
  const node = page.locator('.react-flow__node', { hasText: nodeName });
  await expect(node).toHaveClass(new RegExp(expectedClass, 'i'));
}

/**
 * Wait for multiple conditions to be true
 * @param conditions - Array of async boolean functions
 * @param timeout - Maximum time to wait
 */
export async function waitForAll(
  conditions: Array<() => Promise<boolean>>, 
  timeout = 30000
): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const results = await Promise.all(conditions.map(c => c().catch(() => false)));
    
    if (results.every(r => r === true)) {
      return;
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  throw new Error('Timeout waiting for all conditions to be met');
}
