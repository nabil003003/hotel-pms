import type { NextResponse } from "next/server";

import { COOKIE_ACCESS_TOKEN, COOKIE_ID_TOKEN, COOKIE_REFRESH_TOKEN, COOKIE_SESSION, type SessionClaims } from "./constants";
import { claimsFromToken } from "./jwt";

interface TokenSet {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
}

/**
 * Pose les cookies de session à partir d'un token set Keycloak — partagé
 * entre le callback PKCE initial (app/api/auth/callback) et le renouvellement
 * silencieux (app/api/auth/refresh) pour ne pas dupliquer la logique
 * maxAge/claims entre les deux.
 */
export function setSessionCookies(response: NextResponse, tokens: TokenSet): SessionClaims {
  const claims = claimsFromToken(tokens.access_token);
  const maxAge = Math.max(claims.exp - Math.floor(Date.now() / 1000), 60);
  const secure = process.env.NODE_ENV === "production";

  response.cookies.set(COOKIE_ACCESS_TOKEN, tokens.access_token, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge,
  });

  if (tokens.refresh_token) {
    response.cookies.set(COOKIE_REFRESH_TOKEN, tokens.refresh_token, {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }

  if (tokens.id_token) {
    response.cookies.set(COOKIE_ID_TOKEN, tokens.id_token, {
      httpOnly: true,
      secure,
      sameSite: "lax",
      path: "/",
      maxAge,
    });
  }

  response.cookies.set(COOKIE_SESSION, JSON.stringify(claims), {
    httpOnly: false, // lu par les composants client (sélecteur de Riad, garde de rôle UI — D2)
    secure,
    sameSite: "lax",
    path: "/",
    maxAge,
  });

  return claims;
}

export function clearSessionCookies(response: NextResponse): void {
  response.cookies.delete(COOKIE_ACCESS_TOKEN);
  response.cookies.delete(COOKIE_REFRESH_TOKEN);
  response.cookies.delete(COOKIE_ID_TOKEN);
  response.cookies.delete(COOKIE_SESSION);
}
