import { test, expect } from "@playwright/test";

/**
 * Gate A2 pilot tenant smoke — requires prod-like stack on :3000 and user
 * pilot-mgr@local.test / pilot1234 (see docs/operations/local-gate-checklist.md).
 *
 * Skipped in CI and default local runs. Enable after A2 setup:
 *   E2E_PILOT_LOCAL=1 npm run test:e2e -- pilot-local-smoke
 */
const PILOT_EMAIL = process.env.E2E_PILOT_EMAIL ?? "pilot-mgr@local.test";
const PILOT_PASSWORD = process.env.E2E_PILOT_PASSWORD ?? "pilot1234";

test.describe("Pilot local smoke (Gate A2 tenant)", () => {
  test.skip(
    !process.env.E2E_PILOT_LOCAL,
    "Set E2E_PILOT_LOCAL=1 after A2 demo tenant is configured on localhost",
  );

  test("login → manager dashboard smoke", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill(PILOT_EMAIL);
    await page.getByLabel("Пароль").fill(PILOT_PASSWORD);
    await page.getByRole("button", { name: "Войти" }).click();

    await expect(page).toHaveURL(/\/manager\/?$/);
    await expect(page.getByRole("heading", { name: "Дашборд руководителя" })).toBeVisible({
      timeout: 20_000,
    });
  });
});
