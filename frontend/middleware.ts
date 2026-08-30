import { NextRequest, NextResponse } from "next/server";

import { COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN, COOKIE_SESSION } from "@/lib/auth/constants";

const ADMIN_ROLES = ["admin"];

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasToken = Boolean(request.cookies.get(COOKIE_ACCESS_TOKEN)?.value);

  if (!hasToken) {
    // access_token (~5 min) a expiré avant refresh_token (30 jours, D16) :
    // tente un renouvellement silencieux plutôt que de renvoyer direct sur
    // /login — /api/auth/refresh redirige lui-même vers /login si le
    // refresh_token est absent ou lui aussi invalide.
    const hasRefreshToken = Boolean(request.cookies.get(COOKIE_REFRESH_TOKEN)?.value);
    if (hasRefreshToken) {
      const refreshUrl = new URL("/api/auth/refresh", request.url);
      refreshUrl.searchParams.set("redirect", pathname + search);
      return NextResponse.redirect(refreshUrl);
    }
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname.startsWith("/admin")) {
    const sessionRaw = request.cookies.get(COOKIE_SESSION)?.value;
    try {
      const claims = sessionRaw ? JSON.parse(sessionRaw) : null;
      const isAdmin =
        claims?.is_super_admin === true ||
        (Array.isArray(claims?.roles) && claims.roles.some((r: string) => ADMIN_ROLES.includes(r)));
      if (!isAdmin) {
        return NextResponse.redirect(new URL("/housekeeping", request.url));
      }
    } catch {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/housekeeping/:path*",
    "/link-phone/:path*",
    "/admin/:path*",
    "/reservations/:path*",
    "/front-office/:path*",
    "/analytics/:path*",
    "/night-audit/:path*",
    "/notifications/:path*",
  ],
};
