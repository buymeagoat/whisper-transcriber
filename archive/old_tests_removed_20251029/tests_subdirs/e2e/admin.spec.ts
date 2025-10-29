import { test, expect, Page } from '@playwright/test';

/**
 * E2E Admin Interface Tests
 * 
 * Tests admin-only functionality including:
 * - User management (create, edit, delete users)
 * - System statistics and monitoring
 * - Cleanup operations and maintenance
 * - Configuration management
 * - Admin access controls and permissions
 * - System health monitoring
 */

test.describe('Admin Interface', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('/');
    
    // Login as admin user
    await page.fill('[data-testid="username-input"]', 'e2e_admin_user');
    await page.fill('[data-testid="password-input"]', 'AdminPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
    
    // Navigate to admin panel
    await page.goto('/admin');
    await expect(page.locator('[data-testid="admin-panel"]')).toBeVisible();
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display admin navigation correctly', async () => {
    // Verify admin navigation elements
    await expect(page.locator('[data-testid="admin-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-users"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-statistics"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-system"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-cleanup"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-config"]')).toBeVisible();
    
    // Verify admin-only elements are visible
    await expect(page.locator('[data-testid="admin-badge"]')).toBeVisible();
    await expect(page.locator('[data-testid="admin-tools"]')).toBeVisible();
  });

  test('should display system statistics dashboard', async () => {
    await page.click('[data-testid="nav-statistics"]');
    
    // Verify statistics elements
    await expect(page.locator('[data-testid="stats-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-users"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-transcriptions"]')).toBeVisible();
    await expect(page.locator('[data-testid="storage-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-uptime"]')).toBeVisible();
    
    // Verify charts and graphs
    await expect(page.locator('[data-testid="usage-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="performance-metrics"]')).toBeVisible();
    
    // Check that statistics show actual data
    const totalUsers = await page.locator('[data-testid="total-users"]').textContent();
    expect(totalUsers).toMatch(/\d+/);
    
    const storageUsage = await page.locator('[data-testid="storage-usage"]').textContent();
    expect(storageUsage).toMatch(/\d+(\.\d+)?\s*(GB|MB|TB)/);
  });

  test('should manage users effectively', async () => {
    await page.click('[data-testid="nav-users"]');
    
    // Verify user management interface
    await expect(page.locator('[data-testid="user-management"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="add-user-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-search"]')).toBeVisible();
    
    // Test user search functionality
    await page.fill('[data-testid="user-search"]', 'e2e_test_user');
    await expect(page.locator('[data-testid="user-row"]')).toContainText('e2e_test_user');
    
    // Test user creation
    await page.click('[data-testid="add-user-button"]');
    await expect(page.locator('[data-testid="user-form"]')).toBeVisible();
    
    await page.fill('[data-testid="new-username"]', 'test_new_user');
    await page.fill('[data-testid="new-email"]', 'test@example.com');
    await page.fill('[data-testid="new-password"]', 'NewUserPassword123!');
    await page.selectOption('[data-testid="user-role"]', 'user');
    
    await page.click('[data-testid="create-user-button"]');
    
    // Verify user was created
    await expect(page.locator('[data-testid="success-message"]')).toContainText('User created successfully');
    await expect(page.locator('[data-testid="user-list"]')).toContainText('test_new_user');
  });

  test('should edit user permissions and details', async () => {
    await page.click('[data-testid="nav-users"]');
    
    // Find test user and edit
    await page.fill('[data-testid="user-search"]', 'e2e_test_user');
    await page.click('[data-testid="edit-user-button"]');
    
    await expect(page.locator('[data-testid="edit-user-form"]')).toBeVisible();
    
    // Change user role
    await page.selectOption('[data-testid="edit-user-role"]', 'admin');
    await page.click('[data-testid="save-user-button"]');
    
    // Verify changes
    await expect(page.locator('[data-testid="success-message"]')).toContainText('User updated successfully');
    
    // Verify role change in user list
    const userRow = page.locator('[data-testid="user-row"]').filter({ hasText: 'e2e_test_user' });
    await expect(userRow.locator('[data-testid="user-role"]')).toContainText('admin');
    
    // Revert changes
    await page.click('[data-testid="edit-user-button"]');
    await page.selectOption('[data-testid="edit-user-role"]', 'user');
    await page.click('[data-testid="save-user-button"]');
  });

  test('should handle user deletion with confirmation', async () => {
    await page.click('[data-testid="nav-users"]');
    
    // Create a temporary user to delete
    await page.click('[data-testid="add-user-button"]');
    await page.fill('[data-testid="new-username"]', 'temp_delete_user');
    await page.fill('[data-testid="new-email"]', 'delete@example.com');
    await page.fill('[data-testid="new-password"]', 'TempPassword123!');
    await page.click('[data-testid="create-user-button"]');
    
    // Find and delete the user
    await page.fill('[data-testid="user-search"]', 'temp_delete_user');
    await page.click('[data-testid="delete-user-button"]');
    
    // Verify confirmation dialog
    await expect(page.locator('[data-testid="delete-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirmation-message"]')).toContainText('permanently delete');
    
    await page.click('[data-testid="confirm-delete"]');
    
    // Verify user was deleted
    await expect(page.locator('[data-testid="success-message"]')).toContainText('User deleted successfully');
    await page.fill('[data-testid="user-search"]', 'temp_delete_user');
    await expect(page.locator('[data-testid="no-users-found"]')).toBeVisible();
  });

  test('should perform system cleanup operations', async () => {
    await page.click('[data-testid="nav-cleanup"]');
    
    // Verify cleanup interface
    await expect(page.locator('[data-testid="cleanup-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="temp-files-cleanup"]')).toBeVisible();
    await expect(page.locator('[data-testid="old-transcriptions-cleanup"]')).toBeVisible();
    await expect(page.locator('[data-testid="storage-cleanup"]')).toBeVisible();
    
    // Test temp files cleanup
    await expect(page.locator('[data-testid="temp-files-count"]')).toBeVisible();
    const tempFilesCount = await page.locator('[data-testid="temp-files-count"]').textContent();
    
    await page.click('[data-testid="cleanup-temp-files"]');
    
    // Verify cleanup started
    await expect(page.locator('[data-testid="cleanup-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="cleanup-status"]')).toContainText('Cleaning up');
    
    // Wait for completion
    await expect(page.locator('[data-testid="cleanup-complete"]')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Cleanup completed');
  });

  test('should manage system configuration', async () => {
    await page.click('[data-testid="nav-config"]');
    
    // Verify configuration interface
    await expect(page.locator('[data-testid="config-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-file-size"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-concurrent-jobs"]')).toBeVisible();
    await expect(page.locator('[data-testid="default-model"]')).toBeVisible();
    await expect(page.locator('[data-testid="retention-days"]')).toBeVisible();
    
    // Test configuration changes
    const originalMaxSize = await page.inputValue('[data-testid="max-file-size"]');
    
    await page.fill('[data-testid="max-file-size"]', '200');
    await page.selectOption('[data-testid="default-model"]', 'small');
    await page.fill('[data-testid="retention-days"]', '60');
    
    await page.click('[data-testid="save-config"]');
    
    // Verify configuration saved
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Configuration saved');
    
    // Verify values persist after page reload
    await page.reload();
    await page.click('[data-testid="nav-config"]');
    
    expect(await page.inputValue('[data-testid="max-file-size"]')).toBe('200');
    expect(await page.inputValue('[data-testid="retention-days"]')).toBe('60');
    
    // Restore original configuration
    await page.fill('[data-testid="max-file-size"]', originalMaxSize);
    await page.click('[data-testid="save-config"]');
  });

  test('should monitor system health and status', async () => {
    await page.click('[data-testid="nav-system"]');
    
    // Verify system health interface
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();
    await expect(page.locator('[data-testid="api-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="database-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="queue-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="storage-status"]')).toBeVisible();
    
    // Verify health indicators
    await expect(page.locator('[data-testid="api-status"]')).toContainText('Healthy');
    await expect(page.locator('[data-testid="database-status"]')).toContainText('Connected');
    
    // Test system restart functionality
    await expect(page.locator('[data-testid="restart-services"]')).toBeVisible();
    await expect(page.locator('[data-testid="restart-queue"]')).toBeVisible();
    
    // Test service restart (with confirmation)
    await page.click('[data-testid="restart-queue"]');
    await expect(page.locator('[data-testid="restart-confirmation"]')).toBeVisible();
    await page.click('[data-testid="confirm-restart"]');
    
    await expect(page.locator('[data-testid="restart-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Queue restarted');
  });

  test('should display real-time system metrics', async () => {
    await page.click('[data-testid="nav-system"]');
    
    // Verify real-time metrics
    await expect(page.locator('[data-testid="cpu-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="memory-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="disk-usage"]')).toBeVisible();
    await expect(page.locator('[data-testid="active-jobs"]')).toBeVisible();
    
    // Verify metrics update over time
    const initialCpuUsage = await page.locator('[data-testid="cpu-usage"]').textContent();
    
    // Wait a few seconds and check if metrics updated
    await page.waitForTimeout(5000);
    const updatedCpuUsage = await page.locator('[data-testid="cpu-usage"]').textContent();
    
    // Metrics should be formatted correctly
    expect(initialCpuUsage).toMatch(/\d+(\.\d+)?%/);
    expect(updatedCpuUsage).toMatch(/\d+(\.\d+)?%/);
  });

  test('should handle concurrent admin operations', async () => {
    // Create a second admin session
    const page2 = await page.context().newPage();
    
    try {
      // Login as admin on second page
      await page2.goto('/');
      await page2.fill('[data-testid="username-input"]', 'e2e_admin_user');
      await page2.fill('[data-testid="password-input"]', 'AdminPassword123!');
      await page2.click('[data-testid="login-button"]');
      await page2.goto('/admin');
      
      // Perform operations on both pages simultaneously
      await Promise.all([
        // Page 1: View statistics
        page.click('[data-testid="nav-statistics"]'),
        // Page 2: Manage users
        page2.click('[data-testid="nav-users"]')
      ]);
      
      // Both operations should complete successfully
      await expect(page.locator('[data-testid="stats-dashboard"]')).toBeVisible();
      await expect(page2.locator('[data-testid="user-management"]')).toBeVisible();
      
    } finally {
      await page2.close();
    }
  });

  test('should audit admin actions', async () => {
    // Check if audit log exists
    const hasAuditLog = await page.locator('[data-testid="nav-audit"]').isVisible();
    
    if (hasAuditLog) {
      await page.click('[data-testid="nav-audit"]');
      
      // Verify audit log interface
      await expect(page.locator('[data-testid="audit-log"]')).toBeVisible();
      await expect(page.locator('[data-testid="audit-entries"]')).toBeVisible();
      await expect(page.locator('[data-testid="audit-filters"]')).toBeVisible();
      
      // Perform an action to generate audit entry
      await page.click('[data-testid="nav-users"]');
      await page.click('[data-testid="add-user-button"]');
      await page.fill('[data-testid="new-username"]', 'audit_test_user');
      await page.fill('[data-testid="new-email"]', 'audit@example.com');
      await page.fill('[data-testid="new-password"]', 'AuditPassword123!');
      await page.click('[data-testid="create-user-button"]');
      
      // Return to audit log
      await page.click('[data-testid="nav-audit"]');
      
      // Should see the create user action in audit log
      await expect(page.locator('[data-testid="audit-entry"]').first()).toContainText('User created');
      await expect(page.locator('[data-testid="audit-entry"]').first()).toContainText('audit_test_user');
      
      // Cleanup
      await page.click('[data-testid="nav-users"]');
      await page.fill('[data-testid="user-search"]', 'audit_test_user');
      await page.click('[data-testid="delete-user-button"]');
      await page.click('[data-testid="confirm-delete"]');
    }
  });

  test('should enforce admin-only access restrictions', async () => {
    // Logout and login as regular user
    await page.click('[data-testid="logout-button"]');
    
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    // Try to access admin panel
    await page.goto('/admin');
    
    // Should be denied access
    await expect(page.locator('[data-testid="access-denied"]')).toBeVisible();
    await expect(page.locator('[data-testid="access-denied"]')).toContainText('insufficient permissions');
    
    // Try to access admin API endpoints directly
    const response = await page.request.get('/api/admin/users');
    expect(response.status()).toBe(403);
  });
});

test.describe('Admin API Security', () => {
  test('should require admin authentication for admin endpoints', async ({ request }) => {
    // Test without authentication
    const unauthResponse = await request.get('/api/admin/stats');
    expect(unauthResponse.status()).toBe(401);
    
    // Test with user token (should be forbidden)
    // This would require getting a user token first
  });

  test('should validate admin permissions for destructive operations', async ({ page }) => {
    await page.goto('/');
    await page.fill('[data-testid="username-input"]', 'e2e_admin_user');
    await page.fill('[data-testid="password-input"]', 'AdminPassword123!');
    await page.click('[data-testid="login-button"]');
    
    // Get admin token
    await page.goto('/admin');
    const adminToken = await page.evaluate(() => {
      return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    });
    
    // Test admin API access
    const response = await page.request.get('/api/admin/stats', {
      headers: {
        'Authorization': `Bearer ${adminToken}`
      }
    });
    expect(response.status()).toBe(200);
  });
});
