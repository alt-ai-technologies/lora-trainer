// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  outputDir: './tests/e2e/test-results',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'tests/e2e/playwright-report' }],
    ['list']
  ],
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: '/usr/bin/python3 app.py',
    url: 'http://localhost:5000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});

