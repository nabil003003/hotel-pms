import * as client from "openid-client";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import {
  APP_URL,
  COOKIE_LOGIN_LINK_TOKEN,
  COOKIE_PHONE_LINK_TOKEN,
  COOKIE_PKCE_STATE,
  COOKIE_PKCE_VERIFIER,
} from "@/lib/auth/constants";
import { setSessionCookies } from "@/lib/auth/cookies";
import { getOidcConfig } from "@/lib/auth/openid";
export const dynamic = "force-dynamic";

const AUTH_GATEWAY_URL = process.env.AUTH_GATEWAY_URL ?? "http://localhost:8001";

export async function GET(request: NextRequest) {
  const cookieStore = await cookies();
  const codeVerifier = cookieStore.get(COOKIE_PKCE_VERIFIER)?.value;
  const expectedState = cookieStore.get(COOKIE_PKCE_STATE)?.value;

  if (!codeVerifier || !expectedState) {
    return NextResponse.redirect(new URL("/login?error=missing_pkce_state", APP_URL));
  }

  const config = await getOidcConfig();

  // Reconstruit l'URL avec APP_URL comme origine plutôt que d'utiliser
  // `request.url` tel quel : le serveur standalone Next.js (`node
  // .next/standalone/server.js`, sans HOSTNAME défini) construit request.url
  // à partir de son adresse de bind (0.0.0.0) et non du header Host reçu —
  // ça envoyait `redirect_uri=http://0.0.0.0:3000/...` à Keycloak au lieu de
  // `http://localhost:3000/...`, rejeté avec "Incorrect redirect_uri" (bug
  // réel constaté uniquement en mode standalone/prod, jamais en `next dev`).
  const incomingUrl = new URL(request.url);
  const currentUrl = new URL(`${APP_URL}${incomingUrl.pathname}${incomingUrl.search}`);

  let tokens;
  try {
    tokens = await client.authorizationCodeGrant(config, currentUrl, {
      pkceCodeVerifier: codeVerifier,
      expectedState,
    });
  } catch (error) {
    console.error("PKCE token exchange failed", error);
    return NextResponse.redirect(new URL("/login?error=token_exchange_failed", APP_URL));
  }

  // Flux QR login (biom.txt Flux B) : ce callback tourne sur le TÉLÉPHONE
  // (arrivé via /auth/hybrid-login) — dépose les 3 tokens pour que le
  // desktop, qui poll /login-link/{token}/status sur /login, les récupère.
  const loginLinkToken = cookieStore.get(COOKIE_LOGIN_LINK_TOKEN)?.value;
  if (loginLinkToken) {
    const ok = await completeLoginLink(loginLinkToken, tokens);
    const response = NextResponse.redirect(
      new URL(ok ? "/login-link/success" : "/login?error=login_link_failed", APP_URL)
    );
    setSessionCookies(response, tokens);
    response.cookies.delete(COOKIE_PKCE_VERIFIER);
    response.cookies.delete(COOKIE_PKCE_STATE);
    response.cookies.delete(COOKIE_LOGIN_LINK_TOKEN);
    return response;
  }

  // Flux /link-phone (biom.txt Flux A) : ce callback tourne sur le TÉLÉPHONE
  // (arrivé via /auth/hybrid), pas sur le desktop qui a généré le QR — le
  // cookie posé par /auth/hybrid identifie la session à compléter une fois
  // la cérémonie WebAuthn same-device terminée sur cet appareil.
  const phoneLinkToken = cookieStore.get(COOKIE_PHONE_LINK_TOKEN)?.value;
  if (phoneLinkToken) {
    const kcActionStatus = currentUrl.searchParams.get("kc_action_status");
    const destination =
      kcActionStatus === "success"
        ? await completePhoneLink(phoneLinkToken, tokens.access_token)
        : "/link-phone/failed";

    const response = NextResponse.redirect(new URL(destination, APP_URL));
    setSessionCookies(response, tokens);
    response.cookies.delete(COOKIE_PKCE_VERIFIER);
    response.cookies.delete(COOKIE_PKCE_STATE);
    // Gardé en cas d'échec — /link-phone/failed s'en sert pour proposer un
    // nouvel essai sans devoir rescanner le QR desktop.
    if (destination === "/link-phone/success") {
      response.cookies.delete(COOKIE_PHONE_LINK_TOKEN);
    }
    return response;
  }

  const landingPath = await resolveLandingPath(tokens.access_token);
  const response = NextResponse.redirect(new URL(landingPath, APP_URL));

  // id_token gardé pour `id_token_hint` au logout (RP-Initiated Logout, spec
  // OIDC) — sans ça, /api/auth/logout n'avait que l'access_token à offrir à
  // Keycloak, qui n'est pas un id_token valide : Keycloak ignorait alors le
  // logout (session SSO jamais vraiment terminée, `post_logout_redirect_uri`
  // pas honoré) — bug réel : après "déconnexion", un nouveau /api/auth/login
  // se ré-authentifiait silencieusement via le cookie SSO Keycloak encore
  // actif, sans jamais revenir sur l'écran de connexion.
  setSessionCookies(response, tokens);

  response.cookies.delete(COOKIE_PKCE_VERIFIER);
  response.cookies.delete(COOKIE_PKCE_STATE);

  return response;
}

// Invite (pas force) un compte sans téléphone lié vers /link-phone à chaque
// connexion normale — pas de mécanisme "ne plus demander" pour rester
// simple (le bouton "Continuer sans lier mon téléphone" de la page suffit).
// Échoue ouvert vers /housekeeping si l'appel /me échoue : ce contrôle ne
// doit jamais bloquer un login.
async function resolveLandingPath(accessToken: string): Promise<string> {
  try {
    const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!res.ok) return "/housekeeping";
    const me = await res.json();
    return me.webauthn_linked ? "/housekeeping" : "/link-phone";
  } catch (error) {
    console.error("resolveLandingPath /me call failed", error);
    return "/housekeeping";
  }
}

async function completeLoginLink(
  token: string,
  tokens: { access_token: string; refresh_token?: string; id_token?: string }
): Promise<boolean> {
  try {
    const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/login-link/${token}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${tokens.access_token}`, "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh_token, id_token: tokens.id_token }),
    });
    return res.ok;
  } catch (error) {
    console.error("login-link complete call failed", error);
    return false;
  }
}

async function completePhoneLink(token: string, accessToken: string): Promise<string> {
  try {
    const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/phone-link/${token}/complete`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return res.ok ? "/link-phone/success" : "/link-phone/failed";
  } catch (error) {
    console.error("phone-link complete call failed", error);
    return "/link-phone/failed";
  }
}
