import * as client from "openid-client";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN } from "@/lib/auth/constants";
import { setSessionCookies } from "@/lib/auth/cookies";
import { getOidcConfig } from "@/lib/auth/openid";

type TokenEndpointResponse = Awaited<ReturnType<typeof client.refreshTokenGrant>>;

// Un seul renouvellement Keycloak par refresh_token à la fois (process-wide) :
// une page ouverte plusieurs minutes déclenche plusieurs requêtes react-query
// en parallèle (establishments, rooms, bookings, ...) qui expirent toutes en
// même temps — sans ce cache, chacune lancerait son propre refreshTokenGrant
// avec le même refresh_token, et si la rotation Keycloak est activée seul le
// premier appel réussirait (les autres verraient invalid_grant).
const inFlightRefresh = new Map<string, Promise<TokenEndpointResponse | null>>();

function refreshAccessToken(refreshToken: string): Promise<TokenEndpointResponse | null> {
  const existing = inFlightRefresh.get(refreshToken);
  if (existing) return existing;

  const attempt = (async () => {
    try {
      const config = await getOidcConfig();
      return await client.refreshTokenGrant(config, refreshToken);
    } catch {
      return null; // refresh_token expiré/révoqué — l'appelant retombera sur le 401 habituel
    }
  })().finally(() => inFlightRefresh.delete(refreshToken));

  inFlightRefresh.set(refreshToken, attempt);
  return attempt;
}

/**
 * BFF minimal (spec §2 : "NEXT.JS (Frontend + BFF)") — relaie les appels du
 * navigateur vers les microservices avec le Bearer token lu depuis le cookie
 * httpOnly (jamais exposé au JS client). Un fichier par service cible
 * (app/api/proxy/{service}/[...path]/route.ts) réutilise cette fonction.
 */
export async function proxyToService(
  request: NextRequest,
  targetBaseUrl: string,
  pathSegments: string[]
): Promise<NextResponse> {
  const cookieStore = await cookies();
  let token = cookieStore.get(COOKIE_ACCESS_TOKEN)?.value;
  let refreshedTokens: TokenEndpointResponse | null = null;

  if (!token) {
    // access_token (~5 min) expiré alors que la page est restée ouverte sans
    // navigation complète — middleware.ts ne revoit jamais ces requêtes
    // /api/proxy/* pour les rafraîchir (son matcher ne couvre que les routes
    // de page). Renouvellement silencieux ici plutôt qu'un 401 sec, pour ne
    // pas casser une mutation utilisateur (ex: création de réservation après
    // plusieurs minutes de saisie du formulaire).
    const refreshToken = cookieStore.get(COOKIE_REFRESH_TOKEN)?.value;
    if (refreshToken) {
      refreshedTokens = await refreshAccessToken(refreshToken);
      token = refreshedTokens?.access_token;
    }
  }

  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const search = request.nextUrl.search;
  const targetUrl = `${targetBaseUrl}/api/v1/${pathSegments.join("/")}${search}`;

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  // Headers métier ponctuels transportés tels quels (idempotence Sprint 3/4,
  // jeton de clôture Night Audit Sprint 5) — pas un passthrough générique
  // (on ne relaie jamais les headers de transport/cookies du navigateur).
  for (const name of ["x-idempotency-key", "x-audit-token"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const hasBody = !["GET", "HEAD"].includes(request.method);

  const upstreamResponse = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: hasBody ? await request.blob() : undefined,
    cache: "no-store",
  });

  const responseBody = await upstreamResponse.blob();
  const response = new NextResponse(responseBody, {
    status: upstreamResponse.status,
    headers: {
      "content-type": upstreamResponse.headers.get("content-type") ?? "application/json",
    },
  });

  if (refreshedTokens) {
    setSessionCookies(response, refreshedTokens);
  }

  return response;
}
