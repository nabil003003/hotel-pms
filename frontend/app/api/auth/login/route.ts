import * as client from "openid-client";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { APP_URL, COOKIE_PKCE_STATE, COOKIE_PKCE_VERIFIER } from "@/lib/auth/constants";
import { getOidcConfig } from "@/lib/auth/openid";
export const dynamic = "force-dynamic";

/**
 * Démarre le flow Authorization Code + PKCE (D4) — redirige vers la page de
 * login HÉBERGÉE par Keycloak (thème re-skinné, infra/keycloak/themes/),
 * pas un formulaire Next.js.
 *
 * `?action=` (optionnel) est transmis à Keycloak en `kc_action` — utilisé
 * par le lien "Lier mon téléphone" (user-menu.tsx) pour déclencher la
 * required action `webauthn-register` sur la session déjà
 * authentifiée, plutôt qu'un simple login (biom.txt Flux A).
 *
 * `?forceLogin=1` transmis en `prompt=login` — sans ça, un téléphone déjà
 * connu de Keycloak (cookie SSO encore valide, ex. re-scan du QR /login/qr
 * peu après un premier essai) se reconnecte silencieusement via le
 * Cookie authenticator, sans jamais montrer l'étape empreinte : `prompt=login`
 * force Keycloak à ignorer la session existante et à re-proposer les
 * exécutions du flow (mot de passe / WebAuthn), cf. app/auth/hybrid-login.
 */
export async function GET(request: NextRequest) {
  const config = await getOidcConfig();

  const codeVerifier = client.randomPKCECodeVerifier();
  const codeChallenge = await client.calculatePKCECodeChallenge(codeVerifier);
  const state = client.randomState();
  const kcAction = request.nextUrl.searchParams.get("action");
  const forceLogin = request.nextUrl.searchParams.get("forceLogin") === "1";

  const authorizationUrl = client.buildAuthorizationUrl(config, {
    redirect_uri: `${APP_URL}/api/auth/callback`,
    scope: "openid profile email",
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
    state,
    ...(kcAction ? { kc_action: kcAction } : {}),
    ...(forceLogin ? { prompt: "login" } : {}),
  });

  const cookieStore = await cookies();
  const cookieOptions = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: 300,
  };
  cookieStore.set(COOKIE_PKCE_VERIFIER, codeVerifier, cookieOptions);
  cookieStore.set(COOKIE_PKCE_STATE, state, cookieOptions);

  return NextResponse.redirect(authorizationUrl);
}
