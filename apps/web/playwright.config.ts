import { defineConfig, devices } from "@playwright/test";

/**
 * E2E prerequisites (local):
 * 1. API on :8000 — `migrate`, then `seed_demo`, `seed_integrations`, `seed_ai`
 *    (optional: `seed_dashboard`). Set `CELERY_TASK_ALWAYS_EAGER=true`.
 * 2. Web on :3000 — `API_BACKEND_URL=http://localhost:8000 npm run build && npm run start`
 *
 * CI starts API + web before `playwright test`. Locally, start the API first;
 * webServer below reuses an existing Next server or starts `npm run start`.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  timeout: 60_000,
  expect: { timeout: 15_000 },
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run start",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 120_000,
        env: {
          ...process.env,
          API_BACKEND_URL: process.env.API_BACKEND_URL ?? "http://localhost:8000",
        },
      },
});
