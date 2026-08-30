import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * Spec §7.3 Scénario 2 : Manager lance Night Audit → vérifie rapports →
 * bascule J+1. Aucun compte "manager" de test n'existe (seul sidi.omar,
 * super-admin, cf. `scripts/keycloak_setup.py`) — utilisé ici, il satisfait
 * le rôle requis par `night-audit-service` (manager, admin).
 *
 * Ce test clôture réellement la journée en cours (action irréversible côté
 * backend) — volontairement exécuté après le scénario 1 (qui règle son
 * folio à 0) pour que la vérification soit équilibrée.
 */
test("manager: night audit verify -> close -> business date rolls over", async ({ page }) => {
  await loginAs(page, "sidi.omar");

  await page.goto("/night-audit");
  await expect(page.getByText(/Date métier en cours/)).toBeVisible();

  await page.getByRole("button", { name: /Vérifier/ }).click();
  await expect(page.getByText(/Écart : 0.00 MAD/)).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: /Clôturer la journée/ }).click();
  await expect(page.getByText(/Clôture effectuée/)).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/Journée .* clôturée/)).toBeVisible();
  await expect(page.getByText(/Hash rapport/)).toBeVisible();
});
