import * as client from "openid-client";

import { KEYCLOAK_CLIENT_ID, KEYCLOAK_REALM, KEYCLOAK_URL } from "./constants";

let configPromise: Promise<client.Configuration> | null = null;

/**
 * Découverte OIDC mise en cache (module-level) — `pms-frontend` est un
 * client public PKCE (D4), donc `client.None()` comme authentification.
 */
export function getOidcConfig(): Promise<client.Configuration> {
  if (!configPromise) {
    const issuer = new URL(`${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`);
    // `openid-client` v6 rejette par défaut tout issuer non-HTTPS (Sprint 7,
    // bug réel trouvé par les tests E2E Playwright — jamais exercé avant en
    // conditions réelles) : Keycloak tourne en HTTP dans ce Compose de dev
    // (pas de certificat TLS local), donc `allowInsecureRequests` doit être
    // explicitement autorisé quand l'issuer n'est pas déjà en HTTPS.
    const execute = issuer.protocol === "http:" ? [client.allowInsecureRequests] : [];
    configPromise = client.discovery(issuer, KEYCLOAK_CLIENT_ID, undefined, client.None(), { execute });
  }
  return configPromise;
}
