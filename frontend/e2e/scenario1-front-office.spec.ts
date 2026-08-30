import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * Spec §7.3 Scénario 1 : Réceptionniste crée réservation → check-in →
 * ajoute extra → check-out.
 */
test("receptionniste: walk-in booking -> check-in -> extra -> check-out", async ({ page }) => {
  await loginAs(page, "test.receptionniste");

  await page.goto("/reservations");
  await page.getByRole("button", { name: "Nouvelle réservation (walk-in)" }).click();

  const uniqueSuffix = Date.now().toString().slice(-6);
  // Vérifie une fois que l'association Label/Input fonctionne bien
  // (Sprint 7 : bug réel trouvé ici, `htmlFor`/`id` manquants) avant de
  // retomber sur des locators par id, plus robustes contre un bug interne
  // Playwright observé avec `getByLabel` dans ce dialogue précis.
  await expect(page.locator("#first_name")).toHaveAccessibleName("Prénom client");
  await page.locator("#first_name").fill("E2E");
  await page.locator("#last_name").fill(`Scenario1-${uniqueSuffix}`);
  await page.locator("#deposit_paid").check();
  await page.getByRole("button", { name: "Créer la réservation" }).click();

  await expect(page.getByText("Réservation créée")).toBeVisible({ timeout: 10_000 });

  await page.goto("/front-office");
  await expect(page.getByText("Arrivées du jour")).toBeVisible();
  await page.getByRole("button", { name: "Check-in" }).first().click();
  await expect(page.getByText("Check-in effectué")).toBeVisible({ timeout: 10_000 });

  await expect(page.getByText(/Folio A — solde/)).toBeVisible({ timeout: 10_000 });

  // Ajoute un extra (charge manuelle, Workflow E).
  await page.locator("#libelle").fill("Massage E2E");
  await page.locator("#unit_price_ht").fill("100");
  await page.getByRole("button", { name: "Ajouter" }).click();
  await expect(page.getByText("Charge ajoutée")).toBeVisible({ timeout: 10_000 });

  // Encaisse le solde exact (le champ Montant se réinitialise sur le
  // nouveau solde grâce au remount par `key={folioA.version}`).
  await page.getByRole("button", { name: "Encaisser" }).click();
  await expect(page.getByText("Paiement enregistré")).toBeVisible({ timeout: 10_000 });

  await expect(page.getByText("Folio A — solde 0.00 MAD")).toBeVisible({ timeout: 10_000 });

  await page.getByRole("button", { name: "Check-out" }).click();
  await expect(page.getByText("Check-out effectué")).toBeVisible({ timeout: 10_000 });
});
