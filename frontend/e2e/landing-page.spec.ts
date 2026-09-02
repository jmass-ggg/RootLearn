import { test, expect } from '@playwright/test';

/**
 * E2E Test: Landing Page
 * 
 * Simple tests for landing page functionality that don't require backend
 */

test.describe('Landing Page', () => {
  test('should display landing page correctly', async ({ page }) => {
    await page.goto('/');
    
    // Verify main heading
    await expect(page.locator('h1')).toContainText('RootLearn');
    
    // Verify subtitle
    await expect(page.locator('text=AI-powered knowledge debugger')).toBeVisible();
    
    // Verify form elements
    await expect(page.locator('label[for="prompt"]')).toContainText('What are you struggling with?');
    await expect(page.locator('textarea#prompt')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should validate prompt input', async ({ page }) => {
    await page.goto('/');
    
    const promptInput = page.locator('textarea#prompt');
    const submitButton = page.locator('button[type="submit"]');
    
    // Initially, button should be disabled (empty prompt)
    await expect(submitButton).toBeDisabled();
    
    // Fill in some text
    await promptInput.fill('I need help with recursion');
    
    // Button should now be enabled
    await expect(submitButton).toBeEnabled();
    await expect(submitButton).toContainText('Diagnose my understanding');
    
    // Clear the text
    await promptInput.clear();
    
    // Button should be disabled again
    await expect(submitButton).toBeDisabled();
  });

  test.skip('should show loading state when submitting (requires backend)', async ({ page }) => {
    await page.goto('/');
    
    const promptInput = page.locator('textarea#prompt');
    const submitButton = page.locator('button[type="submit"]');
    
    // Fill in prompt
    await promptInput.fill('Test prompt');
    
    // Click submit
    await submitButton.click();
    
    // Should show loading state (button becomes disabled and text changes)
    // Note: This might fail quickly if backend is not running and returns an error immediately
    const isDisabled = await submitButton.isDisabled({ timeout: 1000 }).catch(() => false);
    const hasLoadingText = await submitButton.textContent().then(text => 
      text?.toLowerCase().includes('creating') || false
    );
    
    // Either the button should be disabled OR show loading text
    // (depending on timing and backend availability)
    expect(isDisabled || hasLoadingText).toBeTruthy();
  });

  test('should have proper responsive layout', async ({ page }) => {
    // Test desktop layout
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    const mainContainer = page.locator('main');
    await expect(mainContainer).toBeVisible();
    
    // Test mobile layout
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Page should still be visible and usable
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('textarea#prompt')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should have accessible form elements', async ({ page }) => {
    await page.goto('/');
    
    // Check textarea has label
    const textarea = page.locator('textarea#prompt');
    await expect(textarea).toHaveAttribute('id', 'prompt');
    
    const label = page.locator('label[for="prompt"]');
    await expect(label).toBeVisible();
    
    // Check button is keyboard accessible
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toHaveAttribute('type', 'submit');
    
    // Verify placeholder text
    await expect(textarea).toHaveAttribute('placeholder', /recursion/i);
  });

  test('should display description text', async ({ page }) => {
    await page.goto('/');
    
    // Verify all description texts are present
    await expect(page.locator('text=Identify and fix your knowledge gaps')).toBeVisible();
    await expect(page.locator('text=/RootLearn will analyze/i')).toBeVisible();
  });
});
