import type { SessionClaims } from "./constants";

/**
 * Décodage (sans vérification de signature) du payload JWT — acceptable ici
 * car le token est reçu directement de Keycloak via un appel serveur-à-serveur
 * de confiance (échange PKCE dans app/api/auth/callback/route.ts), jamais
 * fourni tel quel par un client non authentifié.
 */
export function decodeJwtPayload(token: string): Record<string, unknown> {
  const payload = token.split(".")[1];
  const json = Buffer.from(payload, "base64url").toString("utf-8");
  return JSON.parse(json);
}

export function claimsFromToken(token: string): SessionClaims {
  const payload = decodeJwtPayload(token);
  const realmAccess = (payload.realm_access as { roles?: string[] } | undefined) ?? {};
  const isSuperAdminRaw = payload.is_super_admin;

  return {
    sub: payload.sub as string,
    email: payload.email as string | undefined,
    roles: realmAccess.roles ?? [],
    establishment_ids: (payload.establishment_ids as string[] | undefined) ?? [],
    is_super_admin:
      typeof isSuperAdminRaw === "string" ? isSuperAdminRaw === "true" : Boolean(isSuperAdminRaw),
    exp: payload.exp as number,
  };
}
