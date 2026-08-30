import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  APP_URL,
  COOKIE_ACCESS_TOKEN,
  COOKIE_ID_TOKEN,
  COOKIE_REFRESH_TOKEN,
  COOKIE_SESSION,
  KEYCLOAK_CLIENT_ID,
  KEYCLOAK_REALM,
  KEYCLOAK_URL,
} from "@/lib/auth/constants";

export const dynamic = "force-dynamic";

export async function GET() {
  const cookieStore = await cookies();
  // Doit être le vrai id_token (pas l'access_token — bug corrigé, voir
  // callback/route.ts) : sans id_token_hint valide, Keycloak n'honore pas
  // `post_logout_redirect_uri` et ne termine pas fiablement la session SSO
  // du navigateur, donc le prochain /api/auth/login s'y ré-authentifie en
  // silence au lieu de repasser par l'écran de connexion.
  const idTokenHint = cookieStore.get(COOKIE_ID_TOKEN)?.value;

  const endSessionUrl = new URL(
    `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout`
  );
  endSessionUrl.searchParams.set("post_logout_redirect_uri", `${APP_URL}/login`);
  endSessionUrl.searchParams.set("client_id", KEYCLOAK_CLIENT_ID);
  if (idTokenHint) {
    endSessionUrl.searchParams.set("id_token_hint", idTokenHint);
  }

  const response = NextResponse.redirect(endSessionUrl);
  response.cookies.delete(COOKIE_ACCESS_TOKEN);
  response.cookies.delete(COOKIE_REFRESH_TOKEN);
  response.cookies.delete(COOKIE_ID_TOKEN);
  response.cookies.delete(COOKIE_SESSION);
  return response;
}
