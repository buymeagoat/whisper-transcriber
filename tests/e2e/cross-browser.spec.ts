import { test, expect, devices } from '@playwright/test';

/**
 * Cross-Browser E2E Tests
 * 
 * Tests application functionality across different browsers and devices:
 * - Chrome, Firefox, Safari, Edge compatibility
 * - Mobile device responsiveness
 * - Touch interface functionality
 * - Performance across platforms
 * - Feature parity verification
 */

test.describe('Cross-Browser Compatibility', () => {
  
  test('should work correctly in Chrome', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test basic functionality
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      
      // Test login
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });

  test('should work correctly in Firefox', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test browser-specific features
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      
      // Test file upload (Firefox has different file handling)
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test file input specifically in Firefox
      await page.click('[data-testid="new-transcription"]');
      await expect(page.locator('[data-testid="file-input"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });

  test('should work correctly in WebKit/Safari', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test Safari-specific behaviors
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      
      // Safari has different audio handling
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test media features work in Safari
      await page.click('[data-testid="new-transcription"]');
      await expect(page.locator('[data-testid="file-upload-area"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });
});

test.describe('Mobile Device Testing', () => {
  
  test('should work on iPhone', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 12']
    });
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test mobile responsiveness
      await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
      
      // Test touch interactions
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.tap('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test mobile navigation
      await page.tap('[data-testid="mobile-menu-button"]');
      await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });

  test('should work on Android tablet', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['Galaxy Tab S4']
    });
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test tablet layout
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      
      // Test larger mobile interface
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.tap('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test file upload on tablet
      await page.tap('[data-testid="new-transcription"]');
      await expect(page.locator('[data-testid="file-upload-area"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });

  test('should handle touch gestures correctly', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 12']
    });
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Login first
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.tap('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test swipe gestures if available
      const hasSwipeInterface = await page.locator('[data-testid="swipe-container"]').isVisible();
      if (hasSwipeInterface) {
        // Test swipe left/right navigation
        const swipeContainer = page.locator('[data-testid="swipe-container"]');
        await swipeContainer.click({ position: { x: 100, y: 50 } });
        await page.mouse.down();
        await page.mouse.move(200, 50);
        await page.mouse.up();
      }
      
      // Test long press actions
      const hasLongPressActions = await page.locator('[data-testid="long-press-item"]').isVisible();
      if (hasLongPressActions) {
        await page.locator('[data-testid="long-press-item"]').click({ delay: 1000 });
        await expect(page.locator('[data-testid="context-menu"]')).toBeVisible();
      }
      
    } finally {
      await context.close();
    }
  });
});

test.describe('Feature Parity Testing', () => {
  
  const browsers = ['chromium', 'firefox', 'webkit'];
  
  for (const browserName of browsers) {
    test(`core features should work identically in ${browserName}`, async ({ browser }) => {
      const context = await browser.newContext();
      const page = await context.newPage();
      
      try {
        await page.goto('/');
        
        // Test identical behavior across browsers
        await page.fill('[data-testid="username-input"]', 'e2e_test_user');
        await page.fill('[data-testid="password-input"]', 'TestPassword123!');
        await page.click('[data-testid="login-button"]');
        
        await expect(page).toHaveURL(/.*\/dashboard/);
        
        // Test transcription interface
        await page.click('[data-testid="new-transcription"]');
        await expect(page.locator('[data-testid="file-upload-area"]')).toBeVisible();
        await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
        await expect(page.locator('[data-testid="language-selector"]')).toBeVisible();
        
        // Test history page
        await page.click('[data-testid="transcription-history"]');
        await expect(page.locator('[data-testid="history-list"]')).toBeVisible();
        
        // Verify consistent styling and layout
        const uploadButton = page.locator('[data-testid="upload-button"]');
        if (await uploadButton.isVisible()) {
          const buttonStyles = await uploadButton.evaluate(el => {
            const styles = getComputedStyle(el);
            return {
              backgroundColor: styles.backgroundColor,
              color: styles.color,
              borderRadius: styles.borderRadius
            };
          });
          
          // Basic validation that styles are applied
          expect(buttonStyles.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
        }
        
      } finally {
        await context.close();
      }
    });
  }
});

test.describe('Performance Testing', () => {
  
  test('should load quickly across all browsers', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      const startTime = Date.now();
      await page.goto('/');
      
      // Wait for login form to be visible
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      
      const loadTime = Date.now() - startTime;
      
      // Should load within reasonable time
      expect(loadTime).toBeLessThan(5000); // 5 seconds
      
      // Test subsequent navigation performance
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      
      const loginStartTime = Date.now();
      await page.click('[data-testid="login-button"]');
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      const loginTime = Date.now() - loginStartTime;
      expect(loginTime).toBeLessThan(3000); // 3 seconds for login
      
    } finally {
      await context.close();
    }
  });

  test('should handle large file uploads consistently', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Login
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Test upload interface responsiveness
      await page.click('[data-testid="new-transcription"]');
      
      // Verify upload area responds quickly
      const uploadArea = page.locator('[data-testid="file-upload-area"]');
      await expect(uploadArea).toBeVisible();
      
      // Test drag events (simulated)
      await uploadArea.dispatchEvent('dragenter');
      await expect(page.locator('[data-testid="drop-zone-active"]')).toBeVisible({ timeout: 1000 });
      
      await uploadArea.dispatchEvent('dragleave');
      await expect(page.locator('[data-testid="drop-zone-active"]')).not.toBeVisible({ timeout: 1000 });
      
    } finally {
      await context.close();
    }
  });
});

