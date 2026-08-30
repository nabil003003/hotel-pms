import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { APP_URL, COOKIE_LOGIN_LINK_TOKEN, COOKIE_PHONE_LINK_TOKEN } from "@/lib/auth/constants";
export const dynamic = "force-dynamic";

/**
 * Page d'atterrissage mobile du QR /link-phone (biom.txt Flux A) — le
 * téléphone scanne un lien vers ICI, pas vers Keycloak directement : on a
 * besoin de mémoriser le token de session avant d'entrer dans le flow OIDC,
 * pour pouvoir le retrouver dans /api/auth/callback une fois la cérémonie
 * WebAuthn same-device terminée sur ce même téléphone.
 */
export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.redirect(new URL("/login?error=missing_phone_link_token", APP_URL));
  }

  const cookieStore = await cookies();
  // Supprime tout cookie login-link résiduel d'un scan QR /login précédent —
  // sinon /api/auth/callback voit les deux cookies, teste loginLinkToken en
  // premier (l. 54) et prend le mauvais chemin (Flux B au lieu de Flux A).
  cookieStore.delete(COOKIE_LOGIN_LINK_TOKEN);
  cookieStore.set(COOKIE_PHONE_LINK_TOKEN, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 600,
  });

  return NextResponse.redirect(
    new URL("/api/auth/login?action=webauthn-register", APP_URL)
  );
}

