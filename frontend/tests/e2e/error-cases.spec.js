// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Error Cases', () => {
  test('should handle missing required fields', async ({ page, request }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');

    // Try to create config without filling form
    const createConfigBtn = page.locator('button:has-text("Create Config File")');
    await createConfigBtn.click();
    
    await page.waitForTimeout(1000);
    
    // Check for validation error
    const statusMessage = page.locator('#status');
    const statusText = await statusMessage.textContent();
    
    console.log('Status after empty form submit:', statusText);
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/error-empty-form.png', fullPage: true });
  });

  test('should handle API errors gracefully', async ({ page, request }) => {
    // Test with invalid data
    const response = await request.post('http://localhost:5000/api/config/create', {
      data: {
        // Missing required fields
        lora_name: '',
        dataset_path: ''
      }
    });
    
    console.log('Invalid request status:', response.status());
    const result = await response.json();
    console.log('Invalid request response:', JSON.stringify(result, null, 2));
    
    // Should return validation error or 400
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test('should show error for invalid dataset path', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');

    // Fill form with invalid dataset path
    await page.locator('#lora_name').fill('test_error');
    await page.locator('#dataset_path').fill('/root/datasets/nonexistent');
    await page.locator('#steps').fill('2000');
    await page.locator('#learning_rate').fill('0.0001');

    // Capture console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Click create
    await page.locator('button:has-text("Create Config File")').click();
    await page.waitForTimeout(2000);

    // Check status
    const statusMessage = page.locator('#status');
    const statusText = await statusMessage.textContent();
    
    console.log('Status with invalid path:', statusText);
    console.log('Console errors:', consoleErrors);
    
    await page.screenshot({ path: 'tests/e2e/screenshots/error-invalid-path.png', fullPage: true });
  });
});

