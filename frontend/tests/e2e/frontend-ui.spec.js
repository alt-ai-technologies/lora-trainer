// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('LoRA Training UI', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the UI
    await page.goto('http://localhost:5000');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load the main page', async ({ page }) => {
    // Take screenshot of initial page
    await page.screenshot({ path: 'tests/e2e/screenshots/01-initial-page.png', fullPage: true });
    
    // Check for main heading
    await expect(page.locator('h1')).toContainText('LoRA Training Launcher');
  });

  test('should populate form fields and create config', async ({ page }) => {
    // Take screenshot before filling form
    await page.screenshot({ path: 'tests/e2e/screenshots/02-before-filling-form.png', fullPage: true });

    // Fill in LoRA Name
    const loraNameInput = page.locator('#lora_name');
    await loraNameInput.fill('test_lora_v1');
    await expect(loraNameInput).toHaveValue('test_lora_v1');

    // Wait for datasets to load and select one
    const datasetSelect = page.locator('#dataset_select');
    await page.waitForTimeout(1000); // Wait for datasets to load
    await page.screenshot({ path: 'tests/e2e/screenshots/03-after-dataset-load.png', fullPage: true });
    
    // Fill dataset path manually
    const datasetPathInput = page.locator('#dataset_path');
    await datasetPathInput.fill('/root/datasets/my_style_ui');
    await expect(datasetPathInput).toHaveValue('/root/datasets/my_style_ui');

    // Fill training steps
    const stepsInput = page.locator('#steps');
    await stepsInput.fill('2000');
    await expect(stepsInput).toHaveValue('2000');

    // Fill learning rate
    const lrInput = page.locator('#learning_rate');
    await lrInput.fill('0.0001');
    await expect(lrInput).toHaveValue('0.0001');

    // Fill batch size
    const batchSizeInput = page.locator('#batch_size');
    await batchSizeInput.fill('1');
    await expect(batchSizeInput).toHaveValue('1');

    // Take screenshot after filling form
    await page.screenshot({ path: 'tests/e2e/screenshots/04-form-filled.png', fullPage: true });

    // Set up console error capture
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Set up network error capture
    const networkErrors = [];
    page.on('response', response => {
      if (!response.ok()) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });

    // Click "Create Config File" button
    const createConfigBtn = page.locator('button:has-text("Create Config File")');
    await createConfigBtn.click();

    // Wait for response
    await page.waitForTimeout(2000);

    // Take screenshot after clicking
    await page.screenshot({ path: 'tests/e2e/screenshots/05-after-create-click.png', fullPage: true });

    // Check for status message
    const statusMessage = page.locator('#status');
    const statusText = await statusMessage.textContent();
    
    // Take screenshot of status
    await page.screenshot({ path: 'tests/e2e/screenshots/06-status-message.png', fullPage: true });

    // Log errors
    console.log('\n=== Console Errors ===');
    consoleErrors.forEach(err => console.log(err));
    
    console.log('\n=== Network Errors ===');
    networkErrors.forEach(err => console.log(JSON.stringify(err, null, 2)));

    console.log('\n=== Status Message ===');
    console.log(statusText);

    // Check if status message is visible
    const isStatusVisible = await statusMessage.isVisible();
    console.log('\n=== Status Visible ===');
    console.log(isStatusVisible);

    // Check if launch button is enabled
    const launchBtn = page.locator('#launchBtn');
    const isLaunchEnabled = await launchBtn.isEnabled();
    console.log('\n=== Launch Button Enabled ===');
    console.log(isLaunchEnabled);

    // Save console errors to file
    const fs = require('fs');
    fs.writeFileSync(
      'tests/e2e/console-errors.json',
      JSON.stringify({ consoleErrors, networkErrors, statusText, isStatusVisible, isLaunchEnabled }, null, 2)
    );
  });

  test('should test API endpoints directly', async ({ page, request }) => {
    // Test datasets endpoint
    const datasetsResponse = await request.get('http://localhost:5000/api/datasets');
    console.log('\n=== Datasets API Response ===');
    console.log('Status:', datasetsResponse.status());
    const datasets = await datasetsResponse.json();
    console.log('Datasets:', JSON.stringify(datasets, null, 2));

    // Test validate endpoint
    const validateResponse = await request.post('http://localhost:5000/api/validate', {
      data: {
        lora_name: 'test_lora_v1',
        dataset_path: '/root/datasets/my_style_ui',
        steps: '2000',
        learning_rate: '0.0001'
      }
    });
    console.log('\n=== Validate API Response ===');
    console.log('Status:', validateResponse.status());
    const validation = await validateResponse.json();
    console.log('Validation:', JSON.stringify(validation, null, 2));

    // Test config create endpoint
    const createResponse = await request.post('http://localhost:5000/api/config/create', {
      data: {
        lora_name: 'test_lora_v1',
        dataset_path: '/root/datasets/my_style_ui',
        steps: '2000',
        learning_rate: '0.0001',
        batch_size: '1',
        config_filename: 'test_lora_v1.yaml'
      }
    });
    console.log('\n=== Create Config API Response ===');
    console.log('Status:', createResponse.status());
    const createResult = await createResponse.json();
    console.log('Result:', JSON.stringify(createResult, null, 2));

    // Save API test results
    const fs = require('fs');
    fs.writeFileSync(
      'tests/e2e/api-test-results.json',
      JSON.stringify({ datasets, validation, createResult }, null, 2)
    );
  });
});

