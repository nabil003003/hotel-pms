import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { APP_URL, COOKIE_LOGIN_LINK_TOKEN, COOKIE_PHONE_LINK_TOKEN } from "@/lib/auth/constants";
export const dynamic = "force-dynamic";

/**
 * Atterrissage mobile du QR affiché sur /login (biom.txt Flux B) — contrairement
 * à /auth/hybrid (Flux A, desktop déjà authentifié), ici le desktop attend
 * encore qu'on lui relaie une session complète. Login normal (pas de
 * kc_action) : le téléphone utilise son credential WebAuthn déjà lié via
 * "Essayer une autre méthode" sur l'écran Keycloak, ou son mot de passe.
 *
 * `forceLogin=1` : sans lui, un téléphone déjà connu de Keycloak (session
 * SSO encore valide) se reconnecterait silencieusement sans jamais montrer
 * l'étape empreinte — voir app/api/auth/login/route.ts.
 */
export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.redirect(new URL("/login?error=missing_login_link_token", APP_URL));
  }

  const cookieStore = await cookies();
  // Supprime tout cookie phone-link résiduel d'un scan QR /link-phone
  // précédent — symétrique du nettoyage dans /auth/hybrid.
  cookieStore.delete(COOKIE_PHONE_LINK_TOKEN);
  cookieStore.set(COOKIE_LOGIN_LINK_TOKEN, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 300,
  });

  return NextResponse.redirect(new URL("/api/auth/login?forceLogin=1", APP_URL));
}

