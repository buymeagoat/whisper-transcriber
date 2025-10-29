import { test, expect, Page } from '@playwright/test';
import { promises as fs } from 'fs';
import path from 'path';

/**
 * E2E Transcription Workflow Tests
 * 
 * Tests the complete user journey for audio transcription:
 * - File upload (various formats and sizes)
 * - Transcription processing and progress tracking
 * - Results display and formatting
 * - Download functionality
 * - Error handling and edge cases
 * - Multiple concurrent transcriptions
 */

test.describe('Transcription Workflow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('/');
    
    // Login as test user
    await page.fill('[data-testid="username-input"]', 'e2e_test_user');
    await page.fill('[data-testid="password-input"]', 'TestPassword123!');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display upload interface correctly', async () => {
    // Navigate to upload page
    await page.click('[data-testid="new-transcription"]');
    
    // Verify upload interface elements
    await expect(page.locator('[data-testid="file-upload-area"]')).toBeVisible();
    await expect(page.locator('[data-testid="file-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
    await expect(page.locator('[data-testid="language-selector"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-button"]')).toBeVisible();
    
    // Verify default settings
    await expect(page.locator('[data-testid="model-selector"]')).toHaveValue('base');
    await expect(page.locator('[data-testid="language-selector"]')).toHaveValue('auto');
    
    // Verify drag and drop area
    await expect(page.locator('[data-testid="drop-zone"]')).toContainText('Drop audio files here');
  });

  test('should successfully upload and process audio file', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    // Create a mock audio file for testing
    const testAudioPath = await createMockAudioFile();
    
    try {
      // Upload file
      await page.setInputFiles('[data-testid="file-input"]', testAudioPath);
      
      // Verify file is selected
      await expect(page.locator('[data-testid="selected-file"]')).toContainText('test-audio.wav');
      await expect(page.locator('[data-testid="file-size"]')).toBeVisible();
      
      // Configure transcription settings
      await page.selectOption('[data-testid="model-selector"]', 'small');
      await page.selectOption('[data-testid="language-selector"]', 'en');
      
      // Start transcription
      await page.click('[data-testid="upload-button"]');
      
      // Verify upload progress
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
      
      // Wait for processing to start
      await expect(page.locator('[data-testid="processing-status"]')).toBeVisible();
      await expect(page.locator('[data-testid="processing-status"]')).toContainText('Processing');
      
      // Wait for completion (with timeout)
      await page.waitForSelector('[data-testid="transcription-complete"]', { 
        timeout: 60000 
      });
      
      // Verify results are displayed
      await expect(page.locator('[data-testid="transcription-result"]')).toBeVisible();
      await expect(page.locator('[data-testid="download-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="confidence-score"]')).toBeVisible();
      
    } finally {
      // Cleanup test file
      await fs.unlink(testAudioPath).catch(() => {});
    }
  });

  test('should handle multiple file formats', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    const formats = ['wav', 'mp3', 'flac', 'm4a', 'ogg'];
    
    for (const format of formats) {
      const testFilePath = await createMockAudioFile(format);
      
      try {
        // Clear any previous selection
        await page.reload();
        await page.click('[data-testid="new-transcription"]');
        
        // Upload file
        await page.setInputFiles('[data-testid="file-input"]', testFilePath);
        
        // Verify file is accepted
        await expect(page.locator('[data-testid="selected-file"]')).toContainText(`.${format}`);
        await expect(page.locator('[data-testid="upload-button"]')).toBeEnabled();
        
      } finally {
        await fs.unlink(testFilePath).catch(() => {});
      }
    }
  });

  test('should reject invalid file types', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    // Try to upload a text file
    const invalidFilePath = await createMockTextFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', invalidFilePath);
      
      // Should show error message
      await expect(page.locator('[data-testid="file-error"]')).toContainText('Invalid file type');
      await expect(page.locator('[data-testid="upload-button"]')).toBeDisabled();
      
    } finally {
      await fs.unlink(invalidFilePath).catch(() => {});
    }
  });

  test('should handle large file uploads', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    // Create a larger mock file (simulated)
    const largeFilePath = await createMockAudioFile('wav', 50 * 1024 * 1024); // 50MB
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', largeFilePath);
      
      // Should show size warning if file is very large
      const fileSize = await page.locator('[data-testid="file-size"]').textContent();
      expect(fileSize).toContain('MB');
      
      // Upload should still be possible (unless size limit exceeded)
      await page.click('[data-testid="upload-button"]');
      
      // Should show extended upload progress
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
      
    } finally {
      await fs.unlink(largeFilePath).catch(() => {});
    }
  });

  test('should track transcription progress accurately', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    const testAudioPath = await createMockAudioFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', testAudioPath);
      await page.click('[data-testid="upload-button"]');
      
      // Wait for processing to start
      await expect(page.locator('[data-testid="processing-status"]')).toBeVisible();
      
      // Check progress updates
      const progressBar = page.locator('[data-testid="progress-percentage"]');
      await expect(progressBar).toBeVisible();
      
      // Progress should start at 0 and increase
      let previousProgress = 0;
      let progressIncreased = false;
      
      // Poll progress for up to 30 seconds
      for (let i = 0; i < 30; i++) {
        const progressText = await progressBar.textContent();
        const currentProgress = parseInt(progressText?.replace('%', '') || '0');
        
        if (currentProgress > previousProgress) {
          progressIncreased = true;
          previousProgress = currentProgress;
        }
        
        if (currentProgress >= 100) break;
        
        await page.waitForTimeout(1000);
      }
      
      expect(progressIncreased).toBe(true);
      
    } finally {
      await fs.unlink(testAudioPath).catch(() => {});
    }
  });

  test('should display transcription results correctly', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    const testAudioPath = await createMockAudioFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', testAudioPath);
      await page.click('[data-testid="upload-button"]');
      
      // Wait for completion
      await page.waitForSelector('[data-testid="transcription-complete"]', { 
        timeout: 60000 
      });
      
      // Verify transcription result elements
      await expect(page.locator('[data-testid="transcription-text"]')).toBeVisible();
      await expect(page.locator('[data-testid="confidence-score"]')).toBeVisible();
      await expect(page.locator('[data-testid="processing-time"]')).toBeVisible();
      await expect(page.locator('[data-testid="file-duration"]')).toBeVisible();
      
      // Check result metadata
      const confidence = await page.locator('[data-testid="confidence-score"]').textContent();
      expect(confidence).toMatch(/\d+(\.\d+)?%/);
      
      const duration = await page.locator('[data-testid="file-duration"]').textContent();
      expect(duration).toMatch(/\d+:\d+/); // MM:SS format
      
      // Verify download options
      await expect(page.locator('[data-testid="download-txt"]')).toBeVisible();
      await expect(page.locator('[data-testid="download-json"]')).toBeVisible();
      await expect(page.locator('[data-testid="download-srt"]')).toBeVisible();
      
    } finally {
      await fs.unlink(testAudioPath).catch(() => {});
    }
  });

  test('should allow result download in multiple formats', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    const testAudioPath = await createMockAudioFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', testAudioPath);
      await page.click('[data-testid="upload-button"]');
      
      await page.waitForSelector('[data-testid="transcription-complete"]', { 
        timeout: 60000 
      });
      
      // Test TXT download
      const [txtDownload] = await Promise.all([
        page.waitForEvent('download'),
        page.click('[data-testid="download-txt"]')
      ]);
      expect(txtDownload.suggestedFilename()).toMatch(/\.txt$/);
      
      // Test JSON download
      const [jsonDownload] = await Promise.all([
        page.waitForEvent('download'),
        page.click('[data-testid="download-json"]')
      ]);
      expect(jsonDownload.suggestedFilename()).toMatch(/\.json$/);
      
      // Test SRT download
      const [srtDownload] = await Promise.all([
        page.waitForEvent('download'),
        page.click('[data-testid="download-srt"]')
      ]);
      expect(srtDownload.suggestedFilename()).toMatch(/\.srt$/);
      
    } finally {
      await fs.unlink(testAudioPath).catch(() => {});
    }
  });

  test('should handle transcription errors gracefully', async () => {
    await page.click('[data-testid="new-transcription"]');
    
    // Create a corrupted audio file
    const corruptedFilePath = await createCorruptedAudioFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', corruptedFilePath);
      await page.click('[data-testid="upload-button"]');
      
      // Should eventually show error
      await expect(page.locator('[data-testid="transcription-error"]')).toBeVisible({ 
        timeout: 60000 
      });
      
      await expect(page.locator('[data-testid="error-message"]')).toContainText('failed to process');
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
      
    } finally {
      await fs.unlink(corruptedFilePath).catch(() => {});
    }
  });

  test('should handle concurrent transcriptions', async () => {
    // Create multiple browser tabs
    const page2 = await page.context().newPage();
    const page3 = await page.context().newPage();
    
    try {
      // Login on additional pages
      for (const p of [page2, page3]) {
        await p.goto('/');
        await p.fill('[data-testid="username-input"]', 'e2e_test_user');
        await p.fill('[data-testid="password-input"]', 'TestPassword123!');
        await p.click('[data-testid="login-button"]');
        await expect(p).toHaveURL(/.*\/dashboard/);
      }
      
      // Start transcriptions on all tabs
      const audioFiles = await Promise.all([
        createMockAudioFile('wav'),
        createMockAudioFile('mp3'),
        createMockAudioFile('flac')
      ]);
      
      try {
        // Upload files concurrently
        await Promise.all([
          uploadFileOnPage(page, audioFiles[0]),
          uploadFileOnPage(page2, audioFiles[1]),
          uploadFileOnPage(page3, audioFiles[2])
        ]);
        
        // All should process successfully
        await Promise.all([
          page.waitForSelector('[data-testid="transcription-complete"]', { timeout: 90000 }),
          page2.waitForSelector('[data-testid="transcription-complete"]', { timeout: 90000 }),
          page3.waitForSelector('[data-testid="transcription-complete"]', { timeout: 90000 })
        ]);
        
      } finally {
        // Cleanup
        await Promise.all(audioFiles.map(file => fs.unlink(file).catch(() => {})));
      }
      
    } finally {
      await page2.close();
      await page3.close();
    }
  });

  test('should maintain transcription history', async () => {
    // Navigate to history page
    await page.click('[data-testid="transcription-history"]');
    
    // Verify history interface
    await expect(page.locator('[data-testid="history-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="history-filters"]')).toBeVisible();
    
    // Upload a new transcription
    await page.click('[data-testid="new-transcription"]');
    const testAudioPath = await createMockAudioFile();
    
    try {
      await page.setInputFiles('[data-testid="file-input"]', testAudioPath);
      await page.click('[data-testid="upload-button"]');
      
      await page.waitForSelector('[data-testid="transcription-complete"]', { 
        timeout: 60000 
      });
      
      // Return to history
      await page.click('[data-testid="transcription-history"]');
      
      // Should see the new transcription in history
      await expect(page.locator('[data-testid="history-item"]').first()).toBeVisible();
      await expect(page.locator('[data-testid="history-item"]').first()).toContainText('test-audio.wav');
      
    } finally {
      await fs.unlink(testAudioPath).catch(() => {});
    }
  });
});

