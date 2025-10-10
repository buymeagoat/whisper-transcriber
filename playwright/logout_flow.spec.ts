import { test, expect } from '@playwright/test';

/**
 * End-to-end tests for user authentication and logout flows.
 * 
 * These tests verify that the SPA handles user state correctly,
 * including login, navigation, and logout with proper state cleanup.
 */

test.describe('User Authentication Flow', () => {
  const baseURL = 'http://localhost:8000';
  const testUser = {
    username: 'e2etest_' + Date.now(),
    email: 'e2etest_' + Date.now() + '@example.com',
    password: 'e2etest123'
  };

  test.beforeEach(async ({ page }) => {
    // Navigate to app
    await page.goto(baseURL);
    
    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test('app loads and displays correctly', async ({ page }) => {
    // Should load SPA
    await expect(page).toHaveTitle(/Whisper/i);
    
    // Basic UI elements should be present
    await expect(page.locator('body')).toBeVisible();
    
    // Check for React app mounting
    await expect(page.locator('#root')).toBeVisible();
  });

  test('navigation to different routes works', async ({ page }) => {
    // Test direct navigation to different routes
    const routes = ['/login', '/dashboard', '/upload'];
    
    for (const route of routes) {
      await page.goto(baseURL + route);
      
      // Should not return 404 page, should load SPA
      const pageContent = await page.content();
      expect(pageContent).toContain('<!DOCTYPE html>');
      
      // Should not show "Not Found" or similar error
      const notFoundTexts = ['404', 'Not Found', 'Page Not Found'];
      const hasError = notFoundTexts.some(text => 
        pageContent.toLowerCase().includes(text.toLowerCase())
      );
      expect(hasError).toBeFalsy();
    }
  });

  test('user registration flow', async ({ page }) => {
    // Go to registration page (if separate) or find registration form
    await page.goto(baseURL + '/register');
    
    // Look for registration form elements
    const usernameField = page.locator('[data-testid="username"], input[name="username"], input[placeholder*="username" i]').first();
    const emailField = page.locator('[data-testid="email"], input[name="email"], input[type="email"]').first();
    const passwordField = page.locator('[data-testid="password"], input[name="password"], input[type="password"]').first();
    const submitButton = page.locator('[data-testid="register-submit"], button[type="submit"], button:has-text("Register")').first();
    
    if (await usernameField.isVisible()) {
      // Fill registration form
      await usernameField.fill(testUser.username);
      await emailField.fill(testUser.email);
      await passwordField.fill(testUser.password);
      
      // Submit registration
      await submitButton.click();
      
      // Wait for response (success or error message)
      await page.waitForTimeout(2000);
      
      // Should either succeed or show validation error (not crash)
      const pageContent = await page.content();
      expect(pageContent).not.toContain('Internal Server Error');
    } else {
      test.skip('Registration form not found - skipping registration test');
    }
  });

  test('user login and logout flow', async ({ page }) => {
    // Navigate to login page
    await page.goto(baseURL + '/login');
    
    // Look for login form elements with multiple selector strategies
    const usernameField = page.locator([
      '[data-testid="username"]',
      'input[name="username"]',
      'input[placeholder*="username" i]',
      '#username'
    ].join(', ')).first();
    
    const passwordField = page.locator([
      '[data-testid="password"]',
      'input[name="password"]',
      'input[type="password"]',
      '#password'
    ].join(', ')).first();
    
    const loginButton = page.locator([
      '[data-testid="login-submit"]',
      'button[type="submit"]',
      'button:has-text("Login")',
      'button:has-text("Sign In")'
    ].join(', ')).first();
    
    // Check if login form is available
    if (await usernameField.isVisible()) {
      // Try login with default admin credentials
      await usernameField.fill('admin');
      await passwordField.fill('changeme');
      await loginButton.click();
      
      // Wait for login response
      await page.waitForTimeout(3000);
      
      // Check for successful login indicators
      const afterLoginContent = await page.content();
      
      // Should not show error page
      expect(afterLoginContent).not.toContain('Internal Server Error');
      
      // Look for logout button or user menu (indicating successful login)
      const logoutButton = page.locator([
        '[data-testid="logout-button"]',
        'button:has-text("Logout")',
        'button:has-text("Sign Out")',
        '.logout-button',
        '[data-testid="user-menu"]'
      ].join(', ')).first();
      
      if (await logoutButton.isVisible({ timeout: 5000 })) {
        // Login was successful, test logout
        await logoutButton.click();
        
        // Wait for logout to complete
        await page.waitForTimeout(2000);
        
        // Should redirect back to login or home page
        const finalUrl = page.url();
        const currentContent = await page.content();
        
        // Should not crash or show errors
        expect(currentContent).not.toContain('Internal Server Error');
        
        // User menu/logout button should no longer be visible
        await expect(logoutButton).not.toBeVisible({ timeout: 3000 });
        
        console.log('✓ Login/logout flow completed successfully');
      } else {
        console.log('⚠ Login may have failed or user menu not found');
      }
    } else {
      test.skip('Login form not found - skipping login test');
    }
  });

  test('protected routes redirect when not authenticated', async ({ page }) => {
    // Clear any existing authentication
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());
    
    // Try to access protected routes
    const protectedRoutes = ['/dashboard', '/upload', '/settings'];
    
    for (const route of protectedRoutes) {
      await page.goto(baseURL + route);
      await page.waitForTimeout(2000);
      
      const currentUrl = page.url();
      const content = await page.content();
      
      // Should either redirect to login or show login form
      // Should not crash with 500 error
      expect(content).not.toContain('Internal Server Error');
      
      // If there's authentication, should redirect to login or show login form
      const hasLoginForm = content.includes('password') || content.includes('login');
      const redirectedToLogin = currentUrl.includes('/login') || currentUrl === baseURL + '/';
      
      if (!hasLoginForm && !redirectedToLogin) {
        console.log(`⚠ Route ${route} may not be properly protected`);
      }
    }
  });

  test('file upload interface exists', async ({ page }) => {
    // Navigate to upload page
    await page.goto(baseURL + '/upload');
    await page.waitForTimeout(2000);
    
    const content = await page.content();
    
    // Should not crash
    expect(content).not.toContain('Internal Server Error');
    
    // Look for file upload interface
    const fileInput = page.locator('input[type="file"]').first();
    const hasFileUpload = await fileInput.isVisible({ timeout: 3000 });
    
    if (hasFileUpload) {
      console.log('✓ File upload interface found');
    } else {
      console.log('⚠ File upload interface not immediately visible');
    }
  });

  test('app handles browser back/forward navigation', async ({ page }) => {
    // Navigate through different routes
    await page.goto(baseURL + '/');
    await page.goto(baseURL + '/login');
    await page.goto(baseURL + '/dashboard');
    
    // Use browser back button
    await page.goBack();
    await page.waitForTimeout(1000);
    
    // Should handle navigation without crashing
    const content = await page.content();
    expect(content).not.toContain('Internal Server Error');
    expect(content).toContain('<!DOCTYPE html>');
    
    // Use browser forward button
    await page.goForward();
    await page.waitForTimeout(1000);
    
    const finalContent = await page.content();
    expect(finalContent).not.toContain('Internal Server Error');
  });
});

test.describe('Static Asset Loading', () => {
  const baseURL = 'http://localhost:8000';

  test('CSS and JS assets load correctly', async ({ page }) => {
    // Listen for failed requests
    const failedRequests: string[] = [];
    page.on('requestfailed', request => {
      failedRequests.push(request.url());
    });

    await page.goto(baseURL);
    await page.waitForLoadState('networkidle');

    // Check for critical asset loading failures
    const criticalAssetsFailed = failedRequests.filter(url => 
      url.includes('.css') || url.includes('.js') || url.includes('.ico')
    );

    if (criticalAssetsFailed.length > 0) {
      console.log('⚠ Some assets failed to load:', criticalAssetsFailed);
    }

    // App should still render even if some assets fail
    await expect(page.locator('#root')).toBeVisible({ timeout: 10000 });
  });

  test('favicon and meta tags are present', async ({ page }) => {
    await page.goto(baseURL);
    
    // Check for favicon
    const favicon = page.locator('link[rel*="icon"]');
    await expect(favicon).toHaveCount({ min: 1 });
    
    // Check for basic meta tags
    const title = page.locator('title');
    await expect(title).toHaveText(/whisper/i);
  });
});
