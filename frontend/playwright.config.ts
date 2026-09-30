import { defineConfig, devices } from '@playwright/test';

const FEEDBACK_API_URL = 'http://127.0.0.1:8100';
const EVENT_API_URL = 'http://127.0.0.1:8101';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'py -3.13 -m uvicorn vh.feedback.server:app --host 127.0.0.1 --port 8100',
      cwd: '..',
      env: {
        PYTHONPATH: 'src',
        FEEDBACK_DB_PATH: 'data/feedback-e2e.db',
        FEEDBACK_DEMO_SEED: '1',
        FEEDBACK_DEMO_TOKEN: 'e2e-demo-token-001',
      },
      url: `${FEEDBACK_API_URL}/docs`,
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'py -3.13 -m uvicorn vh.events.server:app --host 127.0.0.1 --port 8101',
      cwd: '..',
      env: {
        PYTHONPATH: 'src',
        EVENT_LOG_PATH: 'data/events-e2e.jsonl',
        EVENT_DEMO_SEED: '1',
      },
      url: `${EVENT_API_URL}/docs`,
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: 'pnpm dev -- --port 5173 --strictPort',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 120000,
      env: {
        VITE_FEEDBACK_API_URL: FEEDBACK_API_URL,
        VITE_EVENT_API_URL: EVENT_API_URL,
      },
    },
  ],
});
