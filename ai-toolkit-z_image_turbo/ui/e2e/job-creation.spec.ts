import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Job Creation E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should capture console errors and take screenshots', async ({ page }) => {
    const consoleErrors: string[] = [];
    const networkErrors: any[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Capture network errors
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        });
      }
    });

    // Take initial screenshot
    await page.screenshot({ path: 'test-results/01-initial-page.png', fullPage: true });

    // Navigate to settings
    await page.click('text=Settings');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/02-settings-page.png', fullPage: true });

    // Check current settings
    const datasetPathInput = page.locator('input[placeholder*="dataset" i], input[placeholder*="Dataset" i]').last();
    const currentDatasetPath = await datasetPathInput.inputValue();
    console.log('Current Dataset Path:', currentDatasetPath);

    // Fix dataset path if it's pointing to a specific dataset folder
    if (currentDatasetPath.includes('/my_style_ui')) {
      const parentPath = currentDatasetPath.replace('/my_style_ui', '');
      await datasetPathInput.clear();
      await datasetPathInput.fill(parentPath);
      console.log('Fixed Dataset Path to:', parentPath);
      await page.screenshot({ path: 'test-results/03-fixed-dataset-path.png', fullPage: true });
    }

    // Save settings
    await page.click('button:has-text("Save Settings")');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/04-settings-saved.png', fullPage: true });

    // Navigate to New Job
    await page.click('text=New Job');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/05-new-job-page.png', fullPage: true });

    // Wait for datasets to load
    await page.waitForTimeout(3000);

    // Check if datasets are loaded
    const datasetSelect = page.locator('select, [role="combobox"]').first();
    const datasetOptions = await datasetSelect.locator('option').count();
    console.log('Dataset options found:', datasetOptions);

    // Take screenshot of job form
    await page.screenshot({ path: 'test-results/06-job-form-with-datasets.png', fullPage: true });

    // Fill in job name
    const jobNameInput = page.locator('input[placeholder*="name" i], input[placeholder*="Name" i]').first();
    if (await jobNameInput.count() > 0) {
      await jobNameInput.fill('test_job_e2e');
      await page.screenshot({ path: 'test-results/07-filled-job-name.png', fullPage: true });
    }

    // Try to select a dataset if available
    if (datasetOptions > 0) {
      await datasetSelect.selectOption({ index: 0 });
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'test-results/08-selected-dataset.png', fullPage: true });
    }

    // Scroll to see more of the form
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/09-scrolled-form.png', fullPage: true });

    // Try to save the job
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Create"), button:has-text("Submit")').first();
    if (await saveButton.count() > 0) {
      await saveButton.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'test-results/10-after-save-click.png', fullPage: true });
    }

    // Log all errors
    console.log('\n=== Console Errors ===');
    consoleErrors.forEach((error, i) => {
      console.log(`${i + 1}. ${error}`);
    });

    console.log('\n=== Network Errors ===');
    networkErrors.forEach((error, i) => {
      console.log(`${i + 1}. ${error.status} ${error.statusText}: ${error.url}`);
    });

    // Save errors to file
    const errorReport = {
      timestamp: new Date().toISOString(),
      consoleErrors,
      networkErrors,
      datasetPath: currentDatasetPath,
      datasetOptionsCount: datasetOptions,
    };

    fs.writeFileSync(
      'test-results/error-report.json',
      JSON.stringify(errorReport, null, 2)
    );

    // Take final screenshot
    await page.screenshot({ path: 'test-results/11-final-state.png', fullPage: true });
  });

  test('should populate job form fields correctly', async ({ page }) => {
    // Navigate to New Job
    await page.goto('/jobs/new');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take screenshot before filling
    await page.screenshot({ path: 'test-results/12-job-form-empty.png', fullPage: true });

    // Fill job name
    const jobNameInput = page.locator('input').first();
    await jobNameInput.fill('e2e_test_job');
    await page.waitForTimeout(500);

    // Select Z-Image Turbo model if available
    const modelSelect = page.locator('select, [role="combobox"]').first();
    const modelOptions = await modelSelect.locator('option').allTextContents();
    console.log('Model options:', modelOptions);
    
    if (modelOptions.some(opt => opt.includes('Z-Image') || opt.includes('zimage'))) {
      await modelSelect.selectOption({ index: modelOptions.findIndex(opt => opt.includes('Z-Image') || opt.includes('zimage')) });
    }
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-results/13-model-selected.png', fullPage: true });

    // Scroll and fill more fields
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(1000);

    // Try to find and fill training steps
    const stepsInput = page.locator('input[type="number"], input[placeholder*="step" i]').first();
    if (await stepsInput.count() > 0) {
      await stepsInput.fill('1000');
    }

    await page.screenshot({ path: 'test-results/14-form-filled.png', fullPage: true });

    // Check for any validation errors
    const errorMessages = await page.locator('[role="alert"], .error, .text-red-500').allTextContents();
    if (errorMessages.length > 0) {
      console.log('Validation errors found:', errorMessages);
    }
  });

  test('should check settings configuration', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Get all input values
    const inputs = await page.locator('input').all();
    const settings: Record<string, string> = {};

    for (const input of inputs) {
      const name = await input.getAttribute('name') || await input.getAttribute('id') || 'unknown';
      const value = await input.inputValue();
      settings[name] = value;
    }

    console.log('Current Settings:', settings);

    // Verify dataset folder path is correct (should be parent folder, not specific dataset)
    const datasetPath = settings['DATASETS_FOLDER'] || Object.values(settings).find(v => v.includes('dataset'));
    if (datasetPath) {
      console.log('Dataset Path:', datasetPath);
      
      // Check if it's pointing to a specific dataset folder (incorrect)
      if (datasetPath.match(/\/datasets\/[^/]+$/)) {
        console.warn('⚠️ Dataset path is pointing to a specific dataset folder, not the parent folder!');
        console.warn('Expected: /path/to/datasets');
        console.warn('Actual:', datasetPath);
      }
    }

    await page.screenshot({ path: 'test-results/15-settings-check.png', fullPage: true });

    // Save settings snapshot
    fs.writeFileSync(
      'test-results/settings-snapshot.json',
      JSON.stringify(settings, null, 2)
    );
  });
});

