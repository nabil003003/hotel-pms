import { Page, expect } from "@playwright/test";

/**
 * Login réel (Sprint 7, D14) — traverse la vraie page Keycloak hébergée
 * (D4 : pas de formulaire Next.js), pas un mock de session.
 */
export async function loginAs(page: Page, username: string, password = "ChangeMe123!") {
  await page.goto("/api/auth/login");
  await page.waitForURL(/realms\/amh-hospitality\/protocol\/openid-connect\/auth/);
  await page.locator("#username").fill(username);
  await page.locator("#password").fill(password);
  await page.locator("#kc-login").click();
  await page.waitForURL((url) => !url.href.includes("keycloak") && !url.href.includes(":8080"), {
    timeout: 15_000,
  });
  await expect(page.getByText("AMH Hospitality")).toBeVisible();
}
