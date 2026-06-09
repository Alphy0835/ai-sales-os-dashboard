import { test, expect } from "@playwright/test";

test.describe("Manager critical flow", () => {
  test("login → dashboard → review → analytics canvas", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("manager@demo.local");
    await page.getByLabel("Пароль").fill("demo1234");
    await page.getByRole("button", { name: "Войти" }).click();

    await expect(page).toHaveURL(/\/manager\/?$/);
    await expect(page.getByRole("heading", { name: "Дашборд руководителя" })).toBeVisible({
      timeout: 20_000,
    });

    await page.getByRole("link", { name: /История разборов/ }).click();
    await expect(page.getByRole("heading", { name: "История разборов" })).toBeVisible();

    const workspaceSelect = page.locator('label:has-text("Подразделение") select').first();
    await workspaceSelect.selectOption({ index: 1 });

    const employeeSelect = page.locator('label:has-text("Сотрудник") select').first();
    await employeeSelect.selectOption({ index: 1 });

    await page.getByRole("button", { name: "Новый разбор" }).click();

    const reviewComment = `E2E разбор ${Date.now()}`;
    await page.locator('textarea').first().fill(reviewComment);
    await page.getByRole("button", { name: "Сохранить разбор" }).click();

    await expect(page.getByText(reviewComment)).toBeVisible({ timeout: 15_000 });

    await page.getByRole("link", { name: /AI-аналитика/ }).click();
    await expect(page.getByRole("heading", { name: "AI-аналитика" })).toBeVisible();

    await page.getByRole("button", { name: "Запустить анализ" }).click();
    await expect(page.getByTestId("analytics-canvas")).toBeVisible({ timeout: 45_000 });
    await expect(page.getByRole("heading", { name: "Канвас отчёта" })).toBeVisible();
  });
});
