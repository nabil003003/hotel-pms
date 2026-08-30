import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

/**
 * Spec §7.3 Scénario 3 : Gouvernante met à jour statuts chambres →
 * vérification temps réel planning. Deux contextes navigateur distincts
 * (acteur + observateur) pour vérifier une vraie propagation WebSocket
 * (Redis pub/sub, `useRoomsWebSocket`) plutôt qu'un simple refetch local.
 *
 * Cible fixe : chambre R02, connue "Sale" au moment d'écrire ce test
 * (vérifié via l'API avant d'écrire le scénario) — action "Commencer
 * nettoyage" (Sale -> Nettoyage), la seule transition qui ne nécessite pas
 * de motif/dialogue.
 */
test("gouvernante: room status change propagates to a second client via websocket", async ({ browser }) => {
  const actorContext = await browser.newContext();
  const observerContext = await browser.newContext();
  const actorPage = await actorContext.newPage();
  const observerPage = await observerContext.newPage();

  try {
    await loginAs(actorPage, "test.gouvernante");
    await loginAs(observerPage, "test.gouvernante");

    await actorPage.goto("/housekeeping");
    await observerPage.goto("/housekeeping");

    await actorPage.getByPlaceholder("Rechercher une chambre...").fill("R02");
    await observerPage.getByPlaceholder("Rechercher une chambre...").fill("R02");

    const actorRow = actorPage.getByRole("row", { name: /R02/ });
    const observerRow = observerPage.getByRole("row", { name: /R02/ });

    await expect(actorRow).toContainText("Sale", { timeout: 10_000 });
    await expect(observerRow).toContainText("Sale", { timeout: 10_000 });

    await actorRow.getByRole("button", { name: "Commencer nettoyage" }).click();

    // L'acteur voit le changement (refetch après mutation)...
    await expect(actorRow).toContainText("Nettoyage", { timeout: 10_000 });
    // ...et l'observateur aussi, sans action de sa part (push WebSocket).
    await expect(observerRow).toContainText("Nettoyage", { timeout: 10_000 });

    // Remet la chambre dans son état d'origine pour ne pas polluer les runs suivants.
    await actorRow.getByRole("button", { name: "Marquer propre" }).click();
    await expect(actorRow).toContainText("Propre", { timeout: 10_000 });
  } finally {
    await actorContext.close();
    await observerContext.close();
  }
});
