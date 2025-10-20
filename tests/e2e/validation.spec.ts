import { test, expect } from '@playwright/test';

/**
 * Basic validation test to ensure Playwright setup is working correctly
 */

test.describe('Playwright Setup Validation', () => {
  test('should be able to navigate to the application', async ({ page }) => {
    // This test validates that Playwright can start the servers and navigate to the app
    await page.goto('/');
    
    // Basic check that the page loads
    await expect(page).toHaveTitle(/Whisper Transcriber/);
    
    // Check that the login form is present (indicates frontend is working)
    const loginForm = page.locator('form, [data-testid="login-form"], input[type="text"], input[type="email"], input[placeholder*="username"], input[placeholder*="email"]');
    await expect(loginForm.first()).toBeVisible();
    
    console.log('✅ Playwright E2E framework setup is working correctly!');
    console.log('✅ Frontend server is running and accessible');
    console.log('✅ Browser automation is functional');
  });

  test('should be able to check backend API health', async ({ request }) => {
    // Test that the backend is accessible
    const response = await request.get('/api/health');
    
    // Should get some response (even if 404, means server is running)
    expect([200, 401, 404]).toContain(response.status());
    
    console.log('✅ Backend API is accessible');
    console.log(`API response status: ${response.status()}`);
  });

  test('should work in different browser configurations', async ({ browser, browserName }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Should work in all configured browsers
      await expect(page.locator('body')).toBeVisible();
      
      console.log(`✅ Browser ${browserName} is working correctly`);
      
    } finally {
      await context.close();
    }
  });
});
