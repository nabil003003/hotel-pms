import * as client from "openid-client";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { APP_URL, COOKIE_REFRESH_TOKEN } from "@/lib/auth/constants";
import { clearSessionCookies, setSessionCookies } from "@/lib/auth/cookies";
import { getOidcConfig } from "@/lib/auth/openid";

export const dynamic = "force-dynamic";

function safeRedirectPath(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/housekeeping";
  return raw;
}

/**
 * Renouvellement silencieux : amh_access_token expire après ~5 min (durée de
 * vie Keycloak) bien avant amh_refresh_token (30 jours). Sans cette route, le
 * refresh_token était posé au login mais jamais relu — l'utilisateur
 * retombait sur /login toutes les 5 minutes malgré un refresh_token encore
 * valide. Déclenché par middleware.ts quand le cookie access_token est
 * absent/expiré mais qu'un refresh_token est encore présent.
 */
export async function GET(request: NextRequest) {
  const redirectTo = safeRedirectPath(request.nextUrl.searchParams.get("redirect"));
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(COOKIE_REFRESH_TOKEN)?.value;

  if (!refreshToken) {
    return NextResponse.redirect(new URL("/login", APP_URL));
  }

  const config = await getOidcConfig();

  let tokens;
  try {
    tokens = await client.refreshTokenGrant(config, refreshToken);
  } catch (error) {
    // refresh_token expiré/révoqué (session Keycloak idle timeout dépassé,
    // ou refresh_token déjà consommé si la rotation est activée) — pas de
    // session à sauver, retour à /login comme au premier login.
    console.error("Silent refresh failed", error);
    const response = NextResponse.redirect(new URL("/login?error=session_expired", APP_URL));
    clearSessionCookies(response);
    return response;
  }

  const response = NextResponse.redirect(new URL(redirectTo, APP_URL));
  setSessionCookies(response, tokens);
  return response;
}
