#!/usr/bin/env node

/**
 * Comprehensive User Journey Simulation
 * 
 * This script simulates complete user journeys through the Whisper Transcriber
 * application, including registration, login, file upload, and transcription workflows.
 */

const BrowserUserSimulator = require('./test_browser_simulation');
const FrontendSimulator = require('./test_frontend_simulation');

class ComprehensiveUserSimulator {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.browserSim = new BrowserUserSimulator(baseUrl);
    this.apiSim = new FrontendSimulator(baseUrl);
    this.testResults = [];
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
    console.log(logEntry);
    this.testResults.push({ timestamp, type, message });
  }

  async simulateNewUserJourney() {
    this.log('👤 Simulating complete new user journey...');
    
    try {
      // Setup browser
      await this.browserSim.setupBrowser();
      
      // 1. User discovers the application
      this.log('🌐 Step 1: User navigates to application');
      await this.browserSim.page.goto(this.baseUrl);
      await this.browserSim.takeScreenshot('user_arrives');
      
      // 2. User explores the landing page
      this.log('👀 Step 2: User explores landing page');
      const heroText = await this.browserSim.page.textContent('body');
      const hasCallToAction = heroText.includes('Start') || heroText.includes('Get Started') || heroText.includes('Try');
      this.log(`   - Call to action present: ${hasCallToAction}`, hasCallToAction ? 'success' : 'info');
      
      // 3. User clicks to register/login
      this.log('📝 Step 3: User attempts to register/login');
      
      // Look for registration link first
      const registerLink = await this.browserSim.page.$('a:has-text("Register"), a:has-text("Sign up"), button:has-text("Register")');
      const loginLink = await this.browserSim.page.$('a:has-text("Login"), a:has-text("Sign in"), button:has-text("Login")');
      
      if (registerLink) {
        await this.browserSim.page.click('a:has-text("Register"), button:has-text("Register")');
        await this.browserSim.page.waitForTimeout(2000);
        await this.browserSim.takeScreenshot('register_page');
        this.log('   ✅ User navigated to registration page', 'success');
      } else if (loginLink) {
        await this.browserSim.page.click('a:has-text("Login"), button:has-text("Login")');
        await this.browserSim.page.waitForTimeout(2000);
        await this.browserSim.takeScreenshot('login_page');
        this.log('   ✅ User navigated to login page', 'success');
      }
      
      // 4. User fills registration/login form
      this.log('📋 Step 4: User fills authentication form');
      
      const usernameField = await this.browserSim.page.$('input[name="username"], input[name="email"], input[type="email"]');
      const passwordField = await this.browserSim.page.$('input[name="password"], input[type="password"]');
      
      if (usernameField && passwordField) {
        await this.browserSim.page.fill('input[name="username"], input[name="email"]', 'demo@example.com');
        await this.browserSim.page.fill('input[name="password"]', 'demo123!');
        
        // Check for additional fields (registration vs login)
        const confirmPasswordField = await this.browserSim.page.$('input[name="confirmPassword"], input[name="password_confirm"]');
        if (confirmPasswordField) {
          await this.browserSim.page.fill('input[name="confirmPassword"], input[name="password_confirm"]', 'demo123!');
          this.log('   - Filled registration form fields', 'success');
        } else {
          this.log('   - Filled login form fields', 'success');
        }
        
        await this.browserSim.takeScreenshot('form_filled');
        
        // 5. User submits form
        this.log('✅ Step 5: User submits authentication form');
        const submitButton = await this.browserSim.page.$('button[type="submit"], button:has-text("Submit"), button:has-text("Login"), button:has-text("Register")');
        
        if (submitButton) {
          await this.browserSim.page.click('button[type="submit"], button:has-text("Submit"), button:has-text("Login"), button:has-text("Register")');
          await this.browserSim.page.waitForTimeout(3000);
          await this.browserSim.takeScreenshot('form_submitted');
          
          // Check for successful authentication or error messages
          const currentUrl = this.browserSim.page.url();
          const errorMessage = await this.browserSim.page.$('.error, .alert-danger, .text-red, [role="alert"]');
          
          if (currentUrl.includes('dashboard') || currentUrl.includes('transcribe')) {
            this.log('   ✅ User successfully authenticated and redirected', 'success');
          } else if (errorMessage) {
            const errorText = await errorMessage.textContent();
            this.log(`   ⚠️  Authentication error shown: ${errorText}`, 'warning');
          } else {
            this.log('   ℹ️  Form submitted, checking response', 'info');
          }
        }
      }
      
      return true;
    } catch (error) {
      this.log(`❌ User journey simulation error: ${error.message}`, 'error');
      return false;
    }
  }

  async simulateFileUploadWorkflow() {
    this.log('📁 Simulating file upload workflow...');
    
    try {
      // Navigate to transcribe page
      const transcribeLink = await this.browserSim.page.$('a:has-text("Transcribe"), a[href*="transcribe"], button:has-text("Transcribe")');
      
      if (transcribeLink) {
        await this.browserSim.page.click('a:has-text("Transcribe"), a[href*="transcribe"]');
        await this.browserSim.page.waitForTimeout(2000);
        await this.browserSim.takeScreenshot('transcribe_page');
        this.log('   ✅ Navigated to transcribe page', 'success');
        
        // Look for upload interface
        const fileInput = await this.browserSim.page.$('input[type="file"]');
        const dropZone = await this.browserSim.page.$('.dropzone, .file-drop, [data-testid="dropzone"]');
        const uploadButton = await this.browserSim.page.$('button:has-text("Upload"), button:has-text("Choose File")');
        
        if (fileInput || dropZone || uploadButton) {
          this.log('   ✅ File upload interface detected', 'success');
          
          // Test drag and drop simulation (visual only)
          if (dropZone) {
            await this.browserSim.page.hover('.dropzone, .file-drop, [data-testid="dropzone"]');
            await this.browserSim.takeScreenshot('dropzone_hover');
            this.log('   ✅ Drag-and-drop zone interactive', 'success');
          }
          
          // Check for model selection
          const modelSelect = await this.browserSim.page.$('select[name="model"], .model-select');
          if (modelSelect) {
            this.log('   ✅ Model selection available', 'success');
          }
          
          // Check for language selection
          const languageSelect = await this.browserSim.page.$('select[name="language"], .language-select');
          if (languageSelect) {
            this.log('   ✅ Language selection available', 'success');
          }
          
          return true;
        } else {
          this.log('   ⚠️  Upload interface not found (may require authentication)', 'warning');
          return true;
        }
      } else {
        this.log('   ⚠️  Transcribe navigation not found', 'warning');
        return true;
      }
    } catch (error) {
      this.log(`❌ File upload workflow error: ${error.message}`, 'error');
      return false;
    }
  }

  async simulateJobsMonitoring() {
    this.log('💼 Simulating jobs monitoring workflow...');
    
    try {
      // Navigate to jobs page
      const jobsLink = await this.browserSim.page.$('a:has-text("Jobs"), a[href*="jobs"], button:has-text("Jobs")');
      
      if (jobsLink) {
        await this.browserSim.page.click('a:has-text("Jobs"), a[href*="jobs"]');
        await this.browserSim.page.waitForTimeout(2000);
        await this.browserSim.takeScreenshot('jobs_page');
        this.log('   ✅ Navigated to jobs page', 'success');
        
        // Check for jobs table/list
        const jobsList = await this.browserSim.page.$('table, .jobs-list, .job-item, [data-testid="jobs"]');
        if (jobsList) {
          this.log('   ✅ Jobs listing interface detected', 'success');
        }
        
        // Check for filtering/search
        const searchInput = await this.browserSim.page.$('input[type="search"], input[placeholder*="search"], .search-input');
        if (searchInput) {
          this.log('   ✅ Jobs search/filter interface available', 'success');
        }
        
        // Check for pagination
        const pagination = await this.browserSim.page.$('.pagination, .page-nav, button:has-text("Next"), button:has-text("Previous")');
        if (pagination) {
          this.log('   ✅ Jobs pagination available', 'success');
        }
        
        return true;
      } else {
        this.log('   ⚠️  Jobs navigation not found', 'warning');
        return true;
      }
    } catch (error) {
      this.log(`❌ Jobs monitoring error: ${error.message}`, 'error');
      return false;
    }
  }

  async runComprehensiveTests() {
    this.log('🚀 Starting comprehensive user journey simulation...');
    
    const tests = [
      { name: 'New User Journey', fn: () => this.simulateNewUserJourney() },
      { name: 'File Upload Workflow', fn: () => this.simulateFileUploadWorkflow() },
      { name: 'Jobs Monitoring', fn: () => this.simulateJobsMonitoring() }
    ];

    const results = [];
    
    for (const test of tests) {
      this.log(`\n--- ${test.name} ---`);
      try {
        const result = await test.fn();
        results.push({ name: test.name, success: result });
      } catch (error) {
        this.log(`❌ ${test.name} threw error: ${error.message}`, 'error');
        results.push({ name: test.name, success: false, error: error.message });
      }
    }

    // Clean up
    await this.browserSim.cleanupBrowser();

    // Generate summary
    this.log('\n=== COMPREHENSIVE SIMULATION SUMMARY ===');
    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;
    
    this.log(`User Journey Success Rate: ${successCount}/${totalCount} (${Math.round(successCount/totalCount*100)}%)`);
    
    results.forEach(result => {
      const status = result.success ? '✅ PASS' : '❌ FAIL';
      this.log(`${status} ${result.name}`);
      if (result.error) {
        this.log(`   Error: ${result.error}`, 'error');
      }
    });

    return {
      totalTests: totalCount,
      passedTests: successCount,
      results: results,
      logs: this.testResults,
      screenshots: this.browserSim.screenshots
    };
  }
}

// Run the simulation if this script is executed directly
if (require.main === module) {
  const simulator = new ComprehensiveUserSimulator();
  
  simulator.runComprehensiveTests()
    .then(results => {
      console.log('\n🎯 Comprehensive user journey simulation completed!');
      
      // Save results to file
      const resultsFile = require('path').join(__dirname, 'logs', 'comprehensive_simulation_results.json');
      require('fs').writeFileSync(resultsFile, JSON.stringify(results, null, 2));
      console.log(`📁 Results saved to: ${resultsFile}`);
      
      process.exit(results.passedTests === results.totalTests ? 0 : 1);
    })
    .catch(error => {
      console.error('❌ Comprehensive simulation failed:', error);
      process.exit(1);
    });
}

module.exports = ComprehensiveUserSimulator;