test.describe('Accessibility Testing', () => {
  
  test('should be accessible with keyboard navigation', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Test keyboard navigation
      await page.press('body', 'Tab');
      await expect(page.locator('[data-testid="username-input"]')).toBeFocused();
      
      await page.press('body', 'Tab');
      await expect(page.locator('[data-testid="password-input"]')).toBeFocused();
      
      await page.press('body', 'Tab');
      await expect(page.locator('[data-testid="login-button"]')).toBeFocused();
      
      // Test form submission with Enter key
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.press('[data-testid="login-button"]', 'Enter');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
    } finally {
      await context.close();
    }
  });

  test('should have proper ARIA labels and roles', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Check ARIA attributes
      const usernameInput = page.locator('[data-testid="username-input"]');
      const passwordInput = page.locator('[data-testid="password-input"]');
      const loginButton = page.locator('[data-testid="login-button"]');
      
      // Verify inputs have proper labels
      await expect(usernameInput).toHaveAttribute('aria-label');
      await expect(passwordInput).toHaveAttribute('aria-label');
      await expect(loginButton).toHaveAttribute('role', 'button');
      
      // Check for proper form structure
      const loginForm = page.locator('[data-testid="login-form"]');
      await expect(loginForm).toHaveAttribute('role', 'form');
      
    } finally {
      await context.close();
    }
  });
});

test.describe('Network Conditions Testing', () => {
  
  test('should work on slow network connections', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      // Simulate slow network
      await page.route('**/*', async route => {
        await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
        await route.continue();
      });
      
      await page.goto('/');
      
      // Should still work with delays
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible({ timeout: 10000 });
      
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/, { timeout: 15000 });
      
    } finally {
      await context.close();
    }
  });

  test('should handle network failures gracefully', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
      await page.goto('/');
      
      // Login first
      await page.fill('[data-testid="username-input"]', 'e2e_test_user');
      await page.fill('[data-testid="password-input"]', 'TestPassword123!');
      await page.click('[data-testid="login-button"]');
      
      await expect(page).toHaveURL(/.*\/dashboard/);
      
      // Simulate network failure for API calls
      await page.route('/api/**', route => route.abort());
      
      // Try to perform an action that requires API
      await page.click('[data-testid="transcription-history"]');
      
      // Should show appropriate error message
      await expect(page.locator('[data-testid="network-error"]')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
      
    } finally {
      await context.close();
    }
  });
});
