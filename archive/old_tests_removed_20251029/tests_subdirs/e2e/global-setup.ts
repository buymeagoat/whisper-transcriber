import { chromium, FullConfig, Page } from '@playwright/test';

/**
 * Global setup for Playwright tests
 * This runs once before all tests and sets up the test environment
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Setting up E2E test environment...');
  
  // Create a browser instance for authentication setup
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the application to be ready
    console.log('⏳ Waiting for application to be ready...');
    await page.goto(config.projects[0].use.baseURL || 'http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Create test admin user if needed
    console.log('👤 Setting up test users...');
    await setupTestUsers(page);
    
    console.log('✅ E2E test environment setup complete');
    
  } catch (error) {
    console.error('❌ Failed to setup E2E test environment:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

/**
 * Set up test users for E2E testing
 */
async function setupTestUsers(page: Page) {
  const testUsers = [
    {
      username: 'e2e_test_user',
      email: 'e2e_test@example.com', 
      password: 'test_password_123'
    },
    {
      username: 'e2e_admin_user',
      email: 'e2e_admin@example.com',
      password: 'admin_password_123'
    }
  ];
  
  for (const user of testUsers) {
    try {
      // Navigate to registration page
      await page.goto('/register');
      
      // Check if user already exists by trying to register
      await page.fill('[data-testid="username-input"]', user.username);
      await page.fill('[data-testid="email-input"]', user.email);
      await page.fill('[data-testid="password-input"]', user.password);
      await page.click('[data-testid="register-button"]');
      
      // Wait a bit for the registration to complete
      await page.waitForTimeout(1000);
      
      console.log(`✅ Test user ${user.username} ready`);
    } catch (error) {
      console.log(`ℹ️  Test user ${user.username} might already exist`);
    }
  }
}

export default globalSetup;
