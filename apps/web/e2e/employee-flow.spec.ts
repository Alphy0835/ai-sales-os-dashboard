import { test, expect } from "@playwright/test";

test.describe("Employee flow", () => {
  test("login → dashboard → logout", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("employee@demo.local");
    await page.getByLabel("Пароль").fill("demo1234");
    await page.getByRole("button", { name: "Войти" }).click();

    await expect(page).toHaveURL(/\/employee\/?$/);
    await expect(page.getByRole("heading", { name: "Дашборд" })).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText("Динамика звонков (7д)")).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "⎋ Выход" }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
    await expect(page.getByRole("button", { name: "Войти" })).toBeVisible();
  });
});
