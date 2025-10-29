import { test, expect, Page } from '@playwright/test';

/**
 * E2E Authentication Tests
 * 
 * Tests comprehensive authentication workflow including:
 * - User login/logout functionality
 * - Session persistence and management
 * - Role-based access controls
 * - JWT token handling
 * - Unauthorized access scenarios
 * - Password security validation
 */

test.describe('Authentication Flow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('/');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display login form on initial visit', async () => {
    // Verify login form is visible
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="username-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
    
    // Verify no authenticated content is visible
    await expect(page.locator('[data-testid="main-content"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).not.toBeVisible();
  });

  test('should successfully login with valid credentials', async () => {
    // Fill login form
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    
    // Submit login
    await page.click('[data-testid="login-button"]');
    
    // Wait for redirect and verify successful login
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-menu"]')).toContainText('e2e_test_user');
    
    // Verify login form is hidden
    await expect(page.locator('[data-testid="login-form"]')).not.toBeVisible();
  });

  test('should reject invalid credentials', async () => {
    // Test invalid username
    await page.fill('[data-testid="username-input"]', 'invalid_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    await expect(page).toHaveURL(/.*\/$/); // Should stay on login page
    
    // Clear form and test invalid password
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'wrong_password');
    await page.click('[data-testid="login-button"]');
    
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
    await expect(page).toHaveURL(/.*\/$/);
  });

  test('should handle empty form submission', async () => {
    // Submit empty form
    await page.click('[data-testid="login-button"]');
    
    // Verify validation errors
    await expect(page.locator('[data-testid="username-error"]')).toContainText('Username is required');
    await expect(page.locator('[data-testid="password-error"]')).toContainText('Password is required');
    await expect(page).toHaveURL(/.*\/$/);
  });

  test('should successfully logout', async () => {
    // Login first
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Logout
    await page.click('[data-testid="logout-button"]');
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/.*\/$/);
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="main-content"]')).not.toBeVisible();
  });

  test('should persist session across page refreshes', async () => {
    // Login
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Refresh page
    await page.reload();
    
    // Verify still authenticated
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
  });

  test('should handle session expiration', async () => {
    // Login
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Simulate session expiration by clearing storage
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Try to access protected resource
    await page.goto('/dashboard');
    
    // Should be redirected to login
    await expect(page).toHaveURL(/.*\/$/);
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });

  test('should enforce role-based access controls', async () => {
    // Login as regular user
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Try to access admin-only pages
    await page.goto('/admin');
    
    // Should be denied access
    await expect(page.locator('[data-testid="access-denied"]')).toBeVisible();
    await expect(page.locator('[data-testid="access-denied"]')).toContainText('insufficient permissions');
  });

  test('should allow admin access to admin features', async () => {
    // Login as admin user
    await page.fill('[data-testid="username-input"]', 'e2e_admin_user');
    await page.fill('[data-testid="password-input"]', 'AdminPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Access admin pages
    await page.goto('/admin');
    
    // Should have access
    await expect(page.locator('[data-testid="admin-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="admin-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-management"]')).toBeVisible();
  });

  test('should protect API endpoints based on authentication', async () => {
    // Test unauthenticated API access
    const response = await page.request.get('/api/jobs');
    expect(response.status()).toBe(401);
    
    // Login and test authenticated API access
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Extract auth token from page context
    const authToken = await page.evaluate(() => {
      return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    });
    
    expect(authToken).toBeTruthy();
    
    // Test authenticated API access
    const authResponse = await page.request.get('/api/jobs', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    expect(authResponse.status()).toBe(200);
  });

  test('should handle concurrent login sessions', async () => {
    // Create second page for concurrent session
    const page2 = await page.context().newPage();
    
    try {
      // Login on both pages
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await page2.goto('/');
      await page2.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page2.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page2.click('[data-testid="login-button"]');
      
      // Both should be authenticated
      await expect(page).toHaveURL(/.*\/dashboard/);
      await expect(page2).toHaveURL(/.*\/dashboard/);
      
      // Logout from first page
      await page.click('[data-testid="logout-button"]');
      
      // Check if second session is affected
      await page2.reload();
      await expect(page2).toHaveURL(/.*\/dashboard/);
      
    } finally {
      await page2.close();
    }
  });

  test('should validate password strength requirements', async () => {
    // Navigate to registration/password change if available
    const hasRegistration = await page.locator('[data-testid="register-link"]').isVisible();
    
    if (hasRegistration) {
      await page.click('[data-testid="register-link"]');
      
      // Test weak passwords
      await page.fill('[data-testid="password-input"]', '123');
      await expect(page.locator('[data-testid="password-strength"]')).toContainText('weak');
      
      await page.fill('[data-testid="password-input"]', 'password');
      await expect(page.locator('[data-testid="password-strength"]')).toContainText('weak');
      
      // Test strong password
      await page.fill('[data-testid="password-input"]', 'StrongPassword123!');
      await expect(page.locator('[data-testid="password-strength"]')).toContainText('strong');
    }
  });

  test('should handle login rate limiting', async () => {
    // Attempt multiple failed logins rapidly
    for (let i = 0; i < 5; i++) {
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'wrong_password');
      await page.click('[data-testid="login-button"]');
      await page.waitForTimeout(100); // Small delay
    }
    
    // Should show rate limiting message
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="rate-limit-message"]')).toContainText('too many attempts');
    
    // Login button should be disabled temporarily
    await expect(page.locator('[data-testid="login-button"]')).toBeDisabled();
  });
});

test.describe('Authentication Security', () => {
  test('should not expose sensitive information in client', async ({ page }) => {
    await page.goto('/');
    
    // Check that sensitive information is not in page source
    const content = await page.content();
    expect(content).not.toContain('SECRET_KEY');
    expect(content).not.toContain('JWT_SECRET');
    expect(content).not.toContain('DATABASE_URL');
    expect(content).not.toContain('password');
  });

  test('should use HTTPS in production', async ({ page }) => {
    // This test would be environment-specific
    const url = page.url();
    if (process.env.NODE_ENV === 'production') {
      expect(url).toMatch(/^https:/);
    }
  });

  test('should handle CORS properly', async ({ page }) => {
    // Test that CORS headers are present and correct
    const response = await page.request.get('/api/health');
    const headers = response.headers();
    
    expect(headers['access-control-allow-origin']).toBeDefined();
    expect(headers['access-control-allow-methods']).toBeDefined();
    expect(headers['access-control-allow-headers']).toBeDefined();
  });
});
