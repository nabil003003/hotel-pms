import { defineConfig, devices } from "@playwright/test";

/**
 * Sprint 7 (D14) — exécuté pour de vrai contre `next dev` (webServer géré ici)
 * + les backends Docker déjà démarrés séparément (`docker compose --profile
 * core up`). Un seul worker : plusieurs scénarios partagent le même
 * établissement Riad Yasmine et créent/annulent leurs propres réservations,
 * pas d'isolation par établissement entre tests.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/login",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
