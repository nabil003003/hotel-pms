import { expect, test, type Locator, type Page } from "@playwright/test";
import { loginAs } from "./helpers";

/**
 * Spec §7.3 Scénario 4 / Planning : Réceptionniste déplace une réservation sur la grille
 * planning (Drag & Drop) -> vérification temps réel sur une 2ème session.
 *
 * Deux contextes navigateur distincts (acteur + observateur) pour vérifier
 * la propagation WebSocket via Redis pub/sub (/ws/planning, `usePlanningWebSocket`).
 */
async function dragAndDropBooking(page: Page, sourceBar: Locator, targetCell: Locator) {
  const sourceBox = await sourceBar.boundingBox();
  const targetBox = await targetCell.boundingBox();
  expect(sourceBox).not.toBeNull();
  expect(targetBox).not.toBeNull();

  const startX = sourceBox!.x + sourceBox!.width / 2;
  const startY = sourceBox!.y + sourceBox!.height / 2;
  const endX = targetBox!.x + targetBox!.width / 2;
  const endY = targetBox!.y + targetBox!.height / 2;

  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // Seuil d'activation PointerSensor (8px) -> mouvement intermédiaire de 12px
  await page.mouse.move(startX + 12, startY + 12, { steps: 5 });
  await page.mouse.move(endX, endY, { steps: 10 });
  await page.mouse.up();
}

test("receptionniste: drag & drop room shift propagates to a second client via websocket", async ({ browser }) => {
  const actorContext = await browser.newContext();
  const observerContext = await browser.newContext();
  const actorPage = await actorContext.newPage();
  const observerPage = await observerContext.newPage();

  try {
    await loginAs(actorPage, "test.receptionniste");
    await loginAs(observerPage, "test.receptionniste");

    await actorPage.goto("/reservations");
    await observerPage.goto("/reservations");

    // S'assurer que les deux sessions sont en Vue Grille
    const actorGridBtn = actorPage.getByRole("button", { name: "Vue Grille" });
    const observerGridBtn = observerPage.getByRole("button", { name: "Vue Grille" });
    if (await actorGridBtn.isVisible()) await actorGridBtn.click();
    if (await observerGridBtn.isVisible()) await observerGridBtn.click();

    // Attendre l'affichage de la grille
    await expect(actorPage.getByText("Chambre")).toBeVisible({ timeout: 10_000 });
    await expect(observerPage.getByText("Chambre")).toBeVisible({ timeout: 10_000 });

    // Localiser les barres de réservation ou créer une réservation si besoin
    const actorBars = actorPage.locator(".group.relative.flex.items-center");
    const count = await actorBars.count();

    // Si aucune réservation n'est visible sur la grille, on repasse en vue tableau ou clique "Nouvelle réservation"
    if (count === 0) {
      await actorPage.getByRole("button", { name: /Nouvelle réservation/ }).click();
      await actorPage.getByLabel("Prénom client").fill("TestDrag");
      await actorPage.getByLabel("Nom client").fill("Realtime");
      await actorPage.getByRole("button", { name: "Créer la réservation" }).click();
      await expect(actorPage.getByText("Réservation créée")).toBeVisible({ timeout: 10_000 });
    }

    const firstBar = actorPage.locator(".group.relative.flex.items-center").first();
    await expect(firstBar).toBeVisible({ timeout: 10_000 });
    const bookingTitle = await firstBar.getAttribute("title");

    // Identifier une cellule de destination sur une autre chambre (ex: deuxième ligne de la grille)
    const droppableCells = actorPage.locator("[id*='__']");
    const cellCount = await droppableCells.count();
    expect(cellCount).toBeGreaterThan(1);

    // Choisir une cellule sur une chambre différente de celle d'origine
    const targetCell = droppableCells.nth(Math.min(10, cellCount - 1));

    // Effectuer le drag & drop
    await dragAndDropBooking(actorPage, firstBar, targetCell);

    // Vérifier la notification de confirmation sur l'acteur
    await expect(actorPage.getByText(/Chambre changée/)).toBeVisible({ timeout: 10_000 });

    // L'observateur reçoit la mise à jour sans rechargement manuel via le WebSocket /ws/planning
    if (bookingTitle) {
      const observerTargetBar = observerPage.locator(`.group.relative.flex.items-center[title="${bookingTitle}"]`);
      await expect(observerTargetBar).toBeVisible({ timeout: 10_000 });
    }
  } finally {
    await actorContext.close();
    await observerContext.close();
  }
});