// Helper functions for creating test files
async function createMockAudioFile(format: string = 'wav', sizeBytes: number = 1024): Promise<string> {
  const fileName = `test-audio.${format}`;
  const filePath = path.join('/tmp', fileName);
  
  // Create a mock audio file with some binary data
  const buffer = Buffer.alloc(sizeBytes, 0);
  // Add some mock audio headers
  if (format === 'wav') {
    buffer.write('RIFF', 0);
    buffer.write('WAVE', 8);
  }
  
  await fs.writeFile(filePath, buffer);
  return filePath;
}

async function createMockTextFile(): Promise<string> {
  const filePath = path.join('/tmp', 'test-file.txt');
  await fs.writeFile(filePath, 'This is not an audio file');
  return filePath;
}

async function createCorruptedAudioFile(): Promise<string> {
  const filePath = path.join('/tmp', 'corrupted-audio.wav');
  // Create a file with audio extension but invalid content
  await fs.writeFile(filePath, 'This is corrupted audio data that should fail processing');
  return filePath;
}

async function uploadFileOnPage(page: Page, filePath: string): Promise<void> {
  await page.click('[data-testid="new-transcription"]');
  await page.setInputFiles('[data-testid="file-input"]', filePath);
  await page.click('[data-testid="upload-button"]');
}
