import { NextRequest, NextResponse } from "next/server";

import { APP_URL } from "@/lib/auth/constants";
import { setSessionCookies } from "@/lib/auth/cookies";
export const dynamic = "force-dynamic";

const AUTH_GATEWAY_URL = process.env.AUTH_GATEWAY_URL ?? "http://localhost:8001";

/**
 * Appelé par la page /login/qr une fois qu'elle a vu status=completed
 * — récupère les tokens déposés par le téléphone (une seule fois, effacés
 * côté backend juste après) et pose la session desktop exactement comme le
 * ferait /api/auth/callback pour un login PKCE classique.
 */
export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.redirect(new URL("/login?error=missing_login_link_token", APP_URL));
  }

  let claimed;
  try {
    const res = await fetch(`${AUTH_GATEWAY_URL}/api/v1/auth/login-link/${token}/claim`, { method: "POST" });
    if (!res.ok) {
      return NextResponse.redirect(new URL("/login?error=login_link_claim_failed", APP_URL));
    }
    claimed = await res.json();
  } catch (error) {
    console.error("login-link claim call failed", error);
    return NextResponse.redirect(new URL("/login?error=login_link_claim_failed", APP_URL));
  }

  if (!claimed.access_token) {
    return NextResponse.redirect(new URL("/login?error=login_link_claim_failed", APP_URL));
  }

  const response = NextResponse.redirect(new URL("/housekeeping", APP_URL));
  setSessionCookies(response, {
    access_token: claimed.access_token,
    refresh_token: claimed.refresh_token ?? undefined,
    id_token: claimed.id_token ?? undefined,
  });
  return response;
}
