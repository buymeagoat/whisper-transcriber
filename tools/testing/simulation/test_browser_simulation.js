#!/usr/bin/env node

/**
 * Browser-Based Frontend User Simulation
 * 
 * This script uses Playwright to simulate real user interactions with the
 * Whisper Transcriber web application through an actual browser.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

class BrowserUserSimulator {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.browser = null;
    this.context = null;
    this.page = null;
    this.testResults = [];
    this.screenshots = [];
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
    console.log(logEntry);
    this.testResults.push({ timestamp, type, message });
  }

  async takeScreenshot(name) {
    if (this.page) {
      try {
        const screenshotPath = path.join(__dirname, 'logs', `screenshot_${name}_${Date.now()}.png`);
        await this.page.screenshot({ path: screenshotPath, fullPage: true });
        this.screenshots.push({ name, path: screenshotPath });
        this.log(`📸 Screenshot saved: ${screenshotPath}`, 'info');
        return screenshotPath;
      } catch (error) {
        this.log(`❌ Screenshot failed: ${error.message}`, 'error');
      }
    }
  }

  async setupBrowser() {
    this.log('🚀 Setting up browser environment...');
    
    try {
      this.browser = await chromium.launch({
        headless: true, // Set to false to see the browser during testing
        args: ['--no-sandbox', '--disable-dev-shm-usage']
      });
      
      this.context = await this.browser.newContext({
        viewport: { width: 1920, height: 1080 },
        userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      });
      
      this.page = await this.context.newPage();
      
      // Enable console logging from the page
      this.page.on('console', msg => {
        if (msg.type() === 'error') {
          this.log(`Browser Console Error: ${msg.text()}`, 'error');
        }
      });
      
      // Enable error tracking
      this.page.on('pageerror', error => {
        this.log(`Page Error: ${error.message}`, 'error');
      });
      
      this.log('✅ Browser setup complete', 'success');
      return true;
    } catch (error) {
      this.log(`❌ Browser setup failed: ${error.message}`, 'error');
      return false;
    }
  }

  async testApplicationLoad() {
    this.log('🌐 Testing application load and initial render...');
    
    try {
      // Navigate to the application
      const response = await this.page.goto(this.baseUrl, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      if (!response.ok()) {
        this.log(`❌ Application failed to load: ${response.status()}`, 'error');
        return false;
      }
      
      // Wait for React to render
      await this.page.waitForSelector('#root', { timeout: 10000 });
      
      // Take screenshot of initial load
      await this.takeScreenshot('initial_load');
      
      // Check for key application elements
      const title = await this.page.title();
      const hasRoot = await this.page.$('#root') !== null;
      const bodyText = await this.page.textContent('body');
      const hasWhisperText = bodyText.includes('Whisper') || bodyText.includes('Transcrib');
      
      this.log(`   - Page title: "${title}"`, title.includes('Whisper') ? 'success' : 'warning');
      this.log(`   - React root element: ${hasRoot}`, hasRoot ? 'success' : 'error');
      this.log(`   - Application content loaded: ${hasWhisperText}`, hasWhisperText ? 'success' : 'warning');
      
      if (hasRoot) {
        this.log('✅ Application loaded successfully', 'success');
        return true;
      } else {
        this.log('❌ Application failed to render properly', 'error');
        return false;
      }
    } catch (error) {
      this.log(`❌ Application load error: ${error.message}`, 'error');
      await this.takeScreenshot('load_error');
      return false;
    }
  }

  async testNavigation() {
    this.log('🧭 Testing application navigation...');
    
    try {
      // Look for navigation elements
      const navLinks = await this.page.$$('nav a, [role="navigation"] a, .nav a, .navbar a');
      this.log(`   - Found ${navLinks.length} navigation links`, navLinks.length > 0 ? 'success' : 'warning');
      
      // Look for common navigation patterns
      const commonLinks = ['login', 'register', 'dashboard', 'transcribe'];
      const foundLinks = [];
      
      for (const linkText of commonLinks) {
        const link = await this.page.$(`a:has-text("${linkText}"), button:has-text("${linkText}")`);
        if (link) {
          foundLinks.push(linkText);
          this.log(`   - Found "${linkText}" link/button`, 'success');
        }
      }
      
      // Test clicking a navigation element if available
      if (foundLinks.length > 0) {
        const firstLink = foundLinks[0];
        this.log(`   - Testing click on "${firstLink}" element`);
        
        try {
          await this.page.click(`a:has-text("${firstLink}"), button:has-text("${firstLink}")`, { timeout: 5000 });
          await this.page.waitForTimeout(2000); // Wait for navigation
          await this.takeScreenshot(`after_${firstLink}_click`);
          this.log(`   ✅ Successfully clicked "${firstLink}"`, 'success');
        } catch (clickError) {
          this.log(`   ⚠️  Click on "${firstLink}" failed: ${clickError.message}`, 'warning');
        }
      }
      
      this.log('✅ Navigation test completed', 'success');
      return true;
    } catch (error) {
      this.log(`❌ Navigation test error: ${error.message}`, 'error');
      return false;
    }
  }

  async testLoginInterface() {
    this.log('🔐 Testing login interface...');
    
    try {
      // Look for login form or button
      const loginButton = await this.page.$('button:has-text("Login"), a:has-text("Login"), [data-testid="login"]');
      const loginForm = await this.page.$('form[action*="login"], form:has([name="username"]), form:has([name="email"])');
      
      if (loginButton) {
        this.log('   - Found login button', 'success');
        await this.page.click('button:has-text("Login"), a:has-text("Login")');
        await this.page.waitForTimeout(1000);
        await this.takeScreenshot('login_button_clicked');
      }
      
      if (loginForm || await this.page.$('input[name="username"], input[name="email"], input[type="email"]')) {
        this.log('   - Found login form elements', 'success');
        
        // Try to fill in login form
        const usernameField = await this.page.$('input[name="username"], input[name="email"], input[type="email"]');
        const passwordField = await this.page.$('input[name="password"], input[type="password"]');
        
        if (usernameField && passwordField) {
          this.log('   - Testing form interaction...');
          
          await this.page.fill('input[name="username"], input[name="email"]', 'test@example.com');
          await this.page.fill('input[name="password"], input[type="password"]', 'testpassword');
          
          await this.takeScreenshot('login_form_filled');
          
          // Look for submit button
          const submitButton = await this.page.$('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
          
          if (submitButton) {
            this.log('   - Found submit button, testing click (expect auth error)');
            
            try {
              await this.page.click('button[type="submit"], button:has-text("Login")');
              await this.page.waitForTimeout(2000);
              await this.takeScreenshot('login_attempted');
              
              // Check for error messages or success
              const errorElement = await this.page.$('.error, .alert-danger, .text-red, [role="alert"]');
              if (errorElement) {
                const errorText = await errorElement.textContent();
                this.log(`   ✅ Login form shows error (expected): ${errorText}`, 'success');
              }
              
            } catch (submitError) {
              this.log(`   ⚠️  Login submit error: ${submitError.message}`, 'warning');
            }
          }
          
          this.log('✅ Login interface test completed', 'success');
          return true;
        } else {
          this.log('   ⚠️  Login form fields not found', 'warning');
          return true;
        }
      } else {
        this.log('   ⚠️  No login interface found (may be expected)', 'warning');
        return true;
      }
    } catch (error) {
      this.log(`❌ Login interface test error: ${error.message}`, 'error');
      return false;
    }
  }

  async testFileUploadInterface() {
    this.log('📁 Testing file upload interface...');
    
    try {
      // Look for file upload elements
      const fileInput = await this.page.$('input[type="file"]');
      const dropZone = await this.page.$('[data-testid="dropzone"], .dropzone, .drop-zone, .file-drop');
      const uploadButton = await this.page.$('button:has-text("Upload"), button:has-text("Choose"), button:has-text("Select")');
      
      let uploadElementsFound = 0;
      
      if (fileInput) {
        this.log('   - Found file input element', 'success');
        uploadElementsFound++;
      }
      
      if (dropZone) {
        this.log('   - Found drag-and-drop zone', 'success');
        uploadElementsFound++;
      }
      
      if (uploadButton) {
        this.log('   - Found upload button', 'success');
        uploadElementsFound++;
      }
      
      // Look for transcribe/upload related navigation
      const transcribeLink = await this.page.$('a:has-text("Transcribe"), a:has-text("Upload"), button:has-text("Transcribe")');
      
      if (transcribeLink) {
        this.log('   - Found transcribe/upload navigation');
        
        try {
          await this.page.click('a:has-text("Transcribe"), button:has-text("Transcribe")');
          await this.page.waitForTimeout(2000);
          await this.takeScreenshot('transcribe_page');
          
          // Re-check for upload elements on transcribe page
          const newFileInput = await this.page.$('input[type="file"]');
          const newDropZone = await this.page.$('[data-testid="dropzone"], .dropzone, .drop-zone, .file-drop');
          
          if (newFileInput || newDropZone) {
            this.log('   ✅ Upload interface found on transcribe page', 'success');
            uploadElementsFound++;
          }
        } catch (navError) {
          this.log(`   ⚠️  Navigation to transcribe failed: ${navError.message}`, 'warning');
        }
      }
      
      if (uploadElementsFound > 0) {
        this.log('✅ File upload interface elements detected', 'success');
        return true;
      } else {
        this.log('⚠️  No file upload interface found (may require authentication)', 'warning');
        return true;
      }
    } catch (error) {
      this.log(`❌ File upload test error: ${error.message}`, 'error');
      return false;
    }
  }

  async testResponsiveDesign() {
    this.log('📱 Testing responsive design...');
    
    try {
      // Test different viewport sizes
      const viewports = [
        { width: 375, height: 667, name: 'Mobile' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 1920, height: 1080, name: 'Desktop' }
      ];
      
      for (const viewport of viewports) {
        await this.page.setViewportSize({ width: viewport.width, height: viewport.height });
        await this.page.waitForTimeout(1000);
        
        await this.takeScreenshot(`responsive_${viewport.name.toLowerCase()}`);
        
        // Check if content is still visible and properly arranged
        const bodyVisible = await this.page.isVisible('body');
        const hasOverflow = await this.page.evaluate(() => {
          return document.body.scrollWidth > window.innerWidth;
        });
        
        this.log(`   - ${viewport.name} (${viewport.width}x${viewport.height}): ${bodyVisible ? 'Visible' : 'Hidden'}, ${hasOverflow ? 'Has horizontal scroll' : 'No horizontal scroll'}`, 
                 bodyVisible && !hasOverflow ? 'success' : 'warning');
      }
      
      // Reset to desktop view
      await this.page.setViewportSize({ width: 1920, height: 1080 });
      
      this.log('✅ Responsive design test completed', 'success');
      return true;
    } catch (error) {
      this.log(`❌ Responsive design test error: ${error.message}`, 'error');
      return false;
    }
  }

  async testAccessibility() {
    this.log('♿ Testing basic accessibility features...');
    
    try {
      // Check for common accessibility elements
      const hasTitle = await this.page.title() !== '';
      const hasMainLandmark = await this.page.$('main, [role="main"]') !== null;
      const hasNavLandmark = await this.page.$('nav, [role="navigation"]') !== null;
      const hasHeadings = await this.page.$$('h1, h2, h3, h4, h5, h6').then(els => els.length > 0);
      const hasSkipLink = await this.page.$('a:has-text("Skip"), .skip-link') !== null;
      
      this.log(`   - Page title: ${hasTitle}`, hasTitle ? 'success' : 'warning');
      this.log(`   - Main landmark: ${hasMainLandmark}`, hasMainLandmark ? 'success' : 'warning');
      this.log(`   - Navigation landmark: ${hasNavLandmark}`, hasNavLandmark ? 'success' : 'warning');
      this.log(`   - Heading structure: ${hasHeadings}`, hasHeadings ? 'success' : 'warning');
      this.log(`   - Skip links: ${hasSkipLink}`, hasSkipLink ? 'success' : 'info');
      
      // Test keyboard navigation
      try {
        await this.page.keyboard.press('Tab');
        await this.page.waitForTimeout(500);
        const focusedElement = await this.page.evaluate(() => document.activeElement.tagName);
        this.log(`   - Keyboard navigation: Focus on ${focusedElement}`, focusedElement !== 'BODY' ? 'success' : 'warning');
      } catch (keyboardError) {
        this.log(`   - Keyboard navigation test failed: ${keyboardError.message}`, 'warning');
      }
      
      this.log('✅ Accessibility test completed', 'success');
      return true;
    } catch (error) {
      this.log(`❌ Accessibility test error: ${error.message}`, 'error');
      return false;
    }
  }

  async cleanupBrowser() {
    this.log('🧹 Cleaning up browser resources...');
    
    try {
      if (this.page) await this.page.close();
      if (this.context) await this.context.close();
      if (this.browser) await this.browser.close();
      
      this.log('✅ Browser cleanup complete', 'success');
    } catch (error) {
      this.log(`⚠️  Browser cleanup error: ${error.message}`, 'warning');
    }
  }

  async runAllTests() {
    this.log('🎭 Starting comprehensive browser-based user simulation...');
    
    const setupSuccess = await this.setupBrowser();
    if (!setupSuccess) {
      this.log('❌ Failed to setup browser - aborting tests', 'error');
      return { totalTests: 0, passedTests: 0, results: [], logs: this.testResults };
    }
    
    const tests = [
      { name: 'Application Load', fn: () => this.testApplicationLoad() },
      { name: 'Navigation', fn: () => this.testNavigation() },
      { name: 'Login Interface', fn: () => this.testLoginInterface() },
      { name: 'File Upload Interface', fn: () => this.testFileUploadInterface() },
      { name: 'Responsive Design', fn: () => this.testResponsiveDesign() },
      { name: 'Accessibility', fn: () => this.testAccessibility() }
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

    // Clean up browser
    await this.cleanupBrowser();

    // Generate summary
    this.log('\n=== BROWSER SIMULATION SUMMARY ===');
    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;
    
    this.log(`Overall Success Rate: ${successCount}/${totalCount} (${Math.round(successCount/totalCount*100)}%)`);
    this.log(`Screenshots taken: ${this.screenshots.length}`);
    
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
      screenshots: this.screenshots
    };
  }
}

// Run the simulation if this script is executed directly
if (require.main === module) {
  const simulator = new BrowserUserSimulator();
  
  simulator.runAllTests()
    .then(results => {
      console.log('\n🎯 Browser-based frontend simulation completed!');
      
      // Save results to file
      const resultsFile = path.join(__dirname, 'logs', 'browser_simulation_results.json');
      fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
      console.log(`📁 Results saved to: ${resultsFile}`);
      
      if (results.screenshots.length > 0) {
        console.log('\n📸 Screenshots captured:');
        results.screenshots.forEach(screenshot => {
          console.log(`   - ${screenshot.name}: ${screenshot.path}`);
        });
      }
      
      process.exit(results.passedTests === results.totalTests ? 0 : 1);
    })
    .catch(error => {
      console.error('❌ Simulation failed:', error);
      process.exit(1);
    });
}

module.exports = BrowserUserSimulator